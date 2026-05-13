# P1 Entry Audit — 2026-05-08

## Source

- Snapshot: `data/processed/mainline_snapshot.json`
- Snapshot generated at: `2026-05-08T16:16:51.477019`
- Audit generated at: `2026-05-08T16:16:54.431517`
- Capital: `100,000`

## Market Context

| Market State | VIX |
| --- | --- |
| **RANGE** | 17.20 |

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
| EntryLock WARN | 3 |
| EntryLock BLOCK | 7 |
| EntryLock SKIP | 0 |
| TradeSetup VALID | 10 |
| TradeSetup INVALID | 0 |
| TradeSetup INSUFFICIENT | 0 |
| Sizing feasible | 10 |
| P1 ENTRY | 0 |
| P1 ENTRY_REDUCED | 3 |
| P1 WAIT | 7 |
| P1 SKIP | 0 |
| P1 DATA_UNAVAILABLE | 0 |
| Divergences | **10** |

## Entry Lock Results (L0–L4)

| # | ticker | name | signal | level | L0 | L1 | L2 | L3 | L4 | status | p1_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 3680.TWO | 家登 | BUY | READY | ⚠️ | ✅ | ✅ | 🚫 | ✅ | **BLOCK** | 🚫 WAIT |
| 2 | 2464.TW | 盟立 | BUY | READY | ⚠️ | ✅ | 🚫 | ✅ | ✅ | **BLOCK** | 🚫 WAIT |
| 3 | 2449.TW | 京元電子 | BUY | READY | ⚠️ | ✅ | ✅ | 🚫 | ✅ | **BLOCK** | 🚫 WAIT |
| 4 | 6147.TWO | 頎邦 | BUY | READY | ⚠️ | ✅ | 🚫 | ✅ | ✅ | **BLOCK** | 🚫 WAIT |
| 5 | 6257.TW | 矽格 | BUY | READY | ⚠️ | ✅ | 🚫 | ✅ | ✅ | **BLOCK** | 🚫 WAIT |
| 6 | 2317.TW | 鴻海 | BUY | READY | ⚠️ | ✅ | ✅ | 🚫 | ✅ | **BLOCK** | 🚫 WAIT |
| 7 | 3231.TW | 緯創 | BUY | READY | ⚠️ | ✅ | ✅ | ✅ | ✅ | **WARN** | ⚠️ ENTRY_REDUCED |
| 8 | 6669.TW | 緯穎 | BUY | READY | ⚠️ | ✅ | 🚫 | ✅ | ✅ | **BLOCK** | 🚫 WAIT |
| 9 | 2356.TW | 英業達 | BUY | READY | ⚠️ | ✅ | ✅ | ✅ | ✅ | **WARN** | ⚠️ ENTRY_REDUCED |
| 10 | 3706.TW | 神達 | BUY | READY | ⚠️ | ✅ | ✅ | ✅ | ✅ | **WARN** | ⚠️ ENTRY_REDUCED |

## Trade Setup Results

| ticker | setup_type | entry_zone | stop | T1 | T2 | R/R | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 3680.TWO | VCP_BREAKOUT | 585.0000 | 555.7500 | 643.5000 | 702.0000 | 2.0000 | VALID |
| 2464.TW | VCP_BREAKOUT | 116.0000 | 110.2000 | 127.6000 | 139.2000 | 2.0000 | VALID |
| 2449.TW | VCP_BREAKOUT | 354.0000 | 336.3000 | 389.4000 | 424.8000 | 2.0000 | VALID |
| 6147.TWO | VCP_BREAKOUT | 192.5000 | 182.8750 | 211.7500 | 231.0000 | 2.0000 | VALID |
| 6257.TW | VCP_BREAKOUT | 213.0000 | 202.3500 | 234.3000 | 255.6000 | 2.0000 | VALID |
| 2317.TW | VCP_BREAKOUT | 253.5000 | 240.8250 | 278.8500 | 304.2000 | 2.0000 | VALID |
| 3231.TW | VCP_BREAKOUT | 146.5000 | 139.1750 | 161.1500 | 175.8000 | 2.0000 | VALID |
| 6669.TW | VCP_BREAKOUT | 4970.0000 | 4721.5000 | 5467.0000 | 5964.0000 | 2.0000 | VALID |
| 2356.TW | VCP_BREAKOUT | 49.9500 | 47.4525 | 54.9450 | 59.9400 | 2.0000 | VALID |
| 3706.TW | VCP_BREAKOUT | 87.8000 | 83.4100 | 96.5800 | 105.3600 | 2.0000 | VALID |

## Position Sizing Results

| ticker | shares | value | pct% | max_loss | risk/share | feasible |
| --- | --- | --- | --- | --- | --- | --- |
| 3680.TWO | 34 | 19890.0000 | 19.89% | 1000.0000 | 29.2500 | ✅ |
| 2464.TW | 172 | 19952.0000 | 19.95% | 1000.0000 | 5.8000 | ✅ |
| 2449.TW | 56 | 19824.0000 | 19.82% | 1000.0000 | 17.7000 | ✅ |
| 6147.TWO | 103 | 19827.5000 | 19.83% | 1000.0000 | 9.6250 | ✅ |
| 6257.TW | 93 | 19809.0000 | 19.81% | 1000.0000 | 10.6500 | ✅ |
| 2317.TW | 78 | 19773.0000 | 19.77% | 1000.0000 | 12.6750 | ✅ |
| 3231.TW | 136 | 19924.0000 | 19.92% | 1000.0000 | 7.3250 | ✅ |
| 6669.TW | 4 | 19880.0000 | 19.88% | 1000.0000 | 248.5000 | ✅ |
| 2356.TW | 400 | 19980.0000 | 19.98% | 1000.0000 | 2.4975 | ✅ |
| 3706.TW | 227 | 19930.6000 | 19.93% | 1000.0000 | 4.3900 | ✅ |

## Pipeline Divergences

| ticker | name | p1_action | pipeline_action | flags |
| --- | --- | --- | --- | --- |
| 3680.TWO | 家登 | WAIT | - | NO_PIPELINE_DECISION |
| 2464.TW | 盟立 | WAIT | BUY | P0_BLOCK_vs_PIPELINE_BUY |
| 2449.TW | 京元電子 | WAIT | BUY | P0_BLOCK_vs_PIPELINE_BUY |
| 6147.TWO | 頎邦 | WAIT | - | NO_PIPELINE_DECISION |
| 6257.TW | 矽格 | WAIT | - | NO_PIPELINE_DECISION |
| 2317.TW | 鴻海 | WAIT | - | NO_PIPELINE_DECISION |
| 3231.TW | 緯創 | ENTRY_REDUCED | - | NO_PIPELINE_DECISION |
| 6669.TW | 緯穎 | WAIT | - | NO_PIPELINE_DECISION |
| 2356.TW | 英業達 | ENTRY_REDUCED | BUY | P0_WARN_vs_PIPELINE_BUY |
| 3706.TW | 神達 | ENTRY_REDUCED | - | NO_PIPELINE_DECISION |

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