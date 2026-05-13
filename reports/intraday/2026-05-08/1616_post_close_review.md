# Investment OS Intraday Observation — post_close_review

**Slot:** post_close_review
**Run timestamp:** 2026-05-08 16:16:42
**Git branch:** main
**Latest commit:** 95ede77

## Git Status Before Run

- Branch: main
- Latest commit: 95ede77
- Working tree: MODIFIED (6 files)

```
M data/candidates.json
 M data/processed/mainline_snapshot.json
 M data/processed/signal_snapshot.json
 M docs/DAILY_DECISION_DASHBOARD_SMOKE_TEST.md
 M reports/daily/2026-05-07_daily_report.md
 M reports/observation/2026-05-07_observation_summary.md
?? .claude/
?? data/observations/
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
?? reports/observation/2026-05-08_observation_summary.md
?? reports/replay/
```

## Runtime

- Command: `python3 -m jobs.daily_run`
- Runtime final status: **PASS**

## Output Paths

- Daily report: `/home/shimeon/investment_os/reports/daily/2026-05-08_daily_report.md` (EXISTS)
- Signal snapshot: `/home/shimeon/investment_os/data/processed/signal_snapshot.json` (EXISTS)
- Mainline snapshot: `/home/shimeon/investment_os/data/processed/mainline_snapshot.json` (EXISTS)
- Slot report: `/home/shimeon/investment_os/reports/intraday/2026-05-08/1616_post_close_review.md`
- Slot log: `/home/shimeon/investment_os/logs/intraday/2026-05-08/1616_post_close_review.log`
- Intraday signal snapshot: `/home/shimeon/investment_os/data/processed/intraday/2026-05-08/1616_signal_snapshot.json`
- Intraday mainline snapshot: `/home/shimeon/investment_os/data/processed/intraday/2026-05-08/1616_mainline_snapshot.json`

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

1. 2464.TW 盟立 — Score: 151.40 | Signal: BUY
2. 2356.TW 英業達 — Score: 145.53 | Signal: BUY
3. 2449.TW 京元電子 — Score: 145.20 | Signal: BUY
4. 3231.TW 緯創 — Score: 144.53 | Signal: BUY
5. 3680.TWO 家登 — Score: 124.00 | Signal: BUY

## P1 Entry Audit Summary

total=10 EntryLock(PASS=0 WARN=3 BLOCK=7) Action(ENTRY=0 WAIT=7 SKIP=0) Divergences=10

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
?? data/observations/
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
?? reports/observation/2026-05-08_observation_summary.md
?? reports/replay/
```

## Notes

> Generated files (reports, logs, snapshots) are runtime outputs only.
> They are NOT committed to git.

*Generated at: 2026-05-08 16:16:42*