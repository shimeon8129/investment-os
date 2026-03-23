# data_node/loader.py

import yfinance as yf
import pandas as pd


def load_price_data(tickers, period="1mo"):
    """
    穩定版資料載入（支援 US + TW + 指數🔥）

    ✔ 單檔失敗不影響整體
    ✔ 自動處理 Series / DataFrame / MultiIndex
    ✔ 過濾壞資料
    ✔ 自動對齊時間
    ✔ 印出成功載入 ticker
    """

    close_dict = {}
    volume_dict = {}

    for ticker in tickers:
        try:
            df = yf.download(
                ticker,
                period=period,
                interval="1d",
                auto_adjust=True,
                progress=False
            )

            # ❌ 無資料
            if df.empty:
                print(f"❌ {ticker} 無資料")
                continue

            # ❌ 沒有必要欄位
            if "Close" not in df or "Volume" not in df:
                print(f"❌ {ticker} 欄位缺失")
                continue

            # ❌ 資料太短
            if len(df) < 5:
                print(f"❌ {ticker} 資料不足")
                continue

            # =========================================
            # 🧠 關鍵：統一格式（核心修正🔥）
            # =========================================

            close_data = df["Close"]
            volume_data = df["Volume"]

            # 👉 如果是 DataFrame（MultiIndex）→ 取第一欄
            if isinstance(close_data, pd.DataFrame):
                close_series = close_data.iloc[:, 0]
            else:
                close_series = close_data

            if isinstance(volume_data, pd.DataFrame):
                volume_series = volume_data.iloc[:, 0]
            else:
                volume_series = volume_data

            # ❌ 最後保險（避免奇怪格式）
            if not isinstance(close_series, pd.Series):
                print(f"❌ {ticker} 格式異常")
                continue

            close_dict[ticker] = close_series
            volume_dict[ticker] = volume_series

            print(f"✔ {ticker} loaded")

        except Exception as e:
            print(f"❌ {ticker} 下載失敗: {e}")
            continue

    # ❌ 全部失敗
    if not close_dict:
        raise ValueError("❌ 所有 ticker 都下載失敗")

    # =========================================
    # 🧠 組 DataFrame（自動對齊時間）
    # =========================================

    close = pd.DataFrame(close_dict)
    volume = pd.DataFrame(volume_dict)

    # =========================================
    # 🧹 清理資料（關鍵🔥）
    # =========================================

    # 移除全空
    close = close.dropna(axis=1, how="all")
    volume = volume.dropna(axis=1, how="all")

    # 對齊欄位
    valid_cols = close.columns.intersection(volume.columns)

    close = close[valid_cols]
    volume = volume[valid_cols]

    # 移除資料過少股票（保留70%以上）
    min_valid = int(len(close) * 0.7)
    close = close.dropna(axis=1, thresh=min_valid)
    volume = volume[close.columns]

    print(f"\n📊 Loaded tickers ({len(close.columns)}): {list(close.columns)}")

    if close.empty:
        raise ValueError("❌ 清理後無有效股票資料")

    return close, volume


# =========================================
# 🧪 測試
# =========================================

if __name__ == "__main__":
    test_tickers = ["NVDA", "TSM", "2330.TW", "3583.TW"]

    close, volume = load_price_data(test_tickers)

    print("\n=== CLOSE ===")
    print(close.tail())

    print("\n=== VOLUME ===")
    print(volume.tail())
