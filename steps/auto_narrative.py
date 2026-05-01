# =========================================================
# steps/auto_narrative.py
# Automated AI Narrative — calls Claude API 3x with
# different analysis perspectives to simulate multi-AI
# consensus input (claude.json, gemini.json, perplexity.json)
# =========================================================

import json
import os
import sys
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.groq_agent import call_groq_narrative


PERSPECTIVES = [
    ("claude",     "主流敘事（AI供應鏈熱度 + 近期新聞）"),
    ("gemini",     "資金面（外資法人動向 + 籌碼集中度）"),
    ("perplexity", "產業鏈位置（上下游連動 + 訂單能見度）"),
]


def load_candidates() -> list[dict]:
    path = "data/candidates.json"
    if not os.path.exists(path):
        raise FileNotFoundError("data/candidates.json not found — run scanner first")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_name_map() -> dict:
    df = pd.read_csv("data/universe_tw.csv")
    return dict(zip(df["ticker"], df["name"]))


def save_narrative(data: list, ai_name: str):
    os.makedirs("data/narrative_raw", exist_ok=True)
    path = f"data/narrative_raw/{ai_name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✅ saved → {path}")


def write_log(ai_name: str, status: str):
    log_path = "data/narrative_raw/log.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*30}\n")
        f.write(f"{timestamp} | {ai_name} | {status}\n")
        f.write(f"{'='*30}\n")


def run_auto_narrative():
    print("🤖 Running Auto Narrative (Gemini API × 3 perspectives)...\n")

    candidates = load_candidates()
    name_map = load_name_map()

    tickers_with_names = [
        {"ticker": c["ticker"], "name": name_map.get(c["ticker"], c["ticker"])}
        for c in candidates
    ]

    print(f"📋 Tickers to analyse: {len(tickers_with_names)}\n")

    success = 0

    for ai_name, perspective in PERSPECTIVES:
        print(f"🧠 [{ai_name}] perspective: {perspective}")
        try:
            result = call_groq_narrative(tickers_with_names, perspective)
            save_narrative(result, ai_name)
            write_log(ai_name, "OK")
            success += 1

            for r in result:
                score = r.get("narrative_score", 0)
                if score >= 70:
                    print(f"    {r['ticker']} {r['name']} | score={score} | {r.get('theme','')}")

        except Exception as e:
            print(f"  ❌ {ai_name} failed: {e}")
            write_log(ai_name, f"ERROR: {e}")

        print()

    print(f"{'='*30}")
    print(f"✅ Done — {success}/3 perspectives completed")

    if success >= 2:
        print("👉 Run next: python3 steps/consensus.py")
    else:
        print("⚠️  Need at least 2 successful perspectives for consensus")


if __name__ == "__main__":
    run_auto_narrative()
