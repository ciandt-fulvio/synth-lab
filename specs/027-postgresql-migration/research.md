# Research: PostgreSQL Migration with SQLAlchemy

**Feature Branch**: `027-postgresql-migration`
**Date**: 2026-01-01
**Status**: Complete

## Research Topics

This document consolidates research findings for migrating synth-lab from SQLite to PostgreSQL using SQLAlchemy 2.0+ and Alembic.

---

## 1. Dual Database Support (SQLite + PostgreSQL)

### Decision
Use a factory function that creates database engines based on environment configuration. SQLAlchemy 2.0 determines the dialect at engine creation time from the connection URL.

### Rationale
- SQLAlchemy 2.0 requires separate engine instances for each dialect
- Environment-based configuration allows seamless switching between SQLite (development) and PostgreSQL (production)
- Factory pattern enables easy testing with different backends

### Alternatives Considered
| Alternative | Rejected Because |
|-------------|------------------|
| Runtime dialect switching | SQLAlchemy 2.0 fixes dialect at engine creation; not possible |
| Abstract database layer | Over-engineering; SQLAlchemy ORM already provides abstraction |
| Database-per-service | Not applicable for monolithic application structure |

### Implementation Pattern

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool, StaticPool
import os

def get_database_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite:///output/synthlab.db")

def create_db_engine(database_url: str | None = None):
    url = database_url or get_database_url()

    if url.startswith("sqlite:"):
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool if ":memory:" in url else QueuePool,
            pool_pre_ping=True,
        )
    else:
        return create_engine(
            url,
            pool_size=10,
            max_overflow=20,
            pool_recycle=300,
            pool_pre_ping=True,
            pool_use_lifo=True,
        )
```

### Caveats
- SQLite requires `check_same_thread=False` for FastAPI multi-threaded access
- In-memory SQLite should use `StaticPool` to maintain single connection
- PostgreSQL pool sizing must not exceed server's `max_connections`

---

## 2. JSON Field Handling (Cross-Database)

### Decision
Use `JSON().with_variant(JSONB(), "postgresql")` for JSON columns. This automatically uses JSONB on PostgreSQL and standard JSON on SQLite.

### Rationale
- PostgreSQL JSONB provides better indexing and query performance
- SQLite JSON1 extension has different operator support
- `with_variant()` is SQLAlchemy's official cross-dialect pattern

### Alternatives Considered
| Alternative | Rejected Because |
|-------------|------------------|
| Always use JSON (not JSONB) | Loses PostgreSQL JSONB performance benefits |
| Separate column types per dialect | Requires duplicate model definitions |
| Store as TEXT with manual serialization | Loses native JSON operators and indexing |

### Implementation Pattern

```python
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.mutable import MutableDict

# Cross-database JSON type
JSONVariant = JSON().with_variant(JSONB(), "postgresql")

class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Use MutableDict for in-place change detection
    scorecard_data: Mapped[dict] = mapped_column(
        MutableDict.as_mutable(JSONVariant),
        default=dict
    )
```

### Caveats
- JSON/JSONB does NOT detect in-place mutations by default; use `MutableDict.as_mutable()`
- JSONB operators like `contains()`, `has_key()` are PostgreSQL-only
- SQLite requires version 3.38.0+ for built-in JSON or JSON1 extension
- GIN indexes on JSONB available only on PostgreSQL

---

## 3. Alembic Multi-Dialect Migrations

### Decision
Enable `render_as_batch=True` in Alembic's `env.py`. This uses SQLite's "move and copy" workflow automatically when needed while working normally on PostgreSQL.

### Rationale
- SQLite cannot DROP columns or ALTER constraints directly
- Batch mode handles table recreation transparently
- Same migration scripts work on both databases

### Alternatives Considered
| Alternative | Rejected Because |
|-------------|------------------|
| Separate migration files per dialect | Doubles maintenance burden; drift risk |
| Raw SQL with dialect conditionals | Error-prone; loses Alembic benefits |
| SQLite-only development | Masks PostgreSQL-specific issues until production |

### Implementation Pattern

```python
# alembic/env.py
def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # CRITICAL for SQLite
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()
```

### Dialect-Specific Operations

```python
def upgrade() -> None:
    with op.batch_alter_table('experiments') as batch_op:
        batch_op.add_column(sa.Column('new_field', sa.String(100)))

    # PostgreSQL-specific (GIN index on JSONB)
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute("CREATE INDEX ix_exp_scorecard ON experiments USING GIN (scorecard_data)")
```

### Caveats
- Batch operations recreate the entire table (slow for large tables)
- Always test migrations on both SQLite and PostgreSQL
- PostgreSQL ENUM types require dialect-specific handling

---

## 4. Session Management for FastAPI

### Decision
Use dependency injection with `sessionmaker` context managers. Avoid `scoped_session` which is discouraged for async applications.

### Rationale
- SQLAlchemy 2.0 documentation explicitly discourages scoped sessions for asyncio
- Dependency injection integrates cleanly with FastAPI
- Clear session lifecycle with automatic commit/rollback

### Alternatives Considered
| Alternative | Rejected Because |
|-------------|------------------|
| scoped_session | Relies on mutable global state; requires explicit teardown |
| Global session | Thread-unsafe; violates isolation |
| Manual session in every function | Code duplication; error-prone cleanup |

### Implementation Pattern

```python
from sqlalchemy.orm import Session, sessionmaker
from collections.abc import Generator

SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)

def get_db_session() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions."""
    with SessionFactory() as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
```

### Caveats
- Set `expire_on_commit=False` to prevent lazy-loading issues after commit
- Each request gets its own session; never share across requests
- Decide commit location (dependency vs service) and be consistent

---

## 5. Connection Pooling for PostgreSQL

### Decision
Use `QueuePool` (default) with `pool_pre_ping=True` and `pool_use_lifo=True`. Size pool based on worker count.

### Rationale
- `pool_pre_ping` validates connections before use (prevents stale connection errors)
- `pool_use_lifo` allows server-side cleanup of idle connections
- Worker-based sizing prevents connection exhaustion

### Alternatives Considered
| Alternative | Rejected Because |
|-------------|------------------|
| NullPool (no pooling) | Performance impact; connection overhead per query |
| External pooler (PgBouncer) | Added infrastructure complexity; not needed for single-instance |
| Static pool size | Doesn't scale with worker count |

### Implementation Pattern

```python
worker_count = int(os.getenv("WORKERS", "4"))

engine = create_engine(
    database_url,
    pool_size=worker_count * 2,      # Persistent connections
    max_overflow=worker_count * 4,    # Burst capacity
    pool_recycle=1800,                # 30 min recycling
    pool_pre_ping=True,               # Validate before use
    pool_use_lifo=True,               # Better idle cleanup
    pool_timeout=30,                  # Wait time for connection
)
```

### Production Configuration Reference

| Parameter | Development | Production |
|-----------|-------------|------------|
| `pool_size` | 5 | 10-20 |
| `max_overflow` | 10 | 20-40 |
| `pool_recycle` | 3600 | 1800 |
| `pool_timeout` | 30 | 30 |
| `pool_pre_ping` | True | True |
| `pool_use_lifo` | False | True |

### Caveats
- Total connections = `pool_size + max_overflow` must not exceed PostgreSQL `max_connections`
- Multi-process deployment: each Uvicorn worker gets its own pool
- `pool_pre_ping` adds `SELECT 1` overhead per checkout

---

## Summary of Key Decisions

| Topic | Decision | Key Configuration |
|-------|----------|-------------------|
| **Dual Database** | Factory function with environment URL | `DATABASE_URL` env var |
| **JSON Fields** | `JSON().with_variant(JSONB())` | Plus `MutableDict.as_mutable()` |
| **Alembic Migrations** | `render_as_batch=True` | In `env.py` configuration |
| **Session Management** | Dependency injection with sessionmaker | `expire_on_commit=False` |
| **Connection Pooling** | QueuePool with pre_ping and LIFO | Size = workers * 2 |

---

## References

- [SQLAlchemy 2.0 Engine Configuration](https://docs.sqlalchemy.org/en/20/core/engines.html)
- [SQLAlchemy 2.0 Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)
- [Alembic Batch Migrations](https://alembic.sqlalchemy.org/en/latest/batch.html)
- [FastAPI SQL Databases Tutorial](https://fastapi.tiangolo.com/tutorial/sql-databases/)
