# Future Upgrades

Keep each item concrete and move completed items to `COMPLETED-UPGRADES.md` with their completion date.

## Tier 1 (High)

### Automation And Reliability

* Add clean clone bootstrap canaries for both LF and CRLF Git checkout policies on Windows and Linux.
* Add executable documentation tests that run every root README novice workflow against a disposable database and container.
* Automatically close repeated failure issues after the affected workflow completes successfully twice.
* Add signed audit comments that identify the exact Dependabot commit synchronized into living documents.
* Publish compatibility canary results as a machine readable pull request artifact and summary.
* Escalate persistent Python prerelease failures only after three scheduled runs fail on the same interpreter.
* Add pinned Python, uv, Node, and npm toolchain installation to the cross-platform bootstrap command.
* Verify downloaded wheel hashes and Trusted Publishing attestations before accepting a dependency lock update.
* Expand mutation coverage to strategy signals, data repair, corporate actions, and notification deduplication.
* Store migration benchmark history and reject statistically significant performance regressions.
* Add a `doctor --repair` mode that creates a clean lock-faithful virtual environment without changing the active one.
* Add static type contract tests that compare Mypy output across every supported interpreter.
* Add expiring, owner assigned exceptions for dependency license and denied package policy violations.
* Add a database backed lease for maintenance when the application moves beyond one workstation.
* Persist SQLite health telemetry and alert on lock wait or WAL checkpoint threshold breaches.
* Add a repeated connection lifecycle stress test that fails on delayed finalization or leaked handles.
* Schedule a local Task Scheduler lifecycle canary and recreate the maintenance task when drift is detected.
* Enforce backup recovery point and recovery time objectives with encrypted off-device copies.
* Add rule based quarantine remediation for known safe CSV formatting defects.
* Add a retention retry queue with bounded backoff for reports locked by scanners or backup tools.
* Record Teams and email delivery receipts and surface exhausted escalation attempts in local health.
* Add configurable staleness thresholds and reason codes to the local health command.
* Add circuit breaker half-open probes and a bounded global quote retry budget.
* Open a remediation pull request when repository policy drift can be corrected safely.
* Verify release and GHCR attestations after publication and block promotion on verification failure.
* Exercise reusable release publication with disposable prerelease tags and reject duplicate tag or release attempts.
* Add transaction fault injection at portfolio report, artifact, flush, and commit boundaries.

### Trading Safety And Data Quality

* Add per strategy and per symbol risk profiles with controlled runtime overrides.
* Make gap detection exchange calendar aware and distinguish holidays from missing market sessions.
* Reconcile corporate actions against two independent sources before applying them to research data.
* Add property based corporate action invariants that reconcile cash, positions, trades, and pending orders.
* Add hash chained execution audit records with verification and tamper detection commands.
* Add versioned API key verifier formats with automatic work factor upgrades and identity rotation.
* Add exchange calendar aware benchmark joins that report every dropped or substituted timestamp.

## Tier 2 (Medium)

### Execution And Research

* Add day, GTC, IOC, and FOK time in force behavior.
* Add trailing stops and bracket orders.
* Add configurable limit order queue assumptions.
* Add fill quality reporting for commission, slippage, cancellation, and partial fill rates.
* Add parameter sweeps for the moving average strategy.
* Add breakout, mean reversion, and RSI strategies.
* Add portfolio sizing models including fixed fractional and volatility targeting.
* Add account level aggregation and deliberate multi run portfolio reporting.
* Add walk forward optimization, Monte Carlo reshuffling, and stress tests.
* Add configurable risk free rates, benchmark symbols, and trading calendar annualization to backtest metrics.
* Add deterministic replay seeds, immutable input snapshots, and artifact checksums.
* Add idempotency keys for externally submitted order intents and maintenance runs.
* Add a live quote persistence benchmark that enforces constant query growth across large symbol sets.
* Add database engine lifecycle telemetry for configuration provenance, leaked sessions, and slow disposal.
* Add bounded memory and duration budgets for experiment dataset and artifact hashing.

### Interfaces And Integrations

* Add a configuration diagnostic command that reports non-sensitive effective settings and their sources.
* Add pagination query budgets and maximum page sizes to every list endpoint.
* Add API and schema versioning with compatibility tests.
* Add authenticated TradingView webhook intake with replay protection and idempotency.
* Add a canonical adapter interface for paper brokers and external signals.
* Add a second live quote provider with automatic failover.
* Add Interactive Brokers, Alpaca, and OANDA paper adapters behind the canonical interface.
* Add structured notification adapters for failed scheduled jobs.
* Add HMAC signed webhook delivery with receiver replay protection and duplicate suppression.
* Add an explicit webhook hostname allowlist for deployments with fixed notification receivers.
* Add authentication and transport guidance before supporting API access outside a trusted local network.
* Add protected deployment environments if the project gains hosted deployment targets or production secrets.
* Add dashboard query plan checks and configurable limits for shared reference data.

### Market Coverage

* Add crypto spot symbols, fee tiers, import, and replay.
* Add options chains, single leg execution, and common multi leg strategies.
* Add futures contracts, rollover, margin, and mark to market accounting.
* Add forex pairs, spreads, swaps, sessions, and base currency reporting.
* Add short selling, borrow fees, locate failures, and forced buy ins.
* Add settlement calendars and delayed cash availability.
* Validate tenant identifiers as UUIDs and compare runtime defaults with migration fixtures in CI.

## Tier 3 (Low)

### Platform Expansion

* Add a shared multi currency portfolio ledger with cross sleeve cash netting and FX attribution.
* Add a durable event store with deterministic replay and schema evolution for runtime events.
* Run third party plugins out of process with signed packages, resource limits, and explicit capabilities.
* Add interactive experiment comparison views with parameter, dataset, and metric diffs.
* Add signed remote worker jobs for distributed experiment batches.
* Add GPU accelerated scenario analytics with deterministic CPU parity gates.
* Add per tenant storage, compute, and request quotas with local audit exports.
* Add optional OIDC identity federation while retaining local service identities.
* Add automated release rollback preparation and forward and backward schema compatibility checks.
* Add Windows Credential Manager, Azure Key Vault, and environment secret provider adapters.
* Add isolated multi site recovery simulations with dependency and operator handoff timing.
* Add a local provenance verification dashboard for packages, images, locks, and research artifacts.
* Add cross architecture artifact reproducibility checks for x64 and ARM64 runners.

### Extended Markets And Connectors

* Add validated exchange calendars, security masters, currencies, and corporate action reference feeds.
* Add Level 2 order book ingestion and deterministic depth replay with bounded storage.
* Add a connector conformance harness with recorded sandboxes, rate limit tests, and capability certification.
* Add options volatility surface calibration, Greeks, and scenario attribution.
* Add versioned yield curve, benchmark rate, credit spread, and macro factor surfaces.

<!-- dependabot-sync: build(deps): bump the github-actions group across 1 directory with 4 updates -->
