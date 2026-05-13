# Investment OS Daily Report - 2026-05-12

Generated at: 2026-05-12 23:53:47

## Data Freshness

- report_label: `TODAY_MARKET_OPEN`
- run_date: 2026-05-12
- market_date: 2026-05-12
- market_status (TW): OPEN
- latest_full_trading_day (TW): 2026-05-11
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

- Market state: **RANGE** | Score: -0.0166 | VIX: 18.92

**Top 3 candidates:**

1. 3711.TW 日月光投控 — Score: 173.47 | Signal: BUY | Role: CORE/CORE [HIGH] intent=—
2. 2449.TW 京元電子 — Score: 145.20 | Signal: BUY | Role: WAVE_SWING/WAVE_SWING [MEDIUM] intent=—
3. 2376.TW 技嘉 — Score: 145.20 | Signal: BUY | Role: WAVE_SWING/WAVE_SWING [MEDIUM] intent=—

- Decisions: BUY: 2 | HOLD: 1
- Advisory only: all outputs are for human review; no trades are placed automatically.

## Mainline Snapshot

- Market state: RANGE
- Market score: -0.0166
- VIX: 18.920000076293945

### Top Ranked

| Rank | Ticker | Name | Sector | Signal | Score | base_role | active_role | role_confidence | intent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 3711.TW | 日月光投控 | Packaging | BUY | 173.46599999999998 | CORE | CORE | HIGH | — |
| 2 | 2449.TW | 京元電子 | Packaging | BUY | 145.2 | WAVE_SWING | WAVE_SWING | MEDIUM | — |
| 3 | 2376.TW | 技嘉 | Server | BUY | 145.2 | WAVE_SWING | WAVE_SWING | MEDIUM | — |
| 4 | 3231.TW | 緯創 | Server | BUY | 144.534 | WAVE_SWING | WAVE_SWING | MEDIUM | — |
| 5 | 2377.TW | 微星 | Server | BUY | 144.2 | UNKNOWN | UNKNOWN | UNKNOWN | — |

### Decisions

| Ticker | Action | Reason |
| --- | --- | --- |
| 3711.TW | HOLD | ALREADY_IN_POSITION |
| 2449.TW | BUY | REDUCED_BY_MARKET |
| 2376.TW | BUY | REDUCED_BY_MARKET |

## P1 Entry Audit

- Total signals audited: 10
- EntryLock: PASS=0 WARN=1 BLOCK=9 SKIP=0
- P1 Action: ENTRY=0 ENTRY_REDUCED=1 WAIT=9 SKIP=0 UNAVAIL=0
- Divergences: 9
- Advisory only. No runtime decisions changed.
- Report: docs/P1_ENTRY_AUDIT_20260512.md

## Role-Aware Candidate Summary

| Ticker | Name | Score | Signal | base_role | active_role | role_confidence | intent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 3711.TW | 日月光投控 | 173.47 | BUY | CORE | CORE | HIGH | — |
| 2449.TW | 京元電子 | 145.20 | BUY | WAVE_SWING | WAVE_SWING | MEDIUM | — |
| 2376.TW | 技嘉 | 145.20 | BUY | WAVE_SWING | WAVE_SWING | MEDIUM | — |
| 3231.TW | 緯創 | 144.53 | BUY | WAVE_SWING | WAVE_SWING | MEDIUM | — |
| 2377.TW | 微星 | 144.20 | BUY | UNKNOWN | UNKNOWN | UNKNOWN | — |
| 3583.TW | 辛耘 | 123.00 | BUY | UNKNOWN | UNKNOWN | UNKNOWN | — |
| 2467.TW | 志聖 | 118.20 | BUY | UNKNOWN | UNKNOWN | UNKNOWN | — |
| 6669.TW | 緯穎 | 108.20 | BUY | UNKNOWN | UNKNOWN | UNKNOWN | — |
| 2313.TW | 華通 | 108.20 | BUY | UNKNOWN | UNKNOWN | UNKNOWN | — |
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
- `/home/shimeon/investment_os/reports/daily/2026-05-12_daily_report.md`
- `/home/shimeon/investment_os/logs/daily_run.log`
