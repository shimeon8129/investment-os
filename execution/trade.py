# execution/trade.py

def execute_trade(signals, capital=100000):
    """
    根據 signal 決定交易動作（v3：支援 READY → BUY）
    """

    decisions = {}

    for ticker, signal in signals.items():

        # =====================================
        # 🔥 1. READY → 主倉（最重要）
        # =====================================
        if signal == "BUY":
            decisions[ticker] = {
                "action": "BUY",
                "position_size": 0.2,   # 🔥 主倉
                "stop_loss": 0.05,
                "signal": signal
            }

        # =====================================
        # 🔥 2. BREAKOUT
        # =====================================
        elif signal == "BUY_BREAKOUT":
            decisions[ticker] = {
                "action": "BUY",
                "position_size": 0.3,
                "stop_loss": 0.05,
                "signal": signal
            }

        # =====================================
        # 🔥 3. LATE ENTRY（追高 → 小倉）
        # =====================================
        elif signal == "BUY_LATE":
            decisions[ticker] = {
                "action": "BUY",
                "position_size": 0.1,
                "stop_loss": 0.05,
                "signal": signal
            }

        # =====================================
        # 🟡 4. TREND
        # =====================================
        elif signal == "TREND_CONTINUE":
            decisions[ticker] = {
                "action": "HOLD",
                "signal": signal
            }

        # =====================================
        # ❌ 5. NO SIGNAL
        # =====================================
        else:
            decisions[ticker] = {
                "action": "NO_TRADE",
                "signal": signal
            }

    return decisions
