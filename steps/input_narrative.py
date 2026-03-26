# =========================================================
# steps/input_narrative.py
# =========================================================
# 功能：
# 👉 依序輸入 3 個 AI（Gemini / Claude / Perplexity）
# 👉 存成對應檔案
# 👉 同時寫入 log
#
# 輸出：
# data/narrative_raw/
# ├── gemini.json
# ├── claude.json
# ├── perplexity.json
# └── log.txt
# =========================================================


import json
import os
from datetime import datetime


def read_json_input(ai_name):

    print("\n==============================")
    print(f"👉 現在請輸入：{ai_name} 的資料")
    print("👉 貼 JSON，最後輸入 [apply]")
    print("👉 若無資料，輸入 [no data]")
    print("==============================\n")

    lines = []

    while True:
        line = input()
        cmd = line.strip().lower()

        if cmd == "[apply]":
            break

        if cmd == "[no data]":
            return "NO_DATA", None

        lines.append(line)

    raw_text = "\n".join(lines).strip()

    try:
        start = raw_text.index("[")
        end = raw_text.rindex("]") + 1
        clean_text = raw_text[start:end]
    except:
        print("❌ 找不到 JSON 區塊")
        return None, None

    try:
        data = json.loads(clean_text)
        return data, raw_text
    except Exception as e:
        print("❌ JSON 解析失敗")
        print(e)
        return None, None


def save_json(data, filename):

    os.makedirs("data/narrative_raw", exist_ok=True)
    path = f"data/narrative_raw/{filename}"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ 已寫入 {path}")


def write_log(ai_name, raw_text, status):

    log_path = "data/narrative_raw/log.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(log_path, "a", encoding="utf-8") as f:
        f.write("\n==============================\n")
        f.write(f"{timestamp} | {ai_name} | {status}\n")
        f.write("==============================\n")

        if raw_text:
            f.write(raw_text + "\n")

    print("📝 log 已記錄")


def run_input():

    ai_list = ["gemini", "claude", "perplexity"]
    success_count = 0

    for ai in ai_list:

        while True:
            result, raw_text = read_json_input(ai)

            if result == "NO_DATA":
                write_log(ai, None, "NO_DATA")
                print(f"⚠️ {ai} 無資料，已略過\n")
                break

            elif result is not None:
                save_json(result, f"{ai}.json")
                write_log(ai, raw_text, "OK")
                success_count += 1
                break

            else:
                print("⚠️ 請重新貼上正確 JSON 或輸入 [no data]\n")

    print("\n==============================")
    print("🎉 輸入完成")
    print(f"👉 成功資料數：{success_count}/3")
    print("==============================\n")

    if success_count >= 2:
        print("👉 可以執行：python3 steps/consensus.py\n")
    else:
        print("⚠️ 資料不足（至少需要2個AI）\n")


if __name__ == "__main__":
    run_input()
