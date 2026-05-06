def build_daily_dashboard(portfolio, close, features, market_state, vix_value=None):
    """
    Minimal daily dashboard output.
    Current stage: summarize portfolio and market state.
    """
    positions = []

    for ticker, pos in portfolio.items():
        entry_price = pos.get("entry_price", 0)
        size = pos.get("size", 0)
        current_price = float(close[ticker].iloc[-1]) if ticker in close.columns else entry_price
        pnl_pct = (current_price - entry_price) / entry_price if entry_price else 0

        positions.append({
            "ticker": ticker,
            "entry_price": entry_price,
            "current_price": current_price,
            "size": size,
            "pnl_pct": pnl_pct,
            "action": "HOLD",
        })

    return {
        "market_state": market_state,
        "vix_value": vix_value,
        "positions": positions,
        "summary": {
            "total_positions": len(positions),
        },
    }
