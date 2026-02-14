"""merge auth and ownership branches

Revision ID: cb21bd0e1556
Revises: 4ed1cc72a059, 3cc6321a86c9
Create Date: 2026-01-23 09:52:54.149763
"""
from typing import Sequence, Union

# revision identifiers, used by Alembic
revision: str = 'cb21bd0e1556'
down_revision: Union[str, None] = ('4ed1cc72a059', '3cc6321a86c9')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    pass


def downgrade() -> None:
    """Downgrade database schema."""
    pass
