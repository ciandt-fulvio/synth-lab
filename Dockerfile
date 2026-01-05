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

# Expose port (Railway sets PORT env var)
EXPOSE 8000

# Start command
CMD ["sh", "-c", "uvicorn synth_lab.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
