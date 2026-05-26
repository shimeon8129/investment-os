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


# ─────────────────────────────────────────────────────────────
# Position grade diagnostic (v0.1: from available report fields)
# ─────────────────────────────────────────────────────────────

_GRADE_A_SIGNALS = {"BUY_BREAKOUT", "TREND_CONTINUE", "BUY"}
_GRADE_C_SIGNALS = {"WATCH_READY"}


def compute_position_grade(
    signal: str,
    market_state: Optional[str],
    role_confidence: Optional[str],
) -> str:
    """Diagnostic grade A/B/C.

    v0.1 uses only: signal type, market_state, role_confidence.
    Chips and chase_risk are not available in historical daily reports.
    """
    if not signal:
        return "C"
    if market_state == "BEAR":
        return "C"
    if signal in _GRADE_C_SIGNALS:
        return "C"
    if signal in _GRADE_A_SIGNALS and market_state in ("BULL", "RANGE") \
            and role_confidence not in ("LOW", None):
        return "A"
    if "LATE" in signal:
        return "B"
    return "B"


# ─────────────────────────────────────────────────────────────
# PnL and transaction cost calculator
# ─────────────────────────────────────────────────────────────

def compute_pnl(
    actual_cost: float,
    shares: int,
    exit_price: Optional[float],
    exit_reason: str,
    valuation_date: date,
    current_price: Optional[float] = None,
) -> dict:
    """Compute realized/unrealized PnL with Taiwan transaction costs."""
    buy_fee = round(actual_cost * BUY_FEE_RATE, 2)
    is_exited = exit_reason not in ("OPEN_POSITION", "DATA_INCOMPLETE") \
                and exit_price is not None

    if is_exited:
        exit_value = shares * exit_price
        sell_fee   = round(exit_value * SELL_FEE_RATE, 2)
        tax        = round(exit_value * STT_RATE, 2)
        gross_pnl  = round(exit_value - actual_cost, 2)
        net_pnl    = round(gross_pnl - buy_fee - sell_fee - tax, 2)
        return {
            "realized_pnl": gross_pnl, "unrealized_pnl": None,
            "gross_pnl": gross_pnl,
            "gross_return_pct": round(gross_pnl / actual_cost * 100, 4) if actual_cost else None,
            "estimated_buy_fee": buy_fee, "estimated_sell_fee": sell_fee,
            "estimated_tax": tax, "estimated_net_pnl": net_pnl,
        }

    # Open / data-incomplete — use current_price
    price = current_price or exit_price
    if price is None:
        return {
            "realized_pnl": None, "unrealized_pnl": None, "gross_pnl": None,
            "gross_return_pct": None,
            "estimated_buy_fee": buy_fee, "estimated_sell_fee": None,
            "estimated_tax": None, "estimated_net_pnl": None,
        }
    current_value = shares * price
    sell_fee  = round(current_value * SELL_FEE_RATE, 2)
    tax       = round(current_value * STT_RATE, 2)
    gross_pnl = round(current_value - actual_cost, 2)
    net_pnl   = round(gross_pnl - buy_fee - sell_fee - tax, 2)
    return {
        "realized_pnl": None, "unrealized_pnl": gross_pnl,
        "gross_pnl": gross_pnl,
        "gross_return_pct": round(gross_pnl / actual_cost * 100, 4) if actual_cost else None,
        "estimated_buy_fee": buy_fee, "estimated_sell_fee": sell_fee,
        "estimated_tax": tax, "estimated_net_pnl": net_pnl,
    }


# ─────────────────────────────────────────────────────────────
# Lot assembly + basket aggregation
# ─────────────────────────────────────────────────────────────

def assemble_lot(entry: dict, exit_info: dict, grade: str, pnl: dict) -> dict:
    """Merge entry, exit, grade, PnL into a single lot record (all spec fields)."""
    entry_price  = entry.get("entry_price")
    initial_stop = entry.get("initial_stop")
    actual_cost  = entry.get("actual_cost") or 0
    shares       = entry.get("shares") or 0
    gross_pnl    = pnl.get("gross_pnl")

    r_multiple = None
    if gross_pnl is not None and entry_price and initial_stop and shares:
        risk_per_share = entry_price - initial_stop
        if risk_per_share > 0:
            r_multiple = round(gross_pnl / (risk_per_share * shares), 3)

    return {
        "strategy_id":               entry.get("strategy_id", STRATEGY_ID),
        "basket_id":                 entry.get("basket_id", BASKET_ID),
        "entry_index":               entry.get("entry_index"),
        "entry_date":                entry.get("entry_date"),
        "ticker":                    entry.get("ticker"),
        "name":                      entry.get("name"),
        "rank":                      entry.get("rank", "Top1"),
        "market_state":              entry.get("market_state"),
        "entry_signal":              entry.get("entry_signal"),
        "role":                      entry.get("role"),
        "position_grade":            grade,
        "planned_entry_capital":     entry.get("planned_entry_capital"),
        "entry_price":               entry_price,
        "shares":                    shares,
        "actual_cost":               actual_cost,
        "unused_cash":               entry.get("unused_cash"),
        "atr20_at_entry":            entry.get("atr20_at_entry"),
        "initial_stop":              initial_stop,
        "highest_close_since_entry": exit_info.get("highest_close_since_entry"),
        "trailing_stop":             exit_info.get("trailing_stop_at_exit"),
        "exit_model":                exit_info.get("exit_model"),
        "exit_date":                 exit_info.get("exit_date"),
        "exit_price":                exit_info.get("exit_price"),
        "exit_reason":               exit_info.get("exit_reason"),
        "holding_days":              exit_info.get("holding_days"),
        "current_price":             exit_info.get("current_price"),
        "current_value":             exit_info.get("current_value"),
        "realized_pnl":              pnl.get("realized_pnl"),
        "unrealized_pnl":            pnl.get("unrealized_pnl"),
        "gross_pnl":                 gross_pnl,
        "gross_return_pct":          pnl.get("gross_return_pct"),
        "estimated_buy_fee":         pnl.get("estimated_buy_fee"),
        "estimated_sell_fee":        pnl.get("estimated_sell_fee"),
        "estimated_tax":             pnl.get("estimated_tax"),
        "estimated_net_pnl":         pnl.get("estimated_net_pnl"),
        "max_profit_seen":           exit_info.get("max_profit_seen"),
        "max_drawdown_seen":         exit_info.get("max_drawdown_seen"),
        "r_multiple":                r_multiple,
        "data_quality_flag":         entry.get("data_quality_flag", "FAIL"),
        "data_quality_note":         entry.get("data_quality_note", ""),
    }


def aggregate_basket(lots: list[dict], planned_capital: float) -> dict:
    """Basket-level summary from list of lot records."""
    valid    = [l for l in lots if l.get("actual_cost") is not None]
    deployed = sum(l["actual_cost"] for l in valid)

    stock_value    = sum((l.get("current_value") or 0) for l in valid
                         if l.get("exit_reason") == "OPEN_POSITION")
    realized_cash  = sum((l.get("exit_price") or 0) * (l.get("shares") or 0)
                         for l in valid
                         if l.get("exit_reason") not in
                         ("OPEN_POSITION", "DATA_INCOMPLETE", None))
    gross_pnl = sum(l.get("gross_pnl") or 0 for l in valid)
    net_pnl   = sum(l.get("estimated_net_pnl") or 0 for l in valid)
    total_eq  = (planned_capital - deployed) + stock_value + realized_cash

    open_lots   = [l for l in valid if l.get("exit_reason") == "OPEN_POSITION"]
    exited_lots = [l for l in valid
                   if l.get("exit_reason") not in ("OPEN_POSITION", "DATA_INCOMPLETE", None)]
    best  = max(valid, key=lambda l: l.get("gross_pnl") or float("-inf")) if valid else None
    worst = min(valid, key=lambda l: l.get("gross_pnl") or float("inf"))  if valid else None

    return {
        "strategy_id":           STRATEGY_ID,
        "basket_id":             BASKET_ID,
        "start_date":            lots[0].get("entry_date") if lots else None,
        "entry_count":           len(valid),
        "planned_capital":       planned_capital,
        "deployed_capital":      round(deployed, 2),
        "cash_remainder":        round(planned_capital - deployed, 2),
        "current_stock_value":   round(stock_value, 2),
        "realized_value":        round(realized_cash, 2),
        "total_equity":          round(total_eq, 2),
        "gross_pnl":             round(gross_pnl, 2),
        "net_pnl_estimated":     round(net_pnl, 2),
        "gross_return_pct":      round(gross_pnl / planned_capital * 100, 4) if planned_capital else None,
        "net_return_pct_estimated": round(net_pnl / planned_capital * 100, 4) if planned_capital else None,
        "open_positions":        len(open_lots),
        "exited_positions":      len(exited_lots),
        "best_lot":              best.get("ticker") if best else None,
        "worst_lot":             worst.get("ticker") if worst else None,
    }


# ─────────────────────────────────────────────────────────────
# TW trading day helper
# ─────────────────────────────────────────────────────────────

def get_tw_trading_days(start: date, end: date) -> list[date]:
    from utils.market_calendar import is_market_open
    result, d = [], start
    while d <= end:
        if is_market_open("TW", d) in ("OPEN", "OPEN_EARLY_CLOSE"):
            result.append(d)
        d += timedelta(days=1)
    return result


# ─────────────────────────────────────────────────────────────
# Backtest orchestrator
# ─────────────────────────────────────────────────────────────

def run_backtest(
    start_date: str,
    n_entries: int,
    entry_capital: float,
    valuation_date: str,
) -> dict:
    val_date = date.fromisoformat(valuation_date)
    start    = date.fromisoformat(start_date)

    # 1. Collect entry trading days
    all_tw = get_tw_trading_days(start, val_date)
    entry_days = [d for d in all_tw if d >= start][:n_entries]
    if len(entry_days) < n_entries:
        print(f"[WARN] Only {len(entry_days)} of {n_entries} entry days available")

    # 2. Parse daily reports → unique tickers
    parsed_reports: dict[str, dict] = {}
    for d in entry_days:
        p = parse_daily_report(d.isoformat())
        if p:
            parsed_reports[d.isoformat()] = p
        else:
            print(f"[WARN] No daily report for {d}")
    tickers = list({p["ticker"] for p in parsed_reports.values()})
    if not tickers:
        return {"error": "No valid daily reports found", "lots": [], "basket": {}}

    # 3. Fetch OHLC (60-day lookback for ATR20 warmup)
    ohlc_start = (start - timedelta(days=65)).isoformat()
    ohlc_end   = (val_date + timedelta(days=1)).isoformat()
    print(f"[backtest] Fetching OHLC for {tickers} ({ohlc_start} → {ohlc_end})")
    ohlc = fetch_ohlc(tickers, ohlc_start, ohlc_end)
    if ohlc.empty:
        return {"error": "OHLC fetch returned empty DataFrame", "lots": [], "basket": {}}

    # 4. Build entries
    entries = []
    for i, d in enumerate(entry_days, 1):
        e = build_entry(i, d.isoformat(), ohlc, entry_capital)
        entries.append(e)
        print(f"[backtest] Entry {i}: {d} {e.get('ticker')} @ {e.get('entry_price')} "
              f"shares={e.get('shares')} ATR20={e.get('atr20_at_entry')} DQ={e.get('data_quality_flag')}")

    trading_days = get_tw_trading_days(start, val_date)

    # 5. Simulate exits for each ATR variant + benchmarks
    lots_by_variant: dict[str, list[dict]] = {v: [] for v in ATR_VARIANTS}
    lots_fixed10d: list[dict] = []
    lots_ma5:      list[dict] = []

    for entry in entries:
        grade = compute_position_grade(
            entry.get("entry_signal", ""),
            entry.get("market_state"),
            entry.get("_role_confidence"),
        )
        for v_name, (im, tm) in ATR_VARIANTS.items():
            ei   = simulate_atr_exit(entry, ohlc, im, tm, val_date)
            pnl  = compute_pnl(
                entry.get("actual_cost") or 0, entry.get("shares") or 0,
                ei.get("exit_price"), ei.get("exit_reason", "DATA_INCOMPLETE"),
                val_date, ei.get("current_price"),
            )
            lots_by_variant[v_name].append(assemble_lot(entry, ei, grade, pnl))

        fi   = simulate_fixed10d_exit(entry, ohlc, trading_days, val_date)
        fp   = compute_pnl(entry.get("actual_cost") or 0, entry.get("shares") or 0,
                           fi.get("exit_price"), fi.get("exit_reason", "DATA_INCOMPLETE"),
                           val_date, fi.get("current_price"))
        lots_fixed10d.append(assemble_lot(entry, fi, grade, fp))

        mi   = simulate_ma_exit(entry, ohlc, ma_period=5, valuation_date=val_date)
        mp   = compute_pnl(entry.get("actual_cost") or 0, entry.get("shares") or 0,
                           mi.get("exit_price"), mi.get("exit_reason", "DATA_INCOMPLETE"),
                           val_date, mi.get("current_price"))
        lots_ma5.append(assemble_lot(entry, mi, grade, mp))

    planned = entry_capital * n_entries
    baskets_all: dict[str, dict] = {v: aggregate_basket(lots_by_variant[v], planned)
                                    for v in ATR_VARIANTS}
    baskets_all["FIXED_10D"] = aggregate_basket(lots_fixed10d, planned)
    baskets_all["MA5"]       = aggregate_basket(lots_ma5, planned)

    primary_lots   = lots_by_variant[PRIMARY_ATR_VARIANT]
    primary_basket = baskets_all[PRIMARY_ATR_VARIANT]

    return {
        "strategy_id": STRATEGY_ID, "basket_id": BASKET_ID,
        "start_date": start_date, "valuation_date": valuation_date,
        "entry_capital": entry_capital, "n_entries": n_entries,
        "planned_capital": planned, "tickers": tickers,
        "lots": primary_lots, "basket": primary_basket,
        "lots_by_variant": lots_by_variant, "baskets_all": baskets_all,
        "lots_fixed10d": lots_fixed10d, "lots_ma5": lots_ma5,
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


def write_basket_json(basket: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(basket, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )


def write_backtest_report_md(result: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    b, lots = result["basket"], result["lots"]
    lines: list[str] = []
    w = lines.append

    w(f"# Backtest Report — {STRATEGY_ID}")
    w(f""); w(f"Generated: {date.today().isoformat()}")
    w(f"Valuation date: {result['valuation_date']}")
    w(""); w("---"); w("")

    w("## Strategy Parameters"); w("")
    w(f"- Strategy ID: `{result['strategy_id']}`")
    w(f"- Basket ID: `{result['basket_id']}`")
    w(f"- Planned capital: {result['planned_capital']:,.0f} TWD")
    w(f"- Entry capital / lot: {result['entry_capital']:,.0f} TWD")
    w(f"- Lots: {result['n_entries']}")
    w(f"- Primary exit model: **{PRIMARY_ATR_VARIANT}** (initial 1.5×ATR, trailing 2.0×ATR)")
    w(f"- Entry price: signal-day close (v0.1)"); w(""); w("---"); w("")

    w("## Lot-Level Results (ATR_BASE — primary)"); w("")
    w("| # | Date | Ticker | Entry | Shares | Cost | ATR20 | InitStop | TrailStop | Exit | Reason | GrossPnL | Grade |")
    w("|---|------|--------|-------|--------|------|-------|----------|-----------|------|--------|----------|-------|")
    for l in lots:
        gp  = l.get("gross_pnl") or 0
        pnl = f"+{gp:,.0f}" if gp >= 0 else f"{gp:,.0f}"
        w(f"| {l.get('entry_index')} | {l.get('entry_date')} | {l.get('ticker')} "
          f"| {l.get('entry_price')} | {l.get('shares')} | {(l.get('actual_cost') or 0):,.0f} "
          f"| {l.get('atr20_at_entry') or '—'} | {l.get('initial_stop') or '—'} "
          f"| {l.get('trailing_stop') or '—'} "
          f"| {l.get('exit_price') or '—'} | {l.get('exit_reason')} | {pnl} | {l.get('position_grade')} |")
    w(""); w("---"); w("")

    w("## Basket Summary (ATR_BASE)"); w("")
    w("| Field | Value |"); w("|-------|-------|")
    for k, v in b.items():
        w(f"| {k} | {v} |")
    w(""); w("---"); w("")

    w("## ATR Stop Status per Lot (ATR_BASE)"); w("")
    w("| Ticker | Entry | ATR20 | Initial Stop | Trailing Stop | Highest Close | Status |")
    w("|--------|-------|-------|-------------|--------------|--------------|--------|")
    for l in lots:
        w(f"| {l.get('ticker')} | {l.get('entry_price')} | {l.get('atr20_at_entry') or '—'} "
          f"| {l.get('initial_stop') or '—'} | {l.get('trailing_stop') or '—'} "
          f"| {l.get('highest_close_since_entry') or '—'} | {l.get('exit_reason')} |")
    w(""); w("---"); w("")

    w("## Multi-Model Comparison"); w("")
    w("| Model | GrossPnL | NetPnL(est) | Gross% | Net%(est) | Open | Exited |")
    w("|-------|----------|------------|--------|----------|------|--------|")
    for mn, mb in result["baskets_all"].items():
        w(f"| {mn} | {(mb.get('gross_pnl') or 0):,.0f} "
          f"| {(mb.get('net_pnl_estimated') or 0):,.0f} "
          f"| {mb.get('gross_return_pct') or 0:.2f}% "
          f"| {mb.get('net_return_pct_estimated') or 0:.2f}% "
          f"| {mb.get('open_positions')} | {mb.get('exited_positions')} |")
    w(""); w("---"); w("")

    w("## ATR Variant Comparison"); w("")
    w("| Variant | Init Mult | Trail Mult | GrossPnL | NetPnL(est) | Return% |")
    w("|---------|-----------|------------|----------|------------|---------|")
    for vn, (im, tm) in ATR_VARIANTS.items():
        vb = result["baskets_all"].get(vn, {})
        w(f"| {vn} | {im}× | {tm}× | {(vb.get('gross_pnl') or 0):,.0f} "
          f"| {(vb.get('net_pnl_estimated') or 0):,.0f} "
          f"| {vb.get('gross_return_pct') or 0:.2f}% |")
    w(""); w("")
    w("*Advisory only. No trades placed. All outputs for human review.*"); w("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_validation_report_md(result: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lots = result["lots"]
    lines: list[str] = []
    w = lines.append

    w(f"# Validation Report — {STRATEGY_ID}"); w("")
    w(f"Generated: {date.today().isoformat()}"); w("")
    w("## Assumptions"); w("")
    w("1. Entry price = signal-day adjusted close (yfinance auto_adjust=True, v0.1)")
    w("2. ATR20 = arithmetic mean of True Range over 20 trading days strictly before entry date")
    w("3. Trailing stop = highest_close_since_entry − trailing_mult × ATR20 (close-based exit)")
    w("4. On day-1 of hold: effective_stop = max(trailing_stop, initial_stop)")
    w("5. Duplicate tickers allowed across entry days (signal persistence)")
    w("6. Transaction costs: buy 0.1425%, sell 0.1425% + STT 0.3% on sell value")
    w("7. No slippage model in v0.1"); w("")

    w("## Data Quality Summary"); w("")
    w("| Entry | Ticker | DQ Flag | Note |")
    w("|-------|--------|---------|------|")
    for l in lots:
        w(f"| {l.get('entry_index')} | {l.get('ticker')} "
          f"| {l.get('data_quality_flag')} | {l.get('data_quality_note') or '—'} |")
    w("")

    w("## Known Limitations"); w("")
    w("- Score field not normalized across all dates (see spec §9)")
    w("- Position grade is diagnostic only — derived from signal/market_state/role_confidence; chips and chase_risk not available in historical reports")
    w("- Entry price uses adjusted close; may differ from actual signal-day raw close due to splits/dividends")
    w("- ATR20 uses calendar-day windows from yfinance, not exact TW trading-day count")
    w("- v0.1 does not compare next-day open vs VWAP entry prices"); w("")

    w("## Ticker Exposure Concentration"); w("")
    ticker_vals: dict[str, float] = {}
    for l in lots:
        t = l.get("ticker", "?")
        ticker_vals[t] = ticker_vals.get(t, 0) + (l.get("current_value") or 0)
    all_val = sum(ticker_vals.values()) or 1
    w("| Ticker | Market Value | % of Total |")
    w("|--------|-------------|------------|")
    for t, v in sorted(ticker_vals.items(), key=lambda x: -x[1]):
        w(f"| {t} | {v:,.0f} | {v / all_val * 100:.1f}% |")
    w(""); w("---"); w("")
    w("*Owner should review before any capital allocation decisions.*"); w("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Five-Day Top1 ATR Strategy Backtest v0.1")
    parser.add_argument("--start-date",      default="2026-05-07")
    parser.add_argument("--entries",         type=int,   default=5)
    parser.add_argument("--entry-capital",   type=float, default=100_000)
    parser.add_argument("--valuation-date",  default="2026-05-25")
    args = parser.parse_args()

    print(f"[backtest] {STRATEGY_ID}")
    print(f"[backtest] start={args.start_date}  entries={args.entries}  "
          f"capital/lot={args.entry_capital:,.0f}  valuation={args.valuation_date}")

    result = run_backtest(
        args.start_date, args.entries, args.entry_capital, args.valuation_date
    )
    if "error" in result:
        print(f"[ERROR] {result['error']}")
        return 1

    lots_csv      = DATA_BACKTEST      / "five_day_top1_atr_strategy_v0_1_lots.csv"
    basket_json   = DATA_BACKTEST      / "five_day_top1_atr_strategy_v0_1_basket.json"
    report_md     = REPORTS_BACKTEST   / "five_day_top1_atr_strategy_v0_1.md"
    validation_md = REPORTS_VALIDATION / "five_day_top1_atr_strategy_v0_1_validation.md"

    write_lots_csv(result["lots"], lots_csv)
    write_basket_json(result["basket"], basket_json)
    write_backtest_report_md(result, report_md)
    write_validation_report_md(result, validation_md)

    b = result["basket"]
    print(f"\n[backtest] Deployed:      {b.get('deployed_capital'):>12,.0f} TWD")
    print(f"[backtest] Gross PnL:     {b.get('gross_pnl'):>12,.0f} TWD  ({b.get('gross_return_pct'):.2f}%)")
    print(f"[backtest] Net PnL (est): {b.get('net_pnl_estimated'):>12,.0f} TWD  ({b.get('net_return_pct_estimated'):.2f}%)")
    print(f"[backtest] Open: {b.get('open_positions')}  Exited: {b.get('exited_positions')}")
    print(f"\n[backtest] Artifacts written:")
    print(f"  {lots_csv}")
    print(f"  {basket_json}")
    print(f"  {report_md}")
    print(f"  {validation_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
