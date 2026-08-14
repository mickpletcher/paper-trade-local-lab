# TradeForge GitHub Spec Instructions

## Repo Intent

TradeForge is a local first paper trading and strategy testing lab.

This repo is for offline simulation, historical replay, and strategy research. It is not live trading infrastructure.

Future work must preserve that boundary unless a spec explicitly expands the repo scope.

## Core Engineering Rules

1. Preserve the current repo structure unless a spec explicitly requires structural change.
2. Keep the local simulation path correct before making it more complex.
3. Prefer additive improvements over speculative rewrites.
4. Keep persistence, broker simulation, backtesting, reporting, CLI, and API concerns separated.
5. Do not add fake compatibility shims for replaced behavior.
6. Keep tests close to behavior changes. Non trivial changes should add or update tests in the same task.
7. When changing schema or persisted behavior, update the migration flow instead of bypassing it.
8. Default to triggered or scheduled automation, self healing, and explicit failure reporting instead of manual operator steps.
9. Treat the four root governance files as required parts of every change: `CHANGELOG.md`, `ASSESSMENT.md`, `FUTURE-UPGRADES.md`, and `COMPLETED-UPGRADES.md`.
10. Run `./scripts/Test-ProjectGovernance.ps1 -CheckWorkingTree` before handing off a change.

## When To Use GitHub Spec

Use the spec workflow for:

1. Any feature that changes behavior across multiple modules.
2. Any schema or migration change.
3. Any execution model change such as orders, fills, risk, or portfolio logic.
4. Any API contract expansion.
5. Any new adapter or integration surface.

Skip the full workflow only for very small fixes, typo corrections, or contained one file changes.

## Required Spec Flow

For non trivial work, use this sequence:

1. Write or update `requirements.md`
2. Write or update `spec.md`
3. Write or update `plan.md`
4. Write or update `tasks.md`
5. Implement
6. Audit against the spec
7. Capture release readiness notes if needed

Store each feature package under `specs/` using a numbered folder:

* `specs/001-core-trading-foundation/`
* `specs/002-stop-orders-and-cancel-flow/`
* `specs/003-parameter-sweeps/`

## TradeForge Specific Guidance

### Simulation Accuracy

Prioritize correctness in these areas:

* Order lifecycle
* Cash accounting
* Position accounting
* Fee and slippage handling
* Final bar behavior
* Strategy signal timing
* Metrics and report output

### Data Handling

Prefer explicit validation for:

* OHLCV column shape
* Timestamp normalization
* Duplicate and conflicting bars
* Symbol normalization

### Scope Discipline

Keep live brokerage ideas behind future specs. Do not blend live execution concerns into the current local only model by accident.

### Documentation

When a spec changes current repo behavior, update:

* `README.md`
* `CHANGELOG.md`
* `ASSESSMENT.md`
* `FUTURE-UPGRADES.md`
* `COMPLETED-UPGRADES.md`

Every changelog entry must state the change and why. When a future upgrade is completed, move it to `COMPLETED-UPGRADES.md` with the completion date and add a replacement idea to the appropriate future tier.

## Verification Expectations

For Python changes, prefer:

```powershell
python -m pytest -q
```

For non trivial behavior changes, include:

1. Regression coverage for the changed path
2. Verification notes in the spec task package
3. Clear documentation of known limits that still remain
