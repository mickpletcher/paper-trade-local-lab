# Tier Three Platform

## Runtime Shape

The historical `BacktestEngine` remains the authoritative execution path. A portfolio run allocates capital to one engine instance per symbol and aggregates the results inside one transaction. Any sleeve failure rolls back all database records and removes generated reports. This preserves existing fill, risk, corporate action, audit, report, and experiment behavior while preventing one symbol from consuming another sleeve's cash.

`EventRuntime` is a deterministic in process priority queue for timezone aware bar, tick, news, and system events. Timestamp orders events first. Publication order breaks timestamp ties. Handlers run synchronously. It is infrastructure for later streaming work, not a second broker loop.

The Pandas vectorized path calculates moving average cross signals for research batches. Multiprocessing distributes independent analytics tasks. Neither shortcut changes order simulation. `scripts/Test-BacktestPerformance.py` fails when the declared vectorized runtime budget is missed.

## Extension Boundary

`PluginRegistry` owns four entry point groups:

| Kind | Entry point group |
| --- | --- |
| Strategy | `tradeforge.strategies` |
| Broker | `tradeforge.brokers` |
| Indicator | `tradeforge.indicators` |
| Report | `tradeforge.reports` |

Built ins are always registered. Installed entry points load only when their normalized plugin name appears in `TRADEFORGE_PLUGIN_ALLOWLIST_JSON`. Duplicate names fail. Listing a package is an explicit decision to execute its Python code in the TradeForge process. Plugins have no sandbox.

## Research Provenance

Every completed backtest creates one `Experiment`. It records tenant, strategy run, built in strategy version, parameters, an SHA-256 hash of the exact ordered price bars, and hashes for generated report artifacts. Dataset JSON and artifacts are streamed into their digests with bounded memory. Repeated tracking of the same strategy run returns the existing record.

## API And Tenants

Authentication remains off by default for loopback use. When enabled, API keys are opaque service identities containing a public key ID and random secret. The database stores only per key salted PBKDF2-HMAC-SHA-256 verifiers. Authentication selects the key ID, derives a candidate verifier, and uses constant time comparison. Keys have a role, expiration, revocation state, last use time, and tenant. Rotation revokes the old key before returning a one time replacement secret.

Viewer keys access read only tenant data. Operator keys additionally access metrics. Admin is reserved for future administrative routes. Symbols and quotes are shared reference data. Positions, orders, strategy runs, experiments, dashboard rows, and portfolio selection are tenant scoped.

The dashboard is server rendered HTML with escaped database values, a restrictive content security policy, and no client side dependencies.

## Market And Connector Boundaries

Instrument value objects cover international equities, fixed income, rates, credit, volatility, index derivatives, CFDs, two leg calendar spreads, OTC spot metals, and binary prediction contracts. These models calculate value or profit and loss. They are not integrated with the bar broker, settlement ledger, margin, or live routes.

`MarketMicrostructure` models auction phase labels, halts, price limits, odd lots, latency, queue ahead quantity, available quantity, and square root market impact. It is an explicit scenario model and does not silently alter existing bar fills.

Tradier, TradeStation, MetaTrader, NinjaTrader, cTrader, and generic crypto descriptors expose quote request construction, quote normalization, and nontransmitting paper signals. Remote URLs require HTTPS. HTTP is accepted only for loopback bridge adapters. Every descriptor declares `live_order_routing=false`.

## Operations

Maintenance measures local backup restore time. `run-dr-drill` also compares newest backup age and restore duration with configured RPO and RTO targets and writes an atomic report.

Semantic release automation reads conventional commits, calculates the next semantic version, runs tests plus migration and performance gates, and opens an automatically squash merged release preparation pull request. When a validated version is ready, it creates the tag and directly calls the reusable release workflow. Manual tag pushes can call the same workflow. The release rebuilds, generates the SBOM, attests artifacts, and publishes the GitHub release.

Supported Python 3.11 through 3.14 environments install from the same lock before the full test suite. Dependency updates cannot substitute the runner's preinstalled package set for the committed lock.

## Cross Links

* [dependency evaluation](./dependency-evaluation.md)
* [backtesting](../backtesting/README.md)
* [plugins](../plugins/README.md)
* [API](../api/README.md)
* [security](../security/README.md)
