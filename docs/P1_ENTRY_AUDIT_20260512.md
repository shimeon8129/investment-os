# P1 Entry Audit — 2026-05-12

## Source

- Snapshot: `data/processed/mainline_snapshot.json`
- Snapshot generated at: `2026-05-12T23:53:56.872186`
- Audit generated at: `2026-05-12T23:53:59.827123`
- Capital: `100,000`

## Market Context

| Market State | VIX |
| --- | --- |
| **RANGE** | 18.92 |

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
| EntryLock WARN | 1 |
| EntryLock BLOCK | 9 |
| EntryLock SKIP | 0 |
| TradeSetup VALID | 10 |
| TradeSetup INVALID | 0 |
| TradeSetup INSUFFICIENT | 0 |
| Sizing feasible | 10 |
| P1 ENTRY | 0 |
| P1 ENTRY_REDUCED | 1 |
| P1 WAIT | 9 |
| P1 SKIP | 0 |
| P1 DATA_UNAVAILABLE | 0 |
| Divergences | **9** |

## Entry Lock Results (L0–L4)

| # | ticker | name | signal | level | L0 | L1 | L2 | L3 | L4 | status | p1_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2467.TW | 志聖 | BUY | READY | ⚠️ | ✅ | 🚫 | ✅ | ✅ | **BLOCK** | 🚫 WAIT |
| 2 | 3583.TW | 辛耘 | BUY | READY | ⚠️ | ✅ | 🚫 | ✅ | ✅ | **BLOCK** | 🚫 WAIT |
| 3 | 3711.TW | 日月光投控 | BUY | READY | ⚠️ | ✅ | 🚫 | ✅ | ✅ | **BLOCK** | 🚫 WAIT |
| 4 | 2449.TW | 京元電子 | BUY | READY | ⚠️ | ✅ | ✅ | 🚫 | 🚫 | **BLOCK** | 🚫 WAIT |
| 5 | 3231.TW | 緯創 | BUY | READY | ⚠️ | ✅ | ✅ | 🚫 | 🚫 | **BLOCK** | 🚫 WAIT |
| 6 | 6669.TW | 緯穎 | BUY | READY | ⚠️ | ✅ | 🚫 | ✅ | ✅ | **BLOCK** | 🚫 WAIT |
| 7 | 2376.TW | 技嘉 | BUY | READY | ⚠️ | ✅ | ✅ | 🚫 | ✅ | **BLOCK** | 🚫 WAIT |
| 8 | 2377.TW | 微星 | BUY | READY | ⚠️ | ✅ | ✅ | ✅ | ✅ | **WARN** | ⚠️ ENTRY_REDUCED |
| 9 | 2313.TW | 華通 | BUY | READY | ⚠️ | ✅ | 🚫 | ✅ | ✅ | **BLOCK** | 🚫 WAIT |
| 10 | 3037.TW | 欣興 | BUY | READY | ⚠️ | ✅ | ✅ | 🚫 | ✅ | **BLOCK** | 🚫 WAIT |

## Trade Setup Results

| ticker | setup_type | entry_zone | stop | T1 | T2 | R/R | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2467.TW | VCP_BREAKOUT | 609.0000 | 578.5500 | 669.9000 | 730.8000 | 2.0000 | VALID |
| 3583.TW | VCP_BREAKOUT | 866.0000 | 822.7000 | 952.6000 | 1039.2000 | 2.0000 | VALID |
| 3711.TW | VCP_BREAKOUT | 540.0000 | 513.0000 | 594.0000 | 648.0000 | 2.0000 | VALID |
| 2449.TW | VCP_BREAKOUT | 354.0000 | 336.3000 | 389.4000 | 424.8000 | 2.0000 | VALID |
| 3231.TW | VCP_BREAKOUT | 146.5000 | 139.1750 | 161.1500 | 175.8000 | 2.0000 | VALID |
| 6669.TW | VCP_BREAKOUT | 5340.0000 | 5073.0000 | 5874.0000 | 6408.0000 | 2.0000 | VALID |
| 2376.TW | VCP_BREAKOUT | 324.5000 | 308.2750 | 356.9500 | 389.4000 | 2.0000 | VALID |
| 2377.TW | VCP_BREAKOUT | 107.5000 | 102.1250 | 118.2500 | 129.0000 | 2.0000 | VALID |
| 2313.TW | VCP_BREAKOUT | 274.5000 | 260.7750 | 301.9500 | 329.4000 | 2.0000 | VALID |
| 3037.TW | VCP_BREAKOUT | 911.0000 | 865.4500 | 1002.1000 | 1093.2000 | 2.0000 | VALID |

## Position Sizing Results

| ticker | shares | value | pct% | max_loss | risk/share | feasible |
| --- | --- | --- | --- | --- | --- | --- |
| 2467.TW | 32 | 19488.0000 | 19.49% | 1000.0000 | 30.4500 | ✅ |
| 3583.TW | 23 | 19918.0000 | 19.92% | 1000.0000 | 43.3000 | ✅ |
| 3711.TW | 37 | 19980.0000 | 19.98% | 1000.0000 | 27.0000 | ✅ |
| 2449.TW | 56 | 19824.0000 | 19.82% | 1000.0000 | 17.7000 | ✅ |
| 3231.TW | 136 | 19924.0000 | 19.92% | 1000.0000 | 7.3250 | ✅ |
| 6669.TW | 3 | 16020.0000 | 16.02% | 1000.0000 | 267.0000 | ✅ |
| 2376.TW | 61 | 19794.5000 | 19.79% | 1000.0000 | 16.2250 | ✅ |
| 2377.TW | 186 | 19995.0000 | 19.99% | 1000.0000 | 5.3750 | ✅ |
| 2313.TW | 72 | 19764.0000 | 19.76% | 1000.0000 | 13.7250 | ✅ |
| 3037.TW | 21 | 19131.0000 | 19.13% | 1000.0000 | 45.5500 | ✅ |

## Pipeline Divergences

| ticker | name | p1_action | pipeline_action | flags |
| --- | --- | --- | --- | --- |
| 2467.TW | 志聖 | WAIT | - | NO_PIPELINE_DECISION |
| 3583.TW | 辛耘 | WAIT | - | NO_PIPELINE_DECISION |
| 2449.TW | 京元電子 | WAIT | BUY | P0_BLOCK_vs_PIPELINE_BUY |
| 3231.TW | 緯創 | WAIT | - | NO_PIPELINE_DECISION |
| 6669.TW | 緯穎 | WAIT | - | NO_PIPELINE_DECISION |
| 2376.TW | 技嘉 | WAIT | BUY | P0_BLOCK_vs_PIPELINE_BUY |
| 2377.TW | 微星 | ENTRY_REDUCED | - | NO_PIPELINE_DECISION |
| 2313.TW | 華通 | WAIT | - | NO_PIPELINE_DECISION |
| 3037.TW | 欣興 | WAIT | - | NO_PIPELINE_DECISION |

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