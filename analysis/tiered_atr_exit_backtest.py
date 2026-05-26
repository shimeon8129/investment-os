#!/usr/bin/env python3
"""
Investment OS — P0.4 Tiered ATR Exit Backtest v0.1

Usage:
    python analysis/tiered_atr_exit_backtest.py \
        --valuation-date 2026-05-26 --entry-capital 100000

Reads:  reports/daily/YYYY-MM-DD_daily_report.md
        yfinance (OHLC price data)
Writes: data/backtest/tiered_atr_exit_backtest_lots.csv
        data/backtest/tiered_atr_exit_backtest_comparison.csv
        data/backtest/tiered_atr_exit_backtest_summary.json
        reports/backtest/tiered_atr_exit_backtest_v0_1.md
        reports/validation/tiered_atr_exit_backtest_validation.md

Advisory and analytical only. No broker connections. No trades placed.
"""
from __future__ import annotations

import argparse
import csv as _csv
import json
import sys
import warnings
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

# P0.2 pure functions — do NOT import broker/execution/controller/decision
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
)

# P0.3 helpers
from analysis.rolling_five_day_top1_atr_diagnosis import (  # noqa: E402
    get_available_report_dates,
    build_rolling_baskets,
    flag_immature_basket,
    compute_post_exit_max_return,
)

REPORTS_BACKTEST   = ROOT / "reports" / "backtest"
REPORTS_VALIDATION = ROOT / "reports" / "validation"
DATA_BACKTEST      = ROOT / "data" / "backtest"

TIERED_STRATEGY_ID = "TIERED_ATR_EXIT_BACKTEST_v0_1"
BASKET_WINDOW      = 5

# Tiered ATR multiplier thresholds (based on peak float from entry price)
TIERED_INIT_MULT      = 1.5    # initial_stop = entry - 1.5 × ATR20
TIERED_TRAIL_LOW      = 2.0    # float_pct  < 5%
TIERED_TRAIL_MID      = 2.5    # 5% ≤ float_pct < 15%
TIERED_TRAIL_HIGH     = 3.0    # float_pct ≥ 15%
TIERED_LOW_THRESHOLD  = 0.05
TIERED_HIGH_THRESHOLD = 0.15
HOLD_PROTECTION_DATES = 3      # first N report dates: only initial_stop active

# Threshold for false exit detection (same as P0.3)
ATR_TOO_TIGHT_THRESHOLD = 0.05

ALL_MODELS = [
    "ATR_BASE",
    "ATR_WIDE",
    "TIERED_ATR",
    "TIERED_ATR_NO_HOLD_PROTECTION",
    "FIXED_10D",
    "MA5",
]


# ─────────────────────────────────────────────────────────────
# TIERED ATR trailing stop exit model
# ─────────────────────────────────────────────────────────────

def simulate_tiered_atr_exit(
    entry: dict,
    ohlc: pd.DataFrame,
    report_dates: list[date],
    valuation_date: date,
    hold_protection: bool = True,
) -> dict:
    """ATR trailing stop with tiered multipliers and optional hold protection.

    Multiplier tiers (based on peak float from entry price):
        float_pct  < 5%  → 2.0× ATR
        5% ≤ float_pct < 15% → 2.5× ATR
        float_pct ≥ 15% → 3.0× ATR

    Hold protection: first HOLD_PROTECTION_DATES report dates after entry,
    only initial_stop (1.5×ATR) is active. Trailing stop ignored in this window.
    hold_period_protected=True when trailing would have triggered during protection.
    """
    entry_price = entry.get("entry_price")
    atr20       = entry.get("atr20_at_entry")
    shares      = entry.get("shares", 0) or 0
    ticker      = entry.get("ticker")

    _empty = {
        "exit_model": "TIERED_ATR", "exit_date": None, "exit_price": None,
        "exit_reason": "DATA_INCOMPLETE", "holding_days": None,
        "highest_close_since_entry": None, "trailing_stop_at_exit": None,
        "max_profit_seen": None, "max_drawdown_seen": None,
        "current_price": None, "current_value": None,
        "hold_period_protected": False,
    }
    if entry_price is None or atr20 is None or ticker is None:
        return _empty

    entry_date   = date.fromisoformat(entry["entry_date"])
    initial_stop = entry_price - TIERED_INIT_MULT * atr20
    highest_close = entry_price
    close_series  = get_close_series(ohlc, ticker, entry_date, valuation_date)

    # Determine protection window end date
    if hold_protection:
        post_entry = sorted(d for d in report_dates if d > entry_date)
        protection_end = post_entry[HOLD_PROTECTION_DATES - 1] if len(post_entry) >= HOLD_PROTECTION_DATES \
                         else (post_entry[-1] if post_entry else entry_date)
    else:
        protection_end = entry_date  # empty window → no protection

    max_profit      = 0.0
    max_drawdown    = 0.0
    hold_period_protected = False

    for i, (d, close) in enumerate(close_series):
        if close > highest_close:
            highest_close = close

        float_pct = (highest_close - entry_price) / entry_price
        if float_pct < TIERED_LOW_THRESHOLD:
            trail_mult = TIERED_TRAIL_LOW
        elif float_pct < TIERED_HIGH_THRESHOLD:
            trail_mult = TIERED_TRAIL_MID
        else:
            trail_mult = TIERED_TRAIL_HIGH
        trailing_stop = highest_close - trail_mult * atr20

        in_protection = d <= protection_end
        if in_protection:
            if close < trailing_stop and not hold_period_protected:
                hold_period_protected = True  # trailing would have triggered
            effective_stop = initial_stop
        elif i == 0:
            effective_stop = max(trailing_stop, initial_stop)  # gap-down floor on day 0
        else:
            effective_stop = trailing_stop

        unrealized = (close - entry_price) * shares
        if unrealized > max_profit:
            max_profit = unrealized
        if unrealized < max_drawdown:
            max_drawdown = unrealized

        if close < effective_stop:
            return {
                "exit_model":               "TIERED_ATR",
                "exit_date":                d.isoformat(),
                "exit_price":               round(close, 2),
                "exit_reason":              "ATR_TRAILING_STOP",
                "holding_days":             i + 1,
                "highest_close_since_entry": round(highest_close, 2),
                "trailing_stop_at_exit":    round(effective_stop, 2),
                "max_profit_seen":          round(max_profit, 2),
                "max_drawdown_seen":        round(max_drawdown, 2),
                "current_price":            round(close, 2),
                "current_value":            round(close * shares, 2),
                "hold_period_protected":    hold_period_protected,
            }

    # Still open at valuation date
    current_price = close_series[-1][1] if close_series else entry_price
    unrealized = (current_price - entry_price) * shares
    if unrealized > max_profit:
        max_profit = unrealized
    if unrealized < max_drawdown:
        max_drawdown = unrealized

    float_pct = (highest_close - entry_price) / entry_price
    if float_pct < TIERED_LOW_THRESHOLD:
        trail_mult = TIERED_TRAIL_LOW
    elif float_pct < TIERED_HIGH_THRESHOLD:
        trail_mult = TIERED_TRAIL_MID
    else:
        trail_mult = TIERED_TRAIL_HIGH
    trailing_stop = highest_close - trail_mult * atr20

    return {
        "exit_model":               "TIERED_ATR",
        "exit_date":                None,
        "exit_price":               None,
        "exit_reason":              "OPEN_POSITION",
        "holding_days":             len(close_series),
        "highest_close_since_entry": round(highest_close, 2),
        "trailing_stop_at_exit":    round(trailing_stop, 2),
        "max_profit_seen":          round(max_profit, 2),
        "max_drawdown_seen":        round(max_drawdown, 2),
        "current_price":            round(current_price, 2),
        "current_value":            round(current_price * shares, 2),
        "hold_period_protected":    hold_period_protected,
    }
