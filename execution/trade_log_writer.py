# execution/trade_log_writer.py

import json
import os
from datetime import datetime


def _read_log(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _write_log(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)


def _get_open_positions(log):
    """
    從 log 推出目前持倉（簡化版：最後一次 BUY 且未被 SELL 抵消）
    """
    positions = {}
    for t in log:
        ticker = t["ticker"]
        action = t["action"]

        if action == "BUY":
            positions[ticker] = t
        elif action == "SELL":
            if ticker in positions:
                del positions[ticker]

    return positions


def _latest_valid_price(close, ticker):
    if ticker not in close.columns:
        return None

    series = close[ticker].dropna()
    if series.empty:
        return None

    return float(series.iloc[-1])


def write_trade_log(decisions, close, filepath="data/trade_log.json"):
    """
    寫入 BUY / SELL（含 PnL）
    """
    log = _read_log(filepath)
    today = datetime.now().strftime("%Y-%m-%d")

    open_positions = _get_open_positions(log)
    new_entries = []

    for ticker, d in decisions.items():
        action = d.get("action")

        # =========================
        # BUY
        # =========================
        if action == "BUY":
            if ticker in open_positions:
                continue  # 避免重複

            price = _latest_valid_price(close, ticker)
            if price is None:
                continue

            size = d.get("position_size", 0)

            new_entries.append({
                "date": today,
                "ticker": ticker,
                "action": "BUY",
                "price": price,
                "size": size
            })

        # =========================
        # SELL（含 PnL🔥）
        # =========================
        elif action == "SELL":
            if ticker not in open_positions:
                continue  # 沒持倉不能賣

            entry = open_positions[ticker]
            entry_price = entry["price"]
            exit_price = _latest_valid_price(close, ticker)
            if exit_price is None:
                continue

            pnl_pct = (exit_price - entry_price) / entry_price

            new_entries.append({
                "date": today,
                "ticker": ticker,
                "action": "SELL",
                "price": exit_price,
                "size": entry.get("size", 0),
                "entry_price": entry_price,
                "pnl_pct": pnl_pct
            })

    if new_entries:
        log.extend(new_entries)
        _write_log(filepath, log)

    return new_entries
