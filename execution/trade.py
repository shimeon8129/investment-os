# execution/trade.py

def execute_trade(signals, capital=100000):
    """
    根據 signal 決定交易動作

    Returns:
    dict: 每檔股票的動作
    """

    decisions = {}

    for ticker, signal in signals.items():

        if signal == "BUY_BREAKOUT":
            decisions[ticker] = {
                "action": "BUY",
                "position_size": 0.3,   # 30%
                "stop_loss": 0.05       # -5%
            }

        elif signal == "BUY_LATE":
            decisions[ticker] = {
                "action": "BUY",
                "position_size": 0.15,  # 小倉
                "stop_loss": 0.05
            }

        elif signal == "TREND_CONTINUE":
            decisions[ticker] = {
                "action": "HOLD"
            }

        else:
            decisions[ticker] = {
                "action": "NO_TRADE"
            }

    return decisions
