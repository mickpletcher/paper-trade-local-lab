# TradeForge

TradeForge is a local first paper trading and strategy testing lab.

It is built to mimic trading behavior on your own machine so new strategies can be tested without live brokerage access. The current repo runs fully offline by default, stores state in SQLite, imports OHLCV CSV data, replays historical bars, executes simulated orders, and writes reports for each backtest run.

TradeForge does not place live trades. It does not connect to brokerages out of the box. It is a local simulation and research tool.

Supporting project docs:

* [assessment.md](./assessment.md)
* [changelog.md](./changelog.md)
* [future-upgrades.md](./future-upgrades.md)
* [specs/README.md](./specs/README.md)

## What The Repo Does

The current repo gives you a usable MVP for local strategy research:

* Local SQLite storage for symbols, bars, orders, fills, positions, trades, strategy runs, and account snapshots.
* Versioned SQLite schema setup through `schema_migrations`.
* A CLI for database initialization, sample data seeding, CSV imports, backtest runs, and result inspection.
* A simulated broker that supports market and limit orders with fees, slippage, cash tracking, and basic position accounting.
* A historical backtest engine that evaluates one strategy against one symbol over a selected date range.
* Markdown report generation for completed strategy runs.
* A small FastAPI app for local visibility into symbols, orders, positions, and strategy runs.
* Automated tests for core persistence, execution, migrations, and CLI flow.

## What The Repo Does Not Do Yet

The repo is still intentionally narrow:

* No live trading.
* No direct brokerage integration.
* No real time data feed.
* No multi symbol portfolio backtesting yet.
* No stop orders or partial fills yet.
* No dashboard UI yet.
* No optimization or parameter sweep engine yet.

## Current Architecture

```text
src/tradeforge/
  api/                    FastAPI app and route handlers
  backtesting/            Backtest engine and performance metrics
  broker_sim/             Simulated account, execution, orders, and positions
  database/               SQLAlchemy models, sessions, and migrations
  market_data/            CSV import and bar replay helpers
  reporting/              Markdown report generation
  sample_data/            Bundled first run CSV data
  strategies/             Strategy base types and built in strategies
  cli.py                  Main Typer command surface
  config.py               Runtime settings from environment

data/
  imports/                User supplied OHLCV CSV files
  reports/                Generated markdown backtest reports

.github/
  copilot-instructions.md Repo specific GitHub Spec rules
  prompts/                Reusable prompts for requirements, spec, plan, tasks, audit

specs/
  001-core-trading-foundation/
                          Baseline spec package for the current MVP
```

## GitHub Spec Workflow

This repo now includes a repo level GitHub Spec scaffold for non trivial work.

Use it when the change affects behavior across multiple modules, schema, execution logic, API surface, or future adapter work.

Repo level spec files:

* `.github/copilot-instructions.md`
* `.github/prompts/generate-requirements.prompt.md`
* `.github/prompts/generate-spec.prompt.md`
* `.github/prompts/generate-plan.prompt.md`
* `.github/prompts/generate-tasks.prompt.md`
* `.github/prompts/audit.prompt.md`
* `.github/prompts/release-readiness.prompt.md`
* `specs/README.md`
* `specs/001-core-trading-foundation/`

Recommended sequence for the next feature:

1. Create the next numbered folder under `specs/`.
2. Write `requirements.md`.
3. Write `spec.md`.
4. Write `plan.md`.
5. Write `tasks.md`.
6. Implement the feature.
7. Audit the finished work against the spec.

The baseline package for the current repo is:

* `specs/001-core-trading-foundation/`

## Requirements

Current package requirement:

* Python 3.12 or newer

Main runtime dependencies:

* FastAPI
* Pandas
* Pydantic Settings
* SQLAlchemy
* Typer
* Uvicorn

Dev dependencies:

* Pytest
* Pytest Cov

## Local Setup

### Windows PowerShell

Create and activate a virtual environment:

```powershell
py -3.13 -m venv .venv
. .\.venv\Scripts\Activate.ps1
```

Install the project and test tools:

```powershell
python -m pip install -e ".[dev]"
```

Initialize the local database:

```powershell
tradeforge init-db
```

Load the bundled sample dataset:

```powershell
tradeforge seed-sample-data
```

### Linux Or macOS

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
tradeforge init-db
tradeforge seed-sample-data
```

## Environment Settings

Runtime settings come from environment variables or `.env`.

The repo includes `.env.example` with the current defaults.

| Variable | Purpose | Default |
|---|---|---|
| `TRADEFORGE_DATABASE_URL` | SQLite or other future database URL | `sqlite:///data/tradeforge.db` |
| `TRADEFORGE_STARTING_CASH` | Starting cash for backtests | `100000` |
| `TRADEFORGE_FEE_PER_ORDER` | Flat fee applied per order | `1.00` |
| `TRADEFORGE_SLIPPAGE_BPS` | Slippage in basis points | `1` |

Typical local `.env`:

```text
TRADEFORGE_DATABASE_URL=sqlite:///data/tradeforge.db
TRADEFORGE_STARTING_CASH=100000
TRADEFORGE_FEE_PER_ORDER=1.00
TRADEFORGE_SLIPPAGE_BPS=1
```

## First Run Workflow

If you want to verify the repo quickly without bringing your own market data, use this flow:

```powershell
tradeforge init-db
tradeforge seed-sample-data
tradeforge run-backtest --strategy moving-average-cross --symbol AAPL --start 2023-01-01 --end 2023-01-08 --short-window 2 --long-window 3 --order-size 2
tradeforge show-orders
tradeforge show-positions
tradeforge show-pnl
```

What this does:

1. Creates the local schema if it does not already exist.
2. Seeds the bundled AAPL sample dataset into the local database.
3. Runs the built in moving average crossover strategy.
4. Prints stored orders, positions, and strategy run summaries.
5. Writes a markdown report to `data/reports/`.

## Using Your Own Market Data

TradeForge expects OHLCV CSV input with these columns:

```csv
date,open,high,low,close,volume
2023-01-03,130.28,130.90,124.17,125.07,112117500
2023-01-04,126.89,128.66,125.08,126.36,89113600
```

Import behavior:

* `date` is normalized to UTC.
* `open`, `high`, `low`, `close`, and `volume` must be present.
* Invalid or missing values are rejected.
* Reimports update existing rows for the same symbol and timestamp.

Import command:

```powershell
tradeforge import-csv --symbol AAPL --file .\data\imports\aapl.csv
```

## CLI Reference

### `tradeforge init-db`

Initializes the local schema and applies any pending SQLite migration steps.

```powershell
tradeforge init-db
```

### `tradeforge seed-sample-data`

Loads the bundled sample CSV into the database. Default symbol is `AAPL`.

```powershell
tradeforge seed-sample-data
tradeforge seed-sample-data --symbol AAPL
```

### `tradeforge import-csv`

Imports your own OHLCV CSV file.

```powershell
tradeforge import-csv --symbol MSFT --file .\data\imports\msft.csv
```

### `tradeforge run-backtest`

Runs the current built in strategy over a date range.

```powershell
tradeforge run-backtest --strategy moving-average-cross --symbol AAPL --start 2023-01-01 --end 2024-01-01
```

Extended example:

```powershell
tradeforge run-backtest --strategy moving-average-cross --symbol AAPL --start 2023-01-01 --end 2023-12-31 --short-window 20 --long-window 50 --order-size 10
```

Current strategy specific parameters:

* `--short-window`
* `--long-window`
* `--order-size`

Current behavior notes:

* Only `moving-average-cross` is available right now.
* Backtests require at least two bars.
* Signals generated on the final bar are not filled on that same final bar.
* Orders still open when the run ends are marked as cancelled.

### `tradeforge show-orders`

Prints stored simulated orders.

```powershell
tradeforge show-orders
```

### `tradeforge show-positions`

Prints stored simulated positions.

```powershell
tradeforge show-positions
```

### `tradeforge show-pnl`

Prints strategy run summaries with ending equity and total return.

```powershell
tradeforge show-pnl
```

## Reports

Each completed backtest writes a markdown report to:

```text
data/reports/<strategy-run-id>.md
```

The report currently includes:

* Strategy name
* Symbol
* Date range
* Run parameters
* Summary metrics
* Recorded trades
* Final positions

## Database And Migration Model

The repo now uses a simple versioned SQLite migration flow managed in `src/tradeforge/database/migrations.py`.

Current behavior:

* `tradeforge init-db` creates the local database folder if needed.
* A `schema_migrations` table tracks applied schema versions.
* The current migration set builds the baseline tables and indexes needed by the app.

This is a real migration path, but it is still lightweight. It is not Alembic yet.

## API

The FastAPI app is intentionally small. It is useful for local inspection and as a base for a future dashboard or service layer.

Run it locally:

```powershell
uvicorn tradeforge.api.app:app --reload
```

Default local URL:

```text
http://localhost:8000
```

Current endpoints:

* `GET /health`
* `GET /symbols`
* `GET /positions`
* `GET /orders`
* `GET /strategy-runs`

Current endpoint intent:

* `/health` returns a simple service check.
* `/symbols` returns imported symbols.
* `/positions` returns simulated positions.
* `/orders` returns stored orders.
* `/strategy-runs` returns completed or in progress run metadata and metrics.

## Docker

### Build And Run

```bash
docker build -t tradeforge .
docker run --rm -p 8000:8000 --env-file .env -v "$(pwd)/data:/app/data" tradeforge
```

### Docker Compose

```bash
docker compose up --build -d
```

Current container behavior:

* Builds from `python:3.12-slim`
* Installs the package from the repo
* Starts the API with Uvicorn
* Runs database initialization before serving requests
* Persists database and report output in the mounted `data` folder

## Proxmox Notes

If you want a simple always on local deployment in Proxmox:

1. Create a small Debian or Ubuntu VM or LXC.
2. Install Docker and Docker Compose.
3. Clone the repo.
4. Copy `.env.example` to `.env`.
5. Run `docker compose up --build -d`.

That gives you a persistent local service with app state stored in the mounted `data` path.

## Testing

Run the automated test suite:

```powershell
python -m pytest -q
```

GitHub Actions runs the same command on pushes to `main` and on pull requests with Python 3.13.

The current suite covers:

* Database initialization and migration version tracking
* CSV import upsert behavior
* Market and limit order behavior
* Invalid sell rejection
* Backtest completion
* Final bar no lookahead behavior
* CLI seed and backtest flow

## Current Limitations

Important current limitations to keep in mind:

* One built in strategy
* One symbol per backtest run
* No portfolio allocation logic
* No stop orders
* No partial fills
* No short selling model
* No exchange calendar support
* No corporate action handling
* No risk engine
* No event driven live paper adapter layer

## Recommended Next Work

The highest value next steps are:

1. Add configurable commission and symbol specific slippage models.
2. Add stop orders, stop limit orders, and cancel workflows.
3. Add partial fill logic with explicit execution rules.
4. Add parameter sweep support for the moving average strategy.
5. Add at least one more built in strategy.
6. Add API tests and richer API contracts.
7. Add a CLI command that starts the API directly.

Good first candidates for the next numbered spec:

1. Configurable commission and symbol specific slippage models.
2. Stop orders and cancel workflows.
3. Partial fill logic with explicit execution rules.
4. Parameter sweep support for the moving average strategy.

## Disclaimer

TradeForge is for research and education only.

It is not financial advice. It does not make investment recommendations. It should not be used as live trading infrastructure.
