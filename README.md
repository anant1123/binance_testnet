# Binance Futures Testnet – Trading Bot

A clean, production-style Python trading bot that places **Market**, **Limit**, and **Stop-Market** orders on the [Binance Futures Testnet](https://testnet.binancefuture.com) via direct REST calls.

---

## Features

| Feature | Detail |
|---|---|
| Order types | MARKET, LIMIT, STOP_MARKET (bonus) |
| Sides | BUY & SELL |
| CLI | `argparse` – flag-based and interactive wizard |
| Validation | symbol, side, type, quantity, price, stop-price |
| Logging | Structured logs (DEBUG → file, WARNING → console) |
| Error handling | API errors, network failures, invalid input |
| Architecture | Separated client / orders / validators / CLI layers |

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance REST client (HMAC signing, requests)
│   ├── orders.py          # Order placement logic & result formatting
│   ├── validators.py      # Input validation (raises ValueError)
│   ├── logging_config.py  # File + console logger setup
│   └── cli.py             # CLI entry point (argparse + interactive wizard)
├── logs/                  # Auto-created; one log file per day
├── README.md
└── requirements.txt
```

---

## Setup

### 1. Prerequisites

- Python 3.9+
- A [Binance Futures Testnet](https://testnet.binancefuture.com) account with API credentials

### 2. Get Testnet API Keys

1. Visit [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Sign in with your GitHub account
3. Click **"Generate HMAC_SHA256 Key"**
4. Copy your API Key and Secret

### 3. Install dependencies

```bash
cd trading_bot
pip install -r requirements.txt
```

### 4. Set environment variables

```bash
export BINANCE_API_KEY="your_testnet_api_key"
export BINANCE_API_SECRET="your_testnet_api_secret"
```

On Windows (PowerShell):
```powershell
$env:BINANCE_API_KEY="your_testnet_api_key"
$env:BINANCE_API_SECRET="your_testnet_api_secret"
```

---

## How to Run

All commands are run from the `trading_bot/` root directory.

### Market Order

```bash
# Buy 0.01 BTC at market price
python -m bot.cli place-order \
  --symbol BTCUSDT \
  --side BUY \
  --type MARKET \
  --quantity 0.01

# Sell 0.05 ETH at market price
python -m bot.cli place-order \
  --symbol ETHUSDT \
  --side SELL \
  --type MARKET \
  --quantity 0.05
```

### Limit Order

```bash
# Sell 0.01 BTC at $115,000
python -m bot.cli place-order \
  --symbol BTCUSDT \
  --side SELL \
  --type LIMIT \
  --quantity 0.01 \
  --price 115000

# Buy 0.1 ETH at $3,000
python -m bot.cli place-order \
  --symbol ETHUSDT \
  --side BUY \
  --type LIMIT \
  --quantity 0.1 \
  --price 3000
```

### Stop-Market Order *(Bonus)*

```bash
# Stop-loss: sell 0.01 BTC if price drops to $85,000
python -m bot.cli place-order \
  --symbol BTCUSDT \
  --side SELL \
  --type STOP_MARKET \
  --quantity 0.01 \
  --stop-price 85000
```

### Interactive Wizard *(Bonus)*

Step-by-step prompts with live validation:

```bash
python -m bot.cli interactive
```

Sample session:

```
  Symbol (e.g. BTCUSDT): BTCUSDT
  Side [BUY/SELL]: BUY
  Order types: MARKET | LIMIT | STOP_MARKET
  Order type: MARKET
  Quantity: 0.01
```

---

## Example Output

```
╔══════════════════════════════════════════════╗
║   Binance Futures Testnet  –  Trading Bot    ║
╚══════════════════════════════════════════════╝

  📋  Order Summary
  ─────────────────────────────────────────
  Symbol       : BTCUSDT
  Side         : BUY
  Type         : MARKET
  Quantity     : 0.01

  📤  Sending MARKET BUY order — 0.01 BTCUSDT ...
────────────────────────────────────────────────────
  ✅  ORDER PLACED SUCCESSFULLY
────────────────────────────────────────────────────
  Order ID      : 4149684895
  Symbol        : BTCUSDT
  Side          : BUY
  Type          : MARKET
  Status        : FILLED
  Quantity      : 0.01
  Executed Qty  : 0.01
  Avg Price     : 107345.2
────────────────────────────────────────────────────
```

---

## Logging

Logs are written to `logs/trading_bot_YYYYMMDD.log`.

- **DEBUG** – every API request URL, params, and raw response body
- **INFO** – order lifecycle events (placing, success)
- **WARNING** – input validation failures
- **ERROR** – API errors and network failures

Console output is limited to WARNING and above to keep the terminal clean.

Sample log entries are included in the `logs/` directory.

---

## Assumptions

1. **Testnet only** – the base URL is hard-coded to `https://testnet.binancefuture.com`. Swap `BASE_URL` in `client.py` for production (at your own risk).
2. **USDT-M Futures** – all orders target `/fapi/v1/order` (USD-margined contracts).
3. **No position-mode check** – the bot sends `positionSide` as `BOTH` (one-way mode). If your testnet account uses hedge mode, pass `positionSide=LONG/SHORT` explicitly.
4. **Quantity precision** – Binance enforces symbol-specific step sizes. If you get a precision error, check the symbol's `LOT_SIZE` filter via `/fapi/v1/exchangeInfo`.
5. **Credentials via environment** – no config files or command-line flags for secrets (follows 12-factor app principles).

---

## Dependencies

```
requests>=2.31.0
```

Only the standard library and `requests` are used — no `python-binance` wrapper, so the signing and HTTP logic is transparent and easy to audit.
