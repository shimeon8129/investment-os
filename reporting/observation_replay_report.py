#!/usr/bin/env python3
"""
Investment OS — Observation Replay Report v0.1

Usage:
    python3 -m reporting.observation_replay_report YYYY-MM-DD

Reads:  data/observations/daily/YYYY-MM-DD_observation_summary.json
Writes: reports/replay/YYYY-MM-DD_daily_replay.md

Reporting / observability only. Does NOT modify any trading logic.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _load_summary(date: str) -> dict:
    src = ROOT / "data" / "observations" / "daily" / f"{date}_observation_summary.json"
    if not src.exists():
        raise FileNotFoundError(f"Summary not found: {src}")
    return json.loads(src.read_text(encoding="utf-8"))


def _section_health(s: dict) -> list[str]:
    sc = s.get("status_counts", {})
    total = s.get("total_slots", 0)
    lines = [
        "## Daily Intraday Health",
        "",
        f"- Date: {s.get('date')}",
        f"- Total slots observed: {total}",
        f"- PASS: {sc.get('PASS', 0)}",
        f"- PARTIAL: {sc.get('PARTIAL', 0)}",
        f"- FAIL: {sc.get('FAIL', 0)}",
        f"- UNKNOWN: {sc.get('UNKNOWN', 0)}",
    ]
    if total == 0:
        lines += ["", "> **No slot observation data found for this date.**"]
    return lines


def _section_persistence(s: dict) -> list[str]:
    top = s.get("top_persistence", [])
    total = s.get("total_slots", 0)
    lines = ["", "## Top Candidate Persistence", ""]
    if not top:
        lines.append("_(no data)_")
        return lines
    lines += ["| Rank | Ticker | Appearances | Slots |", "|------|--------|-------------|-------|"]
    for i, item in enumerate(top, 1):
        pct = f"{item['appearances']}/{total}" if total else str(item["appearances"])
        lines.append(f"| {i} | {item['ticker']} | {item['appearances']} | {pct} |")
    return lines


def _section_rank_momentum(s: dict) -> list[str]:
    rank_trend = s.get("rank_trend", {})
    lines = ["", "## Rank Momentum", ""]
    if not rank_trend:
        lines.append("_(no data)_")
        return lines
    for ticker, records in sorted(rank_trend.items()):
        ranks = [r["rank"] for r in records if r["rank"] is not None]
        if not ranks:
            continue
        trend_str = " → ".join(str(r) for r in ranks)
        change = ranks[-1] - ranks[0] if len(ranks) >= 2 else 0
        direction = "↑ improving" if change < 0 else ("↓ worsening" if change > 0 else "→ stable")
        lines.append(f"- **{ticker}**: rank {trend_str} ({direction})")
    return lines


def _section_score_momentum(s: dict) -> list[str]:
    score_trend = s.get("score_trend", {})
    lines = ["", "## Score Momentum", ""]
    if not score_trend:
        lines.append("_(no data)_")
        return lines
    for ticker, records in sorted(score_trend.items()):
        scores = [r["score"] for r in records if r["score"] is not None]
        if not scores:
            continue
        try:
            trend_str = " → ".join(f"{float(sc):.1f}" for sc in scores)
            change = float(scores[-1]) - float(scores[0]) if len(scores) >= 2 else 0.0
            direction = "(↑ improving)" if change > 1 else ("(↓ worsening)" if change < -1 else "(→ stable)")
            lines.append(f"- **{ticker}**: {trend_str} {direction}")
        except (ValueError, TypeError):
            lines.append(f"- **{ticker}**: {scores}")
    return lines


def _section_p1_transitions(s: dict) -> list[str]:
    p1t = s.get("p1_transitions", {})
    lines = ["", "## P1 Transition Review", ""]
    if not p1t:
        lines.append("_(P1 audit data not available or no candidates)_")
        return lines
    for ticker, records in sorted(p1t.items()):
        actions = [r["p1_result"] for r in records if r["p1_result"] is not None]
        if not actions:
            continue
        unique_actions = list(dict.fromkeys(actions))
        changed = len(unique_actions) > 1
        flag = " ⚠ transition detected" if changed else ""
        lines.append(f"- **{ticker}**: {' → '.join(actions)}{flag}")
    return lines


def _section_l2_chase_risk(s: dict) -> list[str]:
    items = s.get("repeated_l2_block", [])
    lines = ["", "## L2 Chase-Risk Review", ""]
    if not items:
        lines.append("_(no repeated L2 BLOCK candidates)_")
        return lines
    lines.append("Candidates blocked by L2 (setup/chase-risk) in 2+ slots:")
    lines.append("")
    for item in items:
        reason = item.get("block_reason") or "N/A"
        lines.append(f"- **{item['ticker']}** — blocked {item['block_count']} slots | reason: {reason}")
    return lines


def _section_l3_volume(s: dict) -> list[str]:
    items = s.get("repeated_l3_block", [])
    lines = ["", "## L3 Volume Confirmation Review", ""]
    if not items:
        lines.append("_(no repeated L3 BLOCK candidates)_")
        return lines
    lines.append("Candidates blocked by L3 (price/volume validation) in 2+ slots:")
    lines.append("")
    for item in items:
        reason = item.get("block_reason") or "N/A"
        lines.append(f"- **{item['ticker']}** — blocked {item['block_count']} slots | reason: {reason}")
    return lines


def _section_watchlist(s: dict) -> list[str]:
    items = s.get("next_day_watchlist", [])
    lines = ["", "## Next Trading Day Watchlist", ""]
    if not items:
        lines.append(
            "_(no candidates qualify — appeared in <50% of slots, or all L3 blocked)_"
        )
        return lines
    lines += [
        "| Ticker | Name | Appearances | Last Rank | Last Score | Last P1 |",
        "|--------|------|-------------|-----------|------------|---------|",
    ]
    for item in items:
        name = item.get("name") or ""
        lines.append(
            f"| {item['ticker']} | {name} | {item['appearances']} "
            f"| {item.get('last_rank', 'N/A')} "
            f"| {item.get('last_score', 'N/A')} "
            f"| {item.get('last_p1', 'N/A')} |"
        )
    return lines


def _section_limitations() -> list[str]:
    return [
        "",
        "## Data Limitations",
        "",
        "- P1 audit data (`p1_audit_report.json`) is overwritten on each run; "
        "values reflect the most recent slot execution at observation time.",
        "- `already_in_position` field is not yet populated (requires live holdings cross-reference).",
        "- `manual_review_flag` field is not yet populated (requires signal parsing).",
        "- `data_as_of_date` may show `UNKNOWN` when upstream pipeline does not expose vintage.",
        "- Trend comparison across days requires ≥3 trading days of accumulated observation JSONs.",
        "- Backfill observation JSONs (generated from existing snapshots) do not contain L0–L4 "
        "data because `p1_audit_report.json` was not preserved per-slot.",
    ]


def build_report(date: str, summary: dict) -> str:
    lines: list[str] = [
        f"# Investment OS — Daily Replay Report: {date}",
        "",
        f"_Generated at: {summary.get('generated_at', 'N/A')}_",
        "",
    ]
    lines.extend(_section_health(summary))
    lines.extend(_section_persistence(summary))
    lines.extend(_section_rank_momentum(summary))
    lines.extend(_section_score_momentum(summary))
    lines.extend(_section_p1_transitions(summary))
    lines.extend(_section_l2_chase_risk(summary))
    lines.extend(_section_l3_volume(summary))
    lines.extend(_section_watchlist(summary))
    lines.extend(_section_limitations())
    return "\n".join(lines) + "\n"


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 -m reporting.observation_replay_report YYYY-MM-DD")
        return 1
    date = sys.argv[1]

    try:
        summary = _load_summary(date)
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        return 1

    report = build_report(date, summary)

    out_dir = ROOT / "reports" / "replay"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{date}_daily_replay.md"
    out_path.write_text(report, encoding="utf-8")
    print(f"[observation_replay_report] Written: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
