"""add_owner_id_columns

Revision ID: a7b8c9d0e1f2
Revises: f1a2b3c4d5e6
Create Date: 2026-01-22 03:01:00.000000

Adds owner_id columns to experiments and synth_groups tables.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add owner_id columns to experiments and synth_groups."""
    # Add owner_id to experiments
    # Using String(36) to match ORM and users.id column type
    op.add_column(
        'experiments',
        sa.Column('owner_id', sa.String(36), nullable=True)
    )
    op.create_foreign_key(
        'fk_experiments_owner',
        'experiments',
        'users',
        ['owner_id'],
        ['id'],
        ondelete='SET NULL'
    )
    op.create_index('idx_experiments_owner', 'experiments', ['owner_id'])

    # Add owner_id to synth_groups
    op.add_column(
        'synth_groups',
        sa.Column('owner_id', sa.String(36), nullable=True)
    )
    op.create_foreign_key(
        'fk_synth_groups_owner',
        'synth_groups',
        'users',
        ['owner_id'],
        ['id'],
        ondelete='SET NULL'
    )
    op.create_index('idx_synth_groups_owner', 'synth_groups', ['owner_id'])


def downgrade() -> None:
    """Remove owner_id columns from experiments and synth_groups."""
    op.drop_index('idx_synth_groups_owner', table_name='synth_groups')
    op.drop_constraint('fk_synth_groups_owner', 'synth_groups', type_='foreignkey')
    op.drop_column('synth_groups', 'owner_id')

    op.drop_index('idx_experiments_owner', table_name='experiments')
    op.drop_constraint('fk_experiments_owner', 'experiments', type_='foreignkey')
    op.drop_column('experiments', 'owner_id')
