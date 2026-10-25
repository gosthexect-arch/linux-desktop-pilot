#!/usr/bin/env python3
"""Build a reproducible public distribution from an explicit source allowlist."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = ["README.md", "README.pt-BR.md", "LICENSE", "THIRD_PARTY_NOTICES.md",
         "CONTRIBUTING.md", "VERSION"]
TREES = ["linux-visual-computer-use", "tests", "tools", "docs"]


def sources(root=ROOT):
    selected = [root / name for name in FILES]
    for name in TREES:
        selected.extend(path for path in (root / name).rglob("*")
                        if (path.is_file() or path.is_symlink())
                        and "__pycache__" not in path.parts and path.suffix != ".pyc")
    for path in selected:
        if path.is_symlink() or not path.is_file():
            raise ValueError("invalid release source: " + str(path))
    return sorted(set(selected))


def build(output, root=ROOT):
    version = (root / "VERSION").read_text().strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[a-z0-9.]+)?", version):
        raise ValueError("invalid VERSION")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"linux-desktop-pilot-v{version}.zip"
    selected = sources(root)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as stream:
        for path in selected:
            relative = path.relative_to(root).as_posix()
            entry = zipfile.ZipInfo("linux-desktop-pilot/" + relative,
                                    date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            mode = 0o755 if path.stat().st_mode & stat.S_IXUSR else 0o644
            entry.create_system = 3
            entry.external_attr = (stat.S_IFREG | mode) << 16
            stream.writestr(entry, path.read_bytes())
    with zipfile.ZipFile(archive) as stream:
        if stream.testzip() is not None:
            raise RuntimeError("release archive verification failed")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum = archive.with_suffix(".zip.sha256")
    checksum.write_text(digest + "  " + archive.name + "\n")
    return {"version": version, "archive": str(archive.resolve()),
            "checksum": str(checksum.resolve()), "sha256": digest, "files": len(selected)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    print(json.dumps(build(args.output_dir), indent=2))


if __name__ == "__main__":
    main()
