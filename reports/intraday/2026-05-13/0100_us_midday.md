# Investment OS Intraday Observation — us_midday

**Slot:** us_midday
**Run timestamp:** 2026-05-14 01:00:36
**Git branch:** main
**Latest commit:** a73503b

## Git Status Before Run

- Branch: main
- Latest commit: a73503b
- Working tree: CLEAN

```
?? .claude/
```

## Runtime

- Command: `python3 -m jobs.daily_run_us`
- Runtime final status: **PASS**

## Output Paths

- Daily report: `/home/shimeon/investment_os/reports/daily/2026-05-13_daily_report.md` (EXISTS)
- Signal snapshot: `/home/shimeon/investment_os/data/processed/signal_snapshot.json` (EXISTS)
- Mainline snapshot: `/home/shimeon/investment_os/data/processed/mainline_snapshot.json` (EXISTS)
- Slot report: `/home/shimeon/investment_os/reports/intraday/2026-05-13/0100_us_midday.md`
- Slot log: `/home/shimeon/investment_os/logs/intraday/2026-05-13/0100_us_midday.log`
- Intraday signal snapshot: `/home/shimeon/investment_os/data/processed/intraday/2026-05-13/0100_signal_snapshot.json`
- Intraday mainline snapshot: `/home/shimeon/investment_os/data/processed/intraday/2026-05-13/0100_mainline_snapshot.json`

## Data Freshness

- report_label: `TODAY_MARKET_OPEN`
- run_date: 2026-05-13
- market_date: 2026-05-13
- market_status (TW): OPEN
- latest_full_trading_day (TW): 2026-05-12
- data_as_of_date: UNKNOWN
- data_mode: OBSERVATION
> **Warning:** Data vintage not explicitly available in current MVP pipeline.

## Market Status

- TW market status: OPEN
- report_label: TODAY_MARKET_OPEN
- data_as_of_date: UNKNOWN
- latest_full_trading_day: 2026-05-12

## Market State / Score / VIX

- market_state: N/A
- market_score: N/A
- VIX: N/A

## Top Ranked Candidates

1. 2356.TW 英業達 — Score: 155.53 | Signal: BUY | Role: WAVE_SWING/WAVE_SWING [LOW] intent=—
2. 2377.TW 微星 — Score: 154.20 | Signal: BUY | Role: UNKNOWN/UNKNOWN [UNKNOWN] intent=—
3. 2376.TW 技嘉 — Score: 145.20 | Signal: BUY | Role: WAVE_SWING/WAVE_SWING [MEDIUM] intent=—
4. 3583.TW 辛耘 — Score: 128.00 | Signal: BUY | Role: UNKNOWN/UNKNOWN [UNKNOWN] intent=—
5. 2467.TW 志聖 — Score: 118.20 | Signal: BUY | Role: UNKNOWN/UNKNOWN [UNKNOWN] intent=—

## P1 Entry Audit Summary

total=10 EntryLock(PASS=0 WARN=0 BLOCK=10) Action(ENTRY=0 WAIT=10 SKIP=0) Divergences=10

## Manual Review Flags

- EXIT_ALL |

## Data Warnings / Regression Notes

- (none detected)

## Git Status After Run

- Working tree: CLEAN

```
?? .claude/
?? data/processed/intraday/2026-05-13/0100_mainline_snapshot.json
?? data/processed/intraday/2026-05-13/0100_signal_snapshot.json
```

## Notes

> Generated files (reports, logs, snapshots) are runtime outputs only.
> They are NOT committed to git.

*Generated at: 2026-05-14 01:00:36*