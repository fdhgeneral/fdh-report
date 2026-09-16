#!/usr/bin/env python3
"""
FDH Hall of Fame — Full Build Runner
=====================================
Orchestrates the complete build pipeline:
  1. fetch_sleeper.py  — pull latest data from Sleeper API
  2. generate_site.py  — render all HTML pages from templates + data

Usage:
    python scripts/build.py [--skip-fetch] [--skip-generate]

Flags:
    --skip-fetch      Skip the Sleeper API fetch (use existing _data/)
    --skip-generate   Skip HTML generation (data fetch only)
    --dry-run         Print steps without executing
"""

import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT    = Path(__file__).parent.parent
SCRIPTS = ROOT / "scripts"
PYTHON  = sys.executable


def banner(msg: str):
    line = "=" * (len(msg) + 4)
    print(f"\n{line}\n  {msg}\n{line}")


def run(script: str, label: str) -> bool:
    banner(label)
    start = time.time()
    result = subprocess.run(
        [PYTHON, str(SCRIPTS / script)],
        cwd=ROOT,
        capture_output=False,
    )
    elapsed = time.time() - start
    if result.returncode != 0:
        print(f"\n❌ {label} FAILED (exit {result.returncode}) in {elapsed:.1f}s")
        return False
    print(f"\n✅ {label} completed in {elapsed:.1f}s")
    return True


def main():
    args = set(sys.argv[1:])
    skip_fetch    = "--skip-fetch"    in args
    skip_generate = "--skip-generate" in args
    dry_run       = "--dry-run"       in args

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"\n🏈 FDH Hall of Fame Build Pipeline")
    print(f"   Started: {ts}")
    print(f"   Root:    {ROOT}")

    if dry_run:
        print("\n[DRY RUN — no scripts executed]")
        if not skip_fetch:
            print("  → Would run: fetch_sleeper.py")
        if not skip_generate:
            print("  → Would run: generate_site.py")
        return

    success = True

    if not skip_fetch:
        ok = run("fetch_sleeper.py", "Step 1 — Fetch Sleeper Data")
        if not ok:
            print("\n⚠  Fetch failed — attempting generation with existing data...")
            success = False

    if not skip_generate:
        ok = run("generate_site.py", "Step 2 — Generate Static Site")
        if not ok:
            sys.exit(1)

    print(f"\n{'✅' if success else '⚠ '} Build pipeline finished at {datetime.now(timezone.utc).strftime('%H:%M UTC')}")
    print(f"   Output: {ROOT / 'site'}")


if __name__ == "__main__":
    main()
