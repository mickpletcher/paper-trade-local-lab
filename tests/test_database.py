from __future__ import annotations

import pytest
from alembic import command
from sqlalchemy import inspect, select, text

from tradeforge.database.migrations import _build_alembic_config, get_current_version, get_head_version
from tradeforge.database.models import Symbol
from tradeforge.database.session import dispose_application_engine, get_application_engine, get_engine
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
    trade_columns = {column["name"] for column in inspector.get_columns("trades")}
    assert {"stop_price", "filled_quantity", "commission_paid", "triggered_at"}.issubset(order_columns)
    assert {"entry_fee", "exit_fee"}.issubset(trade_columns)
    assert get_current_version(engine) == "004_trade_fee_basis"
    assert get_head_version() == "004_trade_fee_basis"


def test_sqlite_foreign_keys_are_enabled(engine) -> None:
    with engine.connect() as connection:
        assert connection.scalar(text("PRAGMA foreign_keys")) == 1


def test_application_engine_is_cached_and_explicit_engines_are_isolated(monkeypatch, tmp_path) -> None:
    dispose_application_engine()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TRADEFORGE_DATABASE_URL", "sqlite:///data/tradeforge.db")
    first_explicit = get_engine("sqlite:///:memory:")
    second_explicit = get_engine("sqlite:///:memory:")
    try:
        first_application = get_application_engine()
        assert get_application_engine() is first_application
        assert first_explicit is not second_explicit

        dispose_application_engine()

        assert get_application_engine() is not first_application
    finally:
        first_explicit.dispose()
        second_explicit.dispose()
        dispose_application_engine()


def test_trade_fee_migration_separates_legacy_entry_basis(tmp_path) -> None:
    database_url = f"sqlite:///{(tmp_path / 'legacy.db').as_posix()}"
    legacy_engine = get_engine(database_url)
    config = _build_alembic_config(database_url)
    command.upgrade(config, "003_execution_realism")
    with legacy_engine.begin() as connection:
        connection.execute(
            text("INSERT INTO symbols (id, ticker, created_at) VALUES ('symbol', 'AAPL', '2026-08-14 09:00:00')")
        )
        for order_id, side, timestamp in (
            ("buy-order", "buy", "2026-08-14 10:00:00"),
            ("sell-order", "sell", "2026-08-14 11:00:00"),
        ):
            connection.execute(
                text(
                    "INSERT INTO orders "
                    "(id, symbol_id, side, order_type, quantity, status, submitted_at, created_at) "
                    "VALUES (:id, 'symbol', :side, 'market', 4, 'filled', :timestamp, :timestamp)"
                ),
                {"id": order_id, "side": side, "timestamp": timestamp},
            )
        connection.execute(
            text(
                "INSERT INTO fills "
                "(id, order_id, symbol_id, timestamp, side, quantity, price, fee, slippage) VALUES "
                "('buy-fill', 'buy-order', 'symbol', '2026-08-14 10:00:00', 'buy', 4, 100, 1, 0), "
                "('sell-fill', 'sell-order', 'symbol', '2026-08-14 11:00:00', 'sell', 4, 110, 1, 0)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO trades "
                "(id, symbol_id, opened_at, closed_at, quantity, entry_price, exit_price, realized_pnl) "
                "VALUES ('trade', 'symbol', '2026-08-14 10:00:00', '2026-08-14 11:00:00', 4, 100.25, 110, 38)"
            )
        )

    command.upgrade(config, "head")

    with legacy_engine.connect() as connection:
        migrated = (
            connection.execute(text("SELECT entry_price, entry_fee, exit_price, exit_fee, realized_pnl FROM trades"))
            .mappings()
            .one()
        )
    legacy_engine.dispose()
    assert migrated == {
        "entry_price": 100,
        "entry_fee": 1,
        "exit_price": 110,
        "exit_fee": 1,
        "realized_pnl": 38,
    }


def test_trade_fee_migration_separates_shared_boundary_fills(tmp_path) -> None:
    database_url = f"sqlite:///{(tmp_path / 'shared-boundary.db').as_posix()}"
    legacy_engine = get_engine(database_url)
    config = _build_alembic_config(database_url)
    command.upgrade(config, "003_execution_realism")
    with legacy_engine.begin() as connection:
        connection.execute(
            text("INSERT INTO symbols (id, ticker, created_at) VALUES ('symbol', 'AAPL', '2026-08-14 09:00:00')")
        )
        connection.execute(
            text(
                "INSERT INTO orders "
                "(id, symbol_id, side, order_type, quantity, status, submitted_at, created_at) VALUES "
                "('buy-one', 'symbol', 'buy', 'market', 4, 'filled', '2026-08-14 10:00:00', "
                "'2026-08-14 10:00:00'), "
                "('sell-one', 'symbol', 'sell', 'market', 4, 'filled', '2026-08-14 11:00:00', "
                "'2026-08-14 11:00:00'), "
                "('buy-two', 'symbol', 'buy', 'market', 4, 'filled', '2026-08-14 11:00:00', "
                "'2026-08-14 11:00:01'), "
                "('sell-two', 'symbol', 'sell', 'market', 4, 'filled', '2026-08-14 12:00:00', "
                "'2026-08-14 12:00:00')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO fills "
                "(id, order_id, symbol_id, timestamp, side, quantity, price, fee, slippage) VALUES "
                "('buy-fill-one', 'buy-one', 'symbol', '2026-08-14 10:00:00', 'buy', 4, 100, 1, 0), "
                "('sell-fill-one', 'sell-one', 'symbol', '2026-08-14 11:00:00', 'sell', 4, 110, 2, 0), "
                "('buy-fill-two', 'buy-two', 'symbol', '2026-08-14 11:00:00', 'buy', 4, 120, 3, 0), "
                "('sell-fill-two', 'sell-two', 'symbol', '2026-08-14 12:00:00', 'sell', 4, 130, 4, 0)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO trades "
                "(id, symbol_id, opened_at, closed_at, quantity, entry_price, exit_price, realized_pnl) VALUES "
                "('trade-one', 'symbol', '2026-08-14 10:00:00', '2026-08-14 11:00:00', 4, 100.25, 110, 37), "
                "('trade-two', 'symbol', '2026-08-14 11:00:00', '2026-08-14 12:00:00', 4, 120.75, 130, 33)"
            )
        )

    command.upgrade(config, "head")

    with legacy_engine.connect() as connection:
        migrated = (
            connection.execute(text("SELECT id, entry_price, entry_fee, exit_fee FROM trades ORDER BY opened_at"))
            .mappings()
            .all()
        )
    legacy_engine.dispose()
    assert migrated == [
        {"id": "trade-one", "entry_price": 100, "entry_fee": 1, "exit_fee": 2},
        {"id": "trade-two", "entry_price": 120, "entry_fee": 3, "exit_fee": 4},
    ]


def test_csv_import_upserts_bars(session, tmp_path) -> None:
    csv_path = tmp_path / "aapl.csv"
    csv_path.write_text(
        "date,open,high,low,close,volume\n2023-01-01,100,110,99,105,1000\n2023-01-02,106,112,101,108,1200\n",
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
