# decision/position_lock.py

def apply_position_lock(decisions, portfolio):
    """
    避免重複買入（Position Lock v1）

    Parameters:
    - decisions (dict)
    - portfolio (dict): 已持倉股票

    Returns:
    - locked_decisions (dict)
    """

    locked = {}

    for ticker, d in decisions.items():

        action = d.get("action")
        new_d = d.copy()

        # =========================
        # 🔒 已持倉 → 禁止 BUY
        # =========================
        if ticker in portfolio:

            if action == "BUY":
                new_d["action"] = "HOLD"
                new_d["reason"] = "ALREADY_IN_POSITION"

        locked[ticker] = new_d

    return locked
