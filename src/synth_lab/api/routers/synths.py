"""
Synths API router for synth-lab.

REST endpoints for synth data access.

References:
    - OpenAPI spec: specs/010-rest-api/contracts/openapi.yaml
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, RedirectResponse

from synth_lab.models.pagination import PaginatedResponse, PaginationParams
from synth_lab.models.synth import SynthDetail, SynthFieldInfo, SynthSearchRequest, SynthSummary
from synth_lab.services.errors import AvatarNotFoundError
from synth_lab.services.synth_service import SynthService

router = APIRouter()


def get_synth_service() -> SynthService:
    """Get synth service instance."""
    return SynthService()


@router.get("/list", response_model=PaginatedResponse[SynthSummary])
async def list_synths(
    limit: int = Query(default=50, ge=1, le=200, description="Maximum items per page"),
    offset: int = Query(default=0, ge=0, description="Number of items to skip"),
    sort_by: str | None = Query(default=None, description="Field to sort by"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$", description="Sort order"),
    fields: str | None = Query(default=None, description="Comma-separated list of fields"),
    synth_group_id: str | None = Query(default=None, description="Filter by synth group ID"),
) -> PaginatedResponse[SynthSummary]:
    """
    List all synths with pagination.

    Returns a paginated list of synth summaries with optional field selection
    and group filtering.
    """
    service = get_synth_service()
    params = PaginationParams(
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    field_list = fields.split(",") if fields else None
    return service.list_synths(params, field_list, synth_group_id=synth_group_id)


@router.get("/fields", response_model=list[SynthFieldInfo])
async def get_fields() -> list[SynthFieldInfo]:
    """
    Get available synth field metadata.

    Returns a list of all available fields that can be used for querying
    and field selection.
    """
    service = get_synth_service()
    return service.get_fields()


@router.get("/{synth_id}", response_model=SynthDetail)
async def get_synth(synth_id: str) -> SynthDetail:
    """
    Get a synth by ID.

    Returns the full synth profile including demographics, psychographics,
    and technology capabilities.
    """
    service = get_synth_service()
    return service.get_synth(synth_id)


@router.get("/{synth_id}/avatar", response_model=None)
async def get_avatar(synth_id: str) -> FileResponse | RedirectResponse:
    """
    Get avatar image for a synth.

    Returns the PNG avatar image for the specified synth.
    If no avatar file exists, redirects to the link_photo URL as fallback.
    """
    service = get_synth_service()

    try:
        # Try to get the local avatar file
        avatar_path = service.get_avatar(synth_id)
        return FileResponse(
            path=avatar_path,
            media_type="image/png",
            filename=f"{synth_id}.png",
        )
    except AvatarNotFoundError:
        # Fallback: try to use link_photo
        synth = service.get_synth(synth_id)

        if synth.link_photo:
            # Redirect to the dynamic photo generation service
            return RedirectResponse(url=synth.link_photo, status_code=307)

        # No avatar file and no link_photo available
        raise HTTPException(
            status_code=404,
            detail=f"Avatar not found for synth {synth_id} and no fallback link_photo available",
        )


@router.post("/search", response_model=PaginatedResponse[SynthSummary])
async def search_synths(
    request: SynthSearchRequest,
    limit: int = Query(default=50, ge=1, le=200, description="Maximum items per page"),
    offset: int = Query(default=0, ge=0, description="Number of items to skip"),
) -> PaginatedResponse[SynthSummary]:
    """
    Search synths with WHERE clause or full query.

    Allows filtering synths using SQL WHERE clauses or custom SELECT queries.
    Only SELECT queries are allowed for security.
    """
    service = get_synth_service()
    params = PaginationParams(limit=limit, offset=offset)
    return service.search_synths(request.where_clause, request.query, params)


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
        expected_paths = ["/list", "/fields", "/{synth_id}", "/{synth_id}/avatar", "/search"]
        for path in expected_paths:
            if path not in paths:
                all_validation_failures.append(f"Missing route: {path}")
    except Exception as e:
        all_validation_failures.append(f"Route paths test failed: {e}")

    # Test 3: Service instantiation
    total_tests += 1
    try:
        service = get_synth_service()
        if not isinstance(service, SynthService):
            all_validation_failures.append(f"Expected SynthService, got {type(service)}")
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
