"""
Research API router for synth-lab.

REST endpoints for research execution data access.

References:
    - OpenAPI spec: specs/010-rest-api/contracts/openapi.yaml
"""

from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse

from synth_lab.models.pagination import PaginatedResponse, PaginationParams
from synth_lab.models.research import (
    ResearchExecuteRequest,
    ResearchExecuteResponse,
    ResearchExecutionDetail,
    ResearchExecutionSummary,
    TranscriptDetail,
    TranscriptSummary,
)
from synth_lab.services.research_service import ResearchService

router = APIRouter()


def get_research_service() -> ResearchService:
    """Get research service instance."""
    return ResearchService()


@router.get("/list", response_model=PaginatedResponse[ResearchExecutionSummary])
async def list_executions(
    limit: int = Query(default=50, ge=1, le=200, description="Maximum items per page"),
    offset: int = Query(default=0, ge=0, description="Number of items to skip"),
    sort_by: str | None = Query(default="started_at", description="Field to sort by"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$", description="Sort order"),
) -> PaginatedResponse[ResearchExecutionSummary]:
    """
    List all research executions with pagination.

    Returns a paginated list of research execution summaries.
    """
    service = get_research_service()
    params = PaginationParams(
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return service.list_executions(params)


@router.get("/{exec_id}", response_model=ResearchExecutionDetail)
async def get_execution(exec_id: str) -> ResearchExecutionDetail:
    """
    Get a research execution by ID.

    Returns the full execution details including status, counts, and availability flags.
    """
    service = get_research_service()
    return service.get_execution(exec_id)


@router.get("/{exec_id}/transcripts", response_model=PaginatedResponse[TranscriptSummary])
async def get_transcripts(
    exec_id: str,
    limit: int = Query(default=50, ge=1, le=200, description="Maximum items per page"),
    offset: int = Query(default=0, ge=0, description="Number of items to skip"),
) -> PaginatedResponse[TranscriptSummary]:
    """
    Get transcripts for a research execution.

    Returns a paginated list of transcript summaries for the specified execution.
    """
    service = get_research_service()
    params = PaginationParams(limit=limit, offset=offset)
    return service.get_transcripts(exec_id, params)


@router.get("/{exec_id}/transcripts/{synth_id}", response_model=TranscriptDetail)
async def get_transcript(exec_id: str, synth_id: str) -> TranscriptDetail:
    """
    Get a specific transcript.

    Returns the full transcript including all messages.
    """
    service = get_research_service()
    return service.get_transcript(exec_id, synth_id)


@router.get("/{exec_id}/summary")
async def get_summary(exec_id: str) -> PlainTextResponse:
    """
    Get the summary for a research execution.

    Returns the summary as markdown text.
    """
    service = get_research_service()
    summary = service.get_summary(exec_id)
    return PlainTextResponse(content=summary, media_type="text/markdown")


@router.post("/execute", response_model=ResearchExecuteResponse)
async def execute_research(request: ResearchExecuteRequest) -> ResearchExecuteResponse:
    """
    Execute a new research session.

    This starts a batch of interviews with the specified topic and synths.
    The execution runs asynchronously - use GET /research/{exec_id} to check status.

    Args:
        request: Research execution parameters.

    Returns:
        Execution ID and initial status.
    """
    service = get_research_service()
    return await service.execute_research(request)


if __name__ == "__main__":
    import sys

    # Validation - check router is properly configured
    all_validation_failures = []
    total_tests = 0

    # Test 1: Router has routes
    total_tests += 1
    try:
        if len(router.routes) < 5:
            all_validation_failures.append(f"Expected at least 5 routes, got {len(router.routes)}")
    except Exception as e:
        all_validation_failures.append(f"Router routes test failed: {e}")

    # Test 2: Check route paths
    total_tests += 1
    try:
        paths = [r.path for r in router.routes]
        expected_paths = [
            "/list",
            "/{exec_id}",
            "/{exec_id}/transcripts",
            "/{exec_id}/transcripts/{synth_id}",
            "/{exec_id}/summary",
            "/execute",
        ]
        for path in expected_paths:
            if path not in paths:
                all_validation_failures.append(f"Missing route: {path}")
    except Exception as e:
        all_validation_failures.append(f"Route paths test failed: {e}")

    # Test 3: Service instantiation
    total_tests += 1
    try:
        service = get_research_service()
        if not isinstance(service, ResearchService):
            all_validation_failures.append(f"Expected ResearchService, got {type(service)}")
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
