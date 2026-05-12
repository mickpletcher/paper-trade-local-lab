# TradeForge Assessment

## Purpose

TradeForge is a local first paper trading and strategy testing lab. It is built to mimic trading behavior on a single machine so strategies can be tested without any live brokerage connectivity. The current repo supports CSV import, local SQLite persistence, simulated order handling, historical backtests, markdown report output, a minimal API surface, and a small but useful automated test suite.

## Current Status

The repo is in a solid MVP state.

The core architecture is clean and easy to extend:

1. `src/tradeforge/cli.py` exposes the main local workflows.
2. `src/tradeforge/database/` holds schema, sessions, and versioned migrations.
3. `src/tradeforge/market_data/` handles CSV import and bar replay.
4. `src/tradeforge/broker_sim/` handles simulated account, orders, execution, and positions.
5. `src/tradeforge/backtesting/` runs strategy evaluation and metrics.
6. `src/tradeforge/reporting/` writes markdown reports.
7. `src/tradeforge/api/` provides a small FastAPI scaffold for local inspection.

The repo now includes the following key quality improvements:

1. Final bar lookahead behavior was fixed. Orders generated from the last bar are no longer filled on that same bar.
2. Invalid sell behavior was fixed. The local broker now rejects sells that exceed current held quantity.
3. A real migration path exists through `schema_migrations` instead of relying only on `create_all()`.
4. A bundled sample dataset exists at `src/tradeforge/sample_data/aapl_sample.csv`.
5. A repeatable first run command exists through `tradeforge seed-sample-data`.
6. Regression coverage now includes execution edge cases, migration checks, and an end to end CLI flow.

## What Works Well

1. Scope discipline

The project stays focused on local paper trading and backtesting. It does not blur into live execution concerns.

2. Clear package layout

The module boundaries are sensible for an MVP and should scale for the next round of features.

3. Good local developer experience

The CLI surface is small and understandable. `init-db`, `seed-sample-data`, `import-csv`, `run-backtest`, `show-orders`, `show-positions`, and `show-pnl` cover the core local workflows.

4. Useful test baseline

The repo now has fast tests that cover import, persistence, order execution, backtest completion, migration state, and CLI behavior.

5. Practical deployment path

Docker and Compose support make it easy to run the local API and persist data in the repo `data` folder.

## Current Constraints

1. Single strategy implementation

Only `moving-average-cross` is available today.

2. Single symbol backtest model

The engine is still centered on one symbol per run.

3. Simple execution model

The simulator supports market and limit orders, but not stop orders, partial fills, volume aware fills, latency, or venue behavior.

4. No formal API contract layer

The API is intentionally minimal and does not yet have request or response models, pagination, or versioning.

5. No first class research workflow features yet

There is no parameter sweep engine, no walk forward testing, no optimization harness, and no dashboard.

## Risks To Watch

1. Schema evolution

The repo now has versioned migrations, but future schema changes need to keep using that path consistently.

2. Simulation realism drift

As new order types and asset classes get added, the broker logic will become the highest risk area for subtle accuracy bugs.

3. Report and metrics depth

The current output is good for basic verification, but more advanced research will need richer trade analytics and drawdown views.

4. Market data assumptions

The importer assumes a clean OHLCV CSV shape. If broader data sources are introduced, validation and normalization will need to get stricter.

## Recommended Next Steps

1. Add configurable commission and slippage models by symbol or asset class.
2. Add stop and stop limit orders.
3. Add partial fill behavior with explicit fill rules.
4. Add parameter sweep support for the existing moving average strategy.
5. Add at least one more built in strategy to prove the strategy interface is flexible.
6. Add API tests for all current endpoints.
7. Add a dedicated CLI command to run the FastAPI app so local startup uses one command surface.
8. Add data quality checks for gaps, duplicates, and timestamp issues before import.

## Verification Snapshot

Current local verification completed after the latest changes:

1. Python package installed successfully with Python 3.13.
2. Automated tests passed.
3. Result at the time of validation was `10 passed`.

## Bottom Line

This repo is a credible local trading simulation foundation. The architecture is clean, the intent is clear, and the recent fixes addressed the most important correctness problems in the local execution path. The next phase should focus on execution realism, broader strategy support, and stronger research workflows without expanding scope too quickly.
