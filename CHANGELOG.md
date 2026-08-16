# Changelog

## 2026-08-15

### Refreshed the deterministic dependency lock

Summary: Updated Charset Normalizer from 3.5.0 to 3.5.1 to match the current universal resolver output.

Why: Lock verification must remain reproducible so unrelated security fixes are not blocked by dependency drift.

### Enforced repository security gates

Summary: Restricted Actions to GitHub owned plus explicitly allowed Astral and Docker actions, required full commit SHA references, and made dependency review, dependency audit, CodeQL, and Python 3.14 explicit merge checks.

Why: Security workflows and source pinning must be enforced by repository policy instead of depending on reviewers to notice drift.

### Corrected live quote staleness

Summary: Calculated quote age from the provider's market timestamp and exposed retrieval age separately as `fetch_age_seconds`.

Why: Fetching an old exchange snapshot now must not make stale market data appear fresh in portfolio valuation.

### Enforced the normalized quote contract

Summary: Rejected nonfinite or nonpositive prices, fractional or negative sizes, malformed timestamps and payloads, crossed markets, and quotes without a usable mark before persistence.

Why: Invalid provider values can silently corrupt valuation or make API serialization fail unless the ingestion boundary rejects them atomically.

### Blocked Alpaca quote redirects

Summary: Replaced default redirect following with a rejecting redirect handler and added regression coverage for the credential-bearing request path.

Why: Alpaca API key headers must never be forwarded from a validated URL to an unvalidated redirect destination.

### Disambiguated same-timestamp trade migration fills

Summary: Reconstructed legacy entry and exit fees by directional fill quantity sequence instead of inclusive trade timestamp windows.

Why: A sell that closes one trade and a buy that reopens at the same timestamp must not be assigned to both trade lifecycles.

### Indexed legacy fills during fee migration

Summary: Grouped legacy fills once by strategy run and symbol before reconstructing each trade's fee totals.

Why: The migration must not scan every fill for every trade as local history grows.

### Protected the `init-db` command contract

Summary: Added CLI regression coverage proving the renamed implementation still exposes and executes `init-db`.

Why: Internal cleanup must not silently rename an operator-facing automation command.

### Ran compatibility linting on Python 3.11

Summary: Moved the CI lint and strict Mypy environment from Python 3.13 to the minimum supported Python 3.11 runtime.

Why: Mypy must load dependency stubs compatible with its configured Python 3.11 target instead of newer syntax from a Python 3.13 environment.

### Removed the CLI schema alias

Summary: Renamed the `init-db` command implementation and imported the migration initializer by its canonical name.

Why: Removing the alias lets Ruff retain all migration imports in one block without changing the public command name.

### Aligned Mypy with minimum Python support

Summary: Changed strict Mypy analysis from Python 3.13 semantics to the minimum supported Python 3.11 semantics.

Why: Type validation must reject standard library and typing features that would fail on a declared supported runtime.

### Consolidated migration imports

Summary: Combined duplicate migration imports in the CLI into one import block.

Why: One canonical import block is easier for automated formatting and maintainers to keep consistent.

### Corrected the documented container sequence

Summary: Stated that CI builds the container before starting and health checking it.

Why: The workflow inventory must describe the actual artifact lifecycle without implying that CI receives a prebuilt image.

### Corrected the runtime ledger grammar

Summary: Completed the sentence describing separate runner and container validation.

Why: Living project records must remain clear and professionally readable.

### Clarified Python runtime validation

Summary: Distinguished the Python 3.14 runner test job from the separate Python 3.14 container build and health check.

Why: CI documentation must not imply that the unit suite executes inside the built container.

### Clarified configuration diagnostic scope

Summary: Reworded the planned configuration diagnostic to describe its output as non-sensitive.

Why: The security boundary should use clear, standard language before the diagnostic is implemented.

### Blocked failure webhook redirects

Summary: Disabled automatic redirects for failure webhook delivery and added regression coverage for rejected redirect responses.

Why: A validated HTTPS destination must not redirect the notification to an unvalidated plaintext or internal endpoint.

### Clarified outbound URL validation failures

Summary: Updated shared outbound URL validation errors to state that whitespace is forbidden.

Why: Operators need the validation message to identify the exact configuration defect without trial and error.

### Minimized failure webhook data

Summary: Reduced maintenance failure webhook JSON to the event, status, start timestamp, and completion timestamp while retaining the full report locally.

Why: Import names, symbols, local paths, backup locations, and exception details do not need to leave the workstation.

### Validated failure webhook destinations

Summary: Applied shared outbound URL validation to Alpaca and failure webhook endpoints and rejected non HTTPS, hostless, credential bearing, or whitespace polluted URLs before network access.

Why: A webhook configured from environment input must not permit unsafe schemes or embedded credentials.

### Enforced test coverage

Summary: Added a declarative 88 percent coverage floor and made every CI runtime execute the coverage measured suite.

Why: Installing Pytest Cov without a failing threshold allowed coverage loss to pass silently.

### Added static type validation

Summary: Added strict Mypy validation for the application package, Pandas stubs, and the same command to CI and contributor instructions.

Why: Existing annotations did not protect builds because no type checker validated them.

### Expanded Ruff validation

Summary: Enabled Bugbear, import ordering, simplify, and Ruff specific rule families and corrected the findings they exposed.

Why: The previous selection covered syntax and undefined names but missed common bug patterns and maintainability defects.

### Matched CI tests to the container Python version

Summary: Added Python 3.14 to the GitHub hosted runner test matrix, matching the separately validated container runtime.

Why: The container runs Python 3.14, so health checks alone could miss runtime specific failures that the 3.11 and 3.13 suites never exercised.

### Expanded backtest decision metrics

Summary: Added CAGR, annualized volatility, Sharpe, Sortino, profit factor, average win and loss, time exposure, and buy and hold return to stored and Markdown backtest results.

Why: Total return, win rate, and drawdown alone cannot compare strategy risk, trade quality, capital use, or performance against passive ownership.

### Bounded API relationship queries

Summary: Joined symbols and strategies into the positions, orders, and strategy run queries and added fixed one statement query budget coverage with multiple records.

Why: Lazy relationship access issued one additional query per related record and made endpoint latency grow with result size.

### Cached process settings

Summary: Cached the validated Pydantic settings object and added deterministic cache reset coverage for environment-sensitive tests.

Why: Re-reading `.env` and rebuilding the complete settings model on every request added unnecessary disk and validation work.

## 2026-08-14

### Reconciled trade prices and commissions

Summary: Added Alembic revision `004_trade_fee_basis`, stored gross weighted entry and exit prices with separate fee totals, migrated legacy entry basis values, and added profit and loss reconciliation coverage.

Why: Trade price columns must reproduce stored realized profit and loss instead of silently omitting exit commissions.

### Enforced explicit quantity increments

Summary: Added a configurable execution quantity increment that defaults to one share, rejects misaligned orders, and rounds cash limited fills down without floating point quantity dust.

Why: Fill quantities need a declared lot policy so the simulator does not invent arbitrary fractional shares.

### Reused the API database engine

Summary: Added a cached application engine and session factory, reused them for API requests, disposed them during lifespan shutdown, and kept explicit engine factories uncached for isolated callers.

Why: Request handling should not construct a new SQLAlchemy engine while tests and explicit database workflows still require isolation.

### Consolidated the Compose definition

Summary: Removed the divergent `docker-compose.yml` and retained `compose.yaml` as the only Compose configuration.

Why: One hardened definition prevents operators and older commands from selecting a broader port binding and weaker container controls.

### Enforced warning free locked tests

Summary: Declared Pytest warnings as errors, replaced the deprecated HTTPX test dependency with HTTPX2, and regenerated the universal Python dependency lock.

Why: Local and CI tests must expose dependency deprecations under the same lock faithful environment.

### Removed the unused replay surface

Summary: Deleted the unreferenced market data replay module and revised backtesting documentation to describe the actual direct historical bar execution path.

Why: Dead modules and promised but nonexistent replay documents create an unnecessary maintenance and governance surface.

### Corrected current operator documentation

Summary: Updated execution, database, automation, configuration, security, and project overview documentation for fee fields, quantity increments, engine lifecycle, warning policy, and the canonical Compose launch path.

Why: Operator guidance must describe the current implementation and defaults after every behavioral change.

### Upgraded dependency review automation

Summary: Updated `actions/dependency-review-action` from v4.9.0 to v5.0.0 at its full commit SHA.

Why: Pull request dependency policy should run on the current maintained action without mutable references.

### Removed orphaned Pytest configuration

Summary: Removed the `pytest-asyncio` loop scope setting because the project neither declares that plugin nor contains asynchronous tests.

Why: Clean Python environments should run the suite without unknown configuration warnings.

### Regenerated the security audit dependency lock

Summary: Regenerated the universal Python 3.11 lock after adding Pip Audit and captured its complete transitive dependency tree.

Why: Security jobs and local installs must use the same deterministic dependency set as the declared development tools.

### Made Markdown validation safe for Windows workspace paths

Summary: Added a PowerShell Markdownlint wrapper that invokes the locked Node module directly and made CI and contributor guidance use it.

Why: `npm run` misparses Windows repository paths containing `&`, so the documented local validation command failed in this workspace.

### Reconciled the open hardening and dependency branches

Summary: Combined the repository security audit with the current trading fixes, retained the newer correctness behavior in every conflict, and normalized the added workflows to the current dependency set.

Why: The stale draft overlapped newer fixes and could not be merged safely without explicit conflict resolution and full validation.

### Upgraded the Python container runtime

Summary: Updated the digest pinned container base from Python 3.12 slim to Python 3.14 slim and declared Python 3.14 package support.

Why: The container should track a current supported runtime while remaining immutable and executable in CI.

### Upgraded checkout automation

Summary: Updated every `actions/checkout` reference from v6 to v7.0.1 at its full commit SHA.

Why: All workflows should use one current, immutable checkout implementation.

### Upgraded Python setup automation

Summary: Updated every `actions/setup-python` reference from v6 to v7.0.0 at its full commit SHA.

Why: Python setup should stay on the maintained Node runtime and remain consistent across CI, security, and release jobs.

### Upgraded Node setup automation

Summary: Updated `actions/setup-node` from v6 to v7.0.0 at its full commit SHA.

Why: Documentation validation should use the maintained action runtime without mutable tags.

### Upgraded uv setup automation

Summary: Updated `astral-sh/setup-uv` from v7 to v9.0.0 at its full commit SHA while retaining the pinned uv tool version.

Why: The lock drift gate should use the maintained setup action without changing the deterministic compiler version.

### Addressed automated review reliability findings

Summary: Cancelled wholly unfilled orders on reversal, created custom SQLite parent directories, switched Compose to an initialized managed volume, capped quote backoff, and made symbol duplicate detection linear.

Why: Protected review identified edge cases that could leave stale orders active, break first run maintenance or Linux containers, overrun schedules, or scale poorly.

### Made dependency lock drift checks host independent

Summary: Forced uv lock generation to the minimum supported Python 3.11 baseline in both the recorded command and CI comparison.

Why: Regenerating under Python 3.13 omitted conditional Python 3.11 packages and caused a false lock drift failure.

### Protected the default branch and standardized merges

Summary: Required strict CI, Docs, and Governance checks on `main`, enforced linear history and resolved conversations, disabled force pushes and deletion, enabled squash only merges, and enabled branch cleanup.

Why: Repository safety must be enforced by GitHub instead of depending on each contributor to remember the process.

### Added unattended maintenance orchestration

Summary: Added `tradeforge run-maintenance` to initialize the database, process queued symbol CSV files, refresh open position quotes, back up SQLite, and emit a machine readable run report.

Why: Routine data and persistence work should run as one deterministic job without manual command sequencing.

### Added verified SQLite backup retention

Summary: Added online SQLite backups through the native backup API, integrity checks before promotion, atomic file replacement, and configurable newest copy retention.

Why: A copied database is not a valid recovery artifact until it passes an integrity check and retention is automatic.

### Added maintenance failure reporting

Summary: Added durable success and failure JSON reports plus optional generic webhook notification without masking the original job failure.

Why: Scheduled jobs must fail visibly and preserve enough state for diagnosis.

### Added daily Windows scheduling

Summary: Added a PowerShell installer for a daily Task Scheduler job with missed run catch up and three automatic retries.

Why: Maintenance should run on a trigger and recover from transient host failures without an operator launching it.

### Cancelled stale orders during strategy reversals

Summary: Added pending buy and sell quantities to strategy context, blocked duplicate signals, and cancelled open opposite side orders before submitting a reversal.

Why: A partially filled entry must not keep consuming later liquidity after the strategy has emitted an exit.

### Isolated portfolio valuation by strategy run

Summary: Added explicit run selection, latest run defaulting, run scoped cash and positions, unknown run errors, and the selected run ID in valuation output.

Why: Cash and equity from independent simulations must never be summed into one fictitious portfolio.

### Selected quotes deterministically

Summary: Ordered quotes by fetched time and stable ID before choosing the newest provider value for each symbol.

Why: Insertion order must not decide which market price values a position.

### Enforced complete quote refreshes with retry

Summary: Added exponential retry for transient Alpaca failures and rejected missing, duplicate, or unexpected provider symbols before persistence.

Why: Partial or transient provider responses must not silently look like a successful refresh.

### Validated imported OHLCV invariants

Summary: Rejected nonfinite or nonpositive prices, invalid high and low relationships, and negative or fractional volume with row specific errors.

Why: Impossible candles corrupt backtests and must fail at the ingestion boundary.

### Validated moving average parameters

Summary: Required positive windows, a short window smaller than the long window, and a positive finite order size with CLI errors.

Why: Invalid strategy configuration should fail before creating a run.

### Moved API migrations to startup

Summary: Added FastAPI lifespan initialization, removed per request migration checks, and made `/health` execute a database connectivity probe.

Why: Schema work belongs at process startup and health must represent the database dependency.

### Locked dependency and build inputs

Summary: Added a universal transitive constraint lock, exact build tools, SHA pinned Actions, pinned Markdownlint, a digest pinned Python image, CI lock drift detection, and Dependabot configuration.

Why: Lower bounds and mutable tags make local, CI, and container builds nondeterministic.

### Expanded automated compatibility checks

Summary: Added Python 3.11 and 3.13 test jobs and required the built container to reach healthy state before CI succeeds.

Why: The declared Python range and deployable image need executable verification.

### Hardened container runtime defaults

Summary: Ran the image as an unprivileged user, added a database aware health check, excluded secrets, and added loopback only Compose with restart, read only root, no added capabilities, and no new privileges.

Why: The prior image ran as root, exposed an unauthenticated API broadly, and could fail silently.

### Added regression coverage for the remaining assessment findings

Summary: Added tests for order reversals, parameter rejection, quote retry and completeness, run scoped valuation, deterministic quote choice, invalid candles, API startup, and maintenance recovery artifacts.

Why: Each corrected failure mode needs a durable executable contract.

### Updated operational and project documentation

Summary: Updated the README, installation, configuration, automation, API, market data, database, backtesting, security, assessment, roadmap, and completion history for the current implementation.

Why: Operators and the four living project files must describe the code that now exists.

### Corrected Alpaca snapshot response parsing

Summary: Parsed the multi-symbol snapshot response as the root ticker map and rejected non-object payloads.

Why: Looking for a nonexistent top-level `snapshots` field discarded valid provider quotes.

### Added Alpaca response contract coverage

Summary: Added a provider-level test for a root-keyed AAPL snapshot with trade, quote, minute bar, and previous close data.

Why: Fake normalized quotes did not exercise the external provider wire format.

### Updated live quote parsing project tracking

Summary: Refreshed the assessment, completed work history, and future quote completeness backlog after correcting the Alpaca adapter.

Why: The living project files must reflect current provider behavior and its remaining failure-detection gap.

### Sized moving average exits to available inventory

Summary: Replaced the strategy context position flag with the actual quantity and capped crossover sell signals to that inventory.

Why: Partial fills must not produce oversized sell orders that the broker rejects.

### Added partial-position exit regression coverage

Summary: Added a moving average crossover test that verifies a ten share target exits only the available two and a half shares.

Why: Existing signal tests covered entries but not exit sizing after partial fills.

### Updated strategy position project tracking

Summary: Refreshed the assessment, completed work history, and future pending-order awareness backlog for quantity-aware strategy signals.

Why: The living project files must reflect both the corrected behavior and the remaining execution context limitation.

### Preserved cash for flat strategy runs

Summary: Loaded the latest cash snapshot for every strategy run independently from the open position query.

Why: Fully closed runs must retain their cash and equity in portfolio valuation.

### Added flat-run valuation regression coverage

Summary: Added a portfolio valuation test for a completed round trip with cash and no open position.

Why: The zero cash regression was not covered by the existing open position valuation test.

### Updated portfolio valuation project tracking

Summary: Refreshed the assessment, completed work history, and future portfolio scoping backlog for the corrected valuation behavior.

Why: The living project files must describe the repository and remaining work after every implementation change.

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
