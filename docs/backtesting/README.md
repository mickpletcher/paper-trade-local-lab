# Backtesting

## Purpose

This section documents historical bar backtesting, simulation assumptions, reports, and result analysis.

## Intended Contents

* backtest engine behavior
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
8. Strategy context includes actual position quantity and remaining open buy and sell quantities.
9. A reversal cancels open opposite side orders even when current inventory does not permit a replacement order.
10. Quantities use a configurable increment that defaults to one whole share. Cash limited fills round down to that increment.
11. Trade entry and exit prices are gross weighted execution prices. Entry and exit fees are stored separately, and realized profit and loss subtracts both.
12. Risk policy rejects orders or cumulative partial fills beyond order notional, position quantity, gross exposure, maximum drawdown, or the global kill switch.
13. Corporate actions apply once in effective timestamp order. Splits adjust position and pending order quantities and prices. Dividends credit cash. Symbol changes update the ticker. Delistings close the trade, realize profit and loss, cancel orders, deactivate the symbol, and stop later strategy execution.
14. Audit rows persist triggers, cancellations, rejections, remaining quantities, and applied corporate actions.

`BacktestEngine` queries stored `price_bars` in timestamp order and processes them directly. There is no separate replay module or public replay API. Reports include total return, CAGR, annualized volatility, zero risk free Sharpe and Sortino ratios, drawdown, trade counts, win rate, profit factor, average wins and losses, time exposure, and the same period buy and hold return. Profit factor without a losing trade, risk ratios with a nonzero return and zero denominator, and CAGR that cannot be represented are reported as `None` instead of a misleading zero.

## Portfolio, Analytics, And Experiments

`run-portfolio-backtest` allocates fixed or equal capital to one independent single symbol backtest per sleeve, then aggregates ending equity and return. Sleeve records commit in one transaction. A failed sleeve rolls back all strategy runs, experiments, artifacts, and generated reports. It is not a shared cash account.

Every completed run records an experiment with strategy version, parameters, ordered dataset SHA-256, and report SHA-256. Dataset JSON and artifact files are hashed incrementally to keep memory bounded. `show-experiments` exposes provenance metadata without report contents.

`analyze-symbol` reports rolling annualized volatility, beta, factor betas, and simple market regimes. Asset and benchmark bars are inner joined by timestamp before beta calculation. The vectorized moving average signal path and multiprocessing analytics are research accelerators only. They do not bypass broker accounting. The performance gate runs 100,000 rows and independent analytics tasks.

The event runtime orders timezone aware bar, tick, news, and system events by timestamp and then publication sequence. Portfolio lifecycle messages use it now. It is not yet a live streaming loop.

## Cross Links

* [strategies](../strategies/README.md)
* [market-data](../market-data/README.md)
