You are building a new GitHub project named TradeForge.

Goal:
Create a local first paper trading and strategy testing platform that does not require a brokerage account. The system should run locally, use SQLite for persistence, support historical market replay, backtesting, simulated order execution, modular trading strategies, and future AI assisted trading research.

Primary stack:
Python 3.12
SQLite
SQLAlchemy
Typer CLI
Pandas
Pydantic
Pytest
Optional FastAPI scaffold for future dashboard/API support

Build the initial repository scaffold and working MVP.

Repository structure:

tradeforge/
  src/
    tradeforge/
      __init__.py
      cli.py
      config.py
      database/
        __init__.py
        models.py
        session.py
        migrations.py
      market_data/
        __init__.py
        importer.py
        providers.py
        replay.py
      broker_sim/
        __init__.py
        account.py
        orders.py
        execution.py
        portfolio.py
      strategies/
        __init__.py
        base.py
        moving_average_cross.py
      backtesting/
        __init__.py
        engine.py
        metrics.py
      reporting/
        __init__.py
        reports.py
      api/
        __init__.py
        app.py
  data/
    imports/
    tradeforge.db
  tests/
    test_database.py
    test_orders.py
    test_backtest.py
  README.md
  pyproject.toml
  .gitignore
  .env.example

Functional requirements:

1. SQLite persistence
Create SQLAlchemy models for:
- Symbol
- PriceBar
- Order
- Fill
- Position
- Trade
- Strategy
- StrategyRun
- AccountSnapshot

Use UUID primary keys where appropriate.
Use timestamps.
Use indexes for symbol, timestamp, strategy run, and order status.

2. CLI
Use Typer to create commands:

tradeforge init-db
tradeforge import-csv --symbol AAPL --file ./data/imports/aapl.csv
tradeforge run-backtest --strategy moving-average-cross --symbol AAPL --start 2023-01-01 --end 2024-01-01
tradeforge show-positions
tradeforge show-orders
tradeforge show-pnl

3. CSV import
Support OHLCV CSV files with columns:
date, open, high, low, close, volume

Normalize dates.
Validate missing data.
Upsert price bars into SQLite.

4. Paper broker simulation
Implement:
- Market orders
- Limit orders
- Buy and sell sides
- Cash balance
- Position tracking
- Average cost
- Realized P/L
- Unrealized P/L
- Basic fee/slippage model

The simulated broker should not connect to a real brokerage.

5. Matching/execution engine
For backtesting:
- Market orders fill at the next candle open.
- Limit buy fills if candle low is less than or equal to limit price.
- Limit sell fills if candle high is greater than or equal to limit price.
- Track fills, orders, positions, and cash.

6. Strategy system
Create a base Strategy class.
Create a sample MovingAverageCrossStrategy:
- short window default: 20
- long window default: 50
- buys when short MA crosses above long MA
- sells when short MA crosses below long MA
- supports configurable order size

7. Backtesting engine
The engine should:
- Load price bars from SQLite
- Run strategy sequentially across candles
- Submit simulated orders
- Process fills
- Update portfolio
- Write strategy run results
- Generate account snapshots
- Return summary metrics

8. Metrics
Calculate:
- Starting cash
- Ending equity
- Total return
- Number of trades
- Win rate
- Max drawdown
- Realized P/L
- Unrealized P/L

9. Reports
Generate a Markdown report after each backtest:
data/reports/<strategy-run-id>.md

Include:
- Strategy name
- Symbol
- Date range
- Parameters
- Metrics
- Trades table
- Final positions

10. FastAPI scaffold
Create a minimal FastAPI app with endpoints:
GET /health
GET /symbols
GET /positions
GET /orders
GET /strategy-runs

Do not overbuild the UI yet.

11. Tests
Create pytest tests for:
- Database initialization
- CSV import
- Market order execution
- Limit order execution
- Position updates
- Moving average strategy signal generation
- Backtest run completion

12. README
Generate a professional README.md with:
- Project name
- Description
- Features
- Architecture
- Installation
- CLI usage
- Example CSV format
- Example backtest command
- Roadmap
- Disclaimer that this is for research and education only and not financial advice

13. Code quality
Use type hints.
Use dataclasses or Pydantic where helpful.
Keep modules clean and separated.
Do not hardcode absolute paths.
Use pathlib.
Use logging instead of print except CLI output.
Make the app runnable immediately after install.

14. Security and safety
Do not include real brokerage credentials.
Do not create live trading functionality.
Do not make financial recommendations.
Do not send data externally by default.
Keep the project local first and offline capable.

Deliverables:
- Full project scaffold
- Working CLI MVP
- SQLite schema
- Sample strategy
- Sample tests
- README
- pyproject.toml

After creating the files, run tests and fix failures.
Then provide a concise implementation summary and next steps.