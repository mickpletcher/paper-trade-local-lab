# Requirements

## Problem

TradeForge currently supports historical replay and local backtesting, but it does not have a way to update current position valuation from live market prices. That makes the local paper trading model less useful for watching open positions, unrealized profit and loss, and current account equity during the day.

The repo needs a live quote path that updates valuation in near real time while keeping all order submission, fills, and trading decisions local.

## Goals

1. Add live market data support for current valuation.
2. Keep simulated trading fully local.
3. Separate live quote handling from historical backtest data.
4. Expose current quote and valuation state through the local API.
5. Support future provider expansion through a provider interface instead of a one off integration.

## Non Goals

1. Add live order routing.
2. Connect to brokerages for execution.
3. Replace historical CSV import.
4. Merge live quote data into backtest replay data.
5. Add a full streaming architecture in the first pass if simple polling is enough.

## Functional Requirements

1. The repo must support a live market data provider abstraction for current quotes.
2. The repo must support at least one initial provider implementation or a provider scaffold with a clear contract.
3. The repo must store the latest quote separately from historical `price_bars`.
4. The repo must track quote timestamp and quote freshness so stale data can be identified.
5. The repo must calculate current valuation for open positions using the latest available quote.
6. The repo must calculate current account equity using cash plus marked to market position value.
7. The repo must expose current quote and valuation data through local API endpoints.
8. The repo must keep order submission, fill handling, and simulated execution fully local.
9. The repo must handle live quote refresh failure without corrupting trading state.
10. The repo must document how live quote refresh works and what remains local only.

## Non Functional Requirements

1. The design must preserve the current local first repo boundary.
2. The quote refresh path should be simple to run locally.
3. The implementation should allow provider replacement without redesigning the rest of the repo.
4. The valuation path should clearly distinguish live quote state from historical backtest state.
5. The feature should be testable locally with mocked provider responses.

## Acceptance Criteria

1. A user can configure a live market data provider for local quote refresh.
2. Latest quote data is stored separately from historical bars.
3. Open positions can be valued from the latest quote.
4. API endpoints return current quote and valuation data.
5. Trading remains simulated and local only.
6. Tests cover stale quote handling, quote storage, and valuation calculations.

## Open Questions

1. Which provider should be the first real implementation.
2. Whether the first version should use simple polling only or also expose a background service mode.
3. Whether quote refresh should be CLI driven, API driven, or both in the first pass.
