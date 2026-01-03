"""Merge heads: schema sync and source_id

Revision ID: f28fd615d2a9
Revises: 103d7ca69596, add_source_id
Create Date: 2026-01-03 16:53:47.532533
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision: str = 'f28fd615d2a9'
down_revision: Union[str, None] = ('103d7ca69596', 'add_source_id')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    pass


def downgrade() -> None:
    """Downgrade database schema."""
    pass
