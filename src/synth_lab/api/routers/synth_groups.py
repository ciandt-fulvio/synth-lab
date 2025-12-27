"""
T023 Synth Groups API router for synth-lab.

REST endpoints for synth group management.

References:
    - Spec: specs/018-experiment-hub/spec.md
    - OpenAPI: specs/018-experiment-hub/contracts/openapi.yaml
"""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from synth_lab.models.pagination import PaginatedResponse, PaginationParams
from synth_lab.repositories.synth_group_repository import (
    SynthGroupDetail,
    SynthGroupRepository,
    SynthGroupSummary,
)
from synth_lab.services.synth_group_service import SynthGroupService

router = APIRouter()


# Request/Response Schemas

class SynthGroupCreate(BaseModel):
    """Request schema for creating a synth group."""

    id: str | None = Field(
        default=None,
        pattern=r"^grp_[a-f0-9]{8}$",
        description="Optional ID. If not provided, will be generated.",
    )
    name: str = Field(
        min_length=1,
        description="Descriptive name for the group.",
    )
    description: str | None = Field(
        default=None,
        description="Description of the purpose/context.",
    )


class SynthSummaryResponse(BaseModel):
    """Summary of a synth for group detail."""

    id: str
    nome: str
    descricao: str | None = None
    avatar_path: str | None = None
    synth_group_id: str | None = None
    created_at: datetime


class SynthGroupDetailResponse(BaseModel):
    """Response schema for synth group detail."""

    id: str
    name: str
    description: str | None = None
    synth_count: int = 0
    created_at: datetime
    synths: list[SynthSummaryResponse] = Field(default_factory=list)


class SynthGroupResponse(BaseModel):
    """Response schema for synth group."""

    id: str
    name: str
    description: str | None = None
    synth_count: int = 0
    created_at: datetime


def get_synth_group_service() -> SynthGroupService:
    """Get synth group service instance."""
    return SynthGroupService()


@router.post("", response_model=SynthGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_synth_group(data: SynthGroupCreate) -> SynthGroupResponse:
    """
    Create a new synth group.

    Returns the created synth group with generated ID.
    """
    service = get_synth_group_service()
    try:
        group = service.create_group(
            name=data.name,
            description=data.description,
            group_id=data.id,
        )
        return SynthGroupResponse(
            id=group.id,
            name=group.name,
            description=group.description,
            synth_count=group.synth_count,
            created_at=group.created_at,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.get("/list", response_model=PaginatedResponse[SynthGroupSummary])
async def list_synth_groups(
    limit: int = Query(default=50, ge=1, le=200, description="Maximum items per page"),
    offset: int = Query(default=0, ge=0, description="Number of items to skip"),
) -> PaginatedResponse[SynthGroupSummary]:
    """
    List all synth groups with pagination.

    Returns a paginated list of synth groups with synth counts.
    """
    service = get_synth_group_service()
    params = PaginationParams(
        limit=limit,
        offset=offset,
        sort_by="created_at",
        sort_order="desc",
    )
    return service.list_groups(params)


@router.get("/{group_id}", response_model=SynthGroupDetailResponse)
async def get_synth_group(group_id: str) -> SynthGroupDetailResponse:
    """
    Get a synth group by ID with full details.

    Returns the synth group with list of synths.
    """
    service = get_synth_group_service()
    detail = service.get_group_detail(group_id)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Synth group {group_id} not found",
        )

    # Convert synths to response format
    synths = [
        SynthSummaryResponse(
            id=s.id,
            nome=s.nome,
            descricao=s.descricao,
            avatar_path=s.avatar_path,
            synth_group_id=s.synth_group_id,
            created_at=s.created_at,
        )
        for s in detail.synths
    ]

    return SynthGroupDetailResponse(
        id=detail.id,
        name=detail.name,
        description=detail.description,
        synth_count=detail.synth_count,
        created_at=detail.created_at,
        synths=synths,
    )


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_synth_group(group_id: str) -> None:
    """
    Delete a synth group.

    Synths in the group will have their synth_group_id set to NULL.
    Returns 204 No Content on success.
    """
    service = get_synth_group_service()
    deleted = service.delete_group(group_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Synth group {group_id} not found",
        )
