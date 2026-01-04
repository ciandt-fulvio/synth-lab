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
def isolated_db_session(test_database_url: str, monkeypatch):
    """
    Provide an isolated database session for integration tests.

    This fixture:
    1. Verifies we're using the test database (not dev/prod)
    2. Creates a fresh session for each test
    3. Uses nested transactions (SAVEPOINT) to rollback ALL changes after test
       - Even if test calls commit(), changes are rolled back
    4. Ensures complete isolation between tests
    5. Patches get_session_v2() to use test database for Services

    Usage:
        def test_something(isolated_db_session):
            # Use isolated_db_session instead of creating your own connection
            # Services will automatically use this test session
            result = isolated_db_session.execute(text("SELECT 1"))
            assert result.scalar() == 1

    References:
        - SQLAlchemy testing patterns: https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites
    """
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import sessionmaker
    from unittest.mock import MagicMock

    engine = create_engine(test_database_url)
    connection = engine.connect()
    transaction = connection.begin()

    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal(bind=connection)

    # Start a nested transaction (SAVEPOINT)
    nested = connection.begin_nested()

    # Each time the SAVEPOINT ends (commit or rollback), start a new one
    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    # CRITICAL: Clear global caches and patch database functions
    # This ensures Services use the test database instead of dev database
    import synth_lab.infrastructure.database_v2 as db_module

    # Clear any cached session factories/engines from previous tests
    db_module._global_engine = None
    db_module._global_session_factory = None

    # Patch get_engine() to return our test engine
    monkeypatch.setattr("synth_lab.infrastructure.database_v2.get_engine", lambda: engine)

    # Patch get_session_factory() to return session factory bound to test engine
    monkeypatch.setattr("synth_lab.infrastructure.database_v2.get_session_factory", lambda: SessionLocal)

    # Patch get_session() to return a NEW session on the SAME connection
    # This allows Services to see data committed in the test's SAVEPOINT
    def mock_get_session():
        """Mock context manager that yields a new session on test connection."""
        # Create a new session bound to the same connection as the test
        service_session = SessionLocal(bind=connection)
        try:
            yield service_session
        finally:
            service_session.close()

    monkeypatch.setattr("synth_lab.infrastructure.database_v2.get_session", mock_get_session)

    yield session

    # Cleanup: rollback ALL changes (including committed ones in nested transaction)
    session.close()
    transaction.rollback()
    connection.close()
    engine.dispose()
