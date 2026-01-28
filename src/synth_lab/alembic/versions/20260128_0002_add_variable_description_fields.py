"""Add variable description and metadata fields

Revision ID: 20260128_0002
Revises: 20260128_0001
Create Date: 2026-01-28 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20260128_0002'
down_revision: Union[str, None] = '20260128_0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add missing fields to variables table:
    - label: Display label (e.g., "Taxa de Conversão")
    - description: Detailed description
    - controllability: Degree of control (none, low, medium, high)
    - is_intervention: Whether this is the intervention variable
    - is_outcome: Whether this is an outcome variable
    - is_critical_uncertainty: Whether this is a critical uncertainty
    - position_x, position_y: UI position coordinates
    - unit: Unit of measurement (optional)
    """
    # Add label column (display name)
    op.add_column(
        'variables',
        sa.Column('label', sa.String(length=255), nullable=True)
    )

    # Add description column
    op.add_column(
        'variables',
        sa.Column('description', sa.Text(), nullable=True)
    )

    # Add controllability column (replaces boolean 'controllable')
    op.add_column(
        'variables',
        sa.Column('controllability', sa.String(length=20), nullable=True)
    )

    # Add intervention flag
    op.add_column(
        'variables',
        sa.Column('is_intervention', sa.Boolean(), nullable=False, server_default='false')
    )

    # Add outcome flag
    op.add_column(
        'variables',
        sa.Column('is_outcome', sa.Boolean(), nullable=False, server_default='false')
    )

    # Add critical uncertainty flag
    op.add_column(
        'variables',
        sa.Column('is_critical_uncertainty', sa.Boolean(), nullable=False, server_default='false')
    )

    # Add position coordinates for UI
    op.add_column(
        'variables',
        sa.Column('position_x', sa.Float(), nullable=True)
    )

    op.add_column(
        'variables',
        sa.Column('position_y', sa.Float(), nullable=True)
    )

    # Add unit of measurement
    op.add_column(
        'variables',
        sa.Column('unit', sa.String(length=50), nullable=True)
    )

    # Migrate controllable boolean to controllability string
    op.execute("""
        UPDATE variables
        SET controllability = CASE
            WHEN controllable = true THEN 'medium'
            ELSE 'none'
        END
    """)

    # Populate label from name (Title Case) for existing records
    op.execute("""
        UPDATE variables
        SET label = INITCAP(REPLACE(name, '_', ' '))
        WHERE label IS NULL
    """)


def downgrade() -> None:
    """Drop added fields from variables table."""
    op.drop_column('variables', 'unit')
    op.drop_column('variables', 'position_y')
    op.drop_column('variables', 'position_x')
    op.drop_column('variables', 'is_critical_uncertainty')
    op.drop_column('variables', 'is_outcome')
    op.drop_column('variables', 'is_intervention')
    op.drop_column('variables', 'controllability')
    op.drop_column('variables', 'description')
    op.drop_column('variables', 'label')
