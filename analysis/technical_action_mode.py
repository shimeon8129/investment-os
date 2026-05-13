_ACTION_LABELS = {
    "TECH_ATTACK":         "技術強攻，可進場",
    "TECH_ATTACK_CAUTION": "技術強，但不追高",
    "TECH_BUY":            "技術買進",
    "TECH_BUY_CAUTION":    "技術買進，注意分歧",
    "TECH_WATCH":          "觀察中，等待更強訊號",
    "TECH_WAIT":           "等待，條件未齊",
    "TECH_REDUCE":         "持倉減碼",
    "TECH_EXIT":           "出場，優先人工確認",
}

_SUGGESTED_ACTIONS = {
    "TECH_ATTACK":         "可依技術訊號試單，量縮不破 MA5 續持",
    "TECH_ATTACK_CAUTION": "不追高，等回測 MA5 / 量縮不破 / 盤中拉回再評估",
    "TECH_BUY":            "可試單，設停損 MA5 以下",
    "TECH_BUY_CAUTION":    "可小部位，不追價，注意籌碼或數據分歧",
    "TECH_WATCH":          "等待放量突破或回測支撐確認後再進",
    "TECH_WAIT":           "保持觀察，條件未達，暫不行動",
    "TECH_REDUCE":         "考慮減碼，確認是否跌破關鍵支撐",
    "TECH_EXIT":           "優先人工檢查是否出場，確認停損觸發",
}

_INVALID_IF = {
    "TECH_ATTACK":         ["跌破 MA5", "量縮轉弱", "level 喪失"],
    "TECH_ATTACK_CAUTION": ["跌破 MA5", "爆量後量縮轉弱", "隔日開高走低", "level lost"],
    "TECH_BUY":            ["跌破 MA5", "成交量持續萎縮", "market_state 轉 BEAR"],
    "TECH_BUY_CAUTION":    ["籌碼持續賣超", "跌破 MA5", "訊號消失"],
    "TECH_WATCH":          ["level 消失", "market_state 轉 BEAR"],
    "TECH_WAIT":           [],
    "TECH_REDUCE":         ["跌幅超過停損線", "量縮反彈假突破"],
    "TECH_EXIT":           ["已確認止損", "訊號恢復需重新評估"],
}


def classify_action_mode(
    signal: str,
    level: str,
    vol_ratio: float,
    chase_risk: str,
    chip_status: str,
    market_state: str,
    exit_signal: str = None,
) -> dict:
    """
    Classify the technical action mode for a candidate or holding.

    Args:
        signal: BUY / BUY_LATE / TREND_CONTINUE / empty
        level: ATTACK / READY / EARLY
        vol_ratio: current volume / 5-day avg volume
        chase_risk: LOW / MEDIUM / HIGH / EXTREME / UNKNOWN
        chip_status: POSITIVE / STRONG_POSITIVE / MIXED / DIVERGENCE /
                     STRONG_DIVERGENCE / STALE / MISSING / UNKNOWN
        market_state: BULL / RANGE / BEAR
        exit_signal: EXIT_ALL / REDUCE / HOLD / None

    Returns:
        dict with action_mode, action_label, suggested_action,
        technical_reasons, invalid_if
    """
    # Holdings exit overrides candidate logic
    if exit_signal in ("EXIT_ALL", "SELL"):
        action = "TECH_EXIT"
    elif exit_signal == "REDUCE":
        action = "TECH_REDUCE"
    elif signal in ("BUY", "BUY_LATE", "TREND_CONTINUE"):
        if level in ("ATTACK", "READY") and vol_ratio >= 2.0:
            if chase_risk in ("HIGH", "EXTREME"):
                action = "TECH_ATTACK_CAUTION"
            elif market_state == "BEAR":
                action = "TECH_BUY_CAUTION"
            else:
                action = "TECH_ATTACK"
        elif (
            chase_risk == "MEDIUM"
            or chip_status in ("DIVERGENCE", "STRONG_DIVERGENCE")
        ):
            action = "TECH_BUY_CAUTION"
        elif level == "READY" and chase_risk == "LOW":
            if market_state == "BEAR":
                action = "TECH_BUY_CAUTION"
            elif chip_status in ("STALE", "MISSING", "UNKNOWN"):
                action = "TECH_BUY_CAUTION"
            else:
                action = "TECH_BUY"
        elif chip_status in ("STALE", "MISSING", "UNKNOWN"):
            action = "TECH_BUY_CAUTION"
        else:
            action = "TECH_BUY"
    elif level in ("READY", "EARLY"):
        action = "TECH_WATCH"
    else:
        action = "TECH_WAIT"

    technical_reasons = [
        f"signal={signal}",
        f"level={level}",
        f"vol_ratio={round(vol_ratio, 2)}x",
        f"market_state={market_state}",
        f"chase_risk={chase_risk}",
    ]
    if chip_status not in (None, "MISSING", "UNKNOWN"):
        technical_reasons.append(f"chip_status={chip_status}")

    return {
        "action_mode": action,
        "action_label": _ACTION_LABELS.get(action, action),
        "suggested_action": _SUGGESTED_ACTIONS.get(action, ""),
        "technical_reasons": technical_reasons,
        "invalid_if": _INVALID_IF.get(action, []),
    }
