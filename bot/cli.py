"""
CLI entry point for the Binance Futures Testnet trading bot.

Usage examples:
    # Market buy
    python -m bot.cli place-order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

    # Limit sell
    python -m bot.cli place-order --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 100000

    # Stop-Market (bonus)
    python -m bot.cli place-order --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.01 --stop-price 85000

    # Interactive wizard
    python -m bot.cli interactive
"""

from __future__ import annotations

import os
import sys

import argparse

from bot.client import BinanceClient
from bot.logging_config import setup_logger
from bot.orders import place_limit_order, place_market_order, place_stop_market_order
from bot.validators import (
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_stop_price,
    validate_symbol,
)

logger = setup_logger("trading_bot.cli")

BANNER = """
╔══════════════════════════════════════════════╗
║   Binance Futures Testnet  –  Trading Bot    ║
╚══════════════════════════════════════════════╝
"""


# ────────────────────────────────────────────────────────────── helpers ──── #


def _get_client() -> BinanceClient:
    api_key = os.environ.get("BINANCE_API_KEY", "").strip()
    api_secret = os.environ.get("BINANCE_API_SECRET", "").strip()

    if not api_key or not api_secret:
        print(
            "\n  ❌  BINANCE_API_KEY and BINANCE_API_SECRET environment variables must be set.\n"
            "      Export them before running:\n\n"
            "        export BINANCE_API_KEY=your_key\n"
            "        export BINANCE_API_SECRET=your_secret\n"
        )
        logger.error("Missing API credentials in environment.")
        sys.exit(1)

    return BinanceClient(api_key=api_key, api_secret=api_secret)


def _run_order(args: argparse.Namespace) -> None:
    """Validate args and dispatch to the correct order function."""
    try:
        symbol = validate_symbol(args.symbol)
        side = validate_side(args.side)
        order_type = validate_order_type(args.type)
        quantity = validate_quantity(args.quantity)
        price = validate_price(getattr(args, "price", None), order_type)
        stop_price = validate_stop_price(getattr(args, "stop_price", None), order_type)
    except ValueError as exc:
        print(f"\n  ❌  Validation error: {exc}\n")
        logger.warning("Validation error: %s", exc)
        sys.exit(1)

    # Print request summary
    print(BANNER)
    print("  📋  Order Summary")
    print("  ─────────────────────────────────────────")
    print(f"  Symbol       : {symbol}")
    print(f"  Side         : {side}")
    print(f"  Type         : {order_type}")
    print(f"  Quantity     : {quantity}")
    if price:
        print(f"  Price        : {price}")
    if stop_price:
        print(f"  Stop Price   : {stop_price}")
    print()

    client = _get_client()

    if order_type == "MARKET":
        result = place_market_order(client, symbol, side, quantity)
    elif order_type == "LIMIT":
        result = place_limit_order(client, symbol, side, quantity, price)
    elif order_type == "STOP_MARKET":
        result = place_stop_market_order(client, symbol, side, quantity, stop_price)
    else:
        print(f"  ❌  Unhandled order type: {order_type}")
        sys.exit(1)

    result.display()
    sys.exit(0 if result.success else 1)


# ────────────────────────────────────────────────── interactive wizard ───── #


def _interactive() -> None:
    print(BANNER)
    print("  Interactive Order Wizard  (type 'q' to quit at any prompt)\n")

    def ask(prompt: str, validator=None, default=None):
        while True:
            suffix = f" [{default}]" if default else ""
            raw = input(f"  {prompt}{suffix}: ").strip()
            if raw.lower() == "q":
                print("  Bye!\n")
                sys.exit(0)
            if not raw and default:
                raw = default
            if validator:
                try:
                    return validator(raw)
                except ValueError as e:
                    print(f"    ⚠️   {e}")
            else:
                return raw

    symbol = ask("Symbol (e.g. BTCUSDT)", validate_symbol)
    side = ask("Side [BUY/SELL]", validate_side)

    print("  Order types: MARKET | LIMIT | STOP_MARKET")
    order_type = ask("Order type", validate_order_type)

    quantity = ask("Quantity", validate_quantity)

    price = None
    stop_price = None
    if order_type == "LIMIT":
        price = ask("Limit price", lambda x: validate_price(x, "LIMIT"))
    elif order_type == "STOP_MARKET":
        stop_price = ask("Stop price", lambda x: validate_stop_price(x, "STOP_MARKET"))

    # Mimic namespace
    class NS:
        pass

    ns = NS()
    ns.symbol = symbol
    ns.side = side
    ns.type = order_type
    ns.quantity = quantity
    ns.price = price
    ns.stop_price = stop_price

    _run_order(ns)


# ──────────────────────────────────────────────────────────── argparse ───── #


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading-bot",
        description="Binance Futures Testnet – Trading Bot",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # place-order sub-command
    order_p = sub.add_parser("place-order", help="Place a single order.")
    order_p.add_argument("--symbol", required=True, help="Trading pair, e.g. BTCUSDT")
    order_p.add_argument(
        "--side", required=True, choices=["BUY", "SELL"], type=str.upper, help="BUY or SELL"
    )
    order_p.add_argument(
        "--type",
        required=True,
        choices=["MARKET", "LIMIT", "STOP_MARKET"],
        type=str.upper,
        dest="type",
        help="Order type",
    )
    order_p.add_argument("--quantity", required=True, type=float, help="Quantity to trade")
    order_p.add_argument("--price", type=float, default=None, help="Price (required for LIMIT)")
    order_p.add_argument(
        "--stop-price", type=float, default=None, dest="stop_price",
        help="Stop price (required for STOP_MARKET)"
    )

    # interactive sub-command
    sub.add_parser("interactive", help="Launch interactive wizard.")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "interactive":
        _interactive()
    elif args.command == "place-order":
        _run_order(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
