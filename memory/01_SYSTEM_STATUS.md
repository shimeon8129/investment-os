# Investment OS｜System Status

## Current Repository

Repo:
https://github.com/shimeon8129/investment-os

Current working branch:
main

Latest snapshot pushed:
2026-05-14

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
   - Daily report includes: Data Freshness, Market Calendar, Human Summary,
     Mainline Snapshot, P1 Entry Audit, Checks, Safety, Output Files sections.
   - v0.2-lite patch (2026-05-08): added ## Data Freshness to both report paths;
     snapshot now includes run_date, market_date, market_status,
     latest_full_trading_day, data_as_of_date (UNKNOWN), data_mode, report_label,
     data_freshness_warning. Commit: 1e5e6cf.
   - Latest run: ALL PASS (2026-05-08, TW OPEN)

## Market Calendar Gate

v0.1 (current):
- config/market_calendar.json: TW and US holiday + early_close calendars.
- utils/market_calendar.py: classifies OPEN, CLOSED_WEEKEND, CLOSED_HOLIDAY,
  OPEN_EARLY_CLOSE. get_market_context() returns per-market status dict.
  get_latest_full_trading_day(market, d) added (2026-05-08): returns most recent
  completed trading day strictly before d.
- jobs/daily_run.py: if TW not open, writes MARKET_CLOSED snapshot and report.
  v0.2-lite (2026-05-08): both report paths now include ## Data Freshness section
  with report_label, data_as_of_date=UNKNOWN, latest_full_trading_day, data_mode=OBSERVATION.

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

## Intraday Observation Automation — v0.1 (2026-05-08)

### Phase A — Manual Runner (commit a10e0f2)
- jobs/intraday_observation.py: accepts one slot arg, runs jobs.daily_run,
  captures git status before/after, writes slot report/log/snapshot copies.
- scripts/run_intraday_observation.sh: shell wrapper, sets PYTHONPATH.
- Supported slots: pre_market | market_open | mid_morning |
  noon_review | pre_close | post_close_review
- Outputs written to:
  reports/intraday/YYYY-MM-DD/HHMM_<slot>.md
  logs/intraday/YYYY-MM-DD/HHMM_<slot>.log
  data/processed/intraday/YYYY-MM-DD/HHMM_{signal,mainline}_snapshot.json
- All 6 manual slot dry runs: PASS (2026-05-08)

### Phase B — systemd User Timers (commit 1b44a4a)
- systemd/investment-os-intraday-observation@.service: template service
- 6 timers (Mon..Fri, Asia/Taipei system timezone):
  - investment-os-intraday-pre-market.timer     → 08:30
  - investment-os-intraday-market-open.timer    → 09:05
  - investment-os-intraday-mid-morning.timer    → 10:30
  - investment-os-intraday-noon-review.timer    → 12:00
  - investment-os-intraday-pre-close.timer      → 13:10
  - investment-os-intraday-post-close.timer     → 14:30
- All timers: enabled, active (waiting). Next trigger: 2026-05-08 08:30 CST.
- Manual systemd service test: status=0/SUCCESS (market_open, 01:10 CST)
- Note: TimeZone= key ignored by this systemd version (non-blocking;
  system TZ = Asia/Taipei so OnCalendar fires at correct wall-clock time).
- Existing 16:00 observation automation: untouched.

### Stash — WIP Price Context Reporting
- stash@{0}: "WIP price context reporting before intraday timers"
  - decision/entry_lock_engine.py: price_data added to _evaluate_ticker return dict
  - reporting/p1_entry_audit_report.py: _section_price_context() added
  - Status: stashed for owner review. Needs explicit decision: commit or drop.
  - Do not implement or commit without owner approval.

## Session Status — 2026-05-13 System Snapshot

Feature branch `add-daily-decision-dashboard-v0-20260426_2057` fully absorbed by main.
Active baseline is now main. Intraday observation automation active.

- Architecture v0.1 + v1.6 P0/P1/P2-A: ✅ merged, validated, operational.
- v0.2-lite Report Truthfulness Patch: ✅ applied 2026-05-08, commit 1e5e6cf.
- MVP-Auto-Intraday-Observation Phase A: ✅ commit a10e0f2 (2026-05-08).
- MVP-Auto-Intraday-Observation Phase B: ✅ commit 1b44a4a (2026-05-08).
  6 systemd user timers enabled.
- 2026-05-13 system state snapshot: ✅ commit 3e58b1b, pushed to origin/main.
  Large snapshot commit (227 files, +53,496 lines) — not the preferred workflow.
  Future changes should return to small scoped commits.
- Runtime outputs (candidates.json, processed/*.json, daily reports,
  intraday reports/logs): NOW COMMITTED as of 2026-05-13 snapshot.
- Market Context Gate v0.2 full implementation: still DEFERRED (R-001/R-011), approval required.
- R-002 and R-003: PARTIAL — surfaced via v0.2-lite patch. Full automation deferred.

### 2026-05-13 Holdings (as_of: 2026-05-13)

- 00992A: REMOVED
- 2308 台達電: ADDED (20 shares @ 2253.20)
- 2330 台積電: 30 shares @ 1767.50
- 2345 智邦: 65 shares @ 1914.22
- 2408 南亞科: 120 shares @ 236.33
- 3711 日月光投控: 50 shares @ 412.58
- 6830 汎銓: 70 shares @ 735.99
- 009816 凱基台灣TOP50: 5000 shares @ 11.42

### 2026-05-13 Pipeline Output

- Exit signals: 6830 EXIT_ALL (SELL), 2308/2330/2345 REDUCE — now visible in mainline_snapshot.json
- vol_ratio / vol_bonus now reflected in ranked output
- Daily report 2026-05-13: runtime status PASS

## Build Plan v0.1 Status — Technical Action Engine (2026-05-14)

Completed: 6 commits (a0e2cc0 → cfdf659) pushed to origin/main.

1. a0e2cc0 — feat(analysis): technical action mode + chase risk v0.1
   - analysis/technical_action_mode.py: classify_action_mode() → 8 action modes
   - analysis/chase_risk.py: compute_chase_risk() → LOW/MEDIUM/HIGH/EXTREME
   - tests/smoke_technical_action_mode.py: 11 tests PASS

2. f348a80 — feat(reporting): technical action summary in daily report
   - jobs/daily_run.py: Technical Action Summary table + Holding Alerts + Data Coverage section

3. 12de5bd — feat(data): chips refresh pipeline v0.1
   - data_node/chips_fetcher.py: wraps steps/fetch_chips.py, writes latest_chips.json
   - data/chips/latest_chips.json: 1316 tickers, TWSE 2026-05-13 / TPEX 2026-05-14 (FRESH)
   - tests/smoke_chips_fetcher.py: 10 tests PASS

4. 1e91089 — feat(data): news heat refresh pipeline v0.1
   - data_node/news_heat_fetcher.py: freshness FRESH(≤3d)/RECENT(≤7d)/STALE/MISSING
   - tests/smoke_news_heat_fetcher.py: 6 tests PASS

5. 69f18e2 — feat(data): narrative refresh candidate builder v0.1
   - data_node/narrative_refresh_builder.py: CANDIDATE_ONLY, never overwrites final_narrative.json
   - tests/smoke_narrative_refresh.py: 7 tests PASS

6. af695ec — feat(reporting): integrate chips/news/narrative into action report
   - reporting/technical_action_report.py: enrich_ranked_with_action() adds chip_status,
     chip_freshness, news_freshness, narrative_status, suggested_action, invalid_if
   - pipeline/main_v1.py: enrichment wired after exit check

Hotfix: cfdf659 — fix(chips): chips_loader dual-path + dual-index
   - pipeline/chips_loader.py: tries latest_chips.json first, falls back to latest.json
   - Indexes by both ticker (2356.TW) and code (2356)
   - Root cause: chips_fetcher writes to latest_chips.json, old loader read latest.json only

### 2026-05-14 Pipeline Output (Technical Action Engine first run)

- System mode: TECHNICAL_DOMINANT_WITH_DATA_CONTEXT
- Market state: BULL
- Top 3 ranked:
  - 2356.TW 英業達: TECH_ATTACK | chip_status=STRONG_POSITIVE | chip_freshness=FRESH
  - 2377.TW 微星:   TECH_ATTACK | chip_status=STRONG_POSITIVE | chip_freshness=FRESH
  - 2376.TW 技嘉:   TECH_BUY    | chip_status=STRONG_POSITIVE | chip_freshness=FRESH
- Summary: tech_attack=2, tech_buy=2, tech_buy_caution=6, tech_watch=0, tech_reduce=0
- Snapshot: data/processed/mainline_snapshot.json (generated 2026-05-14T01:37:36)
- Chips: 1316 tickers fetched (data_node/chips_fetcher.py)
- All 48 smoke tests: PASS (eeb6efe baseline)

### Observation Phase Continues

- No new feature expansion approved by this snapshot.
- Do not implement Minervini debug, Chips negative penalty, NewsHeat automation,
  ticker normalization, or Market Context Gate v0.2 until explicitly approved.
- Do not implement new features. Do not modify runtime logic. Do not start full v0.2.
