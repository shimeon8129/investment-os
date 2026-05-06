# =========================================================
# decision/entry_lock_engine.py
# =========================================================
# P0.1: Non-invasive L0–L4 entry lock orchestrator.
#
# This is a NEW file. It does NOT modify decision/entry_lock.py.
# It reuses logic from entry_lock.py and imports from lock.py.
# It does NOT integrate into pipeline/main_v1.py.
# =========================================================

from decision.lock import apply_market_lock


def evaluate_all(close, volume, market_state, vix_value, portfolio, signal_results):
    """
    Evaluate L0–L4 entry locks for all signal candidates.

    Parameters
    ----------
    close : DataFrame
        Daily close prices; columns = ticker symbols.
    volume : DataFrame
        Daily volumes; columns = ticker symbols.
    market_state : str
        "BULL" / "RANGE" / "BEAR"
    vix_value : float
        Current VIX reading.
    portfolio : dict
        Current portfolio state (reserved for future L4+ use).
    signal_results : list[dict]
        Each item: {"ticker": str, "signal": str, "level": str}
        signal: "BUY" / other
        level:  "ATTACK" / "READY" / "EARLY" / ""

    Returns
    -------
    list[dict]
        One result dict per ticker — see _evaluate_ticker for schema.
    """
    results = []
    for sig in signal_results:
        ticker = sig.get("ticker", "")
        signal = sig.get("signal", "")
        level = sig.get("level", "")
        result = _evaluate_ticker(
            ticker=ticker,
            signal=signal,
            level=level,
            close=close,
            volume=volume,
            market_state=market_state,
            vix_value=vix_value,
        )
        results.append(result)
    return results


# ─────────────────────────────────────────────────────────
# Internal: per-ticker evaluation
# ─────────────────────────────────────────────────────────

def _evaluate_ticker(ticker, signal, level, close, volume, market_state, vix_value):
    locks = {}
    blocked_by = []

    # ── L0 Market Lock ────────────────────────────────────
    # Calls apply_market_lock from decision.lock (L0 source of truth).
    l0 = _eval_l0(ticker, market_state, vix_value)
    locks["L0_market"] = l0
    if l0["status"] == "BLOCK":
        blocked_by.append("L0_market")

    # ── L1 Selection Lock ─────────────────────────────────
    l1 = _eval_l1(level)
    locks["L1_selection"] = l1
    if l1["status"] == "BLOCK":
        blocked_by.append("L1_selection")

    # ── L2 / L3 / L4: require price & volume data ─────────
    try:
        price = float(close[ticker].iloc[-1])
        ma5 = float(close[ticker].rolling(5).mean().iloc[-1])
        ma10 = float(close[ticker].rolling(10).mean().iloc[-1])
        vol = float(volume[ticker].iloc[-1])
        vol_avg = float(volume[ticker].rolling(10).mean().iloc[-1])
        data_ok = True
    except Exception:
        data_ok = False

    if not data_ok:
        _skip = {
            "status": "SKIP",
            "severity": "INFO",
            "reason": "INSUFFICIENT_DATA",
            "source_module": "decision.entry_lock",
        }
        locks["L2_setup"] = _skip
        locks["L3_validation"] = _skip
        locks["L4_risk"] = _skip
    else:
        l2 = _eval_l2(price, ma5, ma10)
        locks["L2_setup"] = l2
        if l2["status"] == "BLOCK":
            blocked_by.append("L2_setup")

        l3 = _eval_l3(price, ma5, vol, vol_avg)
        locks["L3_validation"] = l3
        if l3["status"] == "BLOCK":
            blocked_by.append("L3_validation")

        l4 = _eval_l4(price, ma10)
        locks["L4_risk"] = l4
        if l4["status"] == "BLOCK":
            blocked_by.append("L4_risk")

    # ── Signal gate ───────────────────────────────────────
    signal_is_buy = (signal or "").upper() == "BUY"

    # ── Aggregate entry_lock_status ───────────────────────
    # Priority: BLOCK > SKIP > WARN > PASS
    # SKIP covers: any lock returned SKIP (insufficient data / unknown input)
    #              OR signal is not BUY (evaluation not applicable).
    if blocked_by:
        entry_lock_status = "BLOCK"
    elif any(lk["status"] == "SKIP" for lk in locks.values()) or not signal_is_buy:
        entry_lock_status = "SKIP"
    elif any(lk["status"] == "WARN" for lk in locks.values()):
        entry_lock_status = "WARN"
    else:
        entry_lock_status = "PASS"

    # ── Final action suggestion ───────────────────────────
    has_hard_block = any(lk.get("severity") == "HARD_BLOCK" for lk in locks.values())
    if has_hard_block or entry_lock_status in ("BLOCK", "SKIP"):
        final_action = "WAIT"
    elif entry_lock_status == "WARN":
        final_action = "ENTRY_REDUCED"
    else:
        final_action = "ENTRY"

    return {
        "ticker": ticker,
        "entry_lock_status": entry_lock_status,
        "final_action_suggestion": final_action,
        "blocked_by": blocked_by,
        "locks": locks,
    }


# ─────────────────────────────────────────────────────────
# Lock evaluators
# ─────────────────────────────────────────────────────────

def _eval_l0(ticker, market_state, vix_value):
    """
    L0 Market Lock — delegates to apply_market_lock from decision.lock.
    Uses a synthetic BUY decision to probe the market lock outcome.
    """
    synthetic = {ticker: {"action": "BUY", "position_size": 1.0}}
    result = apply_market_lock(synthetic, market_state, vix_value)
    ticker_out = result.get(ticker, {})

    action = ticker_out.get("action", "BUY")
    lock_reason = ticker_out.get("reason", "NORMAL")

    if action == "NO_TRADE":
        vix_str = f" (VIX {vix_value:.1f})" if vix_value is not None else ""
        return {
            "status": "BLOCK",
            "severity": "HARD_BLOCK",
            "reason": f"BEAR market - capital protection{vix_str}",
            "source_module": "decision.lock",
        }

    if lock_reason == "REDUCED_BY_MARKET":
        pos_pct = int(round(ticker_out.get("position_size", 1.0) * 100))
        detail = ticker_out.get("reason_detail", "RANGE market")
        return {
            "status": "WARN",
            "severity": "WARNING",
            "reason": f"{detail} - position reduced to {pos_pct}%",
            "source_module": "decision.lock",
        }

    return {
        "status": "PASS",
        "severity": "INFO",
        "reason": f"{market_state} market",
        "source_module": "decision.lock",
    }


def _eval_l1(level):
    """
    L1 Selection Lock — checks scanner signal level.
    ATTACK / READY → PASS.  EARLY → WARN.  Unknown/empty → SKIP.
    """
    level_upper = (level or "").upper()
    if level_upper == "ATTACK":
        return {
            "status": "PASS",
            "severity": "INFO",
            "reason": "ATTACK level",
            "source_module": "scanner",
        }
    if level_upper == "READY":
        return {
            "status": "PASS",
            "severity": "INFO",
            "reason": "READY level",
            "source_module": "scanner",
        }
    if level_upper == "EARLY":
        return {
            "status": "WARN",
            "severity": "WARNING",
            "reason": "EARLY level - signal not fully formed",
            "source_module": "scanner",
        }
    return {
        "status": "SKIP",
        "severity": "INFO",
        "reason": f"unknown level: {level!r}",
        "source_module": "scanner",
    }


def _eval_l2(price, ma5, ma10):
    """
    L2 Setup Lock — near MA5 and not too extended.
    Reuses logic from decision/entry_lock.py.
    """
    near_ma5 = price < ma5 * 1.03
    not_too_extended = price < ma10 * 1.10
    setup_ok = near_ma5 and not_too_extended

    if setup_ok:
        return {
            "status": "PASS",
            "severity": "INFO",
            "reason": "near MA5 and not too extended",
            "source_module": "decision.entry_lock",
        }

    if not near_ma5:
        reason = "price too far above MA5"
    else:
        reason = "price too extended above MA10"

    return {
        "status": "BLOCK",
        "severity": "HARD_BLOCK",
        "reason": reason,
        "source_module": "decision.entry_lock",
    }


def _eval_l3(price, ma5, vol, vol_avg):
    """
    L3 Validation Lock — volume confirmed and price above MA5.
    Reuses logic from decision/entry_lock.py.
    """
    vol_confirm = vol > vol_avg
    not_fake = price > ma5
    validation_ok = vol_confirm and not_fake

    if validation_ok:
        return {
            "status": "PASS",
            "severity": "INFO",
            "reason": "volume confirmed and price above MA5",
            "source_module": "decision.entry_lock",
        }

    if not vol_confirm:
        reason = "volume not confirmed"
    else:
        reason = "price below MA5"

    return {
        "status": "BLOCK",
        "severity": "HARD_BLOCK",
        "reason": reason,
        "source_module": "decision.entry_lock",
    }


def _eval_l4(price, ma10):
    """
    L4 Risk Lock — price above MA10.
    Reuses logic from decision/entry_lock.py.
    """
    if price > ma10:
        return {
            "status": "PASS",
            "severity": "INFO",
            "reason": "above MA10",
            "source_module": "decision.entry_lock",
        }
    return {
        "status": "BLOCK",
        "severity": "HARD_BLOCK",
        "reason": "price below MA10",
        "source_module": "decision.entry_lock",
    }
