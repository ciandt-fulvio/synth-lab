"""
Pytest configuration and shared fixtures for SynthLab tests.

CRITICAL: Integration tests use a SEPARATE test database (synthlab_test).
This prevents destructive tests from affecting development data.
"""

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

import pytest
from dotenv import load_dotenv

# Load .env file automatically for all tests
load_dotenv()


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


@pytest.fixture(scope="session")
def test_database_url() -> str:
    """
    Provide isolated test database URL.

    CRITICAL: This fixture ensures tests NEVER use the development database.
    Integration tests will DROP and recreate tables - only safe on test DB!

    Returns:
        str: PostgreSQL test database URL from POSTGRES_URL environment variable

    Raises:
        pytest.skip: If POSTGRES_URL is not set (test database not configured)
    """
    postgres_url = os.getenv("POSTGRES_URL")

    if not postgres_url:
        pytest.skip("POSTGRES_URL environment variable not set - test database not configured")

    # Safety check: ensure we're NOT using the development database
    if "synthlab_test" not in postgres_url:
        raise ValueError(
            f"CRITICAL: POSTGRES_URL must point to 'synthlab_test' database, not production/dev DB!\n"
            f"Current URL: {postgres_url}\n"
            f"Expected: postgresql://user:pass@localhost:5432/synthlab_test"
        )

    return postgres_url


@pytest.fixture(scope="function")
def isolated_db_session(test_database_url: str):
    """
    Provide an isolated database session for integration tests.

    This fixture:
    1. Verifies we're using the test database (not dev/prod)
    2. Creates all ORM tables if they don't exist
    3. Cleans all tables before and after each test
    4. Creates a fresh session for each test
    5. Uses transactions with rollback for isolation

    IMPORTANT: Tests should create Services by passing repositories with this session.
    Example:
        def test_something(isolated_db_session):
            # Setup test data
            isolated_db_session.add(Experiment(...))
            isolated_db_session.commit()

            # Create service with test session
            repo = ResearchRepository(session=isolated_db_session)
            service = ResearchService(research_repo=repo)

            # Run test
            result = service.list_executions(params)
            assert result.pagination.total == expected
    """
    from sqlalchemy import create_engine, text, event
    from sqlalchemy.orm import sessionmaker

    # Import all ORM models to register them with Base.metadata
    import synth_lab.models.orm  # noqa: F401
    from synth_lab.models.orm.base import Base

    engine = create_engine(test_database_url)

    # Create all tables if they don't exist
    Base.metadata.create_all(engine)

    connection = engine.connect()
    transaction = connection.begin()

    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal(bind=connection)

    # Start a nested transaction (SAVEPOINT) for test isolation
    nested = connection.begin_nested()

    # Restart SAVEPOINT after each commit/rollback
    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    # Rollback everything (including commits via SAVEPOINT)
    session.close()
    if nested.is_active:
        nested.rollback()
    transaction.rollback()
    connection.close()
    engine.dispose()


# ==============================================================================
# PostgreSQL Test Database Auto-Setup
# ==============================================================================


def _ensure_test_database_ready(db_url: str) -> None:
    """
    Ensure PostgreSQL test database exists and is migrated.

    This function:
    1. Creates database if it doesn't exist
    2. Applies all Alembic migrations if needed
    3. Verifies migrations are at HEAD

    Called automatically before any PostgreSQL test runs.
    """
    from sqlalchemy import create_engine, text
    from alembic import command
    from alembic.config import Config
    from alembic.runtime.migration import MigrationContext
    from alembic.script import ScriptDirectory
    from pathlib import Path
    import sys

    # Extract database name from URL
    db_name = db_url.rsplit("/", 1)[1].split("?")[0]
    admin_url = db_url.rsplit("/", 1)[0] + "/postgres"

    # Try to connect to test database
    try:
        test_engine = create_engine(db_url)
        test_engine.connect().close()
        test_engine.dispose()
        database_exists = True
    except Exception:
        database_exists = False

    # Create database if it doesn't exist
    if not database_exists:
        print(f"\n🔧 Creating test database '{db_name}'...")
        try:
            admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
            with admin_engine.connect() as conn:
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
            admin_engine.dispose()
            print(f"✅ Database '{db_name}' created")
        except Exception as e:
            print(f"❌ Failed to create database: {e}")
            print("💡 Make sure PostgreSQL is running: docker compose up -d postgres")
            sys.exit(1)

    # Check and apply migrations
    test_engine = create_engine(db_url)

    try:
        with test_engine.connect() as conn:
            context = MigrationContext.configure(conn)
            current_rev = context.get_current_revision()

            # Get HEAD revision
            project_root = Path(__file__).parent.parent
            alembic_ini = project_root / "src" / "synth_lab" / "alembic" / "alembic.ini"
            config = Config(str(alembic_ini))
            config.set_main_option(
                "script_location", str(project_root / "src" / "synth_lab" / "alembic")
            )
            script = ScriptDirectory.from_config(config)
            head_rev = script.get_current_head()

            # Apply migrations if needed
            if current_rev != head_rev:
                print(f"\n🔧 Applying migrations to test database...")
                print(f"   Current: {current_rev or 'None'}")
                print(f"   Target:  {head_rev}")

                # Set DATABASE_URL for env.py
                os.environ["DATABASE_URL"] = db_url

                command.upgrade(config, "head")
                print("✅ Migrations applied successfully")

    except Exception as e:
        print(f"❌ Migration check/apply failed: {e}")
        sys.exit(1)
    finally:
        test_engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def _auto_setup_postgres_if_needed(request):
    """
    Automatically setup PostgreSQL test database if any test needs it.

    This fixture runs once per test session and:
    - Detects if any test uses PostgreSQL fixtures or has @pytest.mark.requires_postgres
    - Creates database if needed
    - Applies migrations automatically
    - Does nothing if DATABASE_TEST_URL is not set

    No manual setup required - just run pytest!
    """
    db_url = os.getenv("DATABASE_TEST_URL")

    if not db_url:
        # No PostgreSQL configured - tests will skip
        return

    # Check if any test in session uses postgres fixtures or marker
    uses_postgres = False
    for item in request.session.items:
        # Check for requires_postgres marker
        if item.get_closest_marker("requires_postgres"):
            uses_postgres = True
            break

        # Check for postgres fixtures
        fixture_names = getattr(item, "fixturenames", [])
        postgres_fixtures = {
            "postgres_test_url",
            "migrated_db_engine",
            "db_session",
            "seeded_db_session",
        }
        if any(f in postgres_fixtures for f in fixture_names):
            uses_postgres = True
            break

    if uses_postgres:
        print("\n" + "=" * 70)
        print("🐘 PostgreSQL Test Database Auto-Setup")
        print("=" * 70)
        _ensure_test_database_ready(db_url)
        print("=" * 70)


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "requires_postgres: mark test as requiring PostgreSQL (auto-setup enabled)"
    )


# ==============================================================================
# PostgreSQL Test Database Fixtures with Alembic Migrations
# ==============================================================================


@pytest.fixture(scope="session")
def postgres_test_url() -> str:
    """
    Get PostgreSQL test database URL.

    Uses DATABASE_TEST_URL from environment.
    Skips tests if not configured.

    Returns:
        str: PostgreSQL connection string for test database
    """
    db_url = os.getenv("DATABASE_TEST_URL")

    if not db_url:
        pytest.skip("DATABASE_TEST_URL not set - PostgreSQL test database required")

    # Safety check
    if "synthlab_test" not in db_url and "test" not in db_url:
        raise ValueError(
            f"CRITICAL: DATABASE_TEST_URL must point to test database!\n"
            f"Current: {db_url}\n"
            f"Expected: postgresql://user:pass@localhost:5432/synthlab_test"
        )

    return db_url


@pytest.fixture(scope="session")
def migrated_db_engine(postgres_test_url: str):
    """
    Provide database engine with Alembic migrations applied.

    This fixture:
    - Connects to PostgreSQL test database
    - Verifies migrations are at HEAD (fails if not)
    - Returns engine for test use
    - Does NOT create/drop tables (migrations handle that)

    Use this for tests that need a clean database with proper schema.

    IMPORTANT: Run `uv run python scripts/setup_test_db.py --reset`
    before running tests to ensure database is properly migrated.
    """
    from sqlalchemy import create_engine
    from alembic.runtime.migration import MigrationContext
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from pathlib import Path

    engine = create_engine(postgres_test_url)

    # Verify migrations are at HEAD
    with engine.connect() as conn:
        context = MigrationContext.configure(conn)
        current_rev = context.get_current_revision()

        # Get expected HEAD revision
        project_root = Path(__file__).parent.parent
        alembic_ini = project_root / "src" / "synth_lab" / "alembic" / "alembic.ini"
        config = Config(str(alembic_ini))
        config.set_main_option(
            "script_location", str(project_root / "src" / "synth_lab" / "alembic")
        )
        script = ScriptDirectory.from_config(config)
        head_rev = script.get_current_head()

        if current_rev != head_rev:
            pytest.fail(
                f"Database migrations out of date!\n"
                f"Current: {current_rev}\n"
                f"Expected: {head_rev}\n"
                f"Run: uv run python scripts/setup_test_db.py --reset"
            )

    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(migrated_db_engine):
    """
    Provide clean database session for each test.

    Uses SAVEPOINT for isolation - each test gets rolled back.
    Database schema comes from Alembic migrations (not create_all).
    """
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import event

    connection = migrated_db_engine.connect()
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

    # Cleanup
    session.close()
    if nested.is_active:
        nested.rollback()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def seeded_db_session(db_session):
    """
    Provide database session with test data seeded.

    Seeds the database with realistic test data before each test.
    Data is automatically rolled back after test completes.
    """
    from tests.fixtures.seed_test import seed_database

    # Seed data using the session's engine
    seed_database(db_session.get_bind())

    yield db_session
