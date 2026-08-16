# TradeForge Assessment

## Purpose

TradeForge is a local paper trading and historical backtesting lab. It imports bars, values positions with live quotes, simulates orders, runs strategies, stores results, and exposes CLI and read only API views. It does not place live trades.

## Current State

The simulator supports market, limit, stop, and stop limit orders, partial fills, bar volume limits, configurable commission and slippage, and lifecycle trade records. Quantities default to whole shares.

Strategy context includes positions and pending quantities. Reversals cancel stale opposite orders, and exits cannot exceed inventory. Valuation preserves flat run cash. Moving average crossover is the only built in strategy. Backtests remain single symbol.

Alpaca refresh refuses redirects, retries transient failures, requires an exact symbol set, and validates quote values. Existing rows load in one set based query. Staleness uses the provider timestamp.

Backtest reports include returns, CAGR, volatility, risk ratios, drawdown, trade statistics, exposure, and buy and hold comparison. Results use bar close snapshots.

SQLite is versioned through Alembic revision `004_trade_fee_basis`. File database engines initialize persistent WAL once and apply a configurable five second lock wait per connection. The API reuses one engine and session factory until shutdown. Each maintenance run honors its selected lock settings, reuses one engine, then disposes it. `compose.yaml` is the only Compose definition and uses loopback binding plus hardened controls.

## Build And Dependencies

Python 3.11 or newer is required. Core dependencies are Typer, FastAPI, SQLAlchemy, Alembic, Pandas, Pydantic Settings, and Uvicorn. Development uses HTTPX2, Ruff, strict Mypy, Pytest, and coverage. `requirements.lock` uses a universal Python 3.11 baseline. Warnings fail tests.

## Automation

`tradeforge run-maintenance` migrates SQLite, imports queued CSV files, refreshes quotes with bounded retry, verifies a backup, applies retention, and writes JSON reports. Its optional HTTPS webhook sends only failure status and timestamps and refuses redirects. A PowerShell installer registers daily execution with retry and catch up.

GitHub Actions runs Ruff, formatting, strict Mypy, lock drift, dependency review, dependency audit, CodeQL, and tests with an 88 percent coverage floor on Python 3.11, 3.13, and 3.14. A Windows job validates the Task Scheduler installer without mutating the runner. CI builds and health checks the Python 3.14 container. Protected `main` requires strict security and quality checks. Repository policy requires full commit SHA action references and permits only GitHub owned plus explicitly allowed Astral and Docker actions.

## Known Limitations

* Execution uses bar approximations and does not model intrabar ordering, time in force, shorting, venues, market impact, or settlement.
* There is no risk engine, provider failover, account aggregation, or multi symbol backtest.
* Money and quantities remain floating point values despite quantity increment enforcement.
* Imports reprocess retained files and do not quarantine failures.
* Failure delivery uses one nonredirecting webhook without deduplication or escalation.
* The API has no authentication, pagination, or versioning and must remain on loopback or behind an authenticated proxy.
* Automated backup restore drills and maintenance concurrency locking are not implemented.
* Windows CI mocks the Scheduler cmdlets and does not register a disposable real task.
* Developer environments can contain undeclared packages without the current lock drift check reporting them.
* Local Compose and container validation require Docker, which is unavailable on this workstation.

## Health

Overall health is good for a local research MVP. The lock faithful suite has 113 tests, warning failures, and 90.31 percent statement coverage against an 88 percent floor. Focused Windows scheduler validation passes locally. Ruff, strict Mypy, lock, build, audit, Markdown, governance, and GitHub container checks pass. Repository security alerts are clear as of 2026-08-16.
