# Telegram Bot for Investment OS — Design Spec
Date: 2026-05-12

## Overview

A modular Telegram Bot that serves as the primary mobile interface to Investment OS. It provides three capabilities: push notifications from jobs, on-demand command queries, and a conversational Claude assistant with full Investment OS context.

## Goals

- Single user (owner) access via Chat ID whitelist
- Push notifications when daily_run and intraday_observation complete
- Commands to query current state and trigger job execution
- `/ask` command that routes free-form questions to Claude with live Investment OS data as context
- Runs on the same server as Investment OS (`100.92.154.55`) as a systemd service

## Out of Scope

- Multi-user / team access
- Modifying portfolio decisions, holdings, or trade log via Telegram
- Web UI / webhook mode (polling is sufficient for single user)

---

## Directory Structure

```
investment_os/
├── telegram_bot/
│   ├── __init__.py
│   ├── bot.py                  # Entry point: Application setup, polling, auth middleware
│   ├── config.py               # Env var loader (BOT_TOKEN, ANTHROPIC_API_KEY, ALLOWED_CHAT_IDS)
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── investment_os.py    # Reads snapshot / daily report / intraday slots → structured summary
│   │   └── claude_client.py    # Builds prompt with context, calls Anthropic API
│   └── handlers/
│       ├── __init__.py
│       ├── commands.py         # /start /help /status /watchlist /daily /intraday
│       └── ask.py              # /ask [question] handler
└── utils/
    └── telegram_notify.py      # Standalone send_notification() used by jobs
```

---

## Module Responsibilities

| Module | Responsibility |
|--------|----------------|
| `bot.py` | Start polling, register handlers, enforce Chat ID whitelist on every update |
| `config.py` | Load `.env` secrets; expose typed constants |
| `adapters/investment_os.py` | Read Investment OS data files; return structured dict for display and Claude context |
| `adapters/claude_client.py` | Build system prompt + context string; call `claude-sonnet-4-6`; return reply text |
| `handlers/commands.py` | One async function per command; format output as Markdown for Telegram |
| `handlers/ask.py` | Accept free-text after `/ask`, pass to claude_client, stream or return reply |
| `utils/telegram_notify.py` | Single `send_notification(text)` function; pure HTTP, no bot framework dependency |

---

## Commands

| Command | Description | Data Source |
|---------|-------------|-------------|
| `/start` | Welcome message + command list | — |
| `/help` | Command descriptions | — |
| `/status` | Today's snapshot: top candidates, decisions, holdings summary | `data/processed/signal_snapshot.json` |
| `/watchlist` | Tomorrow's watchlist | `signal_snapshot.json` → watchlist section |
| `/daily` | Trigger `daily_run.py` async; reply "Starting…"; push summary when done | subprocess |
| `/intraday` | Trigger `intraday_observation.py` async | subprocess |
| `/ask [question]` | Free-form question answered by Claude with full context | snapshot + daily report + intraday slots |

---

## Push Notification Integration

`utils/telegram_notify.py` exposes:

```python
def send_notification(text: str) -> None:
    """Post a message to the owner's Telegram chat. Silent no-op if env vars missing."""
```

Integration points in existing jobs:
- `jobs/daily_run.py` — call `send_notification(human_summary)` at the end of `main()`
- `jobs/intraday_observation.py` — call `send_notification(slot_summary)` after each slot completes

The function reads `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` from environment. If either is missing it logs a warning and returns without raising, so existing job behaviour is unaffected.

---

## /ask Context Building

```
User: /ask 今天 2382 值得進嗎？

investment_os adapter reads:
  1. data/processed/signal_snapshot.json       → top candidates, decisions, holdings
  2. reports/daily/YYYY-MM-DD_daily_report.md  → full daily report (truncated to key sections)
  3. data/observations/intraday/YYYY-MM-DD/*.json → latest slot observations

claude_client builds:
  system: "你是 Investment OS 分析助手。以下是今日市場資料，請根據資料回答問題。"
  context: [structured summary ≤ 4000 tokens]
  user: "今天 2382 值得進嗎？"

Claude (claude-sonnet-4-6) replies → sent back via Telegram
```

**Token budget protection:** If the daily report exceeds the budget, only extract sections matching `## Role-Aware Candidate Summary` and `## P1 Entry Audit`. Intraday slots: only the most recent slot per date.

---

## Security

- `ALLOWED_CHAT_IDS` env var: comma-separated integer chat IDs
- Auth check applied as a decorator/wrapper on every handler before any logic runs
- Unauthorized messages receive "Unauthorized." and are dropped silently in logs

```python
ALLOWED_CHAT_IDS = {int(x) for x in os.getenv("ALLOWED_CHAT_IDS", "").split(",") if x}
```

---

## Deployment

**Dependencies** (add to existing venv):
```bash
pip install python-telegram-bot anthropic
```

**Environment file** `/home/shimeon/investment_os/.env`:
```
TELEGRAM_BOT_TOKEN=<from BotFather>
TELEGRAM_CHAT_ID=<your numeric chat ID>
ALLOWED_CHAT_IDS=<same chat ID>
ANTHROPIC_API_KEY=<from console.anthropic.com>
```

**systemd service** `systemd/investment-os-telegram-bot.service`:
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

[Install]
WantedBy=multi-user.target
```

---

## Error Handling

- `/daily` and `/intraday` run as subprocesses; stdout/stderr captured to log file; Bot replies with exit code summary
- Claude API errors: catch `anthropic.APIError`, reply "Claude 暫時無法回覆，請稍後再試"
- File read errors in adapter: return partial data with a warning note in the reply
- Bot polling errors: `python-telegram-bot` handles reconnect automatically with `Restart=always` as backstop
