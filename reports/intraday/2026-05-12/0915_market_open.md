# Investment OS Intraday Observation — market_open

**Slot:** market_open
**Run timestamp:** 2026-05-12 09:15:11
**Git branch:** main
**Latest commit:** 04d6c6c

## Git Status Before Run

- Branch: main
- Latest commit: 04d6c6c
- Working tree: MODIFIED (9 files)

```
M data/candidates.json
 M data/processed/mainline_snapshot.json
 M data/processed/signal_snapshot.json
 M docs/DAILY_DECISION_DASHBOARD_SMOKE_TEST.md
 M jobs/daily_run.py
 M reporting/web_report_generator.py
 M reports/daily/2026-05-07_daily_report.md
 M reports/observation/2026-05-07_observation_summary.md
 M reports/web/replay.html
?? .claude/
?? analysis/
?? data/observations/daily/2026-05-08_observation_summary.json
?? data/observations/intraday/
?? data/portfolio/role_map.json
?? data/processed/intraday/
?? data/processed/p1_audit_report.json
?? data/validation/
?? docs/DAILY_DECISION_DASHBOARD_20260502.md
?? docs/DAILY_DECISION_DASHBOARD_20260505.md
?? docs/DAILY_DECISION_DASHBOARD_20260507.md
?? docs/DAILY_DECISION_DASHBOARD_20260508.md
?? docs/DAILY_DECISION_DASHBOARD_20260511.md
?? docs/DAILY_DECISION_DASHBOARD_20260512.md
?? docs/P1_ENTRY_AUDIT_20260507.md
?? docs/P1_ENTRY_AUDIT_20260508.md
?? docs/P1_ENTRY_AUDIT_20260511.md
?? docs/P1_ENTRY_AUDIT_20260512.md
?? docs/ROLE_BASED_POSITION_MODEL_V0_1.md
?? docs/superpowers/plans/2026-05-07-candidate-discovery-pool-v0.1.md
?? docs/superpowers/plans/2026-05-08-observation-replay-layer-v0.1.md
?? portfolio/role_classifier.py
?? reports/daily/2026-05-05_daily_report.md
?? reports/daily/2026-05-08_daily_report.md
?? reports/daily/2026-05-11_daily_report.md
?? reports/daily/2026-05-12_daily_report.md
?? reports/intraday/
?? reports/observation/2026-05-07_trade_log_vs_holdings_audit.md
?? reports/observation/2026-05-08_observation_summary.md
?? reports/observation/2026-05-11_observation_summary.md
?? reports/replay/
?? reports/validation/
?? reports/web/history.html
?? reports/web/status.html
```

## Runtime

- Command: `python3 -m jobs.daily_run`
- Runtime final status: **PASS**

## Output Paths

- Daily report: `/home/shimeon/investment_os/reports/daily/2026-05-12_daily_report.md` (EXISTS)
- Signal snapshot: `/home/shimeon/investment_os/data/processed/signal_snapshot.json` (EXISTS)
- Mainline snapshot: `/home/shimeon/investment_os/data/processed/mainline_snapshot.json` (EXISTS)
- Slot report: `/home/shimeon/investment_os/reports/intraday/2026-05-12/0915_market_open.md`
- Slot log: `/home/shimeon/investment_os/logs/intraday/2026-05-12/0915_market_open.log`
- Intraday signal snapshot: `/home/shimeon/investment_os/data/processed/intraday/2026-05-12/0915_signal_snapshot.json`
- Intraday mainline snapshot: `/home/shimeon/investment_os/data/processed/intraday/2026-05-12/0915_mainline_snapshot.json`

## Data Freshness

- report_label: `TODAY_MARKET_OPEN`
- run_date: 2026-05-12
- market_date: 2026-05-12
- market_status (TW): OPEN
- latest_full_trading_day (TW): 2026-05-11
- data_as_of_date: UNKNOWN
- data_mode: OBSERVATION
> **Warning:** Data vintage not explicitly available in current MVP pipeline.

## Market Status

- TW market status: OPEN
- report_label: TODAY_MARKET_OPEN
- data_as_of_date: UNKNOWN
- latest_full_trading_day: 2026-05-11

## Market State / Score / VIX

- market_state: N/A
- market_score: N/A
- VIX: N/A

## Top Ranked Candidates

1. 2464.TW 盟立 — Score: 151.40 | Signal: BUY | Role: WAVE_SWING/WAVE_SWING [LOW] intent=—
2. 2356.TW 英業達 — Score: 145.53 | Signal: BUY | Role: WAVE_SWING/WAVE_SWING [LOW] intent=—
3. 2449.TW 京元電子 — Score: 145.20 | Signal: BUY | Role: WAVE_SWING/WAVE_SWING [MEDIUM] intent=—
4. 2376.TW 技嘉 — Score: 145.20 | Signal: BUY | Role: WAVE_SWING/WAVE_SWING [MEDIUM] intent=—
5. 2377.TW 微星 — Score: 144.20 | Signal: BUY | Role: UNKNOWN/UNKNOWN [UNKNOWN] intent=—

## P1 Entry Audit Summary

total=10 EntryLock(PASS=2 WARN=0 BLOCK=8) Action(ENTRY=2 WAIT=8 SKIP=0) Divergences=9

## Manual Review Flags

- (none detected)

## Data Warnings / Regression Notes

- (none detected)

## Git Status After Run

- Working tree: MODIFIED (9 files)

```
M data/candidates.json
 M data/processed/mainline_snapshot.json
 M data/processed/signal_snapshot.json
 M docs/DAILY_DECISION_DASHBOARD_SMOKE_TEST.md
 M jobs/daily_run.py
 M reporting/web_report_generator.py
 M reports/daily/2026-05-07_daily_report.md
 M reports/observation/2026-05-07_observation_summary.md
 M reports/web/replay.html
?? .claude/
?? analysis/
?? data/observations/daily/2026-05-08_observation_summary.json
?? data/observations/intraday/
?? data/portfolio/role_map.json
?? data/processed/intraday/
?? data/processed/p1_audit_report.json
?? data/validation/
?? docs/DAILY_DECISION_DASHBOARD_20260502.md
?? docs/DAILY_DECISION_DASHBOARD_20260505.md
?? docs/DAILY_DECISION_DASHBOARD_20260507.md
?? docs/DAILY_DECISION_DASHBOARD_20260508.md
?? docs/DAILY_DECISION_DASHBOARD_20260511.md
?? docs/DAILY_DECISION_DASHBOARD_20260512.md
?? docs/P1_ENTRY_AUDIT_20260507.md
?? docs/P1_ENTRY_AUDIT_20260508.md
?? docs/P1_ENTRY_AUDIT_20260511.md
?? docs/P1_ENTRY_AUDIT_20260512.md
?? docs/ROLE_BASED_POSITION_MODEL_V0_1.md
?? docs/superpowers/plans/2026-05-07-candidate-discovery-pool-v0.1.md
?? docs/superpowers/plans/2026-05-08-observation-replay-layer-v0.1.md
?? portfolio/role_classifier.py
?? reports/daily/2026-05-05_daily_report.md
?? reports/daily/2026-05-08_daily_report.md
?? reports/daily/2026-05-11_daily_report.md
?? reports/daily/2026-05-12_daily_report.md
?? reports/intraday/
?? reports/observation/2026-05-07_trade_log_vs_holdings_audit.md
?? reports/observation/2026-05-08_observation_summary.md
?? reports/observation/2026-05-11_observation_summary.md
?? reports/replay/
?? reports/validation/
?? reports/web/history.html
?? reports/web/status.html
```

## Notes

> Generated files (reports, logs, snapshots) are runtime outputs only.
> They are NOT committed to git.

*Generated at: 2026-05-12 09:15:11*