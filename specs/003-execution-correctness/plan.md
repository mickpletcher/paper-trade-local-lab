# Plan

## Implementation Phases

## Phase 1

Define execution invariants and extend the pending migration with cumulative commission state.

## Phase 2

Correct order matching, commission calculation, position accounting, trade history, order timing, and broker scope.

## Phase 3

Enable SQLite foreign keys, separate fill and trade metrics, and make Ruff selection deterministic.

## Phase 4

Add regression coverage, synchronize project documentation, audit the implementation, and run release checks.

## Verification Plan

1. Run tests under Python 3.11 and Python 3.13.
2. Run Ruff with both installed versions.
3. Measure coverage.
4. Verify migration upgrade, downgrade, and existing row defaults.
5. Build the wheel and source distribution.
6. Run Markdown lint and container validation when tooling is available.

## Documentation Updates

Update `README.md`, `ASSESSMENT.md`, `CHANGELOG.md`, `COMPLETED-UPGRADES.md`, `FUTURE-UPGRADES.md`, and `specs/README.md`.

## Rollback Notes

The change can be rolled back with the `003_execution_realism` downgrade before the revision is released. Code and migration changes must be reverted together.
