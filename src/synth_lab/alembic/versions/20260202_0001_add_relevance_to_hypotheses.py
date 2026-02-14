"""Add relevance column to hypotheses table

Revision ID: 20260202_0001
Revises: 20260128_0002
Create Date: 2026-02-02 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '20260202_0001'
down_revision: Union[str, None] = '20260128_0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add relevance column with default 'medium' for backward compatibility."""
    op.add_column(
        'hypotheses',
        sa.Column(
            'relevance',
            sa.String(10),
            nullable=False,
            server_default='medium',
        ),
    )


def downgrade() -> None:
    """Remove relevance column."""
    op.drop_column('hypotheses', 'relevance')
