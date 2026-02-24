"""add_simulation_reports_table

Revision ID: ce8298d5f150
Revises: dc44de56e920
Create Date: 2026-02-24 11:06:19.806293
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision: str = 'ce8298d5f150'
down_revision: Union[str, None] = 'dc44de56e920'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    op.create_table(
        'simulation_reports',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('experiment_id', sa.String(length=50), nullable=True),
        sa.Column('batch_id', sa.String(length=50), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('model', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['batch_id'], ['simulation_batches.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_simulation_reports_experiment', 'simulation_reports', ['experiment_id'])


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_index('idx_simulation_reports_experiment', table_name='simulation_reports')
    op.drop_table('simulation_reports')
