#!/bin/bash
#
# Deploy a Docker image to Railway using the GraphQL API
#
# This script enables "Build Once, Deploy Anywhere" by deploying
# pre-built images from GHCR to Railway instead of building on Railway.
#
# Usage:
#   ./scripts/railway-deploy-image.sh <service-name> <image-url> <environment>
#
# Examples:
#   ./scripts/railway-deploy-image.sh synth-lab-api ghcr.io/owner/synth-lab-api:abc123 staging
#   ./scripts/railway-deploy-image.sh synth-lab-frontend ghcr.io/owner/synth-lab-frontend:abc123 production
#
# Environment variables required:
#   RAILWAY_API_TOKEN   - Railway API token with deploy permissions
#   RAILWAY_PROJECT_ID  - Railway project ID
#
# Note: The service must already be configured in Railway with Docker Image source.
# First-time setup requires manual configuration in Railway UI:
#   1. Go to Service Settings > Source
#   2. Select "Docker Image"
#   3. Enter the initial image URL
#   After that, this script can update the image for deployments.

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================

RAILWAY_API_URL="https://backboard.railway.app/graphql/v2"

# =============================================================================
# Arguments
# =============================================================================

SERVICE_NAME="${1:-}"
IMAGE_URL="${2:-}"
ENVIRONMENT="${3:-staging}"

if [[ -z "$SERVICE_NAME" || -z "$IMAGE_URL" ]]; then
    echo "Usage: $0 <service-name> <image-url> [environment]"
    echo ""
    echo "Arguments:"
    echo "  service-name   Railway service name (e.g., synth-lab-api)"
    echo "  image-url      Full Docker image URL with tag"
    echo "  environment    Railway environment (default: staging)"
    exit 1
fi

# =============================================================================
# Validate environment variables
# =============================================================================

if [[ -z "${RAILWAY_API_TOKEN:-}" ]]; then
    echo "Error: RAILWAY_API_TOKEN environment variable is required"
    exit 1
fi

if [[ -z "${RAILWAY_PROJECT_ID:-}" ]]; then
    echo "Error: RAILWAY_PROJECT_ID environment variable is required"
    exit 1
fi

# =============================================================================
# Helper functions
# =============================================================================

railway_graphql() {
    local query="$1"

    response=$(curl -s -X POST "$RAILWAY_API_URL" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $RAILWAY_API_TOKEN" \
        -d "$query")

    # Check for errors
    if echo "$response" | jq -e '.errors' > /dev/null 2>&1; then
        echo "GraphQL Error:" >&2
        echo "$response" | jq '.errors' >&2
        return 1
    fi

    echo "$response"
}

# =============================================================================
# Get Environment ID
# =============================================================================

echo "Fetching environment ID for '$ENVIRONMENT'..."

ENV_QUERY=$(cat <<EOF
{
    "query": "query { project(id: \"$RAILWAY_PROJECT_ID\") { environments { edges { node { id name } } } } }"
}
EOF
)

ENV_RESPONSE=$(railway_graphql "$ENV_QUERY")
ENVIRONMENT_ID=$(echo "$ENV_RESPONSE" | jq -r ".data.project.environments.edges[] | select(.node.name == \"$ENVIRONMENT\") | .node.id")

if [[ -z "$ENVIRONMENT_ID" || "$ENVIRONMENT_ID" == "null" ]]; then
    echo "Error: Environment '$ENVIRONMENT' not found in project"
    echo "Available environments:"
    echo "$ENV_RESPONSE" | jq -r '.data.project.environments.edges[].node.name'
    exit 1
fi

echo "Environment ID: $ENVIRONMENT_ID"

# =============================================================================
# Get Service ID
# =============================================================================

echo "Fetching service ID for '$SERVICE_NAME'..."

SERVICE_QUERY=$(cat <<EOF
{
    "query": "query { project(id: \"$RAILWAY_PROJECT_ID\") { services { edges { node { id name } } } } }"
}
EOF
)

SERVICE_RESPONSE=$(railway_graphql "$SERVICE_QUERY")
SERVICE_ID=$(echo "$SERVICE_RESPONSE" | jq -r ".data.project.services.edges[] | select(.node.name == \"$SERVICE_NAME\") | .node.id")

if [[ -z "$SERVICE_ID" || "$SERVICE_ID" == "null" ]]; then
    echo "Error: Service '$SERVICE_NAME' not found in project"
    echo "Available services:"
    echo "$SERVICE_RESPONSE" | jq -r '.data.project.services.edges[].node.name'
    exit 1
fi

echo "Service ID: $SERVICE_ID"

# =============================================================================
# Verify Image Exists in Registry
# =============================================================================

echo "Verifying image exists in registry..."

# Extract registry, image name, and tag
REGISTRY_URL=$(echo "$IMAGE_URL" | cut -d'/' -f1)
IMAGE_PATH=$(echo "$IMAGE_URL" | cut -d':' -f1)
IMAGE_TAG=$(echo "$IMAGE_URL" | cut -d':' -f2)

echo "  Registry: $REGISTRY_URL"
echo "  Image:    $IMAGE_PATH"
echo "  Tag:      $IMAGE_TAG"

# Try to pull the image to verify it exists
# Use skopeo if available (doesn't require downloading the full image)
if command -v skopeo &> /dev/null; then
    echo "  Using skopeo to verify image..."
    if ! skopeo inspect "docker://$IMAGE_URL" &> /dev/null; then
        echo "Error: Image $IMAGE_URL does not exist in registry"
        echo "Available tags can be checked with: podman search $IMAGE_PATH --list-tags"
        exit 1
    fi
    echo "  ✅ Image verified in registry"
elif command -v podman &> /dev/null; then
    echo "  Using podman to verify image..."
    if ! podman pull "$IMAGE_URL" &> /dev/null; then
        echo "Error: Image $IMAGE_URL does not exist in registry or cannot be pulled"
        echo "Available tags can be checked with: podman search $IMAGE_PATH --list-tags"
        exit 1
    fi
    echo "  ✅ Image verified in registry"
elif command -v docker &> /dev/null; then
    echo "  Using docker to verify image..."
    if ! docker pull "$IMAGE_URL" &> /dev/null; then
        echo "Error: Image $IMAGE_URL does not exist in registry or cannot be pulled"
        exit 1
    fi
    echo "  ✅ Image verified in registry"
else
    echo "  ⚠️  Warning: Cannot verify image (no container runtime found)"
    echo "  Proceeding anyway..."
fi

# =============================================================================
# Trigger Redeploy
# =============================================================================
# Strategy: Railway service is configured with a fixed :staging tag in the UI.
# The pre-push hook pushes updated images with the :staging tag to GHCR.
# We just trigger a redeploy so Railway re-pulls the :staging tag (now updated).
# This avoids issues with the serviceInstanceUpdate mutation not properly
# changing the image URL via GraphQL API.

echo "Triggering redeployment for: $IMAGE_URL"
echo "  Railway will re-pull the image tag from GHCR..."

# Update image source explicitly to force Railway to re-pull the image.
# serviceInstanceRedeploy can use cached images; serviceInstanceUpdate forces a fresh pull.
echo "Updating image source to force re-pull..."

UPDATE_QUERY=$(cat <<EOF
{
    "query": "mutation { serviceInstanceUpdate(serviceId: \"$SERVICE_ID\", environmentId: \"$ENVIRONMENT_ID\", input: { source: { image: \"$IMAGE_URL\" } }) }"
}
EOF
)

if UPDATE_RESPONSE=$(railway_graphql "$UPDATE_QUERY" 2>/dev/null); then
    echo "✅ Image source updated"
else
    echo "⚠️  serviceInstanceUpdate failed, continuing with redeploy..."
fi

# Always trigger redeploy to force Railway to re-pull the image.
# serviceInstanceUpdate alone may not trigger a new deployment if the
# image URL string is unchanged (e.g. :production tag reused).
echo "Triggering redeploy to force image re-pull..."

DEPLOY_QUERY=$(cat <<EOF
{
    "query": "mutation { serviceInstanceRedeploy(serviceId: \"$SERVICE_ID\", environmentId: \"$ENVIRONMENT_ID\") }"
}
EOF
)

DEPLOY_RESPONSE=$(railway_graphql "$DEPLOY_QUERY")
echo "✅ Redeployment triggered successfully"

# =============================================================================
# Summary
# =============================================================================

echo ""
echo "============================================"
echo "Deployment Summary"
echo "============================================"
echo "Service:     $SERVICE_NAME"
echo "Environment: $ENVIRONMENT"
echo "Image:       $IMAGE_URL"
echo "Status:      Deployment triggered"
echo "============================================"
echo ""
echo "Monitor deployment at: https://railway.app/project/$RAILWAY_PROJECT_ID"
