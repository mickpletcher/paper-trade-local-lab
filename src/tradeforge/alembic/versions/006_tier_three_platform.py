"""Add tenants, API identities, and experiment tracking.

Revision ID: 006_tier_three_platform
Revises: 005_tier_one_controls
"""

from collections.abc import Sequence
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

revision: str = "006_tier_three_platform"
down_revision: str | None = "005_tier_one_controls"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000001"


def upgrade() -> None:
    tenants = op.create_table(
        "tenants",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_tenants_name", "tenants", ["name"], unique=True)
    op.bulk_insert(
        tenants,
        [{"id": DEFAULT_TENANT_ID, "name": "default", "is_active": True, "created_at": datetime.now(timezone.utc)}],
    )

    op.create_table(
        "api_keys",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("key_hash", sa.String(length=128), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key_hash"),
    )
    op.create_index("ix_api_keys_tenant_id", "api_keys", ["tenant_id"])
    op.create_index("ix_api_keys_key_hash", "api_keys", ["key_hash"], unique=True)
    op.create_index("ix_api_keys_role", "api_keys", ["role"])
    op.create_index("ix_api_keys_tenant_role", "api_keys", ["tenant_id", "role"])

    with op.batch_alter_table("strategy_runs") as batch_op:
        batch_op.add_column(
            sa.Column("tenant_id", sa.String(length=36), nullable=False, server_default=DEFAULT_TENANT_ID)
        )
        batch_op.create_foreign_key("fk_strategy_runs_tenant_id_tenants", "tenants", ["tenant_id"], ["id"])
        batch_op.create_index("ix_strategy_runs_tenant_id", ["tenant_id"])

    op.create_table(
        "experiments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("strategy_run_id", sa.String(length=36), nullable=False),
        sa.Column("strategy_version", sa.String(length=64), nullable=False),
        sa.Column("parameters_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("dataset_sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["strategy_run_id"], ["strategy_runs.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("strategy_run_id", name="uq_experiments_strategy_run_id"),
    )
    op.create_index("ix_experiments_tenant_id", "experiments", ["tenant_id"])
    op.create_index("ix_experiments_strategy_run_id", "experiments", ["strategy_run_id"])
    op.create_index("ix_experiments_created_at", "experiments", ["created_at"])
    op.create_index("ix_experiments_tenant_created", "experiments", ["tenant_id", "created_at"])

    op.create_table(
        "experiment_artifacts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("experiment_id", sa.String(length=36), nullable=False),
        sa.Column("artifact_type", sa.String(length=32), nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["experiment_id"], ["experiments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_experiment_artifacts_experiment_id", "experiment_artifacts", ["experiment_id"])
    op.create_index(
        "ix_experiment_artifacts_experiment_type", "experiment_artifacts", ["experiment_id", "artifact_type"]
    )


def downgrade() -> None:
    op.drop_table("experiment_artifacts")
    op.drop_table("experiments")
    with op.batch_alter_table("strategy_runs") as batch_op:
        batch_op.drop_index("ix_strategy_runs_tenant_id")
        batch_op.drop_constraint("fk_strategy_runs_tenant_id_tenants", type_="foreignkey")
        batch_op.drop_column("tenant_id")
    op.drop_table("api_keys")
    op.drop_table("tenants")
