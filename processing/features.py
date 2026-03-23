# processing/features.py

import pandas as pd


def compute_features(close, volume):
    features = {}

    # MA
    features["ma5"] = close.rolling(5).mean()
    features["ma10"] = close.rolling(10).mean()
    features["ma20"] = close.rolling(20).mean()

    # return
    features["return_1d"] = close.pct_change()

    # volume ratio
    features["vol_ratio"] = volume / volume.rolling(5).mean()
    features["vol_ratio"] = features["vol_ratio"].fillna(0)

    # new high
    features["new_high_20d"] = (close == close.rolling(20).max()).astype(int)

    # trend strength（🔥新增）
    features["trend_strength"] = (features["ma5"] > features["ma20"]).astype(int)

    return features
