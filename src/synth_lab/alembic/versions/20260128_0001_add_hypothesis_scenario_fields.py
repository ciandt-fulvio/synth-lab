"""Add hypothesis scenario fields

Revision ID: 20260128_0001
Revises: 20260126_0001
Create Date: 2026-01-28 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260128_0001'
down_revision: Union[str, None] = '20260126_0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add scenario-related fields to hypotheses table:
    - variable_name: Cached variable name for convenience
    - scenario_options: JSONB array of scenario options for controllable variables
    - selected_scenario: Currently selected scenario value
    """
    # Add variable_name column (cached for convenience, derived from variable_id)
    op.add_column(
        'hypotheses',
        sa.Column('variable_name', sa.String(length=255), nullable=True)
    )

    # Add scenario_options column (JSONB array of ScenarioOption objects)
    op.add_column(
        'hypotheses',
        sa.Column('scenario_options', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )

    # Add selected_scenario column (string value referencing ScenarioOption.value)
    op.add_column(
        'hypotheses',
        sa.Column('selected_scenario', sa.String(length=50), nullable=True)
    )

    # Populate variable_name from variables table (for existing records)
    op.execute("""
        UPDATE hypotheses h
        SET variable_name = v.name
        FROM variables v
        WHERE h.variable_id = v.id
    """)


def downgrade() -> None:
    """Drop scenario-related fields from hypotheses table."""
    op.drop_column('hypotheses', 'selected_scenario')
    op.drop_column('hypotheses', 'scenario_options')
    op.drop_column('hypotheses', 'variable_name')
