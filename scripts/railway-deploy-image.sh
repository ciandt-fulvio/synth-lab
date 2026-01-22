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
# Update Service Image
# =============================================================================

echo "Updating service image to: $IMAGE_URL"

# Note: The service must be configured with "Docker Image" source in Railway UI
# This mutation updates the image URL for image-based services
UPDATE_QUERY=$(cat <<EOF
{
    "query": "mutation { serviceInstanceUpdate(serviceId: \"$SERVICE_ID\", environmentId: \"$ENVIRONMENT_ID\", input: { source: { image: \"$IMAGE_URL\" } }) }"
}
EOF
)

UPDATE_RESPONSE=$(railway_graphql "$UPDATE_QUERY")
echo "Service image updated successfully"

# =============================================================================
# Trigger Redeploy
# =============================================================================

echo "Triggering deployment..."

DEPLOY_QUERY=$(cat <<EOF
{
    "query": "mutation { serviceInstanceRedeploy(serviceId: \"$SERVICE_ID\", environmentId: \"$ENVIRONMENT_ID\") }"
}
EOF
)

DEPLOY_RESPONSE=$(railway_graphql "$DEPLOY_QUERY")
echo "Deployment triggered successfully"

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
