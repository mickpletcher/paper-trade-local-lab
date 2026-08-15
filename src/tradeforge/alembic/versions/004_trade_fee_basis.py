from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "004_trade_fee_basis"
down_revision = "003_execution_realism"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("trades", sa.Column("entry_fee", sa.Float(), nullable=False, server_default="0"))
    op.add_column("trades", sa.Column("exit_fee", sa.Float(), nullable=False, server_default="0"))
    _separate_existing_entry_fees()


def downgrade() -> None:
    bind = op.get_bind()
    trades = sa.table(
        "trades",
        sa.column("id", sa.String()),
        sa.column("quantity", sa.Float()),
        sa.column("entry_price", sa.Float()),
        sa.column("entry_fee", sa.Float()),
    )
    for trade in bind.execute(
        sa.select(trades.c.id, trades.c.quantity, trades.c.entry_price, trades.c.entry_fee)
    ).mappings():
        if trade["quantity"] > 0 and trade["entry_fee"]:
            legacy_entry_price = (trade["entry_price"] * trade["quantity"] + trade["entry_fee"]) / trade["quantity"]
            bind.execute(trades.update().where(trades.c.id == trade["id"]).values(entry_price=legacy_entry_price))
    op.drop_column("trades", "exit_fee")
    op.drop_column("trades", "entry_fee")


def _separate_existing_entry_fees() -> None:
    bind = op.get_bind()
    trades = sa.table(
        "trades",
        sa.column("id", sa.String()),
        sa.column("strategy_run_id", sa.String()),
        sa.column("symbol_id", sa.String()),
        sa.column("opened_at", sa.DateTime(timezone=True)),
        sa.column("closed_at", sa.DateTime(timezone=True)),
        sa.column("quantity", sa.Float()),
        sa.column("entry_price", sa.Float()),
        sa.column("entry_fee", sa.Float()),
        sa.column("exit_fee", sa.Float()),
    )
    fills = sa.table(
        "fills",
        sa.column("strategy_run_id", sa.String()),
        sa.column("symbol_id", sa.String()),
        sa.column("timestamp", sa.DateTime(timezone=True)),
        sa.column("side", sa.String()),
        sa.column("fee", sa.Float()),
    )
    fill_rows = bind.execute(sa.select(fills)).mappings().all()
    for trade in bind.execute(sa.select(trades)).mappings():
        matching_fills = [
            fill
            for fill in fill_rows
            if fill["strategy_run_id"] == trade["strategy_run_id"]
            and fill["symbol_id"] == trade["symbol_id"]
            and fill["timestamp"] >= trade["opened_at"]
            and (trade["closed_at"] is None or fill["timestamp"] <= trade["closed_at"])
        ]
        entry_fee = sum(fill["fee"] or 0.0 for fill in matching_fills if fill["side"] == "buy")
        exit_fee = sum(fill["fee"] or 0.0 for fill in matching_fills if fill["side"] == "sell")
        values = {"entry_fee": entry_fee, "exit_fee": exit_fee}
        if trade["quantity"] > 0 and entry_fee:
            values["entry_price"] = (trade["entry_price"] * trade["quantity"] - entry_fee) / trade["quantity"]
        bind.execute(trades.update().where(trades.c.id == trade["id"]).values(**values))
