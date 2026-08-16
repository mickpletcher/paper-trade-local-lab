# TradeForge Assessment

## Purpose

TradeForge is a local paper trading and historical backtesting lab. It imports and validates bars, values positions with live quotes, simulates orders, runs strategies, stores results, and exposes CLI and read only API views. It does not place live trades.

## Current State

The simulator supports market, limit, stop, and stop limit orders, partial fills, bar volume limits, configurable commissions and slippage, and lifecycle trade records. A risk engine enforces cumulative per order fill notional, position quantity, gross exposure, maximum drawdown, and a kill switch. Durable audit events record triggers, cancellations, rejections, remaining quantity changes, and corporate actions.

CSV imports normalize UTC timestamps, remove duplicate timestamps, flag gaps, reject price outliers, validate OHLCV, and store repair findings. Splits adjust positions and pending orders. Delistings realize trade profit and loss, cancel orders, and stop later strategy execution. Corporate actions are processed once in timestamp order. Moving average crossover remains the only built in strategy, and backtests remain single symbol.

Alpaca refresh rejects redirects, validates exact symbol coverage, applies bounded exponential retry with jitter, and opens a persistent circuit breaker during extended outages. Valuation preserves flat run cash.

SQLite is versioned through Alembic revision `005_tier_one_controls`. File databases use WAL and bounded lock waits. The API reuses one engine until shutdown, and synthetic validation closes raw connections explicitly. Maintenance uses an atomic concurrency lock, one engine, import archive and quarantine with filename safe retry, SQLite telemetry, verified backup and restore drill, nonfatal reported retention errors, and Teams, email, or minimal webhook escalation.

## Build And Dependencies

Python 3.11 or newer is required. Core dependencies are Typer, FastAPI, SQLAlchemy, Alembic, Pandas, Packaging, Pydantic Settings, and Uvicorn. Development adds HTTPX2, Ruff, strict Mypy, Pytest, coverage, Pip Audit, and CycloneDX. The universal lock has verified digest and source metadata. Warnings fail tests.

## Automation

`python scripts/bootstrap.py` installs locked validation dependencies and runs `tradeforge doctor`. `tradeforge health` gives an exit coded local summary. The PowerShell installer registers daily maintenance with retry and catch up.

GitHub Actions runs tests with an 88 percent coverage floor on Python 3.11, 3.13, and 3.14, strict Mypy on 3.11 through 3.14, mutation and migration performance gates, a real Windows scheduler canary, security review, policy drift detection, compatibility canaries, and a nonblocking Python prerelease canary. GHCR publication depends on every build, container, typing, mutation, and migration gate. Repeated failures open one deduplicated issue. Trusted Dependabot updates synchronize living docs. Releases and GHCR publish SBOM and signed provenance.

## Known Limitations

* Execution uses bar approximations and does not model intrabar ordering, time in force, shorting, venues, market impact, or settlement.
* There is no provider failover, account aggregation, or multi symbol backtest.
* Money and quantities remain floating point values despite quantity increment enforcement.
* The API has no authentication, pagination, or versioning and must remain on loopback or behind an authenticated proxy.
* Data gap checks use elapsed days rather than an exchange calendar.
* Corporate actions are manually recorded and are not reconciled against an external feed.
* Local Compose and container validation require Docker, which is unavailable on this workstation.

## Health

Overall health is good for a local research MVP. The lock faithful suite has 149 tests with warnings treated as errors and 90.08 percent statement coverage against an 88 percent floor. Ruff, strict Mypy, environment and provenance verification, three correctness mutations, and the 25,000 row migration gate pass locally. Windows installer validation passes locally; the real scheduler and container canaries require hosted runners. Repository security alerts were clear on 2026-08-16.
