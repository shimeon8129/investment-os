# P1 Entry Audit — 2026-05-11

## Source

- Snapshot: `data/processed/mainline_snapshot.json`
- Snapshot generated at: `2026-05-11T16:00:23.354594`
- Audit generated at: `2026-05-11T16:00:27.181308`
- Capital: `100,000`

## Market Context

| Market State | VIX |
| --- | --- |
| **BULL** | 18.21 |

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
| EntryLock PASS | 2 |
| EntryLock WARN | 0 |
| EntryLock BLOCK | 8 |
| EntryLock SKIP | 0 |
| TradeSetup VALID | 10 |
| TradeSetup INVALID | 0 |
| TradeSetup INSUFFICIENT | 0 |
| Sizing feasible | 10 |
| P1 ENTRY | 2 |
| P1 ENTRY_REDUCED | 0 |
| P1 WAIT | 8 |
| P1 SKIP | 0 |
| P1 DATA_UNAVAILABLE | 0 |
| Divergences | **9** |

## Entry Lock Results (L0–L4)

| # | ticker | name | signal | level | L0 | L1 | L2 | L3 | L4 | status | p1_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2467.TW | 志聖 | BUY | READY | ✅ | ✅ | 🚫 | ✅ | ✅ | **BLOCK** | 🚫 WAIT |
| 2 | 3583.TW | 辛耘 | BUY | READY | ✅ | ✅ | 🚫 | ✅ | ✅ | **BLOCK** | 🚫 WAIT |
| 3 | 2464.TW | 盟立 | BUY | READY | ✅ | ✅ | 🚫 | 🚫 | ✅ | **BLOCK** | 🚫 WAIT |
| 4 | 2449.TW | 京元電子 | BUY | READY | ✅ | ✅ | ✅ | 🚫 | 🚫 | **BLOCK** | 🚫 WAIT |
| 5 | 6147.TWO | 頎邦 | BUY | READY | ✅ | ✅ | 🚫 | ✅ | ✅ | **BLOCK** | 🚫 WAIT |
| 6 | 2356.TW | 英業達 | BUY | READY | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** | ✅ ENTRY |
| 7 | 3706.TW | 神達 | BUY | READY | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** | ✅ ENTRY |
| 8 | 2376.TW | 技嘉 | BUY | READY | ✅ | ✅ | 🚫 | ✅ | ✅ | **BLOCK** | 🚫 WAIT |
| 9 | 2377.TW | 微星 | BUY | READY | ✅ | ✅ | 🚫 | ✅ | ✅ | **BLOCK** | 🚫 WAIT |
| 10 | 3037.TW | 欣興 | BUY | READY | ✅ | ✅ | ✅ | 🚫 | ✅ | **BLOCK** | 🚫 WAIT |

## Trade Setup Results

| ticker | setup_type | entry_zone | stop | T1 | T2 | R/R | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2467.TW | VCP_BREAKOUT | 609.0000 | 578.5500 | 669.9000 | 730.8000 | 2.0000 | VALID |
| 3583.TW | VCP_BREAKOUT | 815.0000 | 774.2500 | 896.5000 | 978.0000 | 2.0000 | VALID |
| 2464.TW | VCP_BREAKOUT | 122.0000 | 115.9000 | 134.2000 | 146.4000 | 2.0000 | VALID |
| 2449.TW | VCP_BREAKOUT | 354.0000 | 336.3000 | 389.4000 | 424.8000 | 2.0000 | VALID |
| 6147.TWO | VCP_BREAKOUT | 198.0000 | 188.1000 | 217.8000 | 237.6000 | 2.0000 | VALID |
| 2356.TW | VCP_BREAKOUT | 49.9500 | 47.4525 | 54.9450 | 59.9400 | 2.0000 | VALID |
| 3706.TW | VCP_BREAKOUT | 87.8000 | 83.4100 | 96.5800 | 105.3600 | 2.0000 | VALID |
| 2376.TW | VCP_BREAKOUT | 317.0000 | 301.1500 | 348.7000 | 380.4000 | 2.0000 | VALID |
| 2377.TW | VCP_BREAKOUT | 101.0000 | 95.9500 | 111.1000 | 121.2000 | 2.0000 | VALID |
| 3037.TW | VCP_BREAKOUT | 911.0000 | 865.4500 | 1002.1000 | 1093.2000 | 2.0000 | VALID |

## Position Sizing Results

| ticker | shares | value | pct% | max_loss | risk/share | feasible |
| --- | --- | --- | --- | --- | --- | --- |
| 2467.TW | 32 | 19488.0000 | 19.49% | 1000.0000 | 30.4500 | ✅ |
| 3583.TW | 24 | 19560.0000 | 19.56% | 1000.0000 | 40.7500 | ✅ |
| 2464.TW | 163 | 19886.0000 | 19.89% | 1000.0000 | 6.1000 | ✅ |
| 2449.TW | 56 | 19824.0000 | 19.82% | 1000.0000 | 17.7000 | ✅ |
| 6147.TWO | 101 | 19998.0000 | 20.00% | 1000.0000 | 9.9000 | ✅ |
| 2356.TW | 400 | 19980.0000 | 19.98% | 1000.0000 | 2.4975 | ✅ |
| 3706.TW | 227 | 19930.6000 | 19.93% | 1000.0000 | 4.3900 | ✅ |
| 2376.TW | 63 | 19971.0000 | 19.97% | 1000.0000 | 15.8500 | ✅ |
| 2377.TW | 198 | 19998.0000 | 20.00% | 1000.0000 | 5.0500 | ✅ |
| 3037.TW | 21 | 19131.0000 | 19.13% | 1000.0000 | 45.5500 | ✅ |

## Pipeline Divergences

| ticker | name | p1_action | pipeline_action | flags |
| --- | --- | --- | --- | --- |
| 2467.TW | 志聖 | WAIT | - | NO_PIPELINE_DECISION |
| 3583.TW | 辛耘 | WAIT | - | NO_PIPELINE_DECISION |
| 2464.TW | 盟立 | WAIT | BUY | P0_BLOCK_vs_PIPELINE_BUY |
| 2449.TW | 京元電子 | WAIT | BUY | P0_BLOCK_vs_PIPELINE_BUY |
| 6147.TWO | 頎邦 | WAIT | - | NO_PIPELINE_DECISION |
| 3706.TW | 神達 | ENTRY | - | P0_ENTRY_vs_NO_PIPELINE, NO_PIPELINE_DECISION |
| 2376.TW | 技嘉 | WAIT | - | NO_PIPELINE_DECISION |
| 2377.TW | 微星 | WAIT | - | NO_PIPELINE_DECISION |
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