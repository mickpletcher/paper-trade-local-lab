# Requirements

## Problem

The execution realism work added richer order types and partial fills, but several paths could produce fills, commissions, profit and loss, or trade records that did not reconcile with the configured rules.

## Goals

1. Make order matching deterministic and bounded by the configured bar liquidity.
2. Preserve stop state and enforce limit price guarantees.
3. Reconcile commissions, cash, positions, trades, and metrics.
4. Isolate each broker instance to one strategy run or the manual order scope.
5. Enforce SQLite relationships and keep CI lint behavior deterministic.

## Non Goals

1. Add short selling, margin, time in force, venue queues, or tick simulation.
2. Add live order execution.
3. Add tax lot accounting or a general ledger.
4. Replace the existing floating point price and quantity model.

## Functional Requirements

1. The maximum bar fill ratio must create one aggregate fill budget per bar.
2. A triggered stop must remain triggered until it fills or is cancelled.
3. A buy limit must never fill above its limit and a sell limit must never fill below its limit.
4. A marketable limit may receive price improvement from the bar open.
5. A fixed commission must be charged once per order regardless of fill count.
6. A per share minimum commission must be reconciled across all fills for one order.
7. Position realized profit and loss must reconcile with cash after a completed round trip.
8. Partial entries and exits within one position lifecycle must produce one consistent trade record.
9. Orders must not execute against bars earlier than their submission timestamp.
10. A broker must process and cancel only orders in its configured strategy run scope.
11. Invalid, nonfinite, or negative order and execution settings must fail validation.
12. SQLite foreign key constraints must be enabled for application connections.
13. Backtest metrics must distinguish fills from completed trades.

## Non Functional Requirements

1. Existing databases must upgrade through Alembic revision `003_execution_realism`.
2. Execution settings used by a backtest must be stored with the strategy run parameters.
3. Tests must cover every corrected failure path.
4. Ruff rules used by CI must be explicit instead of depending on version defaults.

## Acceptance Criteria

1. Two orders cannot consume more than the configured aggregate bar budget.
2. A partially filled stop completes on a later bar without retriggering.
3. Limit boundary and marketable price improvement tests pass.
4. Partial fills do not multiply fixed or minimum commissions.
5. Cash profit, position realized profit and loss, and trade realized profit and loss reconcile.
6. Future dated and out of scope orders are not processed.
7. SQLite reports `PRAGMA foreign_keys = 1` through the application engine.
8. Tests and Ruff pass on Python 3.11 and Python 3.13.

## Open Questions

None for this correction package.
