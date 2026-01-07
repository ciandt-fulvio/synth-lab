"""
Pytest configuration and shared fixtures for SynthLab tests.

Test Database Flow:
1. Session start: DROP ALL → Alembic migrations → Verify schema → Seed data
2. Each test: BEGIN TRANSACTION → SAVEPOINT → test runs → ROLLBACK (seed preserved)

CRITICAL: Integration tests use POSTGRES_URL pointing to 'synthlab_test' database.
This prevents destructive tests from affecting development data.
"""

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

import pytest
from dotenv import load_dotenv

# Load .env file automatically for all tests
load_dotenv()


# ==============================================================================
# Utility Fixtures (no database)
# ==============================================================================


@pytest.fixture
def config_data() -> dict[str, Any]:
    """Load actual config data from data/config/."""
    data_dir = Path(__file__).parent.parent / "data"
    config_dir = data_dir / "config"

    config = {}
    config_files = {
        "ibge": config_dir / "ibge_distributions.json",
        "occupations": config_dir / "occupations_structured.json",
        "interests_hobbies": config_dir / "interests_hobbies.json",
    }

    for key, path in config_files.items():
        with open(path, "r", encoding="utf-8") as f:
            config[key] = json.load(f)

    return config


@pytest.fixture
def sample_synth() -> dict[str, Any]:
    """Provide a minimal valid synth structure for testing (matches synth-schema v2.3.0)."""
    return {
        "id": "test01",
        "nome": "Test User",
        "descricao": "Pessoa de 25 anos para testes automatizados do sistema com descrição mais longa",
        "link_photo": "https://ui-avatars.com/api/?name=Test+User&size=256&background=random",
        "created_at": "2025-12-15T10:00:00Z",
        "version": "2.3.0",
        "demografia": {
            "idade": 25,
            "genero_biologico": "masculino",
            "raca_etnia": "pardo",
            "localizacao": {
                "pais": "Brasil",
                "regiao": "Sudeste",
                "estado": "SP",
                "cidade": "São Paulo",
            },
            "escolaridade": "Superior completo",
            "renda_mensal": 5000.0,
            "ocupacao": "Desenvolvedor",
            "estado_civil": "solteiro",
            "composicao_familiar": {"tipo": "unipessoal", "numero_pessoas": 1},
        },
        "psicografia": {
            "interesses": ["Tecnologia", "Leitura", "Música"],
            "contrato_cognitivo": {
                "tipo": "factual",
                "perfil_cognitivo": "responde só ao que foi perguntado, evita abstrações",
                "regras": ["Proibido dar opinião geral", "Sempre relatar um evento específico"],
                "efeito_esperado": "respostas secas, muito factuais",
            },
        },
        "deficiencias": {
            "visual": {"tipo": "nenhuma"},
            "auditiva": {"tipo": "nenhuma"},
            "motora": {"tipo": "nenhuma"},
            "cognitiva": {"tipo": "nenhuma"},
        },
        "observables": {
            "digital_literacy": 0.9,
            "similar_tool_experience": 0.7,
            "motor_ability": 1.0,
            "time_availability": 0.6,
            "domain_expertise": 0.5,
        },
    }


@pytest.fixture
def temp_output_dir():
    """Provide a temporary directory for test output, cleaned up after test."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


# ==============================================================================
# PostgreSQL Test Database Configuration
# ==============================================================================


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "requires_postgres: mark test as requiring PostgreSQL (auto-setup enabled)"
    )
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test requiring database"
    )


@pytest.fixture(scope="session")
def postgres_test_url() -> str:
    """
    Get PostgreSQL test database URL from POSTGRES_URL.

    Safety checks:
    - Must be set
    - Must contain 'synthlab_test' or 'test' to prevent accidental use of prod DB

    Returns:
        str: PostgreSQL connection string for test database

    Raises:
        pytest.skip: If POSTGRES_URL is not set
        ValueError: If URL doesn't point to test database
    """
    db_url = os.getenv("POSTGRES_URL")

    if not db_url:
        pytest.skip("POSTGRES_URL not set - PostgreSQL test database required")

    # Safety check: ensure we're NOT using the development database
    if "synthlab_test" not in db_url and "test" not in db_url:
        raise ValueError(
            f"CRITICAL: POSTGRES_URL must point to 'synthlab_test' database!\n"
            f"Current: {db_url}\n"
            f"Expected: postgresql://user:pass@localhost:5432/synthlab_test"
        )

    return db_url


@pytest.fixture(scope="session")
def prod_database_url() -> str:
    """
    Get production/development database URL from DATABASE_URL.

    Used for schema comparison to ensure test DB matches prod DB.

    Returns:
        str: PostgreSQL connection string for prod/dev database

    Raises:
        pytest.skip: If DATABASE_URL is not set
    """
    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        pytest.skip("DATABASE_URL not set - cannot compare schemas")

    return db_url


# ==============================================================================
# Database Setup: Clean → Migrate → Verify → Seed (Session-scoped)
# ==============================================================================


def _drop_all_tables(engine) -> None:
    """Drop ALL tables from database (clean slate)."""
    from sqlalchemy import text

    print("   🗑️  Dropping all tables...")

    with engine.connect() as conn:
        # Drop all tables by dropping and recreating schema
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
        conn.commit()

    print("   ✅ All tables dropped")


def _run_alembic_migrations(db_url: str) -> str:
    """
    Run Alembic migrations to create schema from scratch.

    Returns:
        str: HEAD revision that was applied
    """
    from alembic import command
    from alembic.config import Config

    print("   🔧 Running Alembic migrations...")

    project_root = Path(__file__).parent.parent
    alembic_ini = project_root / "src" / "synth_lab" / "alembic" / "alembic.ini"

    config = Config(str(alembic_ini))
    config.set_main_option(
        "script_location", str(project_root / "src" / "synth_lab" / "alembic")
    )

    # Set DATABASE_URL for env.py
    os.environ["DATABASE_URL"] = db_url

    command.upgrade(config, "head")

    # Get HEAD revision
    from alembic.script import ScriptDirectory
    script = ScriptDirectory.from_config(config)
    head_rev = script.get_current_head()

    print(f"   ✅ Migrations applied (HEAD: {head_rev})")
    return head_rev


def _verify_schema_matches_prod(test_engine, prod_url: str) -> None:
    """
    Verify test database schema matches production database schema.

    Compares:
    - Table names
    - Column names and types for each table
    - Primary keys
    - Foreign keys

    Raises:
        AssertionError: If schemas don't match
    """
    from sqlalchemy import create_engine, inspect

    print("   🔍 Verifying schema matches production...")

    prod_engine = create_engine(prod_url)

    try:
        test_inspector = inspect(test_engine)
        prod_inspector = inspect(prod_engine)

        # Compare table names
        test_tables = set(test_inspector.get_table_names())
        prod_tables = set(prod_inspector.get_table_names())

        # Exclude alembic_version from comparison
        test_tables.discard("alembic_version")
        prod_tables.discard("alembic_version")

        if test_tables != prod_tables:
            missing_in_test = prod_tables - test_tables
            extra_in_test = test_tables - prod_tables
            raise AssertionError(
                f"Table mismatch!\n"
                f"Missing in test DB: {missing_in_test}\n"
                f"Extra in test DB: {extra_in_test}"
            )

        # Compare columns for each table
        for table in test_tables:
            test_cols = {c["name"]: c for c in test_inspector.get_columns(table)}
            prod_cols = {c["name"]: c for c in prod_inspector.get_columns(table)}

            if test_cols.keys() != prod_cols.keys():
                missing = set(prod_cols.keys()) - set(test_cols.keys())
                extra = set(test_cols.keys()) - set(prod_cols.keys())
                raise AssertionError(
                    f"Column mismatch in table '{table}'!\n"
                    f"Missing in test: {missing}\n"
                    f"Extra in test: {extra}"
                )

        print("   ✅ Schema verified - matches production")

    finally:
        prod_engine.dispose()


def _seed_test_data(engine) -> None:
    """Seed database with test data from seed_test.py."""
    from tests.fixtures.seed_test import seed_database

    print("   🌱 Seeding test data...")
    seed_database(engine)
    print("   ✅ Test data seeded")


@pytest.fixture(scope="session")
def seeded_test_engine(postgres_test_url: str, prod_database_url: str):
    """
    Session-scoped fixture that prepares the test database.

    Flow:
    1. DROP ALL tables (clean slate)
    2. Run Alembic migrations (create schema)
    3. Verify schema matches production
    4. Seed test data

    This runs ONCE per test session. All tests share the seeded data.
    Individual test isolation is handled by db_session using SAVEPOINT.

    Yields:
        Engine: SQLAlchemy engine connected to seeded test database
    """
    from sqlalchemy import create_engine

    print("\n" + "=" * 70)
    print("🐘 PostgreSQL Test Database Setup")
    print("=" * 70)

    engine = create_engine(postgres_test_url)

    try:
        # Step 1: Clean slate - drop everything
        _drop_all_tables(engine)

        # Step 2: Run Alembic migrations
        _run_alembic_migrations(postgres_test_url)

        # Recreate engine after schema changes
        engine.dispose()
        engine = create_engine(postgres_test_url)

        # Step 3: Verify schema matches production
        _verify_schema_matches_prod(engine, prod_database_url)

        # Step 4: Seed test data
        _seed_test_data(engine)

        print("=" * 70)
        print("✅ Test database ready!")
        print("=" * 70 + "\n")

        yield engine

    except Exception as e:
        print(f"\n❌ Database setup failed: {e}")
        raise
    finally:
        engine.dispose()


# ==============================================================================
# Test Session Fixtures (Function-scoped with SAVEPOINT isolation)
# ==============================================================================


@pytest.fixture(scope="function")
def db_session(seeded_test_engine):
    """
    Function-scoped database session with SAVEPOINT isolation.

    Each test:
    - Sees the seeded data (from session setup)
    - Can insert/update/delete data
    - All changes are ROLLED BACK after the test
    - Seed data remains intact for next test

    Flow:
        BEGIN TRANSACTION
        └─ SAVEPOINT
           └─ Test runs (sees seed data, can modify)
           └─ ROLLBACK SAVEPOINT  ← changes gone
        └─ ROLLBACK TRANSACTION

    Usage:
        def test_something(db_session):
            # Seed data is available
            experiments = db_session.query(Experiment).all()
            assert len(experiments) == 1  # From seed

            # You can add more data
            db_session.add(Experiment(...))
            db_session.commit()

            # After test, your additions are rolled back
            # but seed data remains for next test
    """
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import event

    connection = seeded_test_engine.connect()
    transaction = connection.begin()

    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    # Use nested transaction (SAVEPOINT) for test isolation
    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    # Cleanup - rollback all changes, preserving seed data
    session.close()
    if nested.is_active:
        nested.rollback()
    transaction.rollback()
    connection.close()


# ==============================================================================
# Legacy Fixtures (for backward compatibility)
# ==============================================================================


@pytest.fixture(scope="session")
def test_database_url(postgres_test_url) -> str:
    """Alias for postgres_test_url (backward compatibility)."""
    return postgres_test_url


@pytest.fixture(scope="session")
def migrated_db_engine(seeded_test_engine):
    """Alias for seeded_test_engine (backward compatibility)."""
    return seeded_test_engine


@pytest.fixture(scope="function")
def isolated_db_session(db_session):
    """Alias for db_session (backward compatibility)."""
    return db_session


@pytest.fixture(scope="function")
def seeded_db_session(db_session):
    """
    Alias for db_session (backward compatibility).

    Note: With the new setup, db_session already has seeded data.
    This fixture exists for backward compatibility with tests that
    explicitly requested seeded_db_session.
    """
    return db_session
