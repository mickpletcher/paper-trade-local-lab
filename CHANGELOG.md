# Changelog

## 2026-08-31

### Restored repository policy automation

Summary: Authenticated scheduled policy audits with a repository-scoped read-only administration token, added a missing-secret preflight, and refreshed the universal dependency lock and provenance digest.

Why: The built-in workflow token cannot read branch protection and administration settings, and stale dependency pins blocked unrelated pull requests.

## 2026-08-24

### Automated dependency synchronization: build(deps): bump the github-actions group across 1 directory with 4 updates

Summary: Refreshed the living project records for the trusted Dependabot update `build(deps): bump the github-actions group across 1 directory with 4 updates`.

Why: Dependency changes must update current state before governance validation.

## 2026-08-16

### Made portfolio persistence atomic

Summary: Deferred sleeve commits into one nested portfolio transaction and removed generated reports when any sleeve or final commit fails.

Why: A failed multi symbol run must not leave earlier strategy runs, experiments, artifacts, or reports behind as a partial result.

### Aligned benchmark analytics by timestamp

Summary: Loaded timestamped close series and inner joined asset and benchmark bars before calculating returns and beta.

Why: Different calendars or history ranges must not cause length errors or silently pair prices from different dates.

### Invoked validated releases directly

Summary: Converted the release workflow into a reusable workflow and called it after semantic release creates a validated tag while retaining independent tag push support.

Why: Tags pushed with the workflow token do not trigger another push workflow, which could otherwise skip packages, attestations, SBOMs, and the GitHub release.

### Streamed experiment provenance hashing

Summary: Hashed ordered price bar JSON incrementally and hashed report artifacts in bounded chunks without materializing complete datasets or files.

Why: Provenance generation should have bounded memory growth as backtest history and report artifacts increase.

### Counted dashboard symbols in SQL

Summary: Replaced dashboard symbol identifier materialization with a database `COUNT(*)` query.

Why: Rendering one summary card should not allocate memory proportional to the complete symbol catalog.

### Centralized the runtime default tenant identifier

Summary: Moved the default tenant UUID into one dependency neutral runtime constant shared by settings and database models while leaving the historical migration self contained.

Why: Runtime defaults must not drift apart, and applied Alembic revisions must remain immutable snapshots.

### Added review fix regression coverage

Summary: Added tests for atomic portfolio rollback and report cleanup, timestamp aligned beta, streaming digest compatibility, SQL dashboard counts, the shared tenant default, and direct reusable release invocation.

Why: Each resolved review finding needs an executable guard against recurrence.

### Hardened API key fingerprints

Summary: Stored each API secret as a 600,000 iteration, per key salted PBKDF2-HMAC-SHA-256 verifier and selected identities by the public key ID before constant time verification.

Why: API key storage should resist offline guessing, avoid direct secret fingerprints, and pass the repository's high severity CodeQL policy without persisting raw secrets.

### Added allocated portfolio backtests

Summary: Added equal and fixed capital allocation across multiple isolated symbol backtests with aggregate equity, return, reports, and lifecycle events.

Why: Portfolio research needs repeatable multi symbol comparisons without weakening the existing single symbol execution accounting.

### Added deterministic event processing

Summary: Added a timestamp and publication ordered runtime for timezone aware bar, tick, news, and system events.

Why: Future streaming and portfolio workflows need one predictable event ordering contract.

### Added allowlisted plugins

Summary: Added built in and entry point registries for strategies, brokers, indicators, and reports with normalized names, duplicate rejection, and explicit installed plugin allowlisting.

Why: Extensions must be discoverable without automatically executing every installed package.

### Added the local research dashboard

Summary: Added a tenant scoped server rendered dashboard for symbols, positions, orders, and strategy runs with escaped values and restrictive browser headers.

Why: Operators need an immediately usable inspection surface without a separate frontend build or manual database queries.

### Added advanced research analytics

Summary: Added rolling annualized volatility, benchmark and factor beta, and simple bull, bear, sideways, and high volatility regime classification.

Why: Strategy review needs risk and market context beyond total return.

### Added immutable experiment provenance

Summary: Added strategy experiment and artifact records containing version, parameters, ordered dataset SHA-256, and generated report SHA-256 values.

Why: A reported result must remain traceable to its exact inputs and output artifact.

### Added vectorized and parallel research paths

Summary: Added Pandas vectorized moving average signals, multiprocessing analytics tasks, a 100,000 row benchmark script, and a CI performance budget.

Why: Independent research batches should scale without replacing the authoritative broker simulation path.

### Added optional tenant API authentication

Summary: Added opt in API key authentication, viewer, operator, and admin roles, tenant scoped research queries, and a public health and documentation boundary.

Why: Read only API data needs isolation and caller identity before any approved network exposure.

### Added semantic release automation

Summary: Added conventional commit release planning that gates version preparation on tests, migration performance, and backtest performance before opening an automatically squash merged release pull request.

Why: Release versions should advance from validated repository state without relying on a person to calculate, edit, tag, and publish them manually.

### Added service identity secret rotation

Summary: Added expiring one time API secrets with stored hashes, configurable default lifetimes, immediate revocation, metadata only listings, and replacement rotation.

Why: Automated callers need separate least privilege identities that can be retired or replaced without exposing reusable stored secrets.

### Added measured disaster recovery drills

Summary: Added a command that restores the newest backup, measures backup age and restore duration against configured RPO and RTO targets, writes an atomic report, and exits nonzero on a miss.

Why: Recoverability needs scheduled, machine readable evidence instead of assuming an existing backup is sufficient.

### Reconciled signed provenance tracking

Summary: Removed signed release provenance and SBOM publication from the open Tier 3 backlog after verifying the existing release and GHCR attestation workflows.

Why: The living roadmap must not report an already shipped supply chain control as future work.

### Isolated every supported Python test environment

Summary: Added Python 3.12 to the full CI matrix and made each Python 3.11 through 3.14 job bootstrap the committed lock before running the complete suite.

Why: Dependency updates must pass from lock faithful environments instead of inheriting undeclared runner packages.

### Added extended instrument models

Summary: Added validated value and profit and loss models for international equities, fixed income, rates, credit, volatility, and index derivatives.

Why: Cross asset research needs explicit instrument economics before deeper execution and accounting integration.

### Added extended derivative simulations

Summary: Added validated CFD, two leg calendar spread, OTC spot metal, and binary prediction contract models.

Why: Scenario research needs transparent payoff and carrying cost calculations without implying live venue support.

### Added market microstructure scenarios

Summary: Added auction phase, halt, price limit, odd lot, latency, queue ahead, available quantity, and square root market impact simulation.

Why: Researchers need explicit scenario controls for execution effects that completed OHLCV bars cannot represent.

### Added paper only connector adapters

Summary: Added Tradier, TradeStation, MetaTrader, NinjaTrader, cTrader, and generic crypto descriptors with safe quote request construction, response normalization, and nontransmitting paper signals.

Why: Connector contracts should be testable before credentials, network calls, or live order authority are introduced.

### Evaluated external trading frameworks

Summary: Documented dated adoption decisions for LEAN, backtesting.py, Zipline Reloaded, Freqtrade, Hummingbot, CCXT, TA-Lib, and pandas-ta using primary project sources.

Why: Architecture patterns and dependencies must be assessed for overlap, licensing, runtime support, and operational weight before entering the lock.

### Expanded the novice operator manual for Tier 3

Summary: Added copy and paste portfolio, analytics, experiment, plugin, connector, dashboard, API identity, secret rotation, and recovery objective procedures plus the complete new command inventory.

Why: New automation is incomplete when a first time Windows operator cannot configure, verify, rotate, recover, and troubleshoot it safely.

### Added Tier 3 regression coverage

Summary: Added end to end CLI and API tests plus unit coverage for event ordering, portfolio allocation, experiments, analytics, plugins, connectors, identities, market models, microstructure, and recovery drills.

Why: The expanded platform must retain the repository's warning free 88 percent coverage gate and verify tenant and secret safety boundaries.

### Made lock provenance verification portable

Summary: Canonicalized Windows CRLF line endings before verifying the signed dependency lock digest and added a regression test for a Windows checkout.

Why: Git's standard Windows line ending conversion must not make the documented bootstrap reject an otherwise unchanged and attested lock file.

### Added a novice operator manual

Summary: Replaced the root overview with a Windows first, copy and paste manual covering installation, first run verification, data and configuration, result interpretation, local API use, scheduled maintenance, failure recovery, backup restoration, Docker, upgrades, reset, removal, troubleshooting, and the complete CLI surface.

Why: A first time operator should be able to install, validate, automate, recover, and remove TradeForge without reconstructing procedures from source code or scattered technical documents.

### Gated image publication on standalone validation

Summary: Made GHCR publication depend on every strict Mypy matrix job and the correctness mutation and migration gates.

Why: A buildable commit must not publish when an independent correctness gate has failed.

### Made corporate action traversal linear

Summary: Replaced the per bar full corporate action scan with one ordered cursor that advances each action once.

Why: Backtest runtime should grow with bars plus actions instead of bars multiplied by actions.

### Hardened environment metadata inspection

Summary: Made `tradeforge doctor` skip installed distributions that do not expose a package name.

Why: One malformed package metadata record must not prevent diagnosis of the rest of the environment.

### Reported retention cleanup failures

Summary: Made report retention record locked or undeletable files in the current report without failing maintenance.

Why: Transient scanner or permission locks should remain visible without converting a successful maintenance run into a failure.

### Restored original import names on retry

Summary: Read the original CSV filename from the quarantine error sidecar before returning a failed import to the pending queue.

Why: Timestamped quarantine archive names must not become incorrect ticker symbols during retry.

### Initialized empty risk positions explicitly

Summary: Gave transient no-position risk projections explicit zero quantity, cost, and realized profit and loss values.

Why: SQLAlchemy column defaults are applied on insert and cannot be assumed on an unpersisted projection object.

### Enforced cumulative partial fill notional

Summary: Included all prior fill value for an order when checking its maximum execution notional.

Why: Multiple individually valid partial fills must not combine into an order that exceeds the configured limit.

### Stopped execution after delisting

Summary: Cancelled pending orders and skipped broker and strategy processing after a symbol becomes inactive during a backtest.

Why: A delisted security must not refill a liquidated position or accept later strategy orders.

### Reconciled delisting trade profit and loss

Summary: Made delisting liquidation update position realized profit and loss and close the active trade at the liquidation price.

Why: Cash, position, trade history, and reported realized results must agree after forced liquidation.

### Adjusted pending orders for splits

Summary: Scaled open order quantities and filled quantities while inversely scaling limit and stop prices when a split applies.

Why: Orders carried across a split must preserve their economic exposure.

### Rejected malformed split application

Summary: Made corporate action application fail fast when a stored split ratio is missing or nonpositive.

Why: Invalid persisted action data must not zero positions or cause division by zero.

### Closed synthetic SQLite connections

Summary: Made the local health test and migration benchmark close raw SQLite connections explicitly.

Why: Python 3.14 correctly surfaced delayed connection finalization as a warning in the compatibility canary.

### Refreshed the dependency lock

Summary: Updated Python Dotenv from 1.2.2 to 1.2.3 and regenerated its signed lock digest metadata.

Why: The universal resolver advanced during final validation and the committed lock must match current deterministic output.

### Added execution audit events

Summary: Persisted order trigger, cancellation, rejection, remaining quantity, and corporate action audit events in Alembic revision `005_tier_one_controls`.

Why: Execution decisions need a durable explanation trail instead of being inferred from final order state.

### Added corporate action handling

Summary: Added validated records and backtest processing for splits, dividends, symbol changes, and delistings.

Why: Historical strategy results must account for material security lifecycle events.

### Added market data quality controls

Summary: Normalized timezone naive timestamps, removed duplicate timestamps, flagged gaps, rejected return outliers, and persisted repair findings.

Why: Bad historical inputs otherwise become plausible but incorrect strategy results.

### Added trading risk enforcement

Summary: Enforced configurable order notional, position quantity, gross exposure, maximum drawdown, and kill switch limits in broker execution.

Why: Paper execution should fail safely before accepting orders outside declared risk policy.

### Published artifact SBOM and provenance

Summary: Added CycloneDX release SBOMs, signed release attestations, and BuildKit SBOM plus provenance for GHCR images.

Why: Published artifacts need verifiable dependency contents and build origin.

### Added repository policy drift detection

Summary: Added scheduled checks for required statuses, full SHA action pins, the Actions allowlist, vulnerability alerts, and security updates.

Why: Repository protections can drift outside the code review path and must be checked automatically.

### Added quote retry jitter and circuit breaking

Summary: Randomized retry delays and persisted a failure threshold circuit with timed recovery for Alpaca outages.

Why: Extended provider failures should not create synchronized retry storms or unbounded repeated calls.

### Added local automation health reporting

Summary: Retained a bounded set of maintenance reports and added the exit coded `tradeforge health` command.

Why: Scheduled automation needs a local, scriptable status surface instead of silent failure.

### Added escalated failure delivery

Summary: Added Teams and SMTP adapters with bounded retry and per channel duplicate suppression.

Why: Repeated failures need reliable escalation without flooding operators.

### Added import quarantine lifecycle

Summary: Archived successful imports, quarantined failures with error sidecars, and added acknowledge or retry handling.

Why: Successful files must not run forever and failed files need an explicit recovery path.

### Added automatic restore drills

Summary: Restored the newest SQLite backup into memory, checked integrity and table presence, and reported recovery time.

Why: A verified backup file is not sufficient evidence that recovery works.

### Added a real Windows scheduler canary

Summary: Added a hosted Windows test that registers, starts, verifies, and removes a disposable scheduled task.

Why: Mocked cmdlet validation cannot prove the operating system scheduler lifecycle works.

### Added SQLite maintenance telemetry

Summary: Reported connection time, lock probe time, busy timeout, journal mode, and WAL checkpoint state.

Why: Lock and checkpoint behavior must be observable before contention becomes an unexplained failure.

### Added a maintenance concurrency lock

Summary: Added an atomic process lock with stale lock recovery around every maintenance run.

Why: Overlapping scheduled runs can race imports, backups, reports, and quote refreshes.

### Enforced dependency license and package policy

Summary: Added explicit allowed licenses and denied package identifiers to dependency review.

Why: Vulnerability severity alone does not enforce legal or prohibited dependency boundaries.

### Expanded strict Mypy coverage

Summary: Added strict Mypy jobs for Python 3.11, 3.12, 3.13, and 3.14.

Why: Interpreter specific dependencies and stubs must remain compatible across every declared runtime.

### Added a lock faithful environment doctor

Summary: Added `tradeforge doctor` to report missing, mismatched, and undeclared packages and validate lock provenance.

Why: Lock drift checks do not detect extra or stale packages in an active developer environment.

### Added a migration performance gate

Summary: Added a 25,000 fill and trade synthetic migration benchmark with a 20 second CI limit.

Why: Schema upgrades must not become operationally unsafe as research histories grow.

### Added correctness mutation gates

Summary: Added controlled mutations for oversized sell protection, return direction, and portfolio cash inclusion.

Why: Passing tests should demonstrate that critical accounting defects are actually detected.

### Added signed lock provenance

Summary: Added verified lock digest, approved source, generation metadata, and GitHub OIDC Sigstore attestation on `main`.

Why: A deterministic lock also needs evidence of where it came from and what build signed it.

### Added one validation bootstrap command

Summary: Added `python scripts/bootstrap.py` for locked Python installation, optional declared Node dependencies, and environment verification.

Why: Contributors and CI should use one cross-platform setup path instead of reconstructing manual steps.

### Added a Python prerelease canary

Summary: Added a scheduled nonblocking Python 3.15 development test and type check.

Why: Upcoming interpreter failures should be visible before the runtime becomes supported without destabilizing current builds.

### Added compatibility canaries

Summary: Added full test and container build canaries for workflow, dependency, and container runtime changes.

Why: Major automation and runtime upgrades need compatibility evidence before merge.

### Automated trusted dependency documentation

Summary: Added a `pull_request_target` workflow that runs base branch automation and commits all four living documents to same repository Dependabot branches.

Why: Trusted dependency updates should satisfy living documentation governance without manual intervention or executing pull request code.

### Added repeated failure issue automation

Summary: Added automatic issue creation or comment updates after two consecutive CI or governance failures using an exact open issue title for deduplication.

Why: Persistent failures need an owned GitHub record without creating duplicate noise.

### Refreshed Tier 1 project records

Summary: Moved all 25 completed Tier 1 upgrades into the completion ledger, replaced them with 25 concrete candidates, and rewrote current state documentation.

Why: The four living files must describe the repository after the release rather than the backlog that preceded it.

### Initialized SQLite WAL once per engine

Summary: Moved file database WAL activation from the per-connection hook to SQLAlchemy's one-time first connection hook.

Why: WAL is a persistent database setting, so repeating its locking operation on every `NullPool` connection adds overhead and avoidable contention.

### Honored explicit maintenance lock settings

Summary: Passed the selected settings object's SQLite busy timeout into the maintenance engine and added regression coverage for nondefault values.

Why: Programmatic maintenance calls must not silently replace their explicit lock wait policy with process-global configuration.

### Validated Windows scheduling in CI

Summary: Added a Windows runner job and a PowerShell regression harness that parses the Task Scheduler installer, verifies its action, trigger, retry, catch up, immediate run, and `WhatIf` behavior, and blocks merges on failures.

Why: A Windows only automation entry point must be exercised automatically instead of depending on an operator to discover scheduler drift.

### Hardened SQLite concurrency

Summary: Enabled WAL for file backed SQLite databases, applied a configurable bounded busy timeout to every connection, and covered short write contention and timeout configuration with tests.

Why: Concurrent API and maintenance activity should wait briefly for ordinary locks instead of failing immediately or blocking without an explicit limit.

### Reused the maintenance database engine

Summary: Created one database engine per maintenance run, passed it through migrations, imports, and quote refresh sessions, and guaranteed disposal on success or failure.

Why: Scheduled maintenance should not repeatedly construct database engines while processing one logical run.

### Disposed session owned database engines

Summary: Made transactional session scopes dispose engines they construct while leaving caller supplied engine lifecycles under caller control.

Why: Short lived CLI and explicit database operations should release their engine resources without breaking shared maintenance or application engines.

### Batched live quote persistence lookups

Summary: Replaced one existing quote query per returned symbol with one set based lookup and added a fixed query budget regression test.

Why: Quote refresh database reads should remain constant as the open position symbol count grows.

### Refreshed medium priority reliability documentation

Summary: Updated configuration, database, market data, automation, roadmap, completed work, and current assessment records for the new scheduler, SQLite, engine lifecycle, and quote batching behavior.

Why: Living documentation must describe the repository that operators and contributors actually run.

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
