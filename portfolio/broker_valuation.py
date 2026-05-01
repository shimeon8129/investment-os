from math import floor


BROKER_FEE_RATE = 0.001425
ETF_SELL_TAX_RATE = 0.001
STOCK_SELL_TAX_RATE = 0.003


def get_sell_tax_rate(asset_type: str | None) -> float:
    if str(asset_type or "").upper() == "ETF":
        return ETF_SELL_TAX_RATE
    return STOCK_SELL_TAX_RATE


def estimate_sell_costs(
    market_value: float,
    asset_type: str | None,
    broker_fee_rate: float = BROKER_FEE_RATE,
) -> dict:
    """
    Broker-app style sell cost estimate.

    Taiwan broker apps commonly display trial PnL after estimated sell-side
    costs. Fees/taxes are rounded down to whole TWD in this model, which
    matches the 009816 sample from the user's broker app.
    """
    broker_fee = floor(market_value * broker_fee_rate)
    transaction_tax = floor(market_value * get_sell_tax_rate(asset_type))

    return {
        "estimated_sell_fee": broker_fee,
        "estimated_sell_tax": transaction_tax,
        "estimated_sell_cost": broker_fee + transaction_tax,
    }


def resolve_cost_basis(holding: dict) -> float:
    if holding.get("cost_basis") is not None:
        return float(holding["cost_basis"])

    shares = int(holding.get("shares", 0))
    entry_price = holding.get("entry_price")

    if entry_price is None:
        raise ValueError(f"Missing cost basis for {holding.get('ticker')}")

    return float(entry_price) * shares


def value_position(
    holding: dict,
    last_price: float,
    broker_fee_rate: float = BROKER_FEE_RATE,
) -> dict:
    shares = int(holding.get("shares", 0))
    market_value = float(last_price) * shares
    cost_basis = resolve_cost_basis(holding)

    gross_pnl = market_value - cost_basis
    sell_costs = estimate_sell_costs(
        market_value,
        holding.get("asset_type"),
        broker_fee_rate=broker_fee_rate,
    )
    broker_trial_pnl = gross_pnl - sell_costs["estimated_sell_cost"]

    return {
        "ticker": holding.get("ticker"),
        "name": holding.get("name"),
        "shares": shares,
        "entry_price": holding.get("entry_price"),
        "cost_basis": cost_basis,
        "last_price": float(last_price),
        "market_value": market_value,
        "gross_pnl": gross_pnl,
        "gross_return_pct": (gross_pnl / cost_basis * 100) if cost_basis else 0,
        **sell_costs,
        "broker_trial_pnl": broker_trial_pnl,
        "broker_trial_return_pct": (
            broker_trial_pnl / cost_basis * 100
        ) if cost_basis else 0,
    }


def summarize_positions(position_values: list[dict]) -> dict:
    total_cost = sum(row["cost_basis"] for row in position_values)
    total_market_value = sum(row["market_value"] for row in position_values)
    total_gross_pnl = sum(row["gross_pnl"] for row in position_values)
    total_sell_cost = sum(row["estimated_sell_cost"] for row in position_values)
    total_broker_trial_pnl = sum(row["broker_trial_pnl"] for row in position_values)

    return {
        "total_cost_basis": total_cost,
        "total_market_value": total_market_value,
        "total_gross_pnl": total_gross_pnl,
        "total_gross_return_pct": (
            total_gross_pnl / total_cost * 100
        ) if total_cost else 0,
        "total_estimated_sell_cost": total_sell_cost,
        "total_broker_trial_pnl": total_broker_trial_pnl,
        "total_broker_trial_return_pct": (
            total_broker_trial_pnl / total_cost * 100
        ) if total_cost else 0,
    }
