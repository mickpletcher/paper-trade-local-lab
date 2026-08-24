# Completed Upgrades

This file tracks shipped roadmap work that was previously listed in `FUTURE-UPGRADES.md`.

## 2026-08-16

* Made portfolio strategy runs, experiments, artifacts, and reports persist atomically across every sleeve.
* Aligned asset and benchmark close series by timestamp before beta calculation.
* Made semantic release call the reusable packaging, SBOM, attestation, and GitHub release workflow directly after tagging.
* Streamed dataset and artifact provenance hashing with bounded memory use.
* Replaced dashboard symbol identifier materialization with a SQL count.
* Centralized the runtime default tenant identifier across settings and database models.
* Added regression coverage for every Tier 3 review fix.
* Hardened API keys with per key salted PBKDF2 verification and constant time comparison.
* Added allocated multi symbol portfolio backtesting with equal and fixed capital rules.
* Added a deterministic event runtime for timezone aware bar, tick, news, and system events.
* Added allowlisted strategy, broker, indicator, and report entry point plugins.
* Added a tenant scoped server rendered dashboard for symbols, positions, orders, and strategy runs.
* Added rolling risk, factor beta, benchmark beta, and market regime analytics.
* Added immutable experiment tracking for strategy versions, parameters, dataset hashes, and report artifacts.
* Added vectorized moving average signals, multiprocessing analytics, and a CI performance budget.
* Added optional API authentication, expiring API keys, cumulative roles, and tenant isolation.
* Added conventional commit semantic release automation with test, migration, and performance gates.
* Added one time service identity secrets with default expiration, rotation, revocation, and least privilege roles.
* Added local disaster recovery drills with measured recovery point and recovery time objectives.
* Extended lock faithful full suite CI to every supported Python version before dependency changes merge.
* Added fixed income, rates, credit, volatility, index derivative, and international equity value models.
* Added CFD, calendar spread, OTC spot metal, and binary prediction market simulation models.
* Added auction, halt, price limit, odd lot, latency, queue, and market impact scenario models.
* Added safe quote and paper signal connector adapters for Tradier, TradeStation, MetaTrader, NinjaTrader, cTrader, and crypto exchanges.
* Evaluated LEAN, backtesting.py, Zipline Reloaded, Freqtrade, Hummingbot, CCXT, TA-Lib, and pandas-ta before dependency adoption.
* Made dependency lock provenance verification stable across LF and CRLF checkouts.
* Replaced the root project overview with a complete Windows first novice operator manual.
* Made GHCR publication wait for the strict typing, mutation, and migration gates.
* Replaced repeated corporate action scans with one ordered action cursor.
* Made environment inspection tolerate installed distributions without a package name.
* Made report retention failures nonfatal and visible in the maintenance report.
* Restored original ticker filenames when retrying timestamped quarantined imports.
* Initialized empty risk projection positions with explicit numeric zeros.
* Enforced maximum order notional across cumulative partial fills.
* Stopped pending and future execution after a backtest delisting.
* Reconciled delisting liquidation with position and trade realized profit and loss.
* Adjusted pending order quantities and prices when a split applies.
* Rejected missing or nonpositive split ratios during corporate action application.
* Added automatic deduplicated GitHub issue creation after two consecutive CI or governance failures.
* Added trusted Dependabot living document synchronization before governance validation.
* Added a compatibility canary for workflow, dependency, and container runtime changes.
* Added a scheduled nonblocking Python prerelease test and strict type canary.
* Added one cross-platform bootstrap command for locked Python and declared Node validation dependencies.
* Added lock digest and source provenance metadata with GitHub OIDC Sigstore attestation on `main`.
* Added targeted mutation tests for broker execution, backtest metrics, and portfolio valuation.
* Added a 25,000 row synthetic migration performance gate.
* Added `tradeforge doctor` environment and lock provenance verification.
* Added strict Mypy jobs for Python 3.11, 3.12, 3.13, and 3.14.
* Added explicit dependency license allow rules and denied package policies.
* Added an atomic, stale aware maintenance concurrency lock.
* Added SQLite connection, lock probe, busy timeout, journal, and WAL checkpoint telemetry.
* Closed raw SQLite connections explicitly in local health and migration validation paths.
* Added a disposable Windows Task Scheduler lifecycle canary.
* Added automatic newest backup restore drills with recovery time and table count reporting.
* Added processed import archiving, failure quarantine, and explicit acknowledge or retry handling.
* Added Teams and SMTP escalation with bounded retry and duplicate suppression.
* Added maintenance report retention and the exit coded `tradeforge health` summary.
* Added randomized quote retry jitter and a persistent provider circuit breaker.
* Added scheduled repository policy drift checks for required checks, action pins, allowlists, and security settings.
* Added CycloneDX release SBOMs, release attestations, and GHCR provenance plus SBOM publication.
* Added a risk engine with order notional, position, gross exposure, drawdown, and kill switch controls.
* Added OHLCV gap, duplicate, outlier, timezone normalization, and durable repair findings.
* Added split, dividend, symbol change, and delisting records and backtest application.
* Added durable execution audit events for triggers, cancellations, rejections, remaining quantity, and corporate actions.
* Initialized persistent SQLite WAL mode once per engine instead of on every connection.
* Honored explicit SQLite busy timeout settings in programmatic maintenance runs.
* Added Windows CI coverage for the daily Task Scheduler installer and its nonmutating `WhatIf` path.
* Enabled SQLite WAL and configurable bounded lock waits with contention regression coverage.
* Reused and disposed one database engine for each complete maintenance run.
* Disposed temporary engines owned by transactional session scopes.
* Batched existing live quote reads into one set based query per refresh.

## 2026-08-15

* Enforced the selected Actions allowlist and SHA pinning, verified repository security controls, and required dependency review, dependency audit, CodeQL, and Python 3.14 checks before merge.
* Reconstructed migrated trade fees by directional fill quantity sequence across shared lifecycle timestamps.
* Indexed legacy migration fills by strategy run and symbol instead of rescanning all fills per trade.
* Added regression coverage for the public `init-db` automation command.
* Ran CI lint and strict Mypy in a Python 3.11 environment aligned with the configured compatibility target.
* Removed the CLI schema initializer alias while preserving the public `init-db` command.
* Aligned strict Mypy analysis with the minimum supported Python 3.11 runtime.
* Consolidated duplicate CLI migration imports.
* Distinguished runner unit tests from the separate container build and health validation in runtime documentation.
* Clarified the non-sensitive output boundary for the planned configuration diagnostic.
* Blocked automatic failure webhook redirects so validated HTTPS destinations cannot forward requests to unvalidated endpoints.
* Made outbound URL validation errors identify forbidden whitespace.
* Minimized outbound failure webhook data while retaining detailed local reports.
* Enforced shared HTTPS, hostname, and no credential validation for outbound URLs.
* Enforced an 88 percent test coverage floor in every supported Python CI job.
* Added strict Mypy validation with Pandas typing support.
* Expanded Ruff to Bugbear, import ordering, simplify, and Ruff specific rules.
* Added Python 3.14 to the hosted runner test matrix so it matches the separately validated container runtime.
* Expanded backtest reports with risk adjusted, trade distribution, exposure, and passive benchmark metrics.
* Added single statement relationship loading for API symbols and strategies with query count regression coverage.
* Cached validated process settings and documented restart behavior for configuration changes.

## 2026-08-14

* Promoted unexpected test warnings to failures and migrated Starlette tests from the deprecated HTTPX path to HTTPX2.
* Separated gross trade entry and exit prices from commission totals with migration and reconciliation coverage.
* Added configurable quantity increments with whole share defaults and cash cap quantization.
* Reused one application database engine and session factory across API requests with lifespan disposal.
* Consolidated local container startup on the hardened `compose.yaml` definition.
* Removed the unused replay module and documented the direct historical bar backtest path.
* Upgraded the commit pinned dependency review gate to v5.0.0.
* Removed an undeclared Pytest plugin setting so clean test runs are warning free.
* Locked Pip Audit and its transitive dependencies for reproducible local and scheduled security checks.
* Added one path safe PowerShell Markdown validation command shared by Windows operators and CI.
* Reconciled the open security audit and dependency branches without regressing the newer trading correctness fixes.
* Upgraded the digest pinned container runtime to Python 3.14 slim.
* Upgraded checkout, Python setup, Node setup, and uv setup workflows to their current commit pinned major versions.
* Closed automated review findings for no-fill reversals, first run database paths, Linux container storage, bounded retries, and linear quote validation.
* Made dependency lock generation deterministic across operating systems by targeting the minimum supported Python version.
* Protected `main` with strict required checks, linear history, resolved conversations, squash only merges, and branch cleanup.
* Pinned transitive dependencies, build tooling, Actions, Markdownlint, and the Docker base image with automated drift checks and Dependabot updates.
* Added Python 3.11 and 3.13 CI coverage plus live container health validation.
* Hardened the container with a nonroot user, database health check, loopback only Compose binding, restart policy, read only root, and dropped capabilities.
* Added unattended maintenance for idempotent CSV imports, open position quote refresh, run summaries, and optional failure webhooks.
* Added integrity verified SQLite backups with configurable retention and a daily Windows Task Scheduler installer.
* Added retry with exponential backoff and exact requested symbol completeness enforcement to live quote refresh.
* Added pending order quantities to strategy context and cancellation of stale opposite orders during signal reversals.
* Added explicit or latest strategy run portfolio selection and deterministic newest quote selection.
* Added OHLC relationship, finite positive price, and nonnegative integer volume validation to CSV imports.
* Added fail fast validation for moving average window and order size parameters.
* Moved API migrations to application startup and made health checks verify database connectivity.
* Corrected Alpaca multi-symbol snapshot parsing and added provider response contract coverage.
* Made strategy signals quantity aware and capped moving average exits to available inventory.
* Preserved the latest cash snapshot for fully closed strategy runs in portfolio valuation.
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

<!-- dependabot-sync: build(deps): bump the github-actions group across 1 directory with 4 updates -->
