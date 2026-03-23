# decision/market.py

def market_filter(score):
    """
    根據 global score 判斷市場狀態

    Parameters:
    - score (float)

    Returns:
    - str: BULL / RANGE / BEAR
    """

    if score > 0.01:
        return "BULL"

    elif score < -0.01:
        return "BEAR"

    else:
        return "RANGE"
