# =========================================================
# execution/risk.py
# =========================================================
# 功能：風險管理層（核心）
#
# 流程：
# 1. check_position_risk() — 檢查單筆交易是否超限
# 2. check_market_risk() — 根據市場狀況調整倉位係數
# 3. apply_risk_filters() — 對所有決策應用風險檢查
#
# 關鍵：這層會決定 RISK_FULL 還是 PASS
# =========================================================
 
import pandas as pd
 
 
# ==========================================================
# 🔧 1. 位置風險檢查（最核心）
# ==========================================================
 
def check_position_risk(portfolio, ticker, position_size, capital=100000):
    """
    檢查新交易是否超過風險限制
    
    邏輯：
    - 計算目前總倉位
    - 計算計畫新倉位
    - 檢查是否超過各項限制
    
    參數：
    - portfolio: dict {ticker: {entry_price, size}, ...}
    - ticker: 要買的股票 code
    - position_size: 計畫投入的資金比例（0.05 = 5%）
    - capital: 總資本（預設 10 萬）
    
    回傳：
    - (is_allowed: bool, reason: str, final_size: float)
    
    例子：
    >>> check_position_risk({}, "2467.TW", 0.05, 100000)
    (True, "OK", 0.05)
    
    >>> check_position_risk({"2467.TW": {...}}, "3131.TWO", 0.05, 100000)
    # 如果總倉位會超過 70%，則：
    (False, "TOTAL_EXPOSURE_EXCEED", 0)
    """
    
    # ────────────────────────────────
    # 計算目前總倉位
    # ────────────────────────────────
    current_exposure = 0
    
    for t, pos in portfolio.items():
        current_exposure += pos.get("size", 0)
    
    # ────────────────────────────────
    # 計畫的新倉位大小（元）
    # ────────────────────────────────
    planned_new_size = capital * position_size
    
    # ────────────────────────────────
    # 計算交易後的總倉位
    # ────────────────────────────────
    total_after_trade = current_exposure + planned_new_size
    
    
    # ────────────────────────────────
    # 🔒 規則 1：總倉位限制
    # ────────────────────────────────
    # 解釋：永遠不要把全部資金都投出去
    #      要保留 30% 的機動資金（應急、補倉、止損追加）
    
    MAX_TOTAL_EXPOSURE = capital * 0.70  # 最多用 70% 資本
    
    if total_after_trade > MAX_TOTAL_EXPOSURE:
        return False, "TOTAL_EXPOSURE_EXCEED", 0
    
    
    # ────────────────────────────────
    # 🔒 規則 2：單股倉位限制
    # ────────────────────────────────
    # 解釋：不要把太多雞蛋放在一個籃子裡
    #      單股最多 10%，這樣即使虧損也不會致命
    
    MAX_SINGLE_POSITION = capital * 0.10  # 單股最多 10%
    
    if planned_new_size > MAX_SINGLE_POSITION:
        # 計算最大允許的倉位比例
        adjusted_size = MAX_SINGLE_POSITION / capital
        return False, "SINGLE_POSITION_EXCEED", adjusted_size
    
    
    # ────────────────────────────────
    # 🔒 規則 3：同一產業限制（選擇性）
    # ────────────────────────────────
    # 解釋：台股 AI 股都是設備廠，產業關聯性高
    #      不要全買設備股，避免產業崩盤時全線虧損
    
    # （這個可選，暫時先不做，保持簡單）
    
    
    # ────────────────────────────────
    # ✅ 都通過了！允許進場
    # ────────────────────────────────
    
    return True, "OK", position_size
 
 
# ==========================================================
# 🌍 2. 市場風險係數（根據市場狀況調整）
# ==========================================================
 
def check_market_risk(market_state, vix_value):
    """
    根據市場狀況調整風險係數
    
    邏輯：
    - 牛市時，可以大膽一點（100% 倉位）
    - 熊市時，要保守一點（50% 倉位）
    - VIX 高時，要降低倉位（代表市場恐慌）
    
    參數：
    - market_state: "BULL" / "RANGE" / "BEAR"
    - vix_value: float（當前 VIX 值）
    
    回傳：
    - coefficient: float（0.5 到 1.2）
    
    例子：
    >>> check_market_risk("BULL", 15)
    1.0  # 可以100%執行計畫倉位
    
    >>> check_market_risk("BEAR", 35)
    0.5  # 只能50%執行計畫倉位（保守）
    """
    
    # ────────────────────────────────
    # 根據市場狀況調整
    # ────────────────────────────────
    
    market_coefficients = {
        "BULL": 1.0,    # 牛市：100% 倉位
        "RANGE": 0.85,  # 盤整：85% 倉位
        "BEAR": 0.5     # 熊市：50% 倉位（保守）
    }
    
    market_coeff = market_coefficients.get(market_state, 1.0)
    
    
    # ────────────────────────────────
    # 根據 VIX 調整
    # ────────────────────────────────
    # VIX 解釋：
    # < 15   = 市場平靜，股市看起來很安全
    # 15-30  = 正常波動
    # > 30   = 市場恐慌，很多人在拋售
    
    if vix_value is None:
        vix_coeff = 1.0
    elif vix_value < 15:
        vix_coeff = 1.0      # 低波動，可以大倉位
    elif vix_value < 30:
        vix_coeff = 0.85     # 中波動，小幅降低
    else:
        vix_coeff = 0.7      # 高波動，大幅降低（市場恐慌）
    
    
    # ────────────────────────────────
    # 綜合係數
    # ────────────────────────────────
    # 同時考慮市場狀態和 VIX
    # 例如：BULL (1.0) × VIX 高 (0.5) = 0.5
    
    combined_coeff = market_coeff * vix_coeff
    
    # 確保係數不會太低或太高
    combined_coeff = max(0.3, min(1.2, combined_coeff))
    
    return combined_coeff
 
 
# ==========================================================
# 🔐 3. 應用風險過濾（主要函數）
# ==========================================================
 
def apply_risk_filters(decisions, portfolio, capital=100000, market_state="BULL", vix_value=None):
    """
    對所有決策應用風險檢查
    
    流程：
    1. 計算市場風險係數
    2. 對每個 BUY/BUY_BREAKOUT/BUY_LATE 決策檢查
    3. 通過則允許，失敗則改為 NO_TRADE + 記錄原因
    
    參數：
    - decisions: dict {ticker: {action, position_size, ...}, ...}
    - portfolio: dict {ticker: {entry_price, size}, ...}
    - capital: int（總資本）
    - market_state: str（"BULL"/"RANGE"/"BEAR"）
    - vix_value: float（當前 VIX 值，None 則忽略）
    
    回傳：
    - filtered_decisions: dict（所有決策都通過風險檢查）
    
    【輸出格式改變】：
    之前：
        {
            "action": "BUY",
            "position_size": 0.2,
            "signal": "READY"
        }
    
    之後（如果通過）：
        {
            "action": "BUY",
            "position_size": 0.2,
            "signal": "READY",
            "risk_check": "PASS"
        }
    
    之後（如果失敗）：
        {
            "action": "NO_TRADE",
            "signal": "READY",
            "risk_check": "FAIL",
            "risk_reason": "TOTAL_EXPOSURE_EXCEED"
        }
    """
    
    # ────────────────────────────────
    # 計算市場風險係數
    # ────────────────────────────────
    market_coefficient = check_market_risk(market_state, vix_value)
    
    # 用於 DEBUG
    # print(f"[DEBUG] Market Coefficient: {market_coefficient:.2f}")
    
    
    # ────────────────────────────────
    # 對每個決策進行風險檢查
    # ────────────────────────────────
    filtered = {}
    
    for ticker, decision in decisions.items():
        
        # 🔸 如果已經是 NO_TRADE，直接跳過（不用檢查）
        if decision.get("action") == "NO_TRADE":
            filtered[ticker] = decision
            continue
        
        # 🔸 如果是 HOLD，直接跳過（不涉及新資金）
        if decision.get("action") == "HOLD":
            filtered[ticker] = decision
            continue
        
        # 🔸 如果是 SELL，直接跳過（不涉及新資金）
        if decision.get("action") == "SELL":
            filtered[ticker] = decision
            continue
        
        
        # ────────────────────────────────
        # 取得計畫的倉位大小
        # ────────────────────────────────
        position_size = decision.get("position_size", 0)
        
        
        # ────────────────────────────────
        # 應用市場係數（調整倉位大小）
        # ────────────────────────────────
        # 例如：
        # - 計畫倉位 0.05（5%）
        # - 市場係數 0.7（熊市 + VIX 高）
        # - 實際倉位 0.05 × 0.7 = 0.035（3.5%）
        
        adjusted_position_size = position_size * market_coefficient
        
        
        # ────────────────────────────────
        # 檢查風險
        # ────────────────────────────────
        is_allowed, reason, final_size = check_position_risk(
            portfolio, 
            ticker, 
            adjusted_position_size, 
            capital
        )
        
        
        # ────────────────────────────────
        # 根據檢查結果修改決策
        # ────────────────────────────────
        
        if is_allowed:
            # ✅ 通過風險檢查 → 允許進場
            decision["action"] = "BUY"
            decision["position_size"] = final_size
            decision["risk_check"] = "PASS"
            decision["market_coeff"] = round(market_coefficient, 2)
            
        elif reason == "SINGLE_POSITION_EXCEED" and final_size > 0:
            # 單股超限是可縮倉風險，不應直接拒單。
            decision["action"] = "BUY"
            decision["position_size"] = final_size
            decision["risk_check"] = "PASS_ADJUSTED"
            decision["risk_reason"] = reason
            decision["market_coeff"] = round(market_coefficient, 2)

        else:
            # ❌ 失敗風險檢查 → 拒絕進場
            decision["action"] = "NO_TRADE"
            decision["risk_check"] = "FAIL"
            decision["risk_reason"] = reason
            decision["market_coeff"] = round(market_coefficient, 2)
        
        filtered[ticker] = decision
    
    return filtered
 
 
# ==========================================================
# 📊 4. DEBUG 函數（可選，幫助理解）
# ==========================================================
 
def print_risk_summary(portfolio, capital=100000):
    """
    打印目前的倉位和風險狀況
    
    輸出：
    總資本: 100,000
    已用資金: 35,000 (35%)
    剩餘資金: 65,000 (65%)
    
    持倉：
    - 2467.TW: 15,000 (15%)
    - 3131.TWO: 20,000 (20%)
    """
    
    print("\n=== RISK SUMMARY ===")
    print(f"Total Capital: {capital:,}")
    
    total_exposure = sum(pos.get("size", 0) for pos in portfolio.values())
    used_capital = capital * total_exposure
    remaining_capital = capital - used_capital
    
    print(f"Used: {used_capital:,.0f} ({total_exposure*100:.1f}%)")
    print(f"Remaining: {remaining_capital:,.0f} ({(1-total_exposure)*100:.1f}%)")
    
    print(f"\nPositions:")
    for ticker, pos in portfolio.items():
        size = pos.get("size", 0)
        price = pos.get("entry_price", 0)
        amount = capital * size
        print(f"  - {ticker}: {amount:,.0f} ({size*100:.1f}%) @ {price:.2f}")
