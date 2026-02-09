"""migrate_to_2_outcome_model

Rename 3-outcome columns to 2-outcome model:
- synth_outcomes: did_not_try_rate, failed_rate, success_rate → adopted_rate, not_adopted_rate
- explorations: best_success_rate → best_adopted_rate

Revision ID: a2b3c4d5e6f7
Revises: 1d3d2218f612
Create Date: 2026-02-09 17:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a2b3c4d5e6f7"
down_revision: Union[str, None] = "1d3d2218f612"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- synth_outcomes table ---
    # 1. Rename success_rate → adopted_rate
    op.alter_column("synth_outcomes", "success_rate", new_column_name="adopted_rate")

    # 2. Rename failed_rate → not_adopted_rate (temporarily holds failed data)
    op.alter_column("synth_outcomes", "failed_rate", new_column_name="not_adopted_rate")

    # 3. Recalculate: adopted_rate stays as success_rate, not_adopted_rate = 1 - adopted_rate
    op.execute(
        "UPDATE synth_outcomes SET not_adopted_rate = 1.0 - adopted_rate"
    )

    # 4. Drop did_not_try_rate (no longer needed)
    op.drop_column("synth_outcomes", "did_not_try_rate")

    # --- explorations table ---
    op.alter_column("explorations", "best_success_rate", new_column_name="best_adopted_rate")


def downgrade() -> None:
    # --- explorations table ---
    op.alter_column("explorations", "best_adopted_rate", new_column_name="best_success_rate")

    # --- synth_outcomes table ---
    # 1. Add back did_not_try_rate
    op.add_column(
        "synth_outcomes",
        sa.Column("did_not_try_rate", sa.Float(), nullable=False, server_default="0.0"),
    )

    # 2. Rename not_adopted_rate → failed_rate
    op.alter_column("synth_outcomes", "not_adopted_rate", new_column_name="failed_rate")

    # 3. Rename adopted_rate → success_rate
    op.alter_column("synth_outcomes", "adopted_rate", new_column_name="success_rate")

    # 4. Recalculate old values: did_not_try_rate = 1 - success_rate - failed_rate
    op.execute(
        "UPDATE synth_outcomes SET did_not_try_rate = 1.0 - success_rate - failed_rate"
    )

    # Remove server default
    op.alter_column("synth_outcomes", "did_not_try_rate", server_default=None)
