# TradeForge

[![CI](https://github.com/mickpletcher/paper-trade-local-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/mickpletcher/paper-trade-local-lab/actions/workflows/ci.yml)
[![Docs](https://github.com/mickpletcher/paper-trade-local-lab/actions/workflows/docs.yml/badge.svg)](https://github.com/mickpletcher/paper-trade-local-lab/actions/workflows/docs.yml)
[![Security](https://github.com/mickpletcher/paper-trade-local-lab/actions/workflows/security.yml/badge.svg)](https://github.com/mickpletcher/paper-trade-local-lab/actions/workflows/security.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](./pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)

TradeForge is a local first paper trading laboratory for strategy experimentation, historical backtesting, local valuation, and AI assisted research.

It is designed to grow into a professional research platform with strong privacy boundaries, pluggable components, and durable engineering workflows.

## Why TradeForge

TradeForge is built for teams and solo builders who want:

* local and offline friendly execution
* strategy research without live order routing
* historical backtest workflows that stay inspectable
* AI assisted development without hiding system behavior
* a path toward extensibility, multi provider data, and hardened local infrastructure

## Project Goals

* make local strategy research fast to start and easy to inspect
* keep execution simulated unless a future design explicitly says otherwise
* support backtesting, valuation, and AI assisted analysis from one codebase
* establish a platform shape that can support open source growth and commercial hardening later

## Current Feature Set

* Typer CLI for local workflows
* FastAPI inspection layer
* SQLite storage with Alembic migrations
* CSV import and seeded sample data
* simulated broker execution for local paper trading
* stop, stop limit, and cancel capable order simulation with aggregate volume aware partial fills
* limit price protection, marketable price improvement, and persistent stop triggers
* per order commission reconciliation and symbol specific slippage rules
* gross trade prices with separately recorded entry and exit fees
* whole share execution by default with a configurable quantity increment
* historical backtesting and markdown report output
* live quote refresh for local valuation
* unattended CSV import, quote refresh, verified backup, and failure reporting
* structured logging and optional metrics output
* CI for linting, lock drift, Python 3.11, 3.13, and 3.14 tests, builds, and container health

## Architecture Summary

TradeForge currently has four main layers:

1. operator surfaces through the CLI and local API
2. trading services for backtesting, simulation, valuation, and reporting
3. data services for historical bars, live quotes, and persistence
4. platform services for configuration, migrations, telemetry, and automation

Start with the canonical docs hub for deeper technical details:

* [docs/README.md](./docs/README.md)

## Local First Philosophy

TradeForge treats the local machine as the primary runtime.

That means:

* strategy state should be inspectable
* data storage should be understandable
* privacy should not depend on a hosted service
* automation should remain useful even without cloud dependencies

## AI Integration Philosophy

AI belongs in TradeForge as an accelerator for research, documentation, and development workflow.

AI does not replace transparent system design, source controlled contracts, or reproducible execution paths.

AI workflow guidance lives here:

* [docs/ai-integration/README.md](./docs/ai-integration/README.md)
* [docs/contributing/ai-documentation-workflow.md](./docs/contributing/ai-documentation-workflow.md)

## Screenshots

Planned visual assets:

* `docs/assets/cli-backtest-run.png`
* `docs/assets/api-docs-overview.png`
* `docs/assets/report-output-example.png`
* `docs/assets/architecture-overview.png`

## Installation

### Local Python setup

```powershell
py -3.13 -m venv .venv
. .\.venv\Scripts\Activate.ps1
python -m pip install --constraint requirements.lock -e ".[dev]"
tradeforge init-db
tradeforge seed-sample-data
```

### Container setup

```powershell
Copy-Item .env.example .env
docker compose up --build --detach
```

For platform specific setup guides:

* [docs/installation/README.md](./docs/installation/README.md)
* [docs/configuration/README.md](./docs/configuration/README.md)

## Quick Start

Run a sample backtest:

```powershell
tradeforge run-backtest --strategy moving-average-cross --symbol AAPL --start 2023-01-01 --end 2023-01-08 --short-window 2 --long-window 3 --order-size 2
```

Inspect the results:

```powershell
tradeforge show-orders
tradeforge show-pnl
tradeforge start-api --reload
```

Run the full maintenance path now or register it daily:

```powershell
tradeforge run-maintenance
.\scripts\Install-TradeForgeScheduledTask.ps1 -RunNow
```

Then open:

* `http://localhost:8000/docs`

## Documentation

Core entry points:

* [docs/README.md](./docs/README.md)
* [ASSESSMENT.md](./ASSESSMENT.md)
* [CHANGELOG.md](./CHANGELOG.md)
* [FUTURE-UPGRADES.md](./FUTURE-UPGRADES.md)
* [COMPLETED-UPGRADES.md](./COMPLETED-UPGRADES.md)
* [specs/README.md](./specs/README.md)
* [SECURITY.md](./SECURITY.md)
* [SUPPORT.md](./SUPPORT.md)

Repository governance is checked automatically on pushes, pull requests, and a weekly schedule. Run `./scripts/Test-ProjectGovernance.ps1 -CheckWorkingTree` before handing off local changes.

High value technical sections:

* [architecture](./docs/architecture/README.md)
* [backtesting](./docs/backtesting/README.md)
* [market-data](./docs/market-data/README.md)
* [database](./docs/database/README.md)
* [plugins](./docs/plugins/README.md)
* [security](./docs/security/README.md)

## Roadmap Summary

Current priorities are centered on:

* better execution realism
* stronger strategy research workflows
* broader market data support
* plugin architecture
* long running local operations and platform hardening

Tracked roadmap docs:

* [docs/roadmap/README.md](./docs/roadmap/README.md)
* [docs/roadmap/documentation-roadmap.md](./docs/roadmap/documentation-roadmap.md)
* [specs/002-live-market-data-valuation/README.md](./specs/002-live-market-data-valuation/README.md)
* [specs/003-execution-correctness/README.md](./specs/003-execution-correctness/README.md)

## GitHub Wiki

The Wiki is reserved for exploratory research and temporary design work.

It should not duplicate `docs/`.

* [GitHub Wiki](https://github.com/mickpletcher/paper-trade-local-lab/wiki)
* [Wiki strategy](./docs/contributing/wiki-strategy.md)

## Contributing

Contribution guidance starts here:

* [CONTRIBUTING.md](./CONTRIBUTING.md)
* [docs/contributing/README.md](./docs/contributing/README.md)
* [docs/contributing/documentation-governance.md](./docs/contributing/documentation-governance.md)

## Security And Support

The local API has no authentication. Compose binds it to loopback by default. Place it behind an authenticated reverse proxy before exposing it to another network.

* Report vulnerabilities privately through [SECURITY.md](./SECURITY.md).
* Use [SUPPORT.md](./SUPPORT.md) for setup help and issue-reporting guidance.
* Never commit `.env`, Alpaca credentials, local databases, generated reports, or private market data.

## Disclaimer

TradeForge is for research, experimentation, and education.

It is not financial advice.

It is not a live trading system.

Any market losses, operational errors, or strategy failures remain the responsibility of the operator.
