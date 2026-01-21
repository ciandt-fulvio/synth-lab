#!/bin/bash
# Wrapper script for running E2E environment with Docker or Podman
# Uses unified docker-compose.yml with --profile test
#
# Handles compatibility issues between docker-compose and podman-compose

set -e

COMPOSE_FILE="docker/docker-compose.yml"
COMPOSE_PROFILE="test"
COMMAND="${1:-up}"

# Detect container runtime (uses docker compose v2 or podman compose)
if command -v docker &> /dev/null && docker ps &> /dev/null 2>&1; then
    RUNTIME="docker"
    COMPOSE_CMD="docker compose"
elif command -v podman &> /dev/null; then
    RUNTIME="podman"
    COMPOSE_CMD="podman compose"
else
    echo "❌ Error: Neither Docker nor Podman found"
    exit 1
fi

echo "🐳 Using: $RUNTIME"

case "$COMMAND" in
    up)
        # Full test workflow: start containers, run tests, stop containers
        echo "Starting E2E environment (profile: $COMPOSE_PROFILE)..."

        # Start containers
        if [ "$RUNTIME" = "podman" ]; then
            $COMPOSE_CMD -f "$COMPOSE_FILE" --profile "$COMPOSE_PROFILE" up --build -d --force-recreate
        else
            $COMPOSE_CMD -f "$COMPOSE_FILE" --profile "$COMPOSE_PROFILE" up --build -d
        fi

        # Wait for services to be healthy
        echo "Waiting for services to be ready..."
        sleep 10

        # Run Playwright tests from host
        echo "Running Playwright tests..."
        cd frontend && TEST_ENV=docker npm run test:e2e
        TEST_EXIT_CODE=$?

        # Return to root directory
        cd ..

        # Return test exit code
        exit $TEST_EXIT_CODE
        ;;

    up-detached)
        echo "Starting E2E environment (detached, profile: $COMPOSE_PROFILE)..."
        if [ "$RUNTIME" = "podman" ]; then
            $COMPOSE_CMD -f "$COMPOSE_FILE" --profile "$COMPOSE_PROFILE" up --build -d --force-recreate
        else
            $COMPOSE_CMD -f "$COMPOSE_FILE" --profile "$COMPOSE_PROFILE" up --build -d
        fi
        ;;

    down)
        echo "Stopping E2E environment..."
        if [ "$RUNTIME" = "podman" ]; then
            # Podman: try compose down, fallback to manual cleanup
            $COMPOSE_CMD -f "$COMPOSE_FILE" --profile "$COMPOSE_PROFILE" down -v 2>/dev/null || {
                echo "Cleaning up with podman directly..."
                podman rm -f synthlab-postgres-test synthlab-backend-test synthlab-frontend-test 2>/dev/null || true
                podman pod rm -f pod_docker 2>/dev/null || true
            }
        else
            $COMPOSE_CMD -f "$COMPOSE_FILE" --profile "$COMPOSE_PROFILE" down -v
        fi
        ;;

    logs)
        $COMPOSE_CMD -f "$COMPOSE_FILE" --profile "$COMPOSE_PROFILE" logs -f
        ;;

    *)
        echo "Usage: $0 {up|up-detached|down|logs}"
        exit 1
        ;;
esac
