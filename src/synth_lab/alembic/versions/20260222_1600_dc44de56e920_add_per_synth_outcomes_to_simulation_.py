"""add per_synth_outcomes and drop simulation_synth_results

Adds per_synth_outcomes JSONB column to simulation_runs (replaces
the simulation_synth_results table with an inline dict per run).

Revision ID: dc44de56e920
Revises: b2c3d4e5f6a7
Create Date: 2026-02-22 16:00:44.675953
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic
revision: str = "dc44de56e920"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "simulation_runs",
        sa.Column("per_synth_outcomes", JSONB, nullable=True),
    )
    # Drop if exists: table was created in an earlier revision that may or
    # may not be present depending on migration history.
    op.execute("DROP TABLE IF EXISTS simulation_synth_results")


def downgrade() -> None:
    op.create_table(
        "simulation_synth_results",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column(
            "simulation_run_id",
            sa.String(50),
            sa.ForeignKey("simulation_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("synth_id", sa.String(50), nullable=False),
        sa.Column("outcome", sa.Float, nullable=False),
        sa.Column("dag_values", JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.drop_column("simulation_runs", "per_synth_outcomes")
