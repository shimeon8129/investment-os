# scanner/minervini_scanner.py

from processing.features import compute_features


DEFAULT_LIQUIDITY_THRESHOLD = 1_500_000


def _latest(frame, ticker):
    if frame is None or ticker not in frame.columns:
        return None

    series = frame[ticker].dropna()
    if series.empty:
        return None

    return series.iloc[-1]


def _fundamental_value(fundamentals, ticker, key):
    if fundamentals is None:
        return None

    if hasattr(fundamentals, "loc"):
        if ticker not in fundamentals.index or key not in fundamentals.columns:
            return None
        value = fundamentals.loc[ticker, key]
        return None if value != value else value

    row = fundamentals.get(ticker, {})
    if not isinstance(row, dict):
        return None

    return row.get(key)


def scan_minervini_candidates(
    close,
    volume,
    features=None,
    fundamentals=None,
    liquidity_threshold=DEFAULT_LIQUIDITY_THRESHOLD,
):
    """
    Mark Minervini-style Stage 2 scanner.

    fundamentals is optional. When absent, the scanner still scores the
    technical/liquidity template and marks fundamental checks as unknown.
    Expected keys per ticker:
    - revenue_yoy
    - eps_current
    - eps_last_year
    """
    if features is None:
        features = compute_features(close, volume)

    results = []

    for ticker in close.columns:
        latest_close = _latest(close, ticker)
        latest_volume = _latest(volume, ticker)
        ma50 = _latest(features.get("ma50"), ticker)
        ma150 = _latest(features.get("ma150"), ticker)
        ma200 = _latest(features.get("ma200"), ticker)
        high_52w = _latest(features.get("high_52w"), ticker)
        low_52w = _latest(features.get("low_52w"), ticker)

        required_values = [
            latest_close,
            latest_volume,
            ma50,
            ma150,
            ma200,
            high_52w,
            low_52w,
        ]

        if any(value is None for value in required_values):
            continue

        is_stage2 = bool(latest_close > ma50 > ma150 > ma200)
        above_52w_low_30pct = bool(low_52w > 0 and latest_close > (low_52w * 1.30))
        near_52w_high = bool(high_52w > 0 and latest_close > (high_52w * 0.75))
        liquidity_ok = bool(latest_volume > liquidity_threshold)

        revenue_yoy = _fundamental_value(fundamentals, ticker, "revenue_yoy")
        eps_current = _fundamental_value(fundamentals, ticker, "eps_current")
        eps_last_year = _fundamental_value(fundamentals, ticker, "eps_last_year")

        revenue_growth_ok = None
        if revenue_yoy is not None:
            revenue_growth_ok = bool(revenue_yoy > 20.0)

        eps_growth_ok = None
        if eps_current is not None and eps_last_year is not None:
            eps_growth_ok = bool(eps_current > 0 and eps_current > eps_last_year)

        score = 0
        score += 40 if is_stage2 else 0
        score += 15 if above_52w_low_30pct else 0
        score += 15 if near_52w_high else 0
        score += 10 if liquidity_ok else 0
        score += 10 if revenue_growth_ok is True else 0
        score += 10 if eps_growth_ok is True else 0

        passed_core_template = (
            is_stage2
            and above_52w_low_30pct
            and near_52w_high
            and liquidity_ok
        )

        results.append({
            "ticker": ticker,
            "minervini_score": score,
            "passed_minervini_core": passed_core_template,
            "is_stage2": is_stage2,
            "above_52w_low_30pct": above_52w_low_30pct,
            "near_52w_high": near_52w_high,
            "liquidity_ok": liquidity_ok,
            "revenue_growth_ok": revenue_growth_ok,
            "eps_growth_ok": eps_growth_ok,
            "close": float(latest_close),
            "ma50": float(ma50),
            "ma150": float(ma150),
            "ma200": float(ma200),
            "high_52w": float(high_52w),
            "low_52w": float(low_52w),
            "volume": float(latest_volume),
        })

    return sorted(results, key=lambda row: row["minervini_score"], reverse=True)


def build_minervini_map(results):
    return {row["ticker"]: row for row in results}
