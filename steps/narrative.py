import random

def analyze_narrative(data):

    text = (data["title"] + " " + data["content"]).lower()

    # 🧠 topic 判斷（簡單版）
    if "ai" in text or "nvidia" in text:
        topic = "AI"
    elif "tsmc" in text or "台積電" in text:
        topic = "TSMC"
    elif "dram" in text or "memory" in text:
        topic = "Memory"
    else:
        topic = "Other"

    # 🧠 sentiment（隨機模擬）
    sentiment = random.choice(["positive", "neutral", "negative"])

    # 🧠 strength（依情緒）
    if sentiment == "positive":
        strength = random.randint(70, 90)
    elif sentiment == "negative":
        strength = random.randint(10, 40)
    else:
        strength = random.randint(40, 60)

    return {
        "topic": topic,
        "sentiment": sentiment,
        "strength": strength,
        "summary": "mock generated"
    }
