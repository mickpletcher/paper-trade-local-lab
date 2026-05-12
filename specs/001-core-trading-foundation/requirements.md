# Requirements

## Problem

TradeForge needs a clear baseline specification for its current local paper trading foundation. Without that baseline, future work on order handling, migrations, strategy expansion, API growth, or data adapters can drift away from the current repo intent.

## Goals

1. Define the current MVP scope in durable repo local form.
2. Capture the expected behavior of local data import, local simulation, backtesting, reporting, and inspection workflows.
3. Establish the documentation and verification standards that future features must preserve.
4. Create a stable baseline package that future numbered specs can build on.

## Non Goals

1. Introduce live trading support.
2. Add new execution features beyond the current MVP.
3. Redesign the repo structure.
4. Replace the current strategy model.

## Functional Requirements

1. The repo must support local schema initialization through a versioned migration path.
2. The repo must support importing OHLCV CSV data for a symbol into local SQLite storage.
3. The repo must support seeding a bundled sample dataset for first run validation.
4. The repo must support running a historical backtest for the built in moving average crossover strategy.
5. The repo must track orders, fills, positions, trades, strategy runs, and account snapshots in the local database.
6. The local broker must reject invalid sell orders that exceed current held quantity.
7. The backtest engine must not fill signals generated from the final bar on that same final bar.
8. The repo must generate markdown reports for completed backtests.
9. The repo must expose local inspection endpoints for health, symbols, positions, orders, and strategy runs.
10. The repo must include automated tests for the core local workflows.

## Non Functional Requirements

1. The repo must remain local first and offline by default.
2. The implementation should stay simple and maintainable.
3. Tests must run locally with Python and pytest.
4. Documentation must be detailed enough for a new operator to get the repo running without scanning the codebase.

## Acceptance Criteria

1. A user can initialize the database, seed sample data, run a backtest, and inspect outputs through the CLI.
2. The database schema is tracked through `schema_migrations`.
3. Regression tests cover invalid sells and final bar behavior.
4. The README documents setup, configuration, commands, API usage, Docker usage, and current limitations.
5. The repo contains a numbered spec package that documents the current baseline.

## Open Questions

1. When the schema evolves further, should the repo move from the current lightweight migration layer to Alembic.
2. Which future execution realism feature should become spec `002`.
