# Investment OS｜System Status

## Current Repository

Repo:
https://github.com/shimeon8129/investment-os

Current working branch:
add-daily-decision-dashboard-v0-20260426_2057

Latest snapshot pushed:
2026-05-02

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
   - Runs: daily_decision_dashboard, smoke tests, pipeline_main_v1.
   - Market calendar gate v0.1 integrated: skips pipeline when TW is closed.
   - Daily report includes Market Calendar section and Mainline Snapshot section.
   - Latest run: MARKET_CLOSED (2026-05-02, weekend)

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

## MVP Progress

~98% complete.

Remaining:
- Branch merge readiness review (R-001 to R-011).
- v0.2 market context (future, gated on explicit approval).

## Session Close Status — 2026-05-02 (final)

MVP candidate is stable at ~98%. All planned polish tasks complete.

Summary of session state:
- Step 1 COMPLETE: memory/00_PROJECT_BRAIN.md separates Core Value from Safety Boundary,
  includes memory/04_SYSTEM_AUDIT.md in session-start recall, has System Audit Memory Rule.
- Step 2 COMPLETE: session close memory and audit structure updated.
- Step 3 COMPLETE: jobs/daily_run.py now adds Human Summary section to daily reports.
  Market-closed report: no new trading decision, TW/US market status, v0.1 skip note, advisory-only.
  Open-market report: market_state, market_score, VIX, top 3 candidates with scores,
  decision counts by action, advisory-only note.
- R-004 Human summary/report polish: RESOLVED.
- Next ready task: Branch merge readiness review (R-001 to R-011).
- Market Context Gate v0.2: DEFERRED (R-001/R-002/R-003/R-011), approval required.
- No runtime code changes this session close. No sensitive investment data changes.
