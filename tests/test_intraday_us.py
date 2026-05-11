"""Tests for --market us flag and build_summary integration in intraday_observation."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_us_valid_slots_defined():
    """US_VALID_SLOTS contains the three expected slot names."""
    from jobs.intraday_observation import US_VALID_SLOTS
    assert "us_market_open" in US_VALID_SLOTS
    assert "us_midday" in US_VALID_SLOTS
    assert "us_post_close_review" in US_VALID_SLOTS


def test_run_daily_us_calls_daily_run_us(monkeypatch):
    """_run_daily('us') invokes jobs.daily_run_us module."""
    import subprocess as sp
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        m = MagicMock()
        m.stdout = ""
        m.stderr = ""
        m.returncode = 0
        return m

    monkeypatch.setattr(sp, "run", fake_run)
    from jobs.intraday_observation import _run_daily
    _run_daily("us")
    assert "jobs.daily_run_us" in " ".join(captured["cmd"])


def test_run_daily_tw_calls_daily_run(monkeypatch):
    """_run_daily('tw') invokes jobs.daily_run module."""
    import subprocess as sp
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        m = MagicMock()
        m.stdout = ""
        m.stderr = ""
        m.returncode = 0
        return m

    monkeypatch.setattr(sp, "run", fake_run)
    from jobs.intraday_observation import _run_daily
    _run_daily("tw")
    assert "jobs.daily_run" in " ".join(captured["cmd"])
    assert "daily_run_us" not in " ".join(captured["cmd"])


def test_daily_run_us_exits_zero_without_candidates(tmp_path, monkeypatch):
    """daily_run_us returns 0 when candidates_us.json does not exist."""
    import jobs.daily_run_us as dru
    monkeypatch.setattr(dru, "CANDIDATES_US", tmp_path / "candidates_us.json")
    assert dru.main() == 0


def test_daily_run_us_exits_zero_with_empty_candidates(tmp_path, monkeypatch):
    """daily_run_us returns 0 when candidates_us.json is an empty list."""
    import jobs.daily_run_us as dru
    f = tmp_path / "candidates_us.json"
    f.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(dru, "CANDIDATES_US", f)
    assert dru.main() == 0
