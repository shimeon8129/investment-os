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


from analysis.rolling_five_day_top1_atr_diagnosis import label_post_trade


def test_label_open_winner():
    assert label_post_trade("OPEN_POSITION", 5000.0, None, None) == "OPEN_WINNER"


def test_label_open_risk():
    assert label_post_trade("OPEN_POSITION", -500.0, None, None) == "OPEN_RISK"


def test_label_data_quality():
    assert label_post_trade("DATA_INCOMPLETE", None, None, None) == "DATA_QUALITY_ISSUE"


def test_label_atr_too_tight_takes_priority_over_next1d():
    # post_exit > 5% → ATR_TOO_TIGHT, even though next_1d would suggest entry failure
    assert label_post_trade("ATR_TRAILING_STOP", -1000.0, 0.08, -0.05) == "ATR_TOO_TIGHT"


def test_label_entry_signal_failure():
    # post_exit ≤ 5% and next_1d < -3%
    assert label_post_trade("ATR_TRAILING_STOP", -1000.0, 0.02, -0.04) == "ENTRY_SIGNAL_FAILURE"


def test_label_market_reversal_fallthrough():
    # post_exit ≤ 5% and next_1d ≥ -3% → neither ATR_TOO_TIGHT nor ENTRY_SIGNAL_FAILURE
    assert label_post_trade("ATR_TRAILING_STOP", -1000.0, 0.02, -0.01) == "MARKET_REVERSAL"


def test_label_fixed10d_defaults_to_market_reversal():
    assert label_post_trade("FIXED_10D", -500.0, None, None) == "MARKET_REVERSAL"


from analysis.rolling_five_day_top1_atr_diagnosis import (
    assemble_diagnosis_lot,
    aggregate_diagnosis_basket,
    DIAGNOSIS_STRATEGY_ID,
)


def test_assemble_diagnosis_lot_overrides_strategy_and_adds_diagnosis_fields():
    base = _make_base_lot()
    post_exit = {
        "post_exit_max_return": 0.06,
        "post_exit_high_after_exit": 1060.0,
        "days_to_post_exit_high": 3,
    }
    lot = assemble_diagnosis_lot(
        base_lot=base,
        post_exit_info=post_exit,
        post_trade_label="ATR_TOO_TIGHT",
        next_1d_return=0.02,
        next_3d_return=0.05,
        basket_id="2026-05-07_5D",
        is_immature=False,
    )
    assert lot["strategy_id"]           == DIAGNOSIS_STRATEGY_ID
    assert lot["basket_id"]             == "2026-05-07_5D"
    assert lot["is_immature"]           is False
    assert lot["post_trade_label"]      == "ATR_TOO_TIGHT"
    assert lot["post_exit_max_return"]  == pytest.approx(0.06)
    assert lot["next_1d_return"]        == pytest.approx(0.02)
    assert lot["next_3d_return"]        == pytest.approx(0.05)
    # original P0.2 fields must still be present
    assert lot["gross_pnl"]            == pytest.approx(1000.0)


def test_aggregate_diagnosis_basket_counts_labels_correctly():
    basket_dates = [date(2026, 5, d) for d in [7, 8, 11, 12, 13]]
    lots = [
        {**_make_base_lot("A.TW",  1000, "ATR_TRAILING_STOP"), "post_trade_label": "ATR_TOO_TIGHT"},
        {**_make_base_lot("B.TW", -500,  "ATR_TRAILING_STOP"), "post_trade_label": "ENTRY_SIGNAL_FAILURE"},
        {**_make_base_lot("A.TW",  2000, "OPEN_POSITION",  current_value=101_000),
         "post_trade_label": "OPEN_WINNER"},
        {**_make_base_lot("C.TW",  500,  "ATR_TRAILING_STOP"), "post_trade_label": "MARKET_REVERSAL"},
        {**_make_base_lot("A.TW", -200,  "ATR_TRAILING_STOP"), "post_trade_label": "MARKET_REVERSAL"},
    ]
    basket = aggregate_diagnosis_basket(
        lots, basket_dates, planned_capital=500_000,
        basket_id="2026-05-07_5D", is_immature=False,
    )
    assert basket["basket_id"]           == "2026-05-07_5D"
    assert basket["strategy_id"]         == DIAGNOSIS_STRATEGY_ID
    assert basket["is_immature"]         is False
    assert basket["false_exit_count"]    == 1   # ATR_TOO_TIGHT
    assert basket["entry_failure_count"] == 1   # ENTRY_SIGNAL_FAILURE
    assert basket["open_winner_count"]   == 1
    assert basket["market_reversal_count"] == 2
    # A.TW appears 3 times → duplicate_ticker_count = 3 (lots whose ticker is duplicated)
    assert basket["duplicate_ticker_count"] == 3
    assert basket["unique_ticker_count"]    == 3  # A, B, C


from analysis.rolling_five_day_top1_atr_diagnosis import aggregate_diagnosis_summary


def _make_basket_record(basket_id, gross_pnl, false_exit, entry_failure, is_immature=False):
    return {
        "basket_id": basket_id, "is_immature": is_immature,
        "gross_pnl": gross_pnl, "net_pnl_estimated": gross_pnl * 0.9,
        "gross_return_pct": gross_pnl / 500_000 * 100,
        "false_exit_count": false_exit, "entry_failure_count": entry_failure,
        "open_winner_count": 1, "open_risk_count": 0,
        "market_reversal_count": 2, "data_quality_issue_count": 0,
        "open_positions": 1, "exited_positions": 4, "entry_count": 5,
        "duplicate_ticker_count": 2, "unique_ticker_count": 3,
    }


def test_aggregate_diagnosis_summary_totals():
    baskets = [
        _make_basket_record("B1", 30_000, false_exit=1, entry_failure=1),
        _make_basket_record("B2", -5_000, false_exit=0, entry_failure=2, is_immature=True),
    ]
    summary = aggregate_diagnosis_summary(baskets)
    assert summary["n_baskets"]                == 2
    assert summary["n_immature"]               == 1
    assert summary["total_false_exit_count"]   == 1
    assert summary["total_entry_failure_count"]== 3
    assert summary["total_lots"]               == 10


def test_aggregate_diagnosis_summary_empty():
    assert aggregate_diagnosis_summary([])["n_baskets"] == 0


import json as _json
from analysis.rolling_five_day_top1_atr_diagnosis import (
    write_lots_csv,
    write_baskets_csv,
    write_summary_json,
    write_diagnosis_report_md,
    write_validation_report_md,
)


def _make_minimal_result():
    lot = {
        **_make_base_lot(),
        "strategy_id":               "ROLLING_FIVE_DAY_TOP1_ATR_DIAGNOSIS_v0_1",
        "basket_id":                 "2026-05-07_5D",
        "is_immature":               False,
        "next_1d_return":            0.01,
        "next_3d_return":            0.02,
        "post_exit_max_return":      0.06,
        "post_exit_high_after_exit": 1060.0,
        "days_to_post_exit_high":    3,
        "post_trade_label":          "ATR_TOO_TIGHT",
    }
    basket = {
        "basket_id": "2026-05-07_5D", "is_immature": False,
        "gross_pnl": 1000.0, "net_pnl_estimated": 850.0,
        "gross_return_pct": 0.2, "entry_count": 1,
        "false_exit_count": 1, "entry_failure_count": 0,
        "open_winner_count": 0, "open_risk_count": 0,
        "market_reversal_count": 0, "data_quality_issue_count": 0,
        "model_baskets": {"ATR_BASE": {"gross_pnl": 1000.0, "gross_return_pct": 0.2}},
    }
    summary = {"n_baskets": 1, "total_false_exit_count": 1, "total_lots": 1}
    return {
        "primary_lots_all": [lot],
        "baskets_primary":  [basket],
        "summary":          summary,
        "model_comparison": {"ATR_BASE": {"avg_gross_return_pct": 0.2, "avg_gross_pnl": 1000.0}},
        "valuation_date":   "2026-05-26",
        "n_baskets":        1,
    }


def test_write_lots_csv_creates_file_with_required_columns(tmp_path):
    result = _make_minimal_result()
    p = tmp_path / "lots.csv"
    write_lots_csv(result["primary_lots_all"], p)
    assert p.exists()
    text = p.read_text()
    assert "post_trade_label" in text
    assert "basket_id" in text
    assert "post_exit_max_return" in text


def test_write_baskets_csv_creates_file_with_required_columns(tmp_path):
    result = _make_minimal_result()
    p = tmp_path / "baskets.csv"
    write_baskets_csv(result["baskets_primary"], p)
    assert p.exists()
    assert "false_exit_count" in p.read_text()


def test_write_summary_json_creates_valid_json(tmp_path):
    result = _make_minimal_result()
    p = tmp_path / "summary.json"
    write_summary_json(result, p)
    assert p.exists()
    data = _json.loads(p.read_text())
    assert "summary" in data
    assert "model_comparison" in data


def test_write_diagnosis_report_md_contains_key_sections(tmp_path):
    result = _make_minimal_result()
    p = tmp_path / "report.md"
    write_diagnosis_report_md(result, p)
    assert p.exists()
    text = p.read_text()
    assert "ATR_TOO_TIGHT" in text
    assert "Advisory" in text


def test_write_validation_report_md_contains_advisory_notice(tmp_path):
    result = _make_minimal_result()
    p = tmp_path / "validation.md"
    write_validation_report_md(result, p)
    assert p.exists()
    text = p.read_text().lower()
    assert "simulation" in text or "advisory" in text
