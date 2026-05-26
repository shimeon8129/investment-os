# tests/test_tiered_atr_exit_backtest.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from datetime import date, timedelta
import pandas as pd


def test_import():
    import analysis.tiered_atr_exit_backtest  # noqa: F401


# ─── Shared test helpers ──────────────────────────────────────────────────────

def _make_ohlc(ticker: str, start: date, highs, lows, closes) -> pd.DataFrame:
    """Build mock MultiIndex OHLC DataFrame (same pattern as P0.2/P0.3 tests)."""
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


def _make_entry(
    ticker="X.TW",
    entry_date_offset=0,
    entry_price=100.0,
    shares=10,
    atr20=5.0,
    start=None,
) -> dict:
    """Build minimal entry dict compatible with simulate_tiered_atr_exit."""
    if start is None:
        start = date(2026, 1, 1)
    entry_date = start + timedelta(days=entry_date_offset)
    return {
        "entry_date":   entry_date.isoformat(),
        "ticker":       ticker,
        "entry_price":  entry_price,
        "shares":       shares,
        "atr20_at_entry": atr20,
        "actual_cost":  entry_price * shares,
        "initial_stop": round(entry_price - 1.5 * atr20, 2),
        "data_quality_flag": "PASS",
        "data_quality_note": "",
    }


from analysis.tiered_atr_exit_backtest import simulate_tiered_atr_exit


def test_tiered_low_threshold_trailing_stop():
    # Entry=100, ATR=5 → initial_stop=92.5
    # Closes: [100(entry), 100, 100, 89] → highest=100, float_pct=0% < 5% → trail_mult=2.0
    # trailing_stop = 100 - 2.0*5 = 90.0
    # Day 2: close=89 < 90 → exit
    start = date(2026, 1, 1)
    closes = [100.0, 100.0, 100.0, 89.0, 85.0]
    ohlc = _make_ohlc("X.TW", start, closes, closes, closes)
    report_dates = [start + timedelta(days=i) for i in range(1, 5)]
    entry = _make_entry(start=start)
    result = simulate_tiered_atr_exit(entry, ohlc, report_dates,
                                      date(2026, 6, 1), hold_protection=False)
    assert result["exit_reason"] == "ATR_TRAILING_STOP"
    # close_series starts after entry=start, so day-0 of series is start+1 (close=100)
    # Day-0: i=0, max(trailing=90, initial=92.5)=92.5, close=100 → no exit
    # Day-1: i=1, close=100, trailing=90 → no exit
    # Day-2: i=2, close=89 < 90 → exit
    assert result["exit_price"] == pytest.approx(89.0)
    assert result["holding_days"] == 3


def test_tiered_mid_threshold_widens_stop():
    # Entry=100, ATR=5 → initial=92.5
    # Day 0: close=108 → highest=108, float_pct=8% → trail_mult=2.5, trailing=108-12.5=95.5
    # Day 1: close=94 → 94 < 95.5 → exit
    start = date(2026, 1, 1)
    closes = [100.0, 108.0, 94.0, 90.0]
    ohlc = _make_ohlc("X.TW", start, closes, closes, closes)
    report_dates = [start + timedelta(days=i) for i in range(1, 4)]
    entry = _make_entry(start=start)
    result = simulate_tiered_atr_exit(entry, ohlc, report_dates,
                                      date(2026, 6, 1), hold_protection=False)
    assert result["exit_reason"] == "ATR_TRAILING_STOP"
    assert result["exit_price"] == pytest.approx(94.0)
    assert result["holding_days"] == 2


def test_tiered_high_threshold_uses_widest_stop():
    # Entry=100, ATR=5 → initial=92.5
    # Day 0: close=120 → highest=120, float_pct=20% ≥ 15% → trail_mult=3.0, trailing=120-15=105
    # Day 1: close=104 → 104 < 105 → exit
    start = date(2026, 1, 1)
    closes = [100.0, 120.0, 104.0, 100.0]
    ohlc = _make_ohlc("X.TW", start, closes, closes, closes)
    report_dates = [start + timedelta(days=i) for i in range(1, 4)]
    entry = _make_entry(start=start)
    result = simulate_tiered_atr_exit(entry, ohlc, report_dates,
                                      date(2026, 6, 1), hold_protection=False)
    assert result["exit_reason"] == "ATR_TRAILING_STOP"
    assert result["exit_price"] == pytest.approx(104.0)
    assert result["holding_days"] == 2


def test_hold_protection_prevents_trailing_stop():
    # Entry=100, ATR=5 → initial_stop=92.5
    # report_dates after start: [start+1, start+2, start+3, start+4, start+5]
    # Hold protection window = first 3 report dates = [start+1, start+2, start+3]
    # protection_end = start+3
    #
    # Day 0 (d=start+1, close=107): highest=107, float_pct=7% → trail=107-12.5=94.5
    #   in_protection: start+1 <= start+3 → True → effective=initial=92.5
    #   107 < 92.5? No → continue
    # Day 1 (d=start+2, close=93): highest=107, trail=94.5
    #   93 < 94.5 → hold_period_protected=True; effective=92.5, 93 < 92.5? No → continue
    # Day 2 (d=start+3, close=95): in_protection → effective=92.5, 95 < 92.5? No → continue
    # Day 3 (d=start+4, close=93): NOT in protection → effective=94.5
    #   93 < 94.5 → EXIT
    start = date(2026, 1, 1)
    closes = [100.0, 107.0, 93.0, 95.0, 93.0, 90.0]
    ohlc = _make_ohlc("X.TW", start, closes, closes, closes)
    report_dates = [start + timedelta(days=i) for i in range(1, 6)]
    entry = _make_entry(start=start)
    result = simulate_tiered_atr_exit(entry, ohlc, report_dates,
                                      date(2026, 6, 1), hold_protection=True)
    assert result["exit_reason"] == "ATR_TRAILING_STOP"
    assert result["hold_period_protected"] is True
    assert date.fromisoformat(result["exit_date"]) == start + timedelta(days=4)


def test_no_hold_protection_exits_earlier():
    # Same scenario as above but hold_protection=False → exits on day 1 (start+2, close=93)
    start = date(2026, 1, 1)
    closes = [100.0, 107.0, 93.0, 95.0, 93.0, 90.0]
    ohlc = _make_ohlc("X.TW", start, closes, closes, closes)
    report_dates = [start + timedelta(days=i) for i in range(1, 6)]
    entry = _make_entry(start=start)
    result = simulate_tiered_atr_exit(entry, ohlc, report_dates,
                                      date(2026, 6, 1), hold_protection=False)
    assert result["exit_reason"] == "ATR_TRAILING_STOP"
    assert result["hold_period_protected"] is False
    assert date.fromisoformat(result["exit_date"]) == start + timedelta(days=2)


def test_tiered_atr_open_position_when_no_stop_triggered():
    start = date(2026, 1, 1)
    closes = [100.0, 105.0, 110.0, 115.0]
    ohlc = _make_ohlc("X.TW", start, closes, closes, closes)
    report_dates = [start + timedelta(days=i) for i in range(1, 4)]
    entry = _make_entry(start=start)
    result = simulate_tiered_atr_exit(entry, ohlc, report_dates,
                                      start + timedelta(days=3), hold_protection=False)
    assert result["exit_reason"] == "OPEN_POSITION"
    assert result["current_price"] == pytest.approx(115.0)
    assert result["hold_period_protected"] is False


def test_tiered_atr_data_incomplete_when_missing_atr():
    start = date(2026, 1, 1)
    entry = _make_entry(start=start)
    entry["atr20_at_entry"] = None
    result = simulate_tiered_atr_exit(entry, pd.DataFrame(), [],
                                      date(2026, 6, 1), hold_protection=True)
    assert result["exit_reason"] == "DATA_INCOMPLETE"
    assert result["hold_period_protected"] is False


def test_hold_protection_boundary_exact_date_is_protected():
    # protection_end is the 3rd report date after entry = start+3
    # A close that would exit via trailing on start+3 should NOT exit (still in protection)
    # A close that would exit via trailing on start+4 SHOULD exit
    start = date(2026, 1, 1)
    # Day 0 (start+1): close=115 → highest=115, float_pct=15% → trail=3.0, trailing=115-15=100
    # Days in protection: start+1, start+2, start+3 (protection_end = start+3)
    # Day 2 (start+3): close=99, trailing=100 → IN protection → effective=initial=92.5 → no exit
    # Day 3 (start+4): close=99, trailing=100 → NOT in protection → effective=100 → EXIT
    closes = [100.0, 115.0, 110.0, 99.0, 99.0, 90.0]
    ohlc = _make_ohlc("X.TW", start, closes, closes, closes)
    report_dates = [start + timedelta(days=i) for i in range(1, 6)]
    entry = _make_entry(start=start)
    result = simulate_tiered_atr_exit(entry, ohlc, report_dates,
                                      date(2026, 6, 1), hold_protection=True)
    assert result["exit_reason"] == "ATR_TRAILING_STOP"
    # Should exit on start+4, not start+3
    assert date.fromisoformat(result["exit_date"]) == start + timedelta(days=4)


from analysis.tiered_atr_exit_backtest import compute_profit_giveback_pct, _run_one_model


def test_profit_giveback_pct_partial_giveback():
    # Peak unrealized = +10000, exit PnL = +2000 → gave back 80%
    lot = {"max_profit_seen": 10000.0, "gross_pnl": 2000.0,
           "exit_reason": "ATR_TRAILING_STOP"}
    assert compute_profit_giveback_pct(lot) == pytest.approx(0.80, rel=1e-3)


def test_profit_giveback_pct_crosses_to_loss():
    # Peak = +10000, exit PnL = -5000 → gave back 150% (crossed into loss)
    lot = {"max_profit_seen": 10000.0, "gross_pnl": -5000.0,
           "exit_reason": "ATR_TRAILING_STOP"}
    assert compute_profit_giveback_pct(lot) == pytest.approx(1.50, rel=1e-3)


def test_profit_giveback_pct_zero_peak_returns_none():
    lot = {"max_profit_seen": 0.0, "gross_pnl": -500.0,
           "exit_reason": "ATR_TRAILING_STOP"}
    assert compute_profit_giveback_pct(lot) is None


def test_profit_giveback_pct_none_peak_returns_none():
    lot = {"max_profit_seen": None, "gross_pnl": 1000.0,
           "exit_reason": "OPEN_POSITION"}
    assert compute_profit_giveback_pct(lot) is None


def test_profit_giveback_pct_open_position():
    # Open: peak=5000, current gross_pnl=3000 → gave back 40%
    lot = {"max_profit_seen": 5000.0, "gross_pnl": 3000.0,
           "exit_reason": "OPEN_POSITION"}
    assert compute_profit_giveback_pct(lot) == pytest.approx(0.40, rel=1e-3)


def test_run_one_model_atr_base_returns_exit_info():
    start = date(2026, 1, 1)
    closes = [100.0, 100.0, 100.0, 80.0]
    ohlc = _make_ohlc("X.TW", start, closes, closes, closes)
    report_dates = [start + timedelta(days=i) for i in range(1, 4)]
    entry = _make_entry(start=start)
    result = _run_one_model("ATR_BASE", entry, ohlc, report_dates,
                            date(2026, 6, 1))
    assert "exit_reason" in result
    assert "exit_model" in result


def test_run_one_model_tiered_atr_returns_hold_field():
    start = date(2026, 1, 1)
    closes = [100.0, 110.0, 120.0]
    ohlc = _make_ohlc("X.TW", start, closes, closes, closes)
    report_dates = [start + timedelta(days=i) for i in range(1, 3)]
    entry = _make_entry(start=start)
    result = _run_one_model("TIERED_ATR", entry, ohlc, report_dates,
                            start + timedelta(days=2))
    assert "hold_period_protected" in result


def test_run_one_model_unknown_raises():
    with pytest.raises(ValueError, match="Unknown model"):
        _run_one_model("DOES_NOT_EXIST", {}, pd.DataFrame(), [], date(2026, 1, 1))
