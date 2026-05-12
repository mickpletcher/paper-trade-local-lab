from __future__ import annotations

from sqlalchemy import inspect, select

from tradeforge.database.migrations import get_current_version
from tradeforge.database.models import Symbol
from tradeforge.market_data.importer import import_ohlcv_csv


def test_database_initialization_creates_tables(engine) -> None:
    tables = set(inspect(engine).get_table_names())
    assert {"schema_migrations", "symbols", "price_bars", "orders", "fills", "positions", "trades", "strategy_runs"}.issubset(tables)
    assert get_current_version(engine) == 1


def test_csv_import_upserts_bars(session, tmp_path) -> None:
    csv_path = tmp_path / "aapl.csv"
    csv_path.write_text(
        "date,open,high,low,close,volume\n"
        "2023-01-01,100,110,99,105,1000\n"
        "2023-01-02,106,112,101,108,1200\n",
        encoding="utf-8",
    )
    assert import_ohlcv_csv(session, "AAPL", csv_path) == 2
    assert import_ohlcv_csv(session, "AAPL", csv_path) == 2
    symbol = session.scalar(select(Symbol).where(Symbol.ticker == "AAPL"))
    assert symbol is not None
    assert len(symbol.price_bars) == 2
