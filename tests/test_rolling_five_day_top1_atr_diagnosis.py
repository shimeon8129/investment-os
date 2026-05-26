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
