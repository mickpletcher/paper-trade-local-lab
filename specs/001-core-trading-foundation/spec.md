# Specification

## Summary

This spec captures the current TradeForge MVP as a local paper trading foundation. It defines the current module responsibilities, execution rules, local workflows, and verification expectations that future feature work must preserve unless a later spec intentionally changes them.

## Current State

The repo currently provides:

1. A Typer CLI for initialization, seeding, import, backtest execution, and result inspection.
2. SQLite persistence with versioned schema setup.
3. A CSV importer for OHLCV market data.
4. A simulated broker for market and limit orders.
5. A single symbol backtest engine.
6. Markdown report generation.
7. A minimal FastAPI inspection layer.
8. Automated tests for core behavior.

## Proposed Design

This baseline package does not introduce new behavior. It documents the current working design.

The core design points are:

1. TradeForge remains local only by default.
2. Schema setup runs through `src/tradeforge/database/migrations.py`.
3. Sample data is stored as package data under `src/tradeforge/sample_data/`.
4. Strategy runs use the current `BacktestEngine` and `SimBroker` path.
5. Final bar generated signals are not filled on that same bar.
6. Invalid sells are rejected instead of creating synthetic inventory.

## Module Changes

Baseline module ownership:

1. `src/tradeforge/cli.py`
   Main operator entry point.
2. `src/tradeforge/database/`
   Models, sessions, and migration state.
3. `src/tradeforge/market_data/`
   Symbol handling, CSV import, and bar replay.
4. `src/tradeforge/broker_sim/`
   Account, order submission, fill handling, and position updates.
5. `src/tradeforge/backtesting/`
   Run orchestration and metrics.
6. `src/tradeforge/reporting/`
   Markdown report output.
7. `src/tradeforge/api/`
   Local inspection endpoints.

## Data Model And Migration Impact

The baseline schema includes:

1. `schema_migrations`
2. `symbols`
3. `price_bars`
4. `strategies`
5. `strategy_runs`
6. `orders`
7. `fills`
8. `positions`
9. `trades`
10. `account_snapshots`

Current migration state is version `1`.

## CLI Impact

Current baseline commands:

1. `tradeforge init-db`
2. `tradeforge seed-sample-data`
3. `tradeforge import-csv`
4. `tradeforge run-backtest`
5. `tradeforge show-orders`
6. `tradeforge show-positions`
7. `tradeforge show-pnl`

## API Impact

Current baseline endpoints:

1. `GET /health`
2. `GET /symbols`
3. `GET /positions`
4. `GET /orders`
5. `GET /strategy-runs`

## Reporting Impact

Completed backtests write a markdown report under `data/reports/<strategy-run-id>.md`.

## Testing Strategy

The baseline test suite should continue to cover:

1. Database initialization
2. Migration version tracking
3. CSV import upsert behavior
4. Market and limit order behavior
5. Invalid sell rejection
6. Backtest completion
7. Final bar no lookahead behavior
8. End to end CLI flow

## Risks

1. Execution realism changes can break cash or position accounting.
2. Schema changes can drift if future work bypasses the migration path.
3. New features can outgrow the current one symbol assumptions quickly.

## Rollout Notes

Future non trivial work should reference this package before creating the next numbered spec folder.
