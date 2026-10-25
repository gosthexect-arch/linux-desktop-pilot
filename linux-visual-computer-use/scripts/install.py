#!/usr/bin/env python3
"""Install this skill for the current user, without desktop/configuration changes."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import uuid

NAME = "linux-visual-computer-use"
NATIVE_PACKAGE = "@agent-sh/computer-use-linux@0.7.25"
REQUIRED = ["SKILL.md", "agents/openai.yaml", "scripts/desktop.py", "scripts/wayland_io.py"]


def skills_root(env=None, home=None):
    env = os.environ if env is None else env
    home = Path.home() if home is None else Path(home)
    codex = env.get("CODEX_HOME")
    return (Path(codex).expanduser() if codex else home / ".codex") / "skills"


def data_root(env=None, home=None):
    env = os.environ if env is None else env
    home = Path.home() if home is None else Path(home)
    xdg = env.get("XDG_DATA_HOME", "")
    base = Path(xdg) if xdg and Path(xdg).is_absolute() else home / ".local/share"
    return base / NAME


def payload(root):
    root = Path(root)
    files = {}
    for path in sorted(root.rglob("*")):
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        if path.is_symlink():
            raise ValueError("skill payload contains a symlink: " + str(path))
        if path.is_file():
            files[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return files


def validate_source(source):
    for relative in REQUIRED:
        if not (source / relative).is_file():
            raise ValueError("incomplete skill payload: " + relative)
    name = re.search(r"^name:\s*[\"']?([a-z0-9-]+)[\"']?\s*$",
                     (source / "SKILL.md").read_text(), flags=re.MULTILINE)
    if not name or name.group(1) != NAME:
        raise ValueError("source is not the expected skill")
    return payload(source)


def install(source, skills_dir):
    source, skills_dir = Path(source).resolve(), Path(skills_dir).expanduser().resolve()
    source_files = validate_source(source)
    target = skills_dir / NAME
    if target == source:
        return {"status": "already-installed", "target": str(target), "backup": None}
    if target.is_relative_to(source):
        raise ValueError("installation target cannot be nested inside the source skill")
    if target.is_symlink():
        raise ValueError("installation target is a symlink; select another skills directory")
    if target.exists():
        validate_source(target)  # Do not replace an unrelated/incomplete directory.
        if payload(target) == source_files:
            return {"status": "unchanged", "target": str(target), "backup": None}
    skills_dir.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".lvcu-install-", dir=skills_dir))
    backup = None
    try:
        stage = staging / NAME
        shutil.copytree(source, stage, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        if payload(stage) != source_files:
            raise RuntimeError("source changed during installation; no installation performed")
        if target.exists():
            backup_dir = skills_dir.parent / "skill-backups"
            backup_dir.mkdir(exist_ok=True, mode=0o700)
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            backup = backup_dir / (NAME + "-" + stamp + "-" + uuid.uuid4().hex[:8])
            target.rename(backup)
        try:
            stage.rename(target)
        except BaseException:
            if backup is not None and not target.exists():
                backup.rename(target)
            raise
    finally:
        shutil.rmtree(staging)
    return {"status": "updated" if backup else "installed", "target": str(target),
            "backup": str(backup) if backup else None, "files": len(source_files)}


def install_native(directory):
    if platform.system() != "Linux" or platform.machine().lower() not in {
            "x86_64", "amd64", "aarch64", "arm64"}:
        raise RuntimeError("optional native runtime requires Linux x86_64 or arm64")
    npm = shutil.which("npm")
    if not npm:
        raise RuntimeError("npm unavailable; skill is installed, optional native runtime is not")
    runtime = directory / "runtime"
    subprocess.run([npm, "install", "--prefix", str(runtime), "--omit=optional",
                    "--no-audit", "--no-fund", NATIVE_PACKAGE], check=True,
                   stdout=sys.stderr, stderr=sys.stderr, timeout=300)
    binary = runtime / "node_modules/.bin/computer-use-linux"
    subprocess.run([str(binary), "--help"], check=True, stdout=subprocess.DEVNULL,
                   stderr=sys.stderr, timeout=15)
    return {"package": NATIVE_PACKAGE, "binary": str(binary), "gui_verified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills-dir", type=Path, default=skills_root(),
                        help="parent directory for the installed skill")
    parser.add_argument("--with-native", action="store_true",
                        help="also download the pinned optional Linux MCP runtime")
    args = parser.parse_args()
    result = None
    try:
        if sys.version_info < (3, 9):
            raise RuntimeError("Python 3.9 or newer is required")
        result = install(Path(__file__).resolve().parents[1], args.skills_dir)
        script = str(Path(result["target"]) / "scripts/desktop.py")
        result["commands"] = {"doctor": [sys.executable, script, "doctor"],
                              "native_tools": [sys.executable, script, "native", "tools"]}
        if args.with_native:
            result["native"] = install_native(data_root())
        result["next"] = "Run doctor, check host vision/tools, then perform visual acceptance tests"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(json.dumps({"error": str(error), "skill_installation": result,
                          "gui_verified": False}, ensure_ascii=False),
              file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
