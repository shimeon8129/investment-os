from analysis.technical_action_mode import classify_action_mode


def enrich_ranked_with_action(
    ranked: list,
    close,
    features: dict,
    market_state: str,
    exit_decisions: dict,
    chip_map: dict = None,
) -> list:
    """
    Enrich each ranked candidate with action_mode, chase_risk, chip_status,
    suggested_action, technical_reasons, invalid_if fields.

    Args:
        ranked: list of ranked candidate dicts from rank_stocks()
        close: pd.DataFrame of close prices (tickers as columns)
        features: features dict from compute_features()
        market_state: BULL / RANGE / BEAR
        exit_decisions: dict of {ticker: {action, reason}} from exit check
        chip_map: optional dict of {ticker: chip_info} for chip_status

    Returns:
        enriched ranked list (in-place mutation + return)
    """
    from analysis.chase_risk import compute_chase_risk

    for item in ranked:
        ticker = item["ticker"]

        chase_result = compute_chase_risk(close, features, ticker)

        chip_info = (chip_map or {}).get(ticker)
        chip_status = _resolve_chip_status(chip_info)

        exit_entry = exit_decisions.get(ticker, {})
        exit_signal = exit_entry.get("action") if exit_entry else None
        # Normalise: exit_decisions uses "SELL" action for EXIT_ALL
        if exit_signal == "SELL":
            exit_signal = "EXIT_ALL"

        action_result = classify_action_mode(
            signal=item.get("signal", ""),
            level=item.get("level", ""),
            vol_ratio=item.get("vol_ratio", 0.0),
            chase_risk=chase_result["chase_risk"],
            chip_status=chip_status,
            market_state=market_state,
            exit_signal=exit_signal,
        )

        item.update({
            "action_mode": action_result["action_mode"],
            "action_label": action_result["action_label"],
            "suggested_action": action_result["suggested_action"],
            "chase_risk": chase_result["chase_risk"],
            "chase_risk_score": chase_result["chase_risk_score"],
            "chase_risk_reasons": chase_result["chase_risk_reasons"],
            "chip_status": chip_status,
            "chip_freshness": _resolve_chip_freshness(chip_info),
            "news_freshness": "MISSING",
            "narrative_status": "PRESENT" if item.get("narrative_score", 0) > 0 else "MISSING",
            "technical_reasons": action_result["technical_reasons"],
            "invalid_if": action_result["invalid_if"],
        })

    return ranked


def enrich_holdings_with_action(
    portfolio: dict,
    exit_decisions: dict,
    market_state: str,
) -> list:
    """
    Build holding action alerts for TECH_REDUCE / TECH_EXIT holdings.
    Returns list of alert dicts.
    """
    alerts = []
    for ticker, position in portfolio.items():
        exit_entry = exit_decisions.get(ticker, {})
        if not exit_entry:
            continue

        raw_action = exit_entry.get("action", "")
        exit_signal = "EXIT_ALL" if raw_action == "SELL" else raw_action

        if exit_signal not in ("EXIT_ALL", "REDUCE"):
            continue

        action_result = classify_action_mode(
            signal="",
            level="",
            vol_ratio=0.0,
            chase_risk="LOW",
            chip_status="UNKNOWN",
            market_state=market_state,
            exit_signal=exit_signal,
        )

        alerts.append({
            "ticker": ticker,
            "name": position.get("name", ticker),
            "shares": position.get("shares", 0),
            "action_mode": action_result["action_mode"],
            "exit_signal": exit_signal,
            "reason": exit_entry.get("reason", ""),
            "suggested_action": action_result["suggested_action"],
        })

    return alerts


def build_technical_action_summary(ranked: list) -> dict:
    """
    Count action modes across all ranked candidates for snapshot summary.
    """
    counts = {
        "tech_attack": 0,
        "tech_attack_caution": 0,
        "tech_buy": 0,
        "tech_buy_caution": 0,
        "tech_watch": 0,
        "tech_wait": 0,
        "tech_reduce": 0,
        "tech_exit": 0,
    }
    for item in ranked:
        mode = item.get("action_mode", "").lower()
        key = mode.replace("tech_", "tech_", 1)
        if key in counts:
            counts[key] += 1
    return {"mode": "TECHNICAL_DOMINANT_WITH_DATA_CONTEXT", **counts}


def format_technical_action_section(ranked: list, top_n: int = 5) -> str:
    lines = [
        "## Technical Action Summary\n",
        "| Rank | Ticker | Name | Action Mode | Signal | Level | Chase Risk | Chip Status | Suggested Action |",
        "|------|--------|------|-------------|--------|-------|------------|-------------|-----------------|",
    ]
    for i, item in enumerate(ranked[:top_n], 1):
        lines.append(
            f"| {i} | {item['ticker']} | {item.get('name', '')} "
            f"| {item.get('action_mode', '')} "
            f"| {item.get('signal', '')} "
            f"| {item.get('level', '')} "
            f"| {item.get('chase_risk', '')} "
            f"| {item.get('chip_status', '')} "
            f"| {item.get('suggested_action', '')} |"
        )
    return "\n".join(lines)


def format_holding_alerts_section(alerts: list) -> str:
    if not alerts:
        return "## Holding Action Alerts\n\nNo active exit/reduce signals."

    lines = [
        "## Holding Action Alerts\n",
        "| Ticker | Name | Shares | Action Mode | Exit Signal | Suggested Action |",
        "|--------|------|--------|-------------|-------------|-----------------|",
    ]
    for a in alerts:
        lines.append(
            f"| {a['ticker']} | {a['name']} | {a['shares']} "
            f"| {a['action_mode']} | {a['exit_signal']} "
            f"| {a['suggested_action']} |"
        )
    return "\n".join(lines)


def format_data_coverage_section(ranked: list) -> str:
    total = len(ranked)
    if total == 0:
        return "## Data Coverage Summary\n\nNo candidates."

    chips_count = sum(1 for r in ranked if r.get("chip_status") not in ("MISSING", "UNKNOWN", None))
    fresh_chips = sum(1 for r in ranked if r.get("chip_freshness") == "FRESH")
    news_count = sum(1 for r in ranked if r.get("news_freshness") not in ("MISSING", "STALE", None))
    narrative_count = sum(1 for r in ranked if r.get("narrative_status") == "PRESENT")

    lines = [
        "## Data Coverage Summary\n",
        f"- Technical coverage: {total}/{total} ✅",
        f"- Chips coverage: {chips_count}/{total}",
        f"- Fresh chips: {fresh_chips}/{total}",
        f"- NewsHeat coverage: {news_count}/{total}",
        f"- Narrative coverage: {narrative_count}/{total}",
        "",
        "> Missing data is visible but does not cancel a technical action.",
    ]
    return "\n".join(lines)


def _resolve_chip_status(chip_info: dict) -> str:
    if not chip_info:
        return "MISSING"

    foreign = chip_info.get("foreign_net_buy", 0)
    trust = chip_info.get("trust_net_buy", 0)
    dealer = chip_info.get("dealer_net_buy", 0)
    total = chip_info.get("institutional_net_buy", 0)

    if total > 1_000_000 and foreign > 0:
        return "STRONG_POSITIVE"
    if total > 0 and foreign > 0:
        return "POSITIVE"
    if foreign < 0 and trust < 0 and dealer < 0:
        return "STRONG_DIVERGENCE"
    if total < 0 or foreign < 0:
        return "DIVERGENCE"
    if total == 0 and foreign == 0 and trust == 0:
        return "MISSING"
    return "MIXED"


def _resolve_chip_freshness(chip_info: dict) -> str:
    if not chip_info:
        return "MISSING"
    return chip_info.get("chip_freshness", "STALE")
