from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import RowMapping

revision = "004_trade_fee_basis"
down_revision = "003_execution_realism"
branch_labels = None
depends_on = None

FillRecord = RowMapping


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
        sa.column("id", sa.String()),
        sa.column("strategy_run_id", sa.String()),
        sa.column("symbol_id", sa.String()),
        sa.column("timestamp", sa.DateTime(timezone=True)),
        sa.column("side", sa.String()),
        sa.column("quantity", sa.Float()),
        sa.column("fee", sa.Float()),
    )
    fill_groups: dict[tuple[object, object], dict[str, list[FillRecord]]] = defaultdict(lambda: {"buy": [], "sell": []})
    for fill in bind.execute(sa.select(fills)).mappings():
        fill_groups[(fill["strategy_run_id"], fill["symbol_id"])][fill["side"]].append(fill)
    for fills_by_side in fill_groups.values():
        for fill_rows in fills_by_side.values():
            fill_rows.sort(key=lambda fill: (fill["timestamp"], fill["id"]))

    trade_groups: dict[tuple[object, object], list[FillRecord]] = defaultdict(list)
    for trade in bind.execute(sa.select(trades)).mappings():
        trade_groups[(trade["strategy_run_id"], trade["symbol_id"])].append(trade)

    for key, trade_rows in trade_groups.items():
        trade_rows.sort(
            key=lambda trade: (
                trade["opened_at"],
                trade["closed_at"] is None,
                trade["closed_at"] or trade["opened_at"],
                trade["id"],
            )
        )
        fills_by_side = fill_groups[key]
        buy_index = 0
        sell_index = 0
        for trade in trade_rows:
            entry_fee, buy_index = _consume_fill_fees(fills_by_side["buy"], buy_index, trade["quantity"])
            exit_quantity = trade["quantity"] if trade["closed_at"] is not None else None
            exit_fee, sell_index = _consume_fill_fees(fills_by_side["sell"], sell_index, exit_quantity)
            values = {"entry_fee": entry_fee, "exit_fee": exit_fee}
            if trade["quantity"] > 0 and entry_fee:
                values["entry_price"] = (trade["entry_price"] * trade["quantity"] - entry_fee) / trade["quantity"]
            bind.execute(trades.update().where(trades.c.id == trade["id"]).values(**values))


def _consume_fill_fees(
    fill_rows: Sequence[FillRecord],
    start_index: int,
    expected_quantity: float | None,
) -> tuple[float, int]:
    fee = 0.0
    quantity = 0.0
    index = start_index
    while index < len(fill_rows) and (expected_quantity is None or quantity + 1e-9 < expected_quantity):
        fill = fill_rows[index]
        fee += float(fill["fee"] or 0.0)
        quantity += max(float(fill["quantity"] or 0.0), 0.0)
        index += 1
    return fee, index
