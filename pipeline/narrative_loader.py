# pipeline/narrative_loader.py

import json
import os


DEFAULT_NARRATIVE_PATH = "data/final_narrative.json"


def load_narrative_map(path=DEFAULT_NARRATIVE_PATH):
    if not os.path.exists(path):
        return {}

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    narrative_map = {}

    for row in data:
        ticker = row.get("ticker")
        if not ticker:
            continue
        narrative_map[ticker] = row

    return narrative_map
