from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "001_core_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "symbols",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("ticker", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticker"),
    )
    op.create_index("ix_symbols_ticker", "symbols", ["ticker"], unique=False)

    op.create_table(
        "price_bars",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("symbol_id", sa.String(length=36), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Float(), nullable=False),
        sa.Column("high", sa.Float(), nullable=False),
        sa.Column("low", sa.Float(), nullable=False),
        sa.Column("close", sa.Float(), nullable=False),
        sa.Column("volume", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["symbol_id"], ["symbols.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("symbol_id", "timestamp", name="uq_price_bar_symbol_timestamp"),
    )
    op.create_index("ix_price_bars_symbol_id", "price_bars", ["symbol_id"], unique=False)
    op.create_index("ix_price_bars_symbol_timestamp", "price_bars", ["symbol_id", "timestamp"], unique=False)
    op.create_index("ix_price_bars_timestamp", "price_bars", ["timestamp"], unique=False)

    op.create_table(
        "strategies",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_strategies_name", "strategies", ["name"], unique=False)

    op.create_table(
        "strategy_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("strategy_id", sa.String(length=36), nullable=False),
        sa.Column("symbol_id", sa.String(length=36), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("parameters_json", sa.Text(), nullable=False),
        sa.Column("metrics_json", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"]),
        sa.ForeignKeyConstraint(["symbol_id"], ["symbols.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_strategy_runs_end_date", "strategy_runs", ["end_date"], unique=False)
    op.create_index("ix_strategy_runs_start_date", "strategy_runs", ["start_date"], unique=False)
    op.create_index("ix_strategy_runs_strategy_id", "strategy_runs", ["strategy_id"], unique=False)
    op.create_index("ix_strategy_runs_strategy_symbol", "strategy_runs", ["strategy_id", "symbol_id"], unique=False)
    op.create_index("ix_strategy_runs_symbol_id", "strategy_runs", ["symbol_id"], unique=False)

    op.create_table(
        "orders",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("strategy_run_id", sa.String(length=36), nullable=True),
        sa.Column("symbol_id", sa.String(length=36), nullable=False),
        sa.Column("side", sa.String(length=8), nullable=False),
        sa.Column("order_type", sa.String(length=16), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("limit_price", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("filled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["strategy_run_id"], ["strategy_runs.id"]),
        sa.ForeignKeyConstraint(["symbol_id"], ["symbols.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_orders_run_status", "orders", ["strategy_run_id", "status"], unique=False)
    op.create_index("ix_orders_status", "orders", ["status"], unique=False)
    op.create_index("ix_orders_strategy_run_id", "orders", ["strategy_run_id"], unique=False)
    op.create_index("ix_orders_submitted_at", "orders", ["submitted_at"], unique=False)
    op.create_index("ix_orders_symbol_id", "orders", ["symbol_id"], unique=False)
    op.create_index("ix_orders_symbol_status", "orders", ["symbol_id", "status"], unique=False)

    op.create_table(
        "fills",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("order_id", sa.String(length=36), nullable=False),
        sa.Column("strategy_run_id", sa.String(length=36), nullable=True),
        sa.Column("symbol_id", sa.String(length=36), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("side", sa.String(length=8), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("fee", sa.Float(), nullable=False),
        sa.Column("slippage", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["strategy_run_id"], ["strategy_runs.id"]),
        sa.ForeignKeyConstraint(["symbol_id"], ["symbols.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fills_order_id", "fills", ["order_id"], unique=False)
    op.create_index("ix_fills_order_timestamp", "fills", ["order_id", "timestamp"], unique=False)
    op.create_index("ix_fills_strategy_run_id", "fills", ["strategy_run_id"], unique=False)
    op.create_index("ix_fills_symbol_id", "fills", ["symbol_id"], unique=False)
    op.create_index("ix_fills_timestamp", "fills", ["timestamp"], unique=False)

    op.create_table(
        "positions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("strategy_run_id", sa.String(length=36), nullable=True),
        sa.Column("symbol_id", sa.String(length=36), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("average_cost", sa.Float(), nullable=False),
        sa.Column("realized_pnl", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["strategy_run_id"], ["strategy_runs.id"]),
        sa.ForeignKeyConstraint(["symbol_id"], ["symbols.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("strategy_run_id", "symbol_id", name="uq_position_run_symbol"),
    )
    op.create_index("ix_positions_run_symbol", "positions", ["strategy_run_id", "symbol_id"], unique=False)
    op.create_index("ix_positions_strategy_run_id", "positions", ["strategy_run_id"], unique=False)
    op.create_index("ix_positions_symbol_id", "positions", ["symbol_id"], unique=False)

    op.create_table(
        "trades",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("strategy_run_id", sa.String(length=36), nullable=True),
        sa.Column("symbol_id", sa.String(length=36), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("entry_price", sa.Float(), nullable=False),
        sa.Column("exit_price", sa.Float(), nullable=True),
        sa.Column("realized_pnl", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["strategy_run_id"], ["strategy_runs.id"]),
        sa.ForeignKeyConstraint(["symbol_id"], ["symbols.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trades_closed_at", "trades", ["closed_at"], unique=False)
    op.create_index("ix_trades_opened_at", "trades", ["opened_at"], unique=False)
    op.create_index("ix_trades_run_symbol", "trades", ["strategy_run_id", "symbol_id"], unique=False)
    op.create_index("ix_trades_strategy_run_id", "trades", ["strategy_run_id"], unique=False)
    op.create_index("ix_trades_symbol_id", "trades", ["symbol_id"], unique=False)

    op.create_table(
        "account_snapshots",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("strategy_run_id", sa.String(length=36), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cash", sa.Float(), nullable=False),
        sa.Column("equity", sa.Float(), nullable=False),
        sa.Column("realized_pnl", sa.Float(), nullable=False),
        sa.Column("unrealized_pnl", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["strategy_run_id"], ["strategy_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_account_snapshots_run_timestamp", "account_snapshots", ["strategy_run_id", "timestamp"], unique=False
    )
    op.create_index("ix_account_snapshots_strategy_run_id", "account_snapshots", ["strategy_run_id"], unique=False)
    op.create_index("ix_account_snapshots_timestamp", "account_snapshots", ["timestamp"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_account_snapshots_timestamp", table_name="account_snapshots")
    op.drop_index("ix_account_snapshots_strategy_run_id", table_name="account_snapshots")
    op.drop_index("ix_account_snapshots_run_timestamp", table_name="account_snapshots")
    op.drop_table("account_snapshots")
    op.drop_index("ix_trades_symbol_id", table_name="trades")
    op.drop_index("ix_trades_strategy_run_id", table_name="trades")
    op.drop_index("ix_trades_run_symbol", table_name="trades")
    op.drop_index("ix_trades_opened_at", table_name="trades")
    op.drop_index("ix_trades_closed_at", table_name="trades")
    op.drop_table("trades")
    op.drop_index("ix_positions_symbol_id", table_name="positions")
    op.drop_index("ix_positions_strategy_run_id", table_name="positions")
    op.drop_index("ix_positions_run_symbol", table_name="positions")
    op.drop_table("positions")
    op.drop_index("ix_fills_timestamp", table_name="fills")
    op.drop_index("ix_fills_symbol_id", table_name="fills")
    op.drop_index("ix_fills_strategy_run_id", table_name="fills")
    op.drop_index("ix_fills_order_timestamp", table_name="fills")
    op.drop_index("ix_fills_order_id", table_name="fills")
    op.drop_table("fills")
    op.drop_index("ix_orders_symbol_status", table_name="orders")
    op.drop_index("ix_orders_symbol_id", table_name="orders")
    op.drop_index("ix_orders_submitted_at", table_name="orders")
    op.drop_index("ix_orders_strategy_run_id", table_name="orders")
    op.drop_index("ix_orders_status", table_name="orders")
    op.drop_index("ix_orders_run_status", table_name="orders")
    op.drop_table("orders")
    op.drop_index("ix_strategy_runs_symbol_id", table_name="strategy_runs")
    op.drop_index("ix_strategy_runs_strategy_symbol", table_name="strategy_runs")
    op.drop_index("ix_strategy_runs_strategy_id", table_name="strategy_runs")
    op.drop_index("ix_strategy_runs_start_date", table_name="strategy_runs")
    op.drop_index("ix_strategy_runs_end_date", table_name="strategy_runs")
    op.drop_table("strategy_runs")
    op.drop_index("ix_strategies_name", table_name="strategies")
    op.drop_table("strategies")
    op.drop_index("ix_price_bars_timestamp", table_name="price_bars")
    op.drop_index("ix_price_bars_symbol_timestamp", table_name="price_bars")
    op.drop_index("ix_price_bars_symbol_id", table_name="price_bars")
    op.drop_table("price_bars")
    op.drop_index("ix_symbols_ticker", table_name="symbols")
    op.drop_table("symbols")
