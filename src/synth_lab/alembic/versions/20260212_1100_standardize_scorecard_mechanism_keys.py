"""standardize_scorecard_mechanism_keys_to_english

Renames Portuguese mechanism keys in experiments.scorecard_data->'mechanisms'
JSONB to English equivalents, matching the mechanism_definitions table keys.

Keys renamed:
    valor_intrinseco    -> intrinsic_value
    friccao_operacional -> operational_friction
    frequencia_de_uso   -> frequency_of_use

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-02-12 11:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic
revision: str = "b3c4d5e6f7a8"
down_revision: Union[str, None] = "a2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (old_key, new_key) pairs
_RENAMES = [
    ("valor_intrinseco", "intrinsic_value"),
    ("friccao_operacional", "operational_friction"),
    ("frequencia_de_uso", "frequency_of_use"),
]


def upgrade() -> None:
    """Rename PT mechanism keys to EN in experiments.scorecard_data JSONB."""
    for old_key, new_key in _RENAMES:
        op.execute(f"""
            UPDATE experiments
            SET scorecard_data = jsonb_set(
                scorecard_data #- '{{mechanisms,{old_key}}}',
                '{{mechanisms,{new_key}}}',
                scorecard_data->'mechanisms'->'{old_key}'
            )
            WHERE scorecard_data->'mechanisms'->>'{old_key}' IS NOT NULL;
        """)


def downgrade() -> None:
    """Revert EN mechanism keys to PT in experiments.scorecard_data JSONB."""
    for old_key, new_key in _RENAMES:
        op.execute(f"""
            UPDATE experiments
            SET scorecard_data = jsonb_set(
                scorecard_data #- '{{mechanisms,{new_key}}}',
                '{{mechanisms,{old_key}}}',
                scorecard_data->'mechanisms'->'{new_key}'
            )
            WHERE scorecard_data->'mechanisms'->>'{new_key}' IS NOT NULL;
        """)
