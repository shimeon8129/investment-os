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


def get_minervini_bonus(minervini_info: dict | None) -> float:
    if not minervini_info:
        return 0

    score = minervini_info.get("minervini_score", 0)
    bonus = score * 0.6

    if minervini_info.get("passed_minervini_core") is True:
        bonus += 20

    return bonus


def get_narrative_bonus(narrative_info: dict | None) -> float:
    if not narrative_info:
        return 0

    consensus_score = narrative_info.get("consensus_score", 0)
    strength = narrative_info.get("strength", "")

    bonus = consensus_score * 0.2

    if strength == "STRONG":
        bonus += 20
    elif strength == "MEDIUM":
        bonus += 10

    return bonus


def get_news_heat_bonus(news_heat_info: dict | None) -> float:
    if not news_heat_info:
        return 0

    heat_score = news_heat_info.get("heat_score", 0)
    return min(heat_score * 0.2, 20)


def get_chip_bonus(chip_info: dict | None) -> float:
    if not chip_info:
        return 0

    score = chip_info.get("chip_score", 0)
    return min(score * 0.2, 20)


def calculate_total_score(
    signal: str,
    scanner_score: float,
    sector: str,
    minervini_info: dict | None = None,
    narrative_info: dict | None = None,
    news_heat_info: dict | None = None,
    chip_info: dict | None = None,
) -> float:
    base = (
        get_signal_score(signal)
        + scanner_score * 4
        + get_sector_score(sector)
        + get_minervini_bonus(minervini_info)
        + get_narrative_bonus(narrative_info)
        + get_news_heat_bonus(news_heat_info)
        + get_chip_bonus(chip_info)
    )

    # 微分（避免同分）
    return base + (scanner_score * 0.1)


def rank_stocks(
    signal_results: list,
    scanner_results: dict,
    sector_map: dict,
    name_map: dict,
    minervini_results: dict | None = None,
    narrative_results: dict | None = None,
    news_heat_results: dict | None = None,
    chip_results: dict | None = None,
):

    ranked_list = []

    for item in signal_results:
        ticker = item["ticker"]
        signal = item["signal"]
        level = item.get("level", "UNKNOWN")   # 🔥 這行很重要

        scanner_score = scanner_results.get(ticker, 0)
        sector = sector_map.get(ticker, "UNKNOWN")
        name = name_map.get(ticker, "UNKNOWN")
        minervini_info = (minervini_results or {}).get(ticker)
        narrative_info = (narrative_results or {}).get(ticker)
        news_heat_info = (news_heat_results or {}).get(ticker)
        chip_info = (chip_results or {}).get(ticker)

        total_score = (
            calculate_total_score(
                signal,
                scanner_score,
                sector,
                minervini_info,
                narrative_info,
                news_heat_info,
                chip_info,
            )
            + get_level_score(level)   # 🔥 關鍵
        )

        ranked_list.append({
            "ticker": ticker,
            "name": name,
            "sector": sector,
            "signal": signal,
            "level": level,
            "scanner_score": scanner_score,
            "minervini_score": (minervini_info or {}).get("minervini_score", 0),
            "passed_minervini_core": (minervini_info or {}).get("passed_minervini_core", False),
            "narrative_score": (narrative_info or {}).get("consensus_score", 0),
            "narrative_strength": (narrative_info or {}).get("strength", "NONE"),
            "narrative_count": (narrative_info or {}).get("consensus_count", 0),
            "narrative_bonus": get_narrative_bonus(narrative_info),
            "news_heat_score": (news_heat_info or {}).get("heat_score", 0),
            "news_count": (news_heat_info or {}).get("news_count", 0),
            "source_count": (news_heat_info or {}).get("source_count", 0),
            "news_heat_bonus": get_news_heat_bonus(news_heat_info),
            "chip_score": (chip_info or {}).get("chip_score", 0),
            "institutional_bias": (chip_info or {}).get("institutional_bias", "NONE"),
            "foreign_net_buy": (chip_info or {}).get("foreign_net_buy", 0),
            "trust_net_buy": (chip_info or {}).get("trust_net_buy", 0),
            "dealer_net_buy": (chip_info or {}).get("dealer_net_buy", 0),
            "institutional_net_buy": (chip_info or {}).get("institutional_net_buy", 0),
            "chip_bonus": get_chip_bonus(chip_info),
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
            f"   Minervini: {stock['minervini_score']} | "
            f"Narrative: {stock['narrative_strength']} {stock['narrative_score']} "
            f"(count={stock['narrative_count']}) | "
            f"NewsHeat: {stock['news_heat_score']} "
            f"(news={stock['news_count']}, sources={stock['source_count']}) | "
            f"Chips: {stock['chip_score']} {stock['institutional_bias']} "
            f"(total={stock['institutional_net_buy']:,})\n"
        )
