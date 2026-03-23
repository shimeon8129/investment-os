# execution/exit.py

def check_exit(position, current_price, ma5, highest_price):
    """
    進階出場系統（含 trailing stop）

    position:
        {
            "entry_price": float,
            "size": float
        }
    """

    entry_price = position["entry_price"]

    pnl = (current_price - entry_price) / entry_price

    # 🔴 1. Stop Loss（防死）
    if pnl <= -0.05:
        return "EXIT_ALL"

    # 🟡 2. Trailing Stop（鎖利）
    drawdown = (current_price - highest_price) / highest_price

    if drawdown <= -0.07:
        return "EXIT_ALL"

    # 🟠 3. 跌破 MA5（轉弱）
    if current_price < ma5:
        return "REDUCE"

    # 🟢 4. 強勢持有
    return "HOLD"
