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
