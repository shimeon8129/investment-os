# Investment OS Daily Report - 2026-05-11

Generated at: 2026-05-11 16:00:14

## Data Freshness

- report_label: `TODAY_MARKET_OPEN`
- run_date: 2026-05-11
- market_date: 2026-05-11
- market_status (TW): OPEN
- latest_full_trading_day (TW): 2026-05-08
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

- Market state: **BULL** | Score: 0.0593 | VIX: 18.21

**Top 3 candidates:**

1. 2464.TW 盟立 — Score: 151.40 | Signal: BUY | Role: WAVE_SWING/WAVE_SWING [LOW] intent=—
2. 2356.TW 英業達 — Score: 145.53 | Signal: BUY | Role: WAVE_SWING/WAVE_SWING [LOW] intent=—
3. 2449.TW 京元電子 — Score: 145.20 | Signal: BUY | Role: WAVE_SWING/WAVE_SWING [MEDIUM] intent=—

- Decisions: BUY: 3
- Advisory only: all outputs are for human review; no trades are placed automatically.

## Mainline Snapshot

- Market state: BULL
- Market score: 0.0593
- VIX: 18.209999084472656

### Top Ranked

| Rank | Ticker | Name | Sector | Signal | Score | base_role | active_role | role_confidence | intent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2464.TW | 盟立 | Equipment | BUY | 151.4 | WAVE_SWING | WAVE_SWING | LOW | — |
| 2 | 2356.TW | 英業達 | Server | BUY | 145.534 | WAVE_SWING | WAVE_SWING | LOW | — |
| 3 | 2449.TW | 京元電子 | Packaging | BUY | 145.2 | WAVE_SWING | WAVE_SWING | MEDIUM | — |
| 4 | 2376.TW | 技嘉 | Server | BUY | 145.2 | WAVE_SWING | WAVE_SWING | MEDIUM | — |
| 5 | 2377.TW | 微星 | Server | BUY | 144.2 | UNKNOWN | UNKNOWN | UNKNOWN | — |

### Decisions

| Ticker | Action | Reason |
| --- | --- | --- |
| 2464.TW | BUY | NORMAL |
| 2356.TW | BUY | NORMAL |
| 2449.TW | BUY | NORMAL |

## P1 Entry Audit

- Total signals audited: 10
- EntryLock: PASS=2 WARN=0 BLOCK=8 SKIP=0
- P1 Action: ENTRY=2 ENTRY_REDUCED=0 WAIT=8 SKIP=0 UNAVAIL=0
- Divergences: 9
- Advisory only. No runtime decisions changed.
- Report: docs/P1_ENTRY_AUDIT_20260511.md

## Role-Aware Candidate Summary

| Ticker | Name | Score | Signal | base_role | active_role | role_confidence | intent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2464.TW | 盟立 | 151.40 | BUY | WAVE_SWING | WAVE_SWING | LOW | — |
| 2356.TW | 英業達 | 145.53 | BUY | WAVE_SWING | WAVE_SWING | LOW | — |
| 2449.TW | 京元電子 | 145.20 | BUY | WAVE_SWING | WAVE_SWING | MEDIUM | — |
| 2376.TW | 技嘉 | 145.20 | BUY | WAVE_SWING | WAVE_SWING | MEDIUM | — |
| 2377.TW | 微星 | 144.20 | BUY | UNKNOWN | UNKNOWN | UNKNOWN | — |
| 3583.TW | 辛耘 | 123.00 | BUY | UNKNOWN | UNKNOWN | UNKNOWN | — |
| 2467.TW | 志聖 | 118.20 | BUY | UNKNOWN | UNKNOWN | UNKNOWN | — |
| 6147.TWO | 頎邦 | 108.20 | BUY | WAVE_SWING | WAVE_SWING | LOW | — |
| 3706.TW | 神達 | 108.20 | BUY | WAVE_SWING | WAVE_SWING | LOW | — |
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
- `/home/shimeon/investment_os/reports/daily/2026-05-11_daily_report.md`
- `/home/shimeon/investment_os/logs/daily_run.log`
