"""add_owner_id_to_synth_groups

Revision ID: 4ed1cc72a059
Revises: bf3a417c3c22
Create Date: 2026-01-22 02:05:49.423549
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision: str = '4ed1cc72a059'
down_revision: Union[str, None] = 'bf3a417c3c22'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Add owner_id column to synth_groups table (nullable for existing synth_groups)
    op.add_column('synth_groups', sa.Column('owner_id', sa.UUID(), nullable=True))

    # Add foreign key constraint
    op.create_foreign_key('fk_synth_groups_owner', 'synth_groups', 'users', ['owner_id'], ['id'], ondelete='SET NULL')

    # Create index for efficient owner queries
    op.create_index(op.f('ix_synth_groups_owner_id'), 'synth_groups', ['owner_id'], unique=False)


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop index
    op.drop_index(op.f('ix_synth_groups_owner_id'), table_name='synth_groups')

    # Drop foreign key constraint
    op.drop_constraint('fk_synth_groups_owner', 'synth_groups', type_='foreignkey')

    # Drop owner_id column
    op.drop_column('synth_groups', 'owner_id')
