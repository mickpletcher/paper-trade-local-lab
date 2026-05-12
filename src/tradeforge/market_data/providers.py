from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from tradeforge.database.models import Symbol


def get_or_create_symbol(session: Session, ticker: str, name: str | None = None) -> Symbol:
    normalized = ticker.upper().strip()
    symbol = session.scalar(select(Symbol).where(Symbol.ticker == normalized))
    if symbol is not None:
        return symbol
    symbol = Symbol(ticker=normalized, name=name)
    session.add(symbol)
    session.flush()
    return symbol
