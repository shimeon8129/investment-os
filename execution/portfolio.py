# execution/portfolio.py

import json


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
