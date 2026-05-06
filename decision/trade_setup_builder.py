# =========================================================
# decision/trade_setup_builder.py
# =========================================================
# P0.2: Greenfield trade setup builder.
#
# Reads from existing close DataFrame, volume, features dict.
# Does NOT invent a new data pipeline.
# Does NOT integrate into pipeline/main_v1.py.
# Does NOT modify any existing files.
# =========================================================

import math

# Default parameters
_DEFAULT_STOP_PCT = 0.05   # 5% stop loss from entry
_TARGET_1_PCT = 0.10       # +10% target 1
_TARGET_2_PCT = 0.20       # +20% target 2
_MIN_SERIES_LEN = 10       # minimum bars required
_SWING_LOW_WINDOW = 10     # bars for recent swing low


def build_trade_setup(
    ticker,
    close,
    volume=None,
    features=None,
    signal=None,
    candidate=None,
    setup_type_hint=None,
):
    """
    Build a trade setup dict for a given ticker.

    Parameters
    ----------
    ticker : str
    close : DataFrame
        Daily close prices; columns = ticker symbols.
    volume : DataFrame or None
        Daily volumes; columns = ticker symbols. Optional.
    features : dict or None
        Output of processing.features.compute_features. Optional.
    signal : str or None
        Entry signal string, e.g. "BUY", "READY".
    candidate : dict or None
        Scanner candidate record: {ticker, score, level, price, ...}.
    setup_type_hint : str or None
        If provided, overrides auto-inferred setup_type.

    Returns
    -------
    dict with keys:
        ticker, setup_type, entry_zone, invalidation_price,
        stop_loss_price, target_1, target_2, risk_reward, setup_status
    """
    # ── 1. Validate price data ─────────────────────────────
    try:
        if close is None or ticker not in close.columns:
            return _result_insufficient(ticker)

        price_series = close[ticker].dropna()

        if len(price_series) < _MIN_SERIES_LEN:
            return _result_insufficient(ticker)

        price = float(price_series.iloc[-1])

        if not math.isfinite(price) or price <= 0:
            return _result_insufficient(ticker)

    except Exception:
        return _result_insufficient(ticker)

    # ── 2. Setup type ──────────────────────────────────────
    setup_type = _infer_setup_type(signal, candidate, setup_type_hint)

    # ── 3. Entry zone ──────────────────────────────────────
    # BUY (breakout): entry at the breakout trigger level (10-day prev high).
    # All other signals: entry at current price.
    entry_zone = _compute_entry_zone(price, price_series, signal)

    # ── 4. Invalidation price (recent swing low) ───────────
    invalidation_price = _compute_invalidation_price(price_series, entry_zone)

    # ── 5. Stop loss (rule-based: 5% below entry) ──────────
    stop_loss_price = round(entry_zone * (1 - _DEFAULT_STOP_PCT), 4)

    # ── 6. Targets ─────────────────────────────────────────
    target_1 = round(entry_zone * (1 + _TARGET_1_PCT), 4)
    target_2 = round(entry_zone * (1 + _TARGET_2_PCT), 4)

    # ── 7. Risk/reward ─────────────────────────────────────
    risk_per_share = entry_zone - stop_loss_price
    if risk_per_share <= 0:
        return _result_invalid(
            ticker, setup_type, entry_zone, invalidation_price,
            stop_loss_price, target_1, target_2,
        )

    reward = target_1 - entry_zone
    risk_reward = round(reward / risk_per_share, 4)

    # ── 8. Setup status ────────────────────────────────────
    # Minimum acceptable R/R is 1.0; any lower is structurally unfavorable.
    setup_status = "VALID" if risk_reward >= 1.0 else "INVALID"

    return {
        "ticker": ticker,
        "setup_type": setup_type,
        "entry_zone": round(entry_zone, 4),
        "invalidation_price": round(invalidation_price, 4),
        "stop_loss_price": stop_loss_price,
        "target_1": target_1,
        "target_2": target_2,
        "risk_reward": risk_reward,
        "setup_status": setup_status,
    }


# ─────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────

def _infer_setup_type(signal, candidate, setup_type_hint):
    """Infer setup_type from signal, candidate level, or explicit hint."""
    if setup_type_hint:
        return str(setup_type_hint)

    signal_upper = (signal or "").upper()
    level = ((candidate or {}).get("level") or "").upper()

    if signal_upper == "BUY":
        return "VCP_BREAKOUT"
    if signal_upper == "READY":
        return "PULLBACK_SETUP"

    if level == "ATTACK":
        return "ATTACK_BREAKOUT"
    if level == "READY":
        return "PULLBACK_SETUP"
    if level == "EARLY":
        return "EARLY_WATCH"

    return "UNKNOWN"


def _compute_entry_zone(price, price_series, signal):
    """
    For BUY (breakout) signals, entry at the 10-day prior high (breakout level).
    For all other signals, entry at current price.
    """
    if (signal or "").upper() != "BUY":
        return price

    # The breakout trigger is the rolling-10 high up to yesterday (iloc[-2]).
    try:
        if len(price_series) >= _MIN_SERIES_LEN + 1:
            prev_high = float(price_series.rolling(_SWING_LOW_WINDOW).max().iloc[-2])
            if math.isfinite(prev_high) and prev_high > 0:
                return prev_high
    except Exception:
        pass

    return price


def _compute_invalidation_price(price_series, entry_zone):
    """
    Recent swing low over the past _SWING_LOW_WINDOW bars.
    If the computed low is >= entry_zone (pathological data), fall back to
    entry_zone * 0.90 to keep the structure intact.
    """
    try:
        swing_low = float(price_series.rolling(_SWING_LOW_WINDOW).min().iloc[-1])
        if math.isfinite(swing_low) and swing_low > 0 and swing_low < entry_zone:
            return swing_low
    except Exception:
        pass

    return round(entry_zone * 0.90, 4)


# ─────────────────────────────────────────────────────────
# Status factory helpers
# ─────────────────────────────────────────────────────────

def _result_insufficient(ticker):
    return {
        "ticker": ticker,
        "setup_type": "UNKNOWN",
        "entry_zone": None,
        "invalidation_price": None,
        "stop_loss_price": None,
        "target_1": None,
        "target_2": None,
        "risk_reward": None,
        "setup_status": "INSUFFICIENT_DATA",
    }


def _result_invalid(
    ticker, setup_type, entry_zone, invalidation_price,
    stop_loss_price, target_1, target_2,
):
    return {
        "ticker": ticker,
        "setup_type": setup_type,
        "entry_zone": round(entry_zone, 4),
        "invalidation_price": round(invalidation_price, 4),
        "stop_loss_price": stop_loss_price,
        "target_1": target_1,
        "target_2": target_2,
        "risk_reward": None,
        "setup_status": "INVALID",
    }
