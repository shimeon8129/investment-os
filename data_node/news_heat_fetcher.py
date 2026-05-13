"""
data_node/news_heat_fetcher.py

Daily NewsHeat refresh pipeline — wraps steps/fetch_news_heat.py and adds:
- freshness: FRESH (<=3d) / RECENT (<=7d) / STALE (>7d) / MISSING
- Unified output schema per Build Plan Layer D

Output files:
  data/news/YYYY-MM-DD_news_heat.json
  data/news/latest_news_heat.json
"""

import json
import os
import sys
from datetime import datetime, date, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from steps.fetch_news_heat import (
    fetch_google_news_items,
    score_news_heat,
    build_query,
    load_candidates,
    parse_pub_date,
)

OUTPUT_DIR = "data/news"
LATEST_PATH = os.path.join(OUTPUT_DIR, "latest_news_heat.json")


def compute_freshness(latest_news_date_str: str, run_date: date = None) -> str:
    if not latest_news_date_str:
        return "MISSING"
    try:
        news_date = datetime.strptime(latest_news_date_str[:10], "%Y-%m-%d").date()
        ref = run_date or date.today()
        delta = (ref - news_date).days
        if delta <= 3:
            return "FRESH"
        if delta <= 7:
            return "RECENT"
        return "STALE"
    except ValueError:
        return "MISSING"


def _latest_date_from_articles(articles: list) -> str:
    latest = None
    for a in articles:
        pub = parse_pub_date(a.get("published_at", ""))
        if pub:
            d = pub.astimezone(timezone.utc).strftime("%Y-%m-%d")
            if latest is None or d > latest:
                latest = d
    return latest or ""


def fetch_ticker_news(name: str, ticker: str, days: int = 7) -> dict:
    try:
        query = build_query(name, days=days)
        articles = fetch_google_news_items(query, timeout=10)
    except Exception as e:
        return {
            "ticker": ticker,
            "name": name,
            "news_count_3d": 0,
            "source_count_3d": 0,
            "latest_news_date": "",
            "news_heat_score": 0,
            "freshness": "MISSING",
            "keywords": [],
            "top_headlines": [],
            "error": str(e),
        }

    scored = score_news_heat(articles)
    latest_date = _latest_date_from_articles(articles)
    freshness = compute_freshness(latest_date)

    headlines = [
        {"title": a.get("title", ""), "source": a.get("source", ""), "published_at": a.get("published_at", "")}
        for a in articles[:3]
    ]

    return {
        "ticker": ticker,
        "name": name,
        "news_count_3d": scored.get("news_count", 0),
        "source_count_3d": scored.get("source_count", 0),
        "latest_news_date": latest_date,
        "news_heat_score": scored.get("heat_score", 0),
        "freshness": freshness,
        "keywords": scored.get("theme_hits", []),
        "top_headlines": headlines,
    }


def fetch_and_build(tickers: list, name_map: dict, days: int = 7, run_date: date = None) -> dict:
    today_str = (run_date or date.today()).strftime("%Y-%m-%d")
    items = []
    for ticker in tickers:
        name = name_map.get(ticker, ticker)
        print(f"  Fetching news: {ticker} {name}")
        item = fetch_ticker_news(name, ticker, days=days)
        items.append(item)

    return {
        "generated_at": today_str,
        "days_lookback": days,
        "total": len(items),
        "items": items,
    }


def save(report: dict):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    dated_path = os.path.join(OUTPUT_DIR, f"{report['generated_at']}_news_heat.json")
    for path in [dated_path, LATEST_PATH]:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"NewsHeat saved: {dated_path}")
    print(f"NewsHeat saved: {LATEST_PATH}")


def load_latest() -> dict:
    if not os.path.exists(LATEST_PATH):
        return {}
    with open(LATEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def build_news_heat_map(report: dict) -> dict:
    """Return {ticker: item} for quick lookup."""
    return {item["ticker"]: item for item in report.get("items", [])}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--date", default=None)
    args = parser.parse_args()

    run_date = datetime.strptime(args.date, "%Y-%m-%d").date() if args.date else None

    try:
        candidates = load_candidates()
    except FileNotFoundError:
        print("data/candidates.json not found — using empty list")
        candidates = []

    import pandas as pd
    try:
        df = pd.read_csv("data/universe_tw.csv")
        name_map = dict(zip(df["ticker"], df["name"]))
    except Exception:
        name_map = {}

    tickers = [c.get("ticker", "") for c in candidates[:20]]
    print(f"Fetching NewsHeat for {len(tickers)} tickers (days={args.days})...")
    report = fetch_and_build(tickers, name_map, days=args.days, run_date=run_date)
    save(report)

    print(f"\nTotal: {report['total']} tickers")
    print("\nTop 5 by heat score:")
    sorted_items = sorted(report["items"], key=lambda x: x["news_heat_score"], reverse=True)
    for item in sorted_items[:5]:
        print(
            f"  {item['ticker']} {item['name']} | "
            f"score={item['news_heat_score']} | "
            f"freshness={item['freshness']} | "
            f"count={item['news_count_3d']} | "
            f"keywords={item['keywords'][:3]}"
        )


if __name__ == "__main__":
    main()
