# scanner/pre_scanner.py

import pandas as pd


def run_pre_scanner():

    # =========================
    # 📥 讀 Universe
    # =========================
    try:
        df = pd.read_csv("data/universe_tw.csv")
    except:
        print("❌ 找不到 universe_tw.csv")
        return []

    # =========================
    # 🔥 Role 篩選（放這裡）
    # =========================
    if "role" in df.columns:
        df = df[df["role"] != "LAG"]

    # =========================
    # 🎯 基本篩選（降噪）
    # =========================
    if "market_cap" in df.columns:
        df = df[df["market_cap"] > 50]

    if "volume" in df.columns:
        df = df[df["volume"] > 1000]

    # =========================
    # 限制數量
    # =========================
    df = df.head(50)

    tickers = df["ticker"].tolist()

    print("\n=== PRE-SCANNER ===")
    print(f"Selected {len(tickers)} stocks")

    return tickers
