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
