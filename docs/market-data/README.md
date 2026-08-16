# Market Data

## Purpose

This section documents provider integration, normalization, replay sources, and data quality rules.

## Intended Contents

* provider contracts
* import flows
* quote refresh paths
* replay datasets
* quality controls

## Current Controls

Historical files use `date,open,high,low,close,volume`. Import normalizes timezone naive timestamps to UTC, keeps the last duplicate timestamp, flags elapsed gaps, rejects configurable close return outliers, and records every repair finding. It also rejects missing values, nonfinite or nonpositive prices, invalid OHLC relationships, and negative or fractional volume. Imports upsert by symbol and timestamp. Scheduled success moves the source into a checksummed processed archive; failure moves it into quarantine with an error sidecar until `tradeforge acknowledge-import` accepts or retries it.

The Alpaca snapshot adapter parses the root ticker map and refuses redirects so credential headers cannot reach another destination. Refresh retries rate limits, server failures, network timeouts, and invalid JSON with exponential backoff plus randomized jitter. Repeated final failures open a persistent circuit breaker until its reset window. The requested symbol set must match the response exactly before any quote is persisted.

Provider output must contain timezone-aware timestamps and a usable last price or bid and ask pair. Prices must be finite and positive. Sizes must be nonnegative integers. Crossed markets, malformed raw payloads, and nonfinite JSON constants fail the refresh without updating stored quotes. Persistence loads symbols once and existing provider rows once, so database reads do not grow per returned symbol. `age_seconds` measures market-data age from the provider timestamp, while `fetch_age_seconds` reports how long ago TradeForge retrieved the quote.

## Suggested Future Topics

* provider-interface.md
* csv-imports.md
* live-quote-providers.md
* replay-data-model.md
* data-quality-checks.md

## Naming Conventions

* provider docs use provider names
* ingest docs use `import` or `ingest`
* dataset docs distinguish historical from live

## File Examples

* `provider-interface.md`
* `alpaca-provider.md`
* `data-quality-checks.md`

## Cross Links

* [database](../database/README.md)
* [backtesting](../backtesting/README.md)
