from __future__ import annotations

import pytest
from sqlalchemy import inspect, select, text

from tradeforge.database.migrations import get_current_version, get_head_version
from tradeforge.database.models import Symbol
from tradeforge.market_data.importer import import_ohlcv_csv


def test_database_initialization_creates_tables(engine) -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    assert {
        "alembic_version",
        "symbols",
        "price_bars",
        "orders",
        "fills",
        "positions",
        "trades",
        "strategy_runs",
        "live_quotes",
    }.issubset(tables)
    order_columns = {column["name"] for column in inspector.get_columns("orders")}
    assert {"stop_price", "filled_quantity", "commission_paid", "triggered_at"}.issubset(order_columns)
    assert get_current_version(engine) == "003_execution_realism"
    assert get_head_version() == "003_execution_realism"


def test_sqlite_foreign_keys_are_enabled(engine) -> None:
    with engine.connect() as connection:
        assert connection.scalar(text("PRAGMA foreign_keys")) == 1


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


@pytest.mark.parametrize(
    "row",
    [
        "2023-01-01,-1,110,99,105,1000",
        "2023-01-01,100,98,99,105,1000",
        "2023-01-01,100,110,101,99,1000",
        "2023-01-01,100,110,99,105,-1",
        "2023-01-01,100,110,99,105,1.5",
    ],
)
def test_csv_import_rejects_invalid_ohlcv_rows(session, tmp_path, row) -> None:
    csv_path = tmp_path / "invalid.csv"
    csv_path.write_text(f"date,open,high,low,close,volume\n{row}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="CSV row 2"):
        import_ohlcv_csv(session, "AAPL", csv_path)
