# Future Upgrades

Keep each item concrete and move completed items to `COMPLETED-UPGRADES.md` with their completion date.

## Tier 1 (High)

### Automation And Reliability

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

### Trading Safety And Data Quality

* Add per strategy and per symbol risk profiles with controlled runtime overrides.
* Make gap detection exchange calendar aware and distinguish holidays from missing market sessions.
* Reconcile corporate actions against two independent sources before applying them to research data.
* Add property based corporate action invariants that reconcile cash, positions, trades, and pending orders.
* Add hash chained execution audit records with verification and tamper detection commands.

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

### Market Coverage

* Add crypto spot symbols, fee tiers, import, and replay.
* Add options chains, single leg execution, and common multi leg strategies.
* Add futures contracts, rollover, margin, and mark to market accounting.
* Add forex pairs, spreads, swaps, sessions, and base currency reporting.
* Add short selling, borrow fees, locate failures, and forced buy ins.
* Add settlement calendars and delayed cash availability.

## Tier 3 (Low)

### Platform Expansion

* Add portfolio level multi symbol backtesting with capital allocation rules.
* Add an event driven runtime for bars, ticks, and news events.
* Add a plugin system for strategies, brokers, indicators, and reports.
* Add a web dashboard for symbols, orders, positions, and runs.
* Add advanced analytics for rolling risk, factors, beta, and market regimes.
* Add experiment tracking for strategy versions, parameters, datasets, and artifacts.
* Add vectorized and multiprocessing execution paths with benchmark gates.
* Add authentication, API keys, role based access, and tenant isolation.
* Add semantic release automation with migration and benchmark gates.
* Add secrets rotation and least privilege service identities.
* Add disaster recovery drills with measured recovery objectives.
* Add signed release provenance and software bill of materials publication.
* Add isolated locked environment full-suite tests for every declared Python version before dependency update merges.

### Extended Markets And Connectors

* Add fixed income, rates, credit, volatility, index derivative, and international equity models.
* Add CFD, spread, calendar, OTC spot metal, and prediction market simulation.
* Add auction, halt, price limit, odd lot, latency, queue, and market impact models.
* Add Tradier, TradeStation, MetaTrader, NinjaTrader, cTrader, and crypto exchange connectors.
* Evaluate Lean, backtesting.py, Zipline, Freqtrade, Hummingbot, CCXT, TA Lib, and pandas TA patterns before adopting dependencies.
