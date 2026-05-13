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
MAINLINE_SNAPSHOT_FILE = ROOT / "data" / "processed" / "mainline_snapshot.json"
DAILY_REPORT_DIR = ROOT / "reports" / "daily"
INTRADAY_DIR = ROOT / "data" / "observations" / "intraday"
