#!/usr/bin/env python3
"""Copy shared modules into each skill that bundles them.

Each ``skills/<naam>/bundle.txt`` lists paths (one per line, relative to
``shared/``). Blank lines and lines starting with ``#`` are ignored.
Every listed file is copied to ``skills/<naam>/scripts/<basename>``.

Usage:
    python3 tools/build.py            # copy
    python3 tools/build.py --check    # exit 1 if any copy is missing or differs
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHARED = ROOT / "shared"
SKILLS = ROOT / "skills"


def read_bundle(bundle: Path) -> list[str]:
    entries = []
    for raw in bundle.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            entries.append(line)
    return entries


def plan() -> tuple[list[tuple[Path, Path]], list[str]]:
    """Return (copies, errors). copies = [(source, target), ...]."""
    copies: list[tuple[Path, Path]] = []
    errors: list[str] = []
    for bundle in sorted(SKILLS.glob("*/bundle.txt")):
        skill_dir = bundle.parent
        for rel in read_bundle(bundle):
            src = (SHARED / rel).resolve()
            if SHARED.resolve() not in src.parents:
                errors.append(f"{bundle.relative_to(ROOT)}: pad buiten shared/: {rel}")
                continue
            if not src.is_file():
                errors.append(f"{bundle.relative_to(ROOT)}: bestand ontbreekt: shared/{rel}")
                continue
            copies.append((src, skill_dir / "scripts" / src.name))
    return copies, errors


def main() -> int:
    ap = argparse.ArgumentParser(description="Kopieer shared/-modules naar skills/<naam>/scripts/.")
    ap.add_argument("--check", action="store_true",
                    help="Niets kopiëren; faal als een kopie ontbreekt of afwijkt.")
    args = ap.parse_args()

    copies, errors = plan()
    for err in errors:
        print(f"FOUT: {err}", file=sys.stderr)
    if errors:
        return 2

    stale = []
    for src, dst in copies:
        same = dst.is_file() and dst.read_bytes() == src.read_bytes()
        if args.check:
            if not same:
                stale.append(dst)
            continue
        if not same:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            print(f"gekopieerd: shared/{src.relative_to(SHARED.resolve())} -> {dst.relative_to(ROOT)}")

    if args.check:
        for dst in stale:
            print(f"NIET SYNCHROON: {dst.relative_to(ROOT)} (draai python3 tools/build.py)", file=sys.stderr)
        if stale:
            return 1
        print(f"OK: {len(copies)} gebundelde kopieën zijn synchroon.")
        return 0
    print(f"klaar: {len(copies)} gebundelde bestanden gecontroleerd.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
