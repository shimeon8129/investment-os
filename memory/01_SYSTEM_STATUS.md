# Investment OS｜System Status

## Current Repository

Repo:
https://github.com/shimeon8129/investment-os

Current working branch:
main

Latest snapshot pushed:
2026-05-07

## Current Reality

The system already contains many modules:
- data_node
- scanner
- processing
- signal_engine
- decision
- execution
- feedback
- pipeline
- reporting
- jobs
- docker/hermes-agent
- tools
- tests
- utils (new: market_calendar.py)
- config (new: market_calendar.json)

The problem is not missing modules.

Mainline fragmentation has been largely resolved.

## Known Mainlines

1. pipeline/main.py
   - Legacy. Preserved as historical reference.
   - Contains duplicate Block A (dead) + Block B (active).
   - Do not modify.

2. pipeline/main_v1.py ✅ ACTIVE
   - Clean extraction of Block B from pipeline/main.py.
   - Advisory-only snapshot producer.
   - Writes data/processed/mainline_snapshot.json on every run.
   - Validated standalone and integrated into daily runner.

3. decision/decision_engine.py
   - Standalone, disconnected. Not in active use.
   - Out of scope for current consolidation.

4. jobs/daily_run.py ✅ ACTIVE
   - Hermes-compatible daily runtime orchestrator.
   - Runs: daily_decision_dashboard, smoke tests, pipeline_main_v1, p1_entry_audit.
   - p1_entry_audit is non-blocking advisory (P2-A); failure does not affect status.
   - Market calendar gate v0.1 integrated: skips pipeline when TW is closed.
   - Daily report includes: Market Calendar, Human Summary, Mainline Snapshot,
     P1 Entry Audit, Checks, Safety, Output Files sections.
   - Latest run: ALL PASS (2026-05-07, TW OPEN)

## Market Calendar Gate

v0.1 (current):
- config/market_calendar.json: TW and US holiday + early_close calendars.
- utils/market_calendar.py: classifies OPEN, CLOSED_WEEKEND, CLOSED_HOLIDAY,
  OPEN_EARLY_CLOSE. get_market_context() returns per-market status dict.
- jobs/daily_run.py: if TW not open, writes MARKET_CLOSED snapshot and report.

v0.2 (spec only — do not implement until explicitly approved):
- Defined in docs/MARKET_CONTEXT_GATE_V0_2.md.
- Adds: latest_full_trading_day, data_as_of_date, data_mode, pipeline_policy,
  report_label per market.
- Key principle: market closed ≠ no data. Use latest valid trading day.

## Governance Rules (in 00_PROJECT_BRAIN.md)

- Sensitive Investment Data Protection Rule: provider failure ≠ deletion
  permission. yfinance no price data is a data_warning, not proof of delisting.
  Explicit user approval required before any sensitive data change.
- Local Claude Code Git Workflow Rule: read memory first, minimal change, validate,
  commit/push only if validation passes.
- Claude Code Token Discipline Rule: ChatGPT decides scope; Claude Code executes
  precise patches only.

## Known Ticker Fix

8046.TWO and 3189.TWO had .TWO suffix mismatch with yfinance.
Fixed to 8046.TW (南電, PCB, CORE) and 3189.TW (景碩, PCB, LAG).
Both confirmed loading cleanly.

## Architecture v1.6 Status

- P0 (EntryLockEngine, TradeSetupBuilder, PositionSizing): ✅ COMPLETE
- P1 (p1_entry_audit parallel runner): ✅ COMPLETE — merged from architecture-v1-6-p1-audit
- P2-A (daily_run.py P1 integration): ✅ COMPLETE — non-blocking advisory subprocess

## MVP Progress

✅ 100% complete. All architecture phases merged to main.

Merge commit: d7cb447 — "Merge Investment OS MVP — Architecture v0.1 + v1.6 P0/P1/P2-A"
Merged: 2026-05-07.

Post-merge validation on main:
- py_compile × 4: ALL PASS
- tests/smoke_p1_entry_audit.py: 20/20 PASS
- python3 -m jobs.daily_run (2026-05-07, TW OPEN): ALL PASS

Next phase: observation. No feature expansion until explicitly approved.

## Session Status — 2026-05-07 Observation Phase

Feature branch `add-daily-decision-dashboard-v0-20260426_2057` fully absorbed by main.
Active baseline is now main. Observation phase active.

- Architecture v0.1 + v1.6 P0/P1/P2-A: ✅ merged, validated, operational.
- First post-merge observation run: 2026-05-07, TW OPEN — ALL PASS (5 subprocesses).
  Outputs: data/processed/signal_snapshot.json, reports/daily/2026-05-07_daily_report.md
- No post-merge regression detected.
- Runtime outputs (candidates.json, processed/*.json, daily reports): NOT committed (expected).
- Market Context Gate v0.2: DEFERRED (R-001/R-002/R-003/R-011), approval required.
- Do not implement new features. Do not modify runtime logic. Do not start v0.2.
