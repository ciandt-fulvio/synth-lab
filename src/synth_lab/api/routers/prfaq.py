"""
PR-FAQ API router for synth-lab.

REST endpoints for PR-FAQ document data access.

References:
    - OpenAPI spec: specs/010-rest-api/contracts/openapi.yaml
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import PlainTextResponse

from synth_lab.models.pagination import PaginatedResponse, PaginationParams
from synth_lab.models.prfaq import PRFAQGenerateRequest, PRFAQGenerateResponse, PRFAQSummary
from synth_lab.services.prfaq_service import (
    MarkdownNotFoundError,
    PRFAQService)

router = APIRouter()


def get_prfaq_service() -> PRFAQService:
    """Get PR-FAQ service instance."""
    return PRFAQService()


@router.get("/list", response_model=PaginatedResponse[PRFAQSummary])
async def list_prfaqs(
    limit: int = Query(default=50, ge=1, le=200, description="Maximum items per page"),
    offset: int = Query(default=0, ge=0, description="Number of items to skip"),
    sort_by: str | None = Query(default="generated_at", description="Field to sort by"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$", description="Sort order")) -> PaginatedResponse[PRFAQSummary]:
    """
    List all PR-FAQ documents with pagination.

    Returns a paginated list of PR-FAQ summaries including metadata and validation status.
    """
    service = get_prfaq_service()
    params = PaginationParams(
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order)
    return service.list_prfaqs(params)


@router.get("/{exec_id}", response_model=PRFAQSummary)
async def get_prfaq(exec_id: str) -> PRFAQSummary:
    """
    Get a PR-FAQ by execution ID.

    Returns the PR-FAQ metadata for the specified execution.
    """
    service = get_prfaq_service()
    return service.get_prfaq(exec_id)


@router.get("/{exec_id}/markdown")
async def get_prfaq_markdown(exec_id: str) -> PlainTextResponse:
    """
    Get the PR-FAQ markdown content.

    Returns the full PR-FAQ document as markdown text.
    """
    service = get_prfaq_service()
    try:
        markdown = service.get_markdown(exec_id)
        return PlainTextResponse(content=markdown, media_type="text/markdown")
    except MarkdownNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail={"code": "MARKDOWN_NOT_FOUND", "message": str(e)}) from e


@router.post("/generate", response_model=PRFAQGenerateResponse)
async def generate_prfaq(
    request: PRFAQGenerateRequest,
    background_tasks: BackgroundTasks) -> PRFAQGenerateResponse:
    """
    Start generation of a PR-FAQ from a research execution.

    This endpoint starts generation and returns immediately.
    The actual generation runs in a background task.

    Args:
        request: Generation parameters including exec_id and model.
        background_tasks: FastAPI background tasks.

    Returns:
        Generation status (generating).

    Raises:
        409 Conflict: If PR-FAQ is already being generated for this execution.
        400: If execution is not linked to an experiment or summary is not available.
    """
    from datetime import datetime

    from synth_lab.domain.entities.experiment_document import DocumentType
    from synth_lab.repositories.research_repository import ResearchRepository
    from synth_lab.services.document_service import DocumentService

    # Verify execution exists and get experiment_id
    research_repo = ResearchRepository()
    try:
        execution = research_repo.get_execution(request.exec_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Execution not found")

    if not execution.experiment_id:
        raise HTTPException(
            status_code=400,
            detail="Execution must be linked to an experiment")

    # Create "generating" status record BEFORE starting background task
    # This prevents race condition where frontend polls before record exists
    doc_service = DocumentService()

    # Check if summary exists (prerequisite for prfaq)
    try:
        doc_service.get_markdown(
            execution.experiment_id,
            DocumentType.RESEARCH_SUMMARY,
            source_id=request.exec_id)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Summary must be generated first")

    pending = doc_service.start_generation(
        experiment_id=execution.experiment_id,
        document_type=DocumentType.RESEARCH_PRFAQ,
        source_id=request.exec_id,
        model=request.model)

    if pending is None:
        # Already generating
        return PRFAQGenerateResponse(
            exec_id=request.exec_id,
            status="generating",
            generated_at=datetime.now(),
            validation_status="pending")

    # Start background generation using service method
    service = get_prfaq_service()
    background_tasks.add_task(service.generate_prfaq_background, request)

    return PRFAQGenerateResponse(
        exec_id=request.exec_id,
        status="generating",
        generated_at=datetime.now(),
        validation_status="pending")


if __name__ == "__main__":
    import sys

    # Validation - check router is properly configured
    all_validation_failures = []
    total_tests = 0

    # Test 1: Router has routes
    total_tests += 1
    try:
        if len(router.routes) < 4:
            all_validation_failures.append(f"Expected at least 4 routes, got {len(router.routes)}")
    except Exception as e:
        all_validation_failures.append(f"Router routes test failed: {e}")

    # Test 2: Check route paths
    total_tests += 1
    try:
        paths = [r.path for r in router.routes]
        expected_paths = [
            "/list",
            "/{exec_id}",
            "/{exec_id}/markdown",
            "/generate",
        ]
        for path in expected_paths:
            if path not in paths:
                all_validation_failures.append(f"Missing route: {path}")
    except Exception as e:
        all_validation_failures.append(f"Route paths test failed: {e}")

    # Test 3: Service instantiation
    total_tests += 1
    try:
        service = get_prfaq_service()
        if not isinstance(service, PRFAQService):
            all_validation_failures.append(f"Expected PRFAQService, got {type(service)}")
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
