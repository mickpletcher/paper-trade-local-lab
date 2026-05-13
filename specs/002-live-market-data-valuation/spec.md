# Specification

## Summary

This spec adds live market data support for current valuation while keeping all trading and execution local. The feature introduces a clear split between historical data used for replay and backtests and live quote data used for current account valuation.

## Current State

The repo currently has:

1. Historical OHLCV import through CSV.
2. Historical replay for backtesting.
3. Simulated order handling and position accounting.
4. Local API endpoints for symbols, orders, positions, and strategy runs.
5. No live quote ingestion.
6. No quote freshness or real time valuation model.

## Proposed Design

The proposed design introduces a separate live quote path:

1. Historical bars remain in `price_bars` for import and replay.
2. Current live quotes are stored in a separate quote model.
3. A market data provider interface fetches live quotes from an external source.
4. A refresh service writes latest quote data into local storage.
5. A valuation service combines current positions, account cash, and latest quotes.
6. API endpoints expose current quote and valuation state.

Trading boundaries remain unchanged:

1. Orders are still submitted locally.
2. Fills are still simulated locally.
3. No live execution is added.

## Module Changes

Expected module additions or changes:

1. `src/tradeforge/market_data/`
   Add provider contract and live quote refresh path.
2. `src/tradeforge/database/models.py`
   Add latest quote storage model.
3. `src/tradeforge/database/migrations.py`
   Add migration for the new quote model.
4. `src/tradeforge/broker_sim/` or `src/tradeforge/reporting/`
   Add valuation logic for current positions and account equity.
5. `src/tradeforge/api/app.py`
   Add endpoints for quotes and current portfolio valuation.
6. `src/tradeforge/cli.py`
   Optionally add commands for refreshing live quotes or viewing current valuation.

## Data Model And Migration Impact

Add a new model for current quote state, for example:

1. `live_quotes`
   * `id`
   * `symbol_id`
   * `provider`
   * `quote_timestamp`
   * `last_price`
   * `bid_price`
   * `ask_price`
   * `previous_close`
   * `currency`
   * `fetched_at`

Data model rules:

1. Store only the latest quote per symbol and provider in the first pass.
2. Keep quote data separate from historical `price_bars`.
3. Persist freshness metadata so stale quotes can be detected and reported.

Migration rules:

1. Add the new table through the versioned migration path.
2. Do not bypass `schema_migrations`.

## CLI Impact

Potential first pass CLI additions:

1. `tradeforge refresh-quotes`
2. `tradeforge show-valuation`

If CLI additions are deferred, the first pass should still define whether quote refresh is triggered through API or direct service calls.

## API Impact

Add local endpoints such as:

1. `GET /quotes`
   Return the latest quote state.
2. `GET /portfolio`
   Return current market value, unrealized profit and loss, and total equity.
3. `GET /account`
   Return cash, market value, total equity, and quote freshness summary.

Endpoint behavior:

1. Quote endpoints must indicate stale data when freshness thresholds are exceeded.
2. Endpoints must not imply live trading capability.

## Reporting Impact

The first pass does not need to change historical backtest reports.

Optional future reporting changes:

1. Add a local valuation snapshot view.
2. Add a current holdings mark to market report.

## Testing Strategy

Tests should cover:

1. Quote provider contract behavior with mocked responses.
2. Quote storage and upsert behavior.
3. Quote freshness calculations.
4. Valuation calculations for positions and cash.
5. API responses for quotes and portfolio valuation.
6. Failure behavior when quote refresh fails or quotes are stale.

## Risks

1. Mixing live quote semantics with historical bar semantics.
2. Stale quotes making valuation appear current when they are not.
3. Provider specific formats leaking into the rest of the app.
4. Scope creep into live execution.

## Rollout Notes

Start with valuation only.

Do not add any broker routing, live order state sync, or external execution semantics in this package.
