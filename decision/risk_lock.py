# decision/risk_lock.py

def apply_risk_lock(decisions, portfolio, max_total_position=0.5):

    locked = {}

    # =========================
    # 🧠 計算目前倉位
    # =========================
    current_position = sum(p["size"] for p in portfolio.values())

    for ticker, d in decisions.items():

        action = d.get("action")
        signal = d.get("signal", "")
        new_d = d.copy()

        if action == "BUY":

            new_size = d.get("position_size", 0)

            # =========================
            # 🔴 超過倉位 → 不直接砍（改成縮倉🔥）
            # =========================
            if current_position + new_size > max_total_position:

                # 👉 嘗試縮到一半
                reduced_size = new_size / 2

                if current_position + reduced_size <= max_total_position:
                    new_d["position_size"] = reduced_size
                    new_d["reason"] = "REDUCED_BY_RISK"
                    current_position += reduced_size

                else:
                    # 👉 再縮更小（極小試單）
                    micro_size = 0.02

                    if current_position + micro_size <= max_total_position:
                        new_d["position_size"] = micro_size
                        new_d["reason"] = "MICRO_POSITION"
                        current_position += micro_size

                    else:
                        new_d["action"] = "NO_TRADE"
                        new_d["reason"] = "RISK_FULL"

            else:
                current_position += new_size

        locked[ticker] = new_d

    return locked
