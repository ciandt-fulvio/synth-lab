"""add_owner_id_to_experiments

Revision ID: bf3a417c3c22
Revises: 756cdd5e5b40
Create Date: 2026-01-22 02:05:28.260088
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision: str = 'bf3a417c3c22'
down_revision: Union[str, None] = '756cdd5e5b40'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Check if owner_id column already exists (may be added by parallel migration)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('experiments')]

    if 'owner_id' not in columns:
        # Add owner_id column to experiments table (nullable for existing experiments)
        op.add_column('experiments', sa.Column('owner_id', sa.UUID(), nullable=True))

        # Add foreign key constraint
        op.create_foreign_key('fk_experiments_owner', 'experiments', 'users', ['owner_id'], ['id'], ondelete='SET NULL')

        # Create index for efficient owner queries
        op.create_index(op.f('ix_experiments_owner_id'), 'experiments', ['owner_id'], unique=False)


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop index
    op.drop_index(op.f('ix_experiments_owner_id'), table_name='experiments')

    # Drop foreign key constraint
    op.drop_constraint('fk_experiments_owner', 'experiments', type_='foreignkey')

    # Drop owner_id column
    op.drop_column('experiments', 'owner_id')
