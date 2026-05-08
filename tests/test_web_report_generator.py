import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json
from reporting.web_report_generator import _nav_bar, _badge, _html_page, _load_json, generate_status_page


def test_nav_bar_marks_active():
    html = _nav_bar("status")
    assert 'class="active"' in html
    assert "今日狀態" in html
    assert "歷史記錄" in html
    assert "Replay" in html


def test_nav_bar_active_link_is_not_href():
    html = _nav_bar("history")
    assert 'href="history.html" class="active"' in html


def test_badge_pass_green():
    html = _badge("PASS")
    assert "green" in html
    assert "PASS" in html


def test_badge_fail_red():
    html = _badge("FAIL")
    assert "red" in html


def test_badge_unknown_grey():
    html = _badge("UNKNOWN")
    assert "grey" in html


def test_html_page_has_structure():
    body = "<p>test</p>"
    html = _html_page("Test Title", "status", body)
    assert "<!DOCTYPE html>" in html
    assert "Test Title" in html
    assert "<p>test</p>" in html
    assert "Investment OS" in html


def test_load_json_missing_returns_empty(tmp_path):
    result = _load_json(tmp_path / "nonexistent.json")
    assert result == {}


def test_load_json_reads_file(tmp_path):
    p = tmp_path / "test.json"
    p.write_text('{"key": "value"}', encoding="utf-8")
    assert _load_json(p) == {"key": "value"}


_SIGNAL = {
    "date": "2026-05-08",
    "generated_at": "2026-05-08 16:00:11",
    "status": "PASS",
    "market_status": "OPEN",
    "data_mode": "OBSERVATION",
    "market_context": {"markets": {"TW": {"status": "OPEN"}, "US": {"status": "OPEN"}}},
    "checks": [
        {"label": "daily_decision_dashboard", "status": "PASS"},
        {"label": "pipeline_main_v1", "status": "PASS"},
    ],
    "watchlist_count": 27,
    "holdings_count": 7,
}

_MAINLINE = {
    "market_state": "RANGE",
    "market_score": 0.007,
    "vix_value": 17.2,
    "ranked": [
        {"ticker": "2464.TW", "name": "盟立", "sector": "Equipment",
         "signal": "BUY", "score": 151.4},
        {"ticker": "2356.TW", "name": "英業達", "sector": "Server",
         "signal": "BUY", "score": 145.5},
    ],
    "decisions": {
        "2464.TW": {"action": "BUY", "reason": "REDUCED_BY_MARKET", "position_size": 0.1},
    },
}


def test_generate_status_page_creates_file(tmp_path):
    generate_status_page(web_dir=tmp_path, signal=_SIGNAL, mainline=_MAINLINE)
    assert (tmp_path / "status.html").exists()


def test_generate_status_page_contains_status_badge(tmp_path):
    generate_status_page(web_dir=tmp_path, signal=_SIGNAL, mainline=_MAINLINE)
    html = (tmp_path / "status.html").read_text()
    assert "PASS" in html
    assert "green" in html


def test_generate_status_page_contains_candidates(tmp_path):
    generate_status_page(web_dir=tmp_path, signal=_SIGNAL, mainline=_MAINLINE)
    html = (tmp_path / "status.html").read_text()
    assert "2464.TW" in html
    assert "盟立" in html
    assert "151.4" in html


def test_generate_status_page_contains_decisions(tmp_path):
    generate_status_page(web_dir=tmp_path, signal=_SIGNAL, mainline=_MAINLINE)
    html = (tmp_path / "status.html").read_text()
    assert "REDUCED_BY_MARKET" in html


def test_generate_status_page_market_closed_shows_banner(tmp_path):
    closed_signal = {**_SIGNAL, "market_status": "CLOSED_WEEKEND"}
    generate_status_page(web_dir=tmp_path, signal=closed_signal, mainline={})
    html = (tmp_path / "status.html").read_text()
    assert "休市" in html
    assert "2464.TW" not in html


def test_generate_status_page_contains_checks(tmp_path):
    generate_status_page(web_dir=tmp_path, signal=_SIGNAL, mainline=_MAINLINE)
    html = (tmp_path / "status.html").read_text()
    assert "daily_decision_dashboard" in html
    assert "pipeline_main_v1" in html


from reporting.web_report_generator import generate_history_page

_OBS_SUMMARY_MD = """\
# Investment OS Observation Summary - 2026-05-08

## Final Status

PASS

## Market Gate

- TW market status: OPEN

## Stable Observation Record

- Counts as stable observation record: YES
- Type: OPEN-day PASS
- Reason: All subprocesses PASS

*Generated at: 2026-05-08 16:00:11*
"""

_DAILY_REPORT_MD = """\
# Investment OS Daily Report - 2026-05-08

## Human Summary

- Market state: **RANGE** | Score: 0.0070 | VIX: 17.20

**Top 3 candidates:**

1. 2464.TW 盟立 — Score: 151.40 | Signal: BUY
"""


def test_generate_history_page_creates_file(tmp_path):
    obs_dir = tmp_path / "observation"
    daily_dir = tmp_path / "daily"
    obs_dir.mkdir(); daily_dir.mkdir()
    (obs_dir / "2026-05-08_observation_summary.md").write_text(_OBS_SUMMARY_MD)
    (daily_dir / "2026-05-08_daily_report.md").write_text(_DAILY_REPORT_MD)

    generate_history_page(web_dir=tmp_path, obs_dir=obs_dir, daily_dir=daily_dir)
    assert (tmp_path / "history.html").exists()


def test_generate_history_page_shows_row(tmp_path):
    obs_dir = tmp_path / "observation"
    daily_dir = tmp_path / "daily"
    obs_dir.mkdir(); daily_dir.mkdir()
    (obs_dir / "2026-05-08_observation_summary.md").write_text(_OBS_SUMMARY_MD)
    (daily_dir / "2026-05-08_daily_report.md").write_text(_DAILY_REPORT_MD)

    generate_history_page(web_dir=tmp_path, obs_dir=obs_dir, daily_dir=daily_dir)
    html = (tmp_path / "history.html").read_text()
    assert "2026-05-08" in html
    assert "PASS" in html
    assert "RANGE" in html
    assert "17.20" in html
    assert "2464.TW" in html


def test_generate_history_page_empty_dir(tmp_path):
    obs_dir = tmp_path / "observation"
    obs_dir.mkdir()
    generate_history_page(web_dir=tmp_path, obs_dir=obs_dir, daily_dir=tmp_path / "daily")
    html = (tmp_path / "history.html").read_text()
    assert "歷史記錄" in html
    assert "尚無資料" in html
