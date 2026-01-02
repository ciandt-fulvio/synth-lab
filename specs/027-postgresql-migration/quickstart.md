# Quickstart: PostgreSQL Migration

**Feature Branch**: `027-postgresql-migration`
**Date**: 2026-01-01

## Prerequisites

- Python 3.13+
- Docker (for PostgreSQL testing)
- uv package manager

## Installation

```bash
# Install new dependencies
uv pip install -e ".[dev]"

# Dependencies added:
# - sqlalchemy>=2.0.0
# - alembic>=1.12.0
# - psycopg2-binary>=2.9.0
```

## Configuration

### Environment Variables

```bash
# SQLite (default, development)
export DATABASE_URL="sqlite:///output/synthlab.db"

# PostgreSQL (production)
export DATABASE_URL="postgresql://user:password@localhost:5432/synthlab"

# PostgreSQL with SSL
export DATABASE_URL="postgresql://user:password@host:5432/synthlab?sslmode=require"
```

### Docker PostgreSQL for Testing

```bash
# Start PostgreSQL
docker run -d \
  --name synthlab-postgres \
  -e POSTGRES_USER=synthlab \
  -e POSTGRES_PASSWORD=synthlab \
  -e POSTGRES_DB=synthlab \
  -p 5432:5432 \
  postgres:14

# Set environment
export DATABASE_URL="postgresql://synthlab:synthlab@localhost:5432/synthlab"
```

## Using SQLAlchemy Models

### Import Models

```python
from synth_lab.models import (
    Experiment,
    AnalysisRun,
    Synth,
    SynthGroup,
    SynthOutcome,
    ResearchExecution,
    Transcript,
    InterviewGuide,
    Exploration,
    ScenarioNode,
    ExperimentDocument,
)
from synth_lab.models.base import Base
```

### Create Session

```python
from synth_lab.infrastructure.database_v2 import get_session

# Using context manager
with get_session() as session:
    # Query experiments
    experiments = session.query(Experiment).filter(
        Experiment.status == "active"
    ).all()

    # Create new experiment
    experiment = Experiment(
        id="exp_12345678",
        name="Test Experiment",
        hypothesis="Users will prefer feature X",
        status="active",
        created_at="2026-01-01T10:00:00Z"
    )
    session.add(experiment)
    # Auto-commits on context exit
```

### FastAPI Dependency

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from synth_lab.infrastructure.database_v2 import get_db_session

@app.get("/experiments/{experiment_id}")
def get_experiment(
    experiment_id: str,
    db: Session = Depends(get_db_session)
):
    experiment = db.query(Experiment).filter(
        Experiment.id == experiment_id
    ).first()
    return experiment
```

## Using Alembic Migrations

Alembic is configured in `src/synth_lab/alembic/` with dual-dialect support (SQLite and PostgreSQL).

### Makefile Commands (Recommended)

```bash
# Apply all pending migrations
make alembic-upgrade

# Rollback one migration
make alembic-downgrade

# Create new migration (autogenerate from model changes)
make alembic-revision MSG="add user preferences table"

# Check current migration version
make alembic-current

# Show migration history
make alembic-history
```

### Direct Alembic Commands

```bash
# Apply all pending migrations
alembic -c src/synth_lab/alembic/alembic.ini upgrade head

# Check current version
alembic -c src/synth_lab/alembic/alembic.ini current

# Show migration history
alembic -c src/synth_lab/alembic/alembic.ini history

# Rollback one version
alembic -c src/synth_lab/alembic/alembic.ini downgrade -1

# Rollback all
alembic -c src/synth_lab/alembic/alembic.ini downgrade base
```

### Create New Migration

```bash
# After modifying ORM models, generate migration
make alembic-revision MSG="add new column to experiments"

# Review the generated file in src/synth_lab/alembic/versions/
# Then apply
make alembic-upgrade
```

### Initial Schema

The initial migration `001_initial_schema.py` creates all 17 tables:
- Core: `experiments`, `synths`, `synth_groups`
- Analysis: `analysis_runs`, `synth_outcomes`, `analysis_cache`
- Research: `research_executions`, `transcripts`, `interview_guide`
- Exploration: `explorations`, `scenario_nodes`
- Insights: `chart_insights`, `sensitivity_results`, `region_analyses`
- Documents: `experiment_documents`
- Legacy: `feature_scorecards`, `simulation_runs`

## Repository Migration Guide

### Before (sqlite3 direct)

```python
class ExperimentRepository(BaseRepository):
    def get_by_id(self, experiment_id: str) -> Experiment | None:
        row = self.db.fetchone(
            "SELECT * FROM experiments WHERE id = ?",
            (experiment_id,)
        )
        return self._row_to_entity(row) if row else None
```

### After (SQLAlchemy)

```python
from sqlalchemy.orm import Session
from synth_lab.models import Experiment

class ExperimentRepository(BaseRepository):
    def get_by_id(self, experiment_id: str) -> Experiment | None:
        return self.session.query(Experiment).filter(
            Experiment.id == experiment_id
        ).first()
```

### Migration Pattern

1. Create SQLAlchemy model in `models/`
2. Update repository to accept Session
3. Replace raw SQL with ORM queries
4. Keep same public interface
5. Test with both backends

## Testing

### Run Tests with SQLite

```bash
# Default behavior
pytest tests/

# Explicit SQLite
DATABASE_URL="sqlite:///test.db" pytest tests/
```

### Run Tests with PostgreSQL

```bash
# Start PostgreSQL container
docker compose -f docker/docker-compose.postgres.yml up -d

# Run tests
DATABASE_URL="postgresql://synthlab:synthlab@localhost:5432/synthlab_test" pytest tests/

# Stop container
docker compose -f docker/docker-compose.postgres.yml down
```

### Test Both Backends

```bash
# Run test suite against both databases
./scripts/test-dual-backend.sh
```

## Common Patterns

### JSON Fields

```python
from synth_lab.models.base import MutableJSON

class Experiment(Base):
    # MutableJSON tracks in-place changes
    scorecard_data: Mapped[dict] = mapped_column(MutableJSON, default=dict)

# Usage
experiment.scorecard_data["new_key"] = "value"
session.commit()  # Change detected automatically
```

### Soft Delete

```python
# Query active only
experiments = session.query(Experiment).filter(
    Experiment.status == "active"
).all()

# Soft delete
experiment.status = "deleted"
session.commit()
```

### Pagination

```python
from synth_lab.repositories.base import paginate

# Returns (items, total_count)
experiments, total = paginate(
    session.query(Experiment).filter(Experiment.status == "active"),
    page=1,
    per_page=20
)
```

### Transactions

```python
with get_session() as session:
    try:
        session.add(experiment)
        session.add(analysis_run)
        session.commit()
    except Exception:
        session.rollback()
        raise
```

## Troubleshooting

### Connection Issues

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Test connection
psql -h localhost -U synthlab -d synthlab -c "SELECT 1"
```

### Migration Conflicts

```bash
# If migrations are out of sync
alembic stamp head  # Mark current as latest
alembic upgrade head  # Apply any missing
```

### JSON Query Differences

```python
# Cross-database compatible
session.query(Experiment).filter(
    Experiment.scorecard_data["key"].astext == "value"
)

# PostgreSQL-only (JSONB operators)
# Avoid unless necessary
```

## Next Steps

1. Read `research.md` for architecture decisions
2. Review `data-model.md` for complete schema
3. Check `plan.md` for implementation phases
4. Run `/speckit.tasks` to generate task list
