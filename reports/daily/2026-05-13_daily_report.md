# Investment OS Daily Report - 2026-05-13

Generated at: 2026-05-13 20:35:09

## Data Freshness

- report_label: `TODAY_MARKET_OPEN`
- run_date: 2026-05-13
- market_date: 2026-05-13
- market_status (TW): OPEN
- latest_full_trading_day (TW): 2026-05-12
- data_as_of_date: UNKNOWN
- data_mode: OBSERVATION
> **Warning:** Data vintage not explicitly available in current MVP pipeline.

## Market Calendar

- TW: OPEN
- US: OPEN

## Runtime Status

- Status: PASS
- Watchlist loaded: True
- Watchlist count: 27
- Holdings loaded: True
- Holdings count: 7

## Human Summary

- Market state: **RANGE** | Score: -0.0056 | VIX: 17.89

**Top 3 candidates:**

1. 2356.TW 英業達 — Score: 155.53 | Signal: BUY | Role: WAVE_SWING/WAVE_SWING [LOW] intent=—
2. 2377.TW 微星 — Score: 154.20 | Signal: BUY | Role: UNKNOWN/UNKNOWN [UNKNOWN] intent=—
3. 2376.TW 技嘉 — Score: 145.20 | Signal: BUY | Role: WAVE_SWING/WAVE_SWING [MEDIUM] intent=—

- Decisions: BUY: 3 | REDUCE: 3 | SELL: 1
- Advisory only: all outputs are for human review; no trades are placed automatically.

## Mainline Snapshot

- Market state: RANGE
- Market score: -0.0056
- VIX: 17.889999389648438

### Top Ranked

| Rank | Ticker | Name | Sector | Signal | Score | base_role | active_role | role_confidence | intent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2356.TW | 英業達 | Server | BUY | 155.534 | WAVE_SWING | WAVE_SWING | LOW | — |
| 2 | 2377.TW | 微星 | Server | BUY | 154.2 | UNKNOWN | UNKNOWN | UNKNOWN | — |
| 3 | 2376.TW | 技嘉 | Server | BUY | 145.2 | WAVE_SWING | WAVE_SWING | MEDIUM | — |
| 4 | 3583.TW | 辛耘 | Equipment | BUY | 128.0 | UNKNOWN | UNKNOWN | UNKNOWN | — |
| 5 | 2467.TW | 志聖 | Equipment | BUY | 118.2 | UNKNOWN | UNKNOWN | UNKNOWN | — |

### Decisions

| Ticker | Action | Reason |
| --- | --- | --- |
| 2356.TW | BUY | REDUCED_BY_MARKET |
| 2377.TW | BUY | REDUCED_BY_MARKET |
| 2376.TW | BUY | REDUCED_BY_MARKET |
| 2308.TW | REDUCE | REDUCE |
| 2330.TW | REDUCE | REDUCE |
| 2345.TW | REDUCE | REDUCE |
| 6830.TW | SELL | EXIT_ALL |

## P1 Entry Audit

- Total signals audited: 10
- EntryLock: PASS=0 WARN=0 BLOCK=10 SKIP=0
- P1 Action: ENTRY=0 ENTRY_REDUCED=0 WAIT=10 SKIP=0 UNAVAIL=0
- Divergences: 10
- Advisory only. No runtime decisions changed.
- Report: docs/P1_ENTRY_AUDIT_20260513.md

## Role-Aware Candidate Summary

| Ticker | Name | Score | Signal | base_role | active_role | role_confidence | intent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2356.TW | 英業達 | 155.53 | BUY | WAVE_SWING | WAVE_SWING | LOW | — |
| 2377.TW | 微星 | 154.20 | BUY | UNKNOWN | UNKNOWN | UNKNOWN | — |
| 2376.TW | 技嘉 | 145.20 | BUY | WAVE_SWING | WAVE_SWING | MEDIUM | — |
| 3583.TW | 辛耘 | 128.00 | BUY | UNKNOWN | UNKNOWN | UNKNOWN | — |
| 2467.TW | 志聖 | 118.20 | BUY | UNKNOWN | UNKNOWN | UNKNOWN | — |
| 6187.TWO | 萬潤 | 118.20 | BUY | CORE | CORE | MEDIUM | — |
| 3044.TW | 健鼎 | 114.20 | BUY | UNKNOWN | UNKNOWN | UNKNOWN | — |
| 2368.TW | 金像電 | 113.20 | BUY | UNKNOWN | UNKNOWN | UNKNOWN | — |
| 6669.TW | 緯穎 | 108.20 | BUY | UNKNOWN | UNKNOWN | UNKNOWN | — |
| 3037.TW | 欣興 | 108.20 | BUY | UNKNOWN | UNKNOWN | UNKNOWN | — |

## Checks

### daily_decision_dashboard

- Status: PASS
- Return code: 0

### smoke_daily_decision_dashboard

- Status: PASS
- Return code: 0

### smoke_portfolio_holdings

- Status: PASS
- Return code: 0

### pipeline_main_v1

- Status: PASS
- Return code: 0

## Safety

- Broker login: disabled
- Auto trading: disabled
- Advisory only: true

## Output Files

- `/home/shimeon/investment_os/data/processed/signal_snapshot.json`
- `/home/shimeon/investment_os/reports/daily/2026-05-13_daily_report.md`
- `/home/shimeon/investment_os/logs/daily_run.log`
