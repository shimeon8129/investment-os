# Investment OS｜Session Log

## 2026-05-08 — v0.2-lite Report Truthfulness Patch

Session summary:
- Applied minimal report truthfulness patch to address R-002 and R-003 (partial).
- No trading logic, scoring, EntryLockEngine, or decision rules modified.
- Changes: 2 files, 50 insertions. Commit 1e5e6cf pushed to origin/main.

utils/market_calendar.py:
- Added `timedelta` import.
- Added `get_latest_full_trading_day(market, d)`: returns most recent completed
  trading day strictly before d by scanning backwards up to 30 days.

jobs/daily_run.py:
- Import `get_latest_full_trading_day`.
- After `get_market_context()`, compute `_FRESHNESS_META` dict and `_FRESHNESS_LINES`
  markdown block containing: report_label, run_date, market_date, market_status,
  latest_full_trading_day, data_as_of_date=UNKNOWN, data_mode=OBSERVATION,
  data_freshness_warning.
- report_label logic: TODAY_MARKET_OPEN if TW open, else MARKET_CLOSED_SNAPSHOT.
- _FRESHNESS_META spread into signal_snapshot.json (both market-open and market-closed paths).
- _FRESHNESS_LINES inserted into daily report as ## Data Freshness section
  (before ## Runtime Status on market-closed path; before ## Market Calendar on open path).

Validation:
- py_compile jobs/daily_run.py: PASS
- py_compile utils/market_calendar.py: PASS
- python3 -m jobs.daily_run (2026-05-08, TW OPEN): ALL PASS
- smoke_daily_decision_dashboard: PASS
- smoke_portfolio_holdings: PASS
- GitHub remote read verification (market_calendar.py + daily_run.py): PASS
- ## Data Freshness in 2026-05-08_daily_report.md: PASS

Risk register updates:
- R-002 (data_as_of_date missing): ⚠️ PARTIAL — data_as_of_date=UNKNOWN now surfaced.
  Full derived-date automation still gated on v0.2 approval.
- R-003 (report lacks data vintage label): ⚠️ PARTIAL — report_label now in
  ## Data Freshness. Full v0.2 Mainline Snapshot integration still deferred.
- R-001/R-011 (closed-day pipeline skip, market session phases): still DEFERRED.

No sensitive investment data changed. No Notion update this session (no new Notion page target specified).

## 2026-05-07 — Position source fix (trade_log → current_holdings)

Session summary:
- Ran Trade Log vs Current Holdings audit: FAIL verdict.
  Report: reports/observation/2026-05-07_trade_log_vs_holdings_audit.md
- Root cause: execution/portfolio.py:load_portfolio() treated advisory trade_log BUY rows
  as real broker positions. 4 advisory-only tickers (3583, 6187, 3680, 2449) were live
  in position lock and exit check; 6 real holdings (009816, 00992A, 2330, 2345, 2408, 6830)
  were invisible to both.
- Fix: added load_portfolio_from_holdings() in execution/portfolio.py — reads
  current_holdings.json, normalises ticker suffixes to .TW format.
  Updated pipeline/main_v1.py to use new function; load_portfolio() retained (advisory only).
- Validation: py_compile PASS, smoke_p1_entry_audit 20/20 PASS, smoke_portfolio_holdings PASS.
- Committed b4a9e07, pushed to origin/main.

## 2026-05-07 — MVP main merge completion

Session summary:
- Performed full merge readiness review for branch add-daily-decision-dashboard-v0-20260426_2057.
- Identified F-001 (pipeline/main.py guardrail violation) and F-002 (R-012:
  execution/risk.py SINGLE_POSITION_EXCEED PASS_ADJUSTED behaviour change).
- User approved: A1 R-012 PASS_ADJUSTED accepted, A2 pipeline/main.py revert,
  A3 current_holdings.json, A4 trade_log.json, A5 watchlist.json v0.4.
- Pre-merge cleanup: pipeline/main.py reverted to main state; memory files updated;
  all validations passed; cleanup committed and pushed.
- Merge executed: git merge --no-ff → commit d7cb447
  "Merge Investment OS MVP — Architecture v0.1 + v1.6 P0/P1/P2-A" pushed to origin/main.
- Post-merge validation on main: py_compile × 4 PASS, smoke_p1_entry_audit 20/20 PASS,
  daily_run ALL PASS (5 subprocesses: daily_decision_dashboard, smoke_daily_decision_dashboard,
  smoke_portfolio_holdings, pipeline_main_v1, p1_entry_audit).
- Feature branch add-daily-decision-dashboard-v0-20260426_2057 fully absorbed by main.
- Active baseline is now main. No runtime outputs committed (expected).
- Architecture v0.1 + v1.6 P0/P1/P2-A: all merged, validated, operational.
- Risk register at merge: R-001 to R-003 DEFERRED, R-004 RESOLVED, R-005/R-010 MONITOR,
  R-006 ACCEPTED, R-007 OPEN, R-008/R-009 RESOLVED, R-011 DEFERRED, R-012 ACCEPTED.

## 2026-05-02 — Session close (human summary polish)

Session close summary:
- Step 1 COMPLETE: memory/00_PROJECT_BRAIN.md — Core Rule split into Core Value and
  Safety Boundary; memory/04_SYSTEM_AUDIT.md added to session-start read list;
  System Audit Memory Rule added.
- Step 2 COMPLETE: memory audit and session-close structure updated with R-001 to R-011
  risk register, remediation plan, and next-action mapping.
- Step 3 COMPLETE (R-004): jobs/daily_run.py human summary polish.
  Market-closed path: Human Summary section shows no new trading decision, per-market
  status from market_context, v0.1 skip behavior note, advisory-only note.
  Open-market path: Human Summary section shows market_state, market_score (4dp),
  VIX (2dp), top 3 ranked candidates with scores (2dp), decision counts by action,
  advisory-only note.
- R-004 status: RESOLVED.
- No sensitive investment data changed. No runtime pipeline logic changed.
- Next ready task: Branch merge readiness review (links to R-001 to R-011).

## 2026-05-02 — Session close

Session close summary:
- System audit memory created: memory/04_SYSTEM_AUDIT.md with R-001 to R-011 risk register.
- Remediation plan completed: P0 (resolved), P1 (ready), P2 (monitor), P3 (deferred).
- Next-action mapping: all tasks in 03_NEXT_ACTION.md linked to audit risk IDs.
- Project Brain correction: ## Core Rule split into ## Core Value and ## Safety Boundary.
  Core Value now explicitly states Investment OS purpose (market profit, decision quality,
  trend identification, high-probability detection, swing discipline, risk awareness).
- memory/04_SYSTEM_AUDIT.md added to session-start read list in Memory Principle.
- System Audit Memory Rule added to 00_PROJECT_BRAIN.md.
- Market Context Gate v0.2 confirmed DEFERRED: R-001/R-002/R-003/R-011 gated on explicit approval.
- No runtime code changes this session. No sensitive investment data changes.

## 2026-05-02 — Market calendar and governance session

Major outcomes:

**Governance:**
- Added Sensitive Investment Data Protection Rule to memory/00_PROJECT_BRAIN.md.
  Rule: provider failure (yfinance no price data) is a data_warning, not deletion
  permission. Claude Code may not auto-remove sensitive investment data. Explicit
  user approval required before commit/push of any data change.
- Added Claude Code Token Discipline Rule to memory/00_PROJECT_BRAIN.md.
- Added Local Claude Code Git Workflow Rule to memory/00_PROJECT_BRAIN.md.

**Ticker fix:**
- 8046.TWO and 3189.TWO had wrong suffix for yfinance. Fixed to 8046.TW and
  3189.TW in data/universe_tw.csv. Roles preserved: 南電 PCB CORE, 景碩 PCB LAG.
- Confirmed both load cleanly. All 34 tickers now load without warnings.
- Correction noted: previous session auto-removed these tickers on provider
  warning — this violated the data protection rule. Rule retroactively applied.

**Market calendar:**
- Created config/market_calendar.json with TW and US 2026 holiday calendars.
- Created utils/market_calendar.py with load_calendar(), is_weekend(),
  is_market_open(), get_market_context(). Classifies OPEN, CLOSED_WEEKEND,
  CLOSED_HOLIDAY, OPEN_EARLY_CLOSE.
- Replaced hardcoded weekend guard in jobs/daily_run.py with get_market_context().
  market_context now written into signal_snapshot.json and daily_report.md.
- 2026-05-02 (Saturday): daily runner correctly produced MARKET_CLOSED report.

**Spec:**
- Created docs/MARKET_CONTEXT_GATE_V0_2.md defining v0.2 market-aware
  data_as_of logic: latest_full_trading_day, data_as_of_date, data_mode,
  pipeline_policy, report_label per market.
- Key correction recorded: market closed does not mean no data. Future v0.2
  should run pipeline using latest valid trading day, not skip it.
- v0.2 is spec only. Do not implement until explicitly approved.

## 2026-05-01 (continued — mainline MVP integration)

Major outcomes:
- Created pipeline/main_v1.py: clean extraction of Block B from pipeline/main.py.
  Applied surgical cleanups per docs/MAINLINE_REVIEW_20260501.md:
  removed debug prints, duplicate write_trade_log call, unused imports.
- Converted pipeline/main_v1.py to advisory-only snapshot producer:
  writes data/processed/mainline_snapshot.json with market state, candidates,
  signals, ranked, decisions, exit signals, and safety flags.
- Validated pipeline/main_v1.py standalone (python3 -m pipeline.main_v1): PASS.
- Integrated pipeline_main_v1 into jobs/daily_run.py as a new check block.
- Added Mainline Snapshot section to daily report:
  market state, market score, VIX, top 5 ranked table, decisions table.
- Full daily runner validation (python3 jobs/daily_run.py): PASS.

## 2026-05-01 (earlier)

Major outcomes:
- Confirmed Hermes daily runner works.
- Fixed human_summary.md Markdown formatting.
- Confirmed GitHub branch is pushed and clean.
- Confirmed Google Drive connector can read/list files but Google Docs write test failed with 403.
- Decided GitHub memory/ should be primary AI collaboration memory layer.
- Identified the real system issue: not missing modules, but fragmented mainlines.

Important correction:
- Do not assume missing modules.
- The repo already contains many components.
- Always inspect existing structure before proposing new files.

Current conclusion:
- Use GitHub memory/ as persistent collaboration memory.
- Use Google Drive only as secondary human-readable / NotebookLM layer.
