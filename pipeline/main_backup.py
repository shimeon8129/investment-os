# pipeline/main.py

import sys
import os

# === PATH SETUP ===
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# === DATA ===
from scanner.universe import get_tw_universe, get_us_universe
from scanner.basic_scanner import scan_candidates
from data_node.loader import load_price_data

# === RANKING===
from pipeline.ranking_engine import rank_stocks, print_top_picks

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
    # 🔍 3.5 SCANNER（🔥補回來）
    # =========================================

    print("\n=== SCANNER ===")

    candidates = scan_candidates(close, volume, features)

    # 防呆（避免 None）
    if candidates is None:
        print("⚠️ Scanner returned None")
        candidates = []

    # 取前10
    top_candidates = candidates[:10]

    # 給 Ranking 用
    scanner_results = {}

    for c in top_candidates:

        ticker = c["ticker"]
        scanner_results[ticker] = c["score"]

        # 🔥 加名稱
        row = tw_universe[tw_universe["ticker"] == ticker]
        name = row["name"].values[0] if not row.empty else ""

        tag = ""

        if c["level"] == "ATTACK":
            tag = "🔥ATTACK"
        elif c["level"] == "READY":
            tag = "⚡️READY"
        else:
            tag = "👀EARLY"


        print(f"{ticker} {name} → Score: {c['score']} | {c['level']} {tag} | Price: {c['price']}")


    # =========================================
    # 🔍 4. Signal（🔥整合 READY 升級版）
    # =========================================

    # 👉 從 Scanner 拿 ticker（避免抓不到資料）
    candidate_tickers = [
        c["ticker"] for c in top_candidates
        if c.get("ticker") in close.columns
    ]

    print("\n=== SIGNAL ===")

    # 👉 建立 scanner map（🔥關鍵）
    candidate_info = {c["ticker"]: c for c in top_candidates}

    # 👉 防止空資料 crash
    if not candidate_tickers:
        print("No valid candidates")
        signals = {}
    else:
        # 👉 過濾資料
        filtered_close = close[candidate_tickers]
        filtered_volume = volume[candidate_tickers]

        # 👉 跑 Signal（🔥多傳一個參數）
        signals = generate_entry_signal(
            filtered_close,
            filtered_volume,
            features,
            candidate_info   # 🔥 關鍵在這
        )

    # 👉 收集結果
    signal_results = []

    for c in top_candidates:
        ticker = c["ticker"]

        row = tw_universe[tw_universe["ticker"] == ticker]
        name = row["name"].values[0] if not row.empty else ""

        sig = signals.get(ticker, "")

        if sig:
            print(f"{ticker} {name} → {sig}")

            signal_results.append({
                "ticker": ticker,
                "signal": sig,
                "level": c["level"]
            })


    # =========================================
    # 🧠 RANKING ENGINE（🔥新增）
    # =========================================

    name_map = dict(zip(tw_universe["ticker"], tw_universe["name"]))
    sector_map = dict(zip(tw_universe["ticker"], tw_universe["sector"]))

    ranked = rank_stocks(
        signal_results,
        scanner_results,
        sector_map,
        name_map
    )

    print_top_picks(ranked, top_n=3)

    # =========================================
    # 🟨 5. Decision（原始）
    # =========================================

    # 只取 Top 3
    top_stocks = ranked[:3]

    top_signals = {
        s["ticker"]: s["signal"]
        for s in top_stocks
    }

    decisions = execute_trade(top_signals, market_state)

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
