#!/usr/bin/env python3
"""
Investment OS — P0.3 Rolling Basket Entry Failure Diagnosis v0.1

Usage:
    python analysis/rolling_five_day_top1_atr_diagnosis.py \
        --valuation-date 2026-05-26 --entry-capital 100000

Reads:  reports/daily/YYYY-MM-DD_daily_report.md
        yfinance (OHLC price data)
Writes: data/backtest/rolling_five_day_top1_atr_diagnosis_lots.csv
        data/backtest/rolling_five_day_top1_atr_diagnosis_baskets.csv
        data/backtest/rolling_five_day_top1_atr_diagnosis_summary.json
        reports/backtest/rolling_five_day_top1_atr_diagnosis_v0_1.md
        reports/validation/rolling_five_day_top1_atr_diagnosis_validation.md

Advisory and analytical only. No broker connections. No trades placed.
"""
from __future__ import annotations

import argparse
import csv as _csv
import json
import re
import sys
import warnings
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

# Import pure functions from P0.2 — do NOT import broker/execution/controller/decision
from analysis.five_day_top1_atr_backtest import (  # noqa: E402
    fetch_ohlc,
    get_close_series,
    parse_daily_report,
    build_entry,
    simulate_atr_exit,
    simulate_fixed10d_exit,
    simulate_ma_exit,
    compute_position_grade,
    compute_pnl,
    assemble_lot,
    aggregate_basket,
    ATR_VARIANTS,
)

REPORTS_DAILY      = ROOT / "reports" / "daily"
REPORTS_BACKTEST   = ROOT / "reports" / "backtest"
REPORTS_VALIDATION = ROOT / "reports" / "validation"
DATA_BACKTEST      = ROOT / "data" / "backtest"

DIAGNOSIS_STRATEGY_ID = "ROLLING_FIVE_DAY_TOP1_ATR_DIAGNOSIS_v0_1"
BASKET_WINDOW    = 5    # lots per rolling basket
IMMATURE_MIN_HOLD = 5  # minimum post-entry report dates to be non-immature

# post_trade_label thresholds (owner-confirmed)
ATR_TOO_TIGHT_THRESHOLD = 0.05   # post-exit max return > 5% → exited too early
ENTRY_FAILURE_THRESHOLD = -0.03  # next_1d_return < -3% → entered a bad signal

# ─────────────────────────────────────────────────────────────
# Report date discovery + rolling basket builder
# ─────────────────────────────────────────────────────────────

_DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_daily_report\.md$")


def get_available_report_dates() -> list[date]:
    """Scan REPORTS_DAILY for YYYY-MM-DD_daily_report.md files, return sorted dates."""
    result = []
    for f in REPORTS_DAILY.iterdir():
        m = _DATE_RE.match(f.name)
        if m:
            result.append(date.fromisoformat(m.group(1)))
    return sorted(result)


def build_rolling_baskets(
    report_dates: list[date], window: int = BASKET_WINDOW
) -> list[list[date]]:
    """Sliding window of `window` consecutive report dates."""
    if len(report_dates) < window:
        return []
    return [report_dates[i : i + window] for i in range(len(report_dates) - window + 1)]


# ─────────────────────────────────────────────────────────────
# Basket maturity + short-term return helpers
# ─────────────────────────────────────────────────────────────

def flag_immature_basket(
    basket_dates: list[date],
    report_dates: list[date],
    valuation_date: date,
    min_hold_days: int = IMMATURE_MIN_HOLD,
) -> bool:
    """True if the last entry has fewer than min_hold_days post-entry report dates."""
    last_entry = max(basket_dates)
    post_entry = [d for d in report_dates if last_entry < d <= valuation_date]
    return len(post_entry) < min_hold_days


def compute_next_nd_return(
    entry: dict,
    ohlc: pd.DataFrame,
    n: int,
) -> Optional[float]:
    """Return of entry_price → close on Nth trading day after entry. None if insufficient data."""
    entry_date  = date.fromisoformat(entry["entry_date"])
    entry_price = entry.get("entry_price")
    ticker      = entry.get("ticker")
    if entry_price is None or ticker is None:
        return None
    series = get_close_series(ohlc, ticker, after_date=entry_date, to_date=date(2099, 1, 1))
    if len(series) < n:
        return None
    nth_close = series[n - 1][1]
    return round((nth_close - entry_price) / entry_price, 6)


# ─────────────────────────────────────────────────────────────
# Post-exit max return (for ATR_TOO_TIGHT detection)
# ─────────────────────────────────────────────────────────────

def compute_post_exit_max_return(
    ticker: str,
    exit_date: Optional[date],
    valuation_date: date,
    exit_price: float,
    ohlc: pd.DataFrame,
) -> dict:
    """Max close between exit_date (exclusive) and valuation_date.

    Returns post_exit_max_return, post_exit_high_after_exit, days_to_post_exit_high.
    All None when exit_date is None or no post-exit data is available.
    """
    _empty = {
        "post_exit_max_return":     None,
        "post_exit_high_after_exit": None,
        "days_to_post_exit_high":   None,
    }
    if exit_date is None or not exit_price:
        return _empty

    series = get_close_series(ohlc, ticker, after_date=exit_date, to_date=valuation_date)
    if not series:
        return _empty

    max_close = max(c for _, c in series)
    max_idx   = next(i for i, (_, c) in enumerate(series) if c == max_close)
    return {
        "post_exit_max_return":     round((max_close - exit_price) / exit_price, 6),
        "post_exit_high_after_exit": round(max_close, 4),
        "days_to_post_exit_high":   max_idx + 1,
    }


# ─────────────────────────────────────────────────────────────
# Post-trade label — outcome cause diagnosis
# ─────────────────────────────────────────────────────────────

def label_post_trade(
    exit_reason: str,
    gross_pnl: Optional[float],
    post_exit_max_return: Optional[float],
    next_1d_return: Optional[float],
) -> str:
    """Classify why a trade outcome occurred.

    Priority order is owner-confirmed — do not reorder without explicit approval.
    """
    if exit_reason == "OPEN_POSITION":
        return "OPEN_WINNER" if (gross_pnl or 0) > 0 else "OPEN_RISK"
    if exit_reason == "DATA_INCOMPLETE":
        return "DATA_QUALITY_ISSUE"
    if exit_reason == "ATR_TRAILING_STOP":
        if (post_exit_max_return or 0) > ATR_TOO_TIGHT_THRESHOLD:
            return "ATR_TOO_TIGHT"
        if (next_1d_return or 0) < ENTRY_FAILURE_THRESHOLD:
            return "ENTRY_SIGNAL_FAILURE"
    return "MARKET_REVERSAL"


# ─────────────────────────────────────────────────────────────
# Diagnosis lot assembly + basket aggregation
# ─────────────────────────────────────────────────────────────

def assemble_diagnosis_lot(
    base_lot: dict,
    post_exit_info: dict,
    post_trade_label: str,
    next_1d_return: Optional[float],
    next_3d_return: Optional[float],
    basket_id: str,
    is_immature: bool,
) -> dict:
    """Extend a P0.2 assemble_lot() record with P0.3 diagnosis fields."""
    lot = dict(base_lot)
    lot["strategy_id"]               = DIAGNOSIS_STRATEGY_ID
    lot["basket_id"]                 = basket_id
    lot["is_immature"]               = is_immature
    lot["next_1d_return"]            = next_1d_return
    lot["next_3d_return"]            = next_3d_return
    lot["post_exit_max_return"]      = post_exit_info.get("post_exit_max_return")
    lot["post_exit_high_after_exit"] = post_exit_info.get("post_exit_high_after_exit")
    lot["days_to_post_exit_high"]    = post_exit_info.get("days_to_post_exit_high")
    lot["post_trade_label"]          = post_trade_label
    return lot


def aggregate_diagnosis_basket(
    lots: list[dict],
    basket_dates: list[date],
    planned_capital: float,
    basket_id: str,
    is_immature: bool,
) -> dict:
    """Aggregate one rolling basket's lots into basket-level diagnosis metrics."""
    from collections import Counter

    basket = aggregate_basket(lots, planned_capital)   # P0.2 base aggregation
    basket["strategy_id"] = DIAGNOSIS_STRATEGY_ID
    basket["basket_id"]   = basket_id
    basket["start_date"]  = basket_dates[0].isoformat() if basket_dates else None
    basket["is_immature"] = is_immature

    labels = [l.get("post_trade_label") for l in lots]
    basket["false_exit_count"]         = labels.count("ATR_TOO_TIGHT")
    basket["entry_failure_count"]      = labels.count("ENTRY_SIGNAL_FAILURE")
    basket["open_winner_count"]        = labels.count("OPEN_WINNER")
    basket["open_risk_count"]          = labels.count("OPEN_RISK")
    basket["market_reversal_count"]    = labels.count("MARKET_REVERSAL")
    basket["data_quality_issue_count"] = labels.count("DATA_QUALITY_ISSUE")

    tickers       = [l.get("ticker") for l in lots if l.get("ticker")]
    ticker_counts = Counter(tickers)
    basket["duplicate_ticker_count"] = sum(c for c in ticker_counts.values() if c > 1)
    basket["unique_ticker_count"]    = len(ticker_counts)

    return basket


# ─────────────────────────────────────────────────────────────
# Cross-basket summary
# ─────────────────────────────────────────────────────────────

def aggregate_diagnosis_summary(baskets: list[dict]) -> dict:
    """Aggregate across all rolling baskets for the cross-basket summary."""
    n = len(baskets)
    if n == 0:
        return {"n_baskets": 0}

    n_immature        = sum(1 for b in baskets if b.get("is_immature"))
    total_lots        = sum(b.get("entry_count", 0) for b in baskets)
    total_false_exit  = sum(b.get("false_exit_count", 0) for b in baskets)
    total_entry_fail  = sum(b.get("entry_failure_count", 0) for b in baskets)
    total_open_winner = sum(b.get("open_winner_count", 0) for b in baskets)
    total_open_risk   = sum(b.get("open_risk_count", 0) for b in baskets)
    total_mkt_rev     = sum(b.get("market_reversal_count", 0) for b in baskets)
    total_dq          = sum(b.get("data_quality_issue_count", 0) for b in baskets)
    total_gross_pnl   = sum((b.get("gross_pnl") or 0) for b in baskets)
    avg_gross_return  = sum((b.get("gross_return_pct") or 0) for b in baskets) / n

    return {
        "strategy_id":                    DIAGNOSIS_STRATEGY_ID,
        "n_baskets":                      n,
        "n_immature":                     n_immature,
        "n_mature":                       n - n_immature,
        "total_lots":                     total_lots,
        "total_false_exit_count":         total_false_exit,
        "total_entry_failure_count":      total_entry_fail,
        "total_open_winner_count":        total_open_winner,
        "total_open_risk_count":          total_open_risk,
        "total_market_reversal_count":    total_mkt_rev,
        "total_data_quality_issue_count": total_dq,
        "total_gross_pnl":                round(total_gross_pnl, 2),
        "avg_gross_return_pct_per_basket": round(avg_gross_return, 4),
    }


# ─────────────────────────────────────────────────────────────
# Output writers
# ─────────────────────────────────────────────────────────────

def write_lots_csv(lots: list[dict], path: Path) -> None:
    if not lots:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = _csv.DictWriter(f, fieldnames=list(lots[0].keys()))
        writer.writeheader()
        writer.writerows(lots)


def write_baskets_csv(baskets: list[dict], path: Path) -> None:
    if not baskets:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    flat = [{k: v for k, v in b.items() if k != "model_baskets"} for b in baskets]
    if not flat:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = _csv.DictWriter(f, fieldnames=list(flat[0].keys()))
        writer.writeheader()
        writer.writerows(flat)


def write_summary_json(result: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    out = {
        "summary":          result.get("summary", {}),
        "model_comparison": result.get("model_comparison", {}),
        "valuation_date":   result.get("valuation_date"),
        "n_baskets":        result.get("n_baskets"),
    }
    path.write_text(
        json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )


def write_diagnosis_report_md(result: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    w = lines.append

    w(f"# Diagnosis Report — {DIAGNOSIS_STRATEGY_ID}")
    w("")
    w(f"Generated: {date.today().isoformat()}")
    w(f"Valuation date: {result.get('valuation_date', '—')}")
    w(f"Rolling baskets: {result.get('n_baskets', 0)}")
    w(""); w("---"); w("")

    summary = result.get("summary", {})
    w("## Cross-Basket Summary"); w("")
    for k, v in summary.items():
        w(f"- {k}: {v}")
    w(""); w("---"); w("")

    baskets = result.get("baskets_primary", [])
    w("## Per-Basket Results (ATR_BASE — primary)"); w("")
    w("| Basket ID | Immature | GrossPnL | Return% | FalseExit | EntryFail | OpenWinner | OpenRisk |")
    w("|-----------|----------|----------|---------|-----------|-----------|------------|----------|")
    for b in baskets:
        imm = "YES" if b.get("is_immature") else "NO"
        gp  = b.get("gross_pnl") or 0
        pnl = f"+{gp:,.0f}" if gp >= 0 else f"{gp:,.0f}"
        w(f"| {b.get('basket_id')} | {imm} | {pnl} | {b.get('gross_return_pct') or 0:.2f}% "
          f"| {b.get('false_exit_count', 0)} | {b.get('entry_failure_count', 0)} "
          f"| {b.get('open_winner_count', 0)} | {b.get('open_risk_count', 0)} |")
    w(""); w("---"); w("")

    lots = result.get("primary_lots_all", [])
    w("## Lot-Level Diagnosis (ATR_BASE)"); w("")
    w("| Basket | Date | Ticker | Entry | GrossPnL | Label | PostExitRet | Next1D |")
    w("|--------|------|--------|-------|----------|-------|-------------|--------|")
    for l in lots:
        gp      = l.get("gross_pnl") or 0
        pnl_str = f"+{gp:,.0f}" if gp >= 0 else f"{gp:,.0f}"
        per     = l.get("post_exit_max_return")
        per_str = f"{per:.1%}" if per is not None else "—"
        n1r     = l.get("next_1d_return")
        n1r_str = f"{n1r:.1%}" if n1r is not None else "—"
        w(f"| {l.get('basket_id')} | {l.get('entry_date')} | {l.get('ticker')} "
          f"| {l.get('entry_price')} | {pnl_str} | {l.get('post_trade_label')} "
          f"| {per_str} | {n1r_str} |")
    w(""); w("---"); w("")

    mc = result.get("model_comparison", {})
    if mc:
        w("## Model Comparison (Summed Across All Baskets)"); w("")
        w("| Model | TotalGrossPnL | AvgReturn%/Basket |")
        w("|-------|---------------|------------------|")
        for mn, mv in mc.items():
            w(f"| {mn} | {(mv.get('avg_gross_pnl') or mv.get('total_gross_pnl') or 0):,.0f} "
              f"| {mv.get('avg_gross_return_pct') or 0:.2f}% |")
        w(""); w("---"); w("")

    w("*Advisory only. No trades placed. All outputs for human review.*"); w("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_validation_report_md(result: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    w = lines.append

    w(f"# Validation Report — {DIAGNOSIS_STRATEGY_ID}"); w("")
    w(f"Generated: {date.today().isoformat()}"); w("")

    w("## Assumptions"); w("")
    w("1. Entry price = signal-day adjusted close (yfinance auto_adjust=True, v0.1)")
    w("2. Rolling baskets built from available daily report dates (not all calendar TW trading days)")
    w("3. ATR trailing stop: close-based exit, initial-stop floor on day 1 of hold")
    w("4. post_trade_label priority: OPEN_POSITION → OPEN_WINNER/OPEN_RISK; DATA_INCOMPLETE → DATA_QUALITY_ISSUE; ATR_TRAILING_STOP+post_exit>5% → ATR_TOO_TIGHT; next_1d<-3% → ENTRY_SIGNAL_FAILURE; else → MARKET_REVERSAL")
    w("5. Baskets with fewer than 5 post-entry report dates are flagged is_immature=True")
    w("6. Valuation date fixed at 2026-05-26 for all baskets")
    w("7. Transaction costs: buy 0.1425%, sell 0.1425% + STT 0.3% on sell value"); w("")

    w("## Known Limitations"); w("")
    w("- Only 15 daily report dates available (2026-05-01 to 2026-05-26) → 11 rolling baskets, all within one market regime")
    w("- Chips, chase_risk, narrative fields are not in historical reports; position grade is diagnostic only")
    w("- post_exit_max_return uses yfinance adjusted close; may differ from TWSE raw close")
    w("- IMMATURE_BASKET lots have had limited ATR stop evolution — interpret with caution")
    w("- 5% and 3% thresholds for ATR_TOO_TIGHT / ENTRY_SIGNAL_FAILURE are first-pass heuristics, not statistically derived"); w("")

    w("---"); w("")
    w("*This is a simulation. No trades were placed. No broker connections were made.*")
    w("*Owner should review before any capital allocation decisions.*"); w("")
    path.write_text("\n".join(lines), encoding="utf-8")
