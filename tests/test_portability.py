"""Filesystem install and capability checks, without claiming a new GUI session."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "linux-visual-computer-use/scripts"
sys.path.insert(0, str(SCRIPTS))
import desktop

spec = importlib.util.spec_from_file_location("lvcu_install", SCRIPTS / "install.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="lvcu-install-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "Pacote da usuária" / installer.NAME
        shutil.copytree(SCRIPTS.parent, self.source,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        self.skills = self.root / "Outro usuário" / "skills com espaços"

    def test_install_into_another_user_path_and_rerun_without_changes(self):
        result = installer.install(self.source, self.skills)
        target = Path(result["target"])
        self.assertEqual(result["status"], "installed")
        self.assertEqual(installer.payload(target), installer.payload(self.source))
        repeated = installer.install(self.source, self.skills)
        self.assertEqual(repeated["status"], "unchanged")
        self.assertIsNone(repeated["backup"])
        self.assertFalse((self.skills.parent / "skill-backups").exists())

    def test_update_preserves_users_previous_copy_outside_discovery_root(self):
        result = installer.install(self.source, self.skills)
        target = Path(result["target"])
        local = target / "references/local-notes.md"
        local.write_text("Existing user customization")
        result = installer.install(self.source, self.skills)
        backup = Path(result["backup"])
        self.assertEqual(result["status"], "updated")
        self.assertEqual((backup / "references/local-notes.md").read_text(),
                         "Existing user customization")
        self.assertFalse(backup.is_relative_to(self.skills))
        self.assertEqual(installer.payload(target), installer.payload(self.source))

    def test_failed_swap_restores_previous_installation(self):
        target = Path(installer.install(self.source, self.skills)["target"])
        (target / "references/local-notes.md").write_text("keep me")
        original_rename = Path.rename

        def fail_staged_swap(path, destination):
            if path.parent.name.startswith(".lvcu-install-"):
                raise OSError("injected replacement failure")
            return original_rename(path, destination)

        with patch.object(Path, "rename", fail_staged_swap), self.assertRaises(OSError):
            installer.install(self.source, self.skills)
        self.assertEqual((target / "references/local-notes.md").read_text(), "keep me")
        self.assertFalse(list(self.skills.glob(".lvcu-install-*")))

    def test_unrelated_destination_is_not_overwritten(self):
        target = self.skills / installer.NAME
        target.mkdir(parents=True)
        (target / "important").write_text("preserve")
        with self.assertRaises(ValueError):
            installer.install(self.source, self.skills)
        self.assertEqual((target / "important").read_text(), "preserve")

    def test_symlink_destination_is_not_followed(self):
        self.skills.mkdir(parents=True)
        (self.skills / installer.NAME).symlink_to(self.source, target_is_directory=True)
        with self.assertRaises(ValueError):
            installer.install(self.source, self.skills)

    def test_incomplete_package_is_rejected_before_destination_created(self):
        (self.source / "scripts/desktop.py").unlink()
        with self.assertRaises(ValueError):
            installer.install(self.source, self.skills)
        self.assertFalse(self.skills.exists())

    def test_recursive_install_is_rejected(self):
        with self.assertRaises(ValueError):
            installer.install(self.source, self.source / "nested")

    def test_real_installer_cli_and_relocated_helper_launch(self):
        process = subprocess.run([sys.executable, str(self.source / "scripts/install.py"),
                                  "--skills-dir", str(self.skills)],
                                 capture_output=True, text=True, timeout=10)
        self.assertEqual(process.returncode, 0, process.stderr)
        result = json.loads(process.stdout)
        command = result["commands"]["doctor"]
        self.assertTrue(str(command[1]).startswith(str(self.skills)))
        process = subprocess.run([*command[:2], "--help"], capture_output=True,
                                 text=True, timeout=10)
        self.assertEqual(process.returncode, 0, process.stderr)

    def test_paths_follow_users_codex_and_xdg_configuration(self):
        home = self.root / "home de outro usuário"
        self.assertEqual(installer.skills_root({}, home), home / ".codex/skills")
        self.assertEqual(installer.skills_root({"CODEX_HOME": str(self.root / "custom")}, home),
                         self.root / "custom/skills")
        self.assertEqual(installer.data_root({"XDG_DATA_HOME": "relative-invalid"}, home),
                         home / ".local/share" / installer.NAME)
        self.assertEqual(installer.data_root({"XDG_DATA_HOME": str(self.root / "data")}, home),
                         self.root / "data" / installer.NAME)


class CapabilityTests(unittest.TestCase):
    def test_stale_hyprland_variable_does_not_override_actual_desktop(self):
        for name, expected in [("GNOME", "gnome"), ("KDE", "kde"), ("Xfce", "other")]:
            self.assertEqual(desktop.desktop_kind({"XDG_CURRENT_DESKTOP": name,
                             "HYPRLAND_INSTANCE_SIGNATURE": "stale"}), expected)
        self.assertEqual(desktop.desktop_kind({"HYPRLAND_INSTANCE_SIGNATURE": "live"}), "hyprland")

    def test_each_desktop_is_a_candidate_not_a_claimed_success(self):
        for name in ["gnome", "kde", "hyprland"]:
            report = {"desktop": name, "session_type": "wayland", "native_binary": "/native"}
            result = desktop.readiness(report)
            self.assertEqual(result["status"], "requires-visual-test")
            self.assertFalse(result["gui_success_guaranteed"])
            self.assertFalse(result["model_name_required"])
            self.assertEqual(result["host_requirements"]["can_observe_images"],
                             "must verify in host/model")

    def test_headless_or_unknown_desktop_reports_blockers(self):
        for report in [{"desktop": "other", "session_type": None},
                       {"desktop": "gnome", "session_type": "wayland"}]:
            result = desktop.readiness(report)
            self.assertEqual(result["status"], "blocked")
            self.assertTrue(result["setup_blockers"])

    def test_native_failure_is_not_masked_by_executable_presence(self):
        report = {"desktop": "kde", "session_type": "wayland", "native_binary": "/native",
                  "native": {"error": "not executable on this architecture"}}
        self.assertEqual(desktop.readiness(report)["status"], "blocked")

    def test_detected_hyprland_route_does_not_need_optional_native(self):
        report = {"desktop": "hyprland", "session_type": "wayland",
                  "hyprland_fallback_detected": {"capture": True, "keyboard": True, "pointer": True}}
        result = desktop.readiness(report)
        self.assertEqual(result["candidate_route"], "hyprland-direct")
        self.assertEqual(result["status"], "requires-visual-test")

    def test_stalled_wayland_probe_is_bounded_and_remains_unverified(self):
        with patch.dict(os.environ, {"WAYLAND_DISPLAY": "broken", "XDG_CURRENT_DESKTOP": "other"}), \
             patch.object(desktop, "native_binary", return_value=None), \
             patch.object(desktop, "run", side_effect=subprocess.TimeoutExpired("protocols", 5)) as run:
            result = desktop.doctor()
        self.assertIn("error", result["wayland_protocols"])
        self.assertEqual(run.call_args.kwargs["timeout"], 5)
        self.assertFalse(result["compatibility"]["gui_success_guaranteed"])


if __name__ == "__main__":
    unittest.main()
