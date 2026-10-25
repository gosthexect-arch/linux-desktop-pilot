"""Transport invariants. These are not compositor/application acceptance tests."""
import copy
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "linux-visual-computer-use/scripts"
sys.path.insert(0, str(SCRIPTS))
import desktop
import wayland_io


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.window = {"address": "0x123", "pid": 44, "class": "test",
                       "at": [-900, 40], "size": [800, 600], "monitor": 2,
                       "workspace": {"id": 3}}
        self.meta = {"schema": 1, "coordinate_space": "window-logical", "created": 100,
                     "window": desktop.identity(self.window), "width": 800, "height": 600}
        self.focus = {"address": "0x123"}

    def test_current_state_is_accepted(self):
        desktop.validate_snapshot(self.meta, self.window, self.focus, now=101)

    def test_stale_future_and_nonfinite_observations_refuse_input(self):
        for created in [39, 102, math.nan, math.inf, "now", None]:
            with self.subTest(created=created), self.assertRaises(ValueError):
                desktop.validate_snapshot({**self.meta, "created": created},
                                          self.window, self.focus, now=101)

    def test_target_changes_refuse_input(self):
        for key, value in [("pid", 45), ("at", [0, 0]), ("size", [801, 600]),
                           ("monitor", 4), ("workspace", {"id": 5})]:
            changed = {**self.window, key: value}
            with self.subTest(key=key), self.assertRaises(ValueError):
                desktop.validate_snapshot(self.meta, changed, self.focus, now=101)

    def test_focus_change_refuses_input(self):
        with self.assertRaises(ValueError):
            desktop.validate_snapshot(self.meta, self.window, {"address": "0x999"}, now=101)

    def test_missing_identity_refuses_input(self):
        with self.assertRaises(ValueError):
            desktop.validate_snapshot({**self.meta, "window": None},
                                      self.window, self.focus, now=101)

    def test_dimension_mismatch_refuses_input(self):
        with self.assertRaises(ValueError):
            desktop.validate_snapshot({**self.meta, "width": 1600},
                                      self.window, self.focus, now=101)

    def test_negative_monitor_origin_is_preserved(self):
        self.assertEqual(desktop.point(self.meta, 100, 80), (-800, 120))

    def test_points_outside_capture_never_reach_mouse(self):
        for x, y in [(-1, 0), (800, 0), (0, 600), (math.nan, 1), (1, math.inf)]:
            with self.subTest(point=(x, y)), self.assertRaises(ValueError):
                desktop.point(self.meta, x, y)

    def test_failed_cursor_landing_does_not_emit_a_button(self):
        with patch.object(desktop, "guard"), patch.object(desktop, "hypr_dispatch"), \
             patch.object(desktop, "hypr", return_value={"x": 0, "y": 0}), \
             self.assertRaises(RuntimeError):
            desktop.move_to(self.meta, 100, 100)

    def test_changed_image_refuses_input(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "image.png"
            image.write_bytes(b"changed")
            snapshot = Path(directory) / "image.png.json"
            snapshot.write_text(json.dumps({**self.meta, "image": str(image), "sha256": "bad"}))
            with patch.object(desktop, "find_window", return_value=self.window), \
                 patch.object(desktop, "hypr", return_value=self.focus), \
                 patch.object(desktop.time, "time", return_value=101), \
                 self.assertRaises(ValueError):
                desktop.load_snapshot(snapshot)


class RoutingTests(unittest.TestCase):
    def test_dispatch_error_text_with_exit_zero_is_not_success(self):
        with patch.object(desktop, "run", side_effect=[b"Invalid dispatcher\n", b"ok\n"]) as command:
            desktop.hypr_dispatch("lua", ["legacy"])
            self.assertEqual(command.call_count, 2)

    def test_lua_dispatch_is_used_without_duplicate_legacy_action(self):
        with patch.object(desktop, "run", return_value=b"ok\n") as command:
            desktop.hypr_dispatch("lua", ["legacy"])
            self.assertEqual(command.call_count, 1)

    def test_desktop_detection(self):
        for value, expected in [("Hyprland", "hyprland"), ("ubuntu:GNOME", "gnome"),
                                ("KDE", "kde"), ("Plasma", "kde"), ("Xfce", "other")]:
            with self.subTest(value=value):
                self.assertEqual(desktop.desktop_kind({"XDG_CURRENT_DESKTOP": value}), expected)

    def test_valid_shortcuts_do_not_use_a_shell(self):
        args = desktop.key_args("Ctrl+Shift+L")
        self.assertEqual(args[0], "wtype")
        self.assertEqual(args[1:5], ["-M", "ctrl", "-M", "shift"])
        self.assertEqual(args[-4:], ["-m", "shift", "-m", "ctrl"])

    def test_unknown_or_commandlike_keys_rejected(self):
        for key in ["Ctrl+$(touch /tmp/no)", "Hyper+L", "", "Ctrl+", "Ctrl+L;reboot"]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                desktop.key_args(key)

    def test_indexes_cannot_cross_one_shot_sessions(self):
        self.assertTrue(desktop.contains_index({"nested": [{"element_index": "1"}]}))
        self.assertFalse(desktop.contains_index({"pid": 3, "name": "Save"}))

    def test_private_output_does_not_overwrite_existing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence"
            desktop.write_private(path, b"original")
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                desktop.write_private(path, b"overwrite")
            self.assertEqual(path.read_bytes(), b"original")

    def test_invalid_native_override_does_not_fall_back_silently(self):
        with patch.dict(os.environ, {"LVCU_NATIVE_BIN": "relative-command"}), \
             self.assertRaises(ValueError):
            desktop.native_binary()

    def test_pointer_wire_method_positions_match_public_protocol(self):
        methods = wayland_io.VPOINTER.methods
        self.assertEqual(methods[2].name, b"button")
        self.assertEqual(methods[4].name, b"frame")
        self.assertEqual(methods[7].signature, b"uufi")
        self.assertEqual(methods[8].name, b"destroy")


class McpTests(unittest.TestCase):
    def test_real_stdio_handshake_and_error_without_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            server = Path(directory) / "fake-mcp"
            calls = Path(directory) / "calls"
            server.write_text("#!" + sys.executable + "\n" +
                "import sys,json\n" +
                "for line in sys.stdin:\n" +
                " m=json.loads(line)\n" +
                " if 'id' not in m: continue\n" +
                " method=m['method']\n" +
                " with open(" + repr(str(calls)) + ",'a') as f: f.write(method+'\\n')\n" +
                " response={'jsonrpc':'2.0','id':m['id']}\n" +
                " if method=='initialize': response['result']={'protocolVersion':'2024-11-05','capabilities':{}}\n" +
                " else: response['error']={'code':-32602,'message':'rejected test action'}\n" +
                " print(json.dumps(response),flush=True)\n")
            server.chmod(0o700)
            with patch.dict(os.environ, {"LVCU_NATIVE_BIN": str(server)}):
                with desktop.NativeClient() as client:
                    with self.assertRaisesRegex(RuntimeError, "rejected test action"):
                        client.request("tools/call", {"name": "click", "arguments": {}})
            self.assertEqual(calls.read_text().splitlines(), ["initialize", "tools/call"])


if __name__ == "__main__":
    unittest.main()
