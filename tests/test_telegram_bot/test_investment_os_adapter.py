from __future__ import annotations
import json
from pathlib import Path
from unittest.mock import patch

FAKE_SNAPSHOT = {
    "ranked": [
        {"rank": 1, "ticker": "2382.TW", "name": "廣達", "score": 85, "signal": "BUY"},
        {"rank": 2, "ticker": "2454.TW", "name": "聯發科", "score": 80, "signal": "HOLD"},
    ],
    "decisions": [{"ticker": "2382.TW", "action": "BUY", "reason": "STRONG_SIGNAL"}],
    "watchlist": [{"ticker": "2382.TW", "name": "廣達", "last_rank": 1}],
}


def test_load_snapshot_returns_empty_when_file_missing(tmp_path):
    """load_snapshot() returns {} when the snapshot file does not exist."""
    with patch("telegram_bot.adapters.investment_os.SNAPSHOT_FILE", tmp_path / "missing.json"):
        from telegram_bot.adapters.investment_os import load_snapshot
        result = load_snapshot()
    assert result == {}


def test_load_snapshot_returns_data(tmp_path):
    """load_snapshot() parses and returns the snapshot JSON."""
    snap_file = tmp_path / "signal_snapshot.json"
    snap_file.write_text(json.dumps(FAKE_SNAPSHOT), encoding="utf-8")
    with patch("telegram_bot.adapters.investment_os.SNAPSHOT_FILE", snap_file):
        from telegram_bot.adapters.investment_os import load_snapshot
        result = load_snapshot()
    assert result["ranked"][0]["ticker"] == "2382.TW"


def test_load_daily_report_returns_empty_when_no_files(tmp_path):
    """load_daily_report() returns '' when no report files exist."""
    with patch("telegram_bot.adapters.investment_os.DAILY_REPORT_DIR", tmp_path):
        from telegram_bot.adapters.investment_os import load_daily_report
        result = load_daily_report()
    assert result == ""


def test_load_daily_report_truncates_to_key_sections(tmp_path):
    """load_daily_report() extracts key sections when report is too long."""
    report_dir = tmp_path
    long_text = "## Preamble\n" + "x" * 9000 + "\n## Role-Aware Candidate Summary\nIMPORTANT\n## Other\nstuff"
    (report_dir / "2026-05-12_daily_report.md").write_text(long_text, encoding="utf-8")
    with patch("telegram_bot.adapters.investment_os.DAILY_REPORT_DIR", report_dir):
        from telegram_bot.adapters.investment_os import load_daily_report
        result = load_daily_report("2026-05-12")
    assert "IMPORTANT" in result
    assert len(result) < 9000


def test_load_intraday_slots_returns_empty_when_no_dir(tmp_path):
    """load_intraday_slots() returns [] when the date directory does not exist."""
    with patch("telegram_bot.adapters.investment_os.INTRADAY_DIR", tmp_path):
        from telegram_bot.adapters.investment_os import load_intraday_slots
        result = load_intraday_slots("2026-05-12")
    assert result == []


def test_build_context_summary_contains_candidates(tmp_path):
    """build_context_summary() includes ticker names from ranked candidates."""
    snap_file = tmp_path / "signal_snapshot.json"
    snap_file.write_text(json.dumps(FAKE_SNAPSHOT), encoding="utf-8")
    with patch("telegram_bot.adapters.investment_os.SNAPSHOT_FILE", snap_file):
        with patch("telegram_bot.adapters.investment_os.DAILY_REPORT_DIR", tmp_path):
            with patch("telegram_bot.adapters.investment_os.INTRADAY_DIR", tmp_path):
                from telegram_bot.adapters import investment_os as ios
                result = ios.build_context_summary()
    assert "2382.TW" in result
    assert "廣達" in result
