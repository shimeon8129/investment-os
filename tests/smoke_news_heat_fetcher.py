import sys
from pathlib import Path
from datetime import date
sys.path.append(str(Path(__file__).resolve().parents[1]))

from data_node.news_heat_fetcher import (
    compute_freshness,
    build_news_heat_map,
)


def test_freshness_fresh():
    today = date(2026, 5, 13)
    assert compute_freshness("2026-05-13", today) == "FRESH"
    assert compute_freshness("2026-05-11", today) == "FRESH"


def test_freshness_recent():
    today = date(2026, 5, 13)
    assert compute_freshness("2026-05-07", today) == "RECENT"


def test_freshness_stale():
    today = date(2026, 5, 13)
    assert compute_freshness("2026-04-29", today) == "STALE"


def test_freshness_missing():
    assert compute_freshness("", None) == "MISSING"
    assert compute_freshness(None, None) == "MISSING"


def test_build_news_heat_map():
    report = {
        "items": [
            {
                "ticker": "2356.TW",
                "name": "英業達",
                "news_count_3d": 5,
                "source_count_3d": 3,
                "latest_news_date": "2026-05-13",
                "news_heat_score": 42,
                "freshness": "FRESH",
                "keywords": ["AI", "AWS"],
                "top_headlines": [],
            }
        ]
    }
    news_map = build_news_heat_map(report)
    assert "2356.TW" in news_map
    assert news_map["2356.TW"]["freshness"] == "FRESH"
    assert news_map["2356.TW"]["news_heat_score"] == 42
    assert "AI" in news_map["2356.TW"]["keywords"]


def test_output_schema():
    report = {
        "items": [
            {
                "ticker": "TEST",
                "name": "Test Co",
                "news_count_3d": 0,
                "source_count_3d": 0,
                "latest_news_date": "",
                "news_heat_score": 0,
                "freshness": "MISSING",
                "keywords": [],
                "top_headlines": [],
            }
        ]
    }
    item = report["items"][0]
    for field in ("ticker", "name", "news_count_3d", "source_count_3d",
                  "latest_news_date", "news_heat_score", "freshness",
                  "keywords", "top_headlines"):
        assert field in item, f"missing field: {field}"


def main():
    test_freshness_fresh()
    test_freshness_recent()
    test_freshness_stale()
    test_freshness_missing()
    test_build_news_heat_map()
    test_output_schema()
    print("smoke_news_heat_fetcher: all tests passed.")


if __name__ == "__main__":
    main()
