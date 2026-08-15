from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite, sqrt
from statistics import fmean, pstdev

from tradeforge.database.models import AccountSnapshot, Fill, Position, Trade

SECONDS_PER_YEAR = 365.25 * 24 * 60 * 60


def max_drawdown(equity_curve: list[float]) -> float:
    peak = None
    drawdown = 0.0
    for equity in equity_curve:
        peak = equity if peak is None else max(peak, equity)
        if peak:
            drawdown = min(drawdown, (equity - peak) / peak)
    return drawdown


def calculate_metrics(
    starting_cash: float,
    ending_equity: float,
    fills: list[Fill],
    trades: list[Trade],
    position: Position | None,
    snapshots: list[AccountSnapshot],
    first_price: float,
    last_price: float,
) -> dict[str, float | int | None]:
    realized = position.realized_pnl if position else 0.0
    unrealized = ((last_price - position.average_cost) * position.quantity) if position and position.quantity else 0.0
    closed_trades = [trade for trade in trades if trade.closed_at is not None]
    wins = [trade for trade in closed_trades if trade.realized_pnl > 0]
    losses = [trade for trade in closed_trades if trade.realized_pnl < 0]
    ordered_snapshots = sorted(snapshots, key=lambda snapshot: _utc_timestamp(snapshot.timestamp))
    returns = _periodic_returns(ordered_snapshots)
    periods_per_year, elapsed_years = _annualization(ordered_snapshots, len(returns))
    volatility = pstdev(returns) if len(returns) > 1 else 0.0
    downside_deviation = sqrt(fmean(min(value, 0.0) ** 2 for value in returns)) if returns else 0.0
    mean_return = fmean(returns) if returns else 0.0
    gross_profit = sum(trade.realized_pnl for trade in wins)
    gross_loss = abs(sum(trade.realized_pnl for trade in losses))
    total_return = (ending_equity - starting_cash) / starting_cash if starting_cash else 0.0
    cagr = _cagr(starting_cash, ending_equity, elapsed_years)
    sharpe_ratio = _risk_ratio(mean_return, volatility, periods_per_year)
    sortino_ratio = _risk_ratio(mean_return, downside_deviation, periods_per_year)
    return {
        "starting_cash": round(starting_cash, 2),
        "ending_equity": round(ending_equity, 2),
        "total_return": round(total_return, 6),
        "cagr": round(cagr, 6) if cagr is not None else None,
        "volatility": round(volatility * sqrt(periods_per_year), 6) if periods_per_year else 0.0,
        "sharpe_ratio": round(sharpe_ratio, 6) if sharpe_ratio is not None else None,
        "sortino_ratio": round(sortino_ratio, 6) if sortino_ratio is not None else None,
        "number_of_fills": len(fills),
        "number_of_trades": len(closed_trades),
        "open_trades": len(trades) - len(closed_trades),
        "win_rate": round(len(wins) / len(closed_trades), 6) if closed_trades else 0,
        "profit_factor": round(gross_profit / gross_loss, 6) if gross_loss else None,
        "average_win": round(gross_profit / len(wins), 2) if wins else 0.0,
        "average_loss": round(-gross_loss / len(losses), 2) if losses else 0.0,
        "exposure": round(
            sum(abs(snapshot.equity - snapshot.cash) > 1e-9 for snapshot in ordered_snapshots) / len(ordered_snapshots),
            6,
        )
        if ordered_snapshots
        else 0.0,
        "buy_and_hold_return": round((last_price - first_price) / first_price, 6) if first_price else 0.0,
        "max_drawdown": round(max_drawdown([starting_cash, *[snapshot.equity for snapshot in ordered_snapshots]]), 6),
        "realized_pnl": round(realized, 2),
        "unrealized_pnl": round(unrealized, 2),
    }


def _periodic_returns(snapshots: list[AccountSnapshot]) -> list[float]:
    returns: list[float] = []
    for previous, current in zip(snapshots, snapshots[1:], strict=False):
        if previous.equity:
            returns.append((current.equity - previous.equity) / previous.equity)
    return returns


def _annualization(snapshots: list[AccountSnapshot], return_periods: int) -> tuple[float, float]:
    if len(snapshots) < 2 or not return_periods:
        return 0.0, 0.0
    elapsed_seconds = (_utc_timestamp(snapshots[-1].timestamp) - _utc_timestamp(snapshots[0].timestamp)).total_seconds()
    if elapsed_seconds <= 0:
        return 0.0, 0.0
    elapsed_years = elapsed_seconds / SECONDS_PER_YEAR
    return return_periods / elapsed_years, elapsed_years


def _cagr(starting_cash: float, ending_equity: float, elapsed_years: float) -> float | None:
    if starting_cash <= 0 or ending_equity <= 0 or elapsed_years <= 0:
        return None
    try:
        result = (ending_equity / starting_cash) ** (1 / elapsed_years) - 1
    except OverflowError:
        return None
    return result if isfinite(result) else None


def _risk_ratio(mean_return: float, deviation: float, periods_per_year: float) -> float | None:
    if not periods_per_year or not mean_return:
        return 0.0
    if not deviation:
        return None
    return mean_return / deviation * sqrt(periods_per_year)


def _utc_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
