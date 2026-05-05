# =========================================================
# risk/position_sizing.py
# =========================================================
# P0.3: Provisional additive max-loss position sizing.
#
# This module is UPSTREAM sizing only.
# It is NOT a replacement for execution/risk.py.
# It is NOT a merge of any existing risk modules.
# It does NOT enforce exposure caps or market-state adjustments.
# Those remain in execution/risk.py (active runtime).
# =========================================================

import math


def calculate_position_size(capital, entry_price, stop_price, max_loss_pct=0.01):
    """
    Max-loss based position sizing.

    Given a capital base and a defined stop level, compute the share count
    that limits the maximum loss to max_loss_pct of capital.

    Parameters
    ----------
    capital : float
        Total account capital.
    entry_price : float
        Planned entry price per share.
    stop_price : float
        Stop-loss price per share (must be < entry_price for a long trade).
    max_loss_pct : float
        Maximum acceptable loss as a fraction of capital. Default 0.01 (1%).

    Returns
    -------
    dict with keys:
        shares          int   — number of shares to buy
        position_value  float — total cost of the position (shares × entry_price)
        position_pct    float — position_value as a fraction of capital
        max_loss_value  float — maximum dollar loss (capital × max_loss_pct)
        risk_per_share  float — entry_price - stop_price
        feasible        bool  — False if risk_per_share <= 0 or shares == 0

    Formula
    -------
    max_loss_value = capital × max_loss_pct
    risk_per_share = entry_price - stop_price
    shares         = floor(max_loss_value / risk_per_share)
    position_value = shares × entry_price
    position_pct   = position_value / capital
    """
    max_loss_value = capital * max_loss_pct
    risk_per_share = entry_price - stop_price

    if risk_per_share <= 0:
        return {
            "shares": 0,
            "position_value": 0.0,
            "position_pct": 0.0,
            "max_loss_value": round(max_loss_value, 4),
            "risk_per_share": round(risk_per_share, 4),
            "feasible": False,
        }

    shares = math.floor(max_loss_value / risk_per_share)
    position_value = shares * entry_price
    position_pct = position_value / capital if capital > 0 else 0.0

    return {
        "shares": shares,
        "position_value": round(position_value, 4),
        "position_pct": round(position_pct, 6),
        "max_loss_value": round(max_loss_value, 4),
        "risk_per_share": round(risk_per_share, 4),
        "feasible": shares > 0,
    }
