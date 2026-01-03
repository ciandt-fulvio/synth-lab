"""
Migration tests - Valida que migrations do Alembic estão corretas.

Estes testes garantem que:
- Models estão sincronizados com a última migration (head)
- Não há mudanças em models sem migration correspondente
- Migrations podem ser aplicadas sem erro

Executar: pytest -m schema

CRÍTICO: Se este teste falha com "Models divergem do DB", significa que:
- Alguém mudou um model SEM criar migration
- Ação: alembic revision --autogenerate -m "Descrição da mudança"

Requer: DATABASE_URL_TEST environment variable.
"""

import os
import sys

import pytest
from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory

from synth_lab.infrastructure.database_v2 import create_db_engine
from synth_lab.models.orm.base import Base


@pytest.fixture(scope="module")
def db_engine():
    """Create database engine using DATABASE_URL_TEST."""
    database_url = os.getenv("DATABASE_URL_TEST")
    if not database_url:
        pytest.skip("DATABASE_URL_TEST not set")
    return create_db_engine(database_url)


@pytest.fixture(scope="module")
def alembic_config():
    """Get Alembic configuration."""
    config = Config("src/synth_lab/alembic/alembic.ini")
    config.set_main_option("script_location", "src/synth_lab/alembic")
    return config


@pytest.mark.schema
class TestMigrations:
    """Testes de migrations do Alembic."""

    def test_models_match_migration_head(self, db_engine):
        """
        CRÍTICO: Detecta mudanças em models sem migration.

        Se este teste FALHA:
        - Alguém mudou um model (mudou tipo de coluna, adicionou campo, etc.)
        - MAS não criou a migration correspondente
        - Isso vai quebrar em produção quando deploy for feito

        SOLUÇÃO:
        alembic revision --autogenerate -m "Descrição da mudança"
        """
        with db_engine.connect() as connection:
            context = MigrationContext.configure(connection)

            # Compara metadata dos models com o DB atual
            from alembic.autogenerate import compare_metadata

            diff = compare_metadata(context, Base.metadata)

            if diff:
                print("\n" + "=" * 60)
                print("❌ MUDANÇAS DETECTADAS EM MODELS SEM MIGRATION:")
                print("=" * 60)
                for item in diff:
                    print(f"  - {item}")
                print("\n")
                print("AÇÃO NECESSÁRIA:")
                print(
                    "  alembic revision --autogenerate -m 'Descrição da mudança'"
                )
                print("=" * 60)

            assert not diff, (
                f"Models divergem do DB! {len(diff)} mudança(s) detectada(s). "
                f"Crie migration: alembic revision --autogenerate"
            )

    def test_current_migration_is_head(self, db_engine, alembic_config):
        """Verifica que DB está na última versão das migrations."""
        with db_engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()

            # Pega a versão head
            script = ScriptDirectory.from_config(alembic_config)
            head_rev = script.get_current_head()

            assert current_rev == head_rev, (
                f"DB está desatualizado! "
                f"Versão atual: {current_rev}, "
                f"Versão esperada (head): {head_rev}. "
                f"Execute: alembic upgrade head"
            )

    def test_alembic_version_table_exists(self, db_engine):
        """Tabela alembic_version deve existir."""
        from sqlalchemy import inspect

        inspector = inspect(db_engine)
        tables = inspector.get_table_names()

        assert "alembic_version" in tables, (
            "Tabela 'alembic_version' não existe! "
            "Migrations nunca foram executadas. "
            "Execute: alembic upgrade head"
        )


# Validation block
if __name__ == "__main__":
    import subprocess

    print("=" * 60)
    print("MIGRATION TESTS - Validação de Alembic Migrations")
    print("=" * 60)

    result = subprocess.run(
        ["pytest", "-m", "schema", "-v", __file__],
        capture_output=True,
        text=True,
    )

    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode != 0:
        print("\n" + "=" * 60)
        print("❌ MIGRATION TESTS FAILED")
        print("=" * 60)
        sys.exit(1)
    else:
        print("\n" + "=" * 60)
        print("✅ MIGRATIONS OK - Models sincronizados com DB")
        print("=" * 60)
        sys.exit(0)
