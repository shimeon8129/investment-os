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
