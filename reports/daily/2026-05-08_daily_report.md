# Investment OS Daily Report - 2026-05-08

Generated at: 2026-05-08 16:16:42

## Data Freshness

- report_label: `TODAY_MARKET_OPEN`
- run_date: 2026-05-08
- market_date: 2026-05-08
- market_status (TW): OPEN
- latest_full_trading_day (TW): 2026-05-07
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

- Market state: **RANGE** | Score: 0.0070 | VIX: 17.20

**Top 3 candidates:**

1. 2464.TW 盟立 — Score: 151.40 | Signal: BUY
2. 2356.TW 英業達 — Score: 145.53 | Signal: BUY
3. 2449.TW 京元電子 — Score: 145.20 | Signal: BUY

- Decisions: BUY: 3
- Advisory only: all outputs are for human review; no trades are placed automatically.

## Mainline Snapshot

- Market state: RANGE
- Market score: 0.007
- VIX: 17.200000762939453

### Top Ranked

| Rank | Ticker | Name | Sector | Signal | Score |
| --- | --- | --- | --- | --- | --- |
| 1 | 2464.TW | 盟立 | Equipment | BUY | 151.4 |
| 2 | 2356.TW | 英業達 | Server | BUY | 145.534 |
| 3 | 2449.TW | 京元電子 | Packaging | BUY | 145.2 |
| 4 | 3231.TW | 緯創 | Server | BUY | 144.534 |
| 5 | 3680.TWO | 家登 | Equipment | BUY | 124.0 |

### Decisions

| Ticker | Action | Reason |
| --- | --- | --- |
| 2464.TW | BUY | REDUCED_BY_MARKET |
| 2356.TW | BUY | REDUCED_BY_MARKET |
| 2449.TW | BUY | REDUCED_BY_MARKET |

## P1 Entry Audit

- Total signals audited: 10
- EntryLock: PASS=0 WARN=3 BLOCK=7 SKIP=0
- P1 Action: ENTRY=0 ENTRY_REDUCED=3 WAIT=7 SKIP=0 UNAVAIL=0
- Divergences: 10
- Advisory only. No runtime decisions changed.
- Report: docs/P1_ENTRY_AUDIT_20260508.md

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
- `/home/shimeon/investment_os/reports/daily/2026-05-08_daily_report.md`
- `/home/shimeon/investment_os/logs/daily_run.log`
