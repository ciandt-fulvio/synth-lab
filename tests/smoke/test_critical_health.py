"""
Smoke tests - Health checks críticos que devem SEMPRE passar.

Estes são os testes mais rápidos (~5s total) que validam que:
- Banco de dados está acessível
- Configurações críticas estão presentes
- Imports essenciais funcionam
- Serviços externos básicos estão configurados

Executar: pytest -m smoke
"""

import os
import sys
from pathlib import Path

import pytest
from sqlalchemy import text


@pytest.mark.smoke
class TestDatabaseHealth:
    """Valida que banco de dados está acessível e configurado."""

    def test_database_url_is_configured(self):
        """DATABASE_URL deve estar configurada."""
        database_url = os.getenv("DATABASE_URL")
        assert database_url is not None, (
            "DATABASE_URL não configurada! "
            "Configure com: export DATABASE_URL='postgresql://...'"
        )
        assert database_url.startswith("postgresql"), (
            f"DATABASE_URL deve ser PostgreSQL. Got: {database_url[:20]}"
        )

    def test_database_connection_works(self):
        """Consegue conectar ao banco de dados."""
        from synth_lab.infrastructure.database_v2 import create_db_engine

        engine = create_db_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            assert result == 1, "Query básica falhou"

    def test_database_has_tables(self):
        """Banco de dados tem tabelas essenciais criadas."""
        from sqlalchemy import inspect
        from synth_lab.infrastructure.database_v2 import create_db_engine

        engine = create_db_engine()
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        # Tabelas essenciais devem existir
        essential_tables = ["experiments", "synths"]
        for table in essential_tables:
            assert table in tables, (
                f"Tabela '{table}' não existe! "
                f"Execute as migrations: alembic upgrade head"
            )


@pytest.mark.smoke
class TestLLMClientHealth:
    """Valida que cliente LLM está configurado."""

    def test_openai_api_key_is_configured(self):
        """OPENAI_API_KEY deve estar configurada."""
        api_key = os.getenv("OPENAI_API_KEY")
        assert api_key is not None, (
            "OPENAI_API_KEY não configurada! "
            "Configure com: export OPENAI_API_KEY='sk-...'"
        )
        assert api_key.startswith("sk-"), (
            "OPENAI_API_KEY deve começar com 'sk-'"
        )

    def test_llm_client_can_be_created(self):
        """Cliente LLM pode ser instanciado."""
        from synth_lab.infrastructure.llm_client import get_llm_client

        client = get_llm_client()
        assert client is not None, "get_llm_client() retornou None"
        assert hasattr(client, "complete"), "Cliente não tem método 'complete'"


@pytest.mark.smoke
class TestCriticalImports:
    """Valida que imports críticos funcionam sem erro."""

    def test_can_import_api_main(self):
        """FastAPI app pode ser importada."""
        try:
            from synth_lab.api.main import app

            assert app is not None
        except Exception as e:
            pytest.fail(f"Falha ao importar API: {e}")

    def test_can_import_domain_entities(self):
        """Entities de domínio podem ser importadas."""
        try:
            from synth_lab.domain.entities import Experiment, SynthGroup

            assert Experiment is not None
            assert SynthGroup is not None
        except Exception as e:
            pytest.fail(f"Falha ao importar entities: {e}")

    def test_can_import_key_services(self):
        """Serviços críticos podem ser importados."""
        try:
            from synth_lab.services.insight_service import InsightService

            assert InsightService is not None
        except Exception as e:
            pytest.fail(f"Falha ao importar services: {e}")


@pytest.mark.smoke
class TestProjectStructure:
    """Valida que estrutura de diretórios está correta."""

    def test_data_directory_exists(self):
        """Diretório data/ existe com arquivos de configuração."""
        from synth_lab.infrastructure.config import DATA_DIR

        assert DATA_DIR.exists(), f"DATA_DIR não existe: {DATA_DIR}"
        assert DATA_DIR.is_dir(), f"DATA_DIR não é diretório: {DATA_DIR}"

        # Arquivos de config essenciais
        config_dir = DATA_DIR / "config"
        assert config_dir.exists(), "data/config/ não existe"

        essential_configs = [
            "ibge_distributions.json",
            "occupations_structured.json",
        ]
        for config_file in essential_configs:
            config_path = config_dir / config_file
            assert config_path.exists(), (
                f"Config essencial não encontrado: {config_path}"
            )

    def test_output_directory_accessible(self):
        """Diretório output/ é acessível para escrita."""
        from synth_lab.infrastructure.config import OUTPUT_DIR

        assert OUTPUT_DIR.exists() or OUTPUT_DIR.parent.exists(), (
            f"OUTPUT_DIR ou seu parent deve existir: {OUTPUT_DIR}"
        )


@pytest.mark.smoke
class TestPhoenixTracing:
    """Valida que Phoenix tracing está configurado (opcional mas recomendado)."""

    def test_phoenix_imports_work(self):
        """Phoenix tracing pode ser importado."""
        try:
            from synth_lab.infrastructure.phoenix_tracing import (
                setup_phoenix_tracing,
            )

            assert setup_phoenix_tracing is not None
        except Exception as e:
            pytest.fail(f"Falha ao importar phoenix_tracing: {e}")


@pytest.mark.smoke
class TestBasicCRUD:
    """Valida operações CRUD básicas no banco de dados."""

    def test_can_insert_and_read_experiment(self):
        """Consegue criar e ler um experimento básico."""
        from sqlalchemy import text
        from synth_lab.infrastructure.database_v2 import create_db_engine
        import uuid

        engine = create_db_engine()
        test_exp_id = f"test-exp-{uuid.uuid4()}"
        test_group_id = f"test-group-{uuid.uuid4()}"

        with engine.begin() as conn:
            # Create test synth_group first (FK dependency)
            conn.execute(
                text(
                    "INSERT INTO synth_groups (id, name, created_at) "
                    "VALUES (:id, :name, NOW())"
                ),
                {
                    "id": test_group_id,
                    "name": "Test Group",
                },
            )

            # Insert experiment
            conn.execute(
                text(
                    "INSERT INTO experiments (id, name, hypothesis, status, synth_group_id, created_at) "
                    "VALUES (:id, :name, :hypothesis, :status, :synth_group_id, NOW())"
                ),
                {
                    "id": test_exp_id,
                    "name": "Test Experiment",
                    "hypothesis": "Test hypothesis",
                    "status": "draft",
                    "synth_group_id": test_group_id,
                },
            )

            # Read
            result = conn.execute(
                text("SELECT name, hypothesis FROM experiments WHERE id = :id"),
                {"id": test_exp_id},
            ).first()

            assert result is not None, "Falha ao ler experimento criado"
            assert result[0] == "Test Experiment"
            assert result[1] == "Test hypothesis"

            # Cleanup (experiments first due to FK, then synth_groups)
            conn.execute(text("DELETE FROM experiments WHERE id = :id"), {"id": test_exp_id})
            conn.execute(text("DELETE FROM synth_groups WHERE id = :id"), {"id": test_group_id})


@pytest.mark.smoke
class TestAPIRoutesRegistered:
    """Valida que rotas principais da API estão registradas."""

    def test_main_routes_are_registered(self):
        """Rotas essenciais devem estar registradas no app."""
        from synth_lab.api.main import app

        routes = [route.path for route in app.routes]

        essential_routes = [
            "/experiments/list",
            "/experiments/{experiment_id}",
            "/synth-groups/list",
        ]

        for route in essential_routes:
            assert route in routes, (
                f"Rota essencial '{route}' não está registrada! "
                f"Frontend pode quebrar se esta rota não existir."
            )


# Validation block para executar standalone
if __name__ == "__main__":
    import subprocess

    all_validation_failures = []
    total_tests = 0

    print("=" * 60)
    print("SMOKE TESTS - Validação de Health Checks Críticos")
    print("=" * 60)

    # Executa os smoke tests
    result = subprocess.run(
        ["pytest", "-m", "smoke", "-v", __file__],
        capture_output=True,
        text=True,
    )

    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode != 0:
        all_validation_failures.append("Smoke tests falharam")

    # Final validation result
    if all_validation_failures:
        print("\n" + "=" * 60)
        print("❌ VALIDATION FAILED - Smoke tests falharam")
        print("=" * 60)
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print("\n" + "=" * 60)
        print("✅ VALIDATION PASSED - Todos os smoke tests passaram")
        print("=" * 60)
        print("Sistema está saudável e pronto para uso")
        sys.exit(0)
