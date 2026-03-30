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
import json

def load_pool(pool_type="universe"):

    if pool_type == "watchlist":
        with open("data/watchlist.json", "r") as f:
            data = json.load(f)
        tickers = [x["ticker"] for x in data]

    else:
        import pandas as pd
        df = pd.read_csv("data/universe_tw.csv")
        tickers = df["ticker"].tolist()

    return tickers


try:
    from scanner.pre_scanner import run_pre_scanner
except ImportError:
    from pre_scanner import run_pre_scanner

import json
import os


def scan_candidates(close, volume, features):

    import pandas as pd

    # 🔥 讀 universe（用來 mapping name）
    df = pd.read_csv("data/universe_tw.csv")
    name_map = dict(zip(df["ticker"], df["name"]))

    pre_list = run_pre_scanner()

    ma20 = features["ma20"]
    vol_ratio = features["vol_ratio"]
    ret_1d = features["return_1d"]

    equipment_list = [
        "2467.TW", "3131.TWO", "3583.TW",
        "5443.TWO", "6139.TW", "2464.TW", "3413.TW"
    ]

    candidates = []

    for col in close.columns:

        if col not in pre_list:
            continue

        try:
            latest_close = close[col].iloc[-1]

            ma10 = close[col].rolling(10).mean().iloc[-1]
            ma20_val = ma20[col].iloc[-1]

            recent_low = close[col].rolling(20).min().iloc[-1]
            recent_high = close[col].rolling(20).max().iloc[-1]

            latest_vol = vol_ratio[col].iloc[-1]
            latest_ret = ret_1d[col].iloc[-1]

            rebound = latest_close > recent_low * 1.05
            ma10_break = latest_close > ma10
            near_high = latest_close > recent_high * 0.92
            breakout = latest_close >= recent_high * 0.99

            momentum_ok = latest_ret > 0
            vol_expand = latest_vol > 1.3
            vol_normal = latest_vol > 1.0

            trend_ok = latest_close > ma20_val * 0.98

            sector_boost = 1 if col in equipment_list else 0

            score = (
                rebound * 2 +
                ma10_break * 2 +
                near_high * 1 +
                momentum_ok * 1 +
                vol_normal * 1 +
                trend_ok * 1 +
                sector_boost * 1
            )

            if breakout and vol_expand:
                level = "ATTACK"
            elif ma10_break and near_high and momentum_ok and vol_normal:
                level = "READY"
            elif rebound and trend_ok:
                level = "EARLY"
            else:
                continue

            candidates.append({
                "ticker": col,
                "name": name_map.get(col, col),
                "score": score,
                "level": level,
                "price": float(latest_close)
            })

        except:
            continue

    candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)
    candidates = candidates[:15]

    export_data = [
        {"ticker": c["ticker"], "name": c["name"]}
        for c in candidates
    ]

    os.makedirs("data", exist_ok=True)

    with open("data/candidates.json", "w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    print("\n=== PRE-SCANNER ===")
    print(f"Selected {len(pre_list)} stocks")

    print("\n=== CANDIDATES ===")
    for c in candidates:
        print(f"{c['ticker']} {c['name']} | {c['level']} | score={c['score']}")

    stock_lines = [
        f"{c['ticker']} {c['name']}"
        for c in candidates
    ]

    prompt = f"""

請分析以下股票的「AI供應鏈敘事強度」（針對AI半導體/AI伺服器/先進封裝）
[
  {{
    "ticker": "...",
    "name": "...",
    "narrative_score": 0-100,
    "narrative_strength": "HIGH/MID/LOW",
    "theme": "...",
    "summary": "...",
    "confidence": 0-100
  }}
]

規則：
- 嚴格依照 ticker 對應公司名稱
- 不可自行替換公司名稱
- 不確定請略過
- 不要解釋
- 不要新聞連結
- 只輸出JSON

股票：
{stock_lines}
"""

    print("\n===== AI PROMPT =====\n")
    print(prompt)

    return candidates


if __name__ == "__main__":

    print("🚀 Running Scanner...")

    import pandas as pd
    from data_node.loader import load_price_data
    import sys
#    df = pd.read_csv("data/universe_tw.csv")
#    tickers = df["ticker"].tolist()

    pool = "universe"
    if len(sys.argv) > 1:
        pool = sys.argv[1]

    tickers = load_pool(pool)

    close, volume = load_price_data(tickers, period="3mo")

    features = {
        "ma20": close.rolling(20).mean(),
        "vol_ratio": volume / volume.rolling(20).mean(),
        "return_1d": close.pct_change()
    }

    scan_candidates(close, volume, features)
