from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

_CALENDAR_PATH = Path(__file__).resolve().parents[1] / "config" / "market_calendar.json"

_STATUS_OPEN = "OPEN"
_STATUS_EARLY_CLOSE = "OPEN_EARLY_CLOSE"
_STATUS_WEEKEND = "CLOSED_WEEKEND"
_STATUS_HOLIDAY = "CLOSED_HOLIDAY"


def load_calendar() -> dict:
    return json.loads(_CALENDAR_PATH.read_text(encoding="utf-8"))


def is_weekend(d: date) -> bool:
    return d.weekday() >= 5


def is_market_open(market: str, d: date | None = None) -> str:
    """Return status string for the given market and date."""
    if d is None:
        d = datetime.now().date()
    if isinstance(d, datetime):
        d = d.date()

    if is_weekend(d):
        return _STATUS_WEEKEND

    cal = load_calendar()
    market_cfg = cal.get(market, {})
    iso = d.isoformat()

    if iso in market_cfg.get("holidays", []):
        return _STATUS_HOLIDAY

    if iso in market_cfg.get("early_closes", {}):
        return _STATUS_EARLY_CLOSE

    return _STATUS_OPEN


def get_market_context(d: date | None = None) -> dict:
    """Return a dict with open/closed status for all configured markets."""
    if d is None:
        d = datetime.now().date()
    if isinstance(d, datetime):
        d = d.date()

    cal = load_calendar()
    markets = {}
    for market in cal:
        status = is_market_open(market, d)
        markets[market] = {
            "status": status,
            "is_open": status in (_STATUS_OPEN, _STATUS_EARLY_CLOSE),
        }

    return {
        "date": d.isoformat(),
        "weekend": is_weekend(d),
        "markets": markets,
    }
