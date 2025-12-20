"""
Topics API router for synth-lab.

REST endpoints for topic guide data access.

References:
    - OpenAPI spec: specs/010-rest-api/contracts/openapi.yaml
"""

from fastapi import APIRouter, Query

from synth_lab.models.pagination import PaginatedResponse, PaginationParams
from synth_lab.models.research import ResearchExecutionSummary
from synth_lab.models.topic import TopicDetail, TopicSummary
from synth_lab.services.topic_service import TopicService

router = APIRouter()


def get_topic_service() -> TopicService:
    """Get topic service instance."""
    return TopicService()


@router.get("/list", response_model=PaginatedResponse[TopicSummary])
async def list_topics(
    limit: int = Query(default=50, ge=1, le=200, description="Maximum items per page"),
    offset: int = Query(default=0, ge=0, description="Number of items to skip"),
    sort_by: str | None = Query(default="name", description="Field to sort by"),
    sort_order: str = Query(default="asc", pattern="^(asc|desc)$", description="Sort order"),
) -> PaginatedResponse[TopicSummary]:
    """
    List all topic guides with pagination.

    Returns a paginated list of topic summaries including question count and file count.
    """
    service = get_topic_service()
    params = PaginationParams(
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return service.list_topics(params)


@router.get("/{topic_name}", response_model=TopicDetail)
async def get_topic(topic_name: str) -> TopicDetail:
    """
    Get a topic guide by name.

    Returns the full topic guide including script questions and associated files.
    """
    service = get_topic_service()
    return service.get_topic(topic_name)


@router.get("/{topic_name}/research", response_model=PaginatedResponse[ResearchExecutionSummary])
async def get_topic_executions(
    topic_name: str,
    limit: int = Query(default=50, ge=1, le=200, description="Maximum items per page"),
    offset: int = Query(default=0, ge=0, description="Number of items to skip"),
    sort_by: str | None = Query(default="started_at", description="Field to sort by"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$", description="Sort order"),
) -> PaginatedResponse[ResearchExecutionSummary]:
    """
    Get research executions for a topic.

    Returns a paginated list of research executions that were run for this topic.
    """
    service = get_topic_service()
    params = PaginationParams(
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return service.get_topic_executions(topic_name, params)


if __name__ == "__main__":
    import sys

    # Validation - check router is properly configured
    all_validation_failures = []
    total_tests = 0

    # Test 1: Router has routes
    total_tests += 1
    try:
        if len(router.routes) < 3:
            all_validation_failures.append(f"Expected at least 3 routes, got {len(router.routes)}")
    except Exception as e:
        all_validation_failures.append(f"Router routes test failed: {e}")

    # Test 2: Check route paths
    total_tests += 1
    try:
        paths = [r.path for r in router.routes]
        expected_paths = [
            "/list",
            "/{topic_name}",
            "/{topic_name}/research",
        ]
        for path in expected_paths:
            if path not in paths:
                all_validation_failures.append(f"Missing route: {path}")
    except Exception as e:
        all_validation_failures.append(f"Route paths test failed: {e}")

    # Test 3: Service instantiation
    total_tests += 1
    try:
        service = get_topic_service()
        if not isinstance(service, TopicService):
            all_validation_failures.append(f"Expected TopicService, got {type(service)}")
    except Exception as e:
        all_validation_failures.append(f"Service instantiation failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
