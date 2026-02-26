"""
Low-level Binance Futures REST client.
Handles HMAC-SHA256 signing, request execution, and error parsing.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any
from urllib.parse import urlencode

import requests

from bot.logging_config import setup_logger

BASE_URL = "https://testnet.binancefuture.com"

logger = setup_logger("trading_bot.client")


class BinanceAPIError(Exception):
    """Raised when Binance returns a non-OK response or an API error code."""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"Binance API error {code}: {message}")


class BinanceClient:
    """
    Thin wrapper around the Binance Futures REST API.
    Handles authentication and request/response lifecycle.
    """

    def __init__(self, api_key: str, api_secret: str, base_url: str = BASE_URL) -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-MBX-APIKEY": self.api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _sign(self, params: dict) -> dict:
        """Append HMAC-SHA256 signature to a params dict."""
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    def _timestamp(self) -> int:
        return int(time.time() * 1000)

    def _request(self, method: str, path: str, signed: bool = False, **kwargs) -> Any:
        url = f"{self.base_url}{path}"
        params = kwargs.pop("params", {})
        data = kwargs.pop("data", {})

        if signed:
            payload = {**params, **data, "timestamp": self._timestamp()}
            payload = self._sign(payload)
            if method.upper() in ("GET", "DELETE"):
                params = payload
                data = {}
            else:
                data = payload
                params = {}

        logger.debug("REQUEST  %s %s | params=%s | body=%s", method.upper(), url, params, data)

        try:
            resp = self._session.request(
                method,
                url,
                params=params,
                data=data,
                timeout=10,
                **kwargs,
            )
        except requests.exceptions.ConnectionError as exc:
            logger.error("Network error connecting to %s: %s", url, exc)
            raise ConnectionError(f"Could not reach Binance at {url}. Check your network.") from exc
        except requests.exceptions.Timeout as exc:
            logger.error("Request timed out for %s", url)
            raise TimeoutError("Binance request timed out.") from exc

        logger.debug("RESPONSE %s %s | status=%s | body=%s", method.upper(), url, resp.status_code, resp.text)

        # Binance always returns JSON (even for errors)
        try:
            body = resp.json()
        except ValueError:
            logger.error("Non-JSON response from Binance: %s", resp.text)
            raise BinanceAPIError(-1, f"Non-JSON response: {resp.text}")

        if resp.status_code != 200 or (isinstance(body, dict) and "code" in body and body["code"] < 0):
            code = body.get("code", resp.status_code)
            msg = body.get("msg", resp.text)
            logger.error("API error %s: %s", code, msg)
            raise BinanceAPIError(code, msg)

        return body

    # ------------------------------------------------------------------ #
    #  Public endpoints (no auth)                                         #
    # ------------------------------------------------------------------ #

    def get_exchange_info(self) -> dict:
        return self._request("GET", "/fapi/v1/exchangeInfo")

    def get_price(self, symbol: str) -> dict:
        return self._request("GET", "/fapi/v1/ticker/price", params={"symbol": symbol})

    # ------------------------------------------------------------------ #
    #  Account endpoints (signed)                                         #
    # ------------------------------------------------------------------ #

    def get_account(self) -> dict:
        return self._request("GET", "/fapi/v2/account", signed=True)

    # ------------------------------------------------------------------ #
    #  Order endpoints (signed)                                           #
    # ------------------------------------------------------------------ #

    def place_order(self, **params) -> dict:
        """
        POST /fapi/v1/order
        All Binance order parameters are passed as keyword arguments.
        """
        return self._request("POST", "/fapi/v1/order", signed=True, data=params)

    def get_order(self, symbol: str, order_id: int) -> dict:
        return self._request(
            "GET",
            "/fapi/v1/order",
            signed=True,
            params={"symbol": symbol, "orderId": order_id},
        )

    def cancel_order(self, symbol: str, order_id: int) -> dict:
        return self._request(
            "DELETE",
            "/fapi/v1/order",
            signed=True,
            params={"symbol": symbol, "orderId": order_id},
        )
