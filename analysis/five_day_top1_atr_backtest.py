#!/usr/bin/env python3
"""
Investment OS — Five-Day Top1 ATR Strategy Backtest v0.1

Usage:
    python analysis/five_day_top1_atr_backtest.py \
        --start-date 2026-05-07 --entries 5 \
        --entry-capital 100000 --valuation-date 2026-05-25

Reads:  reports/daily/YYYY-MM-DD_daily_report.md
        yfinance (OHLC price data)
Writes: reports/backtest/five_day_top1_atr_strategy_v0_1.md
        data/backtest/five_day_top1_atr_strategy_v0_1_lots.csv
        data/backtest/five_day_top1_atr_strategy_v0_1_basket.json
        reports/validation/five_day_top1_atr_strategy_v0_1_validation.md

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
from math import floor
from pathlib import Path
from typing import Optional

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import yfinance as yf

REPORTS_DAILY = ROOT / "reports" / "daily"
REPORTS_BACKTEST = ROOT / "reports" / "backtest"
REPORTS_VALIDATION = ROOT / "reports" / "validation"
DATA_BACKTEST = ROOT / "data" / "backtest"

STRATEGY_ID = "FIVE_DAY_TOP1_ATR_STRATEGY_v0_1"
BASKET_ID = "2026-05-07_TOP1_5D"

# Taiwan transaction cost constants
BUY_FEE_RATE = 0.001425   # 0.1425% commission on buy
SELL_FEE_RATE = 0.001425  # 0.1425% commission on sell
STT_RATE = 0.003          # 0.3% securities transaction tax on sell

# ATR variant configs: (initial_mult, trailing_mult)
ATR_VARIANTS = {
    "ATR_TIGHT": (1.0, 1.5),
    "ATR_BASE":  (1.5, 2.0),
    "ATR_WIDE":  (2.0, 2.5),
}
PRIMARY_ATR_VARIANT = "ATR_BASE"


def main() -> int:
    parser = argparse.ArgumentParser(description="Five-Day Top1 ATR Strategy Backtest v0.1")
    parser.add_argument("--start-date", default="2026-05-07")
    parser.add_argument("--entries", type=int, default=5)
    parser.add_argument("--entry-capital", type=float, default=100_000)
    parser.add_argument("--valuation-date", default="2026-05-25")
    args = parser.parse_args()
    print(f"[backtest] {STRATEGY_ID} — scaffold only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
