# Future Upgrades

Keep each item concrete and move completed items to `COMPLETED-UPGRADES.md` with their completion date.

## Tier 1 (High)

### Automation And Reliability

* Add automatic GitHub issue creation for repeated governance or CI failures without creating duplicates.
* Automate living document synchronization for trusted Dependabot updates before governance validation.
* Add automatic compatibility canaries before merging new major Actions and container runtime versions.
* Add a scheduled Python prerelease canary that does not block supported runtime builds.
* Add one cross-platform bootstrap command for Python and Node validation dependencies.
* Add signed lock metadata and automated verification of dependency source provenance.
* Add mutation testing for broker execution, metrics, and valuation correctness paths.
* Add a developer environment verifier that reports undeclared and version drifted packages against `requirements.lock`.
* Add explicit allowed license and denied package policies to dependency review.
* Add a maintenance concurrency lock so overlapping scheduled runs fail safely.
* Add automatic restore drills from the newest backup with recovery time reporting.
* Add import quarantine and acknowledgement so successful files are not reprocessed indefinitely.
* Add Teams and email escalation adapters with retry and duplicate suppression.
* Add maintenance report retention and a local health summary command.
* Add randomized retry jitter and a provider circuit breaker for extended quote outages.
* Verify Dependabot alerts and security updates, secret scanning and push protection, default read-only Actions permissions, and the Actions allowlist in GitHub settings.
* Publish an SBOM plus build provenance for release and GHCR artifacts.

### Trading Safety And Data Quality

* Add a risk engine with per trade limits, exposure caps, maximum drawdown controls, and a kill switch.
* Add data quality checks for gaps, duplicates, outliers, timezones, and repair actions.
* Add corporate action handling for splits, dividends, symbol changes, and delistings.
* Add execution audit events for triggers, cancellations, rejections, and remaining quantity changes.

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

### Interfaces And Integrations

* Add a configuration diagnostic command that reports nonsecret effective settings and their sources.
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
* Add isolated locked environment smoke tests for every declared Python version before dependency update merges.

### Extended Markets And Connectors

* Add fixed income, rates, credit, volatility, index derivative, and international equity models.
* Add CFD, spread, calendar, OTC spot metal, and prediction market simulation.
* Add auction, halt, price limit, odd lot, latency, queue, and market impact models.
* Add Tradier, TradeStation, MetaTrader, NinjaTrader, cTrader, and crypto exchange connectors.
* Evaluate Lean, backtesting.py, Zipline, Freqtrade, Hummingbot, CCXT, TA Lib, and pandas TA patterns before adopting dependencies.
