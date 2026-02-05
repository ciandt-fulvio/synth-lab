"""add_mechanism_tables

Revision ID: d9653ccb9a1a
Revises: 20260202_0001
Create Date: 2026-02-04 19:12:12.946568

Feature: 039-narrative-mechanism-config
Creates tables for mechanism definitions, options, and feature types.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic
revision: str = 'd9653ccb9a1a'
down_revision: Union[str, None] = '20260202_0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create mechanism configuration tables."""
    # mechanism_definitions table
    op.create_table(
        'mechanism_definitions',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('key', sa.String(50), unique=True, nullable=False),
        sa.Column('label_pt', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
    )
    op.create_index('idx_mechanism_definitions_key', 'mechanism_definitions', ['key'], unique=True)

    # mechanism_options table
    op.create_table(
        'mechanism_options',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('mechanism_id', UUID(as_uuid=False), sa.ForeignKey('mechanism_definitions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('label', sa.String(100), nullable=False),
        sa.Column('value', sa.Numeric(3, 2), nullable=False),
        sa.Column('display_order', sa.Integer, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('value >= 0 AND value <= 1', name='check_mechanism_option_value_range'),
    )
    op.create_index('idx_mechanism_options_mechanism_id', 'mechanism_options', ['mechanism_id'])
    op.create_index('idx_mechanism_options_order', 'mechanism_options', ['mechanism_id', 'display_order'], unique=True)

    # feature_types table
    op.create_table(
        'feature_types',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('key', sa.String(50), unique=True, nullable=False),
        sa.Column('label_pt', sa.String(100), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('amplifies_mechanisms', JSONB, server_default='[]', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_feature_types_key', 'feature_types', ['key'], unique=True)


def downgrade() -> None:
    """Drop mechanism configuration tables."""
    op.drop_table('feature_types')
    op.drop_table('mechanism_options')
    op.drop_table('mechanism_definitions')
