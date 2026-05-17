# pipeline/main_v1.py
# Clean extraction of Block B from pipeline/main.py.
# Surgical cleanups applied per docs/MAINLINE_REVIEW_20260501.md.

import sys
import os
import json
from datetime import datetime
from pathlib import Path

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

# === PORTFOLIO ===
from execution.portfolio import load_portfolio_from_holdings

# === MARKET ===
from decision.market import market_filter, get_vix_alert, get_market_guidance

# === LOCK ===
from decision.lock import apply_market_lock
from decision.position_lock import apply_position_lock

# === RISK ===
from execution.risk import apply_risk_filters

# === TECHNICAL ACTION ===
from reporting.technical_action_report import (
    enrich_ranked_with_action,
    enrich_holdings_with_action,
    build_technical_action_summary,
)

# === SAFETY ===
from decision.entry_safety_gate import apply_entry_safety_gate


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

    close, volume = load_price_data(tw_tickers, period="1y")
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

    # Phase 2B: pre-compute chase_risk_score for all candidates, then re-sort
    # so that within the same score tier, lower chase risk wins the top-10 slot.
    from analysis.chase_risk import compute_chase_risk as _compute_chase_risk
    for c in candidates:
        ticker = c.get("ticker", "")
        if ticker in close.columns:
            cr = _compute_chase_risk(close, features, ticker)
            c["_pre_chase_risk_score"] = cr["chase_risk_score"]
        else:
            c["_pre_chase_risk_score"] = 0
    candidates.sort(
        key=lambda x: (-x.get("score", 0), x.get("_pre_chase_risk_score", 0))
    )

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

    # 取最新一日的 vol_ratio（當日量 / 5日均量）
    vol_ratio_map = {}
    if "vol_ratio" in features:
        vr = features["vol_ratio"]
        for ticker in candidate_tickers:
            if ticker in vr.columns:
                latest = vr[ticker].dropna()
                if not latest.empty:
                    vol_ratio_map[ticker] = float(latest.iloc[-1])

    ranked = rank_stocks(
        signal_results,
        scanner_results,
        sector_map,
        name_map,
        minervini_map,
        narrative_map,
        news_heat_map,
        chips_map,
        vol_ratio_map,
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

    portfolio = load_portfolio_from_holdings()

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

        if exit_signal == "EXIT_ALL":
            exit_decisions[ticker] = {"action": "SELL", "reason": exit_signal}
        elif exit_signal == "REDUCE":
            exit_decisions[ticker] = {"action": "REDUCE", "reason": exit_signal}

    decisions.update(exit_decisions)

    # =========================================
    # 🎯 TECHNICAL ACTION ENRICHMENT
    # =========================================

    chips_map = load_chips_map()
    ranked = enrich_ranked_with_action(
        ranked,
        close,
        features,
        market_state,
        exit_decisions,
        chip_map=chips_map,
        news_heat_map=news_heat_map,
        narrative_map=narrative_map,
    )

    # ✅ P0 hotfix: apply safety gate after enrichment (chip_status / chase_risk 已就位)
    held_tickers = set(portfolio.keys())
    ranked = [
        apply_entry_safety_gate({**r, "is_held": r.get("ticker", "") in held_tickers})
        for r in ranked
    ]

    holding_alerts = enrich_holdings_with_action(portfolio, exit_decisions, market_state)
    technical_action_summary = build_technical_action_summary(ranked)

    # =========================================
    # 🎭 ROLE ROUTING
    # =========================================

    vix_alert = get_vix_alert(vix_value)
    market_guidance = get_market_guidance(market_state, vix_alert)

    # Load role_map for routing
    _role_map_path = Path("data/portfolio/role_map.json")
    _role_lookup = {}
    if _role_map_path.exists():
        try:
            _rm = json.loads(_role_map_path.read_text(encoding="utf-8"))
            for entry in _rm.get("entries", []):
                t = entry.get("ticker", "")
                if t:
                    _role_lookup[t] = entry
        except Exception:
            pass

    def _active_role(ticker: str) -> str:
        e = _role_lookup.get(ticker) or _role_lookup.get(ticker.split(".")[0])
        return e.get("active_role", "WAVE_SWING") if e else "WAVE_SWING"

    # Split ranked candidates by role
    wave_swing_candidates = []
    satellite_watch = []
    core_watch = []
    for r in ranked:
        role = _active_role(r["ticker"])
        if role in ("CORE", "CORE_ETF"):
            core_watch.append(r)
        elif role == "SATELLITE":
            satellite_watch.append(r)
        else:
            wave_swing_candidates.append(r)

    # Holdings guidance: role-aware action for each current holding
    holdings_guidance = []
    for ticker, position in portfolio.items():
        role = _active_role(ticker)
        exit_entry = exit_decisions.get(ticker, {})
        exit_action = exit_entry.get("action", "")
        exit_reason = exit_entry.get("reason", "")

        if role in ("CORE", "CORE_ETF"):
            if exit_action == "SELL":
                rec = "WATCH_TREND_DAMAGE"
                note = "出場訊號觸發，確認是否 MA60 結構損壞再決定"
            elif exit_action == "REDUCE":
                rec = "TRIM_OVEREXTENDED"
                note = "技術超買，考慮部分獲利了結"
            else:
                rec = "HOLD_CORE"
                note = "趨勢完整，長期持有，不因短線波動減碼"
        elif role == "SATELLITE":
            if exit_action in ("SELL", "REDUCE"):
                rec = "REVIEW_EXIT"
                note = f"出場訊號 ({exit_reason})，確認籌碼與 MA20 位置"
            else:
                rec = "HOLD_SATELLITE"
                note = "中期持有，注意籌碼變化"
        else:
            if exit_action == "SELL":
                rec = "EXIT"
                note = f"出場 ({exit_reason})"
            elif exit_action == "REDUCE":
                rec = "REDUCE"
                note = f"減碼 ({exit_reason})"
            else:
                rec = "HOLD"
                note = "持有，守 MA5 停損"

        holdings_guidance.append({
            "ticker": ticker,
            "name": position.get("name", ticker),
            "role": role,
            "recommendation": rec,
            "note": note,
        })

    # =========================================
    # 📸 SNAPSHOT
    # =========================================

    snapshot_dir = Path("data/processed")
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = snapshot_dir / "mainline_snapshot.json"

    snapshot = {
        "generated_at": datetime.now().isoformat(),
        "system_mode": "TECHNICAL_DOMINANT_WITH_DATA_CONTEXT",
        "market_state": market_state,
        "market_score": round(float(global_score), 4),
        "vix_value": float(vix_value) if vix_value is not None else None,
        "candidates": top_candidates,
        "signals": signal_results,
        "ranked": ranked,
        "decisions": decisions,
        "exit_signals": exit_decisions,
        "holding_alerts": holding_alerts,
        "technical_action_summary": technical_action_summary,
        "vix_alert": vix_alert,
        "market_guidance": market_guidance,
        "wave_swing_candidates": wave_swing_candidates,
        "satellite_watch": satellite_watch,
        "core_watch": core_watch,
        "holdings_guidance": holdings_guidance,
        "safety": {
            "advisory_only": True,
            "auto_trade": False,
            "broker_login": False
        }
    }

    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n📸 Snapshot written: {snapshot_path}")

    print("\n==============================")
    print("✅ Pipeline Done")
    print("==============================")


# =========================================
# ENTRY POINT
# =========================================

if __name__ == "__main__":
    run_pipeline(capital=100000)
