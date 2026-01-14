#!/bin/bash
set -e

echo "==================================="
echo "synth-lab Backend E2E Environment"
echo "==================================="

echo ""
echo "[1/3] Running Alembic migrations..."
alembic -c src/synth_lab/alembic/alembic.ini upgrade head
echo "✅ Migrations completed"

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

echo ""
echo "[3/3] Starting backend server..."
echo "Backend will be available at http://localhost:8000"
echo ""

# Execute the command passed to the container (uvicorn by default)
exec "$@"
