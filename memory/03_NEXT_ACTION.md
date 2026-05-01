# Investment OS｜Next Action

## Current State

MVP is ~95% complete and stable.

Active components:
- pipeline/main_v1.py — advisory snapshot producer, runs cleanly (34 tickers)
- jobs/daily_run.py — market calendar gate v0.1, daily report with snapshot
- utils/market_calendar.py — OPEN / CLOSED_WEEKEND / CLOSED_HOLIDAY / OPEN_EARLY_CLOSE
- config/market_calendar.json — TW and US 2026 calendars

Latest run: MARKET_CLOSED (2026-05-02, Saturday — correct behavior)

Audit: memory/04_SYSTEM_AUDIT.md (2026-05-02) — 11 risks assessed.

## Next Engineering Tasks

Priority order:

1. Ticker hygiene (resolved + standing rule) — Audit: R-008, R-009 RESOLVED
   - 8046 and 3189 suffix issue has been fixed: .TWO → .TW in data/universe_tw.csv.
   - Do not remove user-observed tickers because of provider warnings (yfinance
     no price data is a data_warning, not deletion permission).
   - Future ticker hygiene: classify provider failures as data_warning, surface in
     reports, investigate alternate sources, and require explicit user approval
     before any sensitive investment data change.

2. Memory and state review — COMPLETE (fulfilled by audit 2026-05-02)
   - memory/04_SYSTEM_AUDIT.md written. Risk register and remediation plan in place.

3. Human summary / report polish — Audit: R-004 | Priority: P1 | Status: READY
   - Review reports/daily output for readability.
   - Improve Mainline Snapshot section formatting in jobs/daily_run.py report template.
   - No new modules. No approval required.

4. Branch merge readiness review — Audit: R-001 to R-011 | Priority: P1/P2
   - Review diff between add-daily-decision-dashboard-v0-20260426_2057 and main.
   - Verify all P0/P1 risks are resolved or accepted before merge.
   - Review decision/decision_engine.py status (R-007): document or mark for deprecation.
   - Merge only after explicit user approval. Do not merge without approval.

5. Market Context Gate v0.2 — Audit: R-001, R-002, R-003, R-011 | Priority: P3 | Status: DEFERRED
   - DEFERRED. Do not implement until explicitly approved by user.
   - Spec defined in docs/MARKET_CONTEXT_GATE_V0_2.md.
   - Addresses: latest_full_trading_day, data_as_of_date, data_mode, pipeline_policy,
     report_label per market. Key principle: market closed ≠ no data.
   - Gate on MVP branch merge first. Approval required before any code change.

6. Market session phase enhancement — Audit: R-011 | Priority: P3 | Status: DEFERRED
   - DEFERRED. Do not implement until explicitly approved.
   - utils/market_calendar.py currently classifies: OPEN, CLOSED_WEEKEND,
     CLOSED_HOLIDAY, OPEN_EARLY_CLOSE.
   - Future: add PRE_MARKET, REGULAR_SESSION, POST_MARKET, CLOSED_BY_TIME.
   - Part of v0.2 scope. Post-MVP only.

## Monitor (no action unless triggered)

- R-005: subprocess timeout 90s — MONITOR; act only if pipeline_main_v1 times out
- R-006: stale 2026-05-01 report — ACCEPTED historical artifact; no action
- R-010: calendar source completeness — FUTURE; cross-check before 2027; approval required for any calendar data change

## Guardrails

Do not:
- Add new decision modules
- Add new market engine modules
- Expand external AI agents
- Modify broker/execution automation
- Modify pipeline/main.py (legacy, preserved as reference)
- Modify decision/decision_engine.py (out of scope until merge review)
- Remove or mutate sensitive investment data without explicit user approval
- Implement v0.2 market context until explicitly approved
- Merge branch to main without explicit user approval

Do:
- Work on a branch
- Read repo memory before each task
- Make minimal targeted changes
- Validate before committing
- Classify provider failures as data_warning, not deletion triggers
- Reference audit risk IDs when proposing changes
