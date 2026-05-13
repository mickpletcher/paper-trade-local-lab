# TradeForge

TradeForge is a local paper trading and strategy testing app.

It lets you do three main things on your own computer:

1. load market data from CSV files
2. run a strategy against that data
3. inspect the simulated results

TradeForge does not place live trades.

TradeForge does not connect to a brokerage for execution.

TradeForge is meant for local testing, learning, and strategy research.

## If You Are New To This Project

Start here.

You do not need to understand the whole codebase first.

The fastest path is:

1. install Python
2. install the project
3. create the local database
4. load the built in sample data
5. run a sample backtest
6. look at the results

That is enough to prove the project is working.

## What This Project Does

TradeForge can currently:

1. store data in a local SQLite database
2. import OHLCV market data from CSV files
3. simulate market and limit orders locally
4. track positions, fills, trades, and strategy runs
5. run historical backtests
6. write markdown reports
7. expose a small local API for inspection

## What This Project Does Not Do

TradeForge does not currently:

1. place live trades
2. connect to a broker for order execution
3. stream live market data yet
4. support stop orders or partial fills
5. support multiple built in strategies
6. provide a web dashboard UI

## Files You Should Know About

These are the most important repo files for a new user:

* [assessment.md](./assessment.md)
* [changelog.md](./changelog.md)
* [future-upgrades.md](./future-upgrades.md)
* [specs/README.md](./specs/README.md)

## What You Need Before You Start

You need:

1. Python 3.12 or newer
2. a terminal
3. this repo on your machine

If you are on Windows, PowerShell is fine.

## Recommended Setup For Windows

### Step 1: Open PowerShell In The Repo Folder

If the repo is already cloned, open PowerShell and move into the repo folder.

Example:

```powershell
cd "C:\Users\mick0\OneDrive\Documents\Code & Dev\GitHub\paper-trade-local-lab"
```

### Step 2: Create A Virtual Environment

This gives the project its own isolated Python environment.

```powershell
py -3.13 -m venv .venv
```

If `py -3.13` is not available, use any installed Python version that is 3.12 or newer.

### Step 3: Activate The Virtual Environment

```powershell
. .\.venv\Scripts\Activate.ps1
```

If it worked, you will usually see `(.venv)` at the start of your prompt.

### Step 4: Install The Project

```powershell
python -m pip install -e ".[dev]"
```

This installs:

1. the TradeForge package
2. the libraries it needs
3. the test tools used by the repo

### Step 5: Create The Local Database

```powershell
tradeforge init-db
```

This creates the local SQLite database structure.

### Step 6: Load The Built In Sample Data

```powershell
tradeforge seed-sample-data
```

This loads a small sample AAPL dataset so you can test the app right away.

### Step 7: Run A Sample Backtest

```powershell
tradeforge run-backtest --strategy moving-average-cross --symbol AAPL --start 2023-01-01 --end 2023-01-08 --short-window 2 --long-window 3 --order-size 2
```

### Step 8: View The Results

```powershell
tradeforge show-orders
tradeforge show-positions
tradeforge show-pnl
```

## Recommended Setup For Linux Or macOS

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
tradeforge init-db
tradeforge seed-sample-data
tradeforge run-backtest --strategy moving-average-cross --symbol AAPL --start 2023-01-01 --end 2023-01-08 --short-window 2 --long-window 3 --order-size 2
tradeforge show-orders
tradeforge show-positions
tradeforge show-pnl
```

## What Each Command Does

### `tradeforge init-db`

Creates the local database and applies the current schema migrations.

Use this first.

```powershell
tradeforge init-db
```

### `tradeforge seed-sample-data`

Loads the built in sample market data into the database.

Use this if you want to test the project without finding your own CSV file first.

```powershell
tradeforge seed-sample-data
```

### `tradeforge import-csv`

Imports your own OHLCV CSV file.

```powershell
tradeforge import-csv --symbol AAPL --file .\data\imports\aapl.csv
```

### `tradeforge run-backtest`

Runs the built in strategy over a date range.

```powershell
tradeforge run-backtest --strategy moving-average-cross --symbol AAPL --start 2023-01-01 --end 2024-01-01
```

Important rules:

1. only `moving-average-cross` is available right now
2. the symbol must already exist in the database
3. the dates must be valid ISO style dates
4. the start date must be earlier than the end date

### `tradeforge start-api`

Starts the local API.

```powershell
tradeforge start-api
```

If you want live reload while developing:

```powershell
tradeforge start-api --reload
```

If you want it reachable from outside the machine or container:

```powershell
tradeforge start-api --host 0.0.0.0 --port 8000
```

### `tradeforge show-orders`

Shows the simulated orders saved in the local database.

```powershell
tradeforge show-orders
```

### `tradeforge show-positions`

Shows the current simulated positions.

```powershell
tradeforge show-positions
```

### `tradeforge show-pnl`

Shows basic results for completed strategy runs.

```powershell
tradeforge show-pnl
```

## Using Your Own CSV Data

TradeForge expects a CSV file with these columns:

```csv
date,open,high,low,close,volume
2023-01-03,130.28,130.90,124.17,125.07,112117500
2023-01-04,126.89,128.66,125.08,126.36,89113600
```

What the columns mean:

1. `date`
   the time for the bar
2. `open`
   the first traded price in the bar
3. `high`
   the highest traded price in the bar
4. `low`
   the lowest traded price in the bar
5. `close`
   the last traded price in the bar
6. `volume`
   the traded volume for the bar

Import example:

```powershell
tradeforge import-csv --symbol MSFT --file .\data\imports\msft.csv
```

Important behavior:

1. dates are normalized to UTC
2. invalid rows are rejected
3. importing the same symbol and timestamp again updates the existing row

## Where The Data Lives

### Database

By default, the local SQLite database lives here:

```text
data/tradeforge.db
```

### Reports

Generated backtest reports are written here:

```text
data/reports/
```

### Input CSV Files

If you want a simple place to keep your import files, use:

```text
data/imports/
```

## Local Settings

You can configure the project with environment variables or a `.env` file.

The repo includes `.env.example`.

Current settings:

| Variable | Meaning | Default |
|---|---|---|
| `TRADEFORGE_DATABASE_URL` | database location | `sqlite:///data/tradeforge.db` |
| `TRADEFORGE_STARTING_CASH` | starting backtest cash | `100000` |
| `TRADEFORGE_FEE_PER_ORDER` | flat fee per order | `1.00` |
| `TRADEFORGE_SLIPPAGE_BPS` | slippage in basis points | `1` |

Example `.env`:

```text
TRADEFORGE_DATABASE_URL=sqlite:///data/tradeforge.db
TRADEFORGE_STARTING_CASH=100000
TRADEFORGE_FEE_PER_ORDER=1.00
TRADEFORGE_SLIPPAGE_BPS=1
```

## Running The API

Start it with:

```powershell
tradeforge start-api --reload
```

Then open:

```text
http://localhost:8000
```

Useful API locations:

* `http://localhost:8000/health`
* `http://localhost:8000/symbols`
* `http://localhost:8000/positions`
* `http://localhost:8000/orders`
* `http://localhost:8000/strategy-runs`
* `http://localhost:8000/docs`

The `/docs` page is especially useful for new users because it shows the endpoints in the browser and now includes example responses.

## Running With Docker

If you prefer Docker:

### Build And Run

```bash
docker build -t tradeforge .
docker run --rm -p 8000:8000 --env-file .env -v "$(pwd)/data:/app/data" tradeforge
```

### Docker Compose

```bash
docker compose up --build -d
```

The container now starts the API through the same command surface used locally:

```text
tradeforge start-api --host 0.0.0.0 --port 8000
```

## How To Check That Everything Works

### Quick Human Check

Run these:

```powershell
tradeforge init-db
tradeforge seed-sample-data
tradeforge run-backtest --strategy moving-average-cross --symbol AAPL --start 2023-01-01 --end 2023-01-08 --short-window 2 --long-window 3 --order-size 2
tradeforge show-orders
tradeforge show-pnl
```

If those work, the project is basically healthy.

### Automated Test Suite

Run:

```powershell
python -m pytest -q
```

The repo also has GitHub Actions CI that runs the same test command on pushes to `main` and pull requests.

## Common Problems

### Problem: `tradeforge` command is not found

Usually this means:

1. the virtual environment is not activated
2. the package was not installed yet

Fix:

```powershell
. .\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

### Problem: backtest says the symbol is unknown

This means the symbol is not in the database yet.

Fix:

1. run `tradeforge seed-sample-data`
2. or import your own CSV with `tradeforge import-csv`

### Problem: invalid date error

Use dates like:

```text
2023-01-01
```

or full ISO datetime strings.

### Problem: API page does not load

Make sure the API is running:

```powershell
tradeforge start-api
```

Then open `http://localhost:8000/docs`.

## For More Advanced Users

Important repo areas:

* `src/tradeforge/cli.py`
* `src/tradeforge/api/app.py`
* `src/tradeforge/database/`
* `src/tradeforge/broker_sim/`
* `src/tradeforge/backtesting/`
* `specs/001-core-trading-foundation/`
* `specs/002-live-market-data-valuation/`

If you are planning larger work, use the GitHub Spec workflow in `specs/`.

## Current Limitations

This repo is still early stage in a few important ways:

1. one built in strategy
2. one symbol per run
3. no stop orders
4. no partial fills
5. no short selling model
6. no live quote ingestion yet
7. no dashboard UI

## What Is Planned Next

The highest value next steps are:

1. configurable commission and slippage models
2. stop orders and cancel workflows
3. partial fill logic
4. more strategies
5. live quote based valuation from the `002` spec package

Useful planning docs:

* [specs/002-live-market-data-valuation/README.md](./specs/002-live-market-data-valuation/README.md)
* [specs/002-live-market-data-valuation/implementation-guide.md](./specs/002-live-market-data-valuation/implementation-guide.md)
* [specs/002-live-market-data-valuation/feed-options.md](./specs/002-live-market-data-valuation/feed-options.md)

## Disclaimer

TradeForge is for research and education only.

It is not financial advice.

It should not be used as live trading infrastructure.
