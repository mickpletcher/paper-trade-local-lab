# TradeForge Assessment

## Purpose

TradeForge is a local first paper trading and strategy testing lab.

It is designed to let you import market data, run strategy tests, simulate fills, track positions, and inspect results on your own machine without live brokerage execution. The repo is intentionally focused on local simulation and research instead of live trading infrastructure.

## Current Status

The repo is in a strong MVP state and is more complete than a basic prototype.

The current foundation now includes:

1. A Typer CLI for database setup, sample data seeding, CSV import, backtest execution, API startup, and result inspection.
2. An Alembic based SQLite migration workflow with versioned revision files and CLI inspection commands.
3. A simulated broker with cash, positions, fills, fees, slippage, and basic trade tracking.
4. A historical backtest engine for the built in moving average crossover strategy.
5. Markdown report output for completed strategy runs.
6. A small FastAPI app with documented endpoint examples.
7. GitHub Actions CI that now runs lint, tests, package build validation, container build validation, and container publishing on `main`.
8. A repo level GitHub Spec workflow with numbered spec packages.
9. Structured JSON logging plus an opt in metrics endpoint for long running API deployments.
10. A first live quote valuation implementation using stored quotes, local valuation math, and quote or portfolio endpoints.
11. A `002` spec package that now serves as the implementation and expansion plan for live quote based valuation while keeping execution local.
12. A three layer documentation system with a landing page README, a canonical `docs/` tree, and a separate GitHub Wiki strategy for exploratory content.

## Architecture Snapshot

The repo structure is clean and easy to follow:

1. `src/tradeforge/cli.py`
   Main operator entry point.
2. `src/tradeforge/database/`
   Models, sessions, and versioned migrations.
3. `src/tradeforge/market_data/`
   CSV import, symbol handling, and replay helpers.
4. `src/tradeforge/broker_sim/`
   Simulated account, execution, orders, and positions.
5. `src/tradeforge/backtesting/`
   Strategy run orchestration and metrics.
6. `src/tradeforge/reporting/`
   Markdown report generation.
7. `src/tradeforge/api/`
   Local inspection API.
8. `specs/`
   Numbered GitHub Spec packages for non trivial work.

## What Works Well

1. Scope discipline

The repo stays focused on local paper trading and backtesting. Even the new live market data planning work is explicitly scoped to valuation only, not live execution.

2. Clear command surface

The CLI now covers the main operator workflow:

* `tradeforge init-db`
* `tradeforge seed-sample-data`
* `tradeforge import-csv`
* `tradeforge run-backtest`
* `tradeforge start-api`
* `tradeforge show-orders`
* `tradeforge show-positions`
* `tradeforge show-pnl`

3. Better correctness baseline

The local simulator now avoids same bar final signal fills and rejects invalid sells that exceed current position size.

4. Better operator experience

The repo now has:

* bundled sample data
* a one command API startup path
* clearer backtest validation errors
* OpenAPI response examples
* a more complete README and repo analysis trail

5. Better engineering hygiene

The repo now includes:

* formal Alembic migrations
* automated tests
* GitHub Actions CI
* package and container build validation
* GitHub Spec scaffolding for larger work
* a durable documentation architecture designed for contributor growth and AI retrieval

6. First live valuation slice is real

The repo can now refresh live quotes, store them separately from historical bars, and calculate current local portfolio valuation from those quotes.

## Current Constraints

1. Single built in strategy

Only `moving-average-cross` exists today.

2. Single symbol run model

Backtests are still one symbol per strategy run.

3. Simple execution model

The broker supports market and limit orders only. There is no stop order flow, partial fill model, short inventory model, or venue simulation yet.

4. Minimal API

The API is useful for inspection, but it still does not have a deeper contract layer, pagination, auth, or versioning.

5. Live quote support is still narrow

The first live valuation implementation is stock quote focused, provider limited, and refreshes on demand rather than through a background scheduler.

## Risks To Watch

1. Schema drift

The repo now has a formal migration path, but future data model changes must keep landing through Alembic revisions instead of direct table edits.

2. Execution realism drift

As new order types and market behaviors are added, the broker and valuation logic will become the highest risk areas for subtle errors.

3. Feature growth without boundaries

This repo can easily drift into live execution ideas if the local only rule is not maintained.

4. Data quality assumptions

CSV import still assumes clean OHLCV data. Broader source support will need stronger validation, duplicate handling, and gap checks.

5. Provider coupling risk

The first live quote implementation is built around Alpaca stock snapshots. Future provider additions need to keep the normalized quote boundary clean.

## Recommended Next Steps

1. Add configurable commission and symbol specific slippage models.
2. Add stop orders, stop limit orders, and cancel workflows.
3. Add partial fill logic with explicit execution rules.
4. Add at least one more built in strategy.
5. Add richer API coverage and versioning beyond the current inspection layer.
6. Add a background quote refresh path and quote staleness monitoring.
7. Add at least one second quote provider after the Alpaca path is stable.
8. Add data quality checks before import.
9. Fill in the new `docs/` placeholders with concrete architecture, provider, plugin, and operator content as implementation grows.

## Verification Snapshot

Current local verification after the latest completed changes:

1. Python package installs under Python 3.13.
2. The automated test suite passes.
3. Current result at the time of this update is `21 passed`.

## Bottom Line

This repo is a credible local trading simulation foundation with a clean structure, a usable command surface, a working test suite, and good planning discipline for future growth. The next phase should stay focused on execution realism, broader strategy support, and live quote based valuation without turning the project into live trading infrastructure.
