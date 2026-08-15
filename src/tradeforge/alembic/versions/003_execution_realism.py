from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "003_execution_realism"
down_revision = "002_live_quotes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("stop_price", sa.Float(), nullable=True))
    op.add_column("orders", sa.Column("filled_quantity", sa.Float(), nullable=False, server_default="0"))
    op.add_column("orders", sa.Column("commission_paid", sa.Float(), nullable=False, server_default="0"))
    op.add_column("orders", sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("orders", "triggered_at")
    op.drop_column("orders", "commission_paid")
    op.drop_column("orders", "filled_quantity")
    op.drop_column("orders", "stop_price")
