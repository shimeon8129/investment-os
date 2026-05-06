import json
import os


DEFAULT_NEWS_HEAT_PATH = "data/narrative_daily/latest.json"


def load_news_heat_map(path=DEFAULT_NEWS_HEAT_PATH):
    if not os.path.exists(path):
        return {}

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {
        row["ticker"]: row
        for row in data.get("items", [])
        if row.get("ticker")
    }
