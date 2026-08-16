from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from tradeforge.database.models import AccountSnapshot, LiveQuote, Position, StrategyRun
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


def build_portfolio_valuation(
    session: Session,
    stale_after_seconds: int,
    strategy_run_id: str | None = None,
    tenant_id: str | None = None,
) -> dict[str, object]:
    selected_run_id = _resolve_strategy_run_id(session, strategy_run_id, tenant_id)
    positions = (
        list(
            session.scalars(
                select(Position)
                .options(selectinload(Position.symbol))
                .where(Position.strategy_run_id == selected_run_id, Position.quantity != 0)
                .order_by(Position.updated_at.desc())
            )
        )
        if selected_run_id is not None
        else []
    )
    quotes = list(
        session.scalars(
            select(LiveQuote)
            .options(selectinload(LiveQuote.symbol))
            .order_by(LiveQuote.symbol_id.asc(), LiveQuote.fetched_at.desc(), LiveQuote.id.desc())
        )
    )
    quote_map: dict[str, LiveQuote] = {}
    for quote in quotes:
        quote_map.setdefault(quote.symbol_id, quote)
    cash = _load_latest_cash(session, selected_run_id)

    position_payloads: list[dict[str, object]] = []
    total_market_value = 0.0
    total_unrealized = 0.0
    stale_count = 0

    for position in positions:
        position_quote = quote_map.get(position.symbol_id)
        serialized_quote = serialize_quote(position_quote, stale_after_seconds) if position_quote is not None else None
        mark_price = cast(float | None, serialized_quote["mark_price"]) if serialized_quote is not None else None
        market_value = None if mark_price is None else round(position.quantity * mark_price, 2)
        unrealized_pnl = (
            None if mark_price is None else round((mark_price - position.average_cost) * position.quantity, 2)
        )
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

    total_cash = round(cash, 2)
    return {
        "strategy_run_id": selected_run_id,
        "cash": total_cash,
        "market_value": round(total_market_value, 2),
        "total_equity": round(total_cash + total_market_value, 2),
        "unrealized_pnl": round(total_unrealized, 2),
        "positions_count": len(position_payloads),
        "stale_quotes": stale_count,
        "positions": position_payloads,
    }


def _resolve_strategy_run_id(
    session: Session,
    requested_run_id: str | None,
    tenant_id: str | None,
) -> str | None:
    if requested_run_id is not None:
        statement = select(StrategyRun.id).where(StrategyRun.id == requested_run_id)
        if tenant_id is not None:
            statement = statement.where(StrategyRun.tenant_id == tenant_id)
        if session.scalar(statement) is None:
            raise ValueError(f"Unknown strategy run: {requested_run_id}")
        return requested_run_id
    statement = select(StrategyRun.id)
    if tenant_id is not None:
        statement = statement.where(StrategyRun.tenant_id == tenant_id)
    return session.scalar(statement.order_by(StrategyRun.started_at.desc(), StrategyRun.id.desc()).limit(1))


def _load_latest_cash(session: Session, strategy_run_id: str | None) -> float:
    if strategy_run_id is None:
        return 0.0
    snapshot = session.scalar(
        select(AccountSnapshot)
        .where(AccountSnapshot.strategy_run_id == strategy_run_id)
        .order_by(AccountSnapshot.timestamp.desc(), AccountSnapshot.id.desc())
        .limit(1)
    )
    return 0.0 if snapshot is None else snapshot.cash
