from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from tradeforge.database.models import AccountSnapshot, LiveQuote, Position
from tradeforge.market_data.live import serialize_quote


@dataclass(frozen=True)
class PositionValuation:
    symbol: str
    strategy_run_id: str | None
    quantity: float
    average_cost: float
    realized_pnl: float
    quote_provider: str | None
    quote_timestamp: str | None
    fetched_at: str | None
    age_seconds: int | None
    is_stale: bool
    mark_price: float | None
    market_value: float | None
    unrealized_pnl: float | None


def build_portfolio_valuation(session: Session, stale_after_seconds: int) -> dict[str, object]:
    positions = list(
        session.scalars(
            select(Position).options(selectinload(Position.symbol)).where(Position.quantity != 0).order_by(Position.updated_at.desc())
        )
    )
    quotes = list(session.scalars(select(LiveQuote).options(selectinload(LiveQuote.symbol))))
    quote_map = {quote.symbol_id: quote for quote in quotes}
    cash_by_run = _load_latest_cash_by_run(session, positions)

    position_payloads: list[dict[str, object]] = []
    total_market_value = 0.0
    total_unrealized = 0.0
    stale_count = 0

    for position in positions:
        quote = quote_map.get(position.symbol_id)
        serialized_quote = serialize_quote(quote, stale_after_seconds) if quote is not None else None
        mark_price = serialized_quote["mark_price"] if serialized_quote is not None else None
        market_value = None if mark_price is None else round(position.quantity * float(mark_price), 2)
        unrealized_pnl = None if mark_price is None else round((float(mark_price) - position.average_cost) * position.quantity, 2)
        if market_value is not None:
            total_market_value += market_value
        if unrealized_pnl is not None:
            total_unrealized += unrealized_pnl
        if serialized_quote is None or bool(serialized_quote["is_stale"]):
            stale_count += 1

        position_payloads.append(
            {
                "symbol": position.symbol.ticker,
                "strategy_run_id": position.strategy_run_id,
                "quantity": position.quantity,
                "average_cost": round(position.average_cost, 4),
                "realized_pnl": round(position.realized_pnl, 2),
                "quote_provider": None if serialized_quote is None else serialized_quote["provider"],
                "quote_timestamp": None if serialized_quote is None else serialized_quote["quote_timestamp"],
                "fetched_at": None if serialized_quote is None else serialized_quote["fetched_at"],
                "age_seconds": None if serialized_quote is None else serialized_quote["age_seconds"],
                "is_stale": serialized_quote is None or bool(serialized_quote["is_stale"]),
                "mark_price": mark_price,
                "market_value": market_value,
                "unrealized_pnl": unrealized_pnl,
            }
        )

    total_cash = round(sum(cash_by_run.values()), 2)
    return {
        "cash": total_cash,
        "market_value": round(total_market_value, 2),
        "total_equity": round(total_cash + total_market_value, 2),
        "unrealized_pnl": round(total_unrealized, 2),
        "positions_count": len(position_payloads),
        "stale_quotes": stale_count,
        "positions": position_payloads,
    }


def _load_latest_cash_by_run(session: Session, positions: Iterable[Position]) -> dict[str, float]:
    run_ids = sorted({position.strategy_run_id for position in positions if position.strategy_run_id})
    if not run_ids:
        return {}

    snapshots = list(
        session.scalars(
            select(AccountSnapshot)
            .where(AccountSnapshot.strategy_run_id.in_(run_ids))
            .order_by(AccountSnapshot.strategy_run_id.asc(), AccountSnapshot.timestamp.desc())
        )
    )
    cash_by_run: dict[str, float] = {}
    for snapshot in snapshots:
        if snapshot.strategy_run_id is None or snapshot.strategy_run_id in cash_by_run:
            continue
        cash_by_run[snapshot.strategy_run_id] = snapshot.cash
    return cash_by_run
