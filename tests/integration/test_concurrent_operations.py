"""
Integration tests for concurrent database operations.

These tests verify that the database handles concurrent reads and writes
correctly with connection pooling. Works with both SQLite and PostgreSQL.

Usage:
    # With SQLite:
    pytest tests/integration/test_concurrent_operations.py -v

    # With PostgreSQL:
    docker-compose -f docker/docker-compose.postgres.yml up -d
    POSTGRES_URL=postgresql://synthlab:synthlab_dev@localhost:5432/synthlab \
        pytest tests/integration/test_concurrent_operations.py -v

References:
    - SQLAlchemy session threading: https://docs.sqlalchemy.org/en/20/orm/session_basics.html
    - Connection pooling: https://docs.sqlalchemy.org/en/20/core/pooling.html
"""

import os
import pytest
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from synth_lab.models.orm.base import Base
from synth_lab.models.orm.experiment import Experiment


@pytest.fixture(scope="module")
def database_url():
    """Get database URL - prefer PostgreSQL if available."""
    postgres_url = os.getenv("POSTGRES_URL")
    if postgres_url:
        return postgres_url
    # Fall back to in-memory SQLite
    return "sqlite:///:memory:"


@pytest.fixture(scope="module")
def engine(database_url):
    """Create database engine."""
    if database_url.startswith("sqlite:"):
        from sqlalchemy.pool import StaticPool
        # Use StaticPool for in-memory SQLite to share connection across threads
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            pool_pre_ping=True,
        )
    else:
        engine = create_engine(
            database_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )

    # For PostgreSQL: drop existing tables first to avoid schema conflicts
    # This is necessary because Alembic migration schema may differ from ORM models
    if not database_url.startswith("sqlite:"):
        # Use CASCADE to handle foreign key dependencies
        with engine.connect() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
            conn.commit()

    # Create tables from ORM models
    Base.metadata.create_all(engine)
    yield engine

    # Cleanup
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="module")
def session_factory(engine):
    """Create session factory."""
    return sessionmaker(bind=engine, expire_on_commit=False)


class TestConcurrentReads:
    """Tests for concurrent read operations."""

    def test_concurrent_reads(self, engine, session_factory):
        """Multiple threads can read concurrently."""
        # Setup: Create test data
        session = session_factory()
        for i in range(10):
            exp = Experiment(
                id=f"exp_read_{i:03d}",
                name=f"Concurrent Read Test {i}",
                hypothesis="Testing concurrent reads",
                status="active",
                created_at=datetime.now().isoformat(),
            )
            session.add(exp)
        session.commit()
        session.close()

        # Test: Read concurrently from multiple threads
        results = []
        errors = []

        def read_experiments():
            try:
                session = session_factory()
                experiments = session.query(Experiment).filter(
                    Experiment.id.like("exp_read_%")
                ).all()
                results.append(len(experiments))
                session.close()
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=read_experiments) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert all(r == 10 for r in results), f"Unexpected results: {results}"

        # Cleanup
        session = session_factory()
        session.query(Experiment).filter(Experiment.id.like("exp_read_%")).delete()
        session.commit()
        session.close()


class TestConcurrentWrites:
    """Tests for concurrent write operations."""

    def test_concurrent_writes_different_rows(self, engine, session_factory):
        """Multiple threads can write different rows concurrently."""
        errors = []
        created_ids = []
        lock = threading.Lock()

        def create_experiment(thread_id: int):
            try:
                session = session_factory()
                exp = Experiment(
                    id=f"exp_write_{thread_id:03d}",
                    name=f"Concurrent Write Test {thread_id}",
                    hypothesis=f"Thread {thread_id}",
                    status="active",
                    created_at=datetime.now().isoformat(),
                )
                session.add(exp)
                session.commit()
                with lock:
                    created_ids.append(exp.id)
                session.close()
            except Exception as e:
                with lock:
                    errors.append(f"Thread {thread_id}: {e}")

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_experiment, i) for i in range(20)]
            for future in as_completed(futures):
                future.result()  # Raise any exceptions

        # Verify
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(created_ids) == 20

        # Cleanup
        session = session_factory()
        session.query(Experiment).filter(Experiment.id.like("exp_write_%")).delete()
        session.commit()
        session.close()

    def test_concurrent_updates_same_row(self, engine, session_factory):
        """Handle concurrent updates to the same row."""
        # Setup
        session = session_factory()
        exp = Experiment(
            id="exp_update_001",
            name="Initial Name",
            hypothesis="Testing concurrent updates",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        session.add(exp)
        session.commit()
        session.close()

        # Test: Multiple threads update the same row
        update_count = [0]
        lock = threading.Lock()

        def update_experiment(new_name: str):
            session = session_factory()
            try:
                exp = session.query(Experiment).filter(
                    Experiment.id == "exp_update_001"
                ).with_for_update().first()  # Row-level lock
                if exp:
                    exp.name = new_name
                    exp.updated_at = datetime.now().isoformat()
                    session.commit()
                    with lock:
                        update_count[0] += 1
            except Exception:
                session.rollback()
            finally:
                session.close()

        threads = [
            threading.Thread(target=update_experiment, args=(f"Update {i}",))
            for i in range(5)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify: All updates should succeed
        assert update_count[0] == 5

        # Cleanup
        session = session_factory()
        session.query(Experiment).filter(Experiment.id == "exp_update_001").delete()
        session.commit()
        session.close()


class TestConnectionPoolBehavior:
    """Tests for connection pool behavior under load."""

    def test_pool_handles_high_load(self, engine, session_factory):
        """Pool handles more requests than pool size."""
        results = []
        errors = []
        lock = threading.Lock()

        def query_database(query_id: int):
            try:
                session = session_factory()
                # Simulate some work
                session.execute(text("SELECT 1"))
                time.sleep(0.01)  # Small delay
                session.close()
                with lock:
                    results.append(query_id)
            except Exception as e:
                with lock:
                    errors.append(f"Query {query_id}: {e}")

        # Run more concurrent queries than pool size
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(query_database, i) for i in range(50)]
            for future in as_completed(futures):
                try:
                    future.result(timeout=10)
                except Exception as e:
                    errors.append(str(e))

        # All queries should succeed
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 50

    def test_sessions_are_independent(self, engine, session_factory, database_url):
        """Each session sees its own uncommitted changes only."""
        # Skip for SQLite with StaticPool - shares same connection
        if database_url.startswith("sqlite:"):
            pytest.skip("SQLite with StaticPool shares connection between sessions")

        # Create base record
        session1 = session_factory()
        exp = Experiment(
            id="exp_isolation_001",
            name="Original",
            hypothesis="Testing isolation",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        session1.add(exp)
        session1.commit()
        session1.close()

        # Session 2 updates without committing
        session2 = session_factory()
        exp2 = session2.query(Experiment).filter(Experiment.id == "exp_isolation_001").first()
        exp2.name = "Modified by Session 2"
        session2.flush()  # Flush but don't commit

        # Session 3 should see original value
        session3 = session_factory()
        exp3 = session3.query(Experiment).filter(Experiment.id == "exp_isolation_001").first()

        # Depending on isolation level, session3 may or may not see the change
        # With default READ COMMITTED, it should see original
        assert exp3.name == "Original"

        session2.rollback()
        session2.close()
        session3.close()

        # Cleanup
        session = session_factory()
        session.query(Experiment).filter(Experiment.id == "exp_isolation_001").delete()
        session.commit()
        session.close()


class TestCRUDConcurrency:
    """Tests for concurrent CRUD operations."""

    def test_mixed_crud_operations(self, engine, session_factory):
        """Handle mixed create, read, update, delete operations concurrently."""
        errors = []
        lock = threading.Lock()

        def crud_operation(op_type: str, item_id: int):
            session = session_factory()
            try:
                if op_type == "create":
                    exp = Experiment(
                        id=f"exp_crud_{item_id:03d}",
                        name=f"CRUD Test {item_id}",
                        hypothesis="Testing CRUD",
                        status="active",
                        created_at=datetime.now().isoformat(),
                    )
                    session.add(exp)
                    session.commit()
                elif op_type == "read":
                    session.query(Experiment).filter(
                        Experiment.id == f"exp_crud_{item_id:03d}"
                    ).first()
                elif op_type == "update":
                    exp = session.query(Experiment).filter(
                        Experiment.id == f"exp_crud_{item_id:03d}"
                    ).first()
                    if exp:
                        exp.updated_at = datetime.now().isoformat()
                        session.commit()
                elif op_type == "delete":
                    session.query(Experiment).filter(
                        Experiment.id == f"exp_crud_{item_id:03d}"
                    ).delete()
                    session.commit()
            except Exception as e:
                session.rollback()
                with lock:
                    errors.append(f"{op_type} {item_id}: {e}")
            finally:
                session.close()

        # First create some records
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(crud_operation, "create", i) for i in range(20)]
            for f in as_completed(futures):
                f.result()

        # Then do mixed operations
        operations = []
        for i in range(20):
            operations.append(("read", i))
            operations.append(("update", i))

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(crud_operation, op, i) for op, i in operations]
            for f in as_completed(futures):
                f.result()

        # Finally delete
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(crud_operation, "delete", i) for i in range(20)]
            for f in as_completed(futures):
                f.result()

        # Should have no errors
        assert len(errors) == 0, f"Errors occurred: {errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
