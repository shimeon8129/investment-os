"""
data_node/narrative_refresh_builder.py

Narrative Refresh Candidate Builder — generates candidate narratives from
news heat data WITHOUT overwriting the formal narrative map.

Output files:
  data/narrative/YYYY-MM-DD_narrative_candidates.json
  reports/validation/YYYY-MM-DD_narrative_refresh.md

Rules:
- NEVER automatically overwrite data/final_narrative.json
- Generate candidate narratives only (status: CANDIDATE_ONLY)
- Report newly detected, weakened, and owner-review-required links
"""

import json
import os
import sys
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

NARRATIVE_DIR = "data/narrative"
VALIDATION_DIR = "reports/validation"
FORMAL_NARRATIVE_PATH = "data/final_narrative.json"

THEME_KEYWORDS = {
    "AI Server":      ["AI", "伺服器", "server", "GB200", "TPU", "Blackwell"],
    "AWS Supply Chain": ["AWS", "Amazon", "雲端", "cloud", "資料中心"],
    "HBM / Memory":   ["HBM", "記憶體", "DRAM", "CoWoS", "先進封裝"],
    "Semiconductor":  ["半導體", "晶圓", "晶片", "fab", "TSMC", "台積電"],
    "PCB / Substrate": ["PCB", "基板", "substrate", "ABF", "載板"],
    "Power":          ["電源", "power", "散熱", "cooling", "VR"],
}


def detect_themes(keywords: list) -> list:
    matched = []
    kw_lower = [k.lower() for k in keywords]
    for theme, theme_kws in THEME_KEYWORDS.items():
        for tkw in theme_kws:
            if tkw.lower() in kw_lower or any(tkw.lower() in k for k in kw_lower):
                matched.append(theme)
                break
    return matched


def build_candidate(ticker: str, name: str, news_item: dict, formal_item: dict) -> dict:
    keywords = news_item.get("keywords", [])
    candidate_themes = detect_themes(keywords)

    evidence = []
    for kw in keywords[:5]:
        evidence.append({
            "source": "news_heat",
            "keyword": kw,
            "confidence": "MEDIUM" if len(keywords) >= 3 else "LOW",
        })

    current_score = formal_item.get("consensus_score", 0) if formal_item else 0
    news_score = news_item.get("news_heat_score", 0)
    suggested_score = round(min(max(current_score * 0.7 + news_score * 0.3, 0), 100), 1)

    review_flag = None
    if formal_item and candidate_themes and not set(candidate_themes) & set(formal_item.get("themes", [])):
        review_flag = "NEW_THEME_DETECTED"
    elif formal_item and not candidate_themes and formal_item.get("consensus_score", 0) > 50:
        review_flag = "NARRATIVE_WEAKENED"
    elif not formal_item and candidate_themes:
        review_flag = "NEW_CANDIDATE"

    return {
        "ticker": ticker,
        "name": name,
        "candidate_themes": candidate_themes,
        "evidence": evidence,
        "news_heat_score": news_score,
        "freshness": news_item.get("freshness", "MISSING"),
        "current_narrative_score": current_score,
        "suggested_narrative_score": suggested_score,
        "review_flag": review_flag,
        "status": "CANDIDATE_ONLY",
    }


def build_narrative_candidates(
    news_heat_items: list,
    name_map: dict,
    formal_narrative_map: dict,
    run_date: date = None,
) -> dict:
    today_str = (run_date or date.today()).strftime("%Y-%m-%d")
    candidates = []

    for item in news_heat_items:
        ticker = item.get("ticker", "")
        name = item.get("name", name_map.get(ticker, ticker))
        formal_item = formal_narrative_map.get(ticker)

        candidate = build_candidate(ticker, name, item, formal_item)
        candidates.append(candidate)

    newly_detected = [c for c in candidates if c["review_flag"] == "NEW_CANDIDATE"]
    weakened = [c for c in candidates if c["review_flag"] == "NARRATIVE_WEAKENED"]
    new_theme = [c for c in candidates if c["review_flag"] == "NEW_THEME_DETECTED"]

    return {
        "generated_at": today_str,
        "note": "CANDIDATE_ONLY — do not auto-apply to formal narrative map",
        "total": len(candidates),
        "newly_detected": len(newly_detected),
        "weakened": len(weakened),
        "new_theme": len(new_theme),
        "candidates": candidates,
    }


def save_candidates(report: dict):
    os.makedirs(NARRATIVE_DIR, exist_ok=True)
    dated_path = os.path.join(NARRATIVE_DIR, f"{report['generated_at']}_narrative_candidates.json")
    with open(dated_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Narrative candidates saved: {dated_path}")
    return dated_path


def save_validation_report(report: dict) -> str:
    os.makedirs(VALIDATION_DIR, exist_ok=True)
    dated_path = os.path.join(VALIDATION_DIR, f"{report['generated_at']}_narrative_refresh.md")

    lines = [
        f"# Narrative Refresh Candidates — {report['generated_at']}",
        "",
        "> CANDIDATE_ONLY: Do not auto-apply to formal narrative map (data/final_narrative.json).",
        "",
        f"- Total candidates: {report['total']}",
        f"- Newly detected: {report['newly_detected']}",
        f"- Narrative weakened: {report['weakened']}",
        f"- New theme detected: {report['new_theme']}",
        "",
        "## Candidates Requiring Owner Review",
        "",
    ]

    review_candidates = [c for c in report["candidates"] if c.get("review_flag")]
    if review_candidates:
        lines += [
            "| Ticker | Name | Flag | Themes | Suggested Score | Freshness |",
            "|--------|------|------|--------|----------------|-----------|",
        ]
        for c in review_candidates:
            lines.append(
                f"| {c['ticker']} | {c['name']} | {c['review_flag']} "
                f"| {', '.join(c['candidate_themes']) or '—'} "
                f"| {c['suggested_narrative_score']} "
                f"| {c['freshness']} |"
            )
    else:
        lines.append("No items requiring review.")

    lines += ["", "## All Candidates", ""]
    for c in report["candidates"]:
        lines.append(
            f"- **{c['ticker']} {c['name']}** | themes: {c['candidate_themes']} "
            f"| news_heat={c['news_heat_score']} | suggested_score={c['suggested_narrative_score']}"
        )

    with open(dated_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Narrative refresh report saved: {dated_path}")
    return dated_path


def main():
    from data_node.news_heat_fetcher import load_latest as load_latest_news
    from pipeline.narrative_loader import load_narrative_map
    import pandas as pd

    news_report = load_latest_news()
    if not news_report:
        print("No latest_news_heat.json found. Run data_node/news_heat_fetcher.py first.")
        return

    try:
        df = pd.read_csv("data/universe_tw.csv")
        name_map = dict(zip(df["ticker"], df["name"]))
    except Exception:
        name_map = {}

    formal_map = load_narrative_map()
    report = build_narrative_candidates(
        news_report.get("items", []),
        name_map,
        formal_map,
    )
    save_candidates(report)
    save_validation_report(report)

    print(f"\nCandidates: {report['total']}")
    print(f"New: {report['newly_detected']} | Weakened: {report['weakened']} | New theme: {report['new_theme']}")


if __name__ == "__main__":
    main()
