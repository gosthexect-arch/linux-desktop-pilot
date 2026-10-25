#!/usr/bin/env python3
"""Read-only diagnosis, native MCP bridge and guarded Hyprland GUI transport."""

import argparse
import base64
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import selectors
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import uuid

from wayland_io import Wayland, probe

MAX_AGE = 60
NATIVE_TOOLS = {
    "doctor", "list_apps", "list_windows", "focused_window", "get_app_state",
    "screenshot", "activate_window", "click", "drag", "scroll", "press_key",
    "type_text", "set_value", "perform_action", "move_window", "resize_window",
}


def run(args, *, data=None, timeout=15):
    result = subprocess.run(args, input=data, capture_output=True, timeout=timeout)
    if result.returncode:
        # Do not echo argv (it could contain task text).
        raise RuntimeError(f"{Path(args[0]).name} failed ({result.returncode}): "
                           + result.stderr.decode(errors="replace")[-1500:])
    return result.stdout


def hypr(*args):
    return json.loads(run(["hyprctl", "-j", *args]))


def hypr_dispatch(lua, legacy):
    errors = []
    for command in [["hyprctl", "dispatch", lua], ["hyprctl", "dispatch", *legacy]]:
        try:
            if run(command).strip() == b"ok":
                return
            errors.append("dispatcher did not return ok")
        except RuntimeError as error:
            errors.append(str(error))
    raise RuntimeError("Hyprland Lua/legacy dispatch failed: " + "; ".join(errors))


def desktop_kind(env=None):
    env = os.environ if env is None else env
    name = env.get("XDG_CURRENT_DESKTOP", "").lower()
    if "hyprland" in name:
        return "hyprland"
    if "gnome" in name:
        return "gnome"
    if "kde" in name or "plasma" in name:
        return "kde"
    if not name and env.get("HYPRLAND_INSTANCE_SIGNATURE"):
        return "hyprland"
    return "other"


def native_binary():
    override = os.environ.get("LVCU_NATIVE_BIN")
    if override:
        path = Path(override)
        if not path.is_absolute() or not path.is_file() or not os.access(path, os.X_OK):
            raise ValueError("LVCU_NATIVE_BIN must be an absolute executable file")
        return str(path)
    candidates = [shutil.which("computer-use-linux")]
    xdg = os.environ.get("XDG_DATA_HOME", "")
    data_home = Path(xdg) if xdg and Path(xdg).is_absolute() else Path.home() / ".local/share"
    candidates += [str(root / "linux-visual-computer-use/runtime/node_modules/.bin/computer-use-linux")
                   for root in [data_home, Path.home() / ".local/share"]]
    return next((p for p in candidates if p and Path(p).is_file()
                 and os.access(p, os.X_OK)), None)


def readiness(report):
    """Detection only: never turn a backend declaration into a real GUI pass."""
    missing = []
    desktop = report["desktop"]
    session = report.get("session_type")
    fallback = report.get("hyprland_fallback_detected", {})
    native = report.get("native_binary")
    if platform.system() != "Linux":
        missing.append("This transport package requires Linux")
    if session not in {"wayland", "x11"}:
        missing.append("Run inside the logged-in graphical desktop session")
    if desktop == "hyprland" and session == "wayland" and all(
            fallback.get(k) for k in ["capture", "keyboard", "pointer"]):
        route = "hyprland-direct"
    elif desktop in {"hyprland", "gnome", "kde"} and native:
        route = "native-mcp"
        if report.get("native", {}).get("error"):
            missing.append("Native backend diagnosis failed; repair it before visual acceptance")
    else:
        route = None
        if desktop == "hyprland" and session == "wayland":
            missing += ["Hyprland fallback missing: " + k for k in
                        ["capture", "keyboard", "pointer"] if not fallback.get(k)]
        if not native:
            missing.append("Install or connect a working native Computer Use backend")
        if desktop not in {"hyprland", "gnome", "kde"}:
            missing.append("No validated desktop adapter selected for this session")
    return {"candidate_route": route, "setup_blockers": missing,
            "status": "blocked" if missing else "requires-visual-test",
            "host_requirements": {"can_load_skill_instructions": "must verify in host",
                                  "can_observe_images": "must verify in host/model",
                                  "can_execute_gui_tools": "must verify in host/model"},
            "model_name_required": False, "gui_success_guaranteed": False}


def doctor():
    commands = ["hyprctl", "grim", "wtype", "open-computer-use", "computer-use-linux"]
    result = {
        "schema_version": 2,
        "desktop": desktop_kind(), "session_type": os.environ.get("XDG_SESSION_TYPE"),
        "runtime": {"os": platform.system(), "architecture": platform.machine(),
                    "python": platform.python_version()},
        "wayland_session": bool(os.environ.get("WAYLAND_DISPLAY")),
        "commands": {name: shutil.which(name) for name in commands},
        "observed_gui_tests": "not-run; diagnostics do not prove capture or input",
    }
    if os.environ.get("WAYLAND_DISPLAY"):
        try:
            # A broken compositor must not hang all diagnosis. This child only
            # enumerates protocols; it creates no input device and sends no input.
            result["wayland_protocols"] = json.loads(run(
                [sys.executable, str(Path(__file__).resolve()), "protocols"], timeout=5))
        except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
            result["wayland_protocols"] = {"error": str(error)}
    if result["desktop"] == "hyprland":
        try:
            result["hyprland_version"] = run(["hyprctl", "version"]).decode().splitlines()[0]
            result["window_count"] = len(hypr("clients"))
            result["monitors"] = [{k: m.get(k) for k in
                                   ["name", "width", "height", "x", "y", "scale", "transform"]}
                                  for m in hypr("monitors")]
            protocols = result.get("wayland_protocols", {})
            result["hyprland_fallback_detected"] = {
                "capture": bool(shutil.which("grim")),
                "keyboard": bool(shutil.which("wtype")),
                "pointer": bool(protocols.get("virtual_pointer")),
                "modifier_gestures": bool(protocols.get("virtual_keyboard")),
                "capture_and_input_verified": False,
            }
        except (OSError, RuntimeError, ValueError) as error:
            result["hyprland_error"] = str(error)
    binary = native_binary()
    result["native_binary"] = binary
    if binary:
        try:
            report = json.loads(run([binary, "doctor"], timeout=30))
            result["native"] = {k: report.get(k) for k in ["readiness", "capabilities"]}
        except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
            result["native"] = {"error": str(error)}
    result["compatibility"] = readiness(result)
    return result


class NativeClient:
    """One MCP stdio session; indexes cannot be carried to a subsequent CLI call."""

    def __enter__(self):
        binary = native_binary()
        if not binary:
            raise RuntimeError("native backend unavailable; read references/backends.md")
        env = {**os.environ, "COMPUTER_USE_LINUX_ENABLE_SHELL": "0"}
        self.errors = tempfile.TemporaryFile()
        self.process = subprocess.Popen([binary, "mcp"], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=self.errors, env=env)
        self.buffer = b""
        self.seq = 0
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ)
        try:
            self.request("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                         "clientInfo": {"name": "linux-visual-computer-use", "version": "1"}})
            self.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        except BaseException:
            self.__exit__(None, None, None)
            raise
        return self

    def send(self, obj):
        self.process.stdin.write((json.dumps(obj) + "\n").encode())
        self.process.stdin.flush()

    def request(self, method, params, timeout=45):
        self.seq += 1
        wanted = self.seq
        self.send({"jsonrpc": "2.0", "id": wanted, "method": method, "params": params})
        deadline = time.monotonic() + timeout
        while True:
            while b"\n" in self.buffer:
                line, self.buffer = self.buffer.split(b"\n", 1)
                if not line.strip():
                    continue
                msg = json.loads(line)
                if msg.get("id") == wanted:
                    if "error" in msg:
                        raise RuntimeError("MCP error: " + json.dumps(msg["error"]))
                    return msg.get("result", {})
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not self.selector.select(remaining):
                raise RuntimeError("MCP timeout; action may have been dispatched; observe before retry")
            chunk = os.read(self.process.stdout.fileno(), 65536)
            if not chunk:
                raise RuntimeError("MCP server closed; observe before retrying any action")
            self.buffer += chunk
            if len(self.buffer) > 32 * 1024 * 1024:
                raise RuntimeError("MCP message exceeds the 32 MiB bridge limit")

    def __exit__(self, *_):
        try:
            self.process.stdin.close()
            self.process.wait(timeout=2)
        except (BrokenPipeError, subprocess.TimeoutExpired):
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        finally:
            self.process.stdout.close()
            self.selector.close()
            self.errors.close()


def contains_index(value):
    if isinstance(value, dict):
        return "element_index" in value or any(contains_index(v) for v in value.values())
    return isinstance(value, list) and any(contains_index(v) for v in value)


def native_call(args):
    with NativeClient() as client:
        catalog = client.request("tools/list", {})
        if args.action == "tools":
            tools = catalog.get("tools", [])
            if args.tool:
                matches = [t for t in tools if t["name"] == args.tool]
                if not matches:
                    raise ValueError("requested tool is not exposed by this server")
                return {k: matches[0][k] for k in ["name", "description", "inputSchema"]}
            return {"tools": [{"name": t["name"],
                               "required": t.get("inputSchema", {}).get("required", [])}
                              for t in tools], "next": "use native tools --tool NAME for its schema"}
        if args.tool not in NATIVE_TOOLS:
            raise ValueError("tool is not in the GUI adapter's allowlist")
        payload = json.loads(args.args)
        if not isinstance(payload, dict) or contains_index(payload):
            raise ValueError("one-shot calls require an object without session-scoped element indexes")
        if args.tool not in {t["name"] for t in catalog.get("tools", [])}:
            raise ValueError("tool not exposed by installed server; inspect native tools")
        result = client.request("tools/call", {"name": args.tool, "arguments": payload})
    content = []
    for item in result.get("content", []):
        if item.get("type") == "image":
            directory = Path(args.output_dir or tempfile.mkdtemp(prefix="lvcu-captures-"))
            directory = directory.expanduser().resolve()
            directory.mkdir(parents=True, exist_ok=True, mode=0o700)
            ext = ".png" if item.get("mimeType") == "image/png" else ".jpg"
            path = directory / (uuid.uuid4().hex + ext)
            write_private(path, base64.b64decode(item["data"], validate=True))
            content.append({"type": "local_image", "path": str(path),
                            "mimeType": item.get("mimeType")})
        else:
            content.append(item)
    return {**result, "content": content,
            "bridge_note": "one-shot session; inspect images/state; dispatch is not verification"}


def identity(window):
    return {k: window.get(k) for k in ["address", "pid", "class", "at", "size", "monitor"]} | {
        "workspace_id": window.get("workspace", {}).get("id")}


def find_window(address):
    if not re.fullmatch(r"0x[0-9a-fA-F]+", address):
        raise ValueError("window must be an observed hexadecimal Hyprland address")
    match = [w for w in hypr("clients") if w.get("address") == address]
    if len(match) != 1 or not match[0].get("mapped", True) or match[0].get("hidden", False):
        raise ValueError("target window is missing, hidden or ambiguous")
    return match[0]


def write_private(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)


def capture(address, output):
    window = find_window(address)
    if hypr("activewindow").get("address") != address:
        raise ValueError("target is not focused; explicitly focus then observe")
    x, y = window["at"]
    width, height = window["size"]
    if width <= 0 or height <= 0:
        raise ValueError("window has no capturable area")
    output = Path(output).expanduser().resolve()
    if output.exists() or Path(str(output) + ".json").exists():
        raise ValueError("capture output already exists; choose a new filename")
    data = run(["grim", "-s", "1", "-g", f"{x},{y} {width}x{height}", "-"])
    if data[:8] != b"\x89PNG\r\n\x1a\n" or len(data) < 24:
        raise ValueError("grim did not produce a PNG")
    actual = struct.unpack(">II", data[16:24])
    if actual != (width, height):
        raise ValueError("capture dimensions disagree with logical window geometry")
    if identity(find_window(address)) != identity(window) or hypr("activewindow").get("address") != address:
        raise ValueError("window changed during capture; observe again")
    metadata = {"schema": 1, "created": time.time(), "image": str(output),
                "sha256": hashlib.sha256(data).hexdigest(), "window": identity(window),
                "coordinate_space": "window-logical", "width": width, "height": height}
    write_private(output, data)
    sidecar = Path(str(output) + ".json")
    write_private(sidecar, (json.dumps(metadata, indent=2) + "\n").encode())
    return {"image": str(output), "snapshot": str(sidecar), "width": width, "height": height}


def validate_snapshot(meta, current, focused, now=None):
    now = time.time() if now is None else now
    created = meta.get("created")
    if (meta.get("schema") != 1 or meta.get("coordinate_space") != "window-logical"
            or not isinstance(created, (int, float)) or not math.isfinite(created)
            or not 0 <= now - created <= MAX_AGE):
        raise ValueError("snapshot is stale or invalid; capture again")
    expected = meta.get("window")
    if not isinstance(expected, dict) or expected != identity(current) or focused.get("address") != expected.get("address"):
        raise ValueError("window identity, geometry, workspace or focus changed; capture again")
    if [meta.get("width"), meta.get("height")] != current.get("size"):
        raise ValueError("snapshot dimensions disagree with target")


def load_snapshot(path):
    meta = json.loads(Path(path).read_text())
    address = meta.get("window", {}).get("address", "")
    validate_snapshot(meta, find_window(address), hypr("activewindow"))
    image = Path(meta["image"])
    if not image.is_absolute() or hashlib.sha256(image.read_bytes()).hexdigest() != meta["sha256"]:
        raise ValueError("snapshot image is missing or changed")
    return meta


def point(meta, x, y):
    if not all(math.isfinite(n) for n in [x, y]):
        raise ValueError("coordinates must be finite")
    x, y = round(x), round(y)
    if not (0 <= x < meta["width"] and 0 <= y < meta["height"]):
        raise ValueError("point is outside the original screenshot")
    origin = meta["window"]["at"]
    return origin[0] + x, origin[1] + y


def guard(meta):
    address = meta["window"]["address"]
    validate_snapshot(meta, find_window(address), hypr("activewindow"))


def move_to(meta, x, y):
    guard(meta)
    hypr_dispatch(f"hl.dsp.cursor.move({{ x = {int(x)}, y = {int(y)} }})",
                  ["movecursor", str(x), str(y)])
    landed = hypr("cursorpos")
    if abs(landed["x"] - x) > 2 or abs(landed["y"] - y) > 2:
        raise RuntimeError("cursor did not reach the observed target; no button will be pressed")
    guard(meta)


def key_args(spec):
    parts = spec.split("+")
    aliases = {"control": "ctrl", "ctrl": "ctrl", "shift": "shift", "alt": "alt",
               "super": "logo", "meta": "logo"}
    modifiers = []
    for part in parts[:-1]:
        if part.lower() not in aliases:
            raise ValueError("unknown key modifier")
        modifiers += [aliases[part.lower()]]
    keys = {"enter": "Return", "return": "Return", "escape": "Escape", "esc": "Escape",
            "tab": "Tab", "backspace": "BackSpace", "delete": "Delete", "space": "space",
            "home": "Home", "end": "End", "pageup": "Page_Up", "pagedown": "Page_Down",
            "left": "Left", "right": "Right", "up": "Up", "down": "Down"}
    key = parts[-1]
    if key.lower() in keys:
        key = keys[key.lower()]
    elif re.fullmatch(r"[A-Za-z0-9]", key):
        key = key.lower()
    elif re.fullmatch(r"[fF](?:[1-9]|1[0-2])", key):
        key = key.upper()
    else:
        raise ValueError("unsupported named key; use a supported key or literal text")
    args = ["wtype"]
    for mod in modifiers:
        args += ["-M", mod]
    args += ["-P", key, "-p", key]
    for mod in reversed(modifiers):
        args += ["-m", mod]
    return args


def hypr_action(args):
    if desktop_kind() != "hyprland":
        raise RuntimeError("Hyprland fallback cannot run in this desktop; use native adapter")
    if args.action == "windows":
        return [{k: w.get(k) for k in ["address", "class", "title", "pid", "at", "size", "xwayland"]}
                for w in hypr("clients")]
    if args.action == "focus":
        find_window(args.window)
        hypr_dispatch('hl.dsp.focus({ window = "address:' + args.window + '" })',
                      ["focuswindow", "address:" + args.window])
        for _ in range(15):
            if hypr("activewindow").get("address") == args.window:
                return {"focused": args.window, "next": "capture and inspect before input"}
            time.sleep(0.05)
        raise RuntimeError("focus could not be verified")
    if args.action == "capture":
        return capture(args.window, args.output)
    meta = load_snapshot(args.snapshot)
    if args.action == "key":
        command = key_args(args.key)  # Validate before any input.
        guard(meta)
        run(command)
    elif args.action == "text":
        data = sys.stdin.buffer.read(4097)
        text = data.decode("utf-8")
        if len(data) > 4096 or not 1 <= len(text) <= 100 or "\0" in text:
            raise ValueError("text must contain 1-100 Unicode characters and no NUL")
        guard(meta)
        run(["wtype", "-"], data=data)
    elif args.action in {"move", "click", "scroll", "drag"}:
        start = point(meta, args.x, args.y)
        end = point(meta, args.to_x, args.to_y) if args.action == "drag" else None
        if args.action == "drag" and not 0.1 <= args.duration <= 5:
            raise ValueError("drag duration must be 0.1-5 seconds")
        mods = [m.lower() for m in args.modifiers.split("+") if m] if hasattr(args, "modifiers") else []
        if any(m not in {"shift", "ctrl", "alt", "super"} for m in mods):
            raise ValueError("unsupported gesture modifier")
        if args.action == "move":
            move_to(meta, *start)
        else:
            with Wayland() as connection:
                connection.start_pointer()
                connection.set_modifiers(mods)
                move_to(meta, *start)
                if args.action == "click":
                    for _ in range(args.count):
                        guard(meta)
                        connection.button(args.button, True)
                        time.sleep(0.04)
                        connection.button(args.button, False)
                        time.sleep(0.07)
                elif args.action == "scroll":
                    connection.scroll(args.horizontal, args.vertical)
                else:
                    connection.button(args.button, True)
                    steps = max(2, int(args.duration * 25))
                    for step in range(1, steps + 1):
                        fraction = step / steps
                        move_to(meta, round(start[0] + (end[0] - start[0]) * fraction),
                                round(start[1] + (end[1] - start[1]) * fraction))
                        time.sleep(args.duration / steps)
                    connection.button(args.button, False)
    else:
        raise ValueError("unknown GUI action")
    result = {"dispatched": True, "verified": False, "action": args.action,
              "next": "inspect the post-action screenshot before proceeding"}
    try:
        guard(meta)
        result.update(capture(meta["window"]["address"], args.after))
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
        result["observation_error"] = str(error)
        result["next"] = "action may have happened; rediscover/capture before retrying"
    return result


def parser():
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="mode", required=True)
    sub.add_parser("doctor")
    sub.add_parser("protocols", help="read-only Wayland protocol discovery")
    native = sub.add_parser("native").add_subparsers(dest="action", required=True)
    tools = native.add_parser("tools")
    tools.add_argument("--tool")
    call = native.add_parser("call")
    call.add_argument("tool")
    call.add_argument("--args", default="{}")
    call.add_argument("--output-dir")
    actions = sub.add_parser("hypr").add_subparsers(dest="action", required=True)
    actions.add_parser("windows")
    focus = actions.add_parser("focus")
    focus.add_argument("--window", required=True)
    cap = actions.add_parser("capture")
    cap.add_argument("--window", required=True)
    cap.add_argument("--output", required=True)
    for name in ["move", "click", "scroll", "drag", "key", "text"]:
        action = actions.add_parser(name)
        action.add_argument("--snapshot", required=True)
        action.add_argument("--after", required=True)
        if name in {"move", "click", "scroll", "drag"}:
            action.add_argument("--x", type=float, required=True)
            action.add_argument("--y", type=float, required=True)
        if name in {"click", "drag"}:
            action.add_argument("--button", choices=["left", "right", "middle"], default="left")
            action.add_argument("--modifiers", default="")
        if name == "click":
            action.add_argument("--count", type=int, choices=[1, 2], default=1)
        elif name == "drag":
            action.add_argument("--to-x", type=float, required=True)
            action.add_argument("--to-y", type=float, required=True)
            action.add_argument("--duration", type=float, default=0.6)
        elif name == "scroll":
            action.add_argument("--horizontal", type=int, default=0)
            action.add_argument("--vertical", type=int, default=0)
        elif name == "key":
            action.add_argument("--key", required=True)
    return root


def main():
    args = parser().parse_args()
    try:
        result = probe() if args.mode == "protocols" else doctor() if args.mode == "doctor" else (
            native_call(args) if args.mode == "native" else hypr_action(args))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if isinstance(result, dict) and result.get("isError") else 0
    except (OSError, RuntimeError, ValueError, KeyError, subprocess.TimeoutExpired) as error:
        print(json.dumps({"error": str(error), "retry": "observe before repeating any input"},
                         ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
