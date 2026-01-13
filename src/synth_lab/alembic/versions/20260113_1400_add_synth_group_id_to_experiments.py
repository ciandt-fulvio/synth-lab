"""add synth_group_id column to experiments table

Revision ID: add_synth_group_id_exp
Revises: add_config_synth_groups
Create Date: 2026-01-13 14:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision: str = "add_synth_group_id_exp"
down_revision: Union[str, None] = "add_config_synth_groups"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add synth_group_id column to experiments table."""
    # Ensure default synth group exists (idempotent - won't fail if already exists)
    op.execute(
        """
        INSERT INTO synth_groups (id, name, description, created_at)
        VALUES (
            'grp_00000001',
            'Default',
            'Grupo padrão para synths sem grupo específico',
            (NOW() AT TIME ZONE 'utc')::text
        )
        ON CONFLICT (id) DO NOTHING
        """
    )

    # Add synth_group_id column (nullable initially for existing data)
    op.add_column(
        "experiments",
        sa.Column("synth_group_id", sa.String(length=50), nullable=True),
    )

    # Set default value for existing experiments
    op.execute(
        """
        UPDATE experiments
        SET synth_group_id = 'grp_00000001'
        WHERE synth_group_id IS NULL
        """
    )

    # Make column non-nullable after populating
    op.alter_column("experiments", "synth_group_id", nullable=False)

    # Add foreign key constraint
    op.create_foreign_key(
        "fk_experiments_synth_group_id",
        "experiments",
        "synth_groups",
        ["synth_group_id"],
        ["id"],
    )

    # Create index for efficient lookups
    op.create_index(
        "idx_experiments_synth_group_id",
        "experiments",
        ["synth_group_id"],
    )


def downgrade() -> None:
    """Remove synth_group_id column from experiments table."""
    op.drop_index("idx_experiments_synth_group_id", table_name="experiments")
    op.drop_constraint("fk_experiments_synth_group_id", "experiments", type_="foreignkey")
    op.drop_column("experiments", "synth_group_id")
