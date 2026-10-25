"""Small virtual-pointer transport; no shell, device access or compositor config.

Wire declarations follow the public virtual-pointer and virtual-keyboard XML
linked in references/backends.md. Only version 1 requests are used.
"""

import ctypes as C
import ctypes.util
import os
import time

P = C.c_void_p
U = C.c_uint32
I = C.c_int32


class Interface(C.Structure):
    pass


class Message(C.Structure):
    _fields_ = [("name", C.c_char_p), ("signature", C.c_char_p),
                ("types", C.POINTER(C.POINTER(Interface)))]


Interface._fields_ = [("name", C.c_char_p), ("version", C.c_int),
                     ("method_count", C.c_int), ("methods", C.POINTER(Message)),
                     ("event_count", C.c_int), ("events", C.POINTER(Message))]
KEEP = []


def interface(name, requests):
    messages = (Message * len(requests))()
    for n, (request, signature, types) in enumerate(requests):
        array = (C.POINTER(Interface) * len(types))(
            *(C.pointer(t) if t is not None else C.POINTER(Interface)()
              for t in types))
        KEEP.append(array)
        messages[n] = Message(request.encode(), signature.encode(), array)
    result = Interface(name.encode(), 1, len(requests), messages, 0, None)
    KEEP.extend([messages, result])
    return result


VPOINTER = interface("zwlr_virtual_pointer_v1", [
    ("motion", "uff", [None] * 3),
    ("motion_absolute", "uuuuu", [None] * 5),
    ("button", "uuu", [None] * 3),
    ("axis", "uuf", [None] * 3),
    ("frame", "", []),
    ("axis_source", "u", [None]),
    ("axis_stop", "uu", [None] * 2),
    ("axis_discrete", "uufi", [None] * 4),
    ("destroy", "", []),
])
VKEYBOARD = interface("zwp_virtual_keyboard_v1", [
    ("keymap", "uhu", [None] * 3),
    ("key", "uuu", [None] * 3),
    ("modifiers", "uuuu", [None] * 4),
    ("destroy", "", []),
])


class Wayland:
    def __init__(self):
        path = ctypes.util.find_library("wayland-client")
        if not path:
            raise RuntimeError("libwayland-client is unavailable")
        self.lib = C.CDLL(path)
        for name, result, args in [
            ("wl_display_connect", P, [C.c_char_p]),
            ("wl_display_disconnect", None, [P]),
            ("wl_display_roundtrip", C.c_int, [P]),
            ("wl_proxy_marshal_flags", P, [P, U, C.POINTER(Interface), U, U]),
            ("wl_proxy_add_listener", C.c_int, [P, P, P]),
            ("wl_proxy_destroy", None, [P]),
        ]:
            fn = getattr(self.lib, name)
            fn.restype, fn.argtypes = result, args
        self.display = self.lib.wl_display_connect(None)
        if not self.display:
            raise RuntimeError("cannot connect to this Wayland session")
        self.pointer = self.keyboard = self.seat = None
        self.held_button = None
        self.globals = {}
        registry_interface = Interface.in_dll(self.lib, "wl_registry_interface")
        self.registry = self.lib.wl_proxy_marshal_flags(
            self.display, 1, C.byref(registry_interface), 1, 0, P())
        global_cb = C.CFUNCTYPE(None, P, P, U, C.c_char_p, U)
        remove_cb = C.CFUNCTYPE(None, P, P, U)

        def add(_data, _registry, name, iface, version):
            self.globals[iface.decode()] = (int(name), int(version))

        self.listeners = (P * 2)()
        self.callbacks = [global_cb(add), remove_cb(lambda *_: None)]
        for n, cb in enumerate(self.callbacks):
            self.listeners[n] = C.cast(cb, P)
        self.lib.wl_proxy_add_listener(self.registry, self.listeners, None)
        self.sync()

    def sync(self):
        if self.lib.wl_display_roundtrip(self.display) < 0:
            raise RuntimeError("Wayland connection failed")

    def bind(self, iface):
        entry = self.globals.get(iface.name.decode())
        if not entry:
            raise RuntimeError(iface.name.decode() + " is not advertised")
        proxy = self.lib.wl_proxy_marshal_flags(
            self.registry, 0, C.byref(iface), 1, 0,
            U(entry[0]), C.c_char_p(iface.name), U(1), P())
        if not proxy:
            raise RuntimeError("Wayland object bind failed")
        return proxy

    def send(self, proxy, opcode, *args, destroy=False):
        return self.lib.wl_proxy_marshal_flags(
            P(proxy), opcode, None, 1, 1 if destroy else 0, *args)

    def start_pointer(self):
        seat_interface = Interface.in_dll(self.lib, "wl_seat_interface")
        manager = interface("zwlr_virtual_pointer_manager_v1", [
            ("create_virtual_pointer", "?on", [seat_interface, VPOINTER]),
            ("destroy", "", []),
        ])
        manager_proxy = self.bind(manager)
        self.pointer = self.lib.wl_proxy_marshal_flags(
            P(manager_proxy), 0, C.byref(VPOINTER), 1, 0, P(), P())
        self.send(manager_proxy, 1, destroy=True)
        self.sync()
        # Keep the device alive through the gesture and allow clients to bind.
        time.sleep(0.08)

    @staticmethod
    def now():
        return U(int(time.monotonic() * 1000) & 0xFFFFFFFF)

    def frame(self):
        self.send(self.pointer, 4)
        self.sync()

    def button(self, name, pressed):
        code = {"left": 272, "right": 273, "middle": 274}[name]
        self.send(self.pointer, 2, self.now(), U(code), U(int(pressed)))
        self.held_button = name if pressed else None
        self.frame()

    def scroll(self, horizontal, vertical):
        self.send(self.pointer, 5, U(0))  # wheel source
        for axis, steps in [(0, vertical), (1, horizontal)]:
            if steps:
                self.send(self.pointer, 7, self.now(), U(axis),
                          I(int(steps * 15 * 256)), I(steps))
        self.frame()

    def set_modifiers(self, names):
        if not names:
            return
        if not self.keyboard:
            self._start_keyboard()
        mask = 0
        for name in names:
            index = self.mod_indices[name.lower()]
            if index >= 32:
                raise RuntimeError("modifier missing from temporary keymap")
            mask |= 1 << index
        self.send(self.keyboard, 2, U(mask), U(0), U(0), U(0))
        self.sync()

    def _start_keyboard(self):
        xkb_path = ctypes.util.find_library("xkbcommon")
        if not xkb_path:
            raise RuntimeError("modifier gestures require libxkbcommon")
        xkb = C.CDLL(xkb_path)
        definitions = [
            ("xkb_context_new", P, [C.c_int]),
            ("xkb_keymap_new_from_names", P, [P, P, C.c_int]),
            ("xkb_keymap_get_as_string", P, [P, C.c_int]),
            ("xkb_keymap_mod_get_index", U, [P, C.c_char_p]),
            ("xkb_keymap_unref", None, [P]),
            ("xkb_context_unref", None, [P]),
        ]
        for name, restype, args in definitions:
            getattr(xkb, name).restype = restype
            getattr(xkb, name).argtypes = args
        context = xkb.xkb_context_new(0)
        if not context:
            raise RuntimeError("could not create temporary modifier keymap")
        keymap = xkb.xkb_keymap_new_from_names(context, None, 0)
        if not keymap:
            xkb.xkb_context_unref(context)
            raise RuntimeError("could not compile temporary modifier keymap")
        raw = xkb.xkb_keymap_get_as_string(keymap, 1)
        if not raw:
            xkb.xkb_keymap_unref(keymap)
            xkb.xkb_context_unref(context)
            raise RuntimeError("could not serialize modifier keymap")
        try:
            data = C.string_at(raw) + b"\0"
            self.mod_indices = {
                alias: int(xkb.xkb_keymap_mod_get_index(keymap, name.encode()))
                for alias, name in [("shift", "Shift"), ("ctrl", "Control"),
                                    ("alt", "Mod1"), ("super", "Mod4")]
            }
        finally:
            libc = C.CDLL(None)
            libc.free.argtypes = [P]
            libc.free(raw)
            xkb.xkb_keymap_unref(keymap)
            xkb.xkb_context_unref(context)
        seat_iface = Interface.in_dll(self.lib, "wl_seat_interface")
        self.seat = self.bind(seat_iface)
        cap_cb = C.CFUNCTYPE(None, P, P, U)(lambda *_: None)
        self.seat_callbacks = [cap_cb]
        self.seat_listener = (P * 1)(C.cast(cap_cb, P))
        self.lib.wl_proxy_add_listener(self.seat, self.seat_listener, None)
        manager = interface("zwp_virtual_keyboard_manager_v1", [
            ("create_virtual_keyboard", "on", [seat_iface, VKEYBOARD])])
        manager_proxy = self.bind(manager)
        self.keyboard = self.lib.wl_proxy_marshal_flags(
            P(manager_proxy), 0, C.byref(VKEYBOARD), 1, 0, P(self.seat), P())
        self.lib.wl_proxy_destroy(P(manager_proxy))
        fd = os.memfd_create("lvcu-modifiers", os.MFD_CLOEXEC)
        try:
            os.write(fd, data)
            self.send(self.keyboard, 0, U(1), C.c_int(fd), U(len(data)))
            self.sync()
        finally:
            os.close(fd)

    def close(self):
        if not self.display:
            return
        try:
            if self.pointer and self.held_button:
                self.button(self.held_button, False)
            if self.keyboard:
                self.send(self.keyboard, 2, U(0), U(0), U(0), U(0))
                self.send(self.keyboard, 3, destroy=True)
            if self.pointer:
                self.send(self.pointer, 8, destroy=True)
            self.sync()
        finally:
            self.lib.wl_display_disconnect(self.display)
            self.display = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def probe():
    with Wayland() as connection:
        return {
            "virtual_pointer": "zwlr_virtual_pointer_manager_v1" in connection.globals,
            "virtual_keyboard": "zwp_virtual_keyboard_manager_v1" in connection.globals,
        }
