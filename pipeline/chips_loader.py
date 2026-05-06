import json
import os


DEFAULT_CHIPS_PATH = "data/chips/latest.json"


def load_chips_map(path=DEFAULT_CHIPS_PATH):
    if not os.path.exists(path):
        return {}

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {
        row["ticker"]: row
        for row in data.get("items", [])
        if row.get("ticker")
    }
