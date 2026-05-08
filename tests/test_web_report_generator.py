import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reporting.web_report_generator import _nav_bar, _badge, _html_page, _load_json


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
