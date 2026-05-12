from __future__ import annotations
import importlib
import sys


def test_config_has_path_constants():
    """Config exposes SNAPSHOT_FILE, DAILY_REPORT_DIR, INTRADAY_DIR as Path objects."""
    import telegram_bot.config as cfg
    from pathlib import Path
    assert isinstance(cfg.SNAPSHOT_FILE, Path)
    assert isinstance(cfg.DAILY_REPORT_DIR, Path)
    assert isinstance(cfg.INTRADAY_DIR, Path)


def test_allowed_chat_ids_parsed_correctly(monkeypatch):
    """ALLOWED_CHAT_IDS parses comma-separated integers from env."""
    monkeypatch.setenv("ALLOWED_CHAT_IDS", "111,222,333")
    import telegram_bot.config as cfg
    importlib.reload(cfg)
    assert cfg.get_allowed_chat_ids() == frozenset({111, 222, 333})


def test_allowed_chat_ids_empty_when_not_set(monkeypatch):
    """get_allowed_chat_ids() returns empty frozenset when env var missing."""
    monkeypatch.delenv("ALLOWED_CHAT_IDS", raising=False)
    import telegram_bot.config as cfg
    importlib.reload(cfg)
    assert cfg.get_allowed_chat_ids() == frozenset()
