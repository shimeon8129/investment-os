# Validation Report — TIERED_ATR_EXIT_BACKTEST_v0_1

Generated: 2026-05-27

## Assumptions

1. Rolling baskets and OHLC data reuse P0.3 infrastructure (same 15 report dates, 11 baskets)
2. Entry price = signal-day adjusted close (yfinance auto_adjust=True, v0.1)
3. Tiered multiplier tiers based on peak float from entry price (highest_close, not current close)
4. Hold protection window = first 3 report dates (not calendar days) after entry
5. false_exit_count: exit_reason=ATR_TRAILING_STOP AND post_exit_max_return > 5%
6. profit_giveback_pct = (max_profit_seen − gross_pnl) / max_profit_seen; None when max_profit_seen ≤ 0
7. Transaction costs: buy 0.1425%, sell 0.1425% + STT 0.3% on sell value

## Known Limitations

- Only 15 daily report dates (2026-05-01 to 2026-05-26) — single bull market regime
- TIERED_ATR parameters (5%/15% thresholds, 2.0/2.5/3.0 multipliers) are first-pass heuristics
- Hold protection period = 3 report dates is heuristic; not derived from empirical data
- post_exit_max_return uses yfinance adjusted close — may differ from TWSE raw close
- DATA_QUALITY_ISSUE lots (ticker=None) excluded from metric aggregation

## Decision Criteria

Upgrade TIERED_ATR to candidate default ONLY if all three hold:
1. total_net_pnl(TIERED_ATR) > total_net_pnl(ATR_BASE)
2. false_exit_count(TIERED_ATR) < false_exit_count(ATR_BASE)
3. max_drawdown(TIERED_ATR) ≤ max_drawdown(ATR_BASE) × 1.2 (not more than 20% worse)
   AND largest_single_lot_loss(TIERED_ATR) ≥ largest_single_lot_loss(ATR_BASE) × 0.8

---

*This is a simulation. No trades were placed. No broker connections were made.*
*Owner should review before any capital allocation decisions.*
