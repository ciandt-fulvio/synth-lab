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
