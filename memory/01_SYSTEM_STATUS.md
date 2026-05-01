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

The problem is mainline fragmentation.

## Known Mainlines

1. pipeline/main.py
   - Most complete historical decision pipeline
   - Contains technical debt and duplicated blocks

2. decision/decision_engine.py
   - Entry-focused decision engine

3. jobs/daily_run.py
   - Hermes-compatible daily runtime / reporting orchestrator

## Current Priority

Do not add new modules.

Focus on:
- Pipeline consolidation
- Clean runtime integration
- Snapshot output unification
- Human summary / report integration
