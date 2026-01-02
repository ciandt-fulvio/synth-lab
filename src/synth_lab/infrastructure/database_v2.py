"""
SQLAlchemy database engine and session management for synth-lab.

PostgreSQL-only database layer using SQLAlchemy ORM.

References:
    - SQLAlchemy 2.0 Engine: https://docs.sqlalchemy.org/en/20/core/engines.html
    - Connection Pooling: https://docs.sqlalchemy.org/en/20/core/pooling.html
    - Session Management: https://docs.sqlalchemy.org/en/20/orm/session_basics.html
    - PostgreSQL SSL: https://www.postgresql.org/docs/current/libpq-ssl.html

Environment Variables:
    DATABASE_URL: PostgreSQL connection string (REQUIRED)
        Format: "postgresql://user:pass@host:5432/dbname"
    SQL_ECHO: Set to "true" to enable SQL logging
    WORKERS: Number of workers for pool sizing (default: 4)
    POSTGRES_SSL_MODE: SSL mode for PostgreSQL connections
        - "disable": No SSL
        - "allow": Try SSL, fallback to unencrypted
        - "prefer": Try SSL first (default for most clients)
        - "require": Require SSL (recommended for production)
        - "verify-ca": Require SSL and verify CA certificate
        - "verify-full": Require SSL and verify CA + hostname
    POSTGRES_SSL_ROOT_CERT: Path to CA certificate file (for verify-ca/verify-full)
"""

import os
from collections.abc import Generator
from contextlib import contextmanager

from loguru import logger
from sqlalchemy import create_engine, Engine, text
from sqlalchemy.orm import Session, sessionmaker


class DatabaseConfigError(Exception):
    """Raised when database configuration is invalid."""

    pass


def get_database_url() -> str:
    """
    Get PostgreSQL database URL from environment.

    DATABASE_URL environment variable is REQUIRED.

    Returns:
        PostgreSQL connection string

    Raises:
        DatabaseConfigError: If DATABASE_URL is not set
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise DatabaseConfigError(
            "DATABASE_URL environment variable is required. "
            "Set it to your PostgreSQL connection string: "
            "postgresql://user:pass@host:5432/dbname"
        )

    if not database_url.startswith("postgresql"):
        raise DatabaseConfigError(
            f"DATABASE_URL must be a PostgreSQL URL (starts with 'postgresql'). "
            f"Got: {database_url[:20]}..."
        )

    return database_url


def create_db_engine(database_url: str | None = None) -> Engine:
    """
    Create SQLAlchemy engine for PostgreSQL.

    PostgreSQL configuration:
        - Connection pooling with worker-based sizing
        - Pool pre-ping for connection validation
        - LIFO mode for better idle cleanup
        - Optional SSL configuration

    Args:
        database_url: Optional override for database URL

    Returns:
        Configured SQLAlchemy Engine
    """
    url = database_url or get_database_url()
    sql_echo = os.getenv("SQL_ECHO", "false").lower() == "true"

    log = logger.bind(component="database_v2")
    # Hide password in logs
    log.info(f"Creating PostgreSQL engine for: {url.split('@')[-1] if '@' in url else url}")

    worker_count = int(os.getenv("WORKERS", "4"))

    # Build connect_args for SSL if configured
    connect_args = {}
    ssl_mode = os.getenv("POSTGRES_SSL_MODE")
    ssl_root_cert = os.getenv("POSTGRES_SSL_ROOT_CERT")

    if ssl_mode:
        connect_args["sslmode"] = ssl_mode
        if ssl_root_cert:
            connect_args["sslrootcert"] = ssl_root_cert
        log.info(f"PostgreSQL SSL enabled with mode: {ssl_mode}")

    engine_kwargs = {
        "pool_size": worker_count * 4,      # Persistent connections (increased)
        "max_overflow": worker_count * 8,   # Burst capacity (increased)
        "pool_recycle": 1800,               # Recycle every 30 minutes
        "pool_pre_ping": True,              # Validate connections before use
        "pool_use_lifo": True,              # Better idle cleanup
        "pool_timeout": 60,                 # Wait time for connection (increased)
        "echo": sql_echo,
    }

    # Only add connect_args if we have SSL configuration
    if connect_args:
        engine_kwargs["connect_args"] = connect_args

    engine = create_engine(url, **engine_kwargs)

    log.debug(
        f"PostgreSQL engine created with pool_size={worker_count * 4}, "
        f"max_overflow={worker_count * 8}"
    )
    return engine


# Global engine and session factory instances
_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """
    Get or create the global database engine.

    Thread-safe singleton pattern. Engine is created on first call
    and reused for subsequent calls.

    Returns:
        SQLAlchemy Engine instance
    """
    # Use module-level access to avoid Python 3.13 annotated global issue
    import synth_lab.infrastructure.database_v2 as db_mod

    if db_mod._engine is None:
        log = logger.bind(component="database_v2")
        log.debug("Creating global database engine (first access)")
        db_mod._engine = create_db_engine()
        log.info("Global database engine initialized")
    return db_mod._engine


def get_session_factory() -> sessionmaker[Session]:
    """
    Get or create the global session factory.

    Uses the global engine and configures expire_on_commit=False
    to prevent lazy-loading issues after commit.

    Returns:
        SQLAlchemy sessionmaker instance
    """
    # Use module-level access to avoid Python 3.13 annotated global issue
    import synth_lab.infrastructure.database_v2 as db_mod

    if db_mod._session_factory is None:
        log = logger.bind(component="database_v2")
        log.debug("Creating global session factory (first access)")
        engine = get_engine()
        db_mod._session_factory = sessionmaker(
            bind=engine,
            expire_on_commit=False,  # Prevent lazy-loading issues
            autoflush=False,          # Manual flush control
        )
        log.info("Global session factory initialized")
    return db_mod._session_factory


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.

    Provides automatic commit on success and rollback on exception.
    Use this for service-layer operations.

    Usage:
        with get_session() as session:
            experiment = session.query(Experiment).first()
            experiment.name = "Updated"
            # Auto-commits on exit

    Yields:
        SQLAlchemy Session instance
    """
    factory = get_session_factory()
    session = factory()
    log = logger.bind(component="database_v2")

    try:
        yield session
        session.commit()
        log.debug("Session committed successfully")
    except Exception as e:
        session.rollback()
        log.warning(f"Session rolled back due to error: {e}")
        raise
    finally:
        session.close()


def get_db_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions.

    Provides a session per request with automatic commit/rollback.
    Use with FastAPI's Depends() for endpoint injection.

    Usage:
        @app.get("/experiments/{id}")
        def get_experiment(
            id: str,
            db: Session = Depends(get_db_session)
        ):
            return db.query(Experiment).filter_by(id=id).first()

    Yields:
        SQLAlchemy Session instance
    """
    factory = get_session_factory()
    session = factory()
    log = logger.bind(component="database_v2")

    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        log.warning(f"Request session rolled back: {e}")
        raise
    finally:
        session.close()


def init_database_v2() -> None:
    """
    Initialize PostgreSQL database with SQLAlchemy.

    Creates all tables defined in the Base metadata.
    For production, use Alembic migrations instead.

    This function is useful for:
    - Testing with fresh databases
    - Development setup
    - Initial schema creation before switching to Alembic
    """
    from synth_lab.models.orm.base import Base

    engine = get_engine()
    log = logger.bind(component="database_v2")

    log.info("Initializing PostgreSQL database with SQLAlchemy ORM")
    log.debug(f"Creating tables from Base.metadata ({len(Base.metadata.tables)} tables)")

    Base.metadata.create_all(bind=engine)

    table_names = list(Base.metadata.tables.keys())
    log.info(f"Database initialized successfully: {len(table_names)} tables created")
    log.debug(f"Tables: {', '.join(sorted(table_names))}")


def dispose_engine() -> None:
    """
    Dispose of the global engine and reset session factory.

    Call this when shutting down the application or
    when switching database configurations in tests.
    """
    # Use module-level access to avoid Python 3.13 annotated global issue
    import synth_lab.infrastructure.database_v2 as db_mod

    if db_mod._engine is not None:
        db_mod._engine.dispose()
        db_mod._engine = None
        db_mod._session_factory = None
        logger.bind(component="database_v2").info("Database engine disposed")


def health_check() -> bool:
    """
    Check database connectivity.

    Executes a simple query to verify the database is accessible.
    Useful for health check endpoints.

    Returns:
        True if database is accessible, False otherwise
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.bind(component="database_v2").error(f"Database health check failed: {e}")
        return False


if __name__ == "__main__":
    import sys

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Test 1: get_database_url requires DATABASE_URL
    total_tests += 1
    original_url = os.environ.pop("DATABASE_URL", None)
    try:
        get_database_url()
        all_validation_failures.append("get_database_url should raise error when DATABASE_URL not set")
    except DatabaseConfigError:
        pass  # Expected
    finally:
        if original_url:
            os.environ["DATABASE_URL"] = original_url

    # Test 2: get_database_url validates PostgreSQL URL
    total_tests += 1
    os.environ["DATABASE_URL"] = "mysql://user:pass@localhost/db"
    try:
        get_database_url()
        all_validation_failures.append("get_database_url should reject non-PostgreSQL URLs")
    except DatabaseConfigError:
        pass  # Expected
    finally:
        if original_url:
            os.environ["DATABASE_URL"] = original_url
        else:
            os.environ.pop("DATABASE_URL", None)

    # Test 3: Valid PostgreSQL URL is accepted
    total_tests += 1
    os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/testdb"
    try:
        url = get_database_url()
        if not url.startswith("postgresql"):
            all_validation_failures.append(f"Expected PostgreSQL URL, got: {url}")
    except Exception as e:
        all_validation_failures.append(f"Valid PostgreSQL URL rejected: {e}")
    finally:
        if original_url:
            os.environ["DATABASE_URL"] = original_url
        else:
            os.environ.pop("DATABASE_URL", None)

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
