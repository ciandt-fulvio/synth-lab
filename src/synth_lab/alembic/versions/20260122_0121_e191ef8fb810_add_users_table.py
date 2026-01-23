"""add_users_table

Revision ID: e191ef8fb810
Revises: e6b4ffd0b652
Create Date: 2026-01-22 01:21:43.350000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision: str = 'e191ef8fb810'
down_revision: Union[str, None] = 'e6b4ffd0b652'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Check if users table already exists (may be created by parallel migration)
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if 'users' not in inspector.get_table_names():
        # Create users table
        op.create_table(
            'users',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('google_user_id', sa.String(), nullable=False),
            sa.Column('email', sa.String(), nullable=False),
            sa.Column('display_name', sa.String(), nullable=True),
            sa.Column('profile_picture_url', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('google_user_id'),
            sa.UniqueConstraint('email')
        )

        # Create indexes for efficient lookups
        op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
        op.create_index(op.f('ix_users_google_user_id'), 'users', ['google_user_id'], unique=True)


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop indexes
    op.drop_index(op.f('ix_users_google_user_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')

    # Drop users table
    op.drop_table('users')
