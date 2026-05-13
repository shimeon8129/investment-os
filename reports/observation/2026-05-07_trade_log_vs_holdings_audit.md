# Trade Log vs Current Holdings Audit — 2026-05-07

## Summary Verdict

**FAIL**

`data/trade_log.json` contains advisory-only BUY rows that are treated as real executed
positions by `execution/portfolio.py`. `data/portfolio/current_holdings.json` (actual broker
holdings) is not used by any position lock or exit check logic. The two sources are structurally
diverged with no reconciliation mechanism.

---

## Current Data Sources

| Source | Purpose | Real Broker Data? | Advisory Data? | Used By |
|---|---|:---:|:---:|---|
| `data/trade_log.json` | Simulated/advisory trade history | No | Yes | `execution/portfolio.py`, `feedback/performance.py`, `pipeline/main_v1.py` (via portfolio) |
| `data/portfolio/current_holdings.json` | Actual broker holdings snapshot | Yes | No | `portfolio/holdings_loader.py`, `reporting/daily_decision_dashboard.py`, `reporting/portfolio_candidate_review.py`, `jobs/daily_run.py` (reporting only) |

---

## Findings

### Finding 1: `execution/portfolio.py` treats advisory BUY rows as real positions

`execution/portfolio.py:load_portfolio()` reads `data/trade_log.json` and builds a live
portfolio by replaying every BUY/SELL entry. It does not distinguish between advisory signals
and confirmed executions.

Current `trade_log.json` contents (5 rows — all advisory):

| date | ticker | action | price | size |
|---|---|---|---|---|
| 2026-04-29 | 3583.TW | BUY | 736.00 | 0.1 |
| 2026-04-29 | 6187.TWO | BUY | 1080.00 | 0.1 |
| 2026-04-29 | 3680.TWO | BUY | 449.00 | 0.1 |
| 2026-04-29 | 3711.TW | BUY | 495.50 | 0.1 |
| 2026-05-01 | 2449.TW | BUY | 302.50 | 0.1 |

`load_portfolio()` returns all 5 tickers as active positions.

### Finding 2: position lock and exit check both depend solely on `trade_log.json`

`pipeline/main_v1.py` calls `load_portfolio()` and passes the result to:

- `decision/position_lock.py:apply_position_lock()` — any ticker in portfolio receives
  `action=HOLD, reason=ALREADY_IN_POSITION`
- `pipeline/main_v1.py` exit loop — iterates `portfolio.items()` and calls `check_exit()`
  on each position

`data/portfolio/current_holdings.json` is not consulted at either step.

### Finding 3: `current_holdings.json` is used only in reporting modules

`current_holdings.json` is read by:

- `portfolio/holdings_loader.py` — loader utility
- `reporting/daily_decision_dashboard.py` — human-readable dashboard
- `reporting/portfolio_candidate_review.py` — portfolio vs candidate cross-reference
- `jobs/daily_run.py` — holdings file existence check for smoke tests

None of these paths feed back into the position lock or exit check logic. The broker-confirmed
holdings file has zero influence on runtime pipeline decisions.

### Finding 4: Four advisory-only tickers can still trigger false ALREADY_IN_POSITION

Divergence map between the two sources:

| Ticker | In trade_log? | In current_holdings? | Status |
|---|:---:|:---:|---|
| 3583.TW | ✅ BUY | ❌ | **Advisory-only — false active position** |
| 6187.TWO | ✅ BUY | ❌ | **Advisory-only — false active position** |
| 3680.TWO | ✅ BUY | ❌ | **Advisory-only — false active position** |
| 2449.TW | ✅ BUY | ❌ | **Advisory-only — false active position** |
| 3711.TW | ✅ BUY (495.5) | ✅ BUY (412.0) | In both — entry price mismatch |
| 009816 | ❌ | ✅ | Real holding, invisible to pipeline |
| 00992A | ❌ | ✅ | Real holding, invisible to pipeline |
| 2330 | ❌ | ✅ | Real holding, invisible to pipeline |
| 2345 | ❌ | ✅ | Real holding, invisible to pipeline |
| 2408 | ❌ | ✅ | Real holding, invisible to pipeline |
| 6830 | ❌ | ✅ | Real holding, invisible to pipeline |

4 advisory-only tickers will receive HOLD/ALREADY_IN_POSITION if they re-appear as candidates.
6 real broker holdings generate no exit check signal and receive no position lock.

### Finding 5: `.TWO` suffix tickers risk data lookup failures

`6187.TWO` and `3680.TWO` use the OTC suffix `.TWO`. The universe ticker fix (commit 2026-05-02)
corrected `.TWO` → `.TW` for 8046 and 3189. These two trade_log entries retain the `.TWO`
suffix. If yfinance does not resolve them, exit check will silently skip them (no price data).

### Finding 6: `feedback/performance.py` is currently inert but structurally depends on `trade_log.json`

`analyze_performance()` filters for SELL records only. Since `trade_log.json` contains zero SELL
rows, it returns empty/zero results. When SELL rows are eventually added, P&L will be computed
from advisory entry prices, not actual broker execution prices.

---

## Risk

**Immediate risk:** 4 advisory-only BUY tickers (3583.TW, 6187.TWO, 3680.TWO, 2449.TW) are
registered as active positions in the pipeline. If any of these tickers re-enter the candidate
list, `apply_position_lock()` will output `HOLD / ALREADY_IN_POSITION` — suppressing a valid
new entry signal. This is the same class of bug as the 2464.TW false lock (commit `3292ab1`).

**Structural risk:** 6 real broker holdings (009816, 00992A, 2330, 2345, 2408, 6830) are
completely invisible to `check_exit()`. If a real position crosses a stop-loss or trailing-stop
threshold, the pipeline will not generate an exit signal for it. The exit logic is operating on
ghost positions instead of real ones.

**Data integrity risk:** 3711.TW appears in both sources with a 83.5 TWD / 17% entry price
discrepancy (trade_log: 495.5, current_holdings: 412.0). Any P&L or stop-loss calculation using
the trade_log entry price will be incorrect.

---

## Recommendation

**B. Make `current_holdings.json` the sole source for actual position state.**

Rationale:

- `current_holdings.json` is sourced from `manual_user_input` (broker-verified) and is the
  authoritative record of real positions.
- `trade_log.json` was designed as an advisory/simulated trade history. It was never intended to
  define live position state for a real portfolio.
- The 2464.TW false lock bug (commit `3292ab1`) and the 4 currently false positions are both
  symptoms of the same root cause: `load_portfolio()` using advisory log data as position truth.

Implementation path (requires explicit user approval before any code change):

1. Create `portfolio/position_loader.py` — reads `current_holdings.json`, returns a dict keyed
   by ticker (same shape as `load_portfolio()` output) for drop-in compatibility.
2. Update `pipeline/main_v1.py` to call `load_position_state()` instead of `load_portfolio()`.
3. Retain `trade_log.json` and `execution/portfolio.py` as the advisory simulation layer only —
   no deletion, no renaming.
4. Update `feedback/performance.py` to clearly document that P&L is advisory/simulated.
5. Add a divergence check (optional): at daily run startup, compare trade_log open positions vs
   current_holdings and log any mismatch as a `data_warning`.

This change is additive — it does not delete `trade_log.json` or alter the advisory layer.
Approval required before any code modification.

---

## No Code Change Confirmation

No runtime logic was modified in this audit.

Files read: `data/trade_log.json`, `data/portfolio/current_holdings.json`,
`execution/portfolio.py`, `decision/position_lock.py`, `feedback/performance.py`,
`pipeline/main_v1.py`, `jobs/observation_daily.py`, `execution/exit.py`,
`execution/trade_log_writer.py`, `portfolio/holdings_loader.py`.

Files written: this report only (`reports/observation/2026-05-07_trade_log_vs_holdings_audit.md`).

*Audit generated: 2026-05-07*
