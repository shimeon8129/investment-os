# scanner/universe.py

import pandas as pd


def get_tw_universe():
    """
    載入台股 universe
    """
    df = pd.read_csv("data/universe_tw.csv")
    return df


def get_us_universe():
    """
    載入美股 universe
    """
    df = pd.read_csv("data/universe_us.csv")
    return df
