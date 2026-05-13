import sys
from pathlib import Path
from datetime import date
sys.path.append(str(Path(__file__).resolve().parents[1]))

from data_node.narrative_refresh_builder import (
    detect_themes,
    build_candidate,
    build_narrative_candidates,
)


def test_detect_themes_ai():
    themes = detect_themes(["AI", "伺服器"])
    assert "AI Server" in themes


def test_detect_themes_hbm():
    themes = detect_themes(["HBM", "CoWoS"])
    assert "HBM / Memory" in themes


def test_detect_themes_empty():
    themes = detect_themes([])
    assert themes == []


def test_build_candidate_status():
    news_item = {
        "ticker": "2356.TW",
        "name": "英業達",
        "keywords": ["AI", "AWS", "伺服器"],
        "news_heat_score": 42,
        "freshness": "FRESH",
    }
    result = build_candidate("2356.TW", "英業達", news_item, None)
    assert result["status"] == "CANDIDATE_ONLY"
    assert result["ticker"] == "2356.TW"
    assert len(result["candidate_themes"]) > 0
    assert result["review_flag"] == "NEW_CANDIDATE"


def test_build_candidate_weakened():
    news_item = {
        "ticker": "2330.TW",
        "name": "台積電",
        "keywords": [],
        "news_heat_score": 0,
        "freshness": "MISSING",
    }
    formal = {"ticker": "2330.TW", "consensus_score": 80, "themes": ["Semiconductor"]}
    result = build_candidate("2330.TW", "台積電", news_item, formal)
    assert result["review_flag"] == "NARRATIVE_WEAKENED"


def test_build_narrative_candidates_no_overwrite():
    items = [
        {"ticker": "TEST.TW", "name": "Test", "keywords": ["AI"],
         "news_heat_score": 30, "freshness": "FRESH"},
    ]
    report = build_narrative_candidates(items, {}, {}, run_date=date(2026, 5, 13))
    assert report["note"] == "CANDIDATE_ONLY — do not auto-apply to formal narrative map"
    assert report["total"] == 1
    assert report["candidates"][0]["status"] == "CANDIDATE_ONLY"


def test_evidence_structure():
    news_item = {
        "ticker": "TEST.TW",
        "name": "Test",
        "keywords": ["AI", "HBM", "CoWoS"],
        "news_heat_score": 50,
        "freshness": "FRESH",
    }
    result = build_candidate("TEST.TW", "Test", news_item, None)
    for ev in result["evidence"]:
        assert "source" in ev
        assert "keyword" in ev
        assert "confidence" in ev


def main():
    test_detect_themes_ai()
    test_detect_themes_hbm()
    test_detect_themes_empty()
    test_build_candidate_status()
    test_build_candidate_weakened()
    test_build_narrative_candidates_no_overwrite()
    test_evidence_structure()
    print("smoke_narrative_refresh: all tests passed.")


if __name__ == "__main__":
    main()
