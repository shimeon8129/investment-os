# Telegram Bot for Investment OS — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Telegram Bot that pushes Investment OS job notifications, accepts commands to query state and trigger jobs, and answers questions via Claude with full Investment OS context.

**Architecture:** Modular bot (`telegram_bot/`) with an adapter layer that reads Investment OS data files, a Claude client for `/ask`, and a standalone `utils/telegram_notify.py` that existing jobs call after completing. Auth enforced via Chat ID whitelist on every handler.

**Tech Stack:** `python-telegram-bot>=20`, `anthropic`, `pytest`, `systemd`

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `telegram_bot/__init__.py` | Package marker |
| Create | `telegram_bot/config.py` | Read env vars; expose typed path constants |
| Create | `telegram_bot/adapters/__init__.py` | Package marker |
| Create | `telegram_bot/adapters/investment_os.py` | Read snapshot / daily report / intraday slots |
| Create | `telegram_bot/adapters/claude_client.py` | Build context + call Anthropic API |
| Create | `telegram_bot/handlers/__init__.py` | Package marker |
| Create | `telegram_bot/handlers/commands.py` | /start /help /status /watchlist /daily /intraday |
| Create | `telegram_bot/handlers/ask.py` | /ask handler |
| Create | `telegram_bot/bot.py` | App entry: auth middleware, register handlers, polling |
| Create | `utils/telegram_notify.py` | `send_notification(text)` — pure urllib, no bot dep |
| Create | `systemd/investment-os-telegram-bot.service` | systemd unit |
| Create | `tests/test_telegram_bot/__init__.py` | Package marker |
| Create | `tests/test_telegram_bot/test_telegram_notify.py` | Tests for notify utility |
| Create | `tests/test_telegram_bot/test_investment_os_adapter.py` | Tests for data adapter |
| Create | `tests/test_telegram_bot/test_claude_client.py` | Tests for Claude client |
| Create | `tests/test_telegram_bot/test_commands.py` | Tests for command handlers |
| Modify | `jobs/daily_run.py` | Add `send_notification()` call at end of `main()` |
| Modify | `jobs/intraday_observation.py` | Add `send_notification()` call after each slot |

---

## Pre-requisites

Before starting: obtain a Telegram Bot Token from @BotFather and your numeric Chat ID (send a message to your bot, then visit `https://api.telegram.org/bot<TOKEN>/getUpdates` and read `result[0].message.chat.id`).

---

## Task 1: Install Dependencies + Create .env Template

**Files:**
- Modify: `requirements.txt` (or install directly into venv)
- Create: `.env.example`

- [ ] **Step 1: Install packages into existing venv**

```bash
cd /home/shimeon/investment_os
source venv/bin/activate
pip install "python-telegram-bot>=20.0" anthropic
```

Expected: both packages install without conflict.

- [ ] **Step 2: Create .env.example**

Create `/home/shimeon/investment_os/.env.example`:

```
TELEGRAM_BOT_TOKEN=123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_CHAT_ID=987654321
ALLOWED_CHAT_IDS=987654321
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

- [ ] **Step 3: Create .env with your real values (do not commit)**

```bash
cp .env.example .env
# edit .env and fill in real values
```

- [ ] **Step 4: Verify .gitignore excludes .env**

```bash
grep -q "^\.env$" .gitignore && echo "OK" || echo "ADD .env to .gitignore"
```

If not present, add `.env` to `.gitignore`.

- [ ] **Step 5: Commit**

```bash
git add .env.example .gitignore
git commit -m "chore: add .env.example and ensure .env is gitignored for telegram bot"
```

---

## Task 2: Package Scaffolding + config.py

**Files:**
- Create: `telegram_bot/__init__.py`
- Create: `telegram_bot/config.py`
- Create: `telegram_bot/adapters/__init__.py`
- Create: `telegram_bot/handlers/__init__.py`

- [ ] **Step 1: Create package directories and __init__.py files**

```bash
mkdir -p telegram_bot/adapters telegram_bot/handlers
touch telegram_bot/__init__.py telegram_bot/adapters/__init__.py telegram_bot/handlers/__init__.py
mkdir -p tests/test_telegram_bot
touch tests/test_telegram_bot/__init__.py
```

- [ ] **Step 2: Write failing test for config**

Create `tests/test_telegram_bot/test_config.py`:

```python
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
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd /home/shimeon/investment_os
source venv/bin/activate
python -m pytest tests/test_telegram_bot/test_config.py -v
```

Expected: `ModuleNotFoundError: No module named 'telegram_bot.config'`

- [ ] **Step 4: Write config.py**

Create `telegram_bot/config.py`:

```python
from __future__ import annotations
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

def get_allowed_chat_ids() -> frozenset[int]:
    raw = os.getenv("ALLOWED_CHAT_IDS", "")
    return frozenset(int(x) for x in raw.split(",") if x.strip())

SNAPSHOT_FILE = ROOT / "data" / "processed" / "signal_snapshot.json"
DAILY_REPORT_DIR = ROOT / "reports" / "daily"
INTRADAY_DIR = ROOT / "data" / "observations" / "intraday"
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
python -m pytest tests/test_telegram_bot/test_config.py -v
```

Expected: 3 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add telegram_bot/ tests/test_telegram_bot/
git commit -m "feat(telegram): scaffold package structure and config module"
```

---

## Task 3: utils/telegram_notify.py (TDD)

**Files:**
- Create: `utils/telegram_notify.py`
- Create: `tests/test_telegram_bot/test_telegram_notify.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_telegram_bot/test_telegram_notify.py`:

```python
from __future__ import annotations
from unittest.mock import patch, MagicMock


def test_send_notification_silent_when_token_missing(monkeypatch):
    """send_notification() does nothing when TELEGRAM_BOT_TOKEN is unset."""
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    from utils.telegram_notify import send_notification
    send_notification("hello")  # Must not raise


def test_send_notification_silent_when_chat_id_missing(monkeypatch):
    """send_notification() does nothing when TELEGRAM_CHAT_ID is unset."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    from utils.telegram_notify import send_notification
    send_notification("hello")  # Must not raise


def test_send_notification_posts_to_telegram_api(monkeypatch):
    """send_notification() calls the Telegram sendMessage endpoint."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_ctx = MagicMock()
        mock_urlopen.return_value.__enter__ = lambda s: mock_ctx
        mock_urlopen.return_value.__exit__ = MagicMock(return_value=False)
        from utils.telegram_notify import send_notification
        send_notification("test message")
    assert mock_urlopen.called
    req = mock_urlopen.call_args[0][0]
    assert "fake-token" in req.full_url
    assert b"test message" in req.data


def test_send_notification_handles_network_error(monkeypatch):
    """send_notification() swallows exceptions and does not re-raise."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
    with patch("urllib.request.urlopen", side_effect=OSError("network error")):
        from utils.telegram_notify import send_notification
        send_notification("test")  # Must not raise
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_telegram_bot/test_telegram_notify.py -v
```

Expected: `ModuleNotFoundError: No module named 'utils.telegram_notify'`

- [ ] **Step 3: Write utils/telegram_notify.py**

Create `utils/telegram_notify.py`:

```python
from __future__ import annotations
import json
import logging
import os
import urllib.request

log = logging.getLogger(__name__)


def send_notification(text: str) -> None:
    """Post a Markdown message to the owner's Telegram chat. Silent no-op if env vars missing."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        log.warning("Telegram env vars missing — skipping notification")
        return
    try:
        payload = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10):
            pass
    except Exception as exc:
        log.warning("Telegram notification failed: %s", exc)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_telegram_bot/test_telegram_notify.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add utils/telegram_notify.py tests/test_telegram_bot/test_telegram_notify.py
git commit -m "feat(telegram): add standalone send_notification utility"
```

---

## Task 4: adapters/investment_os.py (TDD)

**Files:**
- Create: `telegram_bot/adapters/investment_os.py`
- Create: `tests/test_telegram_bot/test_investment_os_adapter.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_telegram_bot/test_investment_os_adapter.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_telegram_bot/test_investment_os_adapter.py -v
```

Expected: `ModuleNotFoundError: No module named 'telegram_bot.adapters.investment_os'`

- [ ] **Step 3: Write adapters/investment_os.py**

Create `telegram_bot/adapters/investment_os.py`:

```python
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from telegram_bot.config import SNAPSHOT_FILE, DAILY_REPORT_DIR, INTRADAY_DIR

MAX_REPORT_CHARS = 8000
_KEY_SECTIONS = ["## Role-Aware Candidate Summary", "## P1 Entry Audit", "## Human Summary"]


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def load_snapshot() -> dict[str, Any]:
    return _load_json(SNAPSHOT_FILE)


def load_daily_report(date: str | None = None) -> str:
    target = date or _today()
    path = DAILY_REPORT_DIR / f"{target}_daily_report.md"
    if not path.exists():
        files = sorted(DAILY_REPORT_DIR.glob("*_daily_report.md"))
        if not files:
            return ""
        path = files[-1]
    text = path.read_text(encoding="utf-8")
    if len(text) <= MAX_REPORT_CHARS:
        return text
    sections: list[str] = []
    for heading in _KEY_SECTIONS:
        idx = text.find(heading)
        if idx == -1:
            continue
        end = text.find("\n## ", idx + 1)
        sections.append(text[idx:end] if end != -1 else text[idx: idx + 2000])
    return "\n\n".join(sections) if sections else text[:MAX_REPORT_CHARS]


def load_intraday_slots(date: str | None = None) -> list[dict]:
    target = date or _today()
    slot_dir = INTRADAY_DIR / target
    if not slot_dir.exists():
        return []
    slots = []
    for f in sorted(slot_dir.glob("*.json"))[-3:]:
        data = _load_json(f)
        if data:
            slots.append(data)
    return slots


def build_context_summary() -> str:
    snap = load_snapshot()
    report = load_daily_report()
    slots = load_intraday_slots()
    parts: list[str] = []

    ranked = snap.get("ranked", [])[:5]
    if ranked:
        lines = ["*今日候選 Top 5:*"]
        for r in ranked:
            lines.append(f"  {r.get('rank','?')}. {r.get('ticker','')} {r.get('name','')} score={r.get('score','?')} signal={r.get('signal','?')}")
        parts.append("\n".join(lines))

    decisions = snap.get("decisions", [])
    if decisions:
        lines = ["*決策:*"]
        for d in decisions:
            lines.append(f"  {d.get('ticker','')} {d.get('action','')} — {d.get('reason','')}")
        parts.append("\n".join(lines))

    if report:
        parts.append(f"*日報摘要:*\n{report[:3000]}")

    if slots:
        latest = slots[-1]
        cands = latest.get("candidates", [])[:3]
        lines = [f"*最新盤中觀察 ({latest.get('slot','?')}):*"]
        for c in cands:
            lines.append(f"  {c.get('ticker','')} {c.get('name','')} rank={c.get('rank','?')}")
        parts.append("\n".join(lines))

    return "\n\n".join(parts) if parts else "（暫無資料）"
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_telegram_bot/test_investment_os_adapter.py -v
```

Expected: 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add telegram_bot/adapters/investment_os.py tests/test_telegram_bot/test_investment_os_adapter.py
git commit -m "feat(telegram): add investment_os data adapter"
```

---

## Task 5: adapters/claude_client.py (TDD)

**Files:**
- Create: `telegram_bot/adapters/claude_client.py`
- Create: `tests/test_telegram_bot/test_claude_client.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_telegram_bot/test_claude_client.py`:

```python
from __future__ import annotations
from unittest.mock import MagicMock, patch


def test_ask_claude_returns_text_response(monkeypatch):
    """ask_claude() returns the text content from Claude's response."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    fake_response = MagicMock()
    fake_response.content = [MagicMock(text="廣達今日訊號強，可考慮進場。")]
    with patch("anthropic.Anthropic") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.messages.create.return_value = fake_response
        with patch("telegram_bot.adapters.investment_os.build_context_summary", return_value="ctx"):
            from telegram_bot.adapters.claude_client import ask_claude
            result = ask_claude("今天廣達值得進嗎？")
    assert "廣達" in result


def test_ask_claude_returns_error_message_on_api_failure(monkeypatch):
    """ask_claude() returns a user-friendly error string when APIError is raised."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    import anthropic
    with patch("anthropic.Anthropic") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.messages.create.side_effect = anthropic.APIStatusError(
            "server error", response=MagicMock(status_code=500), body={}
        )
        with patch("telegram_bot.adapters.investment_os.build_context_summary", return_value="ctx"):
            from telegram_bot.adapters import claude_client
            import importlib
            importlib.reload(claude_client)
            result = claude_client.ask_claude("test")
    assert "暫時無法回覆" in result
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_telegram_bot/test_claude_client.py -v
```

Expected: `ModuleNotFoundError: No module named 'telegram_bot.adapters.claude_client'`

- [ ] **Step 3: Write adapters/claude_client.py**

Create `telegram_bot/adapters/claude_client.py`:

```python
from __future__ import annotations
import anthropic
from telegram_bot.config import ANTHROPIC_API_KEY
from telegram_bot.adapters.investment_os import build_context_summary

_client: anthropic.Anthropic | None = None

_SYSTEM = (
    "你是 Investment OS 分析助手。Investment OS 是一套台股量化投資自動化系統。"
    "以下是今日最新市場資料，請根據這些資料回答問題。"
    "回答請保持簡潔，使用繁體中文，必要時用條列式呈現。"
)


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def ask_claude(question: str) -> str:
    context = build_context_summary()
    try:
        response = _get_client().messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=f"{_SYSTEM}\n\n---\n{context}\n---",
            messages=[{"role": "user", "content": question}],
        )
        return response.content[0].text
    except anthropic.APIError as exc:
        return f"Claude 暫時無法回覆，請稍後再試。（{exc}）"
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_telegram_bot/test_claude_client.py -v
```

Expected: 2 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add telegram_bot/adapters/claude_client.py tests/test_telegram_bot/test_claude_client.py
git commit -m "feat(telegram): add Claude client adapter with Investment OS context"
```

---

## Task 6: handlers/commands.py (TDD)

**Files:**
- Create: `telegram_bot/handlers/commands.py`
- Create: `tests/test_telegram_bot/test_commands.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_telegram_bot/test_commands.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pip install pytest-asyncio
python -m pytest tests/test_telegram_bot/test_commands.py -v
```

Expected: `ModuleNotFoundError: No module named 'telegram_bot.handlers.commands'`

- [ ] **Step 3: Write handlers/commands.py**

Create `telegram_bot/handlers/commands.py`:

```python
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.adapters import investment_os as ios

ROOT = Path(__file__).resolve().parents[2]

HELP_TEXT = (
    "*Investment OS Bot*\n\n"
    "/status — 今日快照（候選、決策）\n"
    "/watchlist — 明日 watchlist\n"
    "/daily — 觸發 daily\\_run\n"
    "/intraday — 觸發盤中觀察\n"
    "/ask \\[問題\\] — 問 Claude\n"
    "/help — 顯示說明"
)


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"Investment OS Bot 啟動。\n\n{HELP_TEXT}", parse_mode="Markdown")


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    snap = ios.load_snapshot()
    ranked = snap.get("ranked", [])[:5]
    decisions = snap.get("decisions", [])
    if not ranked and not decisions:
        await update.message.reply_text("暫無資料，請先執行 /daily")
        return
    lines = ["*今日快照*\n", "*候選 Top 5:*"]
    for r in ranked:
        lines.append(f"  {r.get('rank','?')}\\. {r.get('ticker','')} {r.get('name','')} score={r.get('score','?')}")
    if decisions:
        lines.append("\n*決策:*")
        for d in decisions:
            lines.append(f"  {d.get('ticker','')} {d.get('action','')} — {d.get('reason','')}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_watchlist(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    snap = ios.load_snapshot()
    watchlist = snap.get("watchlist", [])
    if not watchlist:
        await update.message.reply_text("暫無明日 watchlist 資料")
        return
    lines = ["*明日 Watchlist*\n"]
    for w in watchlist:
        ticker = w.get("ticker", "")
        name = w.get("name") or "—"
        rank = w.get("last_rank", "—")
        lines.append(f"  {ticker} {name} 最後排名={rank}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def _run_job(update: Update, script_name: str, timeout: int) -> None:
    script = ROOT / "jobs" / script_name
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True, text=True, timeout=timeout,
    )
    status = "✅ 完成" if result.returncode == 0 else f"❌ 失敗（exit {result.returncode}）"
    tail = (result.stdout or result.stderr or "")[-500:]
    await update.message.reply_text(
        f"{script_name} {status}\n\n```\n{tail}\n```", parse_mode="Markdown"
    )


async def cmd_daily(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("正在啟動 daily\\_run，完成後推送摘要...", parse_mode="Markdown")
    await _run_job(update, "daily_run.py", timeout=300)


async def cmd_intraday(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("正在啟動盤中觀察...", parse_mode="Markdown")
    await _run_job(update, "intraday_observation.py", timeout=180)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_telegram_bot/test_commands.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add telegram_bot/handlers/commands.py tests/test_telegram_bot/test_commands.py
git commit -m "feat(telegram): add command handlers (status/watchlist/daily/intraday)"
```

---

## Task 7: handlers/ask.py

**Files:**
- Create: `telegram_bot/handlers/ask.py`

No separate test file — the handler is a thin wrapper over `claude_client` (already tested). One integration test included.

- [ ] **Step 1: Write ask.py**

Create `telegram_bot/handlers/ask.py`:

```python
from __future__ import annotations
from telegram import Update
from telegram.ext import ContextTypes
from telegram_bot.adapters.claude_client import ask_claude


async def cmd_ask(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    question = " ".join(ctx.args) if ctx.args else ""
    if not question:
        await update.message.reply_text("用法：/ask \\[你的問題\\]\n例如：/ask 今天 2382 值得進嗎", parse_mode="Markdown")
        return
    await update.message.reply_text("思考中...")
    reply = ask_claude(question)
    await update.message.reply_text(reply)
```

- [ ] **Step 2: Write integration test**

Append to `tests/test_telegram_bot/test_commands.py`:

```python
@pytest.mark.asyncio
async def test_cmd_ask_replies_with_claude_response():
    """cmd_ask() forwards question to Claude and sends the reply."""
    from telegram_bot.handlers.ask import cmd_ask
    with patch("telegram_bot.handlers.ask.ask_claude", return_value="廣達訊號強"):
        update = _make_update()
        ctx = MagicMock()
        ctx.args = ["今天", "2382", "值得進嗎"]
        await cmd_ask(update, ctx)
    replies = [c[0][0] for c in update.message.reply_text.call_args_list]
    assert any("廣達" in r for r in replies)


@pytest.mark.asyncio
async def test_cmd_ask_shows_usage_when_no_args():
    """cmd_ask() shows usage hint when called with no arguments."""
    from telegram_bot.handlers.ask import cmd_ask
    update = _make_update()
    ctx = MagicMock()
    ctx.args = []
    await cmd_ask(update, ctx)
    reply = update.message.reply_text.call_args[0][0]
    assert "用法" in reply
```

- [ ] **Step 3: Run all handler tests**

```bash
python -m pytest tests/test_telegram_bot/test_commands.py -v
```

Expected: 6 tests PASS.

- [ ] **Step 4: Commit**

```bash
git add telegram_bot/handlers/ask.py tests/test_telegram_bot/test_commands.py
git commit -m "feat(telegram): add /ask handler wired to Claude client"
```

---

## Task 8: bot.py (Entry Point + Auth Middleware)

**Files:**
- Create: `telegram_bot/bot.py`

- [ ] **Step 1: Write bot.py**

Create `telegram_bot/bot.py`:

```python
from __future__ import annotations
import logging

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from telegram_bot.config import BOT_TOKEN, get_allowed_chat_ids
from telegram_bot.handlers.ask import cmd_ask
from telegram_bot.handlers.commands import (
    cmd_daily,
    cmd_help,
    cmd_intraday,
    cmd_start,
    cmd_status,
    cmd_watchlist,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger(__name__)


def _auth(handler):
    """Decorator: reject any update not from an allowed chat ID."""
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_chat.id not in get_allowed_chat_ids():
            log.warning("Unauthorized access from chat_id=%s", update.effective_chat.id)
            await update.message.reply_text("Unauthorized.")
            return
        await handler(update, ctx)
    return wrapper


def main() -> None:
    if not BOT_TOKEN:
        raise EnvironmentError("TELEGRAM_BOT_TOKEN is not set")
    if not get_allowed_chat_ids():
        raise EnvironmentError("ALLOWED_CHAT_IDS is not set")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    for name, handler in [
        ("start", cmd_start),
        ("help", cmd_help),
        ("status", cmd_status),
        ("watchlist", cmd_watchlist),
        ("daily", cmd_daily),
        ("intraday", cmd_intraday),
        ("ask", cmd_ask),
    ]:
        app.add_handler(CommandHandler(name, _auth(handler)))

    log.info("Investment OS Telegram Bot started, polling...")
    app.run_polling()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke test (local)**

```bash
cd /home/shimeon/investment_os
source venv/bin/activate
# Load env vars
export $(grep -v '^#' .env | xargs)
python -m telegram_bot.bot
```

Expected: `Investment OS Telegram Bot started, polling...` — no errors. Send `/help` from Telegram to confirm.

- [ ] **Step 3: Commit**

```bash
git add telegram_bot/bot.py
git commit -m "feat(telegram): add bot entry point with auth middleware"
```

---

## Task 9: Integrate send_notification into daily_run.py

**Files:**
- Modify: `jobs/daily_run.py` (lines 13-14 for import, line 498 for call)

- [ ] **Step 1: Add import after line 13 in daily_run.py**

In [jobs/daily_run.py](jobs/daily_run.py#L13), after `from utils.market_calendar import get_market_context, get_latest_full_trading_day`, add:

```python
from utils.telegram_notify import send_notification
```

- [ ] **Step 2: Insert notification call before `return 0` at line 500**

In [jobs/daily_run.py](jobs/daily_run.py#L498), after the line `log("=== Investment OS daily_run done ===")` and before `return 0`, insert:

```python
    top3_lines = []
    for entry in mainline_snap.get("ranked", [])[:3]:
        top3_lines.append(
            f"{entry.get('rank','?')}. {entry.get('ticker','')} {entry.get('name','')} "
            f"score={entry.get('score','?')} signal={entry.get('signal','?')}"
        )
    top3_text = "\n".join(top3_lines) if top3_lines else "（無候選）"
    send_notification(f"*Daily Run 完成* ({today})\n\n*Top 3:*\n{top3_text}")
```

- [ ] **Step 3: Verify import works**

```bash
cd /home/shimeon/investment_os && source venv/bin/activate
python -c "from jobs.daily_run import main; print('import OK')"
```

Expected: `import OK`

- [ ] **Step 4: Commit**

```bash
git add jobs/daily_run.py
git commit -m "feat(telegram): push Telegram notification on daily_run completion"
```

---

## Task 10: Integrate send_notification into intraday_observation.py

**Files:**
- Modify: `jobs/intraday_observation.py` (after line 588)

- [ ] **Step 1: Add import after line 30 in intraday_observation.py**

In [jobs/intraday_observation.py](jobs/intraday_observation.py#L30), after `from utils.market_calendar import is_market_open`, add:

```python
from utils.telegram_notify import send_notification
```

- [ ] **Step 2: Insert notification call after line 588**

In [jobs/intraday_observation.py](jobs/intraday_observation.py#L588), after `obs_path.write_text(json.dumps(obs_data, ensure_ascii=False, indent=2), encoding="utf-8")` (inside the `try` block), add:

```python
        slot_cands = obs_data.get("candidates", [])[:3]
        cand_lines = [
            f"  {c.get('rank','?')}. {c.get('ticker','')} {c.get('name','')} signal={c.get('signal','?')}"
            for c in slot_cands
        ]
        cand_text = "\n".join(cand_lines) if cand_lines else "（無候選）"
        send_notification(f"*盤中觀察完成* ({slot})\n\n*Top 3:*\n{cand_text}")
```

- [ ] **Step 3: Verify import works**

```bash
python -c "from jobs.intraday_observation import main; print('import OK')"
```

Expected: `import OK`

- [ ] **Step 4: Run existing intraday tests**

```bash
python -m pytest tests/test_intraday_us.py -v
```

Expected: all existing tests PASS.

- [ ] **Step 5: Commit**

```bash
git add jobs/intraday_observation.py
git commit -m "feat(telegram): push Telegram notification on intraday slot completion"
```

---

## Task 11: systemd Service + Deployment

**Files:**
- Create: `systemd/investment-os-telegram-bot.service`

- [ ] **Step 1: Write systemd unit file**

Create `systemd/investment-os-telegram-bot.service`:

```ini
[Unit]
Description=Investment OS Telegram Bot
After=network.target

[Service]
Type=simple
User=shimeon
WorkingDirectory=/home/shimeon/investment_os
EnvironmentFile=/home/shimeon/investment_os/.env
ExecStart=/home/shimeon/investment_os/venv/bin/python -m telegram_bot.bot
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

- [ ] **Step 2: Install and enable service**

```bash
sudo cp systemd/investment-os-telegram-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable investment-os-telegram-bot
sudo systemctl start investment-os-telegram-bot
sudo systemctl status investment-os-telegram-bot
```

Expected: `Active: active (running)`

- [ ] **Step 3: Verify bot responds**

Send `/help` from your Telegram account to the bot. Expected: full command list reply.

- [ ] **Step 4: Check journal logs**

```bash
journalctl -u investment-os-telegram-bot -n 50 --no-pager
```

Expected: `Investment OS Telegram Bot started, polling...` in logs, no errors.

- [ ] **Step 5: Commit**

```bash
git add systemd/investment-os-telegram-bot.service
git commit -m "feat(telegram): add systemd service for telegram bot"
```

---

## Task 12: Run Full Test Suite

- [ ] **Step 1: Run all telegram bot tests**

```bash
cd /home/shimeon/investment_os
source venv/bin/activate
python -m pytest tests/test_telegram_bot/ -v
```

Expected: all tests PASS.

- [ ] **Step 2: Run full test suite to check for regressions**

```bash
python -m pytest tests/ -v --ignore=tests/test_telegram_bot/ 2>/dev/null | tail -20
```

Expected: no new failures vs. baseline.

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "feat(telegram): complete Telegram Bot integration for Investment OS"
```
