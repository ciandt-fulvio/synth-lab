"""add_experiment_shares_table

Revision ID: d422dd542af3
Revises: e191ef8fb810
Create Date: 2026-01-22 02:01:45.292156
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic
revision: str = 'd422dd542af3'
down_revision: Union[str, None] = 'e191ef8fb810'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create permission_level enum type if it doesn't exist
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE permission_level AS ENUM ('viewer', 'editor');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Check if experiment_shares table already exists (may be created by parallel migration)
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if 'experiment_shares' not in inspector.get_table_names():
        # Create experiment_shares table
        op.create_table(
            'experiment_shares',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('experiment_id', sa.String(length=50), nullable=False),
            sa.Column('user_id', sa.UUID(), nullable=False),
            sa.Column('permission_level', postgresql.ENUM('viewer', 'editor', name='permission_level', create_type=False), nullable=False),
            sa.Column('granted_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.Column('granted_by_id', sa.UUID(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['granted_by_id'], ['users.id'], ondelete='SET NULL'),
            sa.UniqueConstraint('experiment_id', 'user_id', name='uq_experiment_shares_experiment_user')
        )

        # Create index for efficient "my shared experiments" queries
        op.create_index(op.f('ix_experiment_shares_user_id'), 'experiment_shares', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop index
    op.drop_index(op.f('ix_experiment_shares_user_id'), table_name='experiment_shares')

    # Drop experiment_shares table
    op.drop_table('experiment_shares')

    # Note: Don't drop permission_level enum here as it may be used by synth_group_shares
    # The enum will be dropped when all tables using it are removed
