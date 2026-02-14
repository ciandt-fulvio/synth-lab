"""add_synth_group_shares_table

Revision ID: 756cdd5e5b40
Revises: d422dd542af3
Create Date: 2026-01-22 02:02:29.090581
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision: str = '756cdd5e5b40'
down_revision: Union[str, None] = 'd422dd542af3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Check if synth_group_shares table already exists (may be created by parallel migration)
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if 'synth_group_shares' not in inspector.get_table_names():
        # Create synth_group_shares table
        # Note: permission_level enum already created in previous migration
        op.create_table(
            'synth_group_shares',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('synth_group_id', sa.String(length=50), nullable=False),
            sa.Column('user_id', sa.UUID(), nullable=False),
            sa.Column('permission_level', postgresql.ENUM('viewer', 'editor', name='permission_level', create_type=False), nullable=False),
            sa.Column('granted_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.Column('granted_by_id', sa.UUID(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['synth_group_id'], ['synth_groups.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['granted_by_id'], ['users.id'], ondelete='SET NULL'),
            sa.UniqueConstraint('synth_group_id', 'user_id', name='uq_synth_group_shares_group_user')
        )

        # Create index for efficient "my shared synth_groups" queries
        op.create_index(op.f('ix_synth_group_shares_user_id'), 'synth_group_shares', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop index
    op.drop_index(op.f('ix_synth_group_shares_user_id'), table_name='synth_group_shares')

    # Drop synth_group_shares table
    op.drop_table('synth_group_shares')
