"""
Pytest configuration and shared fixtures for SynthLab tests.

Test Database Flow:
1. Session start: DROP ALL → Alembic migrations → Verify schema → Seed data
2. Each test: BEGIN TRANSACTION → SAVEPOINT → test runs → ROLLBACK (seed preserved)

CRITICAL: Tests use DATABASE_URL which must point to a test database (contains 'test').
Run via `make test` or `make test-fast` which sets DATABASE_URL to the test container.
"""

# Ensure pytest-asyncio is loaded for async test support
pytest_plugins = ['pytest_asyncio']

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
# override=True ensures .env values take precedence over shell environment
load_dotenv(override=True)

# Set default JWT_SECRET_KEY for tests if not already set
if not os.environ.get("JWT_SECRET_KEY"):
    os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only-do-not-use-in-production"


# ==============================================================================
# Authentication Fixtures
# ==============================================================================

# Test user constants used across all tests
# IMPORTANT: Must be a valid UUID format for database FK constraints
TEST_USER_ID = "00000001-0000-0000-0000-000000000001"
TEST_USER_EMAIL = "testuser@example.com"
TEST_USER_GOOGLE_ID = "google-test-user-001"


@pytest.fixture
def test_user_id() -> str:
    """Return the test user ID used in tests."""
    return TEST_USER_ID


@pytest.fixture
def test_user_email() -> str:
    """Return the test user email used in tests."""
    return TEST_USER_EMAIL


@pytest.fixture
def test_user_google_id() -> str:
    """Return the test user Google ID used in tests."""
    return TEST_USER_GOOGLE_ID


@pytest.fixture
def auth_token() -> str:
    """Create a valid JWT token for testing."""
    from synth_lab.infrastructure.auth.session_manager import SessionManager
    session_manager = SessionManager()
    return session_manager.create_access_token(
        user_id=TEST_USER_ID,
        email=TEST_USER_EMAIL
    )


@pytest.fixture
def create_test_user(db_session):
    """Factory fixture to create test users in the database.

    Returns a function that creates a user and returns the user_id.
    This allows tests to create users before creating experiments/synth_groups with owner_id.

    Usage:
        def test_something(create_test_user):
            user_id = create_test_user(email="test@example.com")
            # Now you can create experiments with owner_id=user_id
    """
    from synth_lab.models.orm.user import User
    from datetime import datetime
    from uuid import uuid4

    def _create_user(
        user_id: str = None,
        email: str = "test@example.com",
        google_user_id: str = None,
        display_name: str = "Test User"
    ) -> str:
        """Create a user in the database and return the user_id."""
        if user_id is None:
            user_id = str(uuid4())
        if google_user_id is None:
            google_user_id = f"google-{user_id}"

        user = User(
            id=user_id,
            email=email,
            google_user_id=google_user_id,
            display_name=display_name,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
        )
        db_session.add(user)
        db_session.flush()  # Flush to make it available in the same transaction
        return user_id

    return _create_user


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

# Global flag to track if database setup has been done
_database_setup_done = False


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


def _ensure_test_database_setup():
    """
    Ensure test database is set up with migrations and seed data.

    This function is idempotent - it only runs setup once per session.
    Called automatically by the autouse fixture.
    """
    global _database_setup_done

    if _database_setup_done:
        return

    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        # Skip setup if no database URL
        return

    from sqlalchemy import create_engine

    print("\n" + "=" * 70)
    print("🐘 PostgreSQL Test Database Auto-Setup")
    print("=" * 70)

    engine = create_engine(db_url)

    try:
        # Step 1: Clean slate
        _drop_all_tables(engine)

        # Step 2: Run migrations
        _run_alembic_migrations(db_url)

        # Recreate engine after schema changes
        engine.dispose()
        engine = create_engine(db_url)

        # Step 3: Seed data
        _seed_test_data(engine)

        print("=" * 70)
        print("✅ Test database ready!")
        print("=" * 70 + "\n")

        _database_setup_done = True

    except Exception as e:
        print(f"\n❌ Database setup failed: {e}")
        raise
    finally:
        engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def auto_setup_test_database():
    """
    Automatically set up test database at the start of every test session.

    This fixture runs BEFORE any test, ensuring:
    - Migrations are applied
    - Seed data is present
    - All tests can access a properly configured database

    The autouse=True means this runs automatically without being requested.
    """
    _ensure_test_database_setup()
    yield


@pytest.fixture(scope="session")
def postgres_test_url() -> str:
    """
    Get PostgreSQL test database URL from DATABASE_URL.

    Returns:
        str: PostgreSQL connection string for test database

    Raises:
        pytest.skip: If DATABASE_URL is not set
    """
    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        pytest.skip("DATABASE_URL not set - run via: make test")

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
def seeded_test_engine(postgres_test_url: str):
    """
    Session-scoped fixture that prepares the test database.

    Flow:
    1. DROP ALL tables (clean slate)
    2. Run Alembic migrations (create schema)
    3. Seed test data

    This runs ONCE per test session. All tests share the seeded data.
    Individual test isolation is handled by db_session using SAVEPOINT.

    Note: This fixture now uses the global setup flag to avoid
    re-running setup if auto_setup_test_database already ran.

    Yields:
        Engine: SQLAlchemy engine connected to seeded test database
    """
    global _database_setup_done
    from sqlalchemy import create_engine

    engine = create_engine(postgres_test_url)

    try:
        # Only run setup if not already done by auto_setup_test_database
        if not _database_setup_done:
            print("\n" + "=" * 70)
            print("🐘 PostgreSQL Test Database Setup (via seeded_test_engine)")
            print("=" * 70)

            # Step 1: Clean slate - drop everything
            _drop_all_tables(engine)

            # Step 2: Run Alembic migrations
            _run_alembic_migrations(postgres_test_url)

            # Recreate engine after schema changes
            engine.dispose()
            engine = create_engine(postgres_test_url)

            # Step 3: Seed test data
            _seed_test_data(engine)

            print("=" * 70)
            print("✅ Test database ready!")
            print("=" * 70 + "\n")

            _database_setup_done = True

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
