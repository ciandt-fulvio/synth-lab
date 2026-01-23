"""add_auth_tables

Revision ID: f1a2b3c4d5e6
Revises: e6b4ffd0b652
Create Date: 2026-01-22 03:00:00.000000

Adds authentication and sharing tables:
- users: User accounts from Google OAuth
- experiment_shares: Experiment sharing relationships
- synth_group_shares: Synth group sharing relationships
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'e6b4ffd0b652'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add authentication and sharing tables."""
    # Create permission_level enum if it doesn't exist
    conn = op.get_bind()
    enum_exists = conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'permission_level')"
    )).scalar()

    if not enum_exists:
        permission_level_enum = postgresql.ENUM('viewer', 'editor', name='permission_level')
        permission_level_enum.create(conn)

    # Get the enum type for use in table columns
    permission_level_enum = postgresql.ENUM(
        'viewer', 'editor', name='permission_level', create_type=False
    )

    # Create users table
    # Using String(36) to match ORM and be consistent with other ID columns in the codebase
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('google_user_id', sa.String(255), unique=True, nullable=False),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('profile_picture_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.String(50), nullable=False),
        sa.Column('updated_at', sa.String(50), nullable=False),
    )
    op.create_index('idx_users_email', 'users', ['email'], unique=True)
    op.create_index('idx_users_google_id', 'users', ['google_user_id'], unique=True)

    # Create experiment_shares table
    op.create_table(
        'experiment_shares',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('experiment_id', sa.String(50), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('permission_level', permission_level_enum, nullable=False),
        sa.Column('granted_at', sa.String(50), nullable=False),
        sa.Column('granted_by_id', sa.String(36), nullable=True),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['granted_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('experiment_id', 'user_id', name='uq_experiment_user_share')
    )
    op.create_index('idx_experiment_shares_user', 'experiment_shares', ['user_id'])
    op.create_index('idx_experiment_shares_experiment', 'experiment_shares', ['experiment_id'])

    # Create synth_group_shares table
    op.create_table(
        'synth_group_shares',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('synth_group_id', sa.String(50), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('permission_level', permission_level_enum, nullable=False),
        sa.Column('granted_at', sa.String(50), nullable=False),
        sa.Column('granted_by_id', sa.String(36), nullable=True),
        sa.ForeignKeyConstraint(['synth_group_id'], ['synth_groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['granted_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('synth_group_id', 'user_id', name='uq_synth_group_user_share')
    )
    op.create_index('idx_synth_group_shares_user', 'synth_group_shares', ['user_id'])
    op.create_index('idx_synth_group_shares_synth_group', 'synth_group_shares', ['synth_group_id'])


def downgrade() -> None:
    """Remove authentication and sharing tables."""
    op.drop_table('synth_group_shares')
    op.drop_table('experiment_shares')
    op.drop_table('users')

    # Drop enum type
    permission_level_enum = postgresql.ENUM('viewer', 'editor', name='permission_level')
    permission_level_enum.drop(op.get_bind())
