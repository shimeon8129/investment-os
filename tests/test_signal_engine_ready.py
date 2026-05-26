# tests/test_signal_engine_ready.py
# P0 Patch A: 驗證 READY 不再無條件覆蓋為 BUY

import sys
import os
import pandas as pd
import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from signal_engine.entry import generate_entry_signal


def _make_inputs(prices, vols, ticker="T"):
    """Build minimal close/volume/features DataFrames for testing."""
    idx = pd.date_range("2025-01-01", periods=len(prices), freq="B")
    close = pd.DataFrame({ticker: prices}, index=idx, dtype=float)
    volume = pd.DataFrame({ticker: vols}, index=idx, dtype=float)
    price_s = pd.Series(prices, index=idx, dtype=float)
    vol_s = pd.Series(vols, index=idx, dtype=float)
    ma5 = pd.DataFrame({ticker: price_s.rolling(5).mean()}, index=idx)
    vol_ratio = pd.DataFrame({ticker: vol_s / vol_s.rolling(5).mean()}, index=idx)
    features = {"ma5": ma5, "vol_ratio": vol_ratio}
    return close, volume, features


def test_ready_alone_becomes_watch_ready():
    """READY 單獨出現（無 BUY 訊號）→ WATCH_READY，不是 BUY。"""
    # declining stock: below MA5, low volume → no entry signal
    prices = [100.0] * 20 + [95.0, 94.0, 93.0, 92.0, 80.0]
    vols = [1000.0] * 20 + [500.0, 500.0, 500.0, 500.0, 400.0]
    close, volume, features = _make_inputs(prices, vols)
    candidate_info = {"T": {"level": "READY"}}

    signals = generate_entry_signal(close, volume, features, candidate_info)

    assert signals["T"] == "WATCH_READY", f"Expected WATCH_READY, got {signals['T']}"
    assert signals["T"] != "BUY", "READY alone must NOT produce BUY"


def test_ready_preserves_existing_breakout():
    """READY 不應覆蓋既有的 BUY_BREAKOUT。"""
    # breakout: latest > 20d high, high vol_ratio
    base = [100.0] * 20
    prices = base + [95.0, 96.0, 97.0, 99.0, 130.0]  # 130 > prev 20d high of 100
    vols = [1000.0] * 20 + [1200.0, 1200.0, 1200.0, 1200.0, 2500.0]
    close, volume, features = _make_inputs(prices, vols)
    candidate_info = {"T": {"level": "READY"}}

    signals = generate_entry_signal(close, volume, features, candidate_info)

    assert signals["T"] == "BUY_BREAKOUT", f"Expected BUY_BREAKOUT, got {signals['T']}"


def test_ready_preserves_trend_continue():
    """READY 不應覆蓋 TREND_CONTINUE。"""
    # trend: above MA5, moderate vol (> 1.0 but not > 1.2), latest not > prev_close
    prices = [95.0] * 20 + [96.0, 97.0, 98.0, 99.0, 99.0]  # flat last bar
    vols = [1000.0] * 20 + [1050.0, 1050.0, 1050.0, 1050.0, 1080.0]
    close, volume, features = _make_inputs(prices, vols)
    candidate_info = {"T": {"level": "READY"}}

    signals = generate_entry_signal(close, volume, features, candidate_info)

    # Latest close (99) > MA5 (~98.2) and vol_ratio ≈ 1.04 > 1.0 → TREND_CONTINUE
    assert signals["T"] in ("TREND_CONTINUE", "BUY_BREAKOUT", "BUY_LATE"), (
        f"Expected a valid continuation signal, got {signals['T']}"
    )
    assert signals["T"] != "BUY", "READY must NOT override to BUY"


def test_no_ready_level_no_watch_ready():
    """level != READY 的候選不應產生 WATCH_READY。"""
    prices = [100.0] * 20 + [95.0, 94.0, 93.0, 92.0, 80.0]
    vols = [1000.0] * 20 + [500.0, 500.0, 500.0, 500.0, 400.0]
    close, volume, features = _make_inputs(prices, vols)
    candidate_info = {"T": {"level": "EARLY"}}

    signals = generate_entry_signal(close, volume, features, candidate_info)

    assert signals["T"] != "WATCH_READY"
