# TradeForge Assessment

## Purpose

TradeForge is a local paper trading and historical backtesting lab. It imports and validates bars, values positions with live quotes, simulates orders, runs strategies, stores results, and exposes CLI and read only API views. It does not place live trades.

## Current State

The simulator supports market, limit, stop, and stop limit orders, partial fills, bar volume limits, configurable commissions and slippage, and lifecycle trade records. Risk controls cover cumulative order notional, position quantity, gross exposure, drawdown, and a kill switch. Audit events persist triggers, cancellations, rejections, remaining quantities, and corporate actions.

CSV import normalizes timestamps, removes duplicates, flags gaps, rejects outliers, validates OHLCV, and stores findings. Splits adjust positions and pending orders. Delistings reconcile cash, positions, trades, and orders before later execution stops. Moving average crossover is the only built in strategy, and backtests remain single symbol.

Alpaca refresh rejects redirects, validates symbol coverage, uses bounded retry with jitter, and opens a persistent circuit breaker during outages. Valuation preserves flat run cash.

SQLite uses Alembic revision `005_tier_one_controls`, WAL, and bounded lock waits. The API reuses one engine until shutdown. Maintenance adds a concurrency lock, import archive and quarantine with safe retry, SQLite telemetry, verified backup and restore drills, retention reporting, and optional Teams, email, or webhook escalation.

The root README is a Windows first novice manual for installation, first run verification, data, configuration, results, API use, scheduling, recovery, database restoration, Docker, updates, reset, removal, troubleshooting, and every public CLI command.

## Build And Dependencies

Python 3.11 through 3.14 is supported. Core dependencies are Typer, FastAPI, SQLAlchemy, Alembic, Pandas, Packaging, Pydantic Settings, and Uvicorn. Development adds HTTPX2, Ruff, strict Mypy, Pytest, coverage, Pip Audit, and CycloneDX. The universal lock has cross platform digest and source verification. Warnings fail tests.

## Automation

`python scripts/bootstrap.py` installs locked dependencies and runs `tradeforge doctor`. `tradeforge health` gives an exit coded local summary. PowerShell installs daily maintenance with retry and catch up.

GitHub Actions tests supported Python versions with an 88 percent coverage floor, strict typing, correctness mutations, migration performance, Windows scheduler, security, policy drift, compatibility, and prerelease gates. GHCR publication waits for every required gate. Repeated failures create one deduplicated issue. Trusted Dependabot changes synchronize living docs. Releases and GHCR publish SBOM and signed provenance.

## Known Limitations

* Execution uses bar approximations and does not model intrabar ordering, time in force, shorting, venues, market impact, or settlement.
* There is no provider failover, account aggregation, or multi symbol backtest.
* Money and quantities remain floating point values despite quantity increment enforcement.
* The API has no authentication, pagination, or versioning and must remain on loopback or behind an authenticated proxy.
* Gap checks use elapsed days instead of an exchange calendar.
* Corporate actions are manually recorded and not reconciled against an external feed.
* Local container validation requires Docker, which is unavailable on this workstation.

## Health

Overall health is good for a local research MVP. The lock faithful suite has 150 warning free tests and 90.12 percent coverage. Ruff, strict Mypy, environment and provenance checks, three correctness mutations, and the 25,000 row migration gate pass locally. Hosted runners cover the real scheduler and container canaries. Repository security alerts were clear on 2026-08-16.
