from pathlib import Path
import json

from scanner.universe import get_tw_universe
from scanner.basic_scanner import scan_candidates


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "data" / "candidates_smoke_test.json"


def build_fake_features(universe: list[dict]) -> list[dict]:
    """
    Smoke test only.
    Does not fetch real market data.
    Purpose: verify module flow and output format.
    """
    rows = []

    for item in universe[:10]:
        ticker = item.get("ticker")

        rows.append({
            **item,
            "ticker": ticker,
            "close_above_ma20": True,
            "close_above_ma60": True,
            "volume_ratio": 1.3,
            "breakout_20d": False,
        })

    return rows


def main():
    universe_df = get_tw_universe()
    universe = universe_df.to_dict(orient="records")
    features = build_fake_features(universe)
    candidates = scan_candidates_from_features(features)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(candidates, f, ensure_ascii=False, indent=2)

    print(f"TW universe count: {len(universe)}")
    print(f"Smoke candidates count: {len(candidates)}")
    print(f"Output written to: {OUTPUT_PATH}")

    for row in candidates[:5]:
        print(row.get("ticker"), row.get("scanner_score"), row.get("signal"))


def scan_candidates_from_features(feature_rows: list[dict]) -> list[dict]:
    candidates = []

    for row in feature_rows:
        ticker = row.get("ticker")
        if not ticker:
            continue

        score = 0

        if row.get("close_above_ma20") is True:
            score += 1

        if row.get("close_above_ma60") is True:
            score += 1

        if row.get("volume_ratio", 0) >= 1.2:
            score += 1

        if row.get("breakout_20d") is True:
            score += 2

        signal = "WATCH"
        if score >= 4:
            signal = "ENTRY"
        elif score >= 2:
            signal = "READY"

        candidates.append({
            **row,
            "scanner_score": score,
            "signal": signal,
        })

    return sorted(candidates, key=lambda x: x.get("scanner_score", 0), reverse=True)


if __name__ == "__main__":
    main()
