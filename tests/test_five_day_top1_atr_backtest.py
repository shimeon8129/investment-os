# tests/test_five_day_top1_atr_backtest.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest


def test_import():
    import analysis.five_day_top1_atr_backtest  # noqa: F401


from datetime import date, timedelta
import numpy as np
import pandas as pd

from analysis.five_day_top1_atr_backtest import compute_atr20, get_close, get_close_series


def _make_ohlc(ticker: str, start: date, highs, lows, closes) -> pd.DataFrame:
    """Helper: build mock MultiIndex OHLC DataFrame."""
    n = len(closes)
    dates = [start + timedelta(days=i) for i in range(n)]
    df = pd.DataFrame(
        {
            ("High",  ticker): list(highs),
            ("Low",   ticker): list(lows),
            ("Close", ticker): list(closes),
        },
        index=dates,
    )
    df.columns = pd.MultiIndex.from_tuples(df.columns)
    return df


def test_compute_atr20_constant_bars():
    # All 25 bars: H=10, L=8, C=9, prev_close=9
    # TR = max(10-8=2, |10-9|=1, |8-9|=1) = 2 for every bar
    # ATR20 = 2.0
    start = date(2026, 1, 1)
    ohlc = _make_ohlc("X.TW", start, [10.0] * 25, [8.0] * 25, [9.0] * 25)
    as_of = start + timedelta(days=25)
    atr = compute_atr20(ohlc, "X.TW", as_of)
    assert atr == pytest.approx(2.0, rel=1e-4)


def test_compute_atr20_insufficient_data_returns_none():
    start = date(2026, 1, 1)
    ohlc = _make_ohlc("X.TW", start, [10.0] * 10, [8.0] * 10, [9.0] * 10)
    atr = compute_atr20(ohlc, "X.TW", start + timedelta(days=11))
    assert atr is None


def test_compute_atr20_unknown_ticker_returns_none():
    start = date(2026, 1, 1)
    ohlc = _make_ohlc("X.TW", start, [10.0] * 25, [8.0] * 25, [9.0] * 25)
    assert compute_atr20(ohlc, "UNKNOWN.TW", start + timedelta(days=25)) is None


def test_get_close_found():
    start = date(2026, 1, 1)
    ohlc = _make_ohlc("X.TW", start, [10.0] * 3, [8.0] * 3, [100.0, 105.0, 110.0])
    assert get_close(ohlc, "X.TW", start + timedelta(days=1)) == pytest.approx(105.0)


def test_get_close_missing_date_returns_none():
    start = date(2026, 1, 1)
    ohlc = _make_ohlc("X.TW", start, [10.0] * 3, [8.0] * 3, [100.0, 105.0, 110.0])
    assert get_close(ohlc, "X.TW", date(2030, 1, 1)) is None


def test_get_close_series_filters_correctly():
    start = date(2026, 1, 1)
    ohlc = _make_ohlc("X.TW", start, [10.0] * 5, [8.0] * 5, [100.0, 101.0, 102.0, 103.0, 104.0])
    # after_date=start (strictly after), to_date=start+3
    result = get_close_series(ohlc, "X.TW", after_date=start, to_date=start + timedelta(days=3))
    dates_only = [d for d, _ in result]
    assert start not in dates_only                   # strictly after
    assert start + timedelta(days=3) in dates_only  # inclusive upper bound
    assert len(result) == 3


from analysis.five_day_top1_atr_backtest import parse_daily_report


def test_parse_daily_report_2026_05_07():
    p = parse_daily_report("2026-05-07")
    assert p is not None
    assert p["ticker"] == "3711.TW"
    assert p["name"] == "日月光投控"
    assert p["signal"] == "BUY"
    assert p["market_state"] == "RANGE"
    assert p["score"] == pytest.approx(173.466, rel=1e-2)


def test_parse_daily_report_2026_05_11_includes_role_fields():
    p = parse_daily_report("2026-05-11")
    assert p is not None
    assert p["ticker"] == "2464.TW"
    assert p["base_role"] == "WAVE_SWING"
    assert p["role_confidence"] == "LOW"


def test_parse_daily_report_missing_date_returns_none():
    assert parse_daily_report("2000-01-01") is None
