# Investment OS｜Next Action

## Current State

✅ MVP 100% complete. Merged to main 2026-05-07.
Merge commit: d7cb447 — "Merge Investment OS MVP — Architecture v0.1 + v1.6 P0/P1/P2-A"
Active baseline: main branch.

Active components on main:
- pipeline/main_v1.py — advisory snapshot producer, runs cleanly (34 tickers)
- jobs/daily_run.py — market calendar gate v0.1, daily report, P1 audit integrated
- audit/p1_entry_audit.py — P1 parallel audit runner (advisory, non-blocking)
- utils/market_calendar.py — OPEN / CLOSED_WEEKEND / CLOSED_HOLIDAY / OPEN_EARLY_CLOSE
- config/market_calendar.json — TW and US 2026 calendars

Post-merge validation on main: ALL PASS (2026-05-07, TW OPEN)
- py_compile × 4: PASS
- tests/smoke_p1_entry_audit.py: 20/20 PASS
- python3 -m jobs.daily_run: 5 subprocesses ALL PASS

Audit: memory/04_SYSTEM_AUDIT.md (updated 2026-05-07) — 12 risks assessed (R-012 accepted).

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

3. Human summary / report polish — Audit: R-004 | Priority: P1 | Status: ✅ RESOLVED
   - COMPLETE. jobs/daily_run.py now adds Human Summary to both market-closed and
     open-market report paths. Market-closed: no new decision, market status, v0.1
     skip note, advisory-only. Open-market: market_state/score/VIX, top 3 candidates,
     decision counts, advisory-only. Commit: 10a02e3.

4. Branch merge to main — Audit: R-001 to R-012 | Priority: P1 | Status: ✅ COMPLETE
   - Merged 2026-05-07. Commit d7cb447 on origin/main.
   - F-001 RESOLVED: pipeline/main.py reverted to main.
   - R-012 ACCEPTED: execution/risk.py SINGLE_POSITION_EXCEED PASS_ADJUSTED approved.
   - Sensitive data A3/A4/A5 approved: current_holdings.json, trade_log.json, watchlist.json v0.4.
   - Post-merge validation on main: ALL PASS.
   - R-007 (decision_engine.py): orphaned file remains OPEN / out-of-scope; no blocking.

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
- Modify decision/decision_engine.py (out of scope until explicitly scoped)
- Remove or mutate sensitive investment data without explicit user approval
- Implement v0.2 market context until explicitly approved

Do:
- Work on a branch (for any new feature work)
- Read repo memory before each task
- Make minimal targeted changes
- Validate before committing
- Classify provider failures as data_warning, not deletion triggers
- Reference audit risk IDs when proposing changes
