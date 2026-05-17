"""
Smoke test: Phase 2B — chase risk tiebreaker in top-10 selection.

Verifies that within the same score tier, candidates with lower
chase_risk_score are ranked ahead of those with higher chase_risk_score.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import pandas as pd
from analysis.chase_risk import compute_chase_risk


def make_close_for_ticker(ticker: str, prices: list) -> pd.DataFrame:
    return pd.DataFrame({ticker: prices})


def make_features_for_close(close: pd.DataFrame) -> dict:
    ticker = close.columns[0]
    prices = close[ticker]
    return {
        "ma5":       pd.DataFrame({ticker: prices.rolling(5).mean()}),
        "ma20":      pd.DataFrame({ticker: prices.rolling(20).mean()}),
        "vol_ratio": pd.DataFrame({ticker: pd.Series([1.0] * len(prices))}),
    }


def _simulate_tiebreak_sort(candidates: list, close: pd.DataFrame, features: dict) -> list:
    """Replicate the Phase 2B sort logic from pipeline/main_v1.py."""
    for c in candidates:
        ticker = c.get("ticker", "")
        if ticker in close.columns:
            cr = compute_chase_risk(close, features, ticker)
            c["_pre_chase_risk_score"] = cr["chase_risk_score"]
        else:
            c["_pre_chase_risk_score"] = 0
    candidates.sort(
        key=lambda x: (-x.get("score", 0), x.get("_pre_chase_risk_score", 0))
    )
    return candidates


def test_lower_chase_risk_wins_tie():
    """Same score=2: LOW chase risk should rank ahead of HIGH chase risk."""
    # LOW chase: flat price, no extension
    low_prices = [100.0] * 25
    # HIGH chase: big up day pushing above Boll upper
    high_prices = [100.0] * 24 + [112.0]

    close = pd.DataFrame({"LOW_TICKER": low_prices, "HIGH_TICKER": high_prices})
    features = {
        "ma5":       pd.DataFrame({
            "LOW_TICKER":  pd.Series(low_prices).rolling(5).mean(),
            "HIGH_TICKER": pd.Series(high_prices).rolling(5).mean(),
        }),
        "ma20":      pd.DataFrame({
            "LOW_TICKER":  pd.Series(low_prices).rolling(20).mean(),
            "HIGH_TICKER": pd.Series(high_prices).rolling(20).mean(),
        }),
        "vol_ratio": pd.DataFrame({
            "LOW_TICKER":  pd.Series([1.0] * 25),
            "HIGH_TICKER": pd.Series([1.0] * 24 + [3.5]),
        }),
    }

    candidates = [
        {"ticker": "HIGH_TICKER", "score": 2, "level": "READY", "price": 112.0},
        {"ticker": "LOW_TICKER",  "score": 2, "level": "READY", "price": 100.0},
    ]

    sorted_candidates = _simulate_tiebreak_sort(candidates, close, features)

    assert sorted_candidates[0]["ticker"] == "LOW_TICKER", (
        f"Expected LOW_TICKER first, got {sorted_candidates[0]['ticker']} "
        f"(chase_scores: LOW={sorted_candidates[1]['_pre_chase_risk_score']}, "
        f"HIGH={sorted_candidates[0]['_pre_chase_risk_score']})"
    )


def test_score_takes_priority_over_chase_risk():
    """score=2 LOW chase risk should rank ahead of score=1 LOW chase risk."""
    prices = [100.0] * 25
    close = pd.DataFrame({"SCORE2": prices, "SCORE1": prices})
    features = {
        "ma5":       pd.DataFrame({
            "SCORE2": pd.Series(prices).rolling(5).mean(),
            "SCORE1": pd.Series(prices).rolling(5).mean(),
        }),
        "ma20":      pd.DataFrame({
            "SCORE2": pd.Series(prices).rolling(20).mean(),
            "SCORE1": pd.Series(prices).rolling(20).mean(),
        }),
        "vol_ratio": pd.DataFrame({
            "SCORE2": pd.Series([1.0] * 25),
            "SCORE1": pd.Series([1.0] * 25),
        }),
    }

    candidates = [
        {"ticker": "SCORE1", "score": 1, "level": "EARLY", "price": 100.0},
        {"ticker": "SCORE2", "score": 2, "level": "READY", "price": 100.0},
    ]

    sorted_candidates = _simulate_tiebreak_sort(candidates, close, features)

    assert sorted_candidates[0]["ticker"] == "SCORE2", (
        f"Expected SCORE2 first, got {sorted_candidates[0]['ticker']}"
    )


def test_pre_chase_risk_score_attached():
    """Every candidate should have _pre_chase_risk_score after sort."""
    prices = [100.0] * 25
    close = pd.DataFrame({"T1": prices, "T2": prices})
    features = {
        "ma5":       pd.DataFrame({c: pd.Series(prices).rolling(5).mean() for c in ["T1", "T2"]}),
        "ma20":      pd.DataFrame({c: pd.Series(prices).rolling(20).mean() for c in ["T1", "T2"]}),
        "vol_ratio": pd.DataFrame({c: pd.Series([1.0] * 25) for c in ["T1", "T2"]}),
    }
    candidates = [
        {"ticker": "T1", "score": 2, "level": "READY", "price": 100.0},
        {"ticker": "T2", "score": 1, "level": "EARLY", "price": 100.0},
    ]
    result = _simulate_tiebreak_sort(candidates, close, features)
    for c in result:
        assert "_pre_chase_risk_score" in c, f"Missing _pre_chase_risk_score for {c['ticker']}"
        assert isinstance(c["_pre_chase_risk_score"], (int, float))


def main():
    test_lower_chase_risk_wins_tie()
    test_score_takes_priority_over_chase_risk()
    test_pre_chase_risk_score_attached()
    print("smoke_chase_risk_tiebreak: all tests passed.")


if __name__ == "__main__":
    main()
