# Mainline Review — 2026-05-01

Reviewed by: Claude Code (claude-sonnet-4-6)
Branch: add-daily-decision-dashboard-v0-20260426_2057
Scope: pipeline/main.py, jobs/daily_run.py, decision/decision_engine.py

---

## Executive Summary

`pipeline/main.py` contains a severe structural defect: two complete, overlapping versions of
the file were pasted together. The first 201 lines are dead code. The file is not called by
`jobs/daily_run.py` or any test suite. `decision/decision_engine.py` is a parallel, standalone
implementation that is also disconnected from the daily runner.

**Verdict: Preserve pipeline/main.py as legacy. Create pipeline/main_v1.py as the clean replacement.**

---

## 1. pipeline/main.py — Detailed Findings

### 1.1 Duplicate file structure (critical)

The file is structurally two files stacked inside one:

| Block | Lines | Content |
|-------|-------|---------|
| Block A (dead) | 1–201 | First import block + `run_pipeline()` v1 — no `capital`, no VIX, no Minervini, no narrative/chips/news |
| Block B (active) | 203–601 | Second import block + `run_pipeline(capital=100000)` v2 — the "修復版" |

Python executes both. The second `run_pipeline()` definition silently overwrites the first.
Block A is entirely dead code — it is never executed.

### 1.2 Debug side-effects on import

Two print statements fire on every `import pipeline.main`:

- Line 52: `print("FILE LOADED")` — inside Block A
- Line 597: `print(" ENTRY CHECK")` — outside any function in Block B

These are not inside `run_pipeline()`. Every import of this module pollutes stdout.

### 1.3 Orphaned import

Block A (line 43):
```python
from decision.risk_lock import apply_risk_lock
```
This module is imported but `apply_risk_lock` is never called in the active `run_pipeline()`.
The active function uses `apply_risk_filters` from `execution.risk` instead.

### 1.4 Unused import

Block A (line 49):
```python
from execution.portfolio_dashboard import build_daily_dashboard
```
`build_daily_dashboard` is imported but never called in either version of `run_pipeline()`.

### 1.5 write_trade_log called twice

`write_trade_log(decisions, close)` is called at:
- Lines 515–521 — before exit check, only BUY decisions present
- Lines 562–573 — after exit check, decisions include SELL

The first call writes BUY trades that get written again at the second call.
Exit SELL trades are only written at the second call.
The first call is a residual from an earlier version and should be removed.

### 1.6 Parallel narrative/chips/news loaders

`pipeline/main.py` imports:
```python
from pipeline.narrative_loader import load_narrative_map
from pipeline.news_heat_loader import load_news_heat_map
from pipeline.chips_loader import load_chips_map
```

`decision/decision_engine.py` defines its own `load_narrative_map()` inline (reads `data/final_narrative.json`).
These are parallel implementations with different data paths and no shared abstraction.

### 1.7 Missing `apply_market_lock` / `apply_risk_filters` contract documentation

Both functions receive `market_state` (a string from `market_filter()`). The values BULL/BEAR/RANGE
are assumed by callers but never formally defined or validated in this file.

---

## 2. jobs/daily_run.py — Assessment

**Status: Clean and stable.**

- Production-quality orchestrator using `subprocess.run`
- Proper logging, JSON snapshot (`data/processed/signal_snapshot.json`), Markdown daily report
- Safety flags present: `broker_login: False`, `auto_trade: False`, `advisory_only: True`
- **Does NOT invoke pipeline/main.py** — completely independent
- Only invokes `reporting.daily_decision_dashboard` and smoke tests
- Confirmed working per session log 2026-05-01

`jobs/daily_run.py` is the verified daily runtime entry point.
`pipeline/main.py` should connect to it only after `pipeline/main_v1.py` passes standalone validation.

---

## 3. decision/decision_engine.py — Assessment

**Status: Standalone, disconnected, not in active use.**

- Reads from `data/candidates.json` (pre-processed input, not live data pull)
- Uses `decision.entry_engine`, `decision.entry_lock`, `decision.entry_tracker`, `decision.ready_predictor`
- These modules are entirely separate from what `pipeline/main.py` uses (`signal_engine.entry`, `execution.trade`)
- Outputs to `data/decision.json`
- Not called by `jobs/daily_run.py` or `pipeline/main.py`

`decision_engine.py` represents an alternative entry-decision flow. It is not integrated.
It should be evaluated separately — out of scope for the mainline consolidation task.

---

## 4. Three-Way Fragmentation Map

```
jobs/daily_run.py
  └─ reporting.daily_decision_dashboard   (active daily runner)
  └─ tests/smoke_*.py

pipeline/main.py                          (NOT called by anything)
  └─ [duplicate dead code in Block A]
  └─ run_pipeline(capital)               (active but orphaned)

decision/decision_engine.py              (NOT called by anything)
  └─ reads data/candidates.json
  └─ writes data/decision.json
```

No mainline calls another. Integration does not exist.

---

## 5. Verdict: Preserve as Legacy, Create pipeline/main_v1.py

### Why not refactor pipeline/main.py directly

1. The duplication (two stacked versions) makes safe line-by-line editing unreliable.
   Removing exactly the right lines from a 601-line file with duplicate imports and
   two `run_pipeline()` definitions is error-prone.

2. `pipeline/main.py` is not imported or called by any active runtime path.
   Preserving it costs nothing and maintains a complete historical reference.

3. The active code lives in a well-defined block (lines 268–600) that can be extracted
   cleanly without risk of leaving orphaned references.

4. `03_NEXT_ACTION.md` explicitly states: "Decide whether to create pipeline/main_v1.py
   or refactor existing main.py" — the corruption found here settles that question.

### What pipeline/main_v1.py must contain

Extract only Block B (lines 268–600) and apply these surgical cleanups:

| Item | Action |
|------|--------|
| Duplicate imports (Block A lines 3–51) | Remove entirely — Block B imports are the authoritative set |
| `print("FILE LOADED")` line 52 | Remove — debug artifact |
| `print(" ENTRY CHECK")` line 597 | Remove — debug artifact |
| `from decision.risk_lock import apply_risk_lock` | Remove — unused in active function |
| `from execution.portfolio_dashboard import build_daily_dashboard` | Remove — unused |
| First `write_trade_log` call (lines 515–521) | Remove — duplicate; exit SELL trades not yet present at that point |
| Second `write_trade_log` call (lines 562–573) | Keep — this is the correct single write point |

No logic changes. Extraction + cleanup only.

### Integration sequence (after standalone validation)

```
Step 1: Create pipeline/main_v1.py (extraction + cleanup above)
Step 2: Validate pipeline/main_v1.py standalone (python -m pipeline.main_v1)
Step 3: Add to jobs/daily_run.py as a new check block (subprocess, same pattern)
Step 4: Confirm signal_snapshot.json output contains pipeline results
Step 5: Deprecate pipeline/main.py with a header comment pointing to main_v1.py
```

Do not connect to `jobs/daily_run.py` before Step 2 passes cleanly.

---

## 6. Files Not Modified

This review is read-only. No runtime files were changed.

- `pipeline/main.py` — unchanged
- `jobs/daily_run.py` — unchanged
- `decision/decision_engine.py` — unchanged

---

*End of review*
