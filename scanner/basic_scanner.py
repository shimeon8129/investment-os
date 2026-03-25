# scanner/basic_scanner.py


def scan_candidates(close, volume, features):

    ma20 = features["ma20"]
    vol_ratio = features["vol_ratio"]
    ret_1d = features["return_1d"]

    equipment_list = [
        "2467.TW", "3131.TWO", "3583.TW",
        "5443.TWO", "6139.TW", "2464.TW", "3413.TW"
    ]

    candidates = []

    for col in close.columns:

        try:
            latest_close = close[col].iloc[-1]

            ma5 = close[col].rolling(5).mean().iloc[-1]
            ma10 = close[col].rolling(10).mean().iloc[-1]
            ma20_val = ma20[col].iloc[-1]

            recent_low = close[col].rolling(20).min().iloc[-1]
            recent_high = close[col].rolling(20).max().iloc[-1]

            latest_vol = vol_ratio[col].iloc[-1]
            latest_ret = ret_1d[col].iloc[-1]

            # =========================
            # 🎯 行為判斷（拆開🔥）
            # =========================

            rebound = latest_close > recent_low * 1.05
            ma10_break = latest_close > ma10
            near_high = latest_close > recent_high * 0.92
            breakout = latest_close >= recent_high * 0.99

            momentum_ok = latest_ret > 0
            vol_expand = latest_vol > 1.3
            vol_normal = latest_vol > 1.0

            trend_ok = latest_close > ma20_val * 0.98

            sector_boost = 1 if col in equipment_list else 0

            # =========================
            # 🧠 Score（影響排序）
            # =========================

            score = (
                rebound * 2 +
                ma10_break * 2 +
                near_high * 1 +
                momentum_ok * 1 +
                vol_normal * 1 +
                trend_ok * 1 +
                sector_boost * 1
            )

            # =========================
            # 🔥 分級（核心改這裡）
            # =========================

            # === ATTACK（真的在噴）===
            if breakout and vol_expand:
                level = "ATTACK"

            # === READY（最重要🔥）===
            elif (
                ma10_break
                and near_high
                and momentum_ok
                and vol_normal
            ):
                level = "READY"

            # === EARLY（底部轉強）===
            elif rebound and trend_ok:
                level = "EARLY"

            else:
                continue  # 不要垃圾

            # =========================
            # 📦 收集
            # =========================

            candidates.append({
                "ticker": col,
                "score": score,
                "level": level,
                "price": latest_close
            })

        except Exception:
            continue

    # 排序（高分在前）
    candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)

    return candidates
