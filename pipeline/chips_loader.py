import json
import os


_PATHS = [
    "data/chips/latest_chips.json",  # new format (chips_fetcher.py)
    "data/chips/latest.json",        # legacy format (steps/fetch_chips.py)
]


def load_chips_map(path=None):
    candidates = [path] + _PATHS if path else _PATHS

    data = {}
    for p in candidates:
        if p and os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            break

    if not data:
        return {}

    chip_map = {}
    for row in data.get("items", []):
        ticker = row.get("ticker", "")
        code = row.get("code", ticker.split(".")[0] if ticker else "")
        if ticker:
            chip_map[ticker] = row
        if code:
            chip_map[code] = row

    return chip_map
