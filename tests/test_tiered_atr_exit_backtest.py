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
