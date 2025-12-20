#!/bin/bash
# Start the synth-lab REST API server
# Usage: ./scripts/start_api.sh [port]

PORT=${1:-8000}
HOST=${2:-127.0.0.1}

echo "Starting synth-lab API on http://${HOST}:${PORT}"
echo "OpenAPI docs: http://${HOST}:${PORT}/docs"
echo ""

uv run uvicorn synth_lab.api.main:app --host "${HOST}" --port "${PORT}" --reload
