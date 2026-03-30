# =========================================================
# scanner/basic_scanner.py
# =========================================================
# 說明：
# 這個檔案負責完成 Step1：
# 👉 根據 universe 掃描股票
# 👉 產出 candidates.json（系統用）
# 👉 同時印出 AI prompt（給你直接丟AI用）
#
# 執行方式（固定）：
# python3 scanner/basic_scanner.py
#
# 流程：
# 1. 讀取 universe（股票清單）
# 2. 產生測試用價格資料（目前階段）
# 3. Pre-scanner 篩選範圍
# 4. Scanner 判斷強弱（EARLY / READY / ATTACK）
# 5. 輸出：
#    - data/candidates.json
#    - 畫面上的 AI prompt
# =========================================================

# from scanner.pre_scanner import run_pre_scanner
# from pre_scanner import run_pre_scanner

import os
import json
import sys
import pandas as pd
from data_node.loader import load_price_data


def load_pool(pool):
    if pool == "watchlist":
        df = pd.read_csv("data/universe_tw.csv")
    else:
        df = pd.read_csv("data/universe_tw.csv")
    return df["ticker"].tolist()


def scan_candidates(close, volume):

    candidates = []

    for ticker in close.columns:

        try:
            price = close[ticker].iloc[-1]
            ma20 = close[ticker].rolling(20).mean().iloc[-1]
            vol_ratio = volume[ticker].iloc[-1] / volume[ticker].rolling(20).mean().iloc[-1]

            score = 0

            if price > ma20:
                score += 1
            if vol_ratio > 1:
                score += 1

            if score >= 2:
                level = "READY"
            else:
                level = "EARLY"

            candidates.append({
                "ticker": ticker,
                "name": ticker,
                "score": score,
                "level": level,
                "price": float(price)
            })

        except:
            continue

    print(f"\n✅ Candidates: {len(candidates)}")

    os.makedirs("data", exist_ok=True)
    with open("data/candidates.json", "w") as f:
        json.dump(candidates, f, indent=2)

    return candidates


if name == "__main__":

    pool = "universe"
    if len(sys.argv) > 1:
        pool = sys.argv[1]

    tickers = load_pool(pool)

    close, volume = load_price_data(tickers, period="3mo")

    scan_candidates(close, volume)
