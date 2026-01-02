"""
Integration tests for PostgreSQL connection and pooling.

These tests verify PostgreSQL connectivity, connection pooling behavior,
and SSL configuration. Requires a running PostgreSQL instance.

Usage:
    # Start PostgreSQL with Docker:
    docker-compose -f docker/docker-compose.postgres.yml up -d

    # Run tests:
    POSTGRES_URL=postgresql://synthlab:synthlab_dev@localhost:5432/synthlab \
        pytest tests/integration/test_postgres_connection.py -v

References:
    - SQLAlchemy connection pooling: https://docs.sqlalchemy.org/en/20/core/pooling.html
    - PostgreSQL connection: https://www.postgresql.org/docs/current/libpq-connect.html
"""

import os
import pytest
from unittest.mock import patch

from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool


# Skip all tests if PostgreSQL is not available
pytestmark = pytest.mark.skipif(
    not os.getenv("POSTGRES_URL"),
    reason="POSTGRES_URL environment variable not set"
)


@pytest.fixture(scope="module")
def postgres_url():
    """Get PostgreSQL URL from environment."""
    return os.getenv("POSTGRES_URL")


@pytest.fixture(scope="module")
def postgres_engine(postgres_url):
    """Create PostgreSQL engine for testing."""
    engine = create_engine(
        postgres_url,
        pool_size=2,
        max_overflow=2,
        pool_pre_ping=True,
    )
    yield engine
    engine.dispose()


class TestPostgresConnection:
    """Tests for basic PostgreSQL connectivity."""

    def test_can_connect_to_postgres(self, postgres_engine):
        """Verify basic connection to PostgreSQL."""
        with postgres_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_postgres_version(self, postgres_engine):
        """Verify PostgreSQL version."""
        with postgres_engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            assert "PostgreSQL" in version

    def test_current_database(self, postgres_engine, postgres_url):
        """Verify connected to correct database."""
        with postgres_engine.connect() as conn:
            result = conn.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            # Extract expected db name from URL
            expected_db = postgres_url.split("/")[-1].split("?")[0]
            assert db_name == expected_db


class TestPostgresPooling:
    """Tests for PostgreSQL connection pooling."""

    def test_pool_is_queue_pool(self, postgres_engine):
        """PostgreSQL should use QueuePool."""
        assert isinstance(postgres_engine.pool, QueuePool)

    def test_pool_size_configuration(self):
        """Test pool size configuration based on workers."""
        from synth_lab.infrastructure.database_v2 import create_db_engine

        postgres_url = os.getenv("POSTGRES_URL")

        with patch.dict(os.environ, {"WORKERS": "2"}):
            engine = create_db_engine(postgres_url)
            # pool_size should be WORKERS * 2 = 4
            assert engine.pool.size() == 4
            engine.dispose()

    def test_pool_overflow_configuration(self):
        """Test pool overflow configuration."""
        from synth_lab.infrastructure.database_v2 import create_db_engine

        postgres_url = os.getenv("POSTGRES_URL")

        with patch.dict(os.environ, {"WORKERS": "2"}):
            engine = create_db_engine(postgres_url)
            # max_overflow should be WORKERS * 4 = 8
            # Total max connections = pool_size + max_overflow = 12
            pool = engine.pool
            assert pool._max_overflow == 8
            engine.dispose()

    def test_pool_pre_ping_enabled(self, postgres_engine):
        """Verify pool pre-ping is enabled."""
        # Pre-ping prevents stale connections from being used
        assert postgres_engine.pool._pre_ping is True


class TestPostgresSSL:
    """Tests for PostgreSQL SSL configuration."""

    def test_ssl_mode_configuration(self):
        """Test SSL mode configuration from environment."""
        from synth_lab.infrastructure.database_v2 import create_db_engine

        postgres_url = os.getenv("POSTGRES_URL")

        with patch.dict(os.environ, {"POSTGRES_SSL_MODE": "require"}):
            engine = create_db_engine(postgres_url)
            # Engine should be created without error
            assert engine is not None
            engine.dispose()

    def test_ssl_disabled_by_default(self):
        """SSL should be disabled if POSTGRES_SSL_MODE not set."""
        from synth_lab.infrastructure.database_v2 import create_db_engine

        postgres_url = os.getenv("POSTGRES_URL")

        # Remove SSL mode if set
        env = os.environ.copy()
        env.pop("POSTGRES_SSL_MODE", None)

        with patch.dict(os.environ, env, clear=True):
            engine = create_db_engine(postgres_url)
            # Should work without SSL
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                assert result.scalar() == 1
            engine.dispose()


class TestPostgresTransactions:
    """Tests for PostgreSQL transaction handling."""

    def test_transaction_commit(self, postgres_engine):
        """Test transaction commit."""
        with postgres_engine.connect() as conn:
            trans = conn.begin()
            try:
                conn.execute(text("CREATE TABLE IF NOT EXISTS test_tx (id INT)"))
                conn.execute(text("INSERT INTO test_tx VALUES (1)"))
                trans.commit()

                # Verify data persisted
                result = conn.execute(text("SELECT COUNT(*) FROM test_tx"))
                assert result.scalar() == 1

            finally:
                conn.execute(text("DROP TABLE IF EXISTS test_tx"))
                conn.commit()

    def test_transaction_rollback(self, postgres_engine):
        """Test transaction rollback."""
        with postgres_engine.connect() as conn:
            # Create table first
            conn.execute(text("CREATE TABLE IF NOT EXISTS test_rollback (id INT)"))
            conn.commit()

            # Start transaction and rollback
            trans = conn.begin()
            conn.execute(text("INSERT INTO test_rollback VALUES (1)"))
            trans.rollback()

            # Verify data was not persisted
            result = conn.execute(text("SELECT COUNT(*) FROM test_rollback"))
            assert result.scalar() == 0

            # Cleanup
            conn.execute(text("DROP TABLE IF EXISTS test_rollback"))
            conn.commit()


class TestDatabaseV2Integration:
    """Tests for database_v2 module with PostgreSQL."""

    def test_get_session_context_manager(self):
        """Test get_session context manager with PostgreSQL."""
        from synth_lab.infrastructure.database_v2 import (
            create_db_engine,
            get_session,
            dispose_engine,
        )
        import synth_lab.infrastructure.database_v2 as db_mod

        postgres_url = os.getenv("POSTGRES_URL")

        # Set up engine
        db_mod._engine = create_db_engine(postgres_url)
        from sqlalchemy.orm import sessionmaker
        db_mod._session_factory = sessionmaker(bind=db_mod._engine, expire_on_commit=False)

        try:
            with get_session() as session:
                result = session.execute(text("SELECT 1"))
                assert result.scalar() == 1
        finally:
            dispose_engine()

    def test_health_check_with_postgres(self):
        """Test health_check function with PostgreSQL."""
        from synth_lab.infrastructure.database_v2 import (
            create_db_engine,
            health_check,
            dispose_engine,
        )
        import synth_lab.infrastructure.database_v2 as db_mod

        postgres_url = os.getenv("POSTGRES_URL")

        # Set up engine
        db_mod._engine = create_db_engine(postgres_url)
        from sqlalchemy.orm import sessionmaker
        db_mod._session_factory = sessionmaker(bind=db_mod._engine, expire_on_commit=False)

        try:
            assert health_check() is True
        finally:
            dispose_engine()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
