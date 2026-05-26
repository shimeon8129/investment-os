# Comparison Report — TIERED_ATR_EXIT_BACKTEST_v0_1

Generated: 2026-05-27
Valuation date: 2026-05-26
Rolling baskets: 11

---

## Model Comparison Summary

| Model | TotalNetPnL | FalseExits | MaxDrawdown | WorstLot | AvgGiveback% | Protected |
|-------|-------------|------------|-------------|----------|--------------|-----------|
| ATR_BASE | +192,136 | 17 | 14,940 | -14,940 | 104.7% | 0 |
| ATR_WIDE | +328,711 | 12 | 14,940 | -14,940 | 91.4% | 0 |
| TIERED_ATR | +328,711 | 12 | 14,940 | -14,940 | 91.4% | 0 |
| TIERED_ATR_NO_HOLD_PROTECTION | +328,711 | 12 | 14,940 | -14,940 | 91.4% | 0 |
| FIXED_10D | +76,149 | 0 | 0 | +7,872 | — | 0 |
| MA5 | -188,989 | 0 | 0 | -8,100 | — | 0 |

---

## Model Definitions

| Model | Init× | Trail× | Hold Protection |
|-------|-------|--------|-----------------|
| ATR_BASE | 1.5 | 2.0 (fixed) | No |
| ATR_WIDE | 2.0 | 2.5 (fixed) | No |
| TIERED_ATR | 1.5 | 2.0→2.5→3.0 (float-pct tier) | Yes (3 report dates) |
| TIERED_ATR_NO_HOLD_PROTECTION | 1.5 | 2.0→2.5→3.0 | No |
| FIXED_10D | — | — (exit on day 10) | — |
| MA5 | — | — (close < MA5) | — |

---

## Tiered Multiplier Logic

Based on `(highest_close - entry_price) / entry_price`:

- float_pct  < 5%: trailing = 2.0 × ATR20
- 5% ≤ float_pct < 15%: trailing = 2.5 × ATR20
- float_pct ≥ 15%: trailing = 3.0 × ATR20

Hold protection: first 3 report dates after entry → only initial_stop (1.5×ATR) active.

---

*Advisory only. No trades placed. All outputs for human review.*
