# pipeline/main.py

import sys
import os

# === PATH SETUP ===
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# === DATA ===
from scanner.universe import get_tw_universe, get_us_universe
from scanner.basic_scanner import scan_candidates
from scanner.minervini_scanner import build_minervini_map, scan_minervini_candidates
from data_node.loader import load_price_data

# === RANKING===
from pipeline.ranking_engine import rank_stocks, print_top_picks
from pipeline.narrative_loader import load_narrative_map
from pipeline.news_heat_loader import load_news_heat_map
from pipeline.chips_loader import load_chips_map

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

# === DASHBOARD ===
from execution.portfolio_dashboard import build_daily_dashboard

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

    close, volume = load_price_data(tw_tickers, period="2y")
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

# ==========================================================
# 🔄 5. 整合入 main.py 的方式
# ==========================================================


# pipeline/main.py（修復版 - 只改 DECISION 段落）
# 
# 問題：decisions 沒有被正確初始化
# 解決方案：先檢查 ranked 是否為空，確保 decisions 一定會被創建
# ───────────────────────────────────────────────────────

import sys
import os

# === PATH SETUP ===
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# === DATA ===
from scanner.universe import get_tw_universe, get_us_universe
from scanner.basic_scanner import scan_candidates
from scanner.minervini_scanner import build_minervini_map, scan_minervini_candidates
from data_node.loader import load_price_data

# === RANKING===
from pipeline.ranking_engine import rank_stocks, print_top_picks
from pipeline.narrative_loader import load_narrative_map
from pipeline.news_heat_loader import load_news_heat_map
from pipeline.chips_loader import load_chips_map

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

# === 🔥 新增：風險層 ===
from execution.risk import apply_risk_filters

# === FEEDBACK ===
from feedback.performance import analyze_performance

# === DEBUG ===
print("FILE LOADED")

# =========================================
# 🧠 MAIN PIPELINE
# =========================================

def run_pipeline(capital=100000):

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

    # 🔥【新增】取得 VIX 值
    vix_value = None
    if '^VIX' in us_close.columns:
        vix_value = us_close['^VIX'].iloc[-1]

    print("\n=== MARKET ===")
    print(f"State: {market_state} | Score: {round(global_score, 4)}")
    if vix_value:
        print(f"VIX: {vix_value:.2f}")

    # =========================================
    # 🟩 3. TW Data
    # =========================================

    close, volume = load_price_data(tw_tickers, period="2y")
    features = compute_features(close, volume)

    # =========================================
    # 🔍 3.5 SCANNER
    # =========================================

    print("\n=== SCANNER ===")

    candidates = scan_candidates(close, volume, features)

    minervini_candidates = scan_minervini_candidates(close, volume, features)
    minervini_map = build_minervini_map(minervini_candidates)

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
        minervini_score = minervini_map.get(ticker, {}).get("minervini_score", 0)

        # 加名稱
        row = tw_universe[tw_universe["ticker"] == ticker]
        name = row["name"].values[0] if not row.empty else ""

        tag = ""

        if c["level"] == "ATTACK":
            tag = "🔥ATTACK"
        elif c["level"] == "READY":
            tag = "⚡️READY"
        else:
            tag = "👀EARLY"

        print(
            f"{ticker} {name} → Score: {c['score']} | Minervini: {minervini_score} "
            f"| {c['level']} {tag} | Price: {c['price']}"
        )

    # =========================================
    # 🔍 4. Signal
    # =========================================

    # 從 Scanner 拿 ticker（避免抓不到資料）
    candidate_tickers = [
        c["ticker"] for c in top_candidates
        if c.get("ticker") in close.columns
    ]

    print("\n=== SIGNAL ===")

    # 建立 scanner map
    candidate_info = {c["ticker"]: c for c in top_candidates}

    # 防止空資料 crash
    if not candidate_tickers:
        print("No valid candidates")
        signals = {}
    else:
        # 過濾資料
        filtered_close = close[candidate_tickers]
        filtered_volume = volume[candidate_tickers]

        # 跑 Signal
        signals = generate_entry_signal(
            filtered_close,
            filtered_volume,
            features,
            candidate_info
        )

    # 收集結果
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
    # 🧠 RANKING ENGINE
    # =========================================

    name_map = dict(zip(tw_universe["ticker"], tw_universe["name"]))
    sector_map = dict(zip(tw_universe["ticker"], tw_universe["sector"]))
    narrative_map = load_narrative_map()
    news_heat_map = load_news_heat_map()
    chips_map = load_chips_map()

    ranked = rank_stocks(
        signal_results,
        scanner_results,
        sector_map,
        name_map,
        minervini_map,
        narrative_map,
        news_heat_map,
        chips_map
    )

    print_top_picks(ranked, top_n=3)

    # =========================================
    # 🟨 5. Decision（🔥 修復版本）
    # =========================================

    # 🔥【修復】檢查 ranked 是否為空
    if not ranked:
        print("\n⚠️ No ranked stocks, skipping decision")
        ranked = []
    
    # 只取 Top 3
    top_stocks = ranked[:3]

    # 🔥【修復】確保 decisions 一定會被初始化
    if not top_stocks:
        print("⚠️ No top stocks, creating empty decisions")
        decisions = {}
    else:
        top_signals = {
            s["ticker"]: s["signal"]
            for s in top_stocks
        }

        # 這裡 decisions 才會被創建
        decisions = execute_trade(top_signals, market_state)

    # 防呆：確保 decisions 存在
    if decisions is None:
        print("⚠️ execute_trade returned None, using empty dict")
        decisions = {}

    # 🧠 先載入 portfolio（只做一次）
    portfolio = load_portfolio()

    print("\n=== DECISION ===")

    # 🔒 1. Market Lock（外部優先）
    decisions = apply_market_lock(decisions, market_state, vix_value)

    # 🔒 2. Position Lock（內部）
    decisions = apply_position_lock(decisions, portfolio)

    # 🔒 3. 🔥【新增】Risk Lock（資金 + 市場狀態）
    decisions = apply_risk_filters(
        decisions,
        portfolio,
        capital=capital,           # 10 萬元
        market_state=market_state, # BULL/BEAR/RANGE
        vix_value=vix_value        # VIX 值用於調整係數
    )

    # =========================================
    # 🖨️ 顯示 Decision
    # =========================================

    for _, row in tw_universe.iterrows():
        ticker = row["ticker"]
        name = row["name"]

        d = decisions.get(ticker, {})
        action = d.get("action", "")
        reason = d.get("reason", "")
        risk_check = d.get("risk_check", "")
        risk_reason = d.get("risk_reason", "")

        if action == "BUY":
            size = d.get("position_size", 0)
            sl = d.get("stop_loss", 0)
            extra = f" ({reason})" if reason else ""
            risk_str = f" [Risk: {risk_check}]" if risk_check else ""
            print(f"{ticker} {name} → BUY | 倉位: {size*100:.1f}% | 停損: {sl*100:.1f}%{extra}{risk_str}")

        elif action == "NO_TRADE" and risk_check == "FAIL":
            # 顯示被風險層攔截的原因
            extra = f" ({risk_reason})" if risk_reason else ""
            print(f"{ticker} {name} → NO_TRADE (RISK_CHECK: {risk_reason}){extra}")

        elif action:
            extra = f" ({reason})" if reason else ""
            print(f"{ticker} {name} → {action}{extra}")

    # =========================================
    # 📝 WRITE TRADE LOG
    # =========================================

    new_trades = write_trade_log(decisions, close)

    if new_trades:
        print("\n=== NEW TRADES ===")
        for t in new_trades:
            print(f"{t['ticker']} → {t['action']} @ {t['price']} | size: {t['size']*100:.1f}%")

    # =========================================
    # 🟥 7. Exit → 轉 SELL Decision
    # =========================================

    print("\n=== EXIT CHECK ===")

    # 建立 exit decisions（會合併回主 decisions）
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

        # 轉成 SELL decision
        if exit_signal == "SELL":
            exit_decisions[ticker] = {
                "action": "SELL"
            }

    # 合併 SELL decision
    decisions.update(exit_decisions)

    # =========================================
    # 📝 WRITE TRADE LOG（最後一步）
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
    # 📊 PERFORMANCE REPORT
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
    run_pipeline(capital=100000)  # 10 萬元
