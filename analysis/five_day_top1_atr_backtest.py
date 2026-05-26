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


# ─────────────────────────────────────────────────────────────
# Daily report parser
# ─────────────────────────────────────────────────────────────

def parse_daily_report(date_str: str) -> Optional[dict]:
    """Parse Top 1 candidate metadata from daily report Markdown."""
    path = REPORTS_DAILY / f"{date_str}_daily_report.md"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")

    ms_m = re.search(r"Market state:\s*\*\*([A-Z]+)\*\*", text)
    market_state = ms_m.group(1) if ms_m else None

    score_m = re.search(r"Market state:.*?Score:\s*([\d.]+)", text)
    market_score = float(score_m.group(1)) if score_m else None

    vix_m = re.search(r"VIX:\s*([\d.]+)", text)
    vix = float(vix_m.group(1)) if vix_m else None

    # Top Ranked table: handles both 6-column (old) and 10-column (new) formats
    top1_m = re.search(
        r"\|\s*1\s*\|\s*(\S+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*(\S+)\s*\|\s*([\d.]+)\s*"
        r"(?:\|\s*(\S+)\s*\|\s*(\S+)\s*\|\s*(\S+)\s*\|\s*([^|]*?)\s*\|)?",
        text,
    )
    if not top1_m:
        return None

    return {
        "date": date_str,
        "market_state": market_state,
        "market_score": market_score,
        "vix": vix,
        "ticker": top1_m.group(1).strip(),
        "name": top1_m.group(2).strip(),
        "sector": top1_m.group(3).strip(),
        "signal": top1_m.group(4).strip(),
        "score": float(top1_m.group(5)),
        "base_role": (top1_m.group(6) or "").strip() or None,
        "active_role": (top1_m.group(7) or "").strip() or None,
        "role_confidence": (top1_m.group(8) or "").strip() or None,
    }


# ─────────────────────────────────────────────────────────────
# OHLC fetch
# ─────────────────────────────────────────────────────────────

def fetch_ohlc(tickers: list[str], start: str, end: str) -> pd.DataFrame:
    """Fetch daily OHLC. Returns MultiIndex(field, ticker) DataFrame, date index."""
    if not tickers:
        return pd.DataFrame()
    try:
        raw = yf.download(
            tickers, start=start, end=end,
            interval="1d", auto_adjust=True,
            progress=False, threads=True,
        )
        if raw.empty:
            return pd.DataFrame()
        if not isinstance(raw.columns, pd.MultiIndex):
            # Single-ticker: wrap into MultiIndex
            raw.columns = pd.MultiIndex.from_tuples(
                [(col, tickers[0]) for col in raw.columns]
            )
        raw.index = pd.to_datetime(raw.index).date
        return raw
    except Exception as e:
        print(f"[WARN] fetch_ohlc failed: {e}")
        return pd.DataFrame()


# ─────────────────────────────────────────────────────────────
# ATR20 + price helpers
# ─────────────────────────────────────────────────────────────

def compute_atr20(
    ohlc: pd.DataFrame, ticker: str, as_of_date: date, period: int = 20
) -> Optional[float]:
    """ATR20 using `period` trading days strictly before as_of_date."""
    if ohlc.empty:
        return None
    try:
        lvl0 = ohlc.columns.get_level_values(0).unique()
        if not {"High", "Low", "Close"}.issubset(set(lvl0)):
            return None
        if ticker not in ohlc["Close"].columns:
            return None
    except Exception:
        return None

    mask = [d < as_of_date for d in ohlc.index]
    h  = ohlc["High"][ticker][mask].dropna()
    lo = ohlc["Low"][ticker][mask].dropna()
    c  = ohlc["Close"][ticker][mask].dropna()

    if len(c) < period + 1:
        return None

    h  = h.iloc[-(period + 1):].values
    lo = lo.iloc[-(period + 1):].values
    c  = c.iloc[-(period + 1):].values

    tr = np.maximum(
        h[1:] - lo[1:],
        np.maximum(np.abs(h[1:] - c[:-1]), np.abs(lo[1:] - c[:-1])),
    )
    return float(tr.mean())


def get_close(ohlc: pd.DataFrame, ticker: str, d: date) -> Optional[float]:
    """Return closing price for ticker on date d, or None."""
    if ohlc.empty:
        return None
    try:
        if ticker not in ohlc["Close"].columns:
            return None
        val = ohlc["Close"][ticker].get(d)
        if val is None or pd.isna(val):
            return None
        return float(val)
    except Exception:
        return None


def get_close_series(
    ohlc: pd.DataFrame, ticker: str, after_date: date, to_date: date
) -> list[tuple[date, float]]:
    """List of (date, close) for dates strictly after after_date through to_date."""
    if ohlc.empty:
        return []
    try:
        if ticker not in ohlc["Close"].columns:
            return []
        s = ohlc["Close"][ticker]
        return [
            (d, float(v))
            for d, v in s.items()
            if after_date < d <= to_date and not pd.isna(v)
        ]
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────
# Entry builder
# ─────────────────────────────────────────────────────────────

def build_entry(
    entry_index: int, date_str: str, ohlc: pd.DataFrame, entry_capital: float
) -> dict:
    """Build one lot entry dict from daily report + OHLC."""
    parsed = parse_daily_report(date_str)
    if not parsed:
        return {
            "entry_index": entry_index, "entry_date": date_str, "ticker": None,
            "data_quality_flag": "FAIL",
            "data_quality_note": f"missing daily report {date_str}",
        }

    ticker = parsed["ticker"]
    entry_date = date.fromisoformat(date_str)

    entry_price = get_close(ohlc, ticker, entry_date)
    if entry_price is None:
        return {
            **parsed,
            "entry_index": entry_index, "entry_date": date_str,
            "planned_entry_capital": entry_capital,
            "entry_price": None, "shares": None,
            "actual_cost": None, "unused_cash": None,
            "atr20_at_entry": None, "initial_stop": None,
            "data_quality_flag": "FAIL",
            "data_quality_note": f"missing close price for {ticker} on {date_str}",
        }

    shares = int(floor(entry_capital / entry_price))
    actual_cost = shares * entry_price
    unused_cash = entry_capital - actual_cost

    atr20 = compute_atr20(ohlc, ticker, entry_date)
    initial_stop = round(entry_price - 1.5 * atr20, 2) if atr20 else None

    return {
        "strategy_id": STRATEGY_ID,
        "basket_id": BASKET_ID,
        "entry_index": entry_index,
        "entry_date": date_str,
        "ticker": ticker,
        "name": parsed["name"],
        "rank": "Top1",
        "market_state": parsed["market_state"],
        "entry_signal": parsed["signal"],
        "role": parsed.get("base_role"),
        "planned_entry_capital": entry_capital,
        "entry_price": round(entry_price, 2),
        "shares": shares,
        "actual_cost": round(actual_cost, 2),
        "unused_cash": round(unused_cash, 2),
        "atr20_at_entry": round(atr20, 4) if atr20 else None,
        "initial_stop": initial_stop,
        "data_quality_flag": "PASS" if atr20 else "WARN",
        "data_quality_note": "" if atr20 else "ATR20 unavailable — insufficient OHLC history",
        # raw fields for downstream grade/report
        "_score": parsed["score"],
        "_market_score": parsed["market_score"],
        "_vix": parsed["vix"],
        "_base_role": parsed.get("base_role"),
        "_active_role": parsed.get("active_role"),
        "_role_confidence": parsed.get("role_confidence"),
    }


# ─────────────────────────────────────────────────────────────
# Exit model A: ATR trailing stop (primary)
# ─────────────────────────────────────────────────────────────

def simulate_atr_exit(
    entry: dict,
    ohlc: pd.DataFrame,
    initial_mult: float,
    trailing_mult: float,
    valuation_date: date,
) -> dict:
    """Simulate ATR trailing stop. Uses close-based exit (v0.1)."""
    entry_price = entry.get("entry_price")
    atr20       = entry.get("atr20_at_entry")
    shares      = entry.get("shares", 0) or 0
    entry_date  = date.fromisoformat(entry["entry_date"])

    _empty = {
        "exit_model": "ATR_TRAILING", "exit_date": None, "exit_price": None,
        "exit_reason": "DATA_INCOMPLETE", "holding_days": None,
        "highest_close_since_entry": None, "trailing_stop_at_exit": None,
        "max_profit_seen": None, "max_drawdown_seen": None,
        "current_price": None, "current_value": None,
    }
    if entry_price is None or atr20 is None:
        return _empty

    initial_stop   = entry_price - initial_mult * atr20
    highest_close  = entry_price
    close_series   = get_close_series(ohlc, entry["ticker"], entry_date, valuation_date)
    max_profit     = 0.0
    max_drawdown   = 0.0

    for i, (d, close) in enumerate(close_series):
        if close > highest_close:
            highest_close = close
        trailing_stop  = highest_close - trailing_mult * atr20
        # On day-0 of hold use initial_stop as floor so a gap-down triggers exit
        effective_stop = max(trailing_stop, initial_stop) if i == 0 else trailing_stop

        unrealized = (close - entry_price) * shares
        if unrealized > max_profit:
            max_profit = unrealized
        if unrealized < max_drawdown:
            max_drawdown = unrealized

        if close < effective_stop:
            return {
                "exit_model": "ATR_TRAILING",
                "exit_date": d.isoformat(),
                "exit_price": round(close, 2),
                "exit_reason": "ATR_TRAILING_STOP",
                "holding_days": i + 1,
                "highest_close_since_entry": round(highest_close, 2),
                "trailing_stop_at_exit": round(trailing_stop, 2),
                "max_profit_seen": round(max_profit, 2),
                "max_drawdown_seen": round(max_drawdown, 2),
                "current_price": round(close, 2),
                "current_value": round(close * shares, 2),
            }

    # Still open at valuation date
    current_price = close_series[-1][1] if close_series else entry_price
    trailing_stop = highest_close - trailing_mult * atr20
    unrealized = (current_price - entry_price) * shares
    if unrealized > max_profit:
        max_profit = unrealized
    if unrealized < max_drawdown:
        max_drawdown = unrealized

    return {
        "exit_model": "ATR_TRAILING",
        "exit_date": None,
        "exit_price": None,
        "exit_reason": "OPEN_POSITION",
        "holding_days": len(close_series),
        "highest_close_since_entry": round(highest_close, 2),
        "trailing_stop_at_exit": round(trailing_stop, 2),
        "max_profit_seen": round(max_profit, 2),
        "max_drawdown_seen": round(max_drawdown, 2),
        "current_price": round(current_price, 2),
        "current_value": round(current_price * shares, 2),
    }


# ─────────────────────────────────────────────────────────────
# Exit model B: Fixed 10 trading days (benchmark)
# ─────────────────────────────────────────────────────────────

def simulate_fixed10d_exit(
    entry: dict,
    ohlc: pd.DataFrame,
    trading_days: list[date],
    valuation_date: date,
) -> dict:
    """Exit at 10th trading day close after entry (benchmark)."""
    entry_date  = date.fromisoformat(entry["entry_date"])
    shares      = entry.get("shares", 0) or 0
    entry_price = entry.get("entry_price")

    days_after = [d for d in trading_days if d > entry_date]
    if len(days_after) < 10:
        return {"exit_model": "FIXED_10D", "exit_date": None, "exit_price": None,
                "exit_reason": "DATA_INCOMPLETE", "holding_days": None,
                "current_price": None, "current_value": None}

    exit_day   = days_after[9]
    exit_price = get_close(ohlc, entry["ticker"], exit_day)
    if exit_price is None:
        return {"exit_model": "FIXED_10D", "exit_date": exit_day.isoformat(),
                "exit_price": None, "exit_reason": "DATA_INCOMPLETE",
                "holding_days": 10, "current_price": None, "current_value": None}

    return {
        "exit_model": "FIXED_10D",
        "exit_date": exit_day.isoformat(),
        "exit_price": round(exit_price, 2),
        "exit_reason": "FIXED_10D",
        "holding_days": 10,
        "current_price": round(exit_price, 2),
        "current_value": round(exit_price * shares, 2),
    }


# ─────────────────────────────────────────────────────────────
# Exit model C: MA5 trailing exit (benchmark)
# ─────────────────────────────────────────────────────────────

def simulate_ma_exit(
    entry: dict,
    ohlc: pd.DataFrame,
    ma_period: int,
    valuation_date: date,
) -> dict:
    """Exit when close < MA(ma_period). Warmup uses full pre-entry OHLC history."""
    entry_date  = date.fromisoformat(entry["entry_date"])
    shares      = entry.get("shares", 0) or 0
    entry_price = entry.get("entry_price")
    ticker      = entry["ticker"]

    if entry_price is None:
        return {"exit_model": "MA_EXIT", "exit_date": None, "exit_price": None,
                "exit_reason": "DATA_INCOMPLETE", "holding_days": None,
                "current_price": None, "current_value": None}

    # Gather all closes (full history for MA warmup + simulation period)
    all_closes = get_close_series(ohlc, ticker,
                                  after_date=date(2000, 1, 1),
                                  to_date=valuation_date)
    if not all_closes:
        return {"exit_model": "MA_EXIT", "exit_date": None, "exit_price": None,
                "exit_reason": "DATA_INCOMPLETE", "holding_days": None,
                "current_price": None, "current_value": None}

    # Seed window with up to ma_period closes on or before entry_date
    window = [c for d, c in all_closes if d <= entry_date][-ma_period:]
    sim_series = [(d, c) for d, c in all_closes if d > entry_date]

    for i, (d, close) in enumerate(sim_series):
        window.append(close)
        if len(window) > ma_period:
            window.pop(0)
        ma = sum(window) / len(window)
        if close < ma:
            return {
                "exit_model": "MA_EXIT",
                "exit_date": d.isoformat(),
                "exit_price": round(close, 2),
                "exit_reason": "MA_BREAK",
                "holding_days": i + 1,
                "current_price": round(close, 2),
                "current_value": round(close * shares, 2),
            }

    current_price = sim_series[-1][1] if sim_series else entry_price
    return {
        "exit_model": "MA_EXIT",
        "exit_date": None,
        "exit_price": None,
        "exit_reason": "OPEN_POSITION",
        "holding_days": len(sim_series),
        "current_price": round(current_price, 2),
        "current_value": round(current_price * shares, 2),
    }


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
