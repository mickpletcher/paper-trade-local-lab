from __future__ import annotations

from tradeforge.database.models import AccountSnapshot, Fill, Position, Trade


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
    last_price: float,
) -> dict[str, float | int]:
    realized = position.realized_pnl if position else 0.0
    unrealized = ((last_price - position.average_cost) * position.quantity) if position and position.quantity else 0.0
    closed_trades = [trade for trade in trades if trade.closed_at is not None]
    wins = [trade for trade in closed_trades if trade.realized_pnl > 0]
    return {
        "starting_cash": round(starting_cash, 2),
        "ending_equity": round(ending_equity, 2),
        "total_return": round((ending_equity - starting_cash) / starting_cash, 6) if starting_cash else 0,
        "number_of_fills": len(fills),
        "number_of_trades": len(closed_trades),
        "open_trades": len(trades) - len(closed_trades),
        "win_rate": round(len(wins) / len(closed_trades), 6) if closed_trades else 0,
        "max_drawdown": round(max_drawdown([snapshot.equity for snapshot in snapshots]), 6),
        "realized_pnl": round(realized, 2),
        "unrealized_pnl": round(unrealized, 2),
    }
