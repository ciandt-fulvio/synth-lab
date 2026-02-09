"""standardize_mechanism_keys_to_english

Revision ID: 1d3d2218f612
Revises: 933673a892f5
Create Date: 2026-02-09 13:16:06.551404
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision: str = '1d3d2218f612'
down_revision: Union[str, None] = '933673a892f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema - standardize mechanism keys to English."""
    # Update mechanism keys from Portuguese to English
    op.execute("""
        UPDATE mechanism_definitions
        SET key = 'intrinsic_value'
        WHERE key = 'valor_intrinseco';
    """)

    op.execute("""
        UPDATE mechanism_definitions
        SET key = 'operational_friction'
        WHERE key = 'friccao_operacional';
    """)

    op.execute("""
        UPDATE mechanism_definitions
        SET key = 'frequency_of_use'
        WHERE key = 'frequencia_de_uso';
    """)


def downgrade() -> None:
    """Downgrade database schema - revert to Portuguese keys."""
    # Revert mechanism keys from English to Portuguese
    op.execute("""
        UPDATE mechanism_definitions
        SET key = 'valor_intrinseco'
        WHERE key = 'intrinsic_value';
    """)

    op.execute("""
        UPDATE mechanism_definitions
        SET key = 'friccao_operacional'
        WHERE key = 'operational_friction';
    """)

    op.execute("""
        UPDATE mechanism_definitions
        SET key = 'frequencia_de_uso'
        WHERE key = 'frequency_of_use';
    """)
