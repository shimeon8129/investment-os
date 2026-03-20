import yfinance as yf
import pandas as pd
import requests
import json
import os

# ===== CONFIG =====
TOKEN = "8315568434:AAE4uY5t-rvqJHb9UIuuUS-73lpj305aoNw"
CHAT_ID = "7934011157"
STATE_FILE = "alert_state.json"

# ===== STATE =====
def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# ===== DATA =====
def get_data(ticker):
    df = yf.download(ticker, period="3mo", interval="1d")

    if df.empty:
        return None

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.rename(columns={"Close": "price", "Volume": "volume"})

    df["ma20"] = df["price"].rolling(20).mean()
    df["avg_volume20"] = df["volume"].rolling(20).mean()
    df["high20"] = df["price"].rolling(20).max()

    latest = df.iloc[-1]

    return {
        "ticker": ticker,
        "price": float(latest["price"]),
        "volume": float(latest["volume"]),
        "ma20": float(latest["ma20"]),
        "avg_volume20": float(latest["avg_volume20"]),
        "high20": float(latest["high20"])
    }

# ===== SIGNAL =====
def generate_signal(data):
    volume_ratio = data["volume"] / data["avg_volume20"]
    trend_ratio = data["price"] / data["ma20"]
    breakout_gap = data["price"] - data["high20"]

    score = round(volume_ratio + trend_ratio, 2)

    return {
        "ticker": data["ticker"],
        "price": round(data["price"], 2),
        "volume_ratio": round(volume_ratio, 2),
        "trend_ratio": round(trend_ratio, 2),
        "breakout_gap": round(breakout_gap, 2),
        "score": score
    }

# ===== SIGNAL TYPE =====
def get_signal_type(s):
    if s["breakout_gap"] >= 0 and s["volume_ratio"] > 1.2:
        return "✅ ENTRY"
    elif s["breakout_gap"] > -2:
        return "🔥 READY"
    else:
        return ""

# ===== TELEGRAM =====
def send_telegram(msg):
    print("📤 SEND:", msg)

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": msg
    }

    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram Error:", e)

# ===== MAIN =====
if __name__ == "__main__":

    tickers = [
        "NVDA", "AMD", "AVGO", "MU", "INTC",
        "TSM", "ASML", "AMAT", "LRCX", "KLAC",
        "SMH", "SOXX",
        "QCOM", "MRVL", "TXN",
        "ANET", "DELL", "HPQ"
    ]

    state = load_state()
    results = []

    for t in tickers:
        try:
            data = get_data(t)
            if data:
                signal = generate_signal(data)
                results.append(signal)
        except:
            continue

    ranked = sorted(results, key=lambda x: x["score"], reverse=True)

    print("\n=== RANKING ===")

    for r in ranked:
        ticker = r["ticker"]
        signal_type = get_signal_type(r)

        print(f'{ticker} | score:{r["score"]} | gap:{r["breakout_gap"]} {signal_type}')

        prev_signal = state.get(ticker, "")

        if signal_type != "" and signal_type != prev_signal:
            msg = f'{ticker} | {signal_type} | price:{r["price"]}'
            send_telegram(msg)
            state[ticker] = signal_type

    save_state(state)

    print("\n=== OPPORTUNITIES ===")
    for r in ranked:
        if r["breakout_gap"] > -5:
            print(f'{r["ticker"]} | gap:{r["breakout_gap"]}')
