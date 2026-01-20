"""drop_unused_sensitivity_and_region_tables

Revision ID: e6b4ffd0b652
Revises: c5b57ad43acf
Create Date: 2026-01-20 14:18:04.758636
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision: str = 'e6b4ffd0b652'
down_revision: Union[str, None] = 'c5b57ad43acf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop unused sensitivity_results and region_analyses tables."""
    # Drop indexes first
    op.drop_index('idx_sensitivity_analyzed_at', table_name='sensitivity_results')
    op.drop_index('idx_sensitivity_simulation', table_name='sensitivity_results')
    op.drop_index('idx_regions_simulation', table_name='region_analyses')

    # Drop tables
    op.drop_table('sensitivity_results')
    op.drop_table('region_analyses')


def downgrade() -> None:
    """Recreate sensitivity_results and region_analyses tables."""
    # Recreate region_analyses table
    op.create_table(
        'region_analyses',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('simulation_id', sa.String(50), nullable=False),
        sa.Column('rules', sa.JSON(), nullable=False),
        sa.Column('rule_text', sa.Text(), nullable=False),
        sa.Column('synth_count', sa.Integer(), nullable=False),
        sa.Column('synth_percentage', sa.Float(), nullable=False),
        sa.Column('did_not_try_rate', sa.Float(), nullable=False),
        sa.Column('failed_rate', sa.Float(), nullable=False),
        sa.Column('success_rate', sa.Float(), nullable=False),
        sa.Column('failure_delta', sa.Float(), nullable=False),
    )
    op.create_index('idx_regions_simulation', 'region_analyses', ['simulation_id'])

    # Recreate sensitivity_results table
    op.create_table(
        'sensitivity_results',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('simulation_id', sa.String(50), nullable=False),
        sa.Column('analyzed_at', sa.String(50), nullable=False),
        sa.Column('deltas_used', sa.JSON(), nullable=False),
        sa.Column('baseline_success', sa.Float(), nullable=False),
        sa.Column('most_sensitive_dimension', sa.String(100), nullable=False),
        sa.Column('dimensions', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.String(50), nullable=False),
    )
    op.create_index('idx_sensitivity_simulation', 'sensitivity_results', ['simulation_id'])
    op.create_index('idx_sensitivity_analyzed_at', 'sensitivity_results', ['analyzed_at'])
