# Tasks

- [ ] Define the live quote provider contract under `src/tradeforge/market_data/`.
- [ ] Add a latest quote model to `src/tradeforge/database/models.py`.
- [ ] Add a migration step for latest quote storage.
- [ ] Implement quote refresh and storage logic.
- [ ] Implement current valuation calculations for open positions and total equity.
- [ ] Add API endpoints for quote and portfolio valuation views.
- [ ] Add CLI support if the first pass includes operator commands.
- [ ] Add regression tests for quote storage, valuation math, and stale quote handling.
- [ ] Update README, changelog, assessment, and roadmap docs when implementation lands.

## Verification

- [ ] Quote data is stored separately from historical bars.
- [ ] Latest quote freshness is visible in tests or API responses.
- [ ] Position valuation uses latest quote data and local cash state.
- [ ] Trading remains simulated and local only.
- [ ] `python -m pytest -q` passes after implementation.
