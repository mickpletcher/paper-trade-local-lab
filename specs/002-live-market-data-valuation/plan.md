# Plan

## Implementation Phases

## Phase 1

Add the live quote foundation:

1. Define the provider interface.
2. Add the latest quote data model.
3. Add a schema migration for the quote table.

## Phase 2

Add quote refresh and valuation logic:

1. Implement a refresh path that fetches quotes and stores them locally.
2. Add valuation calculations for positions and total equity.
3. Add quote freshness checks.

## Phase 3

Expose the feature to operators:

1. Add API endpoints for quotes and portfolio valuation.
2. Add CLI entry points if they are part of the first pass.
3. Update README and operator docs.

## Verification Plan

1. Add tests for quote model persistence and upsert behavior.
2. Add tests for valuation calculations.
3. Add tests for stale quote handling.
4. Add API tests for quote and valuation endpoints.
5. Run `python -m pytest -q`.

## Documentation Updates

When implemented, update:

1. `README.md`
2. `changelog.md`
3. `assessment.md`
4. `future-upgrades.md`

## Rollback Notes

If the first implementation is unstable:

1. Disable the live quote refresh entry point.
2. Keep historical backtest behavior unchanged.
3. Remove or revert the live quote specific migration and module changes together.
