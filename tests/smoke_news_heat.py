import sys
from pathlib import Path


sys.path.append(str(Path(__file__).resolve().parents[1]))

from pipeline.ranking_engine import rank_stocks
from steps.fetch_news_heat import score_news_heat


def main():
    articles = [
        {
            "title": "台積電 CoWoS 擴產 AI 伺服器需求強",
            "source": "MoneyDJ",
            "published_at": "Wed, 29 Apr 2026 02:00:00 GMT",
        },
        {
            "title": "法人看好半導體與 HBM 訂單",
            "source": "鉅亨網",
            "published_at": "Wed, 29 Apr 2026 03:00:00 GMT",
        },
    ]

    score = score_news_heat(articles)

    assert score["news_count"] == 2
    assert score["source_count"] == 2
    assert score["heat_score"] > 0
    assert "AI" in score["theme_hits"]
    assert "CoWoS" in score["theme_hits"]

    ranked = rank_stocks(
        signal_results=[
            {"ticker": "HOT.TW", "signal": "BUY", "level": "READY"},
            {"ticker": "COLD.TW", "signal": "BUY", "level": "READY"},
        ],
        scanner_results={"HOT.TW": 2, "COLD.TW": 2},
        sector_map={"HOT.TW": "Equipment", "COLD.TW": "Equipment"},
        name_map={"HOT.TW": "Hot News", "COLD.TW": "Cold News"},
        news_heat_results={
            "HOT.TW": {
                "heat_score": 100,
                "news_count": 8,
                "source_count": 4,
            }
        },
    )

    assert ranked[0]["ticker"] == "HOT.TW"
    assert ranked[0]["news_heat_bonus"] == 20

    print("News heat smoke test passed")
    print("Heat score:", score["heat_score"])


if __name__ == "__main__":
    main()
