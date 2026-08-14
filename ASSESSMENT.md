# TradeForge Assessment

## Purpose

TradeForge is a local first paper trading and backtesting lab. It imports historical data, refreshes live quotes for valuation, simulates orders, runs strategies, stores results locally, and exposes CLI and read only API views. It does not place live trades.

## Current State

The MVP supports market, limit, stop, and stop limit orders with cancellation, partial fills, aggregate bar volume limits, configurable commission and slippage, cash and position accounting, and lifecycle trade records. The moving average crossover strategy is the only built in strategy. Backtests operate on one symbol per run.

SQLite persistence is versioned through Alembic. Revision `003_execution_realism` is the current head. Reports are Markdown. Live quotes use an Alpaca adapter and remain separate from historical execution data.

## Build And Dependencies

The application uses Python 3.13, Typer, FastAPI, SQLAlchemy, Alembic, Pydantic Settings, Uvicorn, Prometheus Client, and HTTPX. Development checks use Pytest, Ruff, Build, and Markdownlint. Container packaging uses Docker and publishes to GHCR from GitHub Actions.

## Automation

GitHub Actions runs lint, tests, package builds, container validation, documentation checks, and image publishing. A governance workflow runs on pushes, pull requests, manual dispatch, and a weekly schedule. It fails when a change omits any required living document or when their structure drifts.

The local equivalent is:

```powershell
./scripts/Test-ProjectGovernance.ps1 -CheckWorkingTree
```

## Known Limitations

* Quote refresh and data import still require manual commands.
* No retry queue, failure notification, or automatic provider failover exists.
* Execution uses bar based approximations and does not model intrabar ordering, time in force, shorting, venues, or market impact.
* The API has no authentication, pagination, or versioning.
* Money is stored as floating point values.
* Local container validation requires Docker, which was unavailable during the latest change.

## Health

Overall health is good for a local research MVP. The suite has 41 passing tests on Python 3.11 and 3.13 with 86 percent coverage. Ruff, package builds, migration round trips, dependency audit, configured Markdown checks, and governance validation pass locally. Container validation remains delegated to GitHub Actions.
