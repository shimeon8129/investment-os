# tests/test_rolling_five_day_top1_atr_diagnosis.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from datetime import date, timedelta
import pandas as pd


def test_import():
    import analysis.rolling_five_day_top1_atr_diagnosis  # noqa: F401


# ─── Shared test helpers (used across all tasks) ───────────────────────────

def _make_ohlc(ticker: str, start: date, highs, lows, closes) -> pd.DataFrame:
    """Build mock MultiIndex OHLC DataFrame — same helper as P0.2 tests."""
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


def _make_base_lot(
    ticker="X.TW",
    gross_pnl=1000.0,
    exit_reason="ATR_TRAILING_STOP",
    actual_cost=99000.0,
    shares=100,
    current_value=None,
) -> dict:
    """Build a minimal dict that looks like the output of assemble_lot() from P0.2."""
    is_open = exit_reason == "OPEN_POSITION"
    return {
        "strategy_id":               "OLD_STRATEGY",
        "basket_id":                 "OLD_BASKET",
        "entry_index":               1,
        "entry_date":                "2026-05-07",
        "ticker":                    ticker,
        "name":                      "Test Co",
        "rank":                      "Top1",
        "market_state":              "RANGE",
        "entry_signal":              "BUY",
        "role":                      None,
        "position_grade":            "B",
        "planned_entry_capital":     100_000,
        "entry_price":               990.0,
        "shares":                    shares,
        "actual_cost":               actual_cost,
        "unused_cash":               1_000.0,
        "atr20_at_entry":            10.0,
        "initial_stop":              970.0,
        "highest_close_since_entry": 1_050.0,
        "trailing_stop":             1_030.0,
        "exit_model":                "ATR_TRAILING" if not is_open else "ATR_TRAILING",
        "exit_date":                 None if is_open else "2026-05-15",
        "exit_price":                None if is_open else 1_000.0,
        "exit_reason":               exit_reason,
        "holding_days":              8,
        "current_price":             1_000.0,
        "current_value":             current_value if current_value is not None else (None if not is_open else actual_cost + gross_pnl),
        "realized_pnl":              None if is_open else gross_pnl,
        "unrealized_pnl":            gross_pnl if is_open else None,
        "gross_pnl":                 gross_pnl,
        "gross_return_pct":          round(gross_pnl / actual_cost * 100, 4) if actual_cost else None,
        "estimated_buy_fee":         141.0,
        "estimated_sell_fee":        141.0,
        "estimated_tax":             300.0,
        "estimated_net_pnl":         round(gross_pnl - 582.0, 2),
        "max_profit_seen":           1_200.0,
        "max_drawdown_seen":         -200.0,
        "r_multiple":                0.5,
        "data_quality_flag":         "PASS",
        "data_quality_note":         "",
    }


from analysis.rolling_five_day_top1_atr_diagnosis import (
    get_available_report_dates,
    build_rolling_baskets,
)


def test_get_available_report_dates_returns_sorted(tmp_path, monkeypatch):
    import analysis.rolling_five_day_top1_atr_diagnosis as m
    monkeypatch.setattr(m, "REPORTS_DAILY", tmp_path)
    for ds in ["2026-05-13", "2026-05-07", "2026-05-08"]:
        (tmp_path / f"{ds}_daily_report.md").write_text(f"# fake {ds}\n")
    result = get_available_report_dates()
    assert result == [date(2026, 5, 7), date(2026, 5, 8), date(2026, 5, 13)]


def test_get_available_report_dates_skips_non_date_files(tmp_path, monkeypatch):
    import analysis.rolling_five_day_top1_atr_diagnosis as m
    monkeypatch.setattr(m, "REPORTS_DAILY", tmp_path)
    (tmp_path / "2026-05-07_daily_report.md").write_text("# fake\n")
    (tmp_path / "summary.md").write_text("ignore\n")
    result = get_available_report_dates()
    assert result == [date(2026, 5, 7)]


def test_build_rolling_baskets_window5():
    dates = [date(2026, 5, d) for d in [7, 8, 11, 12, 13, 14, 15]]
    baskets = build_rolling_baskets(dates, window=5)
    assert len(baskets) == 3
    assert baskets[0] == [date(2026, 5, d) for d in [7, 8, 11, 12, 13]]
    assert baskets[1] == [date(2026, 5, d) for d in [8, 11, 12, 13, 14]]
    assert baskets[2] == [date(2026, 5, d) for d in [11, 12, 13, 14, 15]]


def test_build_rolling_baskets_too_few_dates():
    dates = [date(2026, 5, d) for d in [7, 8, 11]]
    assert build_rolling_baskets(dates, window=5) == []


from analysis.rolling_five_day_top1_atr_diagnosis import (
    flag_immature_basket,
    compute_next_nd_return,
)

_ALL_REPORT_DATES = [date(2026, 5, d) for d in [7, 8, 11, 12, 13, 14, 15, 17, 21, 22, 25, 26]]


def test_flag_immature_basket_true_when_few_post_entry_dates():
    # last entry = 05/26; no report dates after 05/26 up to 05/26 → 0 < 5 → immature
    basket_dates = [date(2026, 5, d) for d in [17, 21, 22, 25, 26]]
    assert flag_immature_basket(basket_dates, _ALL_REPORT_DATES, date(2026, 5, 26)) is True


def test_flag_immature_basket_false_when_enough_post_entry_dates():
    # last entry = 05/13; post-entry dates: 05/14,15,17,21,22,25,26 = 7 ≥ 5 → not immature
    basket_dates = [date(2026, 5, d) for d in [7, 8, 11, 12, 13]]
    assert flag_immature_basket(basket_dates, _ALL_REPORT_DATES, date(2026, 5, 26)) is False


def test_compute_next_nd_return_1d():
    start = date(2026, 1, 1)
    ohlc  = _make_ohlc("X.TW", start, [10]*5, [8]*5, [100.0, 105.0, 110.0, 108.0, 112.0])
    entry = {"entry_date": start.isoformat(), "ticker": "X.TW", "entry_price": 100.0}
    result = compute_next_nd_return(entry, ohlc, n=1)
    # day 1 close = 105, entry = 100 → return = 5%
    assert result == pytest.approx(0.05, rel=1e-4)


def test_compute_next_nd_return_insufficient_returns_none():
    start = date(2026, 1, 1)
    ohlc  = _make_ohlc("X.TW", start, [10]*2, [8]*2, [100.0, 105.0])
    entry = {"entry_date": start.isoformat(), "ticker": "X.TW", "entry_price": 100.0}
    assert compute_next_nd_return(entry, ohlc, n=5) is None


def test_compute_next_nd_return_missing_entry_price_returns_none():
    start = date(2026, 1, 1)
    ohlc  = _make_ohlc("X.TW", start, [10]*5, [8]*5, [100.0]*5)
    entry = {"entry_date": start.isoformat(), "ticker": "X.TW", "entry_price": None}
    assert compute_next_nd_return(entry, ohlc, n=1) is None


from analysis.rolling_five_day_top1_atr_diagnosis import compute_post_exit_max_return


def test_compute_post_exit_max_return_finds_max():
    # exit on day 0 (close=100), then closes: 110, 120, 115
    start     = date(2026, 1, 1)
    ohlc      = _make_ohlc("X.TW", start, [12]*4, [8]*4, [100.0, 110.0, 120.0, 115.0])
    exit_date = start  # exit at day 0
    valuation = start + timedelta(days=3)
    result    = compute_post_exit_max_return("X.TW", exit_date, valuation, 100.0, ohlc)
    assert result["post_exit_max_return"]     == pytest.approx(0.20, rel=1e-4)
    assert result["post_exit_high_after_exit"]== pytest.approx(120.0)
    assert result["days_to_post_exit_high"]   == 2  # index 1 in post-exit series (110,120,115)


def test_compute_post_exit_max_return_no_post_exit_data():
    start  = date(2026, 1, 1)
    ohlc   = _make_ohlc("X.TW", start, [12]*1, [8]*1, [100.0])
    result = compute_post_exit_max_return("X.TW", start, start, 100.0, ohlc)
    assert result["post_exit_max_return"]      is None
    assert result["post_exit_high_after_exit"] is None
    assert result["days_to_post_exit_high"]    is None


def test_compute_post_exit_max_return_none_exit_date_returns_nulls():
    start  = date(2026, 1, 1)
    ohlc   = _make_ohlc("X.TW", start, [12]*3, [8]*3, [100.0, 110.0, 120.0])
    result = compute_post_exit_max_return("X.TW", None, start + timedelta(days=2), 100.0, ohlc)
    assert result["post_exit_max_return"] is None
