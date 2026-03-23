# decision/lock.py

def apply_market_lock(decisions, market_state):
    """
    根據市場狀態調整交易決策（Lock v1）

    Parameters:
    - decisions (dict)
    - market_state (str): BULL / RANGE / BEAR

    Returns:
    - locked_decisions (dict)
    """

    locked = {}

    for ticker, d in decisions.items():

        action = d.get("action")

        # 預設複製
        new_d = d.copy()

        # =========================
        # 🔴 BEAR → 禁止所有 BUY
        # =========================
        if market_state == "BEAR":
            if action == "BUY":
                new_d["action"] = "NO_TRADE"
                new_d["reason"] = "LOCKED_BY_MARKET"

        # =========================
        # 🟡 RANGE → 降低倉位
        # =========================
        elif market_state == "RANGE":
            if action == "BUY":
                size = d.get("position_size", 0)
                new_d["position_size"] = size * 0.5  # 倉位減半
                new_d["reason"] = "REDUCED_BY_MARKET"

        # =========================
        # 🟢 BULL → 不動
        # =========================

        locked[ticker] = new_d

    return locked
