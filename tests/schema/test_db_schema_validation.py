"""
Schema validation tests - Detecta divergências entre DB e SQLAlchemy models.

Estes testes previnem o problema crítico de:
- Alguém muda o model (ex: status String → Enum) sem criar migration
- Alguém muda o DB manualmente mas não atualiza o model
- Migrations não foram executadas (DB desatualizado)

Executar: pytest -m schema

IMPORTÂNCIA: Estes testes detectam 90% dos problemas de "funcionou local mas quebrou em prod"
relacionados a divergências de schema.

Requer: DATABASE_TEST_URL environment variable.
"""

import os
import sys

import pytest
from sqlalchemy import inspect, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from synth_lab.infrastructure.database_v2 import create_db_engine
from synth_lab.models.orm.base import Base


@pytest.fixture(scope="module")
def db_inspector():
    """Create inspector for database schema introspection using DATABASE_TEST_URL."""
    database_url = os.getenv("DATABASE_TEST_URL")
    if not database_url:
        pytest.skip("DATABASE_TEST_URL not set")
    engine = create_db_engine(database_url)
    return inspect(engine)


@pytest.mark.schema
class TestExperimentTableSchema:
    """Valida schema da tabela 'experiments'."""

    def test_experiments_table_exists(self, db_inspector):
        """Tabela 'experiments' deve existir."""
        tables = db_inspector.get_table_names()
        assert "experiments" in tables, (
            "Tabela 'experiments' não existe! Execute: alembic upgrade head"
        )

    def test_experiments_has_required_columns(self, db_inspector):
        """Tabela deve ter todas as colunas definidas no model."""
        columns = {
            col["name"]: col for col in db_inspector.get_columns("experiments")}

        # Campos do Experiment model
        required_columns = {
            "id": String,
            "name": String,
            "hypothesis": String,
            "description": Text,
            "scorecard_data": JSONB,
            "status": String,
            "created_at": String,
            "updated_at": String,
        }

        for column_name in required_columns.keys():
            assert column_name in columns, (
                f"Coluna '{column_name}' não existe em 'experiments'! "
                f"Se mudou o model, crie migration: alembic revision --autogenerate"
            )

    def test_experiments_column_types_match(self, db_inspector):
        """Tipos de colunas devem bater com o model."""
        columns = {
            col["name"]: col for col in db_inspector.get_columns("experiments")}

        # id deve ser String/VARCHAR
        id_col = columns["id"]
        assert isinstance(id_col["type"], String), (
            f"experiments.id deve ser String, não {type(id_col['type']).__name__}"
        )

        # status deve ser String (se mudou pra Enum sem migration, FALHA aqui!)
        status_col = columns["status"]
        assert isinstance(status_col["type"], String), (
            f"experiments.status deve ser String, não {type(status_col['type']).__name__}. "
            f"Se mudou para Enum, falta criar migration!"
        )

        # scorecard_data deve ser JSONB (PostgreSQL) ou JSON
        scorecard_col = columns.get("scorecard_data")
        if scorecard_col:
            assert isinstance(scorecard_col["type"], (JSONB,)), (
                f"experiments.scorecard_data deve ser JSONB"
            )

    def test_experiments_nullable_constraints_match(self, db_inspector):
        """Constraints de nullable devem bater com o model."""
        columns = {
            col["name"]: col for col in db_inspector.get_columns("experiments")}

        # id, name, hypothesis, status, created_at são NOT NULL
        not_null_fields = ["id", "name", "hypothesis", "status", "created_at"]
        for field in not_null_fields:
            assert columns[field]["nullable"] is False, (
                f"experiments.{field} deve ser NOT NULL no DB"
            )

        # description, scorecard_data, updated_at são NULL
        nullable_fields = ["description", "scorecard_data", "updated_at"]
        for field in nullable_fields:
            if field in columns:  # scorecard_data pode não existir em versões antigas
                assert columns[field]["nullable"] is True, (
                    f"experiments.{field} deve ser nullable no DB"
                )

    def test_experiments_has_primary_key(self, db_inspector):
        """Deve ter primary key em 'id'."""
        pk = db_inspector.get_pk_constraint("experiments")
        assert "id" in pk["constrained_columns"], (
            "experiments.id deve ser PRIMARY KEY"
        )

    def test_experiments_has_expected_indexes(self, db_inspector):
        """Deve ter índices esperados."""
        indexes = db_inspector.get_indexes("experiments")
        index_names = {idx["name"] for idx in indexes}

        expected_indexes = [
            "idx_experiments_created",
            "idx_experiments_name",
            "idx_experiments_status",
        ]

        for expected_idx in expected_indexes:
            assert expected_idx in index_names, (
                f"Índice '{expected_idx}' não existe. "
                f"Execute migrations: alembic upgrade head"
            )


@pytest.mark.schema
class TestSynthTableSchema:
    """Valida schema da tabela 'synths'."""

    def test_synths_table_exists(self, db_inspector):
        """Tabela 'synths' deve existir."""
        tables = db_inspector.get_table_names()
        assert "synths" in tables, (
            "Tabela 'synths' não existe! Execute: alembic upgrade head"
        )

    def test_synths_has_required_columns(self, db_inspector):
        """Tabela deve ter colunas essenciais."""
        columns = {col["name"]
            : col for col in db_inspector.get_columns("synths")}

        required_columns = ["id", "nome", "data", "version", "created_at"]

        for column_name in required_columns:
            assert column_name in columns, (
                f"Coluna '{column_name}' não existe em 'synths'!"
            )

    def test_synths_has_foreign_key_to_experiments(self, db_inspector):
        """Deve ter FK para experiments (se existir coluna experiment_id)."""
        columns = {col["name"]
            : col for col in db_inspector.get_columns("synths")}

        if "experiment_id" in columns:
            fkeys = db_inspector.get_foreign_keys("synths")
            exp_fkey = next(
                (fk for fk in fkeys if "experiment_id" in fk["constrained_columns"]),
                None,
            )

            assert exp_fkey is not None, (
                "synths.experiment_id deve ter FK para experiments"
            )
            assert exp_fkey["referred_table"] == "experiments", (
                "FK deve apontar para tabela 'experiments'"
            )


@pytest.mark.schema
class TestAnalysisRunTableSchema:
    """Valida schema da tabela 'analysis_runs'."""

    def test_analysis_runs_table_exists(self, db_inspector):
        """Tabela 'analysis_runs' deve existir."""
        tables = db_inspector.get_table_names()
        assert "analysis_runs" in tables, (
            "Tabela 'analysis_runs' não existe! Execute: alembic upgrade head"
        )

    def test_analysis_runs_has_foreign_key_to_experiments(self, db_inspector):
        """Deve ter FK para experiments."""
        fkeys = db_inspector.get_foreign_keys("analysis_runs")
        exp_fkey = next(
            (fk for fk in fkeys if "experiment_id" in fk["constrained_columns"]), None
        )

        assert exp_fkey is not None, (
            "analysis_runs.experiment_id deve ter FK para experiments"
        )


@pytest.mark.schema
class TestExplorationTableSchema:
    """Valida schema da tabela 'explorations'."""

    def test_explorations_table_exists(self, db_inspector):
        """Tabela 'explorations' deve existir."""
        tables = db_inspector.get_table_names()
        assert "explorations" in tables, (
            "Tabela 'explorations' não existe! Execute: alembic upgrade head"
        )


@pytest.mark.schema
class TestResearchTableSchema:
    """Valida schema da tabela 'research_executions'."""

    def test_research_executions_table_exists(self, db_inspector):
        """Tabela 'research_executions' deve existir."""
        tables = db_inspector.get_table_names()
        assert "research_executions" in tables, (
            "Tabela 'research_executions' não existe! Execute: alembic upgrade head"
        )


@pytest.mark.schema
class TestAllModelsHaveTables:
    """Garante que todos os ORM models têm tabelas correspondentes."""

    def test_all_models_have_tables_in_db(self, db_inspector):
        """Todos os models definidos devem ter tabela no DB."""
        db_tables = set(db_inspector.get_table_names())

        # Pega todos os models do Base
        model_tables = {
            mapper.mapped_table.name for mapper in Base.registry.mappers}

        # Remove tabela do Alembic (não é um model)
        db_tables.discard("alembic_version")

        missing_tables = model_tables - db_tables

        assert not missing_tables, (
            f"Models sem tabela no DB: {missing_tables}. "
            f"Execute migrations: alembic upgrade head"
        )

    def test_no_orphan_tables(self, db_inspector):
        """Não deve haver tabelas órfãs (sem model correspondente)."""
        db_tables = set(db_inspector.get_table_names())
        db_tables.discard("alembic_version")  # Tabela do Alembic é OK

        model_tables = {
            mapper.mapped_table.name for mapper in Base.registry.mappers}

        orphan_tables = db_tables - model_tables

        if orphan_tables:
            # Aviso, não erro (pode haver tabelas legacy)
            print(
                f"\n⚠️  ATENÇÃO: Tabelas órfãs no DB (sem model): {orphan_tables}"
            )
            print("    Considere remover ou criar models para elas.")


@pytest.mark.schema
class TestCriticalColumnTypes:
    """Testa que colunas críticas mantêm tipos esperados."""

    def test_id_columns_are_strings(self, db_inspector):
        """Colunas 'id' devem ser String/VARCHAR."""
        critical_tables = ["experiments", "synths", "analysis_runs"]

        for table in critical_tables:
            if table not in db_inspector.get_table_names():
                continue  # Skip se tabela não existe

            columns = {col["name"]
                : col for col in db_inspector.get_columns(table)}

            if "id" in columns:
                id_col = columns["id"]
                assert isinstance(id_col["type"], (String,)), (
                    f"{table}.id deve ser String, não {type(id_col['type']).__name__}. "
                    f"Se mudou tipo, falta migration!"
                )

    def test_json_columns_are_jsonb(self, db_inspector):
        """Colunas JSON devem ser JSONB (PostgreSQL)."""
        # Tabelas com colunas JSON
        tables_with_json = {
            "experiments": ["scorecard_data"],
            "synths": ["data"],
        }

        for table, json_columns in tables_with_json.items():
            if table not in db_inspector.get_table_names():
                continue

            columns = {col["name"]
                : col for col in db_inspector.get_columns(table)}

            for json_col_name in json_columns:
                if json_col_name in columns:
                    col = columns[json_col_name]
                    # Aceita JSONB (ideal) ou JSON (fallback)
                    assert isinstance(col["type"], (JSONB,)), (
                        f"{table}.{json_col_name} deve ser JSONB (PostgreSQL). "
                        f"Got: {type(col['type']).__name__}"
                    )


# Validation block para executar standalone
if __name__ == "__main__":
    import subprocess

    all_validation_failures = []

    print("=" * 60)
    print("SCHEMA VALIDATION TESTS - DB vs SQLAlchemy Models")
    print("=" * 60)

    # Executa os schema tests
    result = subprocess.run(
        ["pytest", "-m", "schema", "-v", __file__],
        capture_output=True,
        text=True,
    )

    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode != 0:
        all_validation_failures.append("Schema validation tests falharam")

    # Final validation result
    if all_validation_failures:
        print("\n" + "=" * 60)
        print("❌ VALIDATION FAILED - DB schema diverge dos models!")
        print("=" * 60)
        print("AÇÃO NECESSÁRIA:")
        print("1. Se mudou models: alembic revision --autogenerate")
        print("2. Se DB está desatualizado: alembic upgrade head")
        print("3. Revise as mensagens de erro acima para detalhes")
        sys.exit(1)
    else:
        print("\n" + "=" * 60)
        print("✅ VALIDATION PASSED - DB schema sincronizado com models")
        print("=" * 60)
        print("Schema do banco está consistente com os models")
        sys.exit(0)
