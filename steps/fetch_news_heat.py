import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

import pandas as pd


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


OUTPUT_DIR = "data/narrative_daily"
LATEST_PATH = os.path.join(OUTPUT_DIR, "latest.json")

GOOGLE_NEWS_RSS_URL = (
    "https://news.google.com/rss/search?"
    "q={query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
)

KEYWORD_WEIGHTS = {
    "AI": 8,
    "人工智慧": 8,
    "半導體": 7,
    "先進封裝": 8,
    "CoWoS": 10,
    "HBM": 10,
    "伺服器": 6,
    "營收": 6,
    "訂單": 6,
    "法人": 5,
    "外資": 5,
    "買超": 5,
    "擴產": 6,
    "漲價": 6,
}


def load_candidates(path="data/candidates.json") -> list[dict]:
    if not os.path.exists(path):
        raise FileNotFoundError("data/candidates.json not found. Run scanner first.")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_name_map(path="data/universe_tw.csv") -> dict:
    df = pd.read_csv(path)
    return dict(zip(df["ticker"], df["name"]))


def build_query(name: str, days: int = 1) -> str:
    keywords = "AI 半導體 法人 營收 訂單"
    return f'"{name}" {keywords} when:{days}d'


def fetch_google_news_items(query: str, timeout: int = 12) -> list[dict]:
    url = GOOGLE_NEWS_RSS_URL.format(query=quote_plus(query))
    req = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            )
        },
    )

    with urlopen(req, timeout=timeout) as response:
        xml_text = response.read()

    root = ET.fromstring(xml_text)
    items = []

    for item in root.findall("./channel/item"):
        title = unescape(item.findtext("title", default="")).strip()
        link = item.findtext("link", default="").strip()
        pub_date = item.findtext("pubDate", default="").strip()
        source_node = item.find("source")
        source = source_node.text.strip() if source_node is not None and source_node.text else ""

        if not title:
            continue

        items.append({
            "title": title,
            "url": link,
            "source": source,
            "published_at": pub_date,
        })

    return items


def parse_pub_date(value: str):
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except Exception:
        return None


def keyword_hits(text: str) -> list[str]:
    return [
        keyword
        for keyword in KEYWORD_WEIGHTS
        if keyword.lower() in text.lower()
    ]


def score_news_heat(articles: list[dict], now=None) -> dict:
    now = now or datetime.now(timezone.utc)

    sources = Counter()
    all_hits = []
    latest_age_hours = None

    for article in articles:
        source = article.get("source") or "UNKNOWN"
        sources[source] += 1

        text = f"{article.get('title', '')} {article.get('summary', '')}"
        all_hits.extend(keyword_hits(text))

        published = parse_pub_date(article.get("published_at", ""))
        if published:
            age_hours = max((now - published.astimezone(timezone.utc)).total_seconds() / 3600, 0)
            latest_age_hours = age_hours if latest_age_hours is None else min(latest_age_hours, age_hours)

    news_count = len(articles)
    source_count = len(sources)
    unique_hits = sorted(set(all_hits))

    news_count_score = min(news_count * 8, 40)
    source_diversity_score = min(source_count * 8, 24)
    keyword_score = min(sum(KEYWORD_WEIGHTS[k] for k in unique_hits), 24)

    if latest_age_hours is None:
        recency_score = 0
    elif latest_age_hours <= 6:
        recency_score = 12
    elif latest_age_hours <= 24:
        recency_score = 8
    else:
        recency_score = 3

    heat_score = min(
        news_count_score
        + source_diversity_score
        + keyword_score
        + recency_score,
        100,
    )

    return {
        "news_count": news_count,
        "source_count": source_count,
        "theme_hits": unique_hits,
        "heat_score": heat_score,
        "score_parts": {
            "news_count_score": news_count_score,
            "source_diversity_score": source_diversity_score,
            "keyword_score": keyword_score,
            "recency_score": recency_score,
        },
    }


def summarize_articles(articles: list[dict], limit: int = 5) -> list[dict]:
    return [
        {
            "title": article.get("title", ""),
            "source": article.get("source", ""),
            "published_at": article.get("published_at", ""),
            "url": article.get("url", ""),
        }
        for article in articles[:limit]
    ]


def build_daily_news_heat(candidates: list[dict], days: int = 1, limit: int | None = None) -> dict:
    name_map = load_name_map()
    selected = candidates[:limit] if limit else candidates
    rows = []

    for candidate in selected:
        ticker = candidate.get("ticker")
        name = name_map.get(ticker, candidate.get("name", ticker))
        query = build_query(name, days=days)

        print(f"📰 {ticker} {name} | query={query}")

        try:
            articles = fetch_google_news_items(query)
        except Exception as exc:
            print(f"  ❌ news fetch failed: {exc}")
            articles = []

        score = score_news_heat(articles)
        rows.append({
            "ticker": ticker,
            "name": name,
            "query": query,
            **score,
            "articles": summarize_articles(articles),
        })

        print(
            f"  heat={score['heat_score']} "
            f"news={score['news_count']} sources={score['source_count']} "
            f"themes={','.join(score['theme_hits']) or '-'}"
        )

    rows.sort(key=lambda row: row["heat_score"], reverse=True)

    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "source": "google_news_rss",
        "lookback_days": days,
        "items": rows,
    }


def save_report(report: dict):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    dated_path = os.path.join(OUTPUT_DIR, f"{report['date']}.json")

    for path in [dated_path, LATEST_PATH]:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"✅ saved: {LATEST_PATH}")
    print(f"✅ saved: {dated_path}")


def main():
    limit = None
    if len(sys.argv) > 1:
        limit = int(sys.argv[1])

    candidates = load_candidates()
    report = build_daily_news_heat(candidates, days=1, limit=limit)
    save_report(report)


if __name__ == "__main__":
    main()
