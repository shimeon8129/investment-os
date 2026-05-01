# Investment OS｜Next Action

## Current State

MVP is ~95% complete and stable.

Active components:
- pipeline/main_v1.py — advisory snapshot producer, runs cleanly (34 tickers)
- jobs/daily_run.py — market calendar gate v0.1, daily report with snapshot
- utils/market_calendar.py — OPEN / CLOSED_WEEKEND / CLOSED_HOLIDAY / OPEN_EARLY_CLOSE
- config/market_calendar.json — TW and US 2026 calendars

Latest run: MARKET_CLOSED (2026-05-02, Saturday — correct behavior)

## Next Engineering Tasks

Priority order:

1. Ticker hygiene (resolved + standing rule)
   - 8046 and 3189 suffix issue has been fixed: .TWO → .TW in data/universe_tw.csv.
   - Do not remove user-observed tickers because of provider warnings (yfinance
     no price data is a data_warning, not deletion permission).
   - Future ticker hygiene: classify provider failures as data_warning, surface in
     reports, investigate alternate sources, and require explicit user approval
     before any sensitive investment data change.

2. Memory and state review (immediate)
   - Verify memory/ files are accurate and current.
   - Confirm branch commit history is coherent.
   - No code changes required.

3. Human summary / report polish
   - Review reports/daily output for readability.
   - Improve Mainline Snapshot section formatting if needed.
   - No new modules.

4. Branch merge planning (optional, when ready)
   - Review diff between add-daily-decision-dashboard-v0-20260426_2057 and main.
   - Confirm no regressions before merge.
   - Merge only after explicit user approval.

5. Market context gate v0.2 (future — do not implement until explicitly approved)
   - Spec defined in docs/MARKET_CONTEXT_GATE_V0_2.md.
   - Adds: latest_full_trading_day, data_as_of_date, data_mode, pipeline_policy,
     report_label per market.
   - Key principle: market closed ≠ no data; pipeline should run using latest
     valid trading day, not skip.
   - Implementation sequence in spec. Gate on MVP merge first.

6. Market session phase enhancement (future, post-MVP)
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
- Remove or mutate sensitive investment data without explicit user approval
- Implement v0.2 market context until explicitly approved

Do:
- Work on a branch
- Read repo memory before each task
- Make minimal targeted changes
- Validate before committing
- Classify provider failures as data_warning, not deletion triggers
