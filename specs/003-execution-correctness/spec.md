# Specification

## Summary

This change establishes explicit execution invariants for the local simulator and corrects the accounting and persistence paths that depend on them.

## Current State

The pending execution model supports stop orders, stop limit orders, partial fills, cancellation, configurable commissions, and symbol specific slippage. The reviewed implementation did not consistently preserve those semantics across multiple bars or multiple orders.

## Proposed Design

1. Calculate `floor(bar.volume * max_bar_fill_ratio)` once and decrement that aggregate budget after each fill.
2. Persist `triggered_at` for stop and stop limit orders. A triggered stop acts as a market order on later bars.
3. Match marketable limits at the bar open and touched limits at the limit price. Apply slippage without crossing the limit boundary.
4. Persist cumulative `commission_paid` on each order. Commission models return total commission due for cumulative filled quantity, and each fill stores only the incremental amount.
5. Include buy commissions in average cost. Recognize realized profit and loss only during sells, including the sell commission once.
6. Maintain one open `Trade` per strategy run and symbol position lifecycle. Aggregate partial entries, partial exits, average exit price, and realized profit and loss into that row until the position is flat.
7. Scope `SimBroker` to one `strategy_run_id`, including the `None` manual scope, and reject mismatched submissions.
8. Filter eligible orders by `submitted_at <= bar.timestamp`.
9. Enable SQLite foreign keys on every application engine connection.

## Module Changes

1. `src/tradeforge/broker_sim/execution.py`
   Implement matching, commission, scope, and trade lifecycle invariants.
2. `src/tradeforge/broker_sim/portfolio.py`
   Correct commission treatment in realized profit and loss.
3. `src/tradeforge/broker_sim/orders.py`
   Reject invalid numeric order inputs.
4. `src/tradeforge/database/models.py`
   Persist cumulative order commission.
5. `src/tradeforge/database/session.py`
   Enable SQLite foreign keys.
6. `src/tradeforge/backtesting/engine.py`
   Scope the broker and persist execution settings with each run.
7. `src/tradeforge/backtesting/metrics.py`
   Separate fill count from completed trade count.
8. `pyproject.toml`
   Select deterministic Ruff rule families.

## Data Model And Migration Impact

Revision `003_execution_realism` adds `orders.commission_paid` with a zero server default in addition to the existing stop and partial fill fields. Existing order rows receive zero cumulative commission.

## CLI Impact

The `run-backtest` result now reports `number_of_fills`, `number_of_trades`, and `open_trades` separately. Existing commands do not change.

## API Impact

No endpoint is added or removed.

## Reporting Impact

Trade rows now represent position lifecycles instead of individual buy fills. Backtest reports therefore show consistent partial entry and exit aggregation.

## Testing Strategy

Tests cover aggregate liquidity, persistent stop state, limit boundaries, price improvement, commission reconciliation, profit and loss reconciliation, trade lifecycle aggregation, order timing, broker scope, numeric validation, migration columns, and SQLite foreign key enforcement.

## Risks

1. SQLite stores timestamps without timezone offsets even when SQLAlchemy models are timezone aware.
2. Floating point arithmetic remains the current money and quantity representation.
3. Intrabar stop and limit sequencing remains a bar based approximation.

## Rollout Notes

Run the Alembic upgrade before using the corrected broker against an existing database. Backtest metric consumers must distinguish the new fill count from completed trade count.
