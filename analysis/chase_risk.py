import pandas as pd


def compute_chase_risk(close: pd.DataFrame, features: dict, ticker: str) -> dict:
    """
    Compute chase risk for the latest trading day for a given ticker.

    Returns dict with: chase_risk, chase_risk_score, chase_risk_reasons
    """
    if ticker not in close.columns:
        return {"chase_risk": "UNKNOWN", "chase_risk_score": 0, "chase_risk_reasons": ["no_price_data"]}

    prices = close[ticker].dropna()
    if len(prices) < 5:
        return {"chase_risk": "LOW", "chase_risk_score": 0, "chase_risk_reasons": ["insufficient_data"]}

    current_close = float(prices.iloc[-1])

    daily_return = float(prices.pct_change().iloc[-1]) if len(prices) >= 2 else 0.0
    three_d_return = float(prices.pct_change(3).iloc[-1]) if len(prices) >= 4 else 0.0

    ma5 = None
    if "ma5" in features and ticker in features["ma5"].columns:
        _ma5 = features["ma5"][ticker].dropna()
        if not _ma5.empty:
            ma5 = float(_ma5.iloc[-1])

    ma20 = None
    if "ma20" in features and ticker in features["ma20"].columns:
        _ma20 = features["ma20"][ticker].dropna()
        if not _ma20.empty:
            ma20 = float(_ma20.iloc[-1])

    std20 = float(prices.rolling(20).std().iloc[-1]) if len(prices) >= 20 else None
    boll_upper = (ma20 + 2 * std20) if (ma20 and std20) else None

    vol_ratio = 0.0
    if "vol_ratio" in features and ticker in features["vol_ratio"].columns:
        _vr = features["vol_ratio"][ticker].dropna()
        if not _vr.empty:
            vol_ratio = float(_vr.iloc[-1])

    close_vs_ma5 = (current_close / ma5 - 1) if (ma5 and ma5 > 0) else 0.0

    reasons = []
    score = 0
    extreme_hits = 0
    high_hits = 0
    medium_hits = 0

    # EXTREME conditions
    if not pd.isna(daily_return) and daily_return >= 0.09:
        reasons.append(f"daily_return >= 9% ({daily_return:.1%})")
        score += 30
        extreme_hits += 1

    if boll_upper and current_close > boll_upper and close_vs_ma5 >= 0.06:
        reasons.append(f"close > Bollinger upper, close/MA5-1 >= 6% ({close_vs_ma5:.1%})")
        score += 20
        extreme_hits += 1

    if vol_ratio >= 3.0:
        reasons.append(f"vol_ratio >= 3.0 ({vol_ratio:.2f}x)")
        score += 10
        extreme_hits += 1

    # HIGH conditions
    if not pd.isna(daily_return) and 0.07 <= daily_return < 0.09:
        reasons.append(f"daily_return >= 7% ({daily_return:.1%})")
        score += 20
        high_hits += 1

    if boll_upper and current_close > boll_upper and extreme_hits == 0:
        reasons.append("close > Bollinger upper")
        score += 15
        high_hits += 1

    if 0.04 <= close_vs_ma5 < 0.06:
        reasons.append(f"close/MA5-1 >= 4% ({close_vs_ma5:.1%})")
        score += 15
        high_hits += 1

    if not pd.isna(three_d_return) and three_d_return >= 0.10:
        reasons.append(f"3d_return >= 10% ({three_d_return:.1%})")
        score += 15
        high_hits += 1

    if 2.0 <= vol_ratio < 3.0:
        reasons.append(f"vol_ratio >= 2.0 ({vol_ratio:.2f}x)")
        score += 10
        high_hits += 1

    # MEDIUM conditions
    if not pd.isna(daily_return) and 0.04 <= daily_return < 0.07:
        reasons.append(f"daily_return >= 4% ({daily_return:.1%})")
        score += 10
        medium_hits += 1

    if 0.025 <= close_vs_ma5 < 0.04:
        reasons.append(f"close/MA5-1 >= 2.5% ({close_vs_ma5:.1%})")
        score += 10
        medium_hits += 1

    if 1.5 <= vol_ratio < 2.0:
        reasons.append(f"vol_ratio >= 1.5 ({vol_ratio:.2f}x)")
        score += 5
        medium_hits += 1

    if extreme_hits >= 2 or score >= 60:
        chase_risk = "EXTREME"
    elif score >= 35 or high_hits >= 2:
        chase_risk = "HIGH"
    elif score >= 15 or medium_hits >= 2:
        chase_risk = "MEDIUM"
    else:
        chase_risk = "LOW"

    return {
        "chase_risk": chase_risk,
        "chase_risk_score": min(score, 100),
        "chase_risk_reasons": reasons,
    }
