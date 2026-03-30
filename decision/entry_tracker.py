# =========================================================
# decision/entry_tracker.py
# =========================================================

import json
import os

TRACK_FILE = "data/ready_tracker.json"


# =========================
# 載入歷史 READY
# =========================
def load_tracker():

    if not os.path.exists(TRACK_FILE):
        return {}

    with open(TRACK_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# =========================
# 儲存
# =========================
def save_tracker(data):

    os.makedirs("data", exist_ok=True)

    with open(TRACK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# =========================
# 核心邏輯
# =========================
def track_entry_transition(entry_signals):

    tracker = load_tracker()

    results = []

    current_ready = set()
    current_buy = set()

    for e in entry_signals:

        ticker = e["ticker"]
        signal = e["signal"]

        if signal == "READY":
            current_ready.add(ticker)

        elif signal == "BUY":
            current_buy.add(ticker)

    prev_ready = set(tracker.get("ready", []))

    # =========================
    # 🔥 轉強（重點）
    # =========================
    breakout = current_buy & prev_ready

    # =========================
    # 👀 還在準備
    # =========================
    still_ready = current_ready

    # =========================
    # ❌ 失敗
    # =========================
    failed = prev_ready - current_ready - current_buy

    # 更新 tracker
    tracker["ready"] = list(current_ready)

    save_tracker(tracker)

    return {
        "breakout": list(breakout),
        "still_ready": list(still_ready),
        "failed": list(failed)
    }
