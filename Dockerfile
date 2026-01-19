# Dockerfile for Railway deployment
FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install uv for fast package management
RUN pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/

# Install dependencies using uv
RUN uv pip install --system -e .

# Copy alembic configuration
COPY src/synth_lab/alembic/ ./src/synth_lab/alembic/

# Expose port (Railway sets PORT env var)
EXPOSE 8000

# Create entrypoint script that runs migrations before starting the server
RUN echo '#!/bin/sh\n\
set -e\n\
echo "Running Alembic migrations..."\n\
alembic -c src/synth_lab/alembic/alembic.ini upgrade head\n\
echo "Migrations completed. Starting server..."\n\
exec uvicorn synth_lab.api.main:app --host 0.0.0.0 --port ${PORT:-8000}\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Start command with migrations
CMD ["/app/entrypoint.sh"]
