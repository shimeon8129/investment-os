# tests/test_five_day_top1_atr_backtest.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest


def test_import():
    import analysis.five_day_top1_atr_backtest  # noqa: F401
