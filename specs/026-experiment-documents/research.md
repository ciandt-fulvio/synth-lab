# Research: Unified Experiment Documents

**Feature**: 026-experiment-documents
**Date**: 2025-12-31
**Status**: Complete

## Overview

This feature is a "finalization" task - all major components already exist. Research focused on identifying gaps in the existing implementation.

## Research Findings

### 1. Database Schema Gap

**Question**: Why is the `experiment_documents` table not being populated?

**Finding**: The table is not defined in the main `SCHEMA_SQL` in `database.py`. It was only created in test fixtures within the repository and service files.

**Decision**: Add the table definition to `SCHEMA_SQL` and create a migration in `init_database()` for existing databases.

**Rationale**: Following the existing migration pattern (v10, v11, v14) ensures backward compatibility and consistency.

**Alternatives Considered**:
- Alembic migration: Rejected because the project doesn't use Alembic for SQLite migrations (uses inline PRAGMA checks)
- Separate migration script: Rejected because the inline pattern is simpler and already established

### 2. Router Registration Gap

**Question**: Why don't the document API endpoints work?

**Finding**: The documents router at `api/routers/documents.py` is never imported or registered in `main.py`.

**Decision**: Import and register the router following the existing pattern.

**Rationale**: Consistent with how other routers are registered (experiments, analysis, insights, etc.)

### 3. Import Path Bug

**Question**: Why does the documents router fail when called?

**Finding**: The router imports `get_db` from `infrastructure.database`, but `get_db` is actually defined in `api.dependencies`.

**Decision**: Fix the import to use `synth_lab.api.dependencies.get_db`.

**Rationale**: This matches how other routers get the database instance.

### 4. Existing Implementation Quality

**Question**: Is the existing implementation correct and complete?

**Finding**: Yes, the existing code follows project patterns:
- Entity: Uses Pydantic, proper ID format, validation
- Repository: Extends BaseRepository, uses parameterized queries
- Service: Delegates to repository, proper logging
- Router: FastAPI patterns, proper error handling
- Schemas: Pydantic models for API serialization
- Frontend: Types, hooks, services all implemented

**Decision**: No changes needed to existing implementation code.

## Technologies Confirmed

| Component | Technology | Version | Notes |
|-----------|------------|---------|-------|
| Database | SQLite 3 | 3.x | JSON1 extension, WAL mode |
| Backend | FastAPI | 0.109+ | Async support |
| ORM | None | - | Raw SQL with parameterized queries |
| Testing | pytest | 8.0+ | With pytest-asyncio |

## Migration Pattern Reference

The project uses inline migrations in `init_database()`:

```python
# Pattern from v10, v11, v14:
cursor = conn.execute("PRAGMA table_info(table_name)")
columns = [row[1] for row in cursor.fetchall()]
if "column_name" not in columns:
    logger.info("Migrating table: adding column")
    conn.execute("ALTER TABLE ...")
    conn.commit()
    logger.info("Migration completed")
```

For new tables, use `CREATE TABLE IF NOT EXISTS` in schema, plus explicit check/creation in migration section.

## No Outstanding Questions

All technical questions have been resolved. The implementation can proceed.
