import json
import os


def classify_roles():

    # =========================
    # 📥 讀取資料
    # =========================
    try:
        with open("data/narrative_raw/latest.json", "r", encoding="utf-8") as f:
            narrative = json.load(f)
    except:
        print("❌ 找不到 narrative 資料")
        return

    try:
        with open("data/candidates.json", "r", encoding="utf-8") as f:
            candidates = json.load(f)
    except:
        print("❌ 找不到 candidates 資料")
        return

    # =========================
    # 🧠 Leader 定義（可擴充）
    # =========================
    leader_list = [
        "2330.TW",  # 台積電
        "3680.TWO", # 家登
        "2308.TW",  # 台達電（電力/散熱）
    ]

    # =========================
    # 🔥 建立 narrative map
    # =========================
    narrative_map = {
        n["ticker"]: n for n in narrative
    }

    results = []

    for c in candidates:

        ticker = c["ticker"]

        if ticker not in narrative_map:
            continue

        n = narrative_map[ticker]

        score = n.get("narrative_score", 0)
        strength = n.get("narrative_strength", "LOW")

        # =========================
        # 🎯 分類邏輯（核心🔥）
        # =========================

        # 🥇 Leader（龍頭）
        if ticker in leader_list:
            role = "LEADER"

        # 🥈 Core（主攻🔥）
        elif score >= 85 and strength == "HIGH":
            role = "CORE"

        # 🥉 Lag（補漲）
        elif score >= 70:
            role = "LAG"

        else:
            continue

        results.append({
            "ticker": ticker,
            "role": role,
            "score": score,
            "theme": n.get("theme", ""),
            "summary": n.get("summary", "")
        })

    # =========================
    # 排序（Core優先）
    # =========================
    priority = {"CORE": 3, "LEADER": 2, "LAG": 1}

    results = sorted(
        results,
        key=lambda x: (priority[x["role"]], x["score"]),
        reverse=True
    )

    # =========================
    # 📦 存檔
    # =========================
    os.makedirs("data", exist_ok=True)

    with open("data/final_narrative.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # =========================
    # 🖥️ 顯示
    # =========================
    print("\n=== FINAL NARRATIVE ===")

    for r in results:
        print(f"{r['ticker']} | {r['role']} | score={r['score']} | {r['theme']}")

    print("\n✅ final_narrative.json 已產生")


if __name__ == "__main__":
    classify_roles()
