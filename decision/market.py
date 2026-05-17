# =========================================================
# decision/market.py (v2 - 改進版)
# =========================================================
# 功能：根據市場表現判斷市場狀態
#
# 改動：
# 1. 調整 BEAR 市場判斷門檻（從 -0.02 改為 -0.05）
# 2. 加入 VIX 參考，不只看價格
# 3. BEAR 市場需要同時滿足多個條件
# =========================================================

def market_filter(global_score, vix_value=None):
    """
    根據市場表現判斷市場狀態
    
    參數：
    - global_score: float（美股日報酬率平均，通常 -0.05 到 +0.05）
    - vix_value: float（VIX 指數，通常 10-40+）
    
    回傳：
    - market_state: str ("BULL" / "RANGE" / "BEAR")
    
    邏輯：
    ─────────────────────────────────────────────────────
    global_score  | VIX      | 判斷
    ─────────────────────────────────────────────────────
    > 0.01        | <20      | BULL（強勢）
    > 0.01        | 20-30    | BULL（仍看好）
    > 0.01        | >30      | RANGE（分歧）
    
    -0.01~0.01    | <30      | RANGE（盤整）
    -0.01~0.01    | >30      | RANGE（盤整+恐慌）
    
    < -0.01       | <20      | RANGE（技術走弱）
    < -0.01       | 20-30    | RANGE（觀望）
    < -0.05       | >30      | BEAR（確認下跌）
    ─────────────────────────────────────────────────────
    
    重點：
    - 不要過度反應單日漲跌
    - global_score = -0.0206 不算 BEAR（只是小幅下跌）
    - 需要 < -0.05 + VIX > 30 才判定 BEAR
    """

    # ═══════════════════════════════════════════════════
    # 🔴 BEAR 市場判斷（嚴格條件）
    # ═══════════════════════════════════════════════════
    # 條件 1：美股連續大幅下跌（-5% 以上）
    # 條件 2：恐慌指標 VIX > 30
    # 兩者同時滿足才判定 BEAR
    
    if global_score < -0.05:
        # 美股大幅下跌
        if vix_value is None or vix_value > 30:
            # 且 VIX 高（或沒有 VIX 資訊時保守判斷）
            return "BEAR"
    
    # ═══════════════════════════════════════════════════
    # 🟢 BULL 市場判斷
    # ═══════════════════════════════════════════════════
    # 條件：美股上漲 + VIX 平穩
    
    if global_score > 0.01:
        # 美股明顯上漲
        if vix_value is None or vix_value < 30:
            # VIX 不高
            return "BULL"
        else:
            # 即使美股上漲，VIX 也很高（分歧情況）
            return "RANGE"
    
    # ═══════════════════════════════════════════════════
    # 🟡 RANGE 市場判斷（預設）
    # ═══════════════════════════════════════════════════
    # 其他所有情況都算盤整
    
    return "RANGE"


def get_vix_alert(vix_value) -> str:
    """
    Returns VIX alert level independent of market_state.
    NORMAL < 20 | ELEVATED 20-25 | HIGH 25-30 | EXTREME >= 30
    """
    if vix_value is None:
        return "UNKNOWN"
    if vix_value >= 30:
        return "EXTREME"
    if vix_value >= 25:
        return "HIGH"
    if vix_value >= 20:
        return "ELEVATED"
    return "NORMAL"


def get_market_guidance(market_state: str, vix_alert: str) -> dict:
    """
    Returns actionable guidance based on market_state + vix_alert.
    Keys: summary, new_entry_ok, role_filter, holding_action
    """
    if market_state == "BEAR":
        return {
            "summary": "市場確認下跌，優先處理持倉，不建議新進場",
            "new_entry_ok": False,
            "role_filter": [],
            "holding_action": "評估所有持倉出場或停損位置，CORE 確認是否結構損壞",
        }
    if vix_alert == "EXTREME":
        return {
            "summary": "VIX 極度恐慌，暫緩新進場，專注持倉管理",
            "new_entry_ok": False,
            "role_filter": [],
            "holding_action": "持倉觀察，避免恐慌出場，確認各部位停損位是否守住",
        }
    if vix_alert == "HIGH":
        return {
            "summary": "VIX 偏高，謹慎操作，僅 WAVE_SWING 短線機會可小量試單",
            "new_entry_ok": True,
            "role_filter": ["WAVE_SWING"],
            "holding_action": "WAVE_SWING 持倉緊守 MA5，SATELLITE/CORE 持續持有",
        }
    if market_state == "BULL":
        return {
            "summary": "市場強勢，三類角色均可依訊號操作",
            "new_entry_ok": True,
            "role_filter": ["WAVE_SWING", "SATELLITE", "CORE"],
            "holding_action": "持倉續持，趨勢未損不輕易減碼",
        }
    # RANGE + NORMAL/ELEVATED
    return {
        "summary": "市場盤整，精選進場，優先有量有籌碼的 WAVE_SWING 標的",
        "new_entry_ok": True,
        "role_filter": ["WAVE_SWING", "SATELLITE"],
        "holding_action": "依角色停損邏輯持有，CORE 不因短線波動減碼",
    }


# ═══════════════════════════════════════════════════════
# 【使用範例】
# ═══════════════════════════════════════════════════════

"""
範例 1：昨天的情況
global_score = -0.0042（小幅下跌）
vix_value = 30.78（VIX 高）

判斷：
- global_score > -0.05 ✓（不符合 BEAR 條件）
- 回傳：RANGE

決策：允許進場，但倉位縮小


範例 2：今天的情況
global_score = -0.0206（略低）
vix_value = 30.41（VIX 高）

判斷：
- global_score > -0.05 ✓（不符合 BEAR 條件）
- 回傳：RANGE

決策：應該也是 RANGE，不是 BEAR


【為什麼會判斷成 BEAR？】

可能是你的 market_filter() 邏輯不同
檢查你的 decision/market.py 裡的判斷門檻：

❌ 錯誤：
    if global_score < -0.01:
        return "BEAR"  # 太敏感！

✅ 正確：
    if global_score < -0.05:
        return "BEAR"  # 只有大幅下跌才算
"""
