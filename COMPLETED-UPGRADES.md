# Completed Upgrades

This file tracks shipped roadmap work that was previously listed in `FUTURE-UPGRADES.md`.

## 2026-08-14

* Completed a repository and GitHub configuration audit with verified settings, access limitations, and manual follow-up actions.
* Added security, support, conduct, ownership, issue, pull request, and dependency maintenance files.
* Added dependency review, scheduled Python audits, deterministic Markdown tooling, and tag-driven GitHub release automation.
* Pinned every committed GitHub Action to a full commit SHA and added Dependabot maintenance for those pins.
* Hardened the Alpaca data URL boundary to HTTPS hosts without embedded credentials and added regression coverage.
* Added deterministic Ruff format enforcement and normalized the existing formatting baseline.
* Expanded Python package metadata, local ignore rules, and operator-facing installation, configuration, security, and automation documentation.
* Added a PowerShell governance validator for the four required living files and their change set synchronization.
* Added push, pull request, manual, and weekly governance validation in GitHub Actions.
* Normalized the required root filenames and made the future upgrade backlog tracked project state.
* Rewrote the current assessment and reprioritized the future backlog into high, medium, and low tiers.
* Corrected aggregate bar volume budgeting across multiple open orders.
* Preserved stop trigger state across partial fills and enforced submission time plus strategy run scope.
* Enforced limit price boundaries and added marketable limit price improvement at the bar open.
* Reconciled fixed and per share minimum commissions across partial fills with persisted cumulative commission state.
* Corrected position profit and loss accounting and aggregated partial fills into one trade lifecycle record.
* Enabled SQLite foreign key enforcement for application connections.
* Separated fill, completed trade, and open trade metrics.
* Added the `003-execution-correctness` specification, audit, release readiness, and regression coverage.
* Made Ruff rule selection explicit so clean CI installs use deterministic lint behavior.

## 2026-05-21

* Added configurable commission models with fixed per order and per share execution fee support.
* Added symbol specific slippage rules so fill pricing can vary by ticker instead of using one global basis point value.
* Added stop orders, stop limit orders, and explicit single order cancel support in the simulator.
* Added partial fill handling with volume aware execution caps and persistent remaining quantity tracking.
* Added the `003_execution_realism` Alembic migration for stop prices, filled quantity, cumulative commission, and stop trigger tracking.
* Added regression coverage for stop orders, stop limit orders, symbol specific slippage, configurable commissions, cancel support, and partial fills.

## 2026-05-12

* Added project scaffold for local first paper trading with CLI, API, backtesting, broker simulation, market data import, reporting, and tests.
* Added SQLite persistence with SQLAlchemy models and local data folders.
* Added container support with Dockerfile and docker compose.
* Added Docker ignore rules for clean image builds.
* Updated README with Docker and Proxmox setup steps.
* Added changelog tracking in changelog.md.
* Added account equity snapshots during backtest runs.
* Added bundled sample data and the `tradeforge seed-sample-data` first run flow.
* Added the first versioned SQLite migration path before the later Alembic upgrade.
* Fixed local execution correctness for final bar order handling and invalid sell rejection.
* Added regression coverage for broker edge cases, migrations, and the end to end CLI path.
* Added `tradeforge start-api` so local and container startup now use one CLI command surface.
* Added cleaner CLI validation for strategy names, symbol existence, and date ranges before backtest runs start.
* Added OpenAPI response examples for the current endpoints plus tests for API docs coverage.
* Added `assessment.md` as the repo level project briefing.
* Added repo level GitHub Spec scaffolding with `.github/copilot-instructions.md`, reusable `.github/prompts`, and `specs/001-core-trading-foundation/`.
* Added basic GitHub Actions CI to run `python -m pytest -q` on pushes to `main` and pull requests with Python 3.13.
* Added `specs/002-live-market-data-valuation/` to define live quote based valuation while keeping execution local only.
* Added the first live quote valuation slice with `live_quotes` storage, quote refresh flow, local valuation calculations, and `/quotes` plus `/portfolio` endpoints.
* Replaced the hand rolled schema runner with an Alembic migration workflow plus CLI revision and version commands.
* Expanded GitHub Actions to run lint, tests, package build validation, container build validation, and GHCR image publishing on `main`.
* Added structured JSON logging plus an opt in `/metrics` endpoint for long running API deployments.
