# steps/theme_leader.py

import json
import os
from collections import Counter


def detect_main_theme(narrative):
    """
    從 narrative 中找出主流 theme（多數決）
    """
    themes = []

    for n in narrative:
        theme = n.get("theme", "")
        if theme:
            # 支援 "CoWoS/AI" 這種格式
            parts = [t.strip() for t in theme.split("/")]
            themes.extend(parts)

    if not themes:
        return None

    theme_count = Counter(themes)
    main_theme = theme_count.most_common(1)[0][0]

    return main_theme


def get_leader_by_theme(theme):
    """
    根據主題回傳 Leader 清單
    """

    theme_map = {

        # =========================
        # 🔥 CoWoS / Advanced Packaging
        # =========================
        "CoWoS": [
            "3680.TWO",  # 家登
            "2467.TW",   # 志聖
            "6187.TWO",  # 萬潤
            "3131.TWO",  # 弘塑
        ],

        "Advanced Packaging": [
            "3680.TWO",
            "3711.TW",   # 日月光
        ],

        # =========================
        # ⚡️ Power
        # =========================
        "Power": [
            "2308.TW",  # 台達電
            "2301.TW",  # 光寶科
        ],

        # =========================
        # ❄️ Cooling
        # =========================
        "Cooling": [
            "3017.TW",  # 奇鋐
            "3324.TW",  # 雙鴻
        ],

        # =========================
        # 🖥 AI Server
        # =========================
        "AI Server": [
            "2382.TW",  # 廣達
            "3231.TW",  # 緯創
            "2317.TW",  # 鴻海
        ],

        # =========================
        # 🧠 Foundry
        # =========================
        "Foundry": [
            "2330.TW",
        ],

        # =========================
        # 🧠 Chip Design
        # =========================
        "AI": [
            "2454.TW",  # 聯發科
            "3661.TW",  # 世芯
        ]
    }

    return theme_map.get(theme, [])


def run_theme_leader():

    # =========================
    # 📥 讀 narrative
    # =========================
    try:
        with open("data/narrative_raw/latest.json", "r", encoding="utf-8") as f:
            narrative = json.load(f)
    except:
        print("❌ 找不到 narrative")
        return

    # =========================
    # 🧠 找主題
    # =========================
    main_theme = detect_main_theme(narrative)

    if not main_theme:
        print("❌ 無法判斷主題")
        return

    # =========================
    # 🎯 對應 Leader
    # =========================
    leaders = get_leader_by_theme(main_theme)

    # =========================
    # 📦 輸出
    # =========================
    output = {
        "main_theme": main_theme,
        "leaders": leaders
    }

    os.makedirs("data", exist_ok=True)

    with open("data/theme_leader.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # =========================
    # 🖥️ 顯示
    # =========================
    print("\n=== THEME DETECTED ===")
    print(f"Theme: {main_theme}")

    print("\n=== ACTIVE LEADERS ===")
    for l in leaders:
        print(l)

    print("\n✅ theme_leader.json 已產生")


if __name__ == "__main__":
    run_theme_leader()
