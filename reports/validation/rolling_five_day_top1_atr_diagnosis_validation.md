# Validation Report — ROLLING_FIVE_DAY_TOP1_ATR_DIAGNOSIS_v0_1

Generated: 2026-05-26

## Assumptions

1. Entry price = signal-day adjusted close (yfinance auto_adjust=True, v0.1)
2. Rolling baskets built from available daily report dates (not all calendar TW trading days)
3. ATR trailing stop: close-based exit, initial-stop floor on day 1 of hold
4. post_trade_label priority: OPEN_POSITION → OPEN_WINNER/OPEN_RISK; DATA_INCOMPLETE → DATA_QUALITY_ISSUE; ATR_TRAILING_STOP+post_exit>5% → ATR_TOO_TIGHT; next_1d<-3% → ENTRY_SIGNAL_FAILURE; else → MARKET_REVERSAL
5. Baskets with fewer than 5 post-entry report dates are flagged is_immature=True
6. Valuation date fixed at 2026-05-26 for all baskets
7. Transaction costs: buy 0.1425%, sell 0.1425% + STT 0.3% on sell value

## Known Limitations

- Only 15 daily report dates available (2026-05-01 to 2026-05-26) → 11 rolling baskets, all within one market regime
- Chips, chase_risk, narrative fields are not in historical reports; position grade is diagnostic only
- post_exit_max_return uses yfinance adjusted close; may differ from TWSE raw close
- IMMATURE_BASKET lots have had limited ATR stop evolution — interpret with caution
- 5% and 3% thresholds for ATR_TOO_TIGHT / ENTRY_SIGNAL_FAILURE are first-pass heuristics, not statistically derived

---

*This is a simulation. No trades were placed. No broker connections were made.*
*Owner should review before any capital allocation decisions.*
