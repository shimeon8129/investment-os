# Investment OS Intraday Observation — pre_market

**Slot:** pre_market
**Run timestamp:** 2026-05-08 08:40:11
**Git branch:** main
**Latest commit:** 2e29c8a

## Git Status Before Run

- Branch: main
- Latest commit: 2e29c8a
- Working tree: MODIFIED (6 files)

```
M data/candidates.json
 M data/processed/mainline_snapshot.json
 M data/processed/signal_snapshot.json
 M docs/DAILY_DECISION_DASHBOARD_SMOKE_TEST.md
 M reports/daily/2026-05-07_daily_report.md
 M reports/observation/2026-05-07_observation_summary.md
?? .claude/
?? data/processed/intraday/
?? data/processed/p1_audit_report.json
?? docs/DAILY_DECISION_DASHBOARD_20260502.md
?? docs/DAILY_DECISION_DASHBOARD_20260505.md
?? docs/DAILY_DECISION_DASHBOARD_20260507.md
?? docs/DAILY_DECISION_DASHBOARD_20260508.md
?? docs/P1_ENTRY_AUDIT_20260507.md
?? docs/P1_ENTRY_AUDIT_20260508.md
?? docs/superpowers/
?? reports/daily/2026-05-05_daily_report.md
?? reports/daily/2026-05-08_daily_report.md
?? reports/intraday/
?? reports/observation/2026-05-07_trade_log_vs_holdings_audit.md
```

## Runtime

- Command: `python3 -m jobs.daily_run`
- Runtime final status: **PASS**

## Output Paths

- Daily report: `/home/shimeon/investment_os/reports/daily/2026-05-08_daily_report.md` (EXISTS)
- Signal snapshot: `/home/shimeon/investment_os/data/processed/signal_snapshot.json` (EXISTS)
- Mainline snapshot: `/home/shimeon/investment_os/data/processed/mainline_snapshot.json` (EXISTS)
- Slot report: `/home/shimeon/investment_os/reports/intraday/2026-05-08/0840_pre_market.md`
- Slot log: `/home/shimeon/investment_os/logs/intraday/2026-05-08/0840_pre_market.log`
- Intraday signal snapshot: `/home/shimeon/investment_os/data/processed/intraday/2026-05-08/0840_signal_snapshot.json`
- Intraday mainline snapshot: `/home/shimeon/investment_os/data/processed/intraday/2026-05-08/0840_mainline_snapshot.json`

## Data Freshness

- report_label: `TODAY_MARKET_OPEN`
- run_date: 2026-05-08
- market_date: 2026-05-08
- market_status (TW): OPEN
- latest_full_trading_day (TW): 2026-05-07
- data_as_of_date: UNKNOWN
- data_mode: OBSERVATION
> **Warning:** Data vintage not explicitly available in current MVP pipeline.

## Market Status

- TW market status: OPEN
- report_label: TODAY_MARKET_OPEN
- data_as_of_date: UNKNOWN
- latest_full_trading_day: 2026-05-07

## Market State / Score / VIX

- market_state: N/A
- market_score: N/A
- VIX: N/A

## Top Ranked Candidates

1. 2356.TW 英業達 — Score: 145.53 | Signal: BUY
2. 2376.TW 技嘉 — Score: 145.20 | Signal: BUY
3. 3231.TW 緯創 — Score: 144.53 | Signal: BUY
4. 2377.TW 微星 — Score: 144.20 | Signal: BUY
5. 6830.TW 汎銓 — Score: 118.20 | Signal: BUY

## P1 Entry Audit Summary

total=10 EntryLock(PASS=0 WARN=1 BLOCK=9) Action(ENTRY=0 WAIT=9 SKIP=0) Divergences=10

## Manual Review Flags

- (none detected)

## Data Warnings / Regression Notes

- (none detected)

## Git Status After Run

- Working tree: MODIFIED (6 files)

```
M data/candidates.json
 M data/processed/mainline_snapshot.json
 M data/processed/signal_snapshot.json
 M docs/DAILY_DECISION_DASHBOARD_SMOKE_TEST.md
 M reports/daily/2026-05-07_daily_report.md
 M reports/observation/2026-05-07_observation_summary.md
?? .claude/
?? data/processed/intraday/
?? data/processed/p1_audit_report.json
?? docs/DAILY_DECISION_DASHBOARD_20260502.md
?? docs/DAILY_DECISION_DASHBOARD_20260505.md
?? docs/DAILY_DECISION_DASHBOARD_20260507.md
?? docs/DAILY_DECISION_DASHBOARD_20260508.md
?? docs/P1_ENTRY_AUDIT_20260507.md
?? docs/P1_ENTRY_AUDIT_20260508.md
?? docs/superpowers/
?? reports/daily/2026-05-05_daily_report.md
?? reports/daily/2026-05-08_daily_report.md
?? reports/intraday/
?? reports/observation/2026-05-07_trade_log_vs_holdings_audit.md
```

## Notes

> Generated files (reports, logs, snapshots) are runtime outputs only.
> They are NOT committed to git.

*Generated at: 2026-05-08 08:40:11*