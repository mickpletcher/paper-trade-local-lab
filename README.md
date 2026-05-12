# TradeForge

TradeForge is a local-first paper trading and strategy testing platform for research and education. It runs offline, stores data in SQLite, replays historical OHLCV market data, executes simulated orders, and provides a clean foundation for future AI-assisted trading research.

TradeForge does not connect to brokerages, place live orders, or send data externally by default.

## Features

- SQLite persistence with SQLAlchemy models for symbols, bars, orders, fills, positions, trades, strategy runs, and account snapshots
- Typer CLI for database setup, CSV imports, backtests, positions, orders, and P/L summaries
- OHLCV CSV importer with date normalization, validation, and upsert behavior
- Paper broker simulation for market and limit orders, buy/sell sides, cash, positions, average cost, fees, slippage, realized P/L, and unrealized P/L
- Historical backtesting engine with candle-by-candle strategy evaluation
- Modular strategy system with a sample moving average crossover strategy
- Markdown reports written to `data/reports/<strategy-run-id>.md`
- Minimal FastAPI scaffold for future dashboard/API work
- Pytest coverage for persistence, importing, orders, strategy signals, and backtest completion

## Architecture

```text
src/tradeforge/
  cli.py                  Typer command surface
  config.py               Local settings
  database/               SQLAlchemy schema, sessions, initialization
  market_data/            CSV import and historical replay helpers
  broker_sim/             Local-only simulated broker and portfolio logic
  strategies/             Strategy base class and moving average crossover
  backtesting/            Sequential backtest engine and metrics
  reporting/              Markdown report generation
  api/                    Minimal FastAPI app
```

## Installation

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Create the local database:

```bash
tradeforge init-db
```

## CLI Usage

```bash
tradeforge import-csv --symbol AAPL --file ./data/imports/aapl.csv
tradeforge run-backtest --strategy moving-average-cross --symbol AAPL --start 2023-01-01 --end 2024-01-01
tradeforge show-positions
tradeforge show-orders
tradeforge show-pnl
```

## CSV Format

TradeForge imports daily or intraday OHLCV files with these columns:

```csv
date,open,high,low,close,volume
2023-01-03,130.28,130.90,124.17,125.07,112117500
2023-01-04,126.89,128.66,125.08,126.36,89113600
```

Dates are normalized to UTC. Rows with missing or invalid OHLCV values are rejected.

## Example Backtest

```bash
tradeforge run-backtest \
  --strategy moving-average-cross \
  --symbol AAPL \
  --start 2023-01-01 \
  --end 2024-01-01 \
  --short-window 20 \
  --long-window 50 \
  --order-size 10
```

Reports are generated in `data/reports/`.

## FastAPI Scaffold

Run the API locally:

```bash
uvicorn tradeforge.api.app:app --reload
```

Endpoints:

- `GET /health`
- `GET /symbols`
- `GET /positions`
- `GET /orders`
- `GET /strategy-runs`

## Roadmap

- More strategy templates and parameter sweeps
- Richer commission, slippage, and partial-fill models
- Portfolio-level multi-symbol backtesting
- Walk-forward testing and optimization workflows
- Dashboard for runs, charts, fills, and reports
- Local AI-assisted research notebooks and strategy explanation tools

## Disclaimer

TradeForge is for research and education only. It is not financial advice, does not make investment recommendations, and must not be used as live trading infrastructure.
