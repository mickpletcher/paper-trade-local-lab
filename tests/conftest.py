from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timezone

import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from tradeforge.database.migrations import init_db
from tradeforge.database.models import PriceBar, Symbol


@pytest.fixture()
def engine() -> Engine:
    engine = create_engine("sqlite:///:memory:", future=True)
    init_db(engine)
    return engine


@pytest.fixture()
def session(engine: Engine) -> Iterator[Session]:
    maker = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    with maker() as session:
        yield session


@pytest.fixture()
def symbol(session: Session) -> Symbol:
    item = Symbol(ticker="AAPL")
    session.add(item)
    session.flush()
    return item


def add_bar(session: Session, symbol: Symbol, day: int, open_: float, high: float, low: float, close: float) -> PriceBar:
    bar = PriceBar(
        symbol_id=symbol.id,
        timestamp=datetime(2023, 1, day, tzinfo=timezone.utc),
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=1000,
    )
    session.add(bar)
    session.flush()
    return bar
