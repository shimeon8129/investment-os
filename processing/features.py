# processing/features.py

import pandas as pd


def compute_features(close, volume):
    features = {}

    # MA
    features["ma5"] = close.rolling(5).mean()
    features["ma10"] = close.rolling(10).mean()
    features["ma20"] = close.rolling(20).mean()
    features["ma50"] = close.rolling(50).mean()
    features["ma150"] = close.rolling(150).mean()
    features["ma200"] = close.rolling(200).mean()

    # return
    features["return_1d"] = close.pct_change()

    # volume ratio
    features["vol_ratio"] = volume / volume.rolling(5).mean()
    features["vol_ratio"] = features["vol_ratio"].fillna(0)

    # new high
    features["new_high_20d"] = (close == close.rolling(20).max()).astype(int)

    # 52-week position for Minervini-style Stage 2 scans.
    features["high_52w"] = close.rolling(250).max()
    features["low_52w"] = close.rolling(250).min()

    # trend strength（🔥新增）
    features["trend_strength"] = (features["ma5"] > features["ma20"]).astype(int)

    return features
