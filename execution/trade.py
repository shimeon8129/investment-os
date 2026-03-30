# =========================================================
# execution/trade.py (v2 - 改進版)
# =========================================================
# 功能：根據訊號決定交易動作
#
# 改動：
# 1. 新增 READY_PULLBACK 訊號識別
# 2. 新增 TREND_CONTINUE → BUY_SMALL 邏輯（選擇性）
# 3. 完整註解說明倉位大小邏輯
# =========================================================

def execute_trade(signals, market_state="BULL", capital=100000):
    """
    根據 signal 決定交易動作
    
    參數：
    - signals: dict {ticker: signal_string, ...}
    - market_state: str ("BULL" / "RANGE" / "BEAR")
    - capital: int (總資本，預設 10 萬)
    
    回傳：
    - decisions: dict {
        ticker: {
            "action": "BUY" / "HOLD" / "NO_TRADE",
            "position_size": float (0.0 - 1.0),
            "stop_loss": float (0.0 - 1.0),
            "signal": str
        }
    }
    
    訊號對應關係：
    ─────────────────────────────────────────────────
    訊號             | 動作    | 倉位  | 說明
    ─────────────────────────────────────────────────
    BUY              | BUY     | 20%   | 標準進場
    BUY_BREAKOUT     | BUY     | 30%   | 破位突破，激進進場
    BUY_LATE         | BUY     | 10%   | 追高進場，保守
    READY_PULLBACK   | BUY     | 8%    | 回檔買點，小倉位
    TREND_CONTINUE   | HOLD    | -     | 繼續持有，暫不進場
    (其他)           | NO_TRADE| -     | 沒有訊號
    ─────────────────────────────────────────────────
    """

    decisions = {}

    for ticker, signal in signals.items():

        # =====================================
        # 🔥 1. BUY（主倉）
        # =====================================
        if signal == "BUY":
            decisions[ticker] = {
                "action": "BUY",
                "position_size": 0.2,   # 20% —— 標準倉位
                "stop_loss": 0.05,      # 5% 停損
                "signal": signal
            }

        # =====================================
        # 🔥 2. BUY_BREAKOUT（激進倉）
        # =====================================
        elif signal == "BUY_BREAKOUT":
            decisions[ticker] = {
                "action": "BUY",
                "position_size": 0.3,   # 30% —— 大倉位（激進）
                "stop_loss": 0.05,      # 5% 停損
                "signal": signal
            }

        # =====================================
        # 🔥 3. BUY_LATE（追高倉）
        # =====================================
        elif signal == "BUY_LATE":
            decisions[ticker] = {
                "action": "BUY",
                "position_size": 0.1,   # 10% —— 小倉位（保守）
                "stop_loss": 0.05,      # 5% 停損
                "signal": signal
            }

        # =====================================
        # 🔥 4. READY_PULLBACK（新增！回檔倉）
        # =====================================
        # 說明：
        # - READY_PULLBACK 表示股票技術面良好，但目前是回檔狀態
        # - 這是比較安全的進場點（不是追高）
        # - 倉位設定為 8% —— 小倉位，因為風險不確定
        # - 停損設定為 5% —— 標準停損
        elif signal == "READY_PULLBACK":
            decisions[ticker] = {
                "action": "BUY",
                "position_size": 0.08,  # 8% —— 小倉位（安全進場）
                "stop_loss": 0.05,      # 5% 停損
                "signal": signal
            }

        # =====================================
        # 🟡 5. TREND_CONTINUE（持有狀態）
        # =====================================
        # 說明：
        # - TREND_CONTINUE 表示目前在上升趨勢中
        # - 如果已經持倉，就繼續持有
        # - 如果還沒持倉，就 HOLD（等待更好的進場點）
        elif signal == "TREND_CONTINUE":
            decisions[ticker] = {
                "action": "HOLD",       # 不進場，只持有
                "signal": signal
            }

        # =====================================
        # ❌ 6. NO SIGNAL（沒有訊號）
        # =====================================
        else:
            decisions[ticker] = {
                "action": "NO_TRADE",
                "signal": signal
            }

    return decisions


# =========================================================
# 【使用範例】
# =========================================================
"""
signals = {
    "2467.TW": "READY_PULLBACK",
    "6640.TWO": "TREND_CONTINUE",
    "6147.TWO": "TREND_CONTINUE"
}

decisions = execute_trade(signals)

# 輸出：
# {
#     "2467.TW": {
#         "action": "BUY",
#         "position_size": 0.08,
#         "stop_loss": 0.05,
#         "signal": "READY_PULLBACK"
#     },
#     "6640.TWO": {
#         "action": "HOLD",
#         "signal": "TREND_CONTINUE"
#     },
#     "6147.TWO": {
#         "action": "HOLD",
#         "signal": "TREND_CONTINUE"
#     }
# }
"""
