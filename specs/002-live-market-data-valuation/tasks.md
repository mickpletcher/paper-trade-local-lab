# Tasks

- [x] Define the live quote provider contract under `src/tradeforge/market_data/`.
- [x] Add a latest quote model to `src/tradeforge/database/models.py`.
- [x] Add a migration step for latest quote storage.
- [x] Implement quote refresh and storage logic.
- [x] Implement current valuation calculations for open positions and total equity.
- [x] Add API endpoints for quote and portfolio valuation views.
- [x] Add CLI support if the first pass includes operator commands.
- [x] Add regression tests for quote storage, valuation math, and stale quote handling.
- [x] Update README, changelog, assessment, and roadmap docs when implementation lands.

## Verification

- [x] Quote data is stored separately from historical bars.
- [x] Latest quote freshness is visible in tests or API responses.
- [x] Position valuation uses latest quote data and local cash state.
- [x] Trading remains simulated and local only.
- [x] `python -m pytest -q` passes after implementation.
