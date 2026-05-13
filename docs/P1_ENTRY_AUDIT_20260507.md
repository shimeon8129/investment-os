# P1 Entry Audit — 2026-05-07

## Source

- Snapshot: `data/processed/mainline_snapshot.json`
- Snapshot generated at: `2026-05-07T16:00:22.828297`
- Audit generated at: `2026-05-07T16:00:25.724969`
- Capital: `100,000`

## Market Context

| Market State | VIX |
| --- | --- |
| **RANGE** | 17.51 |

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
| 1 | 6830.TW | 汎銓 | BUY | READY | ⚠️ | ✅ | ✅ | 🚫 | ✅ | **BLOCK** | 🚫 WAIT |
| 2 | 3711.TW | 日月光投控 | BUY | READY | ⚠️ | ✅ | 🚫 | 🚫 | ✅ | **BLOCK** | 🚫 WAIT |
| 3 | 6239.TW | 力成 | BUY | READY | ⚠️ | ✅ | 🚫 | 🚫 | ✅ | **BLOCK** | 🚫 WAIT |
| 4 | 6257.TW | 矽格 | BUY | READY | ⚠️ | ✅ | 🚫 | ✅ | ✅ | **BLOCK** | 🚫 WAIT |
| 5 | 2382.TW | 廣達 | BUY | READY | ⚠️ | ✅ | 🚫 | ✅ | ✅ | **BLOCK** | 🚫 WAIT |
| 6 | 2317.TW | 鴻海 | BUY | READY | ⚠️ | ✅ | 🚫 | ✅ | ✅ | **BLOCK** | 🚫 WAIT |
| 7 | 3231.TW | 緯創 | BUY | READY | ⚠️ | ✅ | ✅ | ✅ | ✅ | **WARN** | ⚠️ ENTRY_REDUCED |
| 8 | 2356.TW | 英業達 | BUY | READY | ⚠️ | ✅ | 🚫 | ✅ | ✅ | **BLOCK** | 🚫 WAIT |
| 9 | 3706.TW | 神達 | BUY | READY | ⚠️ | ✅ | 🚫 | ✅ | ✅ | **BLOCK** | 🚫 WAIT |
| 10 | 2376.TW | 技嘉 | BUY | READY | ⚠️ | ✅ | 🚫 | ✅ | ✅ | **BLOCK** | 🚫 WAIT |

## Price Context

| ticker | name | price | MA5 | MA10 | price/MA5 | price/MA10 |
| --- | --- | --- | --- | --- | --- | --- |
| 6830.TW | 汎銓 | 874.00 | 900.40 | 816.80 | -2.9% | +7.0% |
| 3711.TW | 日月光投控 | 540.00 | 517.40 | 502.70 | +4.4% | +7.4% |
| 6239.TW | 力成 | 230.50 | 223.70 | 217.55 | +3.0% | +6.0% |
| 6257.TW | 矽格 | 213.00 | 196.80 | 188.60 | +8.2% | +12.9% |
| 2382.TW | 廣達 | 344.00 | 328.40 | 325.55 | +4.8% | +5.7% |
| 2317.TW | 鴻海 | 253.50 | 238.40 | 231.70 | +6.3% | +9.4% |
| 3231.TW | 緯創 | 146.00 | 142.40 | 141.65 | +2.5% | +3.1% |
| 2356.TW | 英業達 | 49.95 | 47.70 | 47.23 | +4.7% | +5.8% |
| 3706.TW | 神達 | 87.40 | 84.72 | 83.25 | +3.2% | +5.0% |
| 2376.TW | 技嘉 | 309.00 | 288.30 | 283.35 | +7.2% | +9.1% |

## Trade Setup Results

| ticker | setup_type | entry_zone | stop | T1 | T2 | R/R | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 6830.TW | VCP_BREAKOUT | 975.0000 | 926.2500 | 1072.5000 | 1170.0000 | 2.0000 | VALID |
| 3711.TW | VCP_BREAKOUT | 525.0000 | 498.7500 | 577.5000 | 630.0000 | 2.0000 | VALID |
| 6239.TW | VCP_BREAKOUT | 234.5000 | 222.7750 | 257.9500 | 281.4000 | 2.0000 | VALID |
| 6257.TW | VCP_BREAKOUT | 203.5000 | 193.3250 | 223.8500 | 244.2000 | 2.0000 | VALID |
| 2382.TW | VCP_BREAKOUT | 346.5000 | 329.1750 | 381.1500 | 415.8000 | 2.0000 | VALID |
| 2317.TW | VCP_BREAKOUT | 252.0000 | 239.4000 | 277.2000 | 302.4000 | 2.0000 | VALID |
| 3231.TW | VCP_BREAKOUT | 146.5000 | 139.1750 | 161.1500 | 175.8000 | 2.0000 | VALID |
| 2356.TW | VCP_BREAKOUT | 49.2000 | 46.7400 | 54.1200 | 59.0400 | 2.0000 | VALID |
| 3706.TW | VCP_BREAKOUT | 87.8000 | 83.4100 | 96.5800 | 105.3600 | 2.0000 | VALID |
| 2376.TW | VCP_BREAKOUT | 301.0000 | 285.9500 | 331.1000 | 361.2000 | 2.0000 | VALID |

## Position Sizing Results

| ticker | shares | value | pct% | max_loss | risk/share | feasible |
| --- | --- | --- | --- | --- | --- | --- |
| 6830.TW | 20 | 19500.0000 | 19.50% | 1000.0000 | 48.7500 | ✅ |
| 3711.TW | 38 | 19950.0000 | 19.95% | 1000.0000 | 26.2500 | ✅ |
| 6239.TW | 85 | 19932.5000 | 19.93% | 1000.0000 | 11.7250 | ✅ |
| 6257.TW | 98 | 19943.0000 | 19.94% | 1000.0000 | 10.1750 | ✅ |
| 2382.TW | 57 | 19750.5000 | 19.75% | 1000.0000 | 17.3250 | ✅ |
| 2317.TW | 79 | 19908.0000 | 19.91% | 1000.0000 | 12.6000 | ✅ |
| 3231.TW | 136 | 19924.0000 | 19.92% | 1000.0000 | 7.3250 | ✅ |
| 2356.TW | 406 | 19975.2000 | 19.98% | 1000.0000 | 2.4600 | ✅ |
| 3706.TW | 227 | 19930.6000 | 19.93% | 1000.0000 | 4.3900 | ✅ |
| 2376.TW | 66 | 19866.0000 | 19.87% | 1000.0000 | 15.0500 | ✅ |

## Pipeline Divergences

| ticker | name | p1_action | pipeline_action | flags |
| --- | --- | --- | --- | --- |
| 6830.TW | 汎銓 | WAIT | - | NO_PIPELINE_DECISION |
| 6239.TW | 力成 | WAIT | - | NO_PIPELINE_DECISION |
| 6257.TW | 矽格 | WAIT | - | NO_PIPELINE_DECISION |
| 2382.TW | 廣達 | WAIT | - | NO_PIPELINE_DECISION |
| 2317.TW | 鴻海 | WAIT | - | NO_PIPELINE_DECISION |
| 3231.TW | 緯創 | ENTRY_REDUCED | - | NO_PIPELINE_DECISION |
| 2356.TW | 英業達 | WAIT | BUY | P0_BLOCK_vs_PIPELINE_BUY |
| 3706.TW | 神達 | WAIT | - | NO_PIPELINE_DECISION |
| 2376.TW | 技嘉 | WAIT | BUY | P0_BLOCK_vs_PIPELINE_BUY |

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