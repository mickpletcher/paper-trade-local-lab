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

Historical files use `date,open,high,low,close,volume`. Import rejects missing values, nonfinite or nonpositive prices, high below low, open or close outside the candle, and negative or fractional volume. Imports upsert by symbol and timestamp.

The Alpaca snapshot adapter parses the root ticker map. Refresh retries rate limits, server failures, network timeouts, and invalid JSON with exponential backoff. The requested symbol set must match the response exactly before any quote is persisted.

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
