from __future__ import annotations

import argparse
import sqlite3
import tempfile
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic

from alembic import command

from tradeforge.database.migrations import _build_alembic_config


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=25_000)
    parser.add_argument("--max-seconds", type=float, default=20.0)
    args = parser.parse_args()
    if args.rows < 1 or args.max_seconds <= 0:
        parser.error("rows and max-seconds must be positive")

    with tempfile.TemporaryDirectory(prefix="tradeforge-migration-") as temp_dir:
        database = Path(temp_dir) / "performance.db"
        database_url = f"sqlite:///{database.as_posix()}"
        config = _build_alembic_config(database_url)
        command.upgrade(config, "003_execution_realism")
        seed_database(database, args.rows)
        started = monotonic()
        command.upgrade(config, "head")
        elapsed = monotonic() - started
    print(f"Migrated {args.rows} fills and trades in {elapsed:.3f} seconds")
    return 1 if elapsed > args.max_seconds else 0


def seed_database(database: Path, rows: int) -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    with closing(sqlite3.connect(database)) as connection:
        connection.execute(
            "INSERT INTO symbols (id, ticker, created_at) VALUES (?, ?, ?)",
            ("symbol", "SYNTH", timestamp),
        )
        batch_size = 1_000
        for start in range(0, rows, batch_size):
            stop = min(start + batch_size, rows)
            orders = []
            fills = []
            trades = []
            for index in range(start, stop):
                order_id = f"order-{index}"
                orders.append((order_id, "symbol", "buy", "market", 1, "filled", timestamp, timestamp))
                fills.append((f"fill-{index}", order_id, "symbol", timestamp, "buy", 1, 100, 0, 0))
                trades.append((f"trade-{index}", "symbol", timestamp, timestamp, 1, 100, 100, 0))
            connection.executemany(
                "INSERT INTO orders (id, symbol_id, side, order_type, quantity, status, submitted_at, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                orders,
            )
            connection.executemany(
                "INSERT INTO fills (id, order_id, symbol_id, timestamp, side, quantity, price, fee, slippage) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                fills,
            )
            connection.executemany(
                "INSERT INTO trades (id, symbol_id, opened_at, closed_at, quantity, entry_price, exit_price, "
                "realized_pnl) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                trades,
            )
        connection.commit()


if __name__ == "__main__":
    raise SystemExit(main())
