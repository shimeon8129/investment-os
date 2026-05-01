# pipeline/main_v1.py
# Clean extraction of Block B from pipeline/main.py.
# Surgical cleanups applied per docs/MAINLINE_REVIEW_20260501.md.

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

# === RISK ===
from execution.risk import apply_risk_filters

# === FEEDBACK ===
from feedback.performance import analyze_performance

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

    if candidates is None:
        print("⚠️ Scanner returned None")
        candidates = []

    top_candidates = candidates[:10]

    scanner_results = {}

    for c in top_candidates:

        ticker = c["ticker"]
        scanner_results[ticker] = c["score"]
        minervini_score = minervini_map.get(ticker, {}).get("minervini_score", 0)

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

    candidate_tickers = [
        c["ticker"] for c in top_candidates
        if c.get("ticker") in close.columns
    ]

    print("\n=== SIGNAL ===")

    candidate_info = {c["ticker"]: c for c in top_candidates}

    if not candidate_tickers:
        print("No valid candidates")
        signals = {}
    else:
        filtered_close = close[candidate_tickers]
        filtered_volume = volume[candidate_tickers]

        signals = generate_entry_signal(
            filtered_close,
            filtered_volume,
            features,
            candidate_info
        )

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
    # 🟨 5. Decision
    # =========================================

    if not ranked:
        print("\n⚠️ No ranked stocks, skipping decision")
        ranked = []

    top_stocks = ranked[:3]

    if not top_stocks:
        print("⚠️ No top stocks, creating empty decisions")
        decisions = {}
    else:
        top_signals = {
            s["ticker"]: s["signal"]
            for s in top_stocks
        }

        decisions = execute_trade(top_signals, market_state)

    if decisions is None:
        print("⚠️ execute_trade returned None, using empty dict")
        decisions = {}

    portfolio = load_portfolio()

    print("\n=== DECISION ===")

    # 🔒 1. Market Lock
    decisions = apply_market_lock(decisions, market_state, vix_value)

    # 🔒 2. Position Lock
    decisions = apply_position_lock(decisions, portfolio)

    # 🔒 3. Risk Lock
    decisions = apply_risk_filters(
        decisions,
        portfolio,
        capital=capital,
        market_state=market_state,
        vix_value=vix_value
    )

    # =========================================
    # 🖨️ Display Decisions
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
            extra = f" ({risk_reason})" if risk_reason else ""
            print(f"{ticker} {name} → NO_TRADE (RISK_CHECK: {risk_reason}){extra}")

        elif action:
            extra = f" ({reason})" if reason else ""
            print(f"{ticker} {name} → {action}{extra}")

    # =========================================
    # 🟥 7. Exit → SELL Decision
    # =========================================

    print("\n=== EXIT CHECK ===")

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

        if exit_signal == "SELL":
            exit_decisions[ticker] = {
                "action": "SELL"
            }

    decisions.update(exit_decisions)

    # =========================================
    # 📝 WRITE TRADE LOG
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

if __name__ == "__main__":
    run_pipeline(capital=100000)
