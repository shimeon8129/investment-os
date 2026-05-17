# decision/entry_safety_gate.py
# P0 Hotfix: 最小 Entry Safety Gate — 在 ranking 前 hard-block 不安全的進場條件


def apply_entry_safety_gate(candidate: dict) -> dict:
    """
    最小安全 gate — 檢查 4 個 hard block 條件。

    Hard blocks（絕對阻止 fresh BUY）:
    1. vol_ratio < 1.0       → 量能不足
    2. chip_status 分歧/負面  → 籌碼空方
    3. chase_risk HIGH/EXTREME → 追價風險過高
    4. is_held = True        → 已持倉，只做倉位管理
    """

    vol_ratio = candidate.get("vol_ratio", 1.0)
    chip_status = candidate.get("chip_status", "NEUTRAL")
    chase_risk = candidate.get("chase_risk", "MEDIUM")
    is_held = candidate.get("is_held", False)

    downgrade_reasons: list[str] = []
    final_action = candidate.get("action_mode", "WATCH")

    # === Hard Block 1: Volume ===
    if vol_ratio < 1.0:
        downgrade_reasons.append(f"vol_ratio={vol_ratio:.2f}<1.0")
        final_action = "WATCH_READY"
        return {**candidate, "action_mode": final_action, "downgrade_reasons": downgrade_reasons}

    # === Hard Block 2: Chip Status ===
    if chip_status in ("DIVERGENCE", "STRONG_DIVERGENCE", "STRONG_NEGATIVE"):
        downgrade_reasons.append(f"chip_status={chip_status}")
        final_action = "WATCH_READY"
        return {**candidate, "action_mode": final_action, "downgrade_reasons": downgrade_reasons}

    # === Hard Block 3: Chase Risk ===
    if chase_risk in ("HIGH", "EXTREME"):
        downgrade_reasons.append(f"chase_risk={chase_risk}")
        final_action = "NO_FRESH_ENTRY_EXTENDED"
        return {**candidate, "action_mode": final_action, "downgrade_reasons": downgrade_reasons}

    # === Hard Block 4: Held Ticker ===
    if is_held:
        downgrade_reasons.append("ticker_already_held")
        final_action = "POSITION_MANAGE_ONLY"
        return {**candidate, "action_mode": final_action, "downgrade_reasons": downgrade_reasons}

    # === 通過所有 checks ===
    return {**candidate, "action_mode": final_action, "downgrade_reasons": downgrade_reasons, "gate_passed": True}
