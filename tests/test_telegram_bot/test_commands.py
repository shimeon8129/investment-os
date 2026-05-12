from __future__ import annotations
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_update(text=""):
    update = MagicMock()
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    update.message.text = text
    return update


@pytest.mark.asyncio
async def test_cmd_help_replies_with_command_list():
    """cmd_help() sends a message containing all command names."""
    from telegram_bot.handlers.commands import cmd_help
    update = _make_update()
    await cmd_help(update, MagicMock())
    call_args = update.message.reply_text.call_args[0][0]
    assert "/status" in call_args
    assert "/watchlist" in call_args
    assert "/daily" in call_args
    assert "/ask" in call_args


@pytest.mark.asyncio
async def test_cmd_status_shows_candidates(tmp_path):
    """cmd_status() lists top candidates from snapshot."""
    snap = {
        "ranked": [{"rank": 1, "ticker": "2382.TW", "name": "廣達", "score": 85, "signal": "BUY"}],
        "decisions": [],
    }
    snap_file = tmp_path / "signal_snapshot.json"
    snap_file.write_text(json.dumps(snap), encoding="utf-8")
    with patch("telegram_bot.adapters.investment_os.SNAPSHOT_FILE", snap_file):
        from telegram_bot.handlers import commands
        import importlib; importlib.reload(commands)
        update = _make_update()
        await commands.cmd_status(update, MagicMock())
    reply = update.message.reply_text.call_args[0][0]
    assert "2382.TW" in reply


@pytest.mark.asyncio
async def test_cmd_status_shows_no_data_message_when_snapshot_empty(tmp_path):
    """cmd_status() informs user when no snapshot data is available."""
    with patch("telegram_bot.adapters.investment_os.SNAPSHOT_FILE", tmp_path / "missing.json"):
        from telegram_bot.handlers import commands
        import importlib; importlib.reload(commands)
        update = _make_update()
        await commands.cmd_status(update, MagicMock())
    reply = update.message.reply_text.call_args[0][0]
    assert "暫無" in reply or "daily" in reply


@pytest.mark.asyncio
async def test_cmd_daily_runs_subprocess_and_reports_result():
    """cmd_daily() invokes daily_run.py and replies with completion status."""
    mock_result = MagicMock(returncode=0, stdout="Done", stderr="")
    with patch("subprocess.run", return_value=mock_result):
        from telegram_bot.handlers.commands import cmd_daily
        update = _make_update()
        ctx = MagicMock()
        await cmd_daily(update, ctx)
    calls = [c[0][0] for c in update.message.reply_text.call_args_list]
    assert any("完成" in c or "daily" in c.lower() for c in calls)
