"""seed_mechanism_data

Revision ID: 933673a892f5
Revises: 21d9e0896964
Create Date: 2026-02-09 11:43:36.585406

Feature: 039-narrative-mechanism-config
Seeds initial mechanism definitions, options, and feature types.

This migration populates the mechanism tables with the initial configuration
required for the narrative generation feature to work.
"""
import json
import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import column, table
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic
revision: str = '933673a892f5'
down_revision: Union[str, None] = '21d9e0896964'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ============================================================================
# Seed Data Definitions
# ============================================================================

MECHANISM_DEFINITIONS = [
    {
        "key": "irreversibility",
        "label_pt": "Irreversibilidade",
        "description": "Grau em que a ação não pode ser desfeita",
        "options": [
            {"label": "totalmente reversível", "value": 0.00, "display_order": 1},
            {"label": "reversível com algum esforço", "value": 0.25, "display_order": 2},
            {"label": "parcialmente reversível", "value": 0.50, "display_order": 3},
            {"label": "difícil de reverter", "value": 0.75, "display_order": 4},
            {"label": "irreversível", "value": 1.00, "display_order": 5},
        ],
    },
    {
        "key": "network_effect",
        "label_pt": "Efeito de Rede",
        "description": "Grau em que o valor depende de outros usarem",
        "options": [
            {"label": "funciona independentemente", "value": 0.00, "display_order": 1},
            {"label": "melhora levemente com mais usuários", "value": 0.25, "display_order": 2},
            {"label": "beneficia-se moderadamente da rede", "value": 0.50, "display_order": 3},
            {"label": "muito melhor com mais pessoas", "value": 0.75, "display_order": 4},
            {"label": "só funciona com massa crítica", "value": 1.00, "display_order": 5},
        ],
    },
    {
        "key": "institutional_trust",
        "label_pt": "Confiança Institucional",
        "description": "Grau em que requer confiar na instituição",
        "options": [
            {"label": "não requer confiança especial", "value": 0.00, "display_order": 1},
            {"label": "requer confiança básica", "value": 0.25, "display_order": 2},
            {"label": "requer confiança moderada", "value": 0.50, "display_order": 3},
            {"label": "requer alta confiança", "value": 0.75, "display_order": 4},
            {"label": "requer confiança total na instituição", "value": 1.00, "display_order": 5},
        ],
    },
    {
        "key": "habit_displacement",
        "label_pt": "Substituição de Hábito",
        "description": "Grau em que substitui hábitos existentes",
        "options": [
            {"label": "não altera hábitos", "value": 0.00, "display_order": 1},
            {"label": "ajuste mínimo de rotina", "value": 0.25, "display_order": 2},
            {"label": "requer mudança moderada", "value": 0.50, "display_order": 3},
            {"label": "substitui hábito significativo", "value": 0.75, "display_order": 4},
            {"label": "substitui completamente um hábito", "value": 1.00, "display_order": 5},
        ],
    },
    {
        "key": "learning_curve",
        "label_pt": "Curva de Aprendizado",
        "description": "Grau em que requer aprender algo novo",
        "options": [
            {"label": "intuitivo, sem aprendizado", "value": 0.00, "display_order": 1},
            {"label": "aprendizado mínimo", "value": 0.25, "display_order": 2},
            {"label": "requer alguma prática", "value": 0.50, "display_order": 3},
            {"label": "curva de aprendizado significativa", "value": 0.75, "display_order": 4},
            {"label": "requer treinamento extensivo", "value": 1.00, "display_order": 5},
        ],
    },
    {
        "key": "social_visibility",
        "label_pt": "Visibilidade Social",
        "description": "Grau em que o uso é visível para outros",
        "options": [
            {"label": "totalmente privado", "value": 0.00, "display_order": 1},
            {"label": "visível apenas para poucos", "value": 0.25, "display_order": 2},
            {"label": "moderadamente visível", "value": 0.50, "display_order": 3},
            {"label": "visível para muitos", "value": 0.75, "display_order": 4},
            {"label": "totalmente público", "value": 1.00, "display_order": 5},
        ],
    },
    {
        "key": "valor_intrinseco",
        "label_pt": "Valor Intrínseco",
        "description": "Grau em que a feature melhora a vida real do usuário",
        "options": [
            {"label": "cosmético", "value": 0.00, "display_order": 1},
            {"label": "conveniência menor", "value": 0.25, "display_order": 2},
            {"label": "melhoria moderada", "value": 0.50, "display_order": 3},
            {"label": "melhoria significativa", "value": 0.75, "display_order": 4},
            {"label": "transformador", "value": 1.00, "display_order": 5},
        ],
    },
    {
        "key": "friccao_operacional",
        "label_pt": "Fricção Operacional",
        "description": "Grau de fricção/etapas/erros no uso cotidiano",
        "options": [
            {"label": "sem fricção", "value": 0.00, "display_order": 1},
            {"label": "fricção mínima", "value": 0.25, "display_order": 2},
            {"label": "fricção moderada", "value": 0.50, "display_order": 3},
            {"label": "fricção significativa", "value": 0.75, "display_order": 4},
            {"label": "fricção extrema", "value": 1.00, "display_order": 5},
        ],
    },
    {
        "key": "frequencia_de_uso",
        "label_pt": "Frequência de Uso",
        "description": "Frequência esperada de uso da feature",
        "options": [
            {"label": "raríssimo", "value": 0.00, "display_order": 1},
            {"label": "ocasional", "value": 0.25, "display_order": 2},
            {"label": "semanal", "value": 0.50, "display_order": 3},
            {"label": "quase diário", "value": 0.75, "display_order": 4},
            {"label": "diário ou mais", "value": 1.00, "display_order": 5},
        ],
    },
]

FEATURE_TYPES = [
    {
        "key": "financial",
        "label_pt": "Financeira",
        "description": "Features que envolvem transações financeiras",
        "amplifies_mechanisms": ["irreversibility", "institutional_trust"],
    },
    {
        "key": "social",
        "label_pt": "Social",
        "description": "Features com componente social ou de rede",
        "amplifies_mechanisms": ["network_effect", "social_visibility"],
    },
    {
        "key": "aesthetic",
        "label_pt": "Estética",
        "description": "Features focadas em aparência ou personalização",
        "amplifies_mechanisms": [],
    },
    {
        "key": "flow",
        "label_pt": "Fluxo",
        "description": "Features que alteram fluxos de trabalho ou processos",
        "amplifies_mechanisms": ["learning_curve", "habit_displacement"],
    },
    {
        "key": "infra",
        "label_pt": "Infraestrutura",
        "description": "Features de infraestrutura ou integração",
        "amplifies_mechanisms": ["institutional_trust"],
    },
]


def upgrade() -> None:
    """Seed mechanism definitions, options, and feature types."""
    conn = op.get_bind()

    # Define table structures for bulk insert
    mechanism_definitions_table = table(
        'mechanism_definitions',
        column('id', UUID),
        column('key', sa.String),
        column('label_pt', sa.String),
        column('description', sa.Text),
    )

    mechanism_options_table = table(
        'mechanism_options',
        column('id', UUID),
        column('mechanism_id', UUID),
        column('label', sa.String),
        column('value', sa.Numeric),
        column('display_order', sa.Integer),
    )

    feature_types_table = table(
        'feature_types',
        column('id', UUID),
        column('key', sa.String),
        column('label_pt', sa.String),
        column('description', sa.Text),
        column('amplifies_mechanisms', sa.Text),  # Will be JSON string
    )

    # Insert mechanism definitions and options
    for mech in MECHANISM_DEFINITIONS:
        mech_id = str(uuid.uuid4())

        # Insert mechanism definition
        op.bulk_insert(
            mechanism_definitions_table,
            [
                {
                    "id": mech_id,
                    "key": mech["key"],
                    "label_pt": mech["label_pt"],
                    "description": mech["description"],
                }
            ],
        )

        # Insert options for this mechanism
        options_data = [
            {
                "id": str(uuid.uuid4()),
                "mechanism_id": mech_id,
                "label": opt["label"],
                "value": opt["value"],
                "display_order": opt["display_order"],
            }
            for opt in mech["options"]
        ]
        op.bulk_insert(mechanism_options_table, options_data)

    # Insert feature types
    feature_types_data = [
        {
            "id": str(uuid.uuid4()),
            "key": ft["key"],
            "label_pt": ft["label_pt"],
            "description": ft["description"],
            "amplifies_mechanisms": json.dumps(ft["amplifies_mechanisms"]),
        }
        for ft in FEATURE_TYPES
    ]
    op.bulk_insert(feature_types_table, feature_types_data)


def downgrade() -> None:
    """Remove seeded mechanism data."""
    # Delete all seeded data (in reverse order due to FK constraints)
    op.execute("DELETE FROM mechanism_options")
    op.execute("DELETE FROM mechanism_definitions")
    op.execute("DELETE FROM feature_types")
