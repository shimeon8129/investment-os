from steps.narrative import analyze_narrative

def run_pipeline(data):

    clean = data

    narratives = []

    # 每筆資料分析
    for item in clean:
        result = analyze_narrative(item)
        narratives.append(result)

    # 🔥 Topic Aggregation v1
    topic_map = {}

    for n in narratives:
        topic = n["topic"]

        if topic not in topic_map:
            topic_map[topic] = {
                "total_strength": 0,
                "count": 0,
                "positive": 0,
                "negative": 0
            }

        topic_map[topic]["total_strength"] += n["strength"]
        topic_map[topic]["count"] += 1

        if n["sentiment"] == "positive":
            topic_map[topic]["positive"] += 1
        elif n["sentiment"] == "negative":
            topic_map[topic]["negative"] += 1

    topic_signal = {}

    for topic, data in topic_map.items():

        avg_strength = data["total_strength"] / data["count"]

        if data["positive"] > data["negative"]:
            trend = "UP"
        elif data["negative"] > data["positive"]:
            trend = "DOWN"
        else:
            trend = "NEUTRAL"

        topic_signal[topic] = {
            "score": int(avg_strength),
            "trend": trend
        }

    # 🔥 Market Map（排序）
    market_map = []

    for topic, data in topic_signal.items():
        market_map.append({
            "topic": topic,
            "score": data["score"],
            "trend": data["trend"]
        })

    market_map = sorted(market_map, key=lambda x: x["score"], reverse=True)

    # 最終 signal
    signal = {
        "topic_signal": topic_signal,
        "market_map": market_map,
        "confidence": "MEDIUM"
    }

    return {
        "narrative": narratives,
        "signal": signal
    }
