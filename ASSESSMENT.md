# TradeForge Assessment

## Purpose

TradeForge is a local paper trading and historical backtesting lab. It imports bars, values positions with live quotes, simulates orders, runs strategies, stores results, and exposes CLI and read only API views. It does not place live trades.

## Current State

The simulator supports market, limit, stop, and stop limit orders, partial fills, bar volume limits, configurable commission and slippage, and lifecycle trade records. Gross entry and exit prices plus separate fees reconcile to realized profit and loss. Quantities default to whole shares; cash limited fills round down to the configured increment.

Strategy context includes positions and pending quantities. Reversals cancel stale opposite orders, and exits cannot exceed inventory. Valuation preserves flat run cash. Moving average crossover is the only built in strategy. Backtests remain single symbol.

Alpaca refresh refuses redirects, retries transient failures, requires an exact requested symbol set, and validates provider output again before persistence. Quotes require timezone-aware timestamps, finite positive prices, nonnegative integer sizes, valid JSON, and a usable noncrossed market. Staleness uses the provider's market timestamp; retrieval age is reported separately.

Backtest reports include returns, CAGR, volatility, zero risk free Sharpe and Sortino ratios, drawdown, trade statistics, time exposure, and buy and hold comparison. Undefined ratios are explicit. Results use bar close snapshots and omit taxes and configurable risk free rates.

SQLite is versioned through Alembic revision `004_trade_fee_basis`. The API reuses one engine and session factory and disposes the engine at shutdown. `compose.yaml` is the only Compose definition and uses loopback binding plus hardened controls.

## Build And Dependencies

Python 3.11 or newer is required. Core dependencies are Typer, FastAPI, SQLAlchemy, Alembic, Pandas, Pydantic Settings, and Uvicorn. Settings are process cached, so environment changes require a restart. Development uses HTTPX2, Ruff, strict Mypy targeting Python 3.11, Pandas stubs, Pytest, and coverage. `requirements.lock` is generated from a universal Python 3.11 baseline. Warnings fail tests.

## Automation

`tradeforge run-maintenance` migrates SQLite, imports queued CSV files, refreshes quotes with bounded retry, verifies a backup, applies retention, and writes JSON reports. Its optional HTTPS webhook sends only failure status and timestamps and refuses redirects. A PowerShell installer registers daily execution with retry and catch up.

GitHub Actions runs Ruff, formatting, strict Mypy, lock drift, dependency review, dependency audit, CodeQL, and tests with an 88 percent coverage floor on Python 3.11, 3.13, and 3.14. CI builds and health checks the Python 3.14 container. Protected `main` requires strict security and quality checks. Repository policy requires full commit SHA action references and permits only GitHub owned plus explicitly allowed Astral and Docker actions.

## Known Limitations

* Execution uses bar approximations and does not model intrabar ordering, time in force, shorting, venues, market impact, or settlement.
* There is no risk engine, provider failover, account aggregation, or multi symbol backtest.
* Money and quantities remain floating point values despite quantity increment enforcement.
* Imports reprocess retained files and do not quarantine failures.
* Failure delivery uses one nonredirecting webhook without deduplication or escalation.
* The API has no authentication, pagination, or versioning and must remain on loopback or behind an authenticated proxy.
* Automated backup restore drills and maintenance concurrency locking are not implemented.
* Developer environments can contain undeclared packages without the current lock drift check reporting them.
* Local Compose and container validation require Docker, which is unavailable on this workstation.

## Health

Overall health is good for a local research MVP. The lock faithful suite has 107 tests, warning failures, and 90.20 percent statement coverage against an 88 percent floor. Ruff, strict Mypy, lock, build, audit, Markdown, governance, and GitHub container checks pass. Repository security alerts are clear as of 2026-08-15.
