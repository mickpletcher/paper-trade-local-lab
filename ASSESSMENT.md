# TradeForge Assessment

## Purpose

TradeForge is a local first paper trading and backtesting lab. It imports historical data, refreshes live quotes for valuation, simulates orders, runs strategies, stores results locally, and exposes CLI and read only API views. It does not place live trades.

## Current State

The simulator supports market, limit, stop, and stop limit orders, partial fills, aggregate bar volume limits, configurable commission and slippage, cash and position accounting, and lifecycle trade records. Strategy context includes actual and pending quantities. Reversal signals cancel stale opposite orders, and exits cannot exceed inventory. Moving average parameters fail fast when invalid.

Portfolio valuation selects one explicit or latest strategy run, preserves cash for flat runs, and deterministically uses the newest quote. Alpaca refresh retries transient failures and rejects missing, duplicate, or unexpected symbols. CSV imports reject invalid OHLC relationships, nonpositive prices, and invalid volume. The moving average crossover is the only built in strategy. Backtests remain single symbol.

SQLite is versioned through Alembic at revision `003_execution_realism`. Reports are Markdown. Live quotes remain separate from historical execution data.

## Build And Dependencies

The application supports Python 3.11 and 3.13 and uses Typer, FastAPI, SQLAlchemy, Alembic, Pandas, Pydantic Settings, and Uvicorn. `requirements.lock` pins transitive runtime and development dependencies from a host independent Python 3.11 baseline. Build tooling, GitHub Actions, Markdownlint, and the Docker base image are version or digest pinned. Dependabot tracks Python, Actions, and Docker updates.

The container runs as an unprivileged user, includes a database aware health check, excludes `.env`, and has a loopback only, read only, capability dropped Compose profile with restart policy and an initialized managed data volume.

## Automation

`tradeforge run-maintenance` creates SQLite parent paths, initializes or upgrades the database, imports every `data/imports/<TICKER>.csv`, refreshes quotes for open positions with capped retry, creates and integrity checks a SQLite backup, applies retention, and writes success or failure JSON reports. An optional webhook reports failures. A PowerShell installer registers the job daily with retry and catch up behavior.

GitHub Actions checks Ruff, dependency lock drift, tests on Python 3.11 and 3.13, package builds, container startup health, documentation, and governance. Successful `main` builds publish to GHCR. Protected `main` requires strict checks, linear history, resolved conversations, and pull requests. Only squash merge is enabled.

The local equivalent is:

```powershell
python -m pytest -q
python -m ruff check .
./scripts/Test-ProjectGovernance.ps1 -CheckWorkingTree
```

## Known Limitations

* Execution uses bar based approximations and does not model intrabar ordering, time in force, shorting, venues, or market impact.
* There is no risk engine, provider failover, account level aggregation, or multi symbol backtest.
* Scheduled imports reprocess retained CSV files and do not quarantine failed inputs.
* Failure delivery is one generic webhook with no duplicate suppression or escalation policy.
* The API has no authentication, pagination, or versioning, so supported launch paths keep it on loopback.
* Money is stored as floating point values.
* Backups are integrity checked, but automated restore drills are not implemented.

## Health

Overall health is good for a local research MVP. The local suite has 68 passing tests on Python 3.11. Ruff, package build, migration tests, dependency audit, and governance validation pass. GitHub validates Python 3.11 and 3.13 plus container runtime health because Docker is unavailable on this workstation.
