#!/usr/bin/env python3
"""
Seed mechanism definitions, options, and feature types.

Populates the database with the initial 6 mechanisms, 30 options (5 per mechanism),
and 5 feature types as defined in the spec.

Usage:
    DATABASE_URL=<url> python scripts/seed_mechanisms.py

References:
    - Spec: specs/039-narrative-mechanism-config/research.md#seed-data
    - Data model: specs/039-narrative-mechanism-config/data-model.md
"""

import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from synth_lab.infrastructure.database_v2 import create_db_engine


def generate_mechanism_id() -> str:
    """Generate a UUID for mechanism entities."""
    return str(uuid.uuid4())


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
        "key": "intrinsic_value",
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
        "key": "operational_friction",
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
        "key": "frequency_of_use",
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


def _check_mechanisms_exist(db_url: str) -> bool:
    """Check if mechanism_definitions table has any records."""
    engine = create_db_engine(db_url)
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT COUNT(*) FROM mechanism_definitions")
            )
            count = result.scalar()
            return count > 0
    except Exception:
        return False
    finally:
        engine.dispose()


def seed_mechanisms(db_url: str) -> None:
    """Seed mechanism definitions, options, and feature types."""
    engine = create_db_engine(db_url)

    try:
        with engine.begin() as conn:
            # Insert mechanism definitions and options
            for mech in MECHANISM_DEFINITIONS:
                mech_id = generate_mechanism_id()

                conn.execute(
                    text("""
                        INSERT INTO mechanism_definitions (id, key, label_pt, description)
                        VALUES (:id, :key, :label_pt, :description)
                        ON CONFLICT (key) DO NOTHING
                    """),
                    {
                        "id": mech_id,
                        "key": mech["key"],
                        "label_pt": mech["label_pt"],
                        "description": mech["description"],
                    },
                )

                # Get the mechanism ID (in case it already existed)
                result = conn.execute(
                    text("SELECT id FROM mechanism_definitions WHERE key = :key"),
                    {"key": mech["key"]},
                )
                actual_mech_id = result.scalar()

                # Insert options
                for opt in mech["options"]:
                    opt_id = generate_mechanism_id()
                    conn.execute(
                        text("""
                            INSERT INTO mechanism_options (id, mechanism_id, label, value, display_order)
                            VALUES (:id, :mechanism_id, :label, :value, :display_order)
                            ON CONFLICT DO NOTHING
                        """),
                        {
                            "id": opt_id,
                            "mechanism_id": actual_mech_id,
                            "label": opt["label"],
                            "value": opt["value"],
                            "display_order": opt["display_order"],
                        },
                    )

                print(f"  ✓ {mech['key']}: {len(mech['options'])} options")

            # Insert feature types
            print("")
            print("Seeding feature types...")
            for ft in FEATURE_TYPES:
                ft_id = generate_mechanism_id()
                import json

                conn.execute(
                    text("""
                        INSERT INTO feature_types (id, key, label_pt, description, amplifies_mechanisms)
                        VALUES (:id, :key, :label_pt, :description, :amplifies_mechanisms)
                        ON CONFLICT (key) DO NOTHING
                    """),
                    {
                        "id": ft_id,
                        "key": ft["key"],
                        "label_pt": ft["label_pt"],
                        "description": ft["description"],
                        "amplifies_mechanisms": json.dumps(ft["amplifies_mechanisms"]),
                    },
                )
                print(f"  ✓ {ft['key']}: amplifies {ft['amplifies_mechanisms']}")

    finally:
        engine.dispose()


def main() -> None:
    """Main entry point for seeding mechanisms."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ ERROR: DATABASE_URL environment variable not set", file=sys.stderr)
        print("", file=sys.stderr)
        print("Usage:", file=sys.stderr)
        print("  DATABASE_URL=<url> python scripts/seed_mechanisms.py", file=sys.stderr)
        sys.exit(1)

    print(f"🔧 Seeding mechanisms to: {db_url.split('@')[-1]}")
    print("")

    # Check if already seeded
    if _check_mechanisms_exist(db_url):
        print("ℹ️  Mechanisms already exist in database")
        print("   Skipping seed to preserve existing data")
        print("")
        print("✅ Seed skipped - mechanisms already exist")
        sys.exit(0)

    print("Seeding mechanism definitions...")
    seed_mechanisms(db_url)
    print("")
    print("✅ Mechanisms seeded successfully!")
    print("")
    print("Summary:")
    print(f"  - {len(MECHANISM_DEFINITIONS)} mechanism definitions")
    print(f"  - {sum(len(m['options']) for m in MECHANISM_DEFINITIONS)} mechanism options")
    print(f"  - {len(FEATURE_TYPES)} feature types")


if __name__ == "__main__":
    main()
