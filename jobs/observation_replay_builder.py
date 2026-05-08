#!/usr/bin/env python3
"""
Investment OS — Observation Replay Builder v0.1

Usage:
    python3 jobs/observation_replay_builder.py YYYY-MM-DD

Reads:  data/observations/intraday/YYYY-MM-DD/*_observation.json
Writes: data/observations/daily/YYYY-MM-DD_observation_summary.json

Reporting / observability only. Does NOT modify any trading logic.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _load_slots(date: str) -> list[dict]:
    src_dir = ROOT / "data" / "observations" / "intraday" / date
    if not src_dir.exists():
        return []
    files = sorted(src_dir.glob("*_observation.json"))
    slots = []
    for f in files:
        try:
            slots.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception as e:
            print(f"[WARN] Could not load {f}: {e}")
    return slots


def _status_counts(slots: list[dict]) -> dict:
    counts: dict[str, int] = {"PASS": 0, "PARTIAL": 0, "FAIL": 0, "UNKNOWN": 0}
    for s in slots:
        status = s.get("runtime_status", "UNKNOWN")
        counts[status] = counts.get(status, 0) + 1
    return counts


def _candidate_appearances(slots: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for s in slots:
        for c in s.get("candidates", []):
            ticker = c.get("ticker")
            if ticker:
                counts[ticker] += 1
    return dict(counts)


def _top_persistence(appearances: dict[str, int], n: int = 10) -> list[dict]:
    sorted_items = sorted(appearances.items(), key=lambda x: x[1], reverse=True)
    return [{"ticker": t, "appearances": cnt} for t, cnt in sorted_items[:n]]


def _rank_trend(slots: list[dict]) -> dict[str, list]:
    trend: dict[str, list] = defaultdict(list)
    for s in slots:
        slot_id = s.get("slot", "unknown")
        for c in s.get("candidates", []):
            ticker = c.get("ticker")
            if ticker:
                trend[ticker].append({"slot": slot_id, "rank": c.get("rank")})
    return dict(trend)


def _score_trend(slots: list[dict]) -> dict[str, list]:
    trend: dict[str, list] = defaultdict(list)
    for s in slots:
        slot_id = s.get("slot", "unknown")
        for c in s.get("candidates", []):
            ticker = c.get("ticker")
            if ticker:
                trend[ticker].append({"slot": slot_id, "score": c.get("score")})
    return dict(trend)


def _p1_transitions(slots: list[dict]) -> dict[str, list]:
    transitions: dict[str, list] = defaultdict(list)
    for s in slots:
        slot_id = s.get("slot", "unknown")
        for c in s.get("candidates", []):
            ticker = c.get("ticker")
            p1 = c.get("p1_result")
            if ticker and p1 is not None:
                transitions[ticker].append({"slot": slot_id, "p1_result": p1})
    return dict(transitions)


def _repeated_block(slots: list[dict], level: str) -> list[dict]:
    """Find tickers blocked at a given level (e.g. 'L2', 'L3') in 2+ slots."""
    block_counts: dict[str, int] = defaultdict(int)
    block_reasons: dict[str, str] = {}
    for s in slots:
        for c in s.get("candidates", []):
            ticker = c.get("ticker")
            if not ticker:
                continue
            if c.get(level) == "BLOCK":
                block_counts[ticker] += 1
                if c.get("block_reason"):
                    block_reasons[ticker] = c["block_reason"]
    return [
        {"ticker": t, "block_count": cnt, "block_reason": block_reasons.get(t)}
        for t, cnt in sorted(block_counts.items(), key=lambda x: x[1], reverse=True)
        if cnt >= 2
    ]


def _warn_with_l1_l4_pass(slots: list[dict]) -> list[dict]:
    """Candidates with L0 WARN but L1–L4 all PASS (potential near-miss entries)."""
    ticker_seen: dict[str, dict] = {}
    for s in slots:
        for c in s.get("candidates", []):
            ticker = c.get("ticker")
            if not ticker:
                continue
            if (
                c.get("L0") == "WARN"
                and c.get("L1") == "PASS"
                and c.get("L2") == "PASS"
                and c.get("L3") == "PASS"
                and c.get("L4") == "PASS"
            ):
                ticker_seen[ticker] = {
                    "ticker": ticker,
                    "name": c.get("name"),
                    "warn_reason": c.get("warn_reason"),
                    "score": c.get("score"),
                }
    return list(ticker_seen.values())


def _next_day_watchlist(
    slots: list[dict],
    appearances: dict[str, int],
    total_slots: int,
) -> list[dict]:
    """Candidates appearing in ≥50% of slots and not L3-blocked in the last slot."""
    if total_slots == 0:
        return []
    threshold = max(1, total_slots // 2)
    last_slot = slots[-1] if slots else {}
    last_blocked: set[str] = set()
    for c in last_slot.get("candidates", []):
        if c.get("L3") == "BLOCK":
            last_blocked.add(c.get("ticker", ""))

    watchlist = []
    for ticker, cnt in sorted(appearances.items(), key=lambda x: x[1], reverse=True):
        if cnt >= threshold and ticker not in last_blocked:
            latest = next(
                (c for c in last_slot.get("candidates", []) if c.get("ticker") == ticker),
                {},
            )
            watchlist.append({
                "ticker": ticker,
                "name": latest.get("name"),
                "appearances": cnt,
                "last_rank": latest.get("rank"),
                "last_score": latest.get("score"),
                "last_p1": latest.get("p1_result"),
            })
    return watchlist


def build_summary(date: str) -> dict:
    slots = _load_slots(date)
    total = len(slots)
    status_counts = _status_counts(slots)
    appearances = _candidate_appearances(slots)

    return {
        "date": date,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_slots": total,
        "status_counts": status_counts,
        "top_persistence": _top_persistence(appearances),
        "rank_trend": _rank_trend(slots),
        "score_trend": _score_trend(slots),
        "p1_transitions": _p1_transitions(slots),
        "repeated_l2_block": _repeated_block(slots, "L2"),
        "repeated_l3_block": _repeated_block(slots, "L3"),
        "warn_l1_l4_pass": _warn_with_l1_l4_pass(slots),
        "next_day_watchlist": _next_day_watchlist(slots, appearances, total),
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 jobs/observation_replay_builder.py YYYY-MM-DD")
        return 1
    date = sys.argv[1]

    print(f"[observation_replay_builder] Building summary for {date}...")
    summary = build_summary(date)

    out_dir = ROOT / "data" / "observations" / "daily"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{date}_observation_summary.json"
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[observation_replay_builder] Written: {out_path}")
    print(f"[observation_replay_builder] total_slots={summary['total_slots']} status={summary['status_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
