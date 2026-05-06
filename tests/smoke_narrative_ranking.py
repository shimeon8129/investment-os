import sys
from pathlib import Path


sys.path.append(str(Path(__file__).resolve().parents[1]))

from pipeline.ranking_engine import rank_stocks


def main():
    signal_results = [
        {"ticker": "NARR.TW", "signal": "BUY", "level": "READY"},
        {"ticker": "PLAIN.TW", "signal": "BUY", "level": "READY"},
    ]

    scanner_results = {
        "NARR.TW": 2,
        "PLAIN.TW": 2,
    }

    sector_map = {
        "NARR.TW": "Equipment",
        "PLAIN.TW": "Equipment",
    }

    name_map = {
        "NARR.TW": "Narrative Strong",
        "PLAIN.TW": "Plain Candidate",
    }

    minervini_map = {
        "NARR.TW": {"minervini_score": 80, "passed_minervini_core": False},
        "PLAIN.TW": {"minervini_score": 80, "passed_minervini_core": False},
    }

    narrative_map = {
        "NARR.TW": {
            "consensus_score": 95,
            "consensus_count": 3,
            "strength": "STRONG",
        }
    }

    ranked = rank_stocks(
        signal_results,
        scanner_results,
        sector_map,
        name_map,
        minervini_map,
        narrative_map,
    )

    assert ranked[0]["ticker"] == "NARR.TW"
    assert ranked[0]["narrative_strength"] == "STRONG"
    assert ranked[0]["narrative_bonus"] == 39.0
    assert ranked[1]["narrative_strength"] == "NONE"

    print("Narrative ranking smoke test passed")
    print("Top ranked:", ranked[0]["ticker"], ranked[0]["score"])


if __name__ == "__main__":
    main()
