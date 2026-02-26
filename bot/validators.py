"""
Input validation for CLI arguments.
All validation raises ValueError with a human-readable message.
"""

from __future__ import annotations

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}


def validate_symbol(symbol: str) -> str:
    symbol = symbol.strip().upper()
    if not symbol.isalnum():
        raise ValueError(f"Symbol '{symbol}' must be alphanumeric (e.g. BTCUSDT).")
    if len(symbol) < 3 or len(symbol) > 20:
        raise ValueError(f"Symbol '{symbol}' length seems invalid.")
    return symbol


def validate_side(side: str) -> str:
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValueError(f"Side must be one of {sorted(VALID_SIDES)}, got '{side}'.")
    return side


def validate_order_type(order_type: str) -> str:
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Order type must be one of {sorted(VALID_ORDER_TYPES)}, got '{order_type}'."
        )
    return order_type


def validate_quantity(quantity: str | float) -> float:
    try:
        qty = float(quantity)
    except (TypeError, ValueError):
        raise ValueError(f"Quantity '{quantity}' is not a valid number.")
    if qty <= 0:
        raise ValueError(f"Quantity must be positive, got {qty}.")
    return qty


def validate_price(price: str | float | None, order_type: str) -> float | None:
    if order_type in ("LIMIT", "STOP_MARKET") and price is None:
        raise ValueError(f"Price is required for {order_type} orders.")
    if price is None:
        return None
    try:
        p = float(price)
    except (TypeError, ValueError):
        raise ValueError(f"Price '{price}' is not a valid number.")
    if p <= 0:
        raise ValueError(f"Price must be positive, got {p}.")
    return p


def validate_stop_price(stop_price: str | float | None, order_type: str) -> float | None:
    if order_type == "STOP_MARKET" and stop_price is None:
        raise ValueError("Stop price is required for STOP_MARKET orders.")
    if stop_price is None:
        return None
    try:
        sp = float(stop_price)
    except (TypeError, ValueError):
        raise ValueError(f"Stop price '{stop_price}' is not a valid number.")
    if sp <= 0:
        raise ValueError(f"Stop price must be positive, got {sp}.")
    return sp
