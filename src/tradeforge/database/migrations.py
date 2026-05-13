from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import Engine

from tradeforge.config import get_settings
from tradeforge.database.session import get_engine


@dataclass(frozen=True)
class MigrationStep:
    version: int
    name: str
    statements: tuple[str, ...]


MIGRATIONS: tuple[MigrationStep, ...] = (
    MigrationStep(
        version=1,
        name="initial_schema",
        statements=(
            """
            CREATE TABLE symbols (
                id TEXT PRIMARY KEY,
                ticker TEXT NOT NULL UNIQUE,
                name TEXT,
                created_at DATETIME NOT NULL
            )
            """,
            "CREATE INDEX ix_symbols_ticker ON symbols (ticker)",
            """
            CREATE TABLE price_bars (
                id TEXT PRIMARY KEY,
                symbol_id TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                open FLOAT NOT NULL,
                high FLOAT NOT NULL,
                low FLOAT NOT NULL,
                close FLOAT NOT NULL,
                volume INTEGER NOT NULL,
                created_at DATETIME NOT NULL,
                CONSTRAINT uq_price_bar_symbol_timestamp UNIQUE (symbol_id, timestamp),
                FOREIGN KEY(symbol_id) REFERENCES symbols (id)
            )
            """,
            "CREATE INDEX ix_price_bars_symbol_id ON price_bars (symbol_id)",
            "CREATE INDEX ix_price_bars_timestamp ON price_bars (timestamp)",
            "CREATE INDEX ix_price_bars_symbol_timestamp ON price_bars (symbol_id, timestamp)",
            """
            CREATE TABLE strategies (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at DATETIME NOT NULL
            )
            """,
            "CREATE INDEX ix_strategies_name ON strategies (name)",
            """
            CREATE TABLE strategy_runs (
                id TEXT PRIMARY KEY,
                strategy_id TEXT NOT NULL,
                symbol_id TEXT NOT NULL,
                started_at DATETIME NOT NULL,
                completed_at DATETIME,
                start_date DATETIME NOT NULL,
                end_date DATETIME NOT NULL,
                parameters_json TEXT NOT NULL,
                metrics_json TEXT,
                FOREIGN KEY(strategy_id) REFERENCES strategies (id),
                FOREIGN KEY(symbol_id) REFERENCES symbols (id)
            )
            """,
            "CREATE INDEX ix_strategy_runs_strategy_id ON strategy_runs (strategy_id)",
            "CREATE INDEX ix_strategy_runs_symbol_id ON strategy_runs (symbol_id)",
            "CREATE INDEX ix_strategy_runs_start_date ON strategy_runs (start_date)",
            "CREATE INDEX ix_strategy_runs_end_date ON strategy_runs (end_date)",
            "CREATE INDEX ix_strategy_runs_strategy_symbol ON strategy_runs (strategy_id, symbol_id)",
            """
            CREATE TABLE orders (
                id TEXT PRIMARY KEY,
                strategy_run_id TEXT,
                symbol_id TEXT NOT NULL,
                side TEXT NOT NULL,
                order_type TEXT NOT NULL,
                quantity FLOAT NOT NULL,
                limit_price FLOAT,
                status TEXT NOT NULL,
                submitted_at DATETIME NOT NULL,
                filled_at DATETIME,
                created_at DATETIME NOT NULL,
                FOREIGN KEY(strategy_run_id) REFERENCES strategy_runs (id),
                FOREIGN KEY(symbol_id) REFERENCES symbols (id)
            )
            """,
            "CREATE INDEX ix_orders_strategy_run_id ON orders (strategy_run_id)",
            "CREATE INDEX ix_orders_symbol_id ON orders (symbol_id)",
            "CREATE INDEX ix_orders_status ON orders (status)",
            "CREATE INDEX ix_orders_submitted_at ON orders (submitted_at)",
            "CREATE INDEX ix_orders_run_status ON orders (strategy_run_id, status)",
            "CREATE INDEX ix_orders_symbol_status ON orders (symbol_id, status)",
            """
            CREATE TABLE fills (
                id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                strategy_run_id TEXT,
                symbol_id TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                side TEXT NOT NULL,
                quantity FLOAT NOT NULL,
                price FLOAT NOT NULL,
                fee FLOAT NOT NULL,
                slippage FLOAT NOT NULL,
                FOREIGN KEY(order_id) REFERENCES orders (id),
                FOREIGN KEY(strategy_run_id) REFERENCES strategy_runs (id),
                FOREIGN KEY(symbol_id) REFERENCES symbols (id)
            )
            """,
            "CREATE INDEX ix_fills_order_id ON fills (order_id)",
            "CREATE INDEX ix_fills_strategy_run_id ON fills (strategy_run_id)",
            "CREATE INDEX ix_fills_symbol_id ON fills (symbol_id)",
            "CREATE INDEX ix_fills_timestamp ON fills (timestamp)",
            "CREATE INDEX ix_fills_order_timestamp ON fills (order_id, timestamp)",
            """
            CREATE TABLE positions (
                id TEXT PRIMARY KEY,
                strategy_run_id TEXT,
                symbol_id TEXT NOT NULL,
                quantity FLOAT NOT NULL,
                average_cost FLOAT NOT NULL,
                realized_pnl FLOAT NOT NULL,
                updated_at DATETIME NOT NULL,
                CONSTRAINT uq_position_run_symbol UNIQUE (strategy_run_id, symbol_id),
                FOREIGN KEY(strategy_run_id) REFERENCES strategy_runs (id),
                FOREIGN KEY(symbol_id) REFERENCES symbols (id)
            )
            """,
            "CREATE INDEX ix_positions_strategy_run_id ON positions (strategy_run_id)",
            "CREATE INDEX ix_positions_symbol_id ON positions (symbol_id)",
            "CREATE INDEX ix_positions_run_symbol ON positions (strategy_run_id, symbol_id)",
            """
            CREATE TABLE trades (
                id TEXT PRIMARY KEY,
                strategy_run_id TEXT,
                symbol_id TEXT NOT NULL,
                opened_at DATETIME NOT NULL,
                closed_at DATETIME,
                quantity FLOAT NOT NULL,
                entry_price FLOAT NOT NULL,
                exit_price FLOAT,
                realized_pnl FLOAT NOT NULL,
                FOREIGN KEY(strategy_run_id) REFERENCES strategy_runs (id),
                FOREIGN KEY(symbol_id) REFERENCES symbols (id)
            )
            """,
            "CREATE INDEX ix_trades_strategy_run_id ON trades (strategy_run_id)",
            "CREATE INDEX ix_trades_symbol_id ON trades (symbol_id)",
            "CREATE INDEX ix_trades_opened_at ON trades (opened_at)",
            "CREATE INDEX ix_trades_closed_at ON trades (closed_at)",
            "CREATE INDEX ix_trades_run_symbol ON trades (strategy_run_id, symbol_id)",
            """
            CREATE TABLE account_snapshots (
                id TEXT PRIMARY KEY,
                strategy_run_id TEXT,
                timestamp DATETIME NOT NULL,
                cash FLOAT NOT NULL,
                equity FLOAT NOT NULL,
                realized_pnl FLOAT NOT NULL,
                unrealized_pnl FLOAT NOT NULL,
                FOREIGN KEY(strategy_run_id) REFERENCES strategy_runs (id)
            )
            """,
            "CREATE INDEX ix_account_snapshots_strategy_run_id ON account_snapshots (strategy_run_id)",
            "CREATE INDEX ix_account_snapshots_timestamp ON account_snapshots (timestamp)",
            "CREATE INDEX ix_account_snapshots_run_timestamp ON account_snapshots (strategy_run_id, timestamp)",
        ),
    ),
    MigrationStep(
        version=2,
        name="live_quotes",
        statements=(
            """
            CREATE TABLE live_quotes (
                id TEXT PRIMARY KEY,
                symbol_id TEXT NOT NULL,
                provider TEXT NOT NULL,
                quote_timestamp DATETIME NOT NULL,
                last_price FLOAT,
                bid_price FLOAT,
                ask_price FLOAT,
                bid_size INTEGER,
                ask_size INTEGER,
                previous_close FLOAT,
                currency TEXT,
                fetched_at DATETIME NOT NULL,
                raw_payload_json TEXT NOT NULL,
                CONSTRAINT uq_live_quotes_symbol_provider UNIQUE (symbol_id, provider),
                FOREIGN KEY(symbol_id) REFERENCES symbols (id)
            )
            """,
            "CREATE INDEX ix_live_quotes_symbol_id ON live_quotes (symbol_id)",
            "CREATE INDEX ix_live_quotes_provider ON live_quotes (provider)",
            "CREATE INDEX ix_live_quotes_quote_timestamp ON live_quotes (quote_timestamp)",
            "CREATE INDEX ix_live_quotes_fetched_at ON live_quotes (fetched_at)",
            "CREATE INDEX ix_live_quotes_symbol_provider ON live_quotes (symbol_id, provider)",
        ),
    ),
)


def init_db(engine: Engine | None = None) -> None:
    settings = get_settings()
    target_engine = engine or get_engine()
    if engine is None and settings.database_path is not None:
        Path(settings.database_path).parent.mkdir(parents=True, exist_ok=True)
    with target_engine.begin() as connection:
        if connection.dialect.name != "sqlite":
            raise ValueError("TradeForge migrations currently support SQLite databases only")
        _ensure_migration_table(connection)
        applied_versions = _get_applied_versions(connection)
        for migration in MIGRATIONS:
            if migration.version in applied_versions:
                continue
            for statement in migration.statements:
                connection.exec_driver_sql(statement)
            connection.exec_driver_sql(
                "INSERT INTO schema_migrations (version, name) VALUES (?, ?)",
                (migration.version, migration.name),
            )


def get_current_version(engine: Engine | None = None) -> int:
    target_engine = engine or get_engine()
    with target_engine.begin() as connection:
        if connection.dialect.name != "sqlite":
            raise ValueError("TradeForge migrations currently support SQLite databases only")
        _ensure_migration_table(connection)
        result = connection.exec_driver_sql("SELECT MAX(version) FROM schema_migrations").scalar_one()
        return int(result or 0)


def _ensure_migration_table(connection) -> None:
    connection.exec_driver_sql(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def _get_applied_versions(connection) -> set[int]:
    rows = connection.exec_driver_sql("SELECT version FROM schema_migrations").all()
    return {int(row[0]) for row in rows}
