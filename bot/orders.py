"""
Order placement logic — sits between the CLI and the raw client.
Each function returns a normalised OrderResult dict.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from bot.client import BinanceClient, BinanceAPIError
from bot.logging_config import setup_logger

logger = setup_logger("trading_bot.orders")


@dataclass
class OrderResult:
    success: bool
    order_id: int | None = None
    symbol: str = ""
    side: str = ""
    order_type: str = ""
    status: str = ""
    quantity: float = 0.0
    executed_qty: float = 0.0
    avg_price: float = 0.0
    price: float = 0.0
    raw: dict = field(default_factory=dict)
    error: str = ""

    def display(self) -> None:
        """Print a formatted summary to stdout."""
        sep = "─" * 52
        print(sep)
        if self.success:
            print("  ✅  ORDER PLACED SUCCESSFULLY")
            print(sep)
            print(f"  Order ID      : {self.order_id}")
            print(f"  Symbol        : {self.symbol}")
            print(f"  Side          : {self.side}")
            print(f"  Type          : {self.order_type}")
            print(f"  Status        : {self.status}")
            print(f"  Quantity      : {self.quantity}")
            print(f"  Executed Qty  : {self.executed_qty}")
            if self.avg_price:
                print(f"  Avg Price     : {self.avg_price}")
            if self.price:
                print(f"  Limit Price   : {self.price}")
        else:
            print("  ❌  ORDER FAILED")
            print(sep)
            print(f"  Error         : {self.error}")
        print(sep)


def _parse_response(raw: dict) -> OrderResult:
    return OrderResult(
        success=True,
        order_id=raw.get("orderId"),
        symbol=raw.get("symbol", ""),
        side=raw.get("side", ""),
        order_type=raw.get("type", ""),
        status=raw.get("status", ""),
        quantity=float(raw.get("origQty", 0)),
        executed_qty=float(raw.get("executedQty", 0)),
        avg_price=float(raw.get("avgPrice", 0) or 0),
        price=float(raw.get("price", 0) or 0),
        raw=raw,
    )


def place_market_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: float,
) -> OrderResult:
    logger.info(
        "Placing MARKET order | symbol=%s side=%s qty=%s",
        symbol, side, quantity,
    )
    print(f"\n  📤  Sending MARKET {side} order — {quantity} {symbol} ...")
    try:
        raw = client.place_order(
            symbol=symbol,
            side=side,
            type="MARKET",
            quantity=quantity,
        )
        result = _parse_response(raw)
        logger.info("MARKET order success | orderId=%s status=%s", result.order_id, result.status)
        return result
    except BinanceAPIError as exc:
        logger.error("MARKET order failed | %s", exc)
        return OrderResult(success=False, error=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error placing MARKET order")
        return OrderResult(success=False, error=f"Unexpected error: {exc}")


def place_limit_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    time_in_force: str = "GTC",
) -> OrderResult:
    logger.info(
        "Placing LIMIT order | symbol=%s side=%s qty=%s price=%s tif=%s",
        symbol, side, quantity, price, time_in_force,
    )
    print(f"\n  📤  Sending LIMIT {side} order — {quantity} {symbol} @ {price} ...")
    try:
        raw = client.place_order(
            symbol=symbol,
            side=side,
            type="LIMIT",
            quantity=quantity,
            price=price,
            timeInForce=time_in_force,
        )
        result = _parse_response(raw)
        logger.info("LIMIT order success | orderId=%s status=%s", result.order_id, result.status)
        return result
    except BinanceAPIError as exc:
        logger.error("LIMIT order failed | %s", exc)
        return OrderResult(success=False, error=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error placing LIMIT order")
        return OrderResult(success=False, error=f"Unexpected error: {exc}")


def place_stop_market_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: float,
    stop_price: float,
) -> OrderResult:
    """Bonus: Stop-Market order — triggers a market order when stop_price is hit."""
    logger.info(
        "Placing STOP_MARKET order | symbol=%s side=%s qty=%s stopPrice=%s",
        symbol, side, quantity, stop_price,
    )
    print(f"\n  📤  Sending STOP_MARKET {side} order — {quantity} {symbol} | stop @ {stop_price} ...")
    try:
        raw = client.place_order(
            symbol=symbol,
            side=side,
            type="STOP_MARKET",
            quantity=quantity,
            stopPrice=stop_price,
        )
        result = _parse_response(raw)
        logger.info("STOP_MARKET order success | orderId=%s status=%s", result.order_id, result.status)
        return result
    except BinanceAPIError as exc:
        logger.error("STOP_MARKET order failed | %s", exc)
        return OrderResult(success=False, error=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error placing STOP_MARKET order")
        return OrderResult(success=False, error=f"Unexpected error: {exc}")
