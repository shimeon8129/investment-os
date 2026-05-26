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
