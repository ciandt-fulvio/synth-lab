"""add multi scenario tables

Creates simulation_batches table, adds batch_id and product_values
to simulation_runs.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-21 18:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create simulation_batches table
    op.create_table(
        "simulation_batches",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column(
            "experiment_id",
            sa.String(50),
            sa.ForeignKey("experiments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "causal_model_id",
            sa.String(50),
            sa.ForeignKey("causal_models.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("n_scenarios", sa.Integer, nullable=False),
        sa.Column("n_synths", sa.Integer, nullable=False),
        sa.Column("n_repetitions", sa.Integer, nullable=False, server_default="10"),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="running",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_simulation_batches_experiment",
        "simulation_batches",
        ["experiment_id"],
    )

    # 2. Alter simulation_runs: add batch_id, product_values
    op.add_column(
        "simulation_runs",
        sa.Column(
            "batch_id",
            sa.String(50),
            sa.ForeignKey("simulation_batches.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "simulation_runs",
        sa.Column("product_values", JSONB, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("simulation_runs", "product_values")
    op.drop_column("simulation_runs", "batch_id")
    op.drop_table("simulation_batches")
