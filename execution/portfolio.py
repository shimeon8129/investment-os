# execution/portfolio.py

import json


def load_portfolio_from_holdings(filepath="data/portfolio/current_holdings.json"):
    """
    Build active position dict from broker-confirmed current_holdings.json.
    This is the authoritative source for real positions used by position lock and exit check.
    Tickers stored without suffix (e.g. '3711') are normalized to yfinance format ('3711.TW').
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {}

    portfolio = {}
    for h in data.get("holdings", []):
        raw = str(h.get("ticker", "")).strip()
        if not raw:
            continue
        ticker = raw if "." in raw else f"{raw}.TW"
        portfolio[ticker] = {
            "entry_price": float(h.get("entry_price") or 0.0),
            "size": int(h.get("shares") or 0),
        }
    return portfolio


def load_portfolio(filepath="data/trade_log.json"):
    """
    從 trade log 建立目前持倉（Portfolio v1）
    """

    try:
        with open(filepath, "r") as f:
            trades = json.load(f)
    except FileNotFoundError:
        return {}

    portfolio = {}

    for t in trades:
        ticker = t["ticker"]
        action = t["action"]

        if action == "BUY":
            portfolio[ticker] = {
                "entry_price": t["price"],
                "size": t["size"]
            }

        elif action == "SELL":
            if ticker in portfolio:
                del portfolio[ticker]

    return portfolio
