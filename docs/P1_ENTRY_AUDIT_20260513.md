# P1 Entry Audit — 2026-05-13

## Source

- Snapshot: `data/processed/mainline_snapshot.json`
- Snapshot generated at: `2026-05-13T20:35:18.408083`
- Audit generated at: `2026-05-13T20:35:21.182866`
- Capital: `100,000`

## Market Context

| Market State | VIX |
| --- | --- |
| **RANGE** | 17.89 |

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
| Divergences | **10** |

## Entry Lock Results (L0–L4)

| # | ticker | name | signal | level | L0 | L1 | L2 | L3 | L4 | status | p1_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2467.TW | 志聖 | BUY | READY | ⚠️ | ✅ | 🚫 | 🚫 | ✅ | **BLOCK** | 🚫 WAIT |
| 2 | 3583.TW | 辛耘 | BUY | READY | ⚠️ | ✅ | 🚫 | ✅ | ✅ | **BLOCK** | 🚫 WAIT |
| 3 | 6187.TWO | 萬潤 | BUY | READY | ⚠️ | ✅ | 🚫 | ✅ | ✅ | **BLOCK** | 🚫 WAIT |
| 4 | 6669.TW | 緯穎 | BUY | READY | ⚠️ | ✅ | 🚫 | ✅ | ✅ | **BLOCK** | 🚫 WAIT |
| 5 | 2356.TW | 英業達 | BUY | READY | ⚠️ | ✅ | 🚫 | ✅ | ✅ | **BLOCK** | 🚫 WAIT |
| 6 | 2376.TW | 技嘉 | BUY | READY | ⚠️ | ✅ | ✅ | 🚫 | ✅ | **BLOCK** | 🚫 WAIT |
| 7 | 2377.TW | 微星 | BUY | READY | ⚠️ | ✅ | 🚫 | ✅ | ✅ | **BLOCK** | 🚫 WAIT |
| 8 | 3037.TW | 欣興 | BUY | READY | ⚠️ | ✅ | ✅ | 🚫 | ✅ | **BLOCK** | 🚫 WAIT |
| 9 | 2368.TW | 金像電 | BUY | READY | ⚠️ | ✅ | ✅ | 🚫 | 🚫 | **BLOCK** | 🚫 WAIT |
| 10 | 3044.TW | 健鼎 | BUY | READY | ⚠️ | ✅ | 🚫 | ✅ | ✅ | **BLOCK** | 🚫 WAIT |

## Trade Setup Results

| ticker | setup_type | entry_zone | stop | T1 | T2 | R/R | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2467.TW | VCP_BREAKOUT | 649.0000 | 616.5500 | 713.9000 | 778.8000 | 2.0000 | VALID |
| 3583.TW | VCP_BREAKOUT | 952.0000 | 904.4000 | 1047.2000 | 1142.4000 | 2.0000 | VALID |
| 6187.TWO | VCP_BREAKOUT | 1345.0000 | 1277.7500 | 1479.5000 | 1614.0000 | 2.0000 | VALID |
| 6669.TW | VCP_BREAKOUT | 5790.0000 | 5500.5000 | 6369.0000 | 6948.0000 | 2.0000 | VALID |
| 2356.TW | VCP_BREAKOUT | 50.2000 | 47.6900 | 55.2200 | 60.2400 | 2.0000 | VALID |
| 2376.TW | VCP_BREAKOUT | 324.5000 | 308.2750 | 356.9500 | 389.4000 | 2.0000 | VALID |
| 2377.TW | VCP_BREAKOUT | 107.5000 | 102.1250 | 118.2500 | 129.0000 | 2.0000 | VALID |
| 3037.TW | VCP_BREAKOUT | 911.0000 | 865.4500 | 1002.1000 | 1093.2000 | 2.0000 | VALID |
| 2368.TW | VCP_BREAKOUT | 1480.0000 | 1406.0000 | 1628.0000 | 1776.0000 | 2.0000 | VALID |
| 3044.TW | VCP_BREAKOUT | 500.0000 | 475.0000 | 550.0000 | 600.0000 | 2.0000 | VALID |

## Position Sizing Results

| ticker | shares | value | pct% | max_loss | risk/share | feasible |
| --- | --- | --- | --- | --- | --- | --- |
| 2467.TW | 30 | 19470.0000 | 19.47% | 1000.0000 | 32.4500 | ✅ |
| 3583.TW | 21 | 19992.0000 | 19.99% | 1000.0000 | 47.6000 | ✅ |
| 6187.TWO | 14 | 18830.0000 | 18.83% | 1000.0000 | 67.2500 | ✅ |
| 6669.TW | 3 | 17370.0000 | 17.37% | 1000.0000 | 289.5000 | ✅ |
| 2356.TW | 398 | 19979.6000 | 19.98% | 1000.0000 | 2.5100 | ✅ |
| 2376.TW | 61 | 19794.5000 | 19.79% | 1000.0000 | 16.2250 | ✅ |
| 2377.TW | 186 | 19995.0000 | 19.99% | 1000.0000 | 5.3750 | ✅ |
| 3037.TW | 21 | 19131.0000 | 19.13% | 1000.0000 | 45.5500 | ✅ |
| 2368.TW | 13 | 19240.0000 | 19.24% | 1000.0000 | 74.0000 | ✅ |
| 3044.TW | 40 | 20000.0000 | 20.00% | 1000.0000 | 25.0000 | ✅ |

## Pipeline Divergences

| ticker | name | p1_action | pipeline_action | flags |
| --- | --- | --- | --- | --- |
| 2467.TW | 志聖 | WAIT | - | NO_PIPELINE_DECISION |
| 3583.TW | 辛耘 | WAIT | - | NO_PIPELINE_DECISION |
| 6187.TWO | 萬潤 | WAIT | - | NO_PIPELINE_DECISION |
| 6669.TW | 緯穎 | WAIT | - | NO_PIPELINE_DECISION |
| 2356.TW | 英業達 | WAIT | BUY | P0_BLOCK_vs_PIPELINE_BUY |
| 2376.TW | 技嘉 | WAIT | BUY | P0_BLOCK_vs_PIPELINE_BUY |
| 2377.TW | 微星 | WAIT | BUY | P0_BLOCK_vs_PIPELINE_BUY |
| 3037.TW | 欣興 | WAIT | - | NO_PIPELINE_DECISION |
| 2368.TW | 金像電 | WAIT | - | NO_PIPELINE_DECISION |
| 3044.TW | 健鼎 | WAIT | - | NO_PIPELINE_DECISION |

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