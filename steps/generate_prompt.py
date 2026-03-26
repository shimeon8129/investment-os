# steps/generate_prompt.py

import json


def generate_prompt():

    try:
        with open("data/candidates.json", "r", encoding="utf-8") as f:
            candidates = json.load(f)
    except:
        print("❌ 找不到 candidates.json")
        return

    # =========================
    # 🎯 整理 ticker list
    # =========================
    ticker_list = [c["ticker"] for c in candidates]

    # =========================
    # 🧠 Prompt Template
    # =========================
    prompt = f"""
請根據以下股票清單，分析「AI供應鏈敘事強度」

輸出 JSON，格式如下：

[
  {{
    "ticker": "...",
    "name": "...",
    "narrative_score": 0-100,
    "narrative_strength": "HIGH / MID / LOW",
    "theme": "...",
    "summary": "...",
    "confidence": 0-100
  }}
]

規則：
- 不要提供新聞連結
- 不要解釋
- 只輸出 JSON
- narrative_score 根據市場熱度 + 新聞 + 資金敘事判斷

股票清單：
{ticker_list}
"""

    # =========================
    # 📦 輸出 prompt.txt
    # =========================
    with open("data/prompt.txt", "w", encoding="utf-8") as f:
        f.write(prompt)

    print("✅ prompt.txt 已產生")


if __name__ == "__main__":
    generate_prompt()
