"""
Experiments API router for synth-lab.

REST endpoints for experiment management.

References:
    - Spec: specs/019-experiment-refactor/spec.md
    - OpenAPI: specs/019-experiment-refactor/contracts/experiment-api.yaml
"""

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from synth_lab.api.schemas.experiments import ExperimentCreate as ExperimentCreateSchema
from synth_lab.api.schemas.experiments import (
    ExperimentDetail,
    ExperimentResponse,
    InterviewSummary,
    PaginatedExperimentSummary,
)
from synth_lab.api.schemas.experiments import ExperimentSummary as ExperimentSummarySchema
from synth_lab.api.schemas.experiments import ExperimentUpdate as ExperimentUpdateSchema
from synth_lab.infrastructure.database_v2 import get_db_session, get_session
from synth_lab.models.pagination import PaginationParams
from synth_lab.models.research import ResearchExecuteRequest, ResearchExecuteResponse
from synth_lab.repositories.interview_guide_repository import InterviewGuideRepository
from synth_lab.repositories.research_repository import ResearchRepository
from synth_lab.repositories.synth_group_repository import SynthGroupRepository
from synth_lab.services.experiment_service import ExperimentService
from synth_lab.services.interview_guide_generator_service import generate_interview_guide_async
from synth_lab.services.permission_service import PermissionService
from synth_lab.services.research_service import ResearchService

router = APIRouter()


# =============================================================================
# Helper Functions
# =============================================================================


def get_experiment_service() -> ExperimentService:
    """Get experiment service instance."""
    return ExperimentService()


async def get_current_user_id(request: Request) -> str:
    """Get current user ID from request state (set by auth middleware).

    Args:
        request: FastAPI request

    Returns:
        User ID from session

    Raises:
        HTTPException: If not authenticated
    """
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user_id


def get_permission_service(db: AsyncSession = Depends(get_db_session)) -> PermissionService:
    """Get permission service instance.

    Args:
        db: Database session

    Returns:
        Configured PermissionService
    """
    return PermissionService(db)


def _get_synth_group_name(synth_group_id: str) -> str:
    """Get synth group name by ID."""
    with get_session() as session:
        repo = SynthGroupRepository(session=session)
        group = repo.get_by_id(synth_group_id)
        return group.name if group else "Unknown"


# =============================================================================
# Experiment CRUD Endpoints
# =============================================================================


@router.post("", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED)
async def create_experiment(
    data: ExperimentCreateSchema,
    request: Request,
    current_user_id: str = Depends(get_current_user_id),
) -> ExperimentResponse:
    """
    Create a new experiment.

    Returns the created experiment with generated ID.
    """
    service = get_experiment_service()
    try:
        experiment = service.create_experiment(
            name=data.name,
            hypothesis=data.hypothesis,
            description=data.description,
            synth_group_id=data.synth_group_id,
            owner_id=current_user_id)

        # Trigger async interview guide generation (non-blocking)
        asyncio.create_task(
            generate_interview_guide_async(
                experiment_id=experiment.id,
                name=experiment.name,
                hypothesis=experiment.hypothesis,
                description=experiment.description)
        )
        logger.info(f"Interview guide generation started for experiment: {experiment.id}")

        # Check if interview guide exists (newly created experiments won't have one)
        with get_session() as session:
            interview_guide_repo = InterviewGuideRepository(session=session)
            has_interview_guide = interview_guide_repo.exists(experiment.id)

        # Get synth group name for response
        synth_group_name = _get_synth_group_name(experiment.synth_group_id)

        return ExperimentResponse(
            id=experiment.id,
            name=experiment.name,
            hypothesis=experiment.hypothesis,
            description=experiment.description,
            synth_group_id=experiment.synth_group_id,
            synth_group_name=synth_group_name,
            has_interview_guide=has_interview_guide,
            tags=experiment.tags,
            created_at=experiment.created_at,
            updated_at=experiment.updated_at)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e))
    except Exception as e:
        # Handle database integrity errors (e.g., foreign key violations)
        if "foreign key" in str(e).lower() or "IntegrityError" in str(type(e).__name__):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid reference: {str(e)}")
        # Re-raise other exceptions
        raise


@router.get("/list", response_model=PaginatedExperimentSummary)
async def list_experiments(
    current_user_id: str = Depends(get_current_user_id),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum items per page"),
    offset: int = Query(default=0, ge=0, description="Number of items to skip"),
    search: str | None = Query(default=None, max_length=200, description="Search by name or hypothesis"),
    tag: str | None = Query(default=None, max_length=50, description="Filter by tag name"),
    sort_by: str = Query(default="created_at", pattern="^(created_at|name)$", description="Sort field"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$", description="Sort order")
) -> PaginatedExperimentSummary:
    """
    List all experiments with pagination, search, sorting, and tag filter.

    - **search**: Filters experiments by name OR hypothesis (case-insensitive)
    - **tag**: Filters experiments by tag name (exact match)
    - **sort_by**: created_at (default) or name
    - **sort_order**: desc (default) or asc

    Returns a paginated list of experiments with interview counts.
    """
    service = get_experiment_service()
    params = PaginationParams(
        limit=limit,
        offset=offset,
        search=search,
        tag=tag,
        sort_by=sort_by,
        sort_order=sort_order)
    result = service.list_experiments(params, user_id=current_user_id)

    # Convert repository summaries to API schemas
    summaries = [
        ExperimentSummarySchema(
            id=exp.id,
            name=exp.name,
            hypothesis=exp.hypothesis,
            description=exp.description,
            synth_group_id=exp.synth_group_id,
            synth_group_name=exp.synth_group_name,
            has_interview_guide=exp.has_interview_guide,
            interview_count=exp.interview_count,
            tags=exp.tags,
            created_at=exp.created_at,
            updated_at=exp.updated_at)
        for exp in result.data
    ]

    return PaginatedExperimentSummary(
        data=summaries,
        pagination=result.pagination)


@router.get("/{experiment_id}", response_model=ExperimentDetail)
async def get_experiment(
    experiment_id: str,
    current_user_id: str = Depends(get_current_user_id),
    permission_service: PermissionService = Depends(get_permission_service),
) -> ExperimentDetail:
    """
    Get an experiment by ID with full details.

    Returns the experiment with interviews.
    """
    service = get_experiment_service()

    # First check if resource exists (404 before 403)
    experiment = service.get_experiment(experiment_id)
    if experiment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found")

    # Then check if user has access to this experiment
    has_access = permission_service.can_access_experiment(current_user_id, experiment_id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this experiment",
        )

    with get_session() as session:
        # Get synth group name
        from sqlalchemy import select

        from synth_lab.models.orm.synth import SynthGroup as SynthGroupORM

        synth_group_name = "Unknown"
        stmt = select(SynthGroupORM.name).where(SynthGroupORM.id == experiment.synth_group_id)
        result = session.execute(stmt).scalar_one_or_none()
        if result:
            synth_group_name = result

        # Fetch interviews using repository methods
        research_repo = ResearchRepository(session=session)
        interview_response = research_repo.list_executions_by_experiment(
            experiment_id, PaginationParams(limit=100)
        )

        # Batch fetch for summary, prfaq, additional_context, and total_turns
        exec_ids = [exec.exec_id for exec in interview_response.data]
        summary_exists = research_repo.check_summaries_exist_batch(exec_ids)
        prfaq_exists = research_repo.check_prfaqs_exist_batch(exec_ids)
        additional_contexts = research_repo.get_additional_context_batch(exec_ids)
        total_turns = research_repo.get_total_turns_batch(exec_ids)

        interviews = [
            InterviewSummary(
                exec_id=exec.exec_id,
                topic_name=exec.topic_name,
                status=exec.status.value if hasattr(exec.status, "value") else str(exec.status),
                synth_count=exec.synth_count,
                total_turns=total_turns.get(exec.exec_id, 0),
                has_summary=summary_exists.get(exec.exec_id, False),
                has_prfaq=prfaq_exists.get(exec.exec_id, False),
                additional_context=additional_contexts.get(exec.exec_id),
                started_at=exec.started_at,
                completed_at=exec.completed_at)
            for exec in interview_response.data
        ]

        # Check if interview guide exists
        interview_guide_repo = InterviewGuideRepository(session=session)
        has_interview_guide = interview_guide_repo.exists(experiment_id)

    return ExperimentDetail(
        id=experiment.id,
        name=experiment.name,
        hypothesis=experiment.hypothesis,
        description=experiment.description,
        synth_group_id=experiment.synth_group_id,
        synth_group_name=synth_group_name,
        has_interview_guide=has_interview_guide,
        tags=experiment.tags,
        created_at=experiment.created_at,
        updated_at=experiment.updated_at,
        interviews=interviews,
        interview_count=len(interviews))


@router.put("/{experiment_id}", response_model=ExperimentResponse)
async def update_experiment(
    experiment_id: str,
    data: ExperimentUpdateSchema,
    current_user_id: str = Depends(get_current_user_id),
    permission_service: PermissionService = Depends(get_permission_service),
) -> ExperimentResponse:
    """
    Update an experiment (name, hypothesis, description, synth_group_id).
    """
    service = get_experiment_service()

    # First check if resource exists (404 before 403)
    existing = service.get_experiment(experiment_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found")

    # Then check if user can edit this experiment
    can_edit = permission_service.can_edit_experiment(current_user_id, experiment_id)
    if not can_edit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to edit this experiment",
        )

    try:
        updated = service.update_experiment(
            experiment_id,
            name=data.name,
            hypothesis=data.hypothesis,
            description=data.description,
            synth_group_id=data.synth_group_id)

        # Check if interview guide exists
        with get_session() as session:
            interview_guide_repo = InterviewGuideRepository(session=session)
            has_interview_guide = interview_guide_repo.exists(experiment_id)

        # Get synth group name for response
        synth_group_name = _get_synth_group_name(updated.synth_group_id)

        return ExperimentResponse(
            id=updated.id,
            name=updated.name,
            hypothesis=updated.hypothesis,
            description=updated.description,
            synth_group_id=updated.synth_group_id,
            synth_group_name=synth_group_name,
            has_interview_guide=has_interview_guide,
            tags=updated.tags,
            created_at=updated.created_at,
            updated_at=updated.updated_at)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e))


@router.delete("/{experiment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_experiment(
    experiment_id: str,
    current_user_id: str = Depends(get_current_user_id),
    permission_service: PermissionService = Depends(get_permission_service),
) -> None:
    """
    Delete an experiment.

    Returns 204 No Content on success.
    """
    service = get_experiment_service()

    # First check if resource exists (404 before 403)
    existing = service.get_experiment(experiment_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found")

    # Then check if user can edit (delete) this experiment
    can_edit = permission_service.can_edit_experiment(current_user_id, experiment_id)
    if not can_edit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this experiment",
        )

    service.delete_experiment(experiment_id)


# =============================================================================
# Interview Endpoints
# =============================================================================


class InterviewCreateRequest(BaseModel):
    """Request model for creating an interview linked to an experiment."""

    additional_context: str | None = Field(
        default=None,
        description="Additional context to complement the research scenario")
    synth_ids: list[str] | None = Field(
        default=None,
        description="Specific synth IDs to interview")
    synth_count: int | None = Field(
        default=5,
        ge=1,
        le=50,
        description="Number of random synths (if synth_ids not provided)")
    max_turns: int = Field(
        default=6,
        ge=1,
        le=20,
        description="Max interview turns (each turn = 1 question + 1 answer)")
    generate_summary: bool = Field(default=True, description="Generate summary after completion")


def get_research_service() -> ResearchService:
    """Get research service instance."""
    return ResearchService()


@router.post(
    "/{experiment_id}/interviews",
    response_model=ResearchExecuteResponse,
    status_code=status.HTTP_201_CREATED)
async def create_interview_for_experiment(
    experiment_id: str,
    request: InterviewCreateRequest) -> ResearchExecuteResponse:
    """
    Create a new interview linked to an experiment.

    The interview is automatically associated with the specified experiment.
    Uses the experiment's interview guide (from database) for context.
    Returns the execution details with ID and initial status.
    """
    # Validate experiment exists
    exp_service = get_experiment_service()
    experiment = exp_service.get_experiment_detail(experiment_id)
    if experiment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found")

    # Validate experiment has interview guide
    with get_session() as session:
        interview_guide_repo = InterviewGuideRepository(session=session)
        if not interview_guide_repo.exists(experiment_id):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Experiment does not have an interview guide configured")

    # Create research execution request with experiment_id
    # The research_service will load the interview_guide from DB
    research_request = ResearchExecuteRequest(
        topic_name=f"exp_{experiment_id}",  # Used as guide_name for logging/tracing
        experiment_id=experiment_id,
        additional_context=request.additional_context,
        synth_ids=request.synth_ids,
        synth_count=request.synth_count,
        max_turns=request.max_turns,
        generate_summary=request.generate_summary)

    # Execute via research service
    research_service = get_research_service()
    try:
        return await research_service.execute_research(research_request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e))
