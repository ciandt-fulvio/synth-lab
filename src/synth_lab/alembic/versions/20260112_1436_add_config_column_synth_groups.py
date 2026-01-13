"""add config column to synth_groups table

Revision ID: add_config_synth_groups
Revises: 09d318020a17
Create Date: 2026-01-12 14:36:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic
revision: str = "add_config_synth_groups"
down_revision: Union[str, None] = "09d318020a17"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Default IBGE configuration for the Default group
DEFAULT_IBGE_CONFIG = {
    "n_synths": 500,
    "distributions": {
        "idade": {"15-29": 0.26, "30-44": 0.27, "45-59": 0.24, "60+": 0.23},
        "escolaridade": {
            "sem_instrucao": 0.068,
            "fundamental": 0.329,
            "medio": 0.314,
            "superior": 0.289,
        },
        "deficiencias": {
            "taxa_com_deficiencia": 0.084,
            "distribuicao_severidade": {
                "nenhuma": 0.20,
                "leve": 0.20,
                "moderada": 0.20,
                "severa": 0.20,
                "total": 0.20,
            },
        },
        "composicao_familiar": {
            "unipessoal": 0.15,
            "casal_sem_filhos": 0.20,
            "casal_com_filhos": 0.35,
            "monoparental": 0.18,
            "multigeracional": 0.12,
        },
        "domain_expertise": {"alpha": 3, "beta": 3},
    },
}


def upgrade() -> None:
    """Add config JSONB column to synth_groups table."""
    # Add config column as JSONB (nullable for backward compatibility)
    op.add_column(
        "synth_groups",
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    # Create GIN index for efficient JSONB queries
    op.create_index(
        "idx_synth_groups_config",
        "synth_groups",
        ["config"],
        postgresql_using="gin",
    )

    # Update Default group with IBGE config
    import json

    op.execute(
        f"""
        UPDATE synth_groups
        SET config = '{json.dumps(DEFAULT_IBGE_CONFIG)}'::jsonb
        WHERE id = 'grp_00000001' OR name = 'Default'
        """
    )


def downgrade() -> None:
    """Remove config column from synth_groups table."""
    op.drop_index("idx_synth_groups_config", table_name="synth_groups")
    op.drop_column("synth_groups", "config")
