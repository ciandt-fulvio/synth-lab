"""add_pending_invites_table

Revision ID: a2d0dcc46c8d
Revises: df69409340e0
Create Date: 2026-02-27 14:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'a2d0dcc46c8d'
down_revision: Union[str, None] = 'df69409340e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'pending_invites' not in existing_tables:
        op.create_table(
            'pending_invites',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('resource_type', sa.String(20), nullable=False),
            sa.Column('resource_id', sa.String(50), nullable=False),
            sa.Column('invited_email', sa.String(255), nullable=False),
            sa.Column('invited_by_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('created_at', sa.String(50), nullable=False),
        )
        op.create_index('ix_pending_invites_invited_email', 'pending_invites', ['invited_email'])
        op.create_index('ix_pending_invites_resource', 'pending_invites', ['resource_type', 'resource_id'])
        op.create_unique_constraint(
            'uq_pending_invites_resource_email',
            'pending_invites',
            ['resource_type', 'resource_id', 'invited_email'],
        )


def downgrade() -> None:
    op.drop_table('pending_invites')
