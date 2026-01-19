"""fix experiments foreign key to use ON DELETE SET DEFAULT

Revision ID: fix_exp_fk_ondelete
Revises: add_synth_group_id_exp
Create Date: 2026-01-19 17:00:00.000000
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic
revision: str = "fix_exp_fk_ondelete"
down_revision: Union[str, None] = "add_synth_group_id_exp"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Update foreign key constraint to use ON DELETE SET DEFAULT."""
    # Drop existing constraint
    op.drop_constraint(
        "fk_experiments_synth_group_id",
        "experiments",
        type_="foreignkey"
    )

    # Recreate with ON DELETE SET DEFAULT
    op.create_foreign_key(
        "fk_experiments_synth_group_id",
        "experiments",
        "synth_groups",
        ["synth_group_id"],
        ["id"],
        ondelete="SET DEFAULT",
    )


def downgrade() -> None:
    """Revert to foreign key without ON DELETE behavior."""
    # Drop constraint with ON DELETE SET DEFAULT
    op.drop_constraint(
        "fk_experiments_synth_group_id",
        "experiments",
        type_="foreignkey"
    )

    # Recreate without ondelete (RESTRICT by default)
    op.create_foreign_key(
        "fk_experiments_synth_group_id",
        "experiments",
        "synth_groups",
        ["synth_group_id"],
        ["id"],
    )
