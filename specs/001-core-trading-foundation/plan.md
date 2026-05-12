# Plan

## Implementation Phases

This baseline package is already reflected in the current repo state. The plan below describes how the current foundation should be maintained and extended.

## Phase 1

Document the current baseline:

1. Record core requirements.
2. Record the current design and module boundaries.
3. Record the current CLI and API surface.

## Phase 2

Preserve baseline verification:

1. Keep migration version checks in tests.
2. Keep execution correctness tests for invalid sells and final bar behavior.
3. Keep at least one end to end CLI verification path.

## Phase 3

Use this package as the starting point for future specs:

1. Create new numbered folders for material features.
2. Reference baseline behavior before changing it.
3. Update repo docs and roadmap state when specs are implemented.

## Verification Plan

Baseline verification should include:

1. `python -m pytest -q`
2. Review of `README.md`
3. Review of `assessment.md`
4. Review of migration version state

## Documentation Updates

When future specs modify this baseline, update:

1. `README.md`
2. `changelog.md`
3. `assessment.md` if project state materially changes
4. `future-upgrades.md` if roadmap items are completed or reprioritized

## Rollback Notes

If a future feature proves unstable:

1. Revert the feature branch changes.
2. Keep this baseline package as the last known good reference.
3. Open a new numbered spec for the rework instead of patching the old package informally.
