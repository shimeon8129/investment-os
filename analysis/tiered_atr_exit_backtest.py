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
