#!/usr/bin/env python3
"""Prepara los archivos de una release: el VSIX, un zip solo con los temas de terminal y SHA256SUMS.

    python3 scripts/package.py && python3 scripts/release.py     # escribe en dist/
"""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    pkg = json.loads((ROOT / "package.json").read_text())
    vsix = ROOT / f"{pkg['name']}-{pkg['version']}.vsix"
    if not vsix.is_file():
        raise SystemExit(f"{vsix.name} not found: run scripts/package.py first")
    DIST.mkdir(exist_ok=True)
    for old in DIST.iterdir():
        old.unlink()
    terminals = DIST / f"{pkg['name']}-terminals-{pkg['version']}.zip"
    with zipfile.ZipFile(terminals, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted((ROOT / "terminals").rglob("*")):
            if path.is_file():
                info = zipfile.ZipInfo(f"{pkg['name']}-terminals/{path.relative_to(ROOT / 'terminals')}", (2020, 1, 1, 0, 0, 0))
                info.external_attr = (0o755 if path.name == "install.sh" else 0o644) << 16
                archive.writestr(info, path.read_bytes(), zipfile.ZIP_DEFLATED)
        for name in ("LICENSE.txt", "NOCTIS-LICENSE.md"):
            archive.write(ROOT / name, f"{pkg['name']}-terminals/{name}")
    (DIST / vsix.name).write_bytes(vsix.read_bytes())
    sums = "".join(f"{sha256(p)}  {p.name}\n" for p in sorted(DIST.iterdir()))
    (DIST / "SHA256SUMS").write_text(sums)
    print(sums, end="")


if __name__ == "__main__":
    main()
