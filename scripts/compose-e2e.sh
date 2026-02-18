#!/bin/bash
# Wrapper script for running E2E environment with Docker or Podman
# Uses unified docker-compose.yml with --profile test
#
# Features:
# - Automatic rebuild detection: only rebuilds when frontend/backend changed
# - Handles compatibility issues between docker-compose and podman-compose

set -e

COMPOSE_FILE="docker/docker-compose.yml"
ENV_FILE="docker/.env.test"
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

# Check if frontend image needs rebuild (compares image timestamp with source files)
needs_frontend_rebuild() {
    local image_name="docker_frontend-test"

    # If image doesn't exist, need to build
    if ! $RUNTIME image inspect "$image_name" &>/dev/null 2>&1; then
        echo "   📦 Frontend image not found, will build..."
        return 0
    fi

    # Get image creation timestamp in seconds since epoch
    local image_created_epoch=$($RUNTIME image inspect "$image_name" --format='{{.Created}}')

    # Convert to epoch seconds (works on both Linux and macOS)
    if date -j -f "%Y-%m-%d %H:%M:%S" "2020-01-01 00:00:00" +%s &>/dev/null; then
        # macOS date
        image_created_epoch=$(echo "$image_created_epoch" | sed 's/\.[0-9]* \+0000 UTC//' | xargs -I {} date -j -f "%Y-%m-%d %H:%M:%S" "{}" +%s 2>/dev/null)
    else
        # GNU date (Linux)
        image_created_epoch=$(date -d "$image_created_epoch" +%s 2>/dev/null)
    fi

    # Check if any frontend source files were modified after the image (by comparing epoch times)
    local has_newer=0
    for file in $(find frontend/src frontend/package.json frontend/vite.config.ts frontend/Dockerfile -type f 2>/dev/null); do
        if [ -f "$file" ]; then
            local file_epoch=$(stat -f %m "$file" 2>/dev/null || stat -c %Y "$file" 2>/dev/null)
            if [ "$file_epoch" -gt "$image_created_epoch" ]; then
                has_newer=1
                break
            fi
        fi
    done

    if [ "$has_newer" -eq 1 ]; then
        echo "   🔄 Frontend changes detected (newer than image), will rebuild..."
        return 0
    fi

    echo "   ✅ No frontend changes, using cached image"
    return 1
}

# Check if backend image needs rebuild (compares image timestamp with source files)
needs_backend_rebuild() {
    local image_name="docker_backend-test"

    # If image doesn't exist, need to build
    if ! $RUNTIME image inspect "$image_name" &>/dev/null 2>&1; then
        echo "   📦 Backend image not found, will build..."
        return 0
    fi

    # Get image creation timestamp in seconds since epoch
    local image_created_epoch=$($RUNTIME image inspect "$image_name" --format='{{.Created}}')

    # Convert to epoch seconds (works on both Linux and macOS)
    if date -j -f "%Y-%m-%d %H:%M:%S" "2020-01-01 00:00:00" +%s &>/dev/null; then
        # macOS date
        image_created_epoch=$(echo "$image_created_epoch" | sed 's/\.[0-9]* \+0000 UTC//' | xargs -I {} date -j -f "%Y-%m-%d %H:%M:%S" "{}" +%s 2>/dev/null)
    else
        # GNU date (Linux)
        image_created_epoch=$(date -d "$image_created_epoch" +%s 2>/dev/null)
    fi

    # Check if any backend source files were modified after the image (by comparing epoch times)
    local has_newer=0
    for file in $(find src pyproject.toml Dockerfile -type f 2>/dev/null); do
        if [ -f "$file" ]; then
            local file_epoch=$(stat -f %m "$file" 2>/dev/null || stat -c %Y "$file" 2>/dev/null)
            if [ "$file_epoch" -gt "$image_created_epoch" ]; then
                has_newer=1
                break
            fi
        fi
    done

    if [ "$has_newer" -eq 1 ]; then
        echo "   🔄 Backend changes detected (newer than image), will rebuild..."
        return 0
    fi

    echo "   ✅ No backend changes, using cached image"
    return 1
}

# Cleanup function for Podman (handles orphaned pods/containers/networks)
cleanup_podman() {
    echo "🧹 Cleaning up previous test environment..."

    # Stop and remove test containers (ignore errors if they don't exist)
    podman stop synthlab-postgres-test synthlab-backend-test synthlab-frontend-test 2>/dev/null || true
    podman rm -f synthlab-postgres-test synthlab-backend-test synthlab-frontend-test 2>/dev/null || true

    # Remove any pods created by podman-compose (pod name contains "docker")
    for pod in $(podman pod ls -q --filter "name=docker" 2>/dev/null); do
        podman pod rm -f "$pod" 2>/dev/null || true
    done

    # Clean up test network (must be after containers/pods are removed)
    podman network rm -f synthlab-test-network 2>/dev/null || true
}

case "$COMMAND" in
    up)
        # Deprecated: Use up-detached and run tests separately for better control
        echo -e "${YELLOW}⚠️  'up' command is deprecated. Use 'make test-e2e' instead.${NC}"
        echo -e "${YELLOW}   This command now behaves like 'up-detached' (starts environment only).${NC}"
        echo ""

        # Pre-cleanup for Podman to handle orphaned pods/containers
        if [ "$RUNTIME" = "podman" ]; then
            cleanup_podman
        fi

        # Check if we need to rebuild images
        echo "🔍 Checking for changes..."
        BUILD_FLAG=""
        if needs_frontend_rebuild || needs_backend_rebuild; then
            BUILD_FLAG="--build"
        fi

        # Start containers
        if [ "$RUNTIME" = "podman" ]; then
            $COMPOSE_CMD -f "$COMPOSE_FILE" --env-file "$ENV_FILE" --profile "$COMPOSE_PROFILE" up $BUILD_FLAG -d --force-recreate
        else
            $COMPOSE_CMD -f "$COMPOSE_FILE" --env-file "$ENV_FILE" --profile "$COMPOSE_PROFILE" up $BUILD_FLAG -d
        fi

        # Wait for services to be healthy
        echo "Waiting for services to be ready..."
        sleep 10

        echo ""
        echo -e "${GREEN}✅ E2E environment ready!${NC}"
        echo -e "${BLUE}   Run tests with: ./scripts/run-e2e-tests-smart.sh${NC}"
        echo -e "${BLUE}   Or use: make test-e2e${NC}"
        echo ""
        ;;

    up-detached)
        echo "Starting E2E environment (detached, profile: $COMPOSE_PROFILE)..."

        # Pre-cleanup for Podman to handle orphaned pods/containers
        if [ "$RUNTIME" = "podman" ]; then
            cleanup_podman
        fi

        # Check if we need to rebuild images
        echo "🔍 Checking for changes..."
        BUILD_FLAG=""
        if needs_frontend_rebuild || needs_backend_rebuild; then
            BUILD_FLAG="--build"
        fi

        if [ "$RUNTIME" = "podman" ]; then
            $COMPOSE_CMD -f "$COMPOSE_FILE" --env-file "$ENV_FILE" --profile "$COMPOSE_PROFILE" up $BUILD_FLAG -d --force-recreate
        else
            $COMPOSE_CMD -f "$COMPOSE_FILE" --env-file "$ENV_FILE" --profile "$COMPOSE_PROFILE" up $BUILD_FLAG -d
        fi
        ;;

    down)
        echo "Stopping E2E environment..."
        if [ "$RUNTIME" = "podman" ]; then
            # Podman: try compose down first, then use cleanup function
            # NOTE: do NOT use -v here — it would remove ALL named volumes including
            # the dev database volume (synthlab-postgres-dev-data)
            $COMPOSE_CMD -f "$COMPOSE_FILE" --env-file "$ENV_FILE" --profile "$COMPOSE_PROFILE" down 2>/dev/null || true
            cleanup_podman
        else
            # NOTE: do NOT use -v here — it would remove ALL named volumes including
            # the dev database volume (synthlab-postgres-dev-data), wiping dev data
            $COMPOSE_CMD -f "$COMPOSE_FILE" --env-file "$ENV_FILE" --profile "$COMPOSE_PROFILE" down
        fi
        # Remove ONLY the test database volume so postgres-test starts fresh next run.
        # We do this explicitly instead of using `down -v` which would also delete
        # synthlab-postgres-dev-data (the development database).
        echo "🧹 Removing test database volume (synthlab-postgres-test-data)..."
        $RUNTIME volume rm -f synthlab-postgres-test-data 2>/dev/null || true
        ;;

    logs)
        $COMPOSE_CMD -f "$COMPOSE_FILE" --env-file "$ENV_FILE" --profile "$COMPOSE_PROFILE" logs -f
        ;;

    *)
        echo "Usage: $0 {up|up-detached|down|logs}"
        echo ""
        echo "Commands:"
        echo "  up          - Start E2E environment and run tests (auto-detects changes)"
        echo "  up-detached - Start E2E environment without running tests"
        echo "  down        - Stop E2E environment"
        echo "  logs        - Show logs from E2E services"
        echo ""
        echo "Note: Rebuild is automatic when source files are newer than Docker images"
        exit 1
        ;;
esac
