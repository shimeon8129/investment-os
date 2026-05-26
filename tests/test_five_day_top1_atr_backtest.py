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


from analysis.five_day_top1_atr_backtest import build_entry


def test_build_entry_shares_and_cost():
    # 2026-05-08 Top1 is 2464.TW. Mock close=122.0 for all 38 days.
    # shares = floor(100000 / 122) = 819
    # actual_cost = 819 * 122 = 99918
    # unused_cash = 100000 - 99918 = 82
    start = date(2026, 4, 1)
    ohlc = _make_ohlc("2464.TW", start, [130.0] * 38, [118.0] * 38, [122.0] * 38)
    entry = build_entry(1, "2026-05-08", ohlc, 100_000)
    assert entry["ticker"] == "2464.TW"
    assert entry["entry_price"] == pytest.approx(122.0, rel=1e-3)
    assert entry["shares"] == 819
    assert entry["actual_cost"] == pytest.approx(819 * 122.0, rel=1e-4)
    assert entry["unused_cash"] == pytest.approx(100_000 - 819 * 122.0, rel=1e-4)


def test_build_entry_data_quality_fail_on_missing_price():
    entry = build_entry(1, "2026-05-08", pd.DataFrame(), 100_000)
    assert entry["data_quality_flag"] == "FAIL"
    assert entry["entry_price"] is None


from analysis.five_day_top1_atr_backtest import simulate_atr_exit


def test_atr_exit_triggers_when_close_falls_below_trailing_stop():
    # entry_price=100, ATR20=5, trailing_mult=2.0
    # Day1: close=110 → highest=110, trailing_stop=110-10=100 → 110>100 no exit
    # Day2: close=105 → highest=110, trailing_stop=100 → 105>100 no exit
    # Day3: close=95  → highest=110, trailing_stop=100 → 95<100 → EXIT
    entry_date = date(2026, 5, 7)
    closes = [100.0, 110.0, 105.0, 95.0, 90.0]
    ohlc = _make_ohlc("X.TW", entry_date, closes, closes, closes)
    entry = {
        "ticker": "X.TW", "entry_date": entry_date.isoformat(),
        "entry_price": 100.0, "shares": 10, "atr20_at_entry": 5.0,
    }
    result = simulate_atr_exit(entry, ohlc, initial_mult=1.5, trailing_mult=2.0,
                               valuation_date=date(2026, 5, 20))
    assert result["exit_reason"] == "ATR_TRAILING_STOP"
    assert result["exit_price"] == pytest.approx(95.0)
    assert result["holding_days"] == 3


def test_atr_exit_open_position_when_no_stop_triggered():
    entry_date = date(2026, 5, 7)
    closes = [100.0, 110.0, 120.0, 130.0]
    ohlc = _make_ohlc("X.TW", entry_date, closes, closes, closes)
    entry = {
        "ticker": "X.TW", "entry_date": entry_date.isoformat(),
        "entry_price": 100.0, "shares": 10, "atr20_at_entry": 5.0,
    }
    result = simulate_atr_exit(entry, ohlc, 1.5, 2.0,
                               valuation_date=entry_date + timedelta(days=3))
    assert result["exit_reason"] == "OPEN_POSITION"
    assert result["current_price"] == pytest.approx(130.0)


def test_atr_exit_data_incomplete_when_atr_missing():
    entry = {
        "ticker": "X.TW", "entry_date": "2026-05-07",
        "entry_price": 100.0, "shares": 10, "atr20_at_entry": None,
    }
    result = simulate_atr_exit(entry, pd.DataFrame(), 1.5, 2.0, date(2026, 5, 20))
    assert result["exit_reason"] == "DATA_INCOMPLETE"


from analysis.five_day_top1_atr_backtest import simulate_fixed10d_exit, simulate_ma_exit


def test_fixed10d_exit_uses_10th_trading_day_close():
    # closes[0]=100 (entry), closes[10]=110 (exit on 10th day after)
    entry_date = date(2026, 5, 7)
    closes = list(range(100, 116))  # 16 values: 100..115
    ohlc = _make_ohlc("X.TW", entry_date, closes, closes, closes)
    trading_days = [entry_date + timedelta(days=i) for i in range(16)]
    entry = {
        "ticker": "X.TW", "entry_date": entry_date.isoformat(),
        "entry_price": 100.0, "shares": 10, "atr20_at_entry": 5.0,
    }
    result = simulate_fixed10d_exit(entry, ohlc, trading_days, date(2026, 6, 1))
    assert result["exit_reason"] == "FIXED_10D"
    assert result["holding_days"] == 10
    assert result["exit_price"] == pytest.approx(110.0)


def test_ma_exit_triggers_when_close_below_ma5():
    # closes: entry_date=100, then 100×4, then 90 (close<MA5 of 98)
    # window=[100,100,100,100,90], MA=98, close=90 < 98 → EXIT
    entry_date = date(2026, 5, 7)
    closes = [100.0, 100.0, 100.0, 100.0, 100.0, 90.0, 85.0]
    ohlc = _make_ohlc("X.TW", entry_date, closes, closes, closes)
    entry = {
        "ticker": "X.TW", "entry_date": entry_date.isoformat(),
        "entry_price": 100.0, "shares": 10, "atr20_at_entry": 5.0,
    }
    result = simulate_ma_exit(entry, ohlc, ma_period=5, valuation_date=date(2026, 6, 1))
    assert result["exit_reason"] == "MA_BREAK"
    assert result["exit_price"] == pytest.approx(90.0)


from analysis.five_day_top1_atr_backtest import compute_position_grade


def test_grade_a_for_strong_signal_high_confidence():
    assert compute_position_grade("BUY_BREAKOUT", "BULL", "HIGH")   == "A"
    assert compute_position_grade("BUY",          "RANGE", "MEDIUM") == "A"
    assert compute_position_grade("TREND_CONTINUE","BULL", "HIGH")   == "A"


def test_grade_b_for_low_confidence_or_late_signal():
    assert compute_position_grade("BUY",      "RANGE", "LOW")  == "B"
    assert compute_position_grade("BUY",      "RANGE", None)   == "B"
    assert compute_position_grade("BUY_LATE", "RANGE", "HIGH") == "B"


def test_grade_c_for_watch_signal_or_bear_market():
    assert compute_position_grade("WATCH_READY", "RANGE", "LOW")  == "C"
    assert compute_position_grade("BUY",         "BEAR",  "HIGH") == "C"
