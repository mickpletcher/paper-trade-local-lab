# Future Upgrades

Keep each item concrete and move completed items to `COMPLETED-UPGRADES.md` with their completion date.

## Tier 1 (High)

### Automation And Reliability

* Add scheduled quote refresh with staleness checks, retry with backoff, and failure alerts.
* Add scheduled market data imports with validation, idempotency, and run summaries.
* Add automated SQLite backup, restore verification, retention, and failure reporting.
* Add container health checks and automatic restart behavior.
* Add automatic GitHub issue creation for repeated governance or CI failures without creating duplicates.
* Apply the proposed solo-maintainer `main` ruleset with pull requests, required checks, conversation resolution, deletion and force-push blocking, and an owner bypass after explicit approval.
* Verify Dependabot alerts and security updates, secret scanning and push protection, default read-only Actions permissions, and the Actions allowlist in GitHub settings.
* Pin the runtime container base image by digest and publish an SBOM plus build provenance for release and GHCR artifacts.
* Add a reproducible Python application lock strategy and use it for container builds and scheduled dependency audits.

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
* Add walk forward optimization, Monte Carlo reshuffling, and stress tests.
* Add deterministic replay seeds, immutable input snapshots, and artifact checksums.

### Interfaces And Integrations

* Add API and schema versioning with compatibility tests.
* Add authenticated TradingView webhook intake with replay protection and idempotency.
* Add a canonical adapter interface for paper brokers and external signals.
* Add a second live quote provider with automatic failover.
* Add Interactive Brokers, Alpaca, and OANDA paper adapters behind the canonical interface.
* Add structured notification adapters for failed scheduled jobs.
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

### Extended Markets And Connectors

* Add fixed income, rates, credit, volatility, index derivative, and international equity models.
* Add CFD, spread, calendar, OTC spot metal, and prediction market simulation.
* Add auction, halt, price limit, odd lot, latency, queue, and market impact models.
* Add Tradier, TradeStation, MetaTrader, NinjaTrader, cTrader, and crypto exchange connectors.
* Evaluate Lean, backtesting.py, Zipline, Freqtrade, Hummingbot, CCXT, TA Lib, and pandas TA patterns before adopting dependencies.
