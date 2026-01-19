"""add server_default to experiments.synth_group_id

Revision ID: add_exp_srvdefault
Revises: fix_exp_fk_ondelete
Create Date: 2026-01-19 17:05:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision: str = "add_exp_srvdefault"
down_revision: Union[str, None] = "fix_exp_fk_ondelete"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add server_default to synth_group_id column."""
    op.alter_column(
        "experiments",
        "synth_group_id",
        existing_type=sa.String(length=50),
        nullable=False,
        server_default="grp_00000001",
    )


def downgrade() -> None:
    """Remove server_default from synth_group_id column."""
    op.alter_column(
        "experiments",
        "synth_group_id",
        existing_type=sa.String(length=50),
        nullable=False,
        server_default=None,
    )
