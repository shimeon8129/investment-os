# Investment OS｜System Status

## Current Repository

Repo:
https://github.com/shimeon8129/investment-os

Current working branch:
add-daily-decision-dashboard-v0-20260426_2057

Latest snapshot pushed:
2026-05-01

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
   - Now runs: daily_decision_dashboard, smoke tests, pipeline_main_v1.
   - Daily report includes Mainline Snapshot section (market state, top ranked, decisions).
   - Latest run: PASS (2026-05-01)

## MVP Progress

~90% complete.

Remaining:
- Ticker hygiene: 8046.TWO and 3189.TWO return no price data (possibly delisted). Non-blocking.
- Human summary / report polish.

## Current Priority

Do not add new modules.

Focus on:
- Ticker hygiene (remove or replace delisted tickers)
- Human summary and daily report polish
- Snapshot output review
