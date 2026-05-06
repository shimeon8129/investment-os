import pandas as pd
import sys
from pathlib import Path


sys.path.append(str(Path(__file__).resolve().parents[1]))

from pipeline.ranking_engine import rank_stocks
from processing.features import compute_features
from scanner.minervini_scanner import (
    build_minervini_map,
    scan_minervini_candidates,
)


def build_price_data():
    dates = pd.date_range("2025-01-01", periods=260, freq="B")

    close = pd.DataFrame({
        "STAGE2.TW": [100 + (idx * 0.35) for idx in range(260)],
        "WEAK.TW": [180 - (idx * 0.20) for idx in range(260)],
    }, index=dates)

    volume = pd.DataFrame({
        "STAGE2.TW": [2_000_000 for _ in range(260)],
        "WEAK.TW": [500_000 for _ in range(260)],
    }, index=dates)

    return close, volume


def main():
    close, volume = build_price_data()
    features = compute_features(close, volume)

    fundamentals = {
        "STAGE2.TW": {
            "revenue_yoy": 35.0,
            "eps_current": 3.2,
            "eps_last_year": 1.8,
        },
        "WEAK.TW": {
            "revenue_yoy": 5.0,
            "eps_current": 0.8,
            "eps_last_year": 1.0,
        },
    }

    results = scan_minervini_candidates(
        close,
        volume,
        features=features,
        fundamentals=fundamentals,
    )
    result_map = build_minervini_map(results)

    strong = result_map["STAGE2.TW"]
    weak = result_map["WEAK.TW"]

    assert strong["passed_minervini_core"] is True
    assert strong["minervini_score"] == 100
    assert weak["passed_minervini_core"] is False
    assert weak["minervini_score"] < strong["minervini_score"]

    ranked = rank_stocks(
        signal_results=[
            {"ticker": "STAGE2.TW", "signal": "BUY", "level": "READY"},
            {"ticker": "WEAK.TW", "signal": "BUY", "level": "READY"},
        ],
        scanner_results={"STAGE2.TW": 2, "WEAK.TW": 2},
        sector_map={"STAGE2.TW": "Equipment", "WEAK.TW": "Equipment"},
        name_map={"STAGE2.TW": "Stage 2 Candidate", "WEAK.TW": "Weak Candidate"},
        minervini_results=result_map,
    )

    assert ranked[0]["ticker"] == "STAGE2.TW"
    assert ranked[0]["passed_minervini_core"] is True

    print("Minervini scanner smoke test passed")
    print("Top ranked:", ranked[0]["ticker"], ranked[0]["score"])


if __name__ == "__main__":
    main()
