"""add tags and experiment_tags tables

Revision ID: 09d318020a17
Revises: ccea4e94f2f7
Create Date: 2026-01-06 11:03:10.039883
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision: str = '09d318020a17'
down_revision: Union[str, None] = 'ccea4e94f2f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create tags table
    op.create_table(
        'tags',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.String(length=50), nullable=False),
        sa.Column('updated_at', sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('idx_tags_name', 'tags', ['name'], unique=False)

    # Create experiment_tags junction table
    op.create_table(
        'experiment_tags',
        sa.Column('experiment_id', sa.String(length=50), nullable=False),
        sa.Column('tag_id', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('experiment_id', 'tag_id')
    )
    op.create_index('idx_experiment_tags_experiment', 'experiment_tags', ['experiment_id'], unique=False)
    op.create_index('idx_experiment_tags_tag', 'experiment_tags', ['tag_id'], unique=False)


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop experiment_tags table
    op.drop_index('idx_experiment_tags_tag', table_name='experiment_tags')
    op.drop_index('idx_experiment_tags_experiment', table_name='experiment_tags')
    op.drop_table('experiment_tags')

    # Drop tags table
    op.drop_index('idx_tags_name', table_name='tags')
    op.drop_table('tags')
