# =========================================================
# decision/lock.py (v2 - 改進版)
# =========================================================
# 功能：根據市場狀態調整交易決策
#
# 改動：
# 1. RANGE 市場允許進場（倉位減半）
# 2. 加入 VIX 參數用於更精細控制
# 3. 不要過度鎖定，給予交易機會
# =========================================================

def apply_market_lock(decisions, market_state, vix_value=None):
    """
    根據市場狀態調整交易決策
    
    參數：
    - decisions (dict): 決策字典
    - market_state (str): "BULL" / "RANGE" / "BEAR"
    - vix_value (float): VIX 值（選擇性）
    
    邏輯：
    ─────────────────────────────────────────────────────
    市場狀態 | VIX   | 決策      | 倉位調整
    ─────────────────────────────────────────────────────
    BULL    | <15   | BUY 允許  | 100%
    BULL    | 15-30 | BUY 允許  | 100%
    BULL    | >30   | BUY 允許  | 80%
    ─────────────────────────────────────────────────────
    RANGE   | <20   | BUY 允許  | 80%
    RANGE   | 20-30 | BUY 允許  | 60%（減半）
    RANGE   | >30   | BUY 允許  | 50%（縮小）
    ─────────────────────────────────────────────────────
    BEAR    | <30   | BUY 禁止  | -
    BEAR    | >30   | BUY 禁止  | -
    ─────────────────────────────────────────────────────
    
    說明：
    - BEAR 市場：完全禁止進場（保護資本）
    - RANGE 市場：允許進場，但倉位縮小（降低風險）
    - BULL 市場：正常進場（可小幅調整 VIX）
    """

    locked = {}

    for ticker, d in decisions.items():
        action = d.get("action")
        
        # 預設複製
        new_d = d.copy()

        # ═══════════════════════════════════════════════
        # 🔴 BEAR 市場 → 禁止所有 BUY
        # ═══════════════════════════════════════════════
        # 說明：熊市時，風險太高，保護資本優先
        
        if market_state == "BEAR":
            if action == "BUY":
                new_d["action"] = "NO_TRADE"
                new_d["reason"] = "LOCKED_BY_MARKET"
                new_d["reason_detail"] = "BEAR market - capital protection"

        # ═══════════════════════════════════════════════
        # 🟡 RANGE 市場 → 允許進場，但倉位縮小
        # ═══════════════════════════════════════════════
        # 說明：盤整時，不確定性高，但仍有機會
        #      倉位根據 VIX 調整：VIX 越高，倉位越小
        
        elif market_state == "RANGE":
            if action == "BUY":
                # 原始倉位
                original_size = d.get("position_size", 0)
                
                # 根據 VIX 調整係數
                if vix_value is None:
                    vix_coeff = 0.8  # VIX 不知道時，保守一點
                elif vix_value < 20:
                    vix_coeff = 0.8  # VIX 低：80% 倉位
                elif vix_value < 30:
                    vix_coeff = 0.5  # VIX 中：50% 倉位（減半）
                else:
                    vix_coeff = 0.4  # VIX 高：40% 倉位（大幅縮小）
                
                # 應用係數
                new_d["position_size"] = original_size * vix_coeff
                new_d["reason"] = "REDUCED_BY_MARKET"
                new_d["reason_detail"] = f"RANGE market - VIX {vix_value:.1f}" if vix_value else "RANGE market"

        # ═══════════════════════════════════════════════
        # 🟢 BULL 市場 → 正常進場
        # ═══════════════════════════════════════════════
        # 說明：牛市時，風險較低，允許正常倉位
        #      VIX 很高時小幅調整
        
        elif market_state == "BULL":
            if action == "BUY":
                original_size = d.get("position_size", 0)
                
                # 即使在牛市，VIX 超高也要小心
                if vix_value and vix_value > 35:
                    vix_coeff = 0.9  # VIX 很高時，90% 倉位（輕微調整）
                else:
                    vix_coeff = 1.0  # 正常倉位
                
                new_d["position_size"] = original_size * vix_coeff
                new_d["reason"] = "NORMAL"

        locked[ticker] = new_d

    return locked


# =========================================================
# 【使用範例】
# =========================================================
"""
決策 + Lock 的完整流程：

1. execute_trade() 生成初始決策
   决策: {"2467.TW": {"action": "BUY", "position_size": 0.08}}

2. apply_market_lock() 根據市場調整
   - 如果 RANGE 市場 + VIX 30.78
   - 倉位被調整為 0.08 × 0.4 = 0.032（3.2%）

3. apply_position_lock() 檢查現有持倉

4. apply_risk_filters() 最後檢查資金管理

【最終決策】
- 如果倉位調整到 0.032，通常能通過後續檢查
- 最後進場時，倉位就是 3.2%

關鍵：不要禁止交易，而是調整倉位大小
"""
