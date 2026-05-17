# decision/entry_safety_gate.py
# P0 Hotfix + P0.1 corrections: Entry Safety Gate

_SENTINEL = object()  # distinguish "key absent" from falsy values


def _downgrade(candidate: dict, action_mode: str, action_label: str,
               suggested_action: str, reason: str) -> dict:
    """Return candidate with updated action fields and downgrade_reasons."""
    reasons = list(candidate.get("downgrade_reasons", []))
    reasons.append(reason)
    return {
        **candidate,
        "action_mode": action_mode,
        "action_label": action_label,
        "suggested_action": suggested_action,
        "downgrade_reasons": reasons,
    }


def apply_entry_safety_gate(candidate: dict, market_state: str = "",
                             market_score: float = 0.0) -> dict:
    """
    Entry Safety Gate — hard-block 不安全的進場條件。

    執行順序（P0.1）:
    0. is_held         → POSITION_MANAGE_ONLY（最優先，無論其他條件）
    1. missing fields  → DATA_INCOMPLETE_REVIEW
    2. market_state    → RANGE + market_score < 0 阻止全力買入
    3. vol_ratio       → < 1.0 → WATCH_READY
    4. chip_status     → 分歧/負面 → WATCH_READY
    5. chase_risk      → HIGH/EXTREME → NO_FRESH_ENTRY_EXTENDED
    """

    is_held = candidate.get("is_held", False)

    # === Block 0: Held Ticker（最高優先，任何其他條件前先判斷）===
    if is_held:
        return _downgrade(
            candidate,
            action_mode="POSITION_MANAGE_ONLY",
            action_label="持倉管理",
            suggested_action="已持倉，只做倉位調整，不開新倉",
            reason="ticker_already_held",
        )

    # === Block 1: Missing Critical Fields ===
    vol_ratio_raw = candidate.get("vol_ratio", _SENTINEL)
    chip_status_raw = candidate.get("chip_status", _SENTINEL)
    chase_risk_raw = candidate.get("chase_risk", _SENTINEL)

    missing = []
    if vol_ratio_raw is _SENTINEL:
        missing.append("vol_ratio")
    if chip_status_raw is _SENTINEL:
        missing.append("chip_status")
    if chase_risk_raw is _SENTINEL:
        missing.append("chase_risk")

    if missing:
        return _downgrade(
            candidate,
            action_mode="DATA_INCOMPLETE_REVIEW",
            action_label="資料不完整",
            suggested_action=f"缺少欄位：{', '.join(missing)}，請先補齊資料再評估",
            reason=f"missing_fields={','.join(missing)}",
        )

    vol_ratio: float = vol_ratio_raw
    chip_status: str = chip_status_raw
    chase_risk: str = chase_risk_raw

    # === Block 2: Market State ===
    ms = (market_state or "").upper()
    if "RANGE" in ms and market_score < 0:
        return _downgrade(
            candidate,
            action_mode="WATCH_MARKET",
            action_label="市場觀望",
            suggested_action="盤整偏空（RANGE + score<0），暫不開新倉，等待市場方向確認",
            reason=f"market_state=RANGE,market_score={market_score:.4f}<0",
        )

    # === Block 3: Volume ===
    if vol_ratio < 1.0:
        return _downgrade(
            candidate,
            action_mode="WATCH_READY",
            action_label="量能不足觀察",
            suggested_action=f"量比 {vol_ratio:.2f}x 未達 1.0，等待放量再評估",
            reason=f"vol_ratio={vol_ratio:.2f}<1.0",
        )

    # === Block 4: Chip Status ===
    if chip_status in ("DIVERGENCE", "STRONG_DIVERGENCE", "STRONG_NEGATIVE"):
        return _downgrade(
            candidate,
            action_mode="WATCH_READY",
            action_label="籌碼分歧觀察",
            suggested_action=f"籌碼狀態 {chip_status}，法人分歧或偏空，暫緩進場",
            reason=f"chip_status={chip_status}",
        )

    # === Block 5: Chase Risk ===
    if chase_risk in ("HIGH", "EXTREME"):
        return _downgrade(
            candidate,
            action_mode="NO_FRESH_ENTRY_EXTENDED",
            action_label="追價風險過高",
            suggested_action=f"追價風險 {chase_risk}，股價偏離均線過遠，不宜追入",
            reason=f"chase_risk={chase_risk}",
        )

    # === 通過所有 checks ===
    return {
        **candidate,
        "downgrade_reasons": candidate.get("downgrade_reasons", []),
        "gate_passed": True,
    }
