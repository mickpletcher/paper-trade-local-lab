# Changelog

## 2026-08-14

### Hardened the market data endpoint boundary

Summary: Restricted the configurable Alpaca data URL to HTTPS hosts without embedded credentials and added regression tests for unsafe schemes and malformed URLs.

Why: An operator-controlled URL must not allow `urlopen` to read local files or send provider headers through an unexpected URL scheme.

### Added automated dependency maintenance

Summary: Added grouped weekly Dependabot updates for Python, npm documentation tooling, GitHub Actions, and Docker dependencies.

Why: Dependency and action updates must arrive automatically instead of relying on the maintainer to check four ecosystems manually.

### Pinned workflow actions and documentation tooling

Summary: Replaced mutable action tags with full commit SHAs and added a locked npm manifest for Markdownlint.

Why: Immutable workflow references and integrity-checked tooling reduce supply-chain drift while remaining updateable through Dependabot.

### Added pull request security gates

Summary: Added dependency review for pull requests plus a scheduled and manually dispatchable Python vulnerability audit.

Why: New vulnerable dependencies must fail visibly before merge and the installed dependency set needs recurring checks between code changes.

### Added tag-driven release automation

Summary: Added a workflow that validates semantic version tags against `pyproject.toml`, reruns release checks, builds artifacts, and creates a GitHub release.

Why: Releases should be reproducible and gated instead of assembled manually from an unverified working tree.

### Added repository security and community files

Summary: Added the security policy, support guide, code of conduct, code ownership, issue forms, and pull request template.

Why: Contributors need explicit reporting channels, review ownership, sanitized issue intake, and a consistent pull request contract.

### Expanded project and package metadata

Summary: Added Python package licensing, authorship, classifiers, keywords, project URLs, security audit tooling, and broader local ignore rules.

Why: Built artifacts and local workflows must describe the project accurately and exclude generated or sensitive files consistently.

### Replaced security and installation placeholders

Summary: Rewrote the installation, configuration, security, automation, contribution, and README guidance around real commands and current trust boundaries.

Why: Canonical documentation must describe the system operators actually run rather than future documentation placeholders.

### Added deterministic format enforcement

Summary: Added `ruff format --check` to CI and release validation and normalized the existing Python formatting drift.

Why: Formatting must fail automatically and produce the same result locally and in GitHub Actions.

### Included staged files in local governance checks

Summary: Added the staged Git diff to `-CheckWorkingTree` change set detection.

Why: Local validation must enforce the four file contract across staged, unstaged, and untracked changes.

### Cleared governance script analyzer warnings

Summary: Renamed internal functions and parameters to avoid automatic variable and plural noun conflicts, then replaced host only output with pipeline output.

Why: The repository validator must pass PowerShell static analysis cleanly and work in noninteractive hosts.

### Documented the active automation workflows

Summary: Replaced the automation documentation placeholder with the live workflow inventory, governance contract, failure behavior, local command, and security boundary.

Why: Operators need the actual automated path instead of a list of suggested future documents.

### Corrected validator date collection handling

Summary: Allowed the validator to process PowerShell's enumerated regular expression matches as an object array.

Why: The first local governance run exposed a parameter conversion failure before validation could start.

### Added a local governance validator

Summary: Added `scripts/Test-ProjectGovernance.ps1` to validate exact root filenames, changelog entries, assessment length and sections, roadmap tiers, completed history ordering, and change set synchronization.

Why: Repository policy must fail automatically instead of depending on a reviewer to remember it.

### Added triggered and scheduled governance checks

Summary: Added a GitHub Actions workflow that runs governance validation on pushes, pull requests, manual dispatch, and every Monday.

Why: Drift must be detected without waiting for someone to run a local command.

### Normalized and tracked the living governance files

Summary: Renamed the four root files to `CHANGELOG.md`, `ASSESSMENT.md`, `FUTURE-UPGRADES.md`, and `COMPLETED-UPGRADES.md`, then removed the future backlog from `.gitignore`.

Why: Exact names and tracked content are required for reliable CI enforcement and shared project state.

### Expanded documentation lint coverage

Summary: Added all four living governance files to the Markdownlint workflow.

Why: Structural validation does not replace Markdown quality checks.

### Updated repository instructions and links

Summary: Updated contributor instructions, README links, and specification references to require the four living files and the local validation command.

Why: Contributors and automation need one consistent contract and exact filenames.

### Rewrote the current assessment

Summary: Replaced the long historical assessment with a current, under one minute overview of purpose, architecture, dependencies, automation, limitations, and health.

Why: The assessment must describe the repo as it exists now.

### Reprioritized future and completed upgrades

Summary: Reorganized future work into high, medium, and low tiers, recorded the governance automation as complete, and added automatic failure issue creation as a new upgrade idea.

Why: The roadmap must stay actionable and populated as automation work ships.

### Corrected aggregate bar volume budgeting

Summary: Applied one volume budget across all orders competing for the same bar.

Why: Per order budgets allowed total simulated fills to exceed available market volume.

### Preserved stop trigger state

Summary: Persisted stop triggers across partial fills and later bars.

Why: A triggered stop must continue as an active market or limit order without requiring a second trigger.

### Enforced limit price boundaries

Summary: Prevented fills outside a limit and added open price improvement for marketable orders.

Why: Slippage must never make a limit fill worse than the requested boundary.

### Reconciled commissions across partial fills

Summary: Charged fixed fees once per order and applied per share minimums to cumulative filled quantity.

Why: Charging a per order minimum on every partial fill inflated trading costs.

### Corrected position profit and loss

Summary: Included buy commission in cost basis and deducted sell commission once from realized profit and loss.

Why: The previous flow counted buy commission twice.

### Aggregated trade lifecycle records

Summary: Combined partial entries and exits into one open trade and recorded weighted exits plus cumulative realized profit and loss.

Why: One trade row per fill created orphaned and misleading trade history.

### Enforced order time and run scope

Summary: Limited bar processing and cancellation to eligible orders from the broker's strategy run.

Why: Future orders and orders owned by another run must not execute.

### Validated execution inputs

Summary: Rejected nonfinite or invalid order values, costs, slippage, and fill ratios.

Why: Invalid numeric values can silently corrupt execution and accounting state.

### Hardened SQLite connections

Summary: Enabled foreign keys on every SQLite connection and corrected connection pooling for memory and file databases.

Why: SQLite foreign keys are disabled by default and leaked connections produced resource warnings.

### Separated fills from trades in metrics

Summary: Added fill, completed trade, and open trade counts.

Why: Partial fills are execution events, not separate completed trades.

### Made Ruff checks deterministic

Summary: Selected explicit stable Ruff rules instead of inheriting version dependent defaults.

Why: A clean CI environment failed even though the existing local Ruff version passed.

### Added execution correctness specifications and tests

Summary: Added `specs/003-execution-correctness/` and regression coverage for every corrected execution path.

Why: Execution behavior needs a durable contract and tests that prevent recurrence.

## 2026-05-21

### Execution realism

* Added stop and stop limit order support to the simulated broker.
* Added explicit single order cancel support for open and partially filled orders.
* Added volume aware partial fill handling with persisted `filled_quantity` tracking on orders.
* Added configurable commission models with fixed per order and per share fee calculations.
* Added symbol specific slippage overrides on top of the default slippage basis point setting.
* Added stop trigger tracking fields and the `003_execution_realism` Alembic migration.

### Tests and verification

* Added regression coverage for stop orders, stop limit orders, cancel support, partial fills, symbol specific slippage, and configurable commissions.
* Updated the database initialization test to assert the new execution realism schema fields and current migration head.

### Roadmap and repo tracking

* Added `completed-upgrades.md` as the tracked history for shipped roadmap items.
* Moved completed roadmap entries out of `future-upgrades.md` into `completed-upgrades.md`.
* Removed the shipped stop, stop limit, cancel, partial fill, commission, and symbol specific slippage items from `future-upgrades.md`.
* Added new roadmap candidates for time in force rules, trailing and bracket orders, execution audit trails, marketable limit handling, and fill quality reporting.
* Updated `assessment.md` so current status, constraints, risks, and next steps reflect the new execution model.

## 2026-05-12

### Initial repo state

* Added the TradeForge local first paper trading project structure.
* Added the Typer CLI for database setup, CSV imports, backtests, positions, orders, and P and L summaries.
* Added the FastAPI scaffold with health, symbols, positions, orders, and strategy run endpoints.
* Added SQLite persistence, SQLAlchemy models, market data import, broker simulation, backtesting, reporting, and tests.
* Added local data folders for imports and reports.

### Container support

* Added `.dockerignore` for cleaner image builds.
* Added `Dockerfile` to run the API in a Python 3.12 container.
* Added `docker-compose.yml` for persistent local container hosting with the `data` folder mounted into the container.
* Updated `README.md` with Docker and Proxmox oriented setup steps.

### Documentation

* Added this `changelog.md` file.
* Updated `README.md` to link to the changelog from the main project documentation.

### Roadmap planning updates

* Updated `future-upgrades.md` with expanded market coverage for crypto, options, futures, commodities, and forex.
* Added additional expansion items for risk controls, execution realism, analytics, experimentation, and platform hardening.
* Added external platform integration planning for TradingView and broker or exchange connectors.
* Added GitHub integration reference targets and supporting libraries to guide future implementation research.
* Added priority labels (`Now`, `Next`, `Later`) across roadmap items.
* Added a top 10 execution sequence for implementation order.
* Added a completed section in `future-upgrades.md` and annotated completed entries with the 2026-05-12 date.

### Simulation and local setup improvements

* Fixed end of backtest execution so orders created from the final bar do not fill on that same final bar.
* Added sell side inventory validation so the local simulator rejects sells that would create inventory out of thin air.
* Added regression tests for final bar execution behavior, sell side validation, migrations, and an end to end CLI flow.
* Added a bundled sample AAPL dataset plus the `tradeforge seed-sample-data` command for repeatable local setup.
* Replaced ad hoc schema creation with the first versioned SQLite migration path.

### Assessment and roadmap maintenance

* Added `assessment.md` at the repo root as the current source of truth for project status, strengths, risks, and next steps.
* Updated `future-upgrades.md` to remove completed items that are now part of the current repo baseline.
* Expanded the completed section in `future-upgrades.md` so planning and current state stay aligned.
* Rewrote `README.md` into a detailed operator guide covering local setup, configuration, sample data flow, CLI usage, API usage, Docker usage, testing, and current limitations.

### GitHub Spec workflow

* Added `.github/copilot-instructions.md` with repo specific GitHub Spec rules for TradeForge.
* Added reusable `.github/prompts` files for requirements, spec, plan, tasks, audit, and release readiness.
* Added `specs/README.md` plus the initial `specs/001-core-trading-foundation/` package as the baseline spec for the current MVP.
* Updated `README.md` and `future-upgrades.md` to document the new spec workflow and baseline package.

### Continuous integration

* Added `.github/workflows/ci.yml` to run `python -m pytest -q` on pushes to `main` and on pull requests using Python 3.13.
* Updated `README.md` testing documentation to note the GitHub Actions validation path.

### New spec package

* Added `specs/002-live-market-data-valuation/` with `requirements.md`, `spec.md`, `plan.md`, and `tasks.md`.
* Defined the next planned feature boundary as live quote based valuation only, with all trading and execution remaining local.
* Added `specs/002-live-market-data-valuation/implementation-guide.md` with provider options and a detailed adapter, storage, valuation, API, and testing implementation plan.
* Added `specs/002-live-market-data-valuation/feed-options.md` to rank providers as easy, best, and later for TradeForge.

### CLI and API usability

* Added `tradeforge start-api` so local startup and container startup use the same CLI app command surface.
* Updated the container startup path to use `tradeforge start-api --host 0.0.0.0 --port 8000`.
* Added cleaner `run-backtest` validation for strategy names, symbols, and date ranges.
* Added OpenAPI response examples for the current API endpoints.
* Added tests for the new CLI validation paths, API startup command wiring, and OpenAPI examples.

### Documentation refresh

* Updated `assessment.md` to reflect the current repo baseline, including GitHub Spec, CI, API startup, and the live valuation planning package.
* Rewrote `README.md` as a more novice friendly setup and usage guide with step by step Windows and Linux instructions, troubleshooting notes, and a simpler first run path.

### CI dependency fix

* Added `httpx` to the `dev` extras in `pyproject.toml` so the FastAPI `TestClient` dependency chain is installed in GitHub Actions and `tests/test_api.py` can collect correctly.
* Updated the invalid date CLI test so it asserts `BadParameter` behavior directly and checks the stable CLI exit code instead of brittle Typer and Rich formatted output in CI.
* Updated GitHub Actions workflow dependencies to Node 24 compatible major versions for checkout, setup Python, setup Node, and Docker publish actions so the Node.js 20 deprecation warnings are removed.

### Live quote valuation

* Added `live_quotes` storage and migration support for quote data that stays separate from historical bars.
* Added a normalized live quote provider contract and the first Alpaca snapshot based provider implementation.
* Added `tradeforge refresh-quotes`, `tradeforge show-quotes`, and `tradeforge show-valuation`.
* Added `/quotes` and `/portfolio` endpoints for live quote inspection and local portfolio valuation.
* Added quote valuation tests and updated the repo docs, environment example, and `specs/002-live-market-data-valuation/tasks.md`.

### Deployment and observability

* Replaced the hand rolled migration runner with Alembic revisions and added `tradeforge db-current` plus `tradeforge db-revision`.
* Added structured JSON logging for CLI and API execution paths.
* Added an opt in `/metrics` endpoint for long running API deployments.
* Expanded GitHub Actions CI to run Ruff, pytest, Python package builds, container image build validation, and GHCR image publishing on `main`.

### Documentation architecture

* Rewrote `README.md` into a concise landing page with badges, quick start, philosophy, and docs entry points.
* Added a full `docs/` information architecture with section indexes for architecture, installation, configuration, strategies, backtesting, AI integration, market data, database, plugins, security, automation, API, roadmap, contributing, and FAQ.
* Added docs governance, naming standards, AI documentation workflow guidance, and a GitHub Wiki strategy that separates durable docs from exploratory research.
* Added `CONTRIBUTING.md`, Markdown lint configuration, and a `docs.yml` GitHub Actions workflow for docs automation.
