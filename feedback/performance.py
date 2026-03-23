# feedback/performance.py

import json


def load_trade_log(filepath="data/trade_log.json"):
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except:
        return []


def analyze_performance(filepath="data/trade_log.json"):
    trades = load_trade_log(filepath)

    # 只抓 SELL（才有 PnL）
    sells = [t for t in trades if t.get("action") == "SELL"]

    if not sells:
        return {
            "total_trades": 0,
            "win_rate": 0,
            "avg_return": 0,
            "total_return": 0,
            "max_drawdown": 0
        }

    pnl_list = [t.get("pnl_pct", 0) for t in sells]

    total_trades = len(pnl_list)
    wins = [p for p in pnl_list if p > 0]

    win_rate = len(wins) / total_trades
    avg_return = sum(pnl_list) / total_trades
    total_return = sum(pnl_list)
    max_drawdown = min(pnl_list)

    return {
        "total_trades": total_trades,
        "win_rate": win_rate,
        "avg_return": avg_return,
        "total_return": total_return,
        "max_drawdown": max_drawdown
    }
