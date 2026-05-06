# P1 Entry Audit — 2026-05-07

## Source

- Snapshot: `data/processed/mainline_snapshot.json`
- Snapshot generated at: `2026-05-05T11:14:34.929696`
- Audit generated at: `2026-05-07T00:12:17.672633`
- Capital: `100,000`

## Market Context

| Market State | VIX |
| --- | --- |
| **BULL** | 18.29 |

## Purpose

This audit report is **advisory only**.
It does not execute trades and does not change any runtime decisions.
`execution/risk.py` remains the active runtime risk gate.
`pipeline/main_v1.py` decisions are unchanged.

## Audit Summary

| Metric | Value |
| --- | --- |
| Data source | `RELOADED` |
| Total signals | 10 |
| EntryLock PASS | 0 |
| EntryLock WARN | 0 |
| EntryLock BLOCK | 10 |
| EntryLock SKIP | 0 |
| TradeSetup VALID | 10 |
| TradeSetup INVALID | 0 |
| TradeSetup INSUFFICIENT | 0 |
| Sizing feasible | 10 |
| P1 ENTRY | 0 |
| P1 ENTRY_REDUCED | 0 |
| P1 WAIT | 10 |
| P1 SKIP | 0 |
| P1 DATA_UNAVAILABLE | 0 |
| Divergences | **8** |

## Entry Lock Results (L0–L4)

| # | ticker | name | signal | level | L0 | L1 | L2 | L3 | L4 | status | p1_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 6830.TW | 汎銓 | BUY | READY | ✅ | ✅ | 🚫 | 🚫 | 🚫 | **BLOCK** | 🚫 WAIT |
| 2 | 6187.TWO | 萬潤 | BUY | READY | ✅ | ✅ | 🚫 | 🚫 | 🚫 | **BLOCK** | 🚫 WAIT |
| 3 | 3711.TW | 日月光投控 | BUY | READY | ✅ | ✅ | 🚫 | 🚫 | 🚫 | **BLOCK** | 🚫 WAIT |
| 4 | 2449.TW | 京元電子 | BUY | READY | ✅ | ✅ | 🚫 | 🚫 | 🚫 | **BLOCK** | 🚫 WAIT |
| 5 | 6239.TW | 力成 | BUY | READY | ✅ | ✅ | 🚫 | 🚫 | 🚫 | **BLOCK** | 🚫 WAIT |
| 6 | 6147.TWO | 頎邦 | BUY | READY | ✅ | ✅ | 🚫 | 🚫 | 🚫 | **BLOCK** | 🚫 WAIT |
| 7 | 6257.TW | 矽格 | BUY | READY | ✅ | ✅ | 🚫 | 🚫 | 🚫 | **BLOCK** | 🚫 WAIT |
| 8 | 3706.TW | 神達 | BUY | READY | ✅ | ✅ | 🚫 | 🚫 | 🚫 | **BLOCK** | 🚫 WAIT |
| 9 | 2313.TW | 華通 | BUY | READY | ✅ | ✅ | 🚫 | 🚫 | 🚫 | **BLOCK** | 🚫 WAIT |
| 10 | 3443.TW | 創意 | BUY | READY | ✅ | ✅ | 🚫 | 🚫 | 🚫 | **BLOCK** | 🚫 WAIT |

## Trade Setup Results

| ticker | setup_type | entry_zone | stop | T1 | T2 | R/R | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 6830.TW | VCP_BREAKOUT | 925.0000 | 878.7500 | 1017.5000 | 1110.0000 | 2.0000 | VALID |
| 6187.TWO | VCP_BREAKOUT | 1390.0000 | 1320.5000 | 1529.0000 | 1668.0000 | 2.0000 | VALID |
| 3711.TW | VCP_BREAKOUT | 525.0000 | 498.7500 | 577.5000 | 630.0000 | 2.0000 | VALID |
| 2449.TW | VCP_BREAKOUT | 332.5000 | 315.8750 | 365.7500 | 399.0000 | 2.0000 | VALID |
| 6239.TW | VCP_BREAKOUT | 223.0000 | 211.8500 | 245.3000 | 267.6000 | 2.0000 | VALID |
| 6147.TWO | VCP_BREAKOUT | 179.0000 | 170.0500 | 196.9000 | 214.8000 | 2.0000 | VALID |
| 6257.TW | VCP_BREAKOUT | 190.5000 | 180.9750 | 209.5500 | 228.6000 | 2.0000 | VALID |
| 3706.TW | VCP_BREAKOUT | 85.3000 | 81.0350 | 93.8300 | 102.3600 | 2.0000 | VALID |
| 2313.TW | VCP_BREAKOUT | 268.5000 | 255.0750 | 295.3500 | 322.2000 | 2.0000 | VALID |
| 3443.TW | VCP_BREAKOUT | 4685.0000 | 4450.7500 | 5153.5000 | 5622.0000 | 2.0000 | VALID |

## Position Sizing Results

| ticker | shares | value | pct% | max_loss | risk/share | feasible |
| --- | --- | --- | --- | --- | --- | --- |
| 6830.TW | 21 | 19425.0000 | 19.43% | 1000.0000 | 46.2500 | ✅ |
| 6187.TWO | 14 | 19460.0000 | 19.46% | 1000.0000 | 69.5000 | ✅ |
| 3711.TW | 38 | 19950.0000 | 19.95% | 1000.0000 | 26.2500 | ✅ |
| 2449.TW | 60 | 19950.0000 | 19.95% | 1000.0000 | 16.6250 | ✅ |
| 6239.TW | 89 | 19847.0000 | 19.85% | 1000.0000 | 11.1500 | ✅ |
| 6147.TWO | 111 | 19869.0000 | 19.87% | 1000.0000 | 8.9500 | ✅ |
| 6257.TW | 104 | 19812.0000 | 19.81% | 1000.0000 | 9.5250 | ✅ |
| 3706.TW | 234 | 19960.2000 | 19.96% | 1000.0000 | 4.2650 | ✅ |
| 2313.TW | 74 | 19869.0000 | 19.87% | 1000.0000 | 13.4250 | ✅ |
| 3443.TW | 4 | 18740.0000 | 18.74% | 1000.0000 | 234.2500 | ✅ |

## Pipeline Divergences

| ticker | name | p1_action | pipeline_action | flags |
| --- | --- | --- | --- | --- |
| 6830.TW | 汎銓 | WAIT | BUY | P0_BLOCK_vs_PIPELINE_BUY |
| 6187.TWO | 萬潤 | WAIT | - | NO_PIPELINE_DECISION |
| 6239.TW | 力成 | WAIT | - | NO_PIPELINE_DECISION |
| 6147.TWO | 頎邦 | WAIT | - | NO_PIPELINE_DECISION |
| 6257.TW | 矽格 | WAIT | - | NO_PIPELINE_DECISION |
| 3706.TW | 神達 | WAIT | - | NO_PIPELINE_DECISION |
| 2313.TW | 華通 | WAIT | - | NO_PIPELINE_DECISION |
| 3443.TW | 創意 | WAIT | - | NO_PIPELINE_DECISION |

## Risk Notes

- This report is advisory only. No automatic trade is executed.
- `execution/risk.py` is the active runtime risk gate and is NOT changed by this audit.
- `pipeline/main_v1.py` decisions are NOT changed.
- Divergence flags are informational. Manual review required before any action.
- `decision/risk_lock.py` is excluded from this audit (not yet reviewed for P1).

## Manual Action Checklist

- [ ] Review all WAIT / BLOCK entries before considering entry
- [ ] Review all ENTRY_REDUCED entries — consider reduced position size
- [ ] Investigate P0_BLOCK_vs_PIPELINE_BUY divergences
- [ ] Confirm no ticker-name mismatch in report
- [ ] Confirm this report does not trigger any direct execution
- [ ] Write manual decision notes before any trade