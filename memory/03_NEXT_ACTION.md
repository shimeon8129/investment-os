# Investment OS｜Next Action

## Current State

Mainline MVP integration is complete (~90%).

pipeline/main_v1.py is live inside jobs/daily_run.py.
Daily report includes Mainline Snapshot section.
Latest full run: PASS.

## Next Engineering Tasks

Priority order:

1. Ticker hygiene
   - Remove or replace 8046.TWO and 3189.TWO from universe (delisted, no price data).
   - Edit only scanner/universe.py or the relevant universe source file.
   - Validate with python3 -m pipeline.main_v1 — confirm no delisted warnings.

2. Human summary / report polish
   - Review reports/daily output for readability.
   - Improve Mainline Snapshot section formatting if needed.
   - No new modules.

3. Branch merge to main (when ready)
   - After ticker hygiene and report polish pass validation.

4. Market session phase enhancement (future, post-MVP)
   - utils/market_calendar.py currently classifies: OPEN, CLOSED_WEEKEND,
     CLOSED_HOLIDAY, OPEN_EARLY_CLOSE.
   - It does not yet classify intraday phases: PRE_MARKET, REGULAR_SESSION,
     POST_MARKET, CLOSED_BY_TIME.
   - Add as a future enhancement after MVP stabilization. Do not implement now.

## Guardrails

Do not:
- Add new decision modules
- Add new market engine modules
- Expand external AI agents
- Modify broker/execution automation
- Modify pipeline/main.py (legacy, preserved as reference)
- Modify decision/decision_engine.py (out of scope)

Do:
- Work on a branch
- Read repo memory before each task
- Make minimal targeted changes
- Validate before committing
