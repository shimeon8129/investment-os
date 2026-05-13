# Observation Replay & Trend Review Layer v0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在每次 intraday slot 執行後寫出正規化 observation JSON，並提供跨 slot 的每日回放摘要與趨勢報告，使系統在 3–10 個交易日後可比較候選人持續性、排名變化、P1 轉換等。

**Architecture:** 三層結構：(1) `intraday_observation.py` 在現有 slot 執行後寫 `HHMM_<slot>_observation.json`；(2) `observation_replay_builder.py` 讀取當日所有 slot JSONs 生成每日彙總；(3) `observation_replay_report.py` 將彙總 JSON 轉為 Markdown 報告。Shell script 統一執行後兩步。

**Tech Stack:** Python 3.12, stdlib only (json, pathlib, subprocess, re, datetime, collections), bash

---

## 資料來源對照

| 欄位 | 來源 |
|------|------|
| market_* | `data/processed/intraday/DATE/HHMM_signal_snapshot.json` |
| candidates rank/score/signal | `data/processed/intraday/DATE/HHMM_mainline_snapshot.json["ranked"]` |
| L0–L4 / block_reason / p1_result | `data/processed/p1_audit_report.json["audit_entries"]` (snapshot 時間最近的) |
| runtime_status / git_commit | 由 `intraday_observation.py` 計算傳入 |

**注意：** P1 audit JSON (`p1_audit_report.json`) 每次 slot 執行後即被覆蓋，因此 `intraday_observation.py` 必須在 `_run_daily()` 返回後立刻讀取，並將結果嵌入 observation JSON。

---

## 目錄結構（執行後新增的路徑）

```
data/observations/intraday/YYYY-MM-DD/HHMM_<slot>_observation.json   ← Task 1
data/observations/daily/YYYY-MM-DD_observation_summary.json           ← Task 2
reports/replay/YYYY-MM-DD_daily_replay.md                             ← Task 3
scripts/run_observation_replay.sh                                      ← Task 4
```

---

## Task 1: 在 intraday_observation.py 寫入正規化 observation JSON

**Files:**
- Modify: `jobs/intraday_observation.py`

### 背景
`intraday_observation.py` 已有 `signal_snap`、`mainline_snap`、`p1_snap` 三個字典（main() 內 step 4）。
只需新增一個 helper `_build_observation_json()` 並在 step 5（複製 snapshots）之後呼叫它。

- [ ] **Step 1: 讀取現有檔案（已在先前步驟讀取，再確認一次 main() 流程）**

確認 `jobs/intraday_observation.py` main() 中 step 4 讀取了：
- `signal_snap` ← `signal_snapshot.json`
- `mainline_snap` ← `mainline_snapshot.json`
- `p1_snap` ← `p1_audit_report.json`

現有流程已滿足需求，無需新增讀取邏輯。

- [ ] **Step 2: 新增 `_build_observation_json()` helper 函式**

在 `jobs/intraday_observation.py` 的 `# ─── Report builder ───` 區塊**之前**插入以下函式（約在第 197 行前）：

```python
# ─────────────────────────────────────────────────────────────────────────────
# Observation JSON builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_p1_index(p1_snap: dict) -> dict:
    """Return dict keyed by ticker for O(1) lookup of P1 audit fields."""
    index: dict = {}
    for entry in p1_snap.get("audit_entries", []):
        ticker = entry.get("ticker")
        if not ticker:
            continue
        el = entry.get("entry_lock", {})
        locks = el.get("locks", {})
        index[ticker] = {
            "p1_result": entry.get("p1_audit_action"),
            "L0": locks.get("L0_market", {}).get("status"),
            "L1": locks.get("L1_selection", {}).get("status"),
            "L2": locks.get("L2_setup", {}).get("status"),
            "L3": locks.get("L3_validation", {}).get("status"),
            "L4": locks.get("L4_risk", {}).get("status"),
            "block_reason": (
                locks.get(f"L{el.get('blocked_by', [None])[0].lstrip('L').split('_')[0] if el.get('blocked_by') else ''}", {}).get("reason")
                if el.get("blocked_by") else None
            ),
            "warn_reason": locks.get("L0_market", {}).get("reason") if locks.get("L0_market", {}).get("status") == "WARN" else None,
        }
    return index


def _build_observation_json(
    slot: str,
    git_before: dict,
    runtime_status: str,
    signal_snap: dict,
    mainline_snap: dict,
    p1_snap: dict,
) -> dict:
    """Build normalized observation dict for a single slot run."""
    mc = signal_snap.get("market_context", {})
    markets = mc.get("markets", {})
    tw = markets.get("TW", {})
    tw_status = tw.get("status") if isinstance(tw, dict) else str(tw)

    market = {
        "market_status": tw_status,
        "market_state": signal_snap.get("market_state"),
        "market_score": signal_snap.get("market_score"),
        "vix": signal_snap.get("vix_value"),
        "report_label": signal_snap.get("report_label"),
        "data_as_of_date": signal_snap.get("data_as_of_date"),
        "latest_full_trading_day": signal_snap.get("latest_full_trading_day"),
    }
    # Fill None → "N/A"
    market = {k: ("N/A" if v is None else v) for k, v in market.items()}

    p1_index = _build_p1_index(p1_snap)
    ranked = mainline_snap.get("ranked", [])

    candidates = []
    for rank, row in enumerate(ranked, 1):
        ticker = row.get("ticker", "")
        p1 = p1_index.get(ticker, {})
        candidates.append({
            "ticker": ticker,
            "name": row.get("name"),
            "rank": rank,
            "score": row.get("score"),
            "signal": row.get("signal"),
            "p1_result": p1.get("p1_result"),
            "L0": p1.get("L0"),
            "L1": p1.get("L1"),
            "L2": p1.get("L2"),
            "L3": p1.get("L3"),
            "L4": p1.get("L4"),
            "block_reason": p1.get("block_reason"),
            "warn_reason": p1.get("warn_reason"),
            "already_in_position": None,
            "manual_review_flag": None,
        })

    return {
        "date": TODAY,
        "slot": slot,
        "run_time": NOW,
        "git_commit": git_before.get("latest_commit"),
        "runtime_status": runtime_status,
        "market": market,
        "candidates": candidates,
    }
```

- [ ] **Step 3: 在 main() 中呼叫 `_build_observation_json()` 並寫入 JSON 檔案**

在 `main()` 中找到這段（約在第 398 行）：
```python
    runtime_status = _compute_runtime_status(returncode, output)
    snap_fields = _read_snapshot_fields(signal_snap)
```

在這段之後、`slot_report = _build_slot_report(...)` 之前，新增：

```python
    # 8. Write normalized observation JSON
    obs_dir = ROOT / "data" / "observations" / "intraday" / TODAY
    obs_dir.mkdir(parents=True, exist_ok=True)
    obs_path = obs_dir / f"{HHMM}_{slot}_observation.json"
    try:
        obs_data = _build_observation_json(
            slot=slot,
            git_before=git_before,
            runtime_status=runtime_status,
            signal_snap=signal_snap,
            mainline_snap=mainline_snap,
            p1_snap=p1_snap,
        )
        obs_path.write_text(json.dumps(obs_data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[{NOW}] [WRITE] {obs_path}")
    except Exception as e:
        print(f"[{NOW}] [WARN] Could not write observation JSON: {e}")
```

- [ ] **Step 4: 驗證語法**

```bash
python3 -m py_compile jobs/intraday_observation.py && echo "OK"
```

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add jobs/intraday_observation.py
git commit -m "feat(observation): write normalized slot observation JSON per run"
```

---

## Task 2: 新增 jobs/observation_replay_builder.py

**Files:**
- Create: `jobs/observation_replay_builder.py`

此腳本讀取指定日期的所有 slot observation JSON，計算跨 slot 趨勢統計，並寫出每日彙總 JSON。

- [ ] **Step 1: 建立 `jobs/observation_replay_builder.py`**

```python
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
    """Find tickers blocked at a given level (e.g. 'L2', 'L3') in multiple slots."""
    block_counts: dict[str, int] = defaultdict(int)
    block_reasons: dict[str, str] = {}
    for s in slots:
        for c in s.get("candidates", []):
            ticker = c.get("ticker")
            if not ticker:
                continue
            lv_status = c.get(level)
            if lv_status == "BLOCK":
                block_counts[ticker] += 1
                if c.get("block_reason"):
                    block_reasons[ticker] = c["block_reason"]
    return [
        {"ticker": t, "block_count": cnt, "block_reason": block_reasons.get(t)}
        for t, cnt in sorted(block_counts.items(), key=lambda x: x[1], reverse=True)
        if cnt >= 2
    ]


def _warn_with_l1_l4_pass(slots: list[dict]) -> list[dict]:
    """Candidates with L0 WARN but L1–L4 all PASS."""
    ticker_set: dict[str, dict] = {}
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
                ticker_set[ticker] = {
                    "ticker": ticker,
                    "name": c.get("name"),
                    "warn_reason": c.get("warn_reason"),
                    "score": c.get("score"),
                }
    return list(ticker_set.values())


def _next_day_watchlist(
    slots: list[dict],
    appearances: dict[str, int],
    total_slots: int,
) -> list[dict]:
    """
    Candidates appearing in ≥50% of slots and not L3-blocked in the last slot.
    Sorted by appearance count desc.
    """
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
            # Grab latest score and rank from last slot
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
```

- [ ] **Step 2: 驗證語法**

```bash
python3 -m py_compile jobs/observation_replay_builder.py && echo "OK"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add jobs/observation_replay_builder.py
git commit -m "feat(observation): add observation replay builder v0.1"
```

---

## Task 3: 新增 reporting/observation_replay_report.py

**Files:**
- Create: `reporting/observation_replay_report.py`

此模組讀取每日彙總 JSON，輸出 Markdown 報告至 `reports/replay/YYYY-MM-DD_daily_replay.md`。

- [ ] **Step 1: 建立 `reporting/observation_replay_report.py`**

```python
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
        lines.append("")
        lines.append("> **No slot observation data found for this date.**")
    return lines


def _section_persistence(s: dict) -> list[str]:
    top = s.get("top_persistence", [])
    total = s.get("total_slots", 0)
    lines = ["", "## Top Candidate Persistence", ""]
    if not top:
        lines.append("_(no data)_")
        return lines
    lines.append(f"| Rank | Ticker | Appearances | Slots |")
    lines.append(f"|------|--------|-------------|-------|")
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
    # Only show tickers with rank variation
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
            direction = "↑" if change > 1 else ("↓" if change < -1 else "→")
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
        lines.append("_(no candidates qualify — appeared in <50% of slots, or all L3 blocked)_")
        return lines
    lines.append("| Ticker | Name | Appearances | Last Rank | Last Score | Last P1 |")
    lines.append("|--------|------|-------------|-----------|------------|---------|")
    for item in items:
        name = item.get("name") or ""
        lines.append(
            f"| {item['ticker']} | {name} | {item['appearances']} "
            f"| {item.get('last_rank', 'N/A')} "
            f"| {item.get('last_score', 'N/A')} "
            f"| {item.get('last_p1', 'N/A')} |"
        )
    return lines


def _section_limitations(s: dict) -> list[str]:
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
    ]


def build_report(date: str, summary: dict) -> str:
    lines: list[str] = [
        f"# Investment OS — Daily Replay Report: {date}",
        "",
        f"_Generated at: {summary.get('generated_at', 'N/A')}_",
        "",
    ]
    sections = [
        _section_health,
        _section_persistence,
        _section_rank_momentum,
        _section_score_momentum,
        _section_p1_transitions,
        _section_l2_chase_risk,
        _section_l3_volume,
        _section_watchlist,
        _section_limitations,
    ]
    for fn in sections:
        lines.extend(fn(summary))

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
```

- [ ] **Step 2: 驗證語法**

```bash
python3 -m py_compile reporting/observation_replay_report.py && echo "OK"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add reporting/observation_replay_report.py
git commit -m "feat(observation): add observation replay report generator v0.1"
```

---

## Task 4: 新增 scripts/run_observation_replay.sh

**Files:**
- Create: `scripts/run_observation_replay.sh`

- [ ] **Step 1: 建立 shell script**

```bash
#!/usr/bin/env bash
# Investment OS — Run Observation Replay for a given trading date
#
# Usage: scripts/run_observation_replay.sh YYYY-MM-DD

set -euo pipefail

DATE="${1:-}"
if [[ -z "$DATE" ]]; then
    echo "Usage: $0 YYYY-MM-DD" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"

PYTHON="${ROOT}/venv/bin/python3"
if [[ ! -x "$PYTHON" ]]; then
    PYTHON="python3"
fi

echo "[run_observation_replay] DATE=${DATE}"
echo "[run_observation_replay] Step 1: Build daily observation summary..."
PYTHONPATH="$ROOT" "$PYTHON" "$ROOT/jobs/observation_replay_builder.py" "$DATE"

echo "[run_observation_replay] Step 2: Generate replay report..."
PYTHONPATH="$ROOT" "$PYTHON" -m reporting.observation_replay_report "$DATE"

echo "[run_observation_replay] Done."
```

- [ ] **Step 2: 設定執行權限並驗證 bash 語法**

```bash
chmod +x scripts/run_observation_replay.sh
bash -n scripts/run_observation_replay.sh && echo "OK"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add scripts/run_observation_replay.sh
git commit -m "feat(observation): add run_observation_replay.sh script"
```

---

## Task 5: 完整驗證與手動測試

**Note:** 此 task 的前提是 `data/processed/intraday/2026-05-08/` 已有現存 snapshot 數據，但尚未有 `data/observations/intraday/2026-05-08/` 資料（因為 Task 1 修改了 `intraday_observation.py`，新 slot 執行才會生成）。手動測試需要先從現有 snapshots 補填 observation JSONs，或直接以現有 snapshot 資料測試 replay builder。

- [ ] **Step 1: 全部 py_compile 驗證**

```bash
cd /home/shimeon/investment_os
python3 -m py_compile jobs/intraday_observation.py && echo "intraday_observation: OK"
python3 -m py_compile jobs/observation_replay_builder.py && echo "replay_builder: OK"
python3 -m py_compile reporting/observation_replay_report.py && echo "replay_report: OK"
bash -n scripts/run_observation_replay.sh && echo "shell: OK"
```

Expected: 四行 `OK`

- [ ] **Step 2: 從現有 snapshots 手動補填 2026-05-08 observation JSONs**

執行以下 Python one-liner 從已有的 `data/processed/intraday/2026-05-08/` snapshots 補填 observation JSONs（供測試用）：

```bash
cd /home/shimeon/investment_os && python3 - <<'PYEOF'
import json, sys
from pathlib import Path
from datetime import datetime

ROOT = Path(".")
DATE = "2026-05-08"
SRC = ROOT / "data" / "processed" / "intraday" / DATE
OBS_DIR = ROOT / "data" / "observations" / "intraday" / DATE
OBS_DIR.mkdir(parents=True, exist_ok=True)

SLOT_MAP = {
    "0058": "market_open", "0102": "pre_market", "0103": "market_open",
    "0107": "market_open", "0110": "market_open", "0830": "pre_market",
    "0840": "pre_market", "0915": "market_open", "1040": "mid_morning",
    "1210": "noon_review", "1320": "pre_close", "1440": "post_close_review",
}

for hhmm, slot in SLOT_MAP.items():
    sig_f = SRC / f"{hhmm}_signal_snapshot.json"
    ml_f  = SRC / f"{hhmm}_mainline_snapshot.json"
    if not sig_f.exists() or not ml_f.exists():
        continue
    sig = json.loads(sig_f.read_text())
    ml  = json.loads(ml_f.read_text())
    mc = sig.get("market_context", {})
    tw = mc.get("markets", {}).get("TW", {})
    market = {
        "market_status": tw.get("status") if isinstance(tw, dict) else str(tw),
        "market_state": sig.get("market_state", "N/A"),
        "market_score": sig.get("market_score", "N/A"),
        "vix": sig.get("vix_value", "N/A"),
        "report_label": sig.get("report_label", "N/A"),
        "data_as_of_date": sig.get("data_as_of_date", "N/A"),
        "latest_full_trading_day": sig.get("latest_full_trading_day", "N/A"),
    }
    candidates = []
    for rank, row in enumerate(ml.get("ranked", []), 1):
        candidates.append({
            "ticker": row.get("ticker"),
            "name": row.get("name"),
            "rank": rank,
            "score": row.get("score"),
            "signal": row.get("signal"),
            "p1_result": None, "L0": None, "L1": None, "L2": None,
            "L3": None, "L4": None, "block_reason": None,
            "warn_reason": None, "already_in_position": None, "manual_review_flag": None,
        })
    obs = {
        "date": DATE, "slot": slot,
        "run_time": f"{DATE} {hhmm[:2]}:{hhmm[2:]}:00",
        "git_commit": "backfill", "runtime_status": "PASS",
        "market": market, "candidates": candidates,
    }
    out = OBS_DIR / f"{hhmm}_{slot}_observation.json"
    out.write_text(json.dumps(obs, ensure_ascii=False, indent=2))
    print(f"Written: {out}")
PYEOF
```

- [ ] **Step 3: 執行 run_observation_replay.sh**

```bash
cd /home/shimeon/investment_os && bash scripts/run_observation_replay.sh 2026-05-08
```

Expected outputs:
- `data/observations/daily/2026-05-08_observation_summary.json`
- `reports/replay/2026-05-08_daily_replay.md`

- [ ] **Step 4: 確認輸出存在且非空**

```bash
ls -lh data/observations/daily/2026-05-08_observation_summary.json
ls -lh reports/replay/2026-05-08_daily_replay.md
python3 -c "import json; d=json.load(open('data/observations/daily/2026-05-08_observation_summary.json')); print('total_slots:', d['total_slots'])"
```

Expected: 兩個檔案存在，`total_slots` > 0

- [ ] **Step 5: 最終 Commit（若尚未 commit 各步驟）**

不 commit 生成的觀測資料、replay 報告、snapshots。

```bash
git status
# 確認只有實作檔案未 commit
git add jobs/intraday_observation.py jobs/observation_replay_builder.py reporting/observation_replay_report.py scripts/run_observation_replay.sh
git commit -m "feat(observation): add replayable intraday trend review layer v0.1"
```

---

## 自我審查（Spec Coverage）

| 需求 | 對應 Task |
|------|-----------|
| `intraday_observation.py` 寫 observation JSON | Task 1 |
| observation JSON 包含 market fields | Task 1 `_build_observation_json()` |
| observation JSON 包含 candidates + L0–L4 | Task 1 `_build_p1_index()` |
| `observation_replay_builder.py` | Task 2 |
| 彙總：total slots、PASS/PARTIAL/FAIL | Task 2 `_status_counts()` |
| 彙總：candidate appearance count、top 10 persistence | Task 2 `_top_persistence()` |
| 彙總：rank trend、score trend | Task 2 `_rank_trend()`, `_score_trend()` |
| 彙總：P1 transition、repeated L2/L3 BLOCK | Task 2 `_p1_transitions()`, `_repeated_block()` |
| 彙總：WARN + L1–L4 PASS | Task 2 `_warn_with_l1_l4_pass()` |
| 彙總：next-day watchlist | Task 2 `_next_day_watchlist()` |
| `observation_replay_report.py` | Task 3 |
| 報告包含所有指定 sections | Task 3 各 `_section_*()` |
| `run_observation_replay.sh YYYY-MM-DD` | Task 4 |
| py_compile 驗證 | Task 5 Step 1 |
| bash -n 驗證 | Task 5 Step 1 |
| 手動測試 + 驗證輸出路徑 | Task 5 Steps 2–4 |
| 不 commit 生成資料 | Task 5 Step 5 注意事項 |

## 已知限制

- `already_in_position` 需要 holdings cross-reference，目前設為 `null`
- `manual_review_flag` 需要 signal parsing，目前設為 `null`
- P1 audit 資料在每次 `daily_run` 後被覆蓋，backfill 的 observation JSON 無 L0–L4 資料
- 跨日趨勢比較需要至少 3 個交易日的積累
