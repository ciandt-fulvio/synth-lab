#!/bin/bash
set -e

echo "==================================="
echo "synth-lab Backend Entrypoint"
echo "==================================="

# ============================================================================
# Migrations (conditional - only for E2E environments)
# ============================================================================
# For staging/production deployments, migrations are handled by GitHub Actions
# workflow BEFORE the container starts. Only E2E environments should run
# migrations from the entrypoint.
# ============================================================================
if [ "${RUN_MIGRATIONS}" = "true" ]; then
    echo ""
    echo "[1/3] Running Alembic migrations..."
    alembic -c src/synth_lab/alembic/alembic.ini upgrade head
    echo "✅ Migrations completed"
else
    echo ""
    echo "[1/3] Skipping migrations (handled by deployment workflow)"
    echo "    Set RUN_MIGRATIONS=true to enable migrations in entrypoint"
fi

# ============================================================================
# Database Seeding (conditional - only for E2E environments)
# ============================================================================
# For staging/production deployments, seeding is handled by GitHub Actions
# workflow BEFORE the container starts. Only E2E environments should run
# seeding from the entrypoint.
# ============================================================================
if [ "${SEED_E2E_DATABASE}" = "true" ]; then
    echo ""
    echo "[2/3] Seeding test database..."
    python -c "
from sqlalchemy import create_engine
from tests.fixtures.seed_test import seed_database
import os

database_url = os.getenv('DATABASE_URL')
if not database_url:
    raise ValueError('DATABASE_URL environment variable is required')

print(f'Connecting to: {database_url}')
engine = create_engine(database_url)
seed_database(engine)
print('✅ Database seeded successfully')
"
else
    echo ""
    echo "[2/3] Skipping database seeding (not an E2E environment)"
    echo "    For E2E: Set SEED_E2E_DATABASE=true to enable seeding"
fi

echo ""
echo "[3/3] Starting backend server..."
echo "Backend will be available at http://localhost:\${PORT:-8000}"
echo ""

# Execute the command passed to the container (uvicorn by default)
exec "$@"
