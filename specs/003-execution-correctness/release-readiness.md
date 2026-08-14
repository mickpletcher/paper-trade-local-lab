# Release Readiness

## Status

Conditionally ready. Code, tests, migration, package, dependency, and documentation checks pass. Container validation remains pending on a Docker enabled host or in GitHub Actions.

## Ready Items

* All ten reviewed correctness and reliability issues are fixed.
* Revision `003_execution_realism` carries the new persisted order state.
* Existing revision 002 data survives the tested migration round trip.
* Regression coverage protects each corrected behavior.
* User and operator documentation reflects the corrected semantics.

## Release Checks

* Python 3.11 tests: passed, 41 tests.
* Python 3.13 tests: passed, 41 tests.
* Ruff checks: passed in both installed toolchains.
* Coverage: 86 percent.
* Package build: passed.
* Dependency audit: passed.
* Markdown checks: passed.
* Container build: pending because Docker is unavailable locally.

## Operator Steps

1. Back up an existing SQLite database.
2. Run `tradeforge init-db` to apply revision `003_execution_realism`.
3. Run `tradeforge db-current` and confirm the current and head revisions match.
4. Run the container build in GitHub Actions or on a Docker enabled host before publishing an image.

## Rollback

Downgrade revision `003_execution_realism` before reverting the matching application code. The downgrade removes cumulative commission and execution realism state added by revision 003.
