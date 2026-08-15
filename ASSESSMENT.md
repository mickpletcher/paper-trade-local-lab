# TradeForge Assessment

## Purpose

TradeForge is a local first paper trading and historical backtesting lab. It imports price bars, refreshes live quotes for valuation, simulates orders, runs strategies, stores results locally, and exposes CLI plus read only API views. It does not place live trades.

## Current State

The simulator supports market, limit, stop, and stop limit orders, partial fills, aggregate bar volume limits, configurable commission and slippage, and lifecycle trade records. Gross weighted entry and exit prices are stored separately from entry and exit fees so reported realized profit and loss reconciles. Quantities default to whole shares and use a configurable positive increment for deliberate fractional testing. Cash limited fills round down to that increment.

Strategy context includes actual positions and pending quantities. Reversals cancel stale opposite orders, and exits cannot exceed inventory. Portfolio valuation preserves cash for flat runs and uses deterministic current quotes. Alpaca refresh validates the provider response, retries transient failures, and rejects incomplete symbol sets. The moving average crossover remains the only built in strategy. Backtests query stored historical bars directly and remain single symbol.

Backtest reports include returns, CAGR, annualized volatility, zero risk free Sharpe and Sortino ratios, drawdown, profit factor, win and loss averages, time exposure, and a same period buy and hold benchmark. Undefined ratios are explicit instead of becoming misleading zeros. Results still use bar close equity snapshots and do not model taxes or a configurable risk free rate.

SQLite is versioned through Alembic revision `004_trade_fee_basis`. The API reuses one application engine and session factory, joins scalar endpoint relationships in one statement, then disposes the engine at shutdown. Explicit database engines remain uncached. `compose.yaml` is the only Compose definition and applies loopback binding plus hardened container controls.

## Build And Dependencies

Python 3.11 or newer is required. Core dependencies are Typer, FastAPI, SQLAlchemy, Alembic, Pandas, Pydantic Settings, and Uvicorn. Validated settings are cached for each process. Development tests use HTTPX2. `requirements.lock` pins runtime, development, and audit dependencies from a universal Python 3.11 baseline. Pytest treats every warning as an error.

## Automation

`tradeforge run-maintenance` initializes or upgrades SQLite, imports queued CSV files, refreshes quotes for open positions with bounded retry, creates and integrity checks a backup, applies retention, and writes success or failure JSON reports. An optional webhook reports failures. A PowerShell installer registers daily execution with retry and catch up behavior.

GitHub Actions runs Ruff, lock drift checks, warning free tests on Python 3.11, 3.13, and the container's Python 3.14 runtime, package builds, container health validation, governance checks, dependency review, scheduled audits, releases, and GHCR publishing. Protected `main` requires strict checks and squash merges.

## Known Limitations

* Execution uses bar approximations and does not model intrabar ordering, time in force, shorting, venues, market impact, or settlement.
* There is no risk engine, provider failover, account aggregation, or multi symbol backtest.
* Money and quantities remain floating point values despite quantity increment enforcement.
* Imports reprocess retained files and do not quarantine failures.
* Failure delivery uses one webhook without deduplication or escalation.
* The API has no authentication, pagination, or versioning and must remain on loopback or behind an authenticated proxy.
* Automated backup restore drills are not implemented.
* Developer environments can contain undeclared packages without the current lock drift check reporting them.
* Local Compose and container validation require Docker, which is unavailable on this workstation.

## Health

Overall health is good for a local research MVP. The lock faithful suite has 83 tests with warnings treated as errors. Ruff, reproducible lock, package build, dependency audit, Markdown, and governance checks pass. GitHub remains responsible for container build and runtime validation because Docker is unavailable locally.
