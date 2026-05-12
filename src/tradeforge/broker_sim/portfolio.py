from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from tradeforge.database.models import OrderSide, Position


@dataclass
class PositionUpdate:
    realized_pnl_delta: float
    closed_quantity: float


def get_or_create_position(session: Session, symbol_id: str, strategy_run_id: str | None = None) -> Position:
    position = session.scalar(
        select(Position).where(Position.symbol_id == symbol_id, Position.strategy_run_id == strategy_run_id)
    )
    if position is not None:
        return position
    position = Position(symbol_id=symbol_id, strategy_run_id=strategy_run_id)
    session.add(position)
    session.flush()
    return position


def apply_fill_to_position(position: Position, side: OrderSide, quantity: float, price: float, fee: float = 0.0) -> PositionUpdate:
    realized = -fee
    closed_quantity = 0.0

    if side is OrderSide.BUY:
        total_cost = position.average_cost * position.quantity + price * quantity + fee
        position.quantity += quantity
        position.average_cost = total_cost / position.quantity if position.quantity else 0.0
    else:
        sell_quantity = min(quantity, position.quantity)
        closed_quantity = sell_quantity
        realized += (price - position.average_cost) * sell_quantity
        position.quantity -= sell_quantity
        if position.quantity <= 0:
            position.quantity = 0.0
            position.average_cost = 0.0

    position.realized_pnl += realized
    return PositionUpdate(realized_pnl_delta=realized, closed_quantity=closed_quantity)
