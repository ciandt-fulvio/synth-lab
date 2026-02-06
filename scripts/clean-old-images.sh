#!/bin/bash
#
# Clean Old Docker Images Script
#
# Strategy:
# 1. Keep only essential tags: latest + 2 most recent commit SHAs
# 2. Remove all other tags (old commits, duplicates, orphans)
# 3. Remove dangling/orphaned images
#
# Usage:
#   ./scripts/clean-old-images.sh
#   or
#   make clean-images
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🧹 Cleaning Old Docker Images & Tags${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Detect container runtime
if command -v podman &> /dev/null; then
    CONTAINER_RUNTIME="podman"
    echo -e "${BLUE}Using: Podman${NC}"
elif command -v docker &> /dev/null; then
    CONTAINER_RUNTIME="docker"
    echo -e "${BLUE}Using: Docker${NC}"
else
    echo -e "${RED}❌ Neither podman nor docker found. Please install one.${NC}"
    exit 1
fi
echo ""

# Show current state
echo -e "${CYAN}📊 Current synth-lab images:${NC}"
BEFORE_COUNT=$($CONTAINER_RUNTIME images --filter "reference=*synth-lab*" --format "{{.Repository}}:{{.Tag}}" | wc -l | tr -d ' ')
echo -e "${BLUE}  Total image tags: ${BEFORE_COUNT}${NC}"
$CONTAINER_RUNTIME images --filter "reference=*synth-lab*" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.ID}}" | head -30
echo ""

# Function to clean tags for a specific repository
clean_repository_tags() {
    local repo_pattern=$1
    local keep_tags=4  # Keep latest + 3 most recent commit SHAs

    echo -e "${YELLOW}Cleaning repository: ${repo_pattern}${NC}"

    # Get all tags for this repository, sorted by creation date (newest first)
    local all_tags=$($CONTAINER_RUNTIME images --format "{{.Repository}}:{{.Tag}}|{{.CreatedAt}}" | \
        grep "$repo_pattern" | \
        grep -v "<none>" | \
        sort -t'|' -k2 -r | \
        cut -d'|' -f1)

    if [ -z "$all_tags" ]; then
        echo -e "${BLUE}  No images found${NC}"
        echo ""
        return
    fi

    local total=$(echo "$all_tags" | wc -l | tr -d ' ')
    echo -e "${BLUE}  Found ${total} tag(s)${NC}"

    # Separate latest tags from commit SHA tags
    local latest_tags=$(echo "$all_tags" | grep ":latest$" || true)
    local commit_tags=$(echo "$all_tags" | grep -v ":latest$" || true)

    # Keep all latest tags (important)
    local kept=0
    local removed=0

    # Count and keep latest tags
    if [ -n "$latest_tags" ]; then
        local latest_count=$(echo "$latest_tags" | wc -l | tr -d ' ')
        kept=$((kept + latest_count))
        echo -e "${GREEN}  Keeping ${latest_count} :latest tag(s)${NC}"
    fi

    # Keep only the 3 most recent commit SHA tags
    if [ -n "$commit_tags" ]; then
        local commit_count=$(echo "$commit_tags" | wc -l | tr -d ' ')
        local keep_commit_count=3

        if [ $commit_count -le $keep_commit_count ]; then
            kept=$((kept + commit_count))
            echo -e "${GREEN}  Keeping ${commit_count} commit SHA tag(s)${NC}"
        else
            kept=$((kept + keep_commit_count))
            echo -e "${GREEN}  Keeping ${keep_commit_count} most recent commit SHA tag(s)${NC}"

            # Remove old commit tags (skip first N)
            local tags_to_remove=$(echo "$commit_tags" | tail -n +$((keep_commit_count + 1)))
            removed=$(echo "$tags_to_remove" | wc -l | tr -d ' ')

            echo -e "${YELLOW}  Removing ${removed} old commit SHA tag(s)...${NC}"
            while IFS= read -r tag; do
                if [ -n "$tag" ]; then
                    echo -e "${BLUE}    Removing: ${tag}${NC}"
                    $CONTAINER_RUNTIME rmi "$tag" 2>/dev/null || true
                fi
            done <<< "$tags_to_remove"
        fi
    fi

    echo -e "${GREEN}  ✅ Kept: ${kept}, Removed: ${removed}${NC}"
    echo ""
}

# Clean main repositories
echo -e "${CYAN}Step 1: Cleaning repository tags${NC}"
echo ""

clean_repository_tags "localhost/synth-lab-api"
clean_repository_tags "ghcr.io/.*/synth-lab-api"
clean_repository_tags "localhost/synth-lab-frontend"
clean_repository_tags "ghcr.io/.*/synth-lab-frontend"

# Clean orphaned/strange named images
echo -e "${CYAN}Step 2: Cleaning orphaned/strange images${NC}"
echo ""

echo -e "${YELLOW}Removing orphaned images (parmejjani, polizel, fulvio, etc.)${NC}"
ORPHAN_COUNT=0

# List of orphaned image patterns to remove
ORPHAN_PATTERNS=(
    "localhost/parmejjani/synth-lab-api"
    "localhost/polizel"
    "ghcr.io/fulvio"
    "localhost/docker_backend-test"
    "localhost/docker_frontend-test"
)

for pattern in "${ORPHAN_PATTERNS[@]}"; do
    orphans=$($CONTAINER_RUNTIME images --format "{{.Repository}}:{{.Tag}}" | grep "$pattern" || true)
    if [ -n "$orphans" ]; then
        while IFS= read -r tag; do
            if [ -n "$tag" ]; then
                echo -e "${BLUE}  Removing: ${tag}${NC}"
                $CONTAINER_RUNTIME rmi "$tag" 2>/dev/null || true
                ORPHAN_COUNT=$((ORPHAN_COUNT + 1))
            fi
        done <<< "$orphans"
    fi
done

if [ $ORPHAN_COUNT -gt 0 ]; then
    echo -e "${GREEN}  ✅ Removed ${ORPHAN_COUNT} orphaned image(s)${NC}"
else
    echo -e "${BLUE}  No orphaned images found${NC}"
fi
echo ""

# Clean dangling images (images with no tags)
echo -e "${CYAN}Step 3: Cleaning dangling images${NC}"
echo ""

DANGLING_COUNT=$($CONTAINER_RUNTIME images -f "dangling=true" -q | wc -l | tr -d ' ')
if [ "$DANGLING_COUNT" -gt 0 ]; then
    echo -e "${BLUE}  Found ${DANGLING_COUNT} dangling image(s)${NC}"
    $CONTAINER_RUNTIME image prune -f > /dev/null 2>&1
    echo -e "${GREEN}  ✅ Cleaned dangling images${NC}"
else
    echo -e "${GREEN}  ✅ No dangling images${NC}"
fi
echo ""

# Final summary
echo -e "${GREEN}✅ Cleanup complete!${NC}"
echo ""

echo -e "${CYAN}📊 Remaining synth-lab images:${NC}"
AFTER_COUNT=$($CONTAINER_RUNTIME images --filter "reference=*synth-lab*" --format "{{.Repository}}:{{.Tag}}" | wc -l | tr -d ' ')
echo -e "${BLUE}  Total image tags: ${AFTER_COUNT} (was ${BEFORE_COUNT})${NC}"
echo -e "${GREEN}  Cleaned: $((BEFORE_COUNT - AFTER_COUNT)) tag(s)${NC}"
echo ""

$CONTAINER_RUNTIME images --filter "reference=*synth-lab*" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.ID}}"
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
