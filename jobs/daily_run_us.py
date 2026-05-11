#!/usr/bin/env python3
"""
Investment OS — US Market Daily Run (scaffold)

Usage:
    python3 -m jobs.daily_run_us

Reads:  data/candidates_us.json  (must be populated before this script produces real output)
Writes: data/processed/signal_snapshot.json, data/processed/mainline_snapshot.json

No-ops gracefully when candidates_us.json is absent or empty.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CANDIDATES_US = ROOT / "data" / "candidates_us.json"


def main() -> int:
    if not CANDIDATES_US.exists():
        print("[INFO] candidates_us.json not found — skipping US run")
        return 0

    try:
        candidates = json.loads(CANDIDATES_US.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[WARN] Could not read candidates_us.json: {e}")
        return 1

    if not candidates:
        print("[INFO] candidates_us.json is empty — skipping US run")
        return 0

    print(f"[INFO] US run: {len(candidates)} candidates loaded (scaffold — implement US data logic here)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
