# =========================================================
# steps/consensus.py (FINAL with name + fault tolerance + log)
# =========================================================

import json
import os
from collections import defaultdict
from datetime import datetime
import pandas as pd


# =========================
# 載入名稱對照
# =========================
def load_name_map():

    df = pd.read_csv("data/universe_tw.csv")
    return dict(zip(df["ticker"], df["name"]))


# =========================
# 載入 AI 資料
# =========================
def load_narratives():

    base_path = "data/narrative_raw"
    ai_files = ["gemini.json", "claude.json", "perplexity.json"]

    narratives = []
    used_ai = []

    for f in ai_files:
        path = os.path.join(base_path, f)

        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)
                narratives.append(data)
                used_ai.append(f.replace(".json", ""))

    return narratives, used_ai


# =========================
# 共識計算
# =========================
def build_consensus(narratives, name_map):

    pool = defaultdict(list)

    for ai_data in narratives:
        for item in ai_data:

            score = item.get("narrative_score", 0)

            if score < 70:
                continue

            ticker = item["ticker"]
            pool[ticker].append(score)

    results = []

    for ticker, scores in pool.items():

        count = len(scores)

        if count < 2:
            continue

        avg_score = sum(scores) / count

        if count >= 3 and avg_score >= 80:
            strength = "STRONG"
        elif count >= 2 and avg_score >= 80:
            strength = "MEDIUM"
        else:
            continue

        results.append({
            "ticker": ticker,
            "name": name_map.get(ticker, "UNKNOWN"),
            "consensus_score": round(avg_score, 2),
            "consensus_count": count,
            "strength": strength
        })

    results = sorted(results, key=lambda x: x["consensus_score"], reverse=True)

    return results


# =========================
# 存檔 + log
# =========================
def save_result(results, used_ai):

    os.makedirs("data", exist_ok=True)

    path = "data/final_narrative.json"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # log
    log_path = "data/narrative_raw/log.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(log_path, "a", encoding="utf-8") as f:
        f.write("\n==============================\n")
        f.write(f"{timestamp} | CONSENSUS | used={used_ai}\n")
        f.write("==============================\n")
        f.write(json.dumps(results, ensure_ascii=False, indent=2))
        f.write("\n")

    print("\n✅ final_narrative.json 已產生\n")

    print("=== CONSENSUS RESULT ===")
    for r in results:
        print(f"{r['ticker']} | {r['name']} | {r['strength']} | score={r['consensus_score']} | count={r['consensus_count']}")


# =========================
# 主程式
# =========================
if __name__ == "__main__":

    print("🚀 Running Consensus Engine...")

    narratives, used_ai = load_narratives()

    if len(narratives) < 2:
        print("❌ 至少需要2個AI資料")
        exit()

    name_map = load_name_map()

    results = build_consensus(narratives, name_map)

    if len(results) == 0:
        print("⚠️ 沒有符合共識條件的標的")
        exit()

    save_result(results, used_ai)
