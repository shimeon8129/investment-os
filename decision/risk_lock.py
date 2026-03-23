# decision/risk_lock.py

def apply_risk_lock(decisions, portfolio, max_total_position=0.5):
    """
    控制總倉位（Risk Lock v1）

    Parameters:
    - decisions (dict)
    - portfolio (dict)
    - max_total_position (float): 最大總倉位

    Returns:
    - locked_decisions (dict)
    """

    locked = {}

    # =========================
    # 🧠 計算目前已持倉
    # =========================
    current_position = sum(p["size"] for p in portfolio.values())

    for ticker, d in decisions.items():

        action = d.get("action")
        new_d = d.copy()

        if action == "BUY":

            new_size = d.get("position_size", 0)

            # =========================
            # 🔴 超過總倉位 → 禁止
            # =========================
            if current_position + new_size > max_total_position:
                new_d["action"] = "NO_TRADE"
                new_d["reason"] = "RISK_LIMIT_EXCEEDED"

            else:
                # 🟢 可以買 → 更新模擬倉位
                current_position += new_size

        locked[ticker] = new_d

    return locked
