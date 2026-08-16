# Trading Dependency Evaluation

Evaluated on 2026-08-16 before adding Tier 3 platform dependencies. Decision: adopt useful architecture patterns but add none of these packages to the runtime lock now.

| Project | Useful Pattern | Decision |
| --- | --- | --- |
| [QuantConnect LEAN](https://github.com/QuantConnect/Lean) | Event driven components, explicit models, broad asset support, broker conformance concepts | Do not embed. It is a separate Python and C# trading engine with a much larger runtime and overlapping responsibilities. Use its component boundaries as design references. |
| [backtesting.py](https://kernc.github.io/backtesting.py/doc/backtesting/) | Compact strategy API, vectorized indicators, optimization ergonomics | Do not add. The existing engine owns durable orders, partial fills, risk, corporate actions, and audit records. Its AGPL license also needs a deliberate distribution review before code reuse. |
| [Zipline Reloaded](https://github.com/stefan-jansen/zipline-reloaded) | Event scheduling, data bundles, exchange calendars, pipeline research | Do not add. Its engine and ingestion model overlap TradeForge. Reevaluate its calendar and bundle patterns when exchange aware sessions are implemented. |
| [Freqtrade](https://docs.freqtrade.io/en/latest/backtesting/) | Reproducible crypto backtests, fee aware results, detailed timeframe simulation | Do not embed. It is a crypto trading application, not a small execution dependency. Keep its reproducibility and intrabar documentation patterns. |
| [Hummingbot](https://hummingbot.org/docs/) | Standardized connector interfaces, modular strategies, clock driven execution | Do not embed. It targets live crypto and market making operations. Reuse the connector capability and strategy separation concepts only. |
| [CCXT](https://github.com/ccxt/ccxt/wiki/manual) | Unified public exchange API with explicit per venue capabilities | Candidate only for the future crypto spot adapter. Adoption requires a read only proof, rate limit tests, symbol mapping, credential isolation, and a locked license and vulnerability review. |
| [TA-Lib](https://ta-lib.org/) | Stable indicator definitions and candlestick pattern names | Do not add. The native C dependency expands cross platform packaging. Use formula parity tests if an indicator needs a recognized reference. |
| [pandas-ta](https://pypi.org/project/pandas-ta/) | DataFrame indicator composition and bulk research ergonomics | Do not add. The current release line is beta and requires Python 3.12 while TradeForge supports Python 3.11. Reevaluate a stable, provenance verified release or maintained alternative later. |

## Adopted Patterns

* deterministic event ordering
* explicit plugin and connector capabilities
* allowlisted extension loading
* vectorized research without bypassing execution accounting
* immutable experiment inputs and artifact hashes
* paper only connector signals with no live order route

## Dependency Admission Gate

A future adoption must have one bounded use case, compatible licensing, supported Python wheels, lock and provenance coverage, no credential expansion outside the documented boundary, deterministic fixtures, benchmark evidence, and a removal plan.
