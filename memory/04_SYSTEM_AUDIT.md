# Investment OS｜System Audit

---

## Audit Entry: 2026-05-02

### Metadata

| Field | Value |
|-------|-------|
| Audit date | 2026-05-02 |
| Audited by | Claude Code (claude-sonnet-4-6) |
| Branch | add-daily-decision-dashboard-v0-20260426_2057 |
| Latest commit | 140d1f5 |
| Files reviewed | memory/00–03, docs/MARKET_CONTEXT_GATE_V0_2.md, jobs/daily_run.py, pipeline/main_v1.py, config/market_calendar.json, utils/market_calendar.py, data/universe_tw.csv |

---

### Current System State

| Component | File | Status | Notes |
|-----------|------|--------|-------|
| Memory layer | memory/00–03 | ✅ Current | Updated 2026-05-02 |
| Project brain | memory/00_PROJECT_BRAIN.md | ✅ Current | 3 governance rules active |
| System status | memory/01_SYSTEM_STATUS.md | ✅ Current | MVP ~95% |
| Session log | memory/02_SESSION_LOG.md | ✅ Current | 3 sessions recorded |
| Next actions | memory/03_NEXT_ACTION.md | ✅ Current | 6 tasks, 2 gated |
| Mainline legacy | pipeline/main.py | ✅ Preserved | Legacy, do not modify |
| Mainline active | pipeline/main_v1.py | ✅ Active | Advisory snapshot producer |
| Daily runner | jobs/daily_run.py | ✅ Active | Calendar gate v0.1 integrated |
| Market calendar config | config/market_calendar.json | ✅ Active | TW + US 2026 |
| Market calendar utils | utils/market_calendar.py | ✅ Active | 4 status classes |
| Universe TW | data/universe_tw.csv | ✅ Active | 34 tickers, all loading |
| Decision engine | decision/decision_engine.py | ⚠️ Orphaned | Not connected, out of scope |
| Market gate spec | docs/MARKET_CONTEXT_GATE_V0_2.md | ✅ Draft | Spec only, not implemented |
| Daily report | reports/daily/2026-05-02_daily_report.md | ✅ Written | MARKET_CLOSED (Saturday) |
| Mainline snapshot | data/processed/mainline_snapshot.json | ✅ Written | From last weekday run |
| Signal snapshot | data/processed/signal_snapshot.json | ✅ Written | MARKET_CLOSED |

---

### Governance State

| Rule | Location | Status |
|------|----------|--------|
| Core Rule (no broker login, no auto-trade) | 00_PROJECT_BRAIN.md | ✅ Enforced |
| Sensitive Investment Data Protection Rule | 00_PROJECT_BRAIN.md | ✅ Active — highest priority |
| Local Claude Code Git Workflow Rule | 00_PROJECT_BRAIN.md | ✅ Active |
| Claude Code Token Discipline Rule | 00_PROJECT_BRAIN.md | ✅ Active |
| Memory Principle (read memory first) | 00_PROJECT_BRAIN.md | ✅ Active |
| Collaboration Rule (short precise commands) | 00_PROJECT_BRAIN.md | ✅ Active |

All governance rules are documented in `memory/00_PROJECT_BRAIN.md` and enforced
through the AI collaboration protocol. No broker automation violations observed.

---

### Resolved Incidents

#### INC-001 — Auto-removal of user-observed tickers on provider warning
- **Date:** 2026-05-01 / 2026-05-02
- **What happened:** Claude Code auto-removed 8046.TWO and 3189.TWO from
  `data/universe_tw.csv` after yfinance returned "no price data" warning.
  This violated the Sensitive Investment Data Protection Rule (which did not
  yet exist at the time of removal, but was retroactively established).
- **Root cause:** Provider failure misclassified as evidence of delisting.
- **Resolution:** Tickers restored. Suffix corrected: .TWO → .TW. Both confirmed
  loading cleanly: 8046.TW (南電, PCB, CORE) and 3189.TW (景碩, PCB, LAG).
  Protection Rule codified in 00_PROJECT_BRAIN.md.
- **Status:** ✅ Resolved

#### INC-002 — Mainline fragmentation (pipeline/main.py had duplicate dead code)
- **Date:** 2026-05-01
- **What happened:** pipeline/main.py contained two stacked versions (Block A
  dead, Block B active). Block A's `run_pipeline()` was silently overwritten
  by Block B. Two debug print statements fired on every import.
- **Resolution:** Created pipeline/main_v1.py as clean extraction of Block B
  with all surgical cleanups applied. pipeline/main.py preserved as legacy reference.
- **Status:** ✅ Resolved

---

### Risk Register

#### R-001 — v0.1 closed-day skip: pipeline not run on valid data days
- **Category:** Data / Pipeline
- **Severity:** Medium
- **Description:** When TW market is CLOSED_WEEKEND or CLOSED_HOLIDAY,
  `jobs/daily_run.py` currently skips `pipeline_main_v1` entirely and writes
  a MARKET_CLOSED report. However, the last full trading day's data is still
  valid and available. The pipeline could run using that data.
- **Impact:** On weekends and holidays, no fresh advisory snapshot is produced
  even though the underlying market data has not changed. Reports say "no
  pipeline run" rather than "analysis as of last trading day."
- **Mitigation:** Spec documented in `docs/MARKET_CONTEXT_GATE_V0_2.md`.
- **Resolution path:** Implement v0.2 `latest_full_trading_day` + `data_as_of_date`
  logic. Do not implement until explicitly approved after MVP merge.
- **Status:** ⚠️ Open — tracked, gated on v0.2 approval

#### R-002 — Missing `data_as_of_date` field in snapshots
- **Category:** Data Integrity / Observability
- **Severity:** Medium
- **Description:** Neither `data/processed/mainline_snapshot.json` nor
  `data/processed/signal_snapshot.json` currently records which trading day's
  data was used. A reader of the snapshot cannot determine data vintage without
  checking the `generated_at` timestamp and inferring from the calendar.
- **Impact:** Reports may silently show stale data without attribution. AI
  sessions reading old snapshots cannot tell if data is from today or a prior day.
- **Mitigation:** `generated_at` timestamp provides partial context.
- **Resolution path:** Add `data_as_of_date`, `data_mode`, `report_label` to
  `get_market_context()` and propagate into both snapshots (v0.2 spec, step 2–5).
- **Status:** ⚠️ Open — gated on v0.2 approval

#### R-003 — Mainline snapshot missing per-market data vintage in report
- **Category:** Observability / Report Quality
- **Severity:** Low–Medium
- **Description:** The `## Mainline Snapshot` section in daily reports shows
  market_state, market_score, VIX, ranked, and decisions — but does not label
  which date the data represents. On a Monday report, it is unclear whether the
  data is from Friday close or Monday intraday.
- **Impact:** Human reader cannot confirm data freshness from the report alone.
- **Mitigation:** `generated_at` in report header provides partial context.
- **Resolution path:** Add `report_label` field from v0.2 market context into
  the Mainline Snapshot section header.
- **Status:** ⚠️ Open — gated on v0.2 approval

#### R-004 — Daily report formatting polish incomplete
- **Category:** UX / Observability
- **Severity:** Low
- **Description:** Daily report Mainline Snapshot tables render correctly but
  the overall report structure has not been reviewed for human readability.
  Some sections may benefit from clearer section headers or summary lines.
- **Impact:** Human readers may find reports harder to scan quickly.
- **Resolution path:** Review reports/daily output, improve section formatting.
  No code changes needed — only report template updates in `jobs/daily_run.py`.
- **Status:** ⚠️ Open — low priority, next polish task

#### R-005 — Subprocess timeout 90 seconds may be insufficient for pipeline
- **Category:** Runtime Reliability
- **Severity:** Low–Medium
- **Description:** `run_module_or_script()` in `jobs/daily_run.py` uses a
  hardcoded `timeout=90` for all subprocesses. `pipeline_main_v1` downloads
  1y of price data for 34 TW tickers plus 5 US tickers via yfinance. Under
  slow network or rate-limit conditions, this may exceed 90 seconds.
- **Observed:** Pipeline completed well within 90s in all tested runs.
  No timeout failures recorded.
- **Impact:** If timeout triggers, `pipeline_main_v1` status = FAIL, daily
  report shows PARTIAL, and mainline_snapshot.json is not refreshed.
- **Resolution path:** Add per-label `timeout_seconds` parameter to
  `run_module_or_script()` and pass `timeout_seconds=240` for pipeline_main_v1.
  (Was spec'd in a prior task but not yet implemented as a configurable param.)
- **Status:** ⚠️ Open — low priority while pipeline completes within 90s

#### R-006 — Stale historical daily reports from before fixes
- **Category:** Data Integrity / Observability
- **Severity:** Low
- **Description:** `reports/daily/2026-05-01_daily_report.md` was committed
  before the 8046/3189 ticker suffix fix. It still contains yfinance delisted
  warnings for those tickers in its STDERR section. This is a historical
  artifact, not a current runtime issue.
- **Impact:** Auditing past reports will show warnings that are no longer
  reproduced in current runs. May cause confusion in future AI sessions that
  read historical reports.
- **Resolution path:** Accept as historical record. Add note in report or
  rename to `..._pre_ticker_fix.md` if confusion arises. Low priority.
- **Status:** ⚠️ Open — low priority, accepted historical artifact

#### R-007 — `decision/decision_engine.py` is orphaned and not integrated
- **Category:** Technical Debt / Architecture
- **Severity:** Low
- **Description:** `decision/decision_engine.py` is a standalone entry-decision
  engine that reads `data/candidates.json` and writes `data/decision.json`. It
  is not called by `jobs/daily_run.py`, `pipeline/main_v1.py`, or any test.
  It uses a separate module chain (`decision.entry_engine`, `decision.entry_lock`,
  etc.) unrelated to the active pipeline.
- **Impact:** Dead code that may confuse AI sessions about which decision
  engine is in use.
- **Resolution path:** Evaluate separately post-MVP. Options: integrate, document
  as experimental, or deprecate. Do not touch until explicitly scoped.
- **Status:** ⚠️ Open — out of scope for current work

#### R-008 — Sensitive investment data auto-mutation (resolved)
- **Category:** Data Integrity / Governance
- **Severity:** High (at time of incident) → Resolved
- **Description:** See INC-001. Auto-removal of user-observed tickers triggered
  by provider warning, without explicit user approval.
- **Resolution:** Sensitive Investment Data Protection Rule established in
  `00_PROJECT_BRAIN.md`. Tickers restored with correct suffixes.
- **Residual risk:** Future AI sessions must read and apply the protection rule.
  Rule is in highest-priority memory file (00_PROJECT_BRAIN.md). Audited as
  enforced.
- **Status:** ✅ Resolved — rule in place, residual risk: LOW

#### R-009 — 8046/3189 ticker suffix mismatch (resolved)
- **Category:** Data Quality
- **Severity:** Medium (at time of incident) → Resolved
- **Description:** 8046.TWO and 3189.TWO used the `.TWO` OTC suffix which
  yfinance does not recognise. Correct suffix for yfinance is `.TW`.
- **Resolution:** Both rows updated in `data/universe_tw.csv`:
  - `8046.TW,南電,PCB,CORE` (was 8046.TWO,南電,PCB,CORE then briefly .TWO,DYNAMIC)
  - `3189.TW,景碩,PCB,LAG` (was 3189.TWO,景碩,PCB,LAG then briefly .TWO,DYNAMIC)
  Both confirmed loading cleanly in pipeline run. 34/34 tickers load without warnings.
- **Status:** ✅ Resolved

#### R-010 — Market calendar source completeness not independently verified
- **Category:** Data Quality / Calendar
- **Severity:** Low
- **Description:** `config/market_calendar.json` contains TW and US 2026 holiday
  lists as provided by ChatGPT / user instruction. These lists have not been
  independently cross-checked against official exchange calendars (TWSE, NYSE).
  TW has no early_close entries; actual TW market may have shortened sessions
  not yet captured.
- **Known gaps:**
  - TW: no early_close entries defined (TW has some shortened trading days)
  - US: only covers NYSE; NASDAQ follows same calendar but not explicitly verified
  - Calendar covers 2026 only; no 2027+ dates
- **Impact:** Wrong holiday classification could cause pipeline to run on a day
  markets are actually closed, or skip on a day markets are open.
- **Resolution path:** Cross-check against official TWSE and NYSE holiday
  announcements before next year. Add TW early_close dates if applicable.
- **Status:** ⚠️ Open — low priority for 2026, revisit before 2027

#### R-011 — Session phase classification not implemented
- **Category:** Feature Gap / Calendar
- **Severity:** Low
- **Description:** `utils/market_calendar.py` classifies day-level status
  (OPEN, CLOSED_WEEKEND, CLOSED_HOLIDAY, OPEN_EARLY_CLOSE) but has no
  intraday session phase classification (PRE_MARKET, REGULAR_SESSION,
  POST_MARKET, CLOSED_BY_TIME). All runs currently receive status based on
  calendar date only, regardless of wall-clock time.
- **Impact:** A run at 07:00 Taipei (before TW session opens) is classified
  OPEN, same as a run at 11:00 (inside session). No distinction in snapshot or
  report.
- **Resolution path:** Add `session_phase` to `get_market_context()` using
  market `regular_session` open/close times from calendar config. Part of v0.2
  spec. Do not implement until explicitly approved.
- **Status:** ⚠️ Open — tracked in v0.2 spec, gated on approval

---

### Remediation Plan

| Risk | Remediation plan | Related next action | Priority | Status | Do now? | Approval required? |
|------|-----------------|---------------------|----------|--------|---------|--------------------|
| R-001 | Implement v0.2 `latest_full_trading_day` + `data_as_of_date`; change pipeline_policy to RUN_WITH_LATEST_AVAILABLE on closed days | Task 5 — Market Context Gate v0.2 | P3 | DEFERRED | No | Yes — explicit approval before any implementation |
| R-002 | Add `data_as_of_date`, `data_mode`, `report_label` to `get_market_context()` output and propagate into both snapshots | Task 5 — Market Context Gate v0.2 | P3 | DEFERRED | No | Yes — gated on v0.2 approval |
| R-003 | Add data vintage label to Mainline Snapshot section header in daily report | Task 5 — Market Context Gate v0.2 | P3 | DEFERRED | No | Yes — gated on v0.2 approval |
| R-004 | Review reports/daily output; improve section formatting and readability in jobs/daily_run.py report template | Task 3 — Human summary / report polish | P1 | ✅ RESOLVED | N/A | N/A |
| R-005 | Add `timeout_seconds` param to `run_module_or_script()`; pass `timeout_seconds=240` for pipeline_main_v1 | Not yet in next actions | P2 | MONITOR | Only if timeout failures observed | No |
| R-006 | Accept 2026-05-01 report as historical artifact; add note if confusion arises in future AI sessions | Accept as artifact | P2 | ACCEPTED | No | No |
| R-007 | Review decision_engine.py at branch merge readiness: document as experimental or mark for deprecation | Task 4 — Branch merge planning | P1/P2 | OPEN | At merge review | No — review only; deprecation requires user approval |
| R-008 | ✅ Resolved. Sensitive Investment Data Protection Rule codified. Tickers restored. | Resolved — rule in 00_PROJECT_BRAIN.md | P0 | RESOLVED | N/A | N/A |
| R-009 | ✅ Resolved. 8046.TW and 3189.TW confirmed loading cleanly. | Resolved — data/universe_tw.csv fixed | P0 | RESOLVED | N/A | N/A |
| R-010 | Cross-check TW and US holiday lists against official exchange announcements; add TW early_close dates if applicable | Not yet in next actions — revisit before 2027 | P2 | MONITOR | No — 2026 calendar in use | No for verification; Yes for changes to calendar data |
| R-011 | Add `session_phase` to `get_market_context()` using `regular_session` open/close times from calendar config | Task 6 — Market session phase enhancement | P3 | DEFERRED | No | Yes — gated on v0.2 / post-MVP approval |

**Priority definitions:**
- P0 — Resolved; no action needed
- P1 — Ready to action; no approval gate
- P2 — Monitor or low-urgency; do only if triggered
- P3 — Deferred; explicit approval required before any implementation

---

### Next-Action Mapping

| Audit finding | Risk | Next action from 03_NEXT_ACTION.md | Priority |
|---------------|------|------------------------------------|----------|
| Closed-day skip behavior | R-001 | Task 5 (v0.2, gated) | Future |
| Missing data_as_of_date | R-002 | Task 5 (v0.2, gated) | Future |
| Missing data vintage in report | R-003 | Task 5 (v0.2, gated) | Future |
| Report polish | R-004 | Task 3 (human summary polish) | Low |
| Subprocess timeout 90s | R-005 | Not yet in next actions | Low |
| Stale historical reports | R-006 | Accept as artifact | Low |
| Orphaned decision_engine.py | R-007 | Not yet in next actions | Low |
| Sensitive data auto-mutation | R-008 | ✅ Resolved, rule in place | Done |
| Ticker suffix mismatch | R-009 | ✅ Resolved | Done |
| Calendar source completeness | R-010 | Not yet in next actions | Low/Future |
| Missing session phases | R-011 | Task 6 (future, post-MVP) | Future |

**Immediate open tasks (from 03_NEXT_ACTION.md):**
1. Memory and state review — this audit fulfills that task
2. Human summary / report polish — R-004
3. Branch merge planning (optional)

**Gated tasks (do not start without explicit approval):**
- v0.2 market context gate (resolves R-001, R-002, R-003, R-011)

---

---

## Audit Update: 2026-05-02 Session Close

| Field | Value |
|-------|-------|
| Update time | 2026-05-02 (session close) |
| Branch | add-daily-decision-dashboard-v0-20260426_2057 |
| Latest commit at update | bdc508c |
| Scope | Memory-only updates; no runtime code changes; no sensitive data changes |

**Changes recorded this update:**

1. `memory/00_PROJECT_BRAIN.md` correction:
   - `## Core Rule` renamed and split into `## Core Value` and `## Safety Boundary`.
   - Core Value now explicitly states the system's investment purpose (market profit,
     decision quality, trend identification, high-probability detection, swing discipline,
     emotional-trade reduction, structured decision support).
   - Safety Boundary retains the original no-broker-login / no-auto-trade rules.
   - `memory/04_SYSTEM_AUDIT.md` added to session-start read list under Memory Principle.
   - `## System Audit Memory Rule` added: defines required audit entry structure and
     establishes 03 (what to do) vs 04 (why) separation.

2. Risk register and remediation plan:
   - R-001 to R-011 documented with severity, impact, status, and remediation plan.
   - Priorities: P0 (R-008, R-009 resolved), P1 (R-004 ready, R-007 at merge),
     P2 (R-005 monitor, R-006 accepted, R-010 future), P3 (R-001/002/003/011 deferred).
   - v0.2 market context gate confirmed DEFERRED: no implementation without explicit approval.

3. No runtime code changes. No sensitive investment data changes.
   All 34 universe tickers confirmed loading cleanly as of last run (2026-05-02).

---

## Audit Update: 2026-05-02 Human Summary Polish

| Field | Value |
|-------|-------|
| Update time | 2026-05-02 (session close — human summary polish) |
| Branch | add-daily-decision-dashboard-v0-20260426_2057 |
| Latest commit at update | 10a02e3 |
| Scope | jobs/daily_run.py report polish only; no pipeline logic changes; no sensitive data changes |

**R-004 — RESOLVED**

`jobs/daily_run.py` now generates a `## Human Summary` section in all daily reports:

- **Market-closed path**: states no new trading decision today; shows TW/US market
  status from `market_context`; explains pipeline is skipped under v0.1 behavior;
  advisory-only note.
- **Open-market path**: shows `market_state`, `market_score` (4dp), `vix_value` (2dp);
  lists top 3 ranked candidates with names and scores (2dp); shows decision counts
  by action; advisory-only note.

No v0.2 data_as_of logic implemented (remains DEFERRED per R-001/R-002/R-003/R-011).
No sensitive investment data changed. No runtime pipeline logic changed.

**Next P1 task: Branch merge readiness review (R-001 to R-011)**

*End of audit entry 2026-05-02*
