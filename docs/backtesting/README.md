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

`BacktestEngine` queries stored `price_bars` in timestamp order and processes them directly. There is no separate replay module or public replay API. Reports include total return, CAGR, annualized volatility, zero risk free Sharpe and Sortino ratios, drawdown, trade counts, win rate, profit factor, average wins and losses, time exposure, and the same period buy and hold return. Profit factor without a losing trade, risk ratios with a nonzero return and zero denominator, and CAGR that cannot be represented are reported as `None` instead of a misleading zero.

## Cross Links

* [strategies](../strategies/README.md)
* [market-data](../market-data/README.md)
