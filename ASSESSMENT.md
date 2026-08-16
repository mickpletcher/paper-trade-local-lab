# TradeForge Assessment

## Purpose

TradeForge is a local paper trading and historical research lab. It imports and validates bars, simulates strategies and orders, stores results, values positions with optional quotes, and automates maintenance. It does not place live trades.

## Current State

Historical execution supports market, limit, stop, and stop limit orders, partial fills, volume limits, quantity increments, commissions, slippage, risk limits, corporate actions, and durable decision audits. One built in moving average strategy can run against one symbol or allocated equal and fixed capital portfolio sleeves.

Research services add deterministic bar, tick, news, and system event ordering; vectorized signals; multiprocessing analytics; rolling volatility; benchmark and factor beta; market regimes; and immutable experiments with dataset and report hashes. Allowlisted Python entry points extend strategies, brokers, indicators, and reports.

Instrument value objects cover international equities, fixed income, rates, credit, volatility, index derivatives, CFDs, calendar spreads, OTC metals, and prediction contracts. Microstructure scenarios cover auctions, halts, price limits, odd lots, latency, queues, and market impact. Tradier, TradeStation, MetaTrader, NinjaTrader, cTrader, and crypto adapters construct quote requests, normalize responses, and create nontransmitting paper signals. These models and adapters do not route live orders.

The read only API includes health, metrics, research data, experiments, and an escaped server rendered dashboard. Optional expiring API keys provide viewer, operator, and admin roles plus tenant isolation. Authentication is off by default for loopback use. Symbols and quotes are shared reference data.

SQLite uses Alembic revision `006_tier_three_platform`, WAL, bounded lock waits, cached API engines, tenants, salted PBKDF2 verified API identities, and experiment records. Maintenance locks runs, archives or quarantines imports, refreshes quotes, records SQLite health, verifies backups, measures local RPO and RTO, applies retention, and sends deduplicated alerts.

The Windows first root manual covers installation, first and portfolio runs, analytics, API identities, dashboard use, automation, recovery, Docker, troubleshooting, and every public CLI command.

## Build And Dependencies

Python 3.11 through 3.14 is supported. Core dependencies are Typer, FastAPI, SQLAlchemy, Alembic, Pandas, Packaging, Pydantic Settings, and Uvicorn. Development adds HTTPX2, Ruff, strict Mypy, Pytest, coverage, Pip Audit, and CycloneDX. LEAN, backtesting.py, Zipline, Freqtrade, Hummingbot, CCXT, TA-Lib, and pandas-ta were evaluated but not added.

## Automation

CI bootstraps the lock on every supported Python version and enforces warning free tests, 88 percent coverage, strict typing, correctness mutations, migration and backtest benchmarks, package and container builds, security, governance, and repository policy. Conventional commits drive a gated semantic release preparation PR. Tagged releases and GHCR images publish SBOMs and signed provenance.

## Known Limitations

* Execution is completed bar based. It lacks time in force, shorting, settlement, and integrated order book simulation.
* Portfolio sleeves do not share cash or net exposure.
* Extended market models and connectors are isolated scenario and normalization layers.
* Money and quantities use floating point values.
* API authentication is opt in and provides no TLS, pagination, or versioning.
* Gap checks are not exchange calendar aware. Corporate actions are manually recorded.
* Local container validation requires Docker, which is unavailable on this workstation.

## Health

Overall health is good for a local research platform. The lock faithful suite has 172 warning free tests and 89.67 percent coverage. Ruff and strict Mypy pass across 67 source files. The 25,000 row migration gate and 100,000 row vectorized benchmark are enforced in CI.
