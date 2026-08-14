# Configuration

## Purpose

This section defines runtime settings, profiles, defaults, and configuration guardrails.

## Intended Contents

* environment variables
* profile design
* secret boundaries
* config validation
* sample `.env` patterns

## Current Execution Settings

* `TRADEFORGE_STARTING_CASH` must be greater than zero.
* `TRADEFORGE_COMMISSION_MODEL` must be `fixed` or `per_share`.
* `TRADEFORGE_FEE_PER_ORDER` is charged once when a fixed commission order receives its first fill.
* `TRADEFORGE_COMMISSION_PER_SHARE` and `TRADEFORGE_COMMISSION_MINIMUM` are reconciled across all fills for one order.
* `TRADEFORGE_SLIPPAGE_BPS` applies the default adverse fill adjustment.
* `TRADEFORGE_SYMBOL_SLIPPAGE_RULES_JSON` maps uppercase tickers to nonnegative basis point overrides.
* `TRADEFORGE_MAX_BAR_FILL_RATIO` must be between zero and one and limits aggregate fills against each bar.

Invalid, negative, nonfinite, or unsupported execution settings fail before a backtest starts.

## Suggested Future Topics

* environment-variables.md
* profile-model.md
* startup-validation.md
* secrets-handling.md
* sample-configurations.md

## Naming Conventions

* settings inventories use plural nouns
* secret docs use the `secrets` term explicitly
* examples live in a dedicated examples block inside each file

## File Examples

* `environment-variables.md`
* `startup-validation.md`
* `sample-configurations.md`

## Cross Links

* [security](../security/README.md)
* [installation](../installation/README.md)
