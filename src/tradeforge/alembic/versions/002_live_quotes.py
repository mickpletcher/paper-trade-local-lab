from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "002_live_quotes"
down_revision = "001_core_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "live_quotes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("symbol_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("quote_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_price", sa.Float(), nullable=True),
        sa.Column("bid_price", sa.Float(), nullable=True),
        sa.Column("ask_price", sa.Float(), nullable=True),
        sa.Column("bid_size", sa.Integer(), nullable=True),
        sa.Column("ask_size", sa.Integer(), nullable=True),
        sa.Column("previous_close", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(length=16), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_payload_json", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["symbol_id"], ["symbols.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("symbol_id", "provider", name="uq_live_quotes_symbol_provider"),
    )
    op.create_index("ix_live_quotes_fetched_at", "live_quotes", ["fetched_at"], unique=False)
    op.create_index("ix_live_quotes_provider", "live_quotes", ["provider"], unique=False)
    op.create_index("ix_live_quotes_quote_timestamp", "live_quotes", ["quote_timestamp"], unique=False)
    op.create_index("ix_live_quotes_symbol_id", "live_quotes", ["symbol_id"], unique=False)
    op.create_index("ix_live_quotes_symbol_provider", "live_quotes", ["symbol_id", "provider"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_live_quotes_symbol_provider", table_name="live_quotes")
    op.drop_index("ix_live_quotes_symbol_id", table_name="live_quotes")
    op.drop_index("ix_live_quotes_quote_timestamp", table_name="live_quotes")
    op.drop_index("ix_live_quotes_provider", table_name="live_quotes")
    op.drop_index("ix_live_quotes_fetched_at", table_name="live_quotes")
    op.drop_table("live_quotes")
