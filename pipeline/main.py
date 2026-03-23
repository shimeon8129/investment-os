# pipeline/main.py

import sys
import os

# === PATH SETUP ===
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# === DATA ===
from scanner.universe import get_tw_universe, get_us_universe
from scanner.basic_scanner import scan_candidates
from data_node.loader import load_price_data

# === PROCESSING ===
from processing.features import compute_features

# === SIGNAL ===
from signal_engine.entry import generate_entry_signal

# === DECISION ===
from execution.trade import execute_trade

# === EXIT ===
from execution.exit import check_exit

# === PORTFOLIO + LOG ===
from execution.portfolio import load_portfolio
from execution.trade_log_writer import write_trade_log

# === MARKET ===
from decision.market import market_filter

# === LOCK ===
from decision.lock import apply_market_lock
from decision.position_lock import apply_position_lock
from decision.risk_lock import apply_risk_lock

# === FEEDBACK ===
from feedback.performance import analyze_performance

# === DEBUG ===
print("FILE LOADED")

# =========================================
# 🧠 MAIN PIPELINE
# =========================================

def run_pipeline():

    print("\n==============================")
    print("🚀 Investment OS Running")
    print("==============================")

    # =========================================
    # 🟦 1. Universe
    # =========================================

    tw_universe = get_tw_universe()
    us_universe = get_us_universe()

    tw_tickers = tw_universe["ticker"].tolist()
    us_tickers = us_universe["ticker"].tolist()

    # =========================================
    # 🟨 2. Market Engine（US）
    # =========================================

    us_close, us_volume = load_price_data(us_tickers)

    global_score = us_close.pct_change().iloc[-1].mean()
    market_state = market_filter(global_score)

    print("\n=== MARKET ===")
    print(f"State: {market_state} | Score: {round(global_score, 4)}")

    # =========================================
    # 🟩 3. TW Data
    # =========================================

    close, volume = load_price_data(tw_tickers)
    features = compute_features(close, volume)

    # =========================================
    # 🔍 SCANNER（新增🔥）
    # =========================================

    candidates = scan_candidates(close, volume, features)

    print("\n=== SCANNER ===")

    top_candidates = candidates[:10]  # 只取前10

    for c in top_candidates:

        tag = ""

        if c["level"] == "ATTACK":
            tag = "🔥ATTACK"
        elif c["level"] == "READY":
            tag = "⚡️READY"
        else:
            tag = "👀EARLY"

    print(f"{c['ticker']} → Score: {c['score']} | {c['level']} {tag} | Price: {c['price']}")

    # =========================================
    # 🔍 4. Signal
    # =========================================

    # 👉 從 Scanner 拿 ticker
    candidate_tickers = [c["ticker"] for c in top_candidates]

    # 👉 過濾資料（只保留候選股）
    filtered_close = close[candidate_tickers]
    filtered_volume = volume[candidate_tickers]

    # 👉 跑 Signal（只針對候選）
    signals = generate_entry_signal(filtered_close, filtered_volume, features)

    print("\n=== SIGNAL ===")

    # 👉 只印候選股（不是整個 universe）
    for c in top_candidates:
        ticker = c["ticker"]

        # 找名稱（從 universe）
        row = tw_universe[tw_universe["ticker"] == ticker]
        name = row["name"].values[0] if not row.empty else ""

        sig = signals.get(ticker, "")

        if sig:
            print(f"{ticker} {name} → {sig}")

        if not candidate_tickers:
            print("\n=== SIGNAL ===")
            print("No candidates")
            signals = {}
        else:
            filtered_close = close[candidate_tickers]
            filtered_volume = volume[candidate_tickers]

            signals = generate_entry_signal(filtered_close, filtered_volume, features)

    # =========================================
    # 🟨 5. Decision（原始）
    # =========================================

    decisions = execute_trade(signals, market_state)
    # 🧠 先載入 portfolio（只做一次）
    portfolio = load_portfolio()

    # 🔒 1. Market Lock（外部優先）
    decisions = apply_market_lock(decisions, market_state)

    # 🔒 2. Position Lock（內部）
    decisions = apply_position_lock(decisions, portfolio)

    # 🔒 3. Risk Lock（資金）
    decisions = apply_risk_lock(decisions, portfolio)

    # =========================================
    # 🖨️ 顯示 Decision（先看🔥）
    # =========================================

    print("\n=== DECISION ===")
    for _, row in tw_universe.iterrows():
        ticker = row["ticker"]
        name = row["name"]

        d = decisions.get(ticker, {})
        action = d.get("action", "")
        reason = d.get("reason", "")

        if action == "BUY":
            size = d.get("position_size", 0)
            sl = d.get("stop_loss", 0)
            extra = f" ({reason})" if reason else ""
            print(f"{ticker} {name} → BUY | 倉位: {size*100:.1f}% | 停損: {sl*100:.1f}%{extra}")

        elif action:
            extra = f" ({reason})" if reason else ""
            print(f"{ticker} {name} → {action}{extra}")

    # =========================================
    # 📝 WRITE TRADE LOG（🔥 再寫入）
    # =========================================

    new_trades = write_trade_log(decisions, close)

    if new_trades:
        print("\n=== NEW TRADES ===")
        for t in new_trades:
            print(f"{t['ticker']} → {t['action']} @ {t['price']} | size: {t['size']*100:.1f}%")

    # =========================================
    # 🟥 7. Exit → 轉 SELL Decision（🔥關鍵）
    # =========================================

    print("\n=== EXIT CHECK ===")

    # 👉 建立 exit decisions（會合併回主 decisions）
    exit_decisions = {}

    for ticker, position in portfolio.items():

        if ticker not in close.columns:
            continue

        current_price = close[ticker].iloc[-1]
        ma5 = features["ma5"][ticker].iloc[-1]
        highest_price = close[ticker].max()

        exit_signal = check_exit(
            position,
            current_price,
            ma5,
            highest_price
    )

    print(f"{ticker} → {exit_signal}")

    # 🔥 轉成 SELL decision
    if exit_signal == "SELL":
        exit_decisions[ticker] = {
            "action": "SELL"
        }

    # 👉 合併 SELL decision
    decisions.update(exit_decisions)

    # =========================================
    # 📝 WRITE TRADE LOG（最後一步🔥）
    # =========================================

    new_trades = write_trade_log(decisions, close)

    if new_trades:
        print("\n=== NEW TRADES ===")
        for t in new_trades:

            if t["action"] == "BUY":
                print(f"{t['ticker']} → BUY @ {t['price']} | size: {t['size']*100:.1f}%")

            elif t["action"] == "SELL":
                pnl = t.get("pnl_pct", 0)
                print(f"{t['ticker']} → SELL @ {t['price']} | PnL: {pnl*100:.2f}%")

    # =========================================
    # 🔁 8. Feedback（預留）
    # =========================================

    # TODO:
    # write_trade_log()
    # review()

    # =========================================
    # 📊 PERFORMANCE REPORT（🔥 新增）
    # =========================================

    perf = analyze_performance()

    print("\n=== PERFORMANCE ===")
    print(f"Trades: {perf['total_trades']}")
    print(f"Win Rate: {perf['win_rate']*100:.1f}%")
    print(f"Avg Return: {perf['avg_return']*100:.2f}%")
    print(f"Total Return: {perf['total_return']*100:.2f}%")
    print(f"Max Drawdown: {perf['max_drawdown']*100:.2f}%")

    print("\n==============================")
    print("✅ Pipeline Done")
    print("==============================")


# =========================================
# ENTRY POINT
# =========================================

print(" ENTRY CHECK")

if __name__ == "__main__":
    run_pipeline()
