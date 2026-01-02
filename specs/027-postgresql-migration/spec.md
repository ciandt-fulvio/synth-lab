# Feature Specification: PostgreSQL Migration with SQLAlchemy

**Feature Branch**: `027-postgresql-migration`
**Created**: 2026-01-01
**Status**: Draft
**Input**: User description: "precisamos passar a usar o postgresql ao invés do SQLite usando o SQLAlchemy + Alembic. Plano de migração em fases: Fase 1 - Instalar SQLAlchemy + Alembic, criar models. Fase 2 - Criar database_v2.py com SQLAlchemy engine. Fase 3 - Migrar repositories um a um para usar SQLAlchemy. Fase 4 - Gerar migration inicial do schema atual. Fase 5 - Testar com PostgreSQL local Docker. Fase 6 - Remover database.py antigo e sqlite3."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Seamless Database Operations During Migration (Priority: P1)

During the phased migration, developers and users can continue using the application without interruption. The system maintains full functionality whether running on SQLite or PostgreSQL, with no data loss during the transition period.

**Why this priority**: Business continuity is critical. Users cannot tolerate application downtime or data corruption during infrastructure changes. This is the foundation that enables all other migration work.

**Independent Test**: Can be tested by running the full application test suite against both SQLite and PostgreSQL databases and verifying identical behavior and data integrity.

**Acceptance Scenarios**:

1. **Given** the system is running with SQLite, **When** a new repository is migrated to SQLAlchemy, **Then** all existing functionality continues to work without modification to API endpoints or services.

2. **Given** repositories are partially migrated (some using old database.py, some using SQLAlchemy), **When** the application handles concurrent requests, **Then** all operations complete successfully with proper transaction isolation.

3. **Given** data exists in the SQLite database, **When** the system switches to PostgreSQL, **Then** all existing data is accessible with identical query results.

---

### User Story 2 - PostgreSQL Production Deployment (Priority: P2)

Operations team can deploy the application with PostgreSQL as the production database. The deployment supports standard PostgreSQL configurations including connection pooling, SSL connections, and environment-based configuration.

**Why this priority**: PostgreSQL brings critical production-grade features (better concurrency, ACID compliance, replication support) needed for scaling the application. This unlocks enterprise deployment scenarios.

**Independent Test**: Can be tested by deploying the application in a Docker environment with PostgreSQL and verifying all CRUD operations, concurrent access, and connection management work correctly.

**Acceptance Scenarios**:

1. **Given** a PostgreSQL server is available, **When** the application starts with PostgreSQL connection string in environment, **Then** the application connects and initializes the schema successfully.

2. **Given** PostgreSQL is configured with SSL, **When** the application connects, **Then** the connection uses encrypted transport.

3. **Given** multiple application instances connect to PostgreSQL, **When** concurrent writes occur, **Then** transactions are isolated correctly with no data corruption.

---

### User Story 3 - Database Schema Version Control (Priority: P2)

Developers can manage database schema changes through version-controlled migrations. Each schema change is tracked, reversible, and can be applied consistently across all environments (development, staging, production).

**Why this priority**: Professional database management requires reproducible schema changes. This enables team collaboration, safe rollbacks, and audit trails for compliance requirements.

**Independent Test**: Can be tested by creating a migration, applying it to a fresh database, reverting it, and re-applying it, verifying the schema matches expected state at each step.

**Acceptance Scenarios**:

1. **Given** a developer creates a new migration, **When** the migration is applied, **Then** the database schema updates accordingly and the migration is recorded in version history.

2. **Given** a migration has been applied, **When** a rollback is triggered, **Then** the schema reverts to the previous state.

3. **Given** a fresh database, **When** all migrations are applied in sequence, **Then** the final schema matches the current production schema exactly.

---

### User Story 4 - Legacy Database Cleanup (Priority: P3)

After successful migration validation, the legacy SQLite code can be safely removed. The codebase is simplified with a single database abstraction, reducing maintenance burden and potential confusion.

**Why this priority**: Code cleanup improves maintainability and reduces technical debt. This is lower priority because it only happens after full migration validation and does not add new functionality.

**Independent Test**: Can be tested by removing legacy database.py, running the full test suite, and verifying no import errors or functionality regressions occur.

**Acceptance Scenarios**:

1. **Given** all repositories have been migrated to SQLAlchemy, **When** the legacy database.py is removed, **Then** the application compiles and runs without errors.

2. **Given** the SQLite dependencies are removed, **When** the application is deployed, **Then** no SQLite-related packages are installed.

---

### Edge Cases

- What happens when PostgreSQL connection is lost mid-transaction? System should rollback the transaction and return appropriate error to the caller.
- What happens when migration is interrupted? Alembic should track partial migration state and allow resume or rollback.
- How does the system handle PostgreSQL-specific SQL syntax differences from SQLite? SQLAlchemy ORM abstracts differences; any raw SQL queries must be parameterized using SQLAlchemy's text() with dialect-aware syntax.
- What happens if a repository is used during migration transition (hybrid state)? Both database connections should work independently without cross-contamination.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support SQLAlchemy ORM models that map to all 19 existing database tables (experiments, synths, synth_groups, analysis_runs, synth_outcomes, research_executions, transcripts, interview_guide, analysis_cache, chart_insights, sensitivity_results, region_analyses, explorations, scenario_nodes, experiment_documents, feature_scorecards, simulation_runs).

- **FR-002**: System MUST provide Alembic migration support with ability to generate, apply, and rollback schema migrations.

- **FR-003**: System MUST maintain backward compatibility with existing repository interfaces during migration (repositories continue to expose same public methods with identical signatures).

- **FR-004**: System MUST support database connection configuration via environment variables (DATABASE_URL format for PostgreSQL, legacy SYNTHLAB_DB_PATH for SQLite fallback).

- **FR-005**: System MUST preserve all foreign key relationships and constraints in SQLAlchemy models (e.g., synths -> synth_groups, analysis_runs -> experiments, synth_outcomes -> analysis_runs).

- **FR-006**: System MUST handle JSON fields correctly for both SQLite (JSON1 extension) and PostgreSQL (native JSONB type).

- **FR-007**: System MUST provide transaction management with automatic commit/rollback semantics matching current behavior.

- **FR-008**: System MUST support connection pooling for PostgreSQL deployments.

- **FR-009**: System MUST generate an initial Alembic migration that creates schema equivalent to current SQLite schema (version 15).

- **FR-010**: System MUST maintain soft-delete pattern for experiments (status='deleted' instead of hard delete).

- **FR-011**: System MUST preserve thread-safety characteristics of the current implementation for multi-threaded access patterns.

- **FR-012**: System MUST support pagination patterns currently implemented in BaseRepository.

### Key Entities

- **SQLAlchemy Base**: Declarative base class for all ORM models with common configurations (naming conventions, JSON serialization).

- **Session Factory**: Scoped session factory providing thread-local session management with configurable isolation levels.

- **Database Engine**: SQLAlchemy engine configured for either SQLite (file-based) or PostgreSQL (connection pool) based on environment.

- **Alembic Environment**: Migration environment with support for offline generation, online apply, and revision history tracking.

- **Repository Base v2**: Updated base repository class using SQLAlchemy sessions instead of raw sqlite3 connections.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All existing application tests pass with both SQLite and PostgreSQL backends without test modifications (100% compatibility).

- **SC-002**: Application handles 100 concurrent database operations without connection errors or deadlocks on PostgreSQL.

- **SC-003**: Schema migrations can be applied to a fresh database in under 30 seconds.

- **SC-004**: Schema migrations can be rolled back completely, returning database to previous state with data intact.

- **SC-005**: Repository migration can be completed incrementally, with each repository migrated independently without breaking other repositories.

- **SC-006**: Data migration from existing SQLite database to PostgreSQL preserves all records with 100% fidelity (no data loss or corruption).

- **SC-007**: Application startup time with PostgreSQL is within 5 seconds (including connection pool initialization).

- **SC-008**: All 18 repository files are migrated to use SQLAlchemy with no remaining direct sqlite3 imports.

## Assumptions

- PostgreSQL version 14+ will be used in production environments.
- Docker will be available for local PostgreSQL testing.
- Existing SQLite data can be exported and imported during migration (one-time migration script acceptable).
- Application restarts are acceptable during final switchover from SQLite to PostgreSQL.
- JSON fields in SQLite use standard JSON format compatible with PostgreSQL JSONB.
- Current schema version (v15) is stable and no schema changes will be introduced during migration.

## Dependencies

- SQLAlchemy 2.0+ (async support if needed in future).
- Alembic 1.12+ for migrations.
- psycopg2-binary or asyncpg for PostgreSQL driver.
- Existing DatabaseManager interface must remain stable during migration period.
