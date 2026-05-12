from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from tradeforge.database.models import PriceBar, Symbol


def load_bars(session: Session, ticker: str, start: datetime, end: datetime) -> list[PriceBar]:
    symbol = session.scalar(select(Symbol).where(Symbol.ticker == ticker.upper()))
    if symbol is None:
        return []
    return list(
        session.scalars(
            select(PriceBar)
            .where(PriceBar.symbol_id == symbol.id, PriceBar.timestamp >= start, PriceBar.timestamp <= end)
            .order_by(PriceBar.timestamp.asc())
        )
    )


def replay_bars(bars: Iterable[PriceBar]) -> Iterable[PriceBar]:
    yield from bars
