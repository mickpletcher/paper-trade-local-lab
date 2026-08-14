# Backtesting

## Purpose

This section documents replay logic, simulation assumptions, reports, and result analysis.

## Intended Contents

* backtest engine behavior
* replay workflow
* result metrics
* report artifacts
* realism limitations

## Current Execution Rules

1. Strategy signals are submitted after the current bar is processed and cannot fill against an earlier bar.
2. The configured volume ratio creates one aggregate liquidity budget for all eligible orders on a bar.
3. A stop remains triggered after a partial fill. Its remaining quantity behaves as a market order on later bars.
4. Buy limits never fill above their limit and sell limits never fill below their limit.
5. Marketable limits use the bar open when it improves the requested limit.
6. Fixed commissions and per share minimums are reconciled once per order across partial fills.
7. One trade row represents one position lifecycle from the first entry until the position returns to zero.

Backtest metrics report fills, completed trades, and open trades separately.

## Suggested Future Topics

* engine-overview.md
* market-replay-workflow.md
* metrics-reference.md
* report-format.md
* simulation-limitations.md

## Naming Conventions

* references use `reference`
* workflows use `workflow`
* limitations use `limitations`

## File Examples

* `engine-overview.md`
* `metrics-reference.md`
* `market-replay-workflow.md`

## Cross Links

* [strategies](../strategies/README.md)
* [market-data](../market-data/README.md)
