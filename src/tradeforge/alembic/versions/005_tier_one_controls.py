"""Add Tier 1 safety, data quality, and audit records.

Revision ID: 005_tier_one_controls
Revises: 004_trade_fee_basis
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "005_tier_one_controls"
down_revision: str | None = "004_trade_fee_basis"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("symbols") as batch_op:
        batch_op.add_column(sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))

    op.create_table(
        "corporate_actions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("symbol_id", sa.String(length=36), nullable=False),
        sa.Column("action_type", sa.String(length=24), nullable=False),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ratio", sa.Float(), nullable=True),
        sa.Column("cash_amount", sa.Float(), nullable=True),
        sa.Column("new_ticker", sa.String(length=32), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["symbol_id"], ["symbols.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_corporate_actions_symbol_id", "corporate_actions", ["symbol_id"])
    op.create_index("ix_corporate_actions_action_type", "corporate_actions", ["action_type"])
    op.create_index("ix_corporate_actions_effective_at", "corporate_actions", ["effective_at"])
    op.create_index("ix_corporate_actions_symbol_effective", "corporate_actions", ["symbol_id", "effective_at"])

    op.create_table(
        "data_quality_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("symbol_id", sa.String(length=36), nullable=True),
        sa.Column("source_file", sa.Text(), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("issue_type", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("repair_action", sa.String(length=64), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.ForeignKeyConstraint(["symbol_id"], ["symbols.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_data_quality_events_symbol_id", "data_quality_events", ["symbol_id"])
    op.create_index("ix_data_quality_events_detected_at", "data_quality_events", ["detected_at"])
    op.create_index("ix_data_quality_events_issue_type", "data_quality_events", ["issue_type"])
    op.create_index("ix_data_quality_events_symbol_detected", "data_quality_events", ["symbol_id", "detected_at"])

    op.create_table(
        "execution_audit_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("order_id", sa.String(length=36), nullable=True),
        sa.Column("strategy_run_id", sa.String(length=36), nullable=True),
        sa.Column("symbol_id", sa.String(length=36), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("remaining_quantity", sa.Float(), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["strategy_run_id"], ["strategy_runs.id"]),
        sa.ForeignKeyConstraint(["symbol_id"], ["symbols.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_execution_audit_events_order_id", "execution_audit_events", ["order_id"])
    op.create_index("ix_execution_audit_events_strategy_run_id", "execution_audit_events", ["strategy_run_id"])
    op.create_index("ix_execution_audit_events_symbol_id", "execution_audit_events", ["symbol_id"])
    op.create_index("ix_execution_audit_events_timestamp", "execution_audit_events", ["timestamp"])
    op.create_index("ix_execution_audit_events_event_type", "execution_audit_events", ["event_type"])
    op.create_index("ix_execution_audit_events_order_timestamp", "execution_audit_events", ["order_id", "timestamp"])
    op.create_index(
        "ix_execution_audit_events_run_timestamp", "execution_audit_events", ["strategy_run_id", "timestamp"]
    )


def downgrade() -> None:
    op.drop_table("execution_audit_events")
    op.drop_table("data_quality_events")
    op.drop_table("corporate_actions")
    with op.batch_alter_table("symbols") as batch_op:
        batch_op.drop_column("is_active")
