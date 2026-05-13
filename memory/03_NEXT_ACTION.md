# Investment OS｜Next Action

## Current State

✅ MVP 100% complete. Merged to main 2026-05-07.
✅ MVP-Auto-Intraday-Observation v0.1 Phase A + B complete. 2026-05-08.
✅ Memory-only sync complete. 2026-05-13.

Merge commit: d7cb447 — "Merge Investment OS MVP — Architecture v0.1 + v1.6 P0/P1/P2-A"
Latest commit: chore(memory) — memory sync after 2026-05-13 snapshot
Active baseline: main branch.

Active components on main:
- pipeline/main_v1.py — advisory snapshot producer, runs cleanly (34 tickers)
- jobs/daily_run.py — market calendar gate v0.1, daily report, P1 audit integrated
- audit/p1_entry_audit.py — P1 parallel audit runner (advisory, non-blocking)
- utils/market_calendar.py — OPEN / CLOSED_WEEKEND / CLOSED_HOLIDAY / OPEN_EARLY_CLOSE
- config/market_calendar.json — TW and US 2026 calendars
- jobs/intraday_observation.py — manual intraday slot runner (Phase A, a10e0f2)
- scripts/run_intraday_observation.sh — shell wrapper for intraday runner
- systemd/investment-os-intraday-observation@.service — template service (Phase B, 1b44a4a)
- systemd/investment-os-intraday-*.timer (×6) — Mon..Fri timers 08:30–14:30 CST

Intraday timers status (2026-05-08 01:12 CST):
- All 6 timers: enabled, active (waiting)
- Next trigger: 2026-05-08 08:30 CST (pre_market)
- Monitor: journalctl --user -u 'investment-os-intraday-*' -f

Stash on hold (requires owner decision before resuming):
- stash@{0}: "WIP price context reporting before intraday timers"
  Files: decision/entry_lock_engine.py, reporting/p1_entry_audit_report.py
  Nature: additive price_data field + Price Context report section
  Action needed: owner approve to commit, or git stash drop to discard

Audit: memory/04_SYSTEM_AUDIT.md (updated 2026-05-08) — 13 risks assessed (R-002/R-003 PARTIAL via v0.2-lite patch).
Position source fix: commit b4a9e07. Active positions now from current_holdings.json.
v0.2-lite patch: commit 1e5e6cf (2026-05-08). Data Freshness section in daily report + snapshot.

## Immediate Next (After Memory Sync)

1. ✅ COMPLETE — Memory-only sync commit (this session).
2. No new feature work until memory/audit state confirmed aligned.
3. If a review of the large 2026-05-13 snapshot commit is needed, perform it as a
   separate session with explicit scope.

## Deferred Work (Do Not Start Until Explicitly Approved)

- Minervini score debug — all 10 candidates score 0, cause unknown
- Chips coverage expansion — 4/10 no data, no negative penalty mechanism
- NewsHeat automation — API integration needed, 1/10 coverage
- Ticker format normalization — .TW/.TWO suffix mismatch with holdings
- Market Context Gate v0.2 / data_as_of_date resolution
- Fundamentals (EPS, ROE, growth filters) — completely absent

## Previous Engineering Tasks

Priority order:

0. Position source fix — ✅ RESOLVED (2026-05-07, commit b4a9e07)
   - execution/portfolio.py: added load_portfolio_from_holdings() from current_holdings.json.
   - pipeline/main_v1.py: switched portfolio = load_portfolio_from_holdings().
   - load_portfolio() (trade_log) retained for advisory/performance use only.
   - Validation: full observation wrapper ALL PASS (5 subprocesses).
   - Audit report: reports/observation/2026-05-07_trade_log_vs_holdings_audit.md.

0a. 6830.TW 汎銓 — EXIT_ALL manual review flag ⚠️ OPEN
   - After position source fix, check_exit() evaluated 6830 using broker entry_price=712.8.
   - Trailing stop (drawdown from 1y highest > 7%) triggered EXIT_ALL.
   - This is NOT a regression. It is expected behavior after using real broker entry price.
   - Action required: manual owner review of 6830 position before any real-world decision.
   - No code change needed. Advisory signal only.

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

5. Market Context Gate v0.2 full — Audit: R-001, R-002, R-003, R-011 | Priority: P3 | Status: PARTIAL/DEFERRED
   - v0.2-lite patch applied 2026-05-08 (commit 1e5e6cf): R-002 and R-003 partially addressed.
     data_as_of_date=UNKNOWN, report_label, latest_full_trading_day now surfaced.
   - Full v0.2 still DEFERRED. Do not implement until explicitly approved by user.
   - Spec defined in docs/MARKET_CONTEXT_GATE_V0_2.md.
   - Remaining: derived data_as_of_date from pipeline data, pipeline_policy per market,
     running pipeline on closed days using latest_full_trading_day data.
   - Key principle: market closed ≠ no data. Approval required before any further code change.

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
