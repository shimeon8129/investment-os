import sys
from pathlib import Path
from datetime import date
sys.path.append(str(Path(__file__).resolve().parents[1]))

from data_node.chips_fetcher import (
    compute_chip_status,
    compute_chip_freshness,
    build_chip_map,
)


def test_chip_status_strong_positive():
    row = {"foreign_net_buy": 2_000_000, "trust_net_buy": 100_000,
           "dealer_net_buy": 50_000, "institutional_net_buy": 2_150_000}
    assert compute_chip_status(row) == "STRONG_POSITIVE"


def test_chip_status_positive():
    row = {"foreign_net_buy": 500_000, "trust_net_buy": 50_000,
           "dealer_net_buy": 10_000, "institutional_net_buy": 560_000}
    assert compute_chip_status(row) == "POSITIVE"


def test_chip_status_divergence():
    row = {"foreign_net_buy": -300_000, "trust_net_buy": 50_000,
           "dealer_net_buy": 10_000, "institutional_net_buy": -240_000}
    assert compute_chip_status(row) == "DIVERGENCE"


def test_chip_status_strong_divergence():
    row = {"foreign_net_buy": -500_000, "trust_net_buy": -100_000,
           "dealer_net_buy": -50_000, "institutional_net_buy": -650_000}
    assert compute_chip_status(row) == "STRONG_DIVERGENCE"


def test_chip_status_missing():
    row = {"foreign_net_buy": 0, "trust_net_buy": 0,
           "dealer_net_buy": 0, "institutional_net_buy": 0}
    assert compute_chip_status(row) == "MISSING"


def test_chip_status_mixed():
    row = {"foreign_net_buy": 100_000, "trust_net_buy": -50_000,
           "dealer_net_buy": -10_000, "institutional_net_buy": 40_000}
    assert compute_chip_status(row) in ("MIXED", "POSITIVE")


def test_chip_freshness_fresh():
    today = date(2026, 5, 13)
    assert compute_chip_freshness("2026-05-13", today) == "FRESH"
    assert compute_chip_freshness("2026-05-12", today) == "FRESH"


def test_chip_freshness_stale():
    today = date(2026, 5, 13)
    assert compute_chip_freshness("2026-04-29", today) == "STALE"


def test_chip_freshness_missing():
    assert compute_chip_freshness("", None) == "MISSING"
    assert compute_chip_freshness(None, None) == "MISSING"


def test_build_chip_map():
    report = {
        "items": [
            {"code": "2356", "ticker": "2356.TW", "chip_status": "POSITIVE",
             "chip_freshness": "FRESH", "chip_score": 75,
             "institutional_net_buy": 61_726, "foreign_net_buy": 60_647,
             "trust_net_buy": -56, "dealer_net_buy": 1_135,
             "institutional_bias": "BUY"},
        ]
    }
    chip_map = build_chip_map(report)
    assert "2356" in chip_map
    assert chip_map["2356"]["chip_status"] == "POSITIVE"


def main():
    test_chip_status_strong_positive()
    test_chip_status_positive()
    test_chip_status_divergence()
    test_chip_status_strong_divergence()
    test_chip_status_missing()
    test_chip_status_mixed()
    test_chip_freshness_fresh()
    test_chip_freshness_stale()
    test_chip_freshness_missing()
    test_build_chip_map()
    print("smoke_chips_fetcher: all tests passed.")


if __name__ == "__main__":
    main()
