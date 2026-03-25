# pipeline/ranking_engine.py


def get_signal_score(signal: str) -> int:
    if signal == "BUY":
        return 50
    elif signal == "BUY_LATE":
        return 25
    elif signal == "TREND_CONTINUE":
        return 30
    else:
        return 0


def get_sector_score(sector: str) -> int:
    STRONG_SECTORS = ["Equipment"]
    if sector in STRONG_SECTORS:
        return 20
    else:
        return 10


# 🔥 新增：level 分數（核心）
def get_level_score(level: str) -> int:
    if level == "READY":
        return 40   # 最重要（起飛前）
    elif level == "EARLY":
        return 30   # 潛力
    elif level == "ATTACK":
        return 10   # 已經漲（降低）
    else:
        return 0


def calculate_total_score(signal: str, scanner_score: float, sector: str) -> float:
    base = (
        get_signal_score(signal)
        + scanner_score * 4
        + get_sector_score(sector)
    )

    # 微分（避免同分）
    return base + (scanner_score * 0.1)


def rank_stocks(signal_results: list, scanner_results: dict, sector_map: dict, name_map: dict):

    ranked_list = []

    for item in signal_results:
        ticker = item["ticker"]
        signal = item["signal"]
        level = item.get("level", "UNKNOWN")   # 🔥 這行很重要

        scanner_score = scanner_results.get(ticker, 0)
        sector = sector_map.get(ticker, "UNKNOWN")
        name = name_map.get(ticker, "UNKNOWN")

        total_score = (
            calculate_total_score(signal, scanner_score, sector)
            + get_level_score(level)   # 🔥 關鍵
        )

        ranked_list.append({
            "ticker": ticker,
            "name": name,
            "sector": sector,
            "signal": signal,
            "level": level,
            "scanner_score": scanner_score,
            "score": total_score
        })

    ranked_list.sort(key=lambda x: x["score"], reverse=True)

    return ranked_list


def print_top_picks(ranked_list, top_n=3):
    print("\n=== TOP PICKS ===\n")

    for i, stock in enumerate(ranked_list[:top_n], start=1):
        print(
            f"#{i} {stock['ticker']} {stock['name']} ({stock['sector']})\n"
            f"   Score: {stock['score']:.1f} | Signal: {stock['signal']} | Level: {stock['level']}\n"
        )
