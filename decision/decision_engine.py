# =========================================================
# decision/decision_engine.py
# FINAL VERSION（含 Entry + Lock）
# =========================================================

import json
import os

from data_node.loader import load_price_data
from decision.entry_engine import generate_entry_signal
from decision.entry_lock import apply_entry_lock


# =========================
# 載入 candidates（Scanner 輸出）
# =========================
def load_candidates():

    path = "data/candidates.json"

    if not os.path.exists(path):
        print("❌ candidates.json 不存在")
        return []

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


# =========================
# 主流程
# =========================
def run_decision():

    print("🚀 Running Decision Engine...")

    # =========================================
    # 1️⃣ Load Candidates
    # =========================================
    candidates = load_candidates()

    if not candidates:
        print("❌ 無 candidates")
        return

    tickers = [c["ticker"] for c in candidates]
    name_map = {c["ticker"]: c.get("name", c["ticker"]) for c in candidates}

    # =========================================
    # 2️⃣ Load Market Data
    # =========================================
    print("\n📡 Loading market data...")

    close, volume = load_price_data(tickers)

    # =========================================
    # 3️⃣ Entry Signal
    # =========================================
    entry_signals = generate_entry_signal(close, volume)
    from decision.entry_tracker import track_entry_transition

    from decision.ready_predictor import predict_ready_breakout

    ready_prediction = predict_ready_breakout(close, volume, entry_signals)

    print("\n=== READY PREDICTION ===")

    for r in ready_prediction:
        print(f"{r['ticker']} | {r['level']} | score={r['score']} | price={r['price']}")

    transition = track_entry_transition(entry_signals)

    print("\n=== ENTRY TRANSITION ===")

    print("\n🔥 BREAKOUT (READY → BUY)")
    for t in transition["breakout"]:
        print(t)

    print("\n👀 STILL READY")
    for t in transition["still_ready"]:
        print(t)

    print("\n❌ FAILED")
    for t in transition["failed"]:
        print(t)


    print("\n=== ENTRY SIGNAL ===")
    for e in entry_signals:
        if e["signal"]:
            name = name_map.get(e["ticker"], "")
            print(f"{e['ticker']} {name} | {e['signal']} | price={e['price']}")

    # =========================================
    # 4️⃣ Entry Lock（🔥核心）
    # =========================================
    entry_decisions = apply_entry_lock(close, volume, entry_signals)

    print("\n=== ENTRY DECISION ===")
    for d in entry_decisions:
        name = name_map.get(d["ticker"], "")
        print(f"{d['ticker']} {name} | {d['decision']} | price={d['price']}")

    # =========================================
    # 5️⃣ 分類
    # =========================================
    buy_list = []
    watch_list = []

    for d in entry_decisions:

        if d["decision"] == "BUY":
            buy_list.append(d)

        elif d["decision"] == "BUY_PARTIAL":
            watch_list.append(d)

    # =========================================
    # 6️⃣ 輸出 JSON
    # =========================================
    result = {
        "buy": buy_list,
        "watch": watch_list
    }

    os.makedirs("data", exist_ok=True)

    with open("data/decision.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("\n✅ decision.json 已產生")

    # =========================================
    # 7️⃣ 顯示結果
    # =========================================
    print("\n=== BUY LIST ===")
    for b in buy_list:
        name = name_map.get(b["ticker"], "")
        print(f"{b['ticker']} {name} | price={b['price']}")

    print("\n=== WATCH LIST ===")
    for w in watch_list:
        name = name_map.get(w["ticker"], "")
        print(f"{w['ticker']} {name} | price={w['price']}")


# =========================
# 主程式
# =========================
if __name__ == "__main__":

    run_decision()
