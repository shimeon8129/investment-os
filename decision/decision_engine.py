# =========================================================
# decision/decision_engine.py (FINAL - real data version)
# =========================================================
# 功能：
# 👉 讀取 AI 共識（final_narrative.json）
# 👉 接真實市場資料（loader）
# 👉 技術面過濾（breakout / trend）
# 👉 輸出 decision.json（買 / 觀察）
# =========================================================

import json
import os
import pandas as pd

from data_node.loader import load_price_data


# =========================
# 載入 AI 共識
# =========================
def load_narrative():

    path = "data/final_narrative.json"

    if not os.path.exists(path):
        print("❌ 找不到 final_narrative.json")
        return None

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# =========================
# 載入股票名稱
# =========================
def load_name_map():

    df = pd.read_csv("data/universe_tw.csv")
    return dict(zip(df["ticker"], df["name"]))


# =========================
# 技術判斷（核心）
# =========================
def technical_filter(close, ticker):

    if ticker not in close.columns:
        return "IGNORE"

    price = close[ticker].dropna()

    # ❌ 資料不足
    if len(price) < 25:
        return "IGNORE"

    ma20 = price.rolling(20).mean().iloc[-1]
    ma10 = price.rolling(10).mean().iloc[-1]

    latest = price.iloc[-1]
    recent_high = price.rolling(20).max().iloc[-1]

    breakout = latest >= recent_high * 0.99
    trend_ok = latest > ma20
    momentum = latest > ma10

    # =========================
    # B策略（敘事 + 技術）
    # =========================
    if breakout and trend_ok and momentum:
        return "BUY"

    elif trend_ok:
        return "WATCH"

    else:
        return "IGNORE"


# =========================
# 決策引擎
# =========================
def run_decision():

    data = load_narrative()

    if data is None:
        return

    name_map = load_name_map()

    # 👉 取共識標的
    tickers = [d["ticker"] for d in data]

    print("\n📡 Loading market data...")
    close, volume = load_price_data(tickers, period="3mo")

    buy_list = []
    watch_list = []

    print("\n=== DECISION ===")

    for item in data:

        ticker = item["ticker"]
        name = name_map.get(ticker, "UNKNOWN")
        strength = item["strength"]

        if strength not in ["STRONG", "MEDIUM"]:
            continue

        decision = technical_filter(close, ticker)

        print(f"{ticker} | {name} | {strength} → {decision}")

        if decision == "BUY":
            buy_list.append({
                "ticker": ticker,
                "name": name,
                "score": item["consensus_score"]
            })

        elif decision == "WATCH":
            watch_list.append({
                "ticker": ticker,
                "name": name,
                "score": item["consensus_score"]
            })

    # =========================
    # 輸出結果
    # =========================
    result = {
        "buy": buy_list,
        "watch": watch_list
    }

    os.makedirs("data", exist_ok=True)

    with open("data/decision.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("\n✅ decision.json 已產生")

    print("\n=== BUY LIST ===")
    for b in buy_list:
        print(f"{b['ticker']} | {b['name']} | score={b['score']}")

    print("\n=== WATCH LIST ===")
    for w in watch_list:
        print(f"{w['ticker']} | {w['name']} | score={w['score']}")


# =========================
# 主程式
# =========================
if __name__ == "__main__":

    print("🚀 Running Decision Engine...")

    run_decision()
