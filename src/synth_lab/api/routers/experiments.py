"""
Experiments API router for synth-lab.

REST endpoints for experiment management with embedded scorecard support.

References:
    - Spec: specs/019-experiment-refactor/spec.md
    - OpenAPI: specs/019-experiment-refactor/contracts/experiment-api.yaml
"""

import asyncio

from fastapi import APIRouter, HTTPException, Query, status
from loguru import logger
from pydantic import BaseModel, Field

from synth_lab.api.schemas.experiments import (
    AggregatedOutcomesSchema,
    AnalysisSummary,
    ExperimentDetail,
    ExperimentResponse,
    InterviewSummary,
    PaginatedExperimentSummary,
    ScorecardDataSchema,
    ScorecardDimensionSchema,
    ScorecardEstimateResponse)
from synth_lab.api.schemas.experiments import (
    ExperimentCreate as ExperimentCreateSchema)
from synth_lab.api.schemas.experiments import (
    ExperimentSummary as ExperimentSummarySchema)
from synth_lab.api.schemas.experiments import (
    ExperimentUpdate as ExperimentUpdateSchema)
from synth_lab.api.schemas.exploration import ExplorationSummary
from synth_lab.domain.entities.experiment import ScorecardData, ScorecardDimension
from synth_lab.infrastructure.database_v2 import get_session
from synth_lab.models.pagination import PaginationParams
from synth_lab.models.research import ResearchExecuteRequest, ResearchExecuteResponse
from synth_lab.repositories.analysis_repository import AnalysisRepository
from synth_lab.repositories.exploration_repository import ExplorationRepository
from synth_lab.repositories.interview_guide_repository import InterviewGuideRepository
from synth_lab.repositories.research_repository import ResearchRepository
from synth_lab.repositories.synth_repository import SynthRepository
from synth_lab.services.experiment_service import ExperimentService
from synth_lab.services.interview_guide_generator_service import (
    generate_interview_guide_async)
from synth_lab.services.research_service import ResearchService
from synth_lab.services.scorecard_estimator import (
    ScorecardEstimationError,
    ScorecardEstimator)

router = APIRouter()


# =============================================================================
# Helper Functions
# =============================================================================


def get_experiment_service() -> ExperimentService:
    """Get experiment service instance."""
    return ExperimentService()


def _convert_schema_to_scorecard_data(
    schema: ScorecardDataSchema) -> ScorecardData:
    """Convert API schema to domain entity."""
    return ScorecardData(
        feature_name=schema.feature_name,
        scenario=schema.scenario,
        description_text=schema.description_text,
        description_media_urls=schema.description_media_urls,
        complexity=ScorecardDimension(
            score=schema.complexity.score,
            rules_applied=schema.complexity.rules_applied,
            lower_bound=schema.complexity.lower_bound,
            upper_bound=schema.complexity.upper_bound),
        initial_effort=ScorecardDimension(
            score=schema.initial_effort.score,
            rules_applied=schema.initial_effort.rules_applied,
            lower_bound=schema.initial_effort.lower_bound,
            upper_bound=schema.initial_effort.upper_bound),
        perceived_risk=ScorecardDimension(
            score=schema.perceived_risk.score,
            rules_applied=schema.perceived_risk.rules_applied,
            lower_bound=schema.perceived_risk.lower_bound,
            upper_bound=schema.perceived_risk.upper_bound),
        time_to_value=ScorecardDimension(
            score=schema.time_to_value.score,
            rules_applied=schema.time_to_value.rules_applied,
            lower_bound=schema.time_to_value.lower_bound,
            upper_bound=schema.time_to_value.upper_bound),
        justification=schema.justification,
        impact_hypotheses=schema.impact_hypotheses)


def _convert_scorecard_data_to_schema(
    data: ScorecardData) -> ScorecardDataSchema:
    """Convert domain entity to API schema."""
    return ScorecardDataSchema(
        feature_name=data.feature_name,
        scenario=data.scenario,
        description_text=data.description_text,
        description_media_urls=data.description_media_urls,
        complexity=ScorecardDimensionSchema(
            score=data.complexity.score,
            rules_applied=data.complexity.rules_applied,
            lower_bound=data.complexity.lower_bound,
            upper_bound=data.complexity.upper_bound),
        initial_effort=ScorecardDimensionSchema(
            score=data.initial_effort.score,
            rules_applied=data.initial_effort.rules_applied,
            lower_bound=data.initial_effort.lower_bound,
            upper_bound=data.initial_effort.upper_bound),
        perceived_risk=ScorecardDimensionSchema(
            score=data.perceived_risk.score,
            rules_applied=data.perceived_risk.rules_applied,
            lower_bound=data.perceived_risk.lower_bound,
            upper_bound=data.perceived_risk.upper_bound),
        time_to_value=ScorecardDimensionSchema(
            score=data.time_to_value.score,
            rules_applied=data.time_to_value.rules_applied,
            lower_bound=data.time_to_value.lower_bound,
            upper_bound=data.time_to_value.upper_bound),
        justification=data.justification,
        impact_hypotheses=data.impact_hypotheses)


# =============================================================================
# Experiment CRUD Endpoints
# =============================================================================


@router.post("", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED)
async def create_experiment(data: ExperimentCreateSchema) -> ExperimentResponse:
    """
    Create a new experiment, optionally with embedded scorecard.

    Returns the created experiment with generated ID.
    """
    service = get_experiment_service()
    try:
        # Convert scorecard schema if provided
        scorecard_data = None
        if data.scorecard_data:
            scorecard_data = _convert_schema_to_scorecard_data(data.scorecard_data)

        experiment = service.create_experiment(
            name=data.name,
            hypothesis=data.hypothesis,
            description=data.description,
            synth_group_id=data.synth_group_id,
            scorecard_data=scorecard_data)

        # Trigger async interview guide generation (non-blocking)
        asyncio.create_task(
            generate_interview_guide_async(
                experiment_id=experiment.id,
                name=experiment.name,
                hypothesis=experiment.hypothesis,
                description=experiment.description)
        )
        logger.info(f"Interview guide generation started for experiment: {experiment.id}")

        # Build response with scorecard if present
        scorecard_schema = None
        if experiment.scorecard_data:
            scorecard_schema = _convert_scorecard_data_to_schema(experiment.scorecard_data)

        # Check if interview guide exists (newly created experiments won't have one)
        with get_session() as session:
            interview_guide_repo = InterviewGuideRepository(session=session)
            has_interview_guide = interview_guide_repo.exists(experiment.id)

        return ExperimentResponse(
            id=experiment.id,
            name=experiment.name,
            hypothesis=experiment.hypothesis,
            description=experiment.description,
            synth_group_id=experiment.synth_group_id,
            scorecard_data=scorecard_schema,
            has_scorecard=experiment.has_scorecard(),
            has_interview_guide=has_interview_guide,
            tags=experiment.tags,
            created_at=experiment.created_at,
            updated_at=experiment.updated_at)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e))


class ScorecardEstimateRequest(BaseModel):
    """Request for AI scorecard estimation from text."""

    name: str = Field(
        max_length=100,
        description="Short name of the feature.")
    hypothesis: str = Field(
        max_length=500,
        description="Description of the hypothesis to test.")
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Additional context.")


@router.post(
    "/estimate-scorecard",
    response_model=ScorecardEstimateResponse,
    status_code=status.HTTP_200_OK)
async def estimate_scorecard_from_text(
    request: ScorecardEstimateRequest) -> ScorecardEstimateResponse:
    """
    Use AI to estimate scorecard dimensions from text input.

    This endpoint allows estimation before an experiment exists,
    useful for forms where the user wants AI-generated estimates.
    Takes name, hypothesis, and optional description as input.
    """
    estimator = ScorecardEstimator()
    try:
        estimate = estimator.estimate_from_text(
            name=request.name,
            hypothesis=request.hypothesis,
            description=request.description)
        return ScorecardEstimateResponse(
            complexity=ScorecardDimensionSchema(
                score=estimate.complexity.value,
                rules_applied=[],
                lower_bound=estimate.complexity.min,
                upper_bound=estimate.complexity.max),
            initial_effort=ScorecardDimensionSchema(
                score=estimate.initial_effort.value,
                rules_applied=[],
                lower_bound=estimate.initial_effort.min,
                upper_bound=estimate.initial_effort.max),
            perceived_risk=ScorecardDimensionSchema(
                score=estimate.perceived_risk.value,
                rules_applied=[],
                lower_bound=estimate.perceived_risk.min,
                upper_bound=estimate.perceived_risk.max),
            time_to_value=ScorecardDimensionSchema(
                score=estimate.time_to_value.value,
                rules_applied=[],
                lower_bound=estimate.time_to_value.min,
                upper_bound=estimate.time_to_value.max),
            justification=getattr(estimate, "justification", ""),
            impact_hypotheses=getattr(estimate, "impact_hypotheses", []))
    except ScorecardEstimationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e))


@router.get("/list", response_model=PaginatedExperimentSummary)
async def list_experiments(
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

    Returns a paginated list of experiments with analysis and interview counts.
    """
    service = get_experiment_service()
    params = PaginationParams(
        limit=limit,
        offset=offset,
        search=search,
        tag=tag,
        sort_by=sort_by,
        sort_order=sort_order)
    result = service.list_experiments(params)

    # Convert repository summaries to API schemas
    summaries = [
        ExperimentSummarySchema(
            id=exp.id,
            name=exp.name,
            hypothesis=exp.hypothesis,
            description=exp.description,
            synth_group_id=exp.synth_group_id,
            synth_group_name=exp.synth_group_name,
            has_scorecard=exp.has_scorecard,
            has_analysis=exp.has_analysis,
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
async def get_experiment(experiment_id: str) -> ExperimentDetail:
    """
    Get an experiment by ID with full details.

    Returns the experiment with scorecard, analysis, and interviews.
    """
    service = get_experiment_service()

    # Get full experiment (with scorecard)
    experiment = service.get_experiment(experiment_id)
    if experiment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found")

    with get_session() as session:
        # Get synth group name
        from synth_lab.models.orm.synth import SynthGroup as SynthGroupORM
        from sqlalchemy import select

        synth_group_name = "Unknown"
        stmt = select(SynthGroupORM.name).where(SynthGroupORM.id == experiment.synth_group_id)
        result = session.execute(stmt).scalar_one_or_none()
        if result:
            synth_group_name = result

        # Get analysis (1:1 relationship)
        analysis_repo = AnalysisRepository(session=session)
        analysis_run = analysis_repo.get_by_experiment_id(experiment_id)
        analysis_summary = None
        if analysis_run:
            outcomes_schema = None
            if analysis_run.aggregated_outcomes:
                outcomes_schema = AggregatedOutcomesSchema(
                    did_not_try_rate=analysis_run.aggregated_outcomes.did_not_try_rate,
                    failed_rate=analysis_run.aggregated_outcomes.failed_rate,
                    success_rate=analysis_run.aggregated_outcomes.success_rate)
            analysis_summary = AnalysisSummary(
                id=analysis_run.id,
                simulation_id=analysis_run.id,  # Use analysis ID for chart endpoints
                status=analysis_run.status,
                started_at=analysis_run.started_at,
                completed_at=analysis_run.completed_at,
                total_synths=analysis_run.total_synths,
                n_executions=analysis_run.config.n_executions,
                execution_time_seconds=analysis_run.execution_time_seconds,
                aggregated_outcomes=outcomes_schema)

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

        # Build response with scorecard if present
        scorecard_schema = None
        if experiment.scorecard_data:
            scorecard_schema = _convert_scorecard_data_to_schema(experiment.scorecard_data)

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
        scorecard_data=scorecard_schema,
        has_scorecard=experiment.has_scorecard(),
        has_interview_guide=has_interview_guide,
        tags=experiment.tags,
        created_at=experiment.created_at,
        updated_at=experiment.updated_at,
        analysis=analysis_summary,
        interviews=interviews,
        interview_count=len(interviews))


@router.put("/{experiment_id}", response_model=ExperimentResponse)
async def update_experiment(
    experiment_id: str,
    data: ExperimentUpdateSchema) -> ExperimentResponse:
    """
    Update an experiment (name, hypothesis, description only).

    To update the scorecard, use PUT /experiments/{id}/scorecard.
    """
    service = get_experiment_service()
    try:
        updated = service.update_experiment(
            experiment_id,
            name=data.name,
            hypothesis=data.hypothesis,
            description=data.description)
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experiment {experiment_id} not found")

        scorecard_schema = None
        if updated.scorecard_data:
            scorecard_schema = _convert_scorecard_data_to_schema(updated.scorecard_data)

        # Check if interview guide exists
        with get_session() as session:
            interview_guide_repo = InterviewGuideRepository(session=session)
            has_interview_guide = interview_guide_repo.exists(experiment_id)

        return ExperimentResponse(
            id=updated.id,
            name=updated.name,
            hypothesis=updated.hypothesis,
            description=updated.description,
            synth_group_id=updated.synth_group_id,
            scorecard_data=scorecard_schema,
            has_scorecard=updated.has_scorecard(),
            has_interview_guide=has_interview_guide,
            tags=updated.tags,
            created_at=updated.created_at,
            updated_at=updated.updated_at)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e))


@router.delete("/{experiment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_experiment(experiment_id: str) -> None:
    """
    Delete an experiment.

    Returns 204 No Content on success.
    """
    service = get_experiment_service()
    deleted = service.delete_experiment(experiment_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found")


# =============================================================================
# Scorecard Endpoints (Embedded in Experiment)
# =============================================================================


@router.put("/{experiment_id}/scorecard", response_model=ExperimentResponse)
async def update_scorecard(
    experiment_id: str,
    data: ScorecardDataSchema) -> ExperimentResponse:
    """
    Update the embedded scorecard of an experiment.

    Creates or replaces the scorecard data for the experiment.
    """
    service = get_experiment_service()

    # Convert schema to domain entity
    scorecard_data = _convert_schema_to_scorecard_data(data)

    try:
        updated = service.update_scorecard(experiment_id, scorecard_data)
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experiment {experiment_id} not found")

        scorecard_schema = None
        if updated.scorecard_data:
            scorecard_schema = _convert_scorecard_data_to_schema(updated.scorecard_data)

        # Check if interview guide exists
        with get_session() as session:
            interview_guide_repo = InterviewGuideRepository(session=session)
            has_interview_guide = interview_guide_repo.exists(experiment_id)

        return ExperimentResponse(
            id=updated.id,
            name=updated.name,
            hypothesis=updated.hypothesis,
            description=updated.description,
            synth_group_id=updated.synth_group_id,
            scorecard_data=scorecard_schema,
            has_scorecard=updated.has_scorecard(),
            has_interview_guide=has_interview_guide,
            tags=updated.tags,
            created_at=updated.created_at,
            updated_at=updated.updated_at)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e))


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


@router.get(
    "/{experiment_id}/interviews/auto",
    response_model=ResearchExecuteResponse | None)
async def get_auto_interview_for_experiment(
    experiment_id: str) -> ResearchExecuteResponse | None:
    """
    Get the auto-interview execution for this experiment if it exists.

    Returns the most recent auto-interview (extreme cases) created for this experiment.
    Returns None if no auto-interview has been created yet.

    Args:
        experiment_id: Experiment ID.

    Returns:
        ResearchExecuteResponse with interview details, or None if not found.
    """
    with get_session() as session:
        research_repo = ResearchRepository(session=session)
        execution = research_repo.get_auto_interview_for_experiment(experiment_id)

        if execution is None:
            return None

        return ResearchExecuteResponse(
            exec_id=execution.exec_id,
            status=execution.status,
            topic_name=execution.topic_name,
            synth_count=execution.synth_count,
            started_at=execution.started_at)


@router.post(
    "/{experiment_id}/interviews/auto",
    response_model=ResearchExecuteResponse,
    status_code=status.HTTP_201_CREATED)
async def create_auto_interview_for_experiment(
    experiment_id: str) -> ResearchExecuteResponse:
    """
    Create an interview with extreme case synths (top 5 + bottom 5).

    Automatically selects the 10 most extreme cases (5 best + 5 worst performers)
    from the experiment's simulation results and creates an interview with them.

    Requires:
    - Experiment must exist
    - Experiment must have an interview guide configured
    - Simulation must have at least 10 synths

    Returns:
        ResearchExecuteResponse: Interview execution details with ID
    """
    # Validate experiment exists
    exp_service = get_experiment_service()
    experiment = exp_service.get_experiment_detail(experiment_id)
    if experiment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found")

    with get_session() as session:
        # Validate experiment has interview guide
        interview_guide_repo = InterviewGuideRepository(session=session)
        if not interview_guide_repo.exists(experiment_id):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Experiment does not have an interview guide configured")

        # Get extreme cases (top 5 + bottom 5)
        synth_repo = SynthRepository(session=session)
        bottom_ids, top_ids = synth_repo.get_extreme_cases(experiment_id, top_n=5)

        # Validate we have at least 10 synths
        total_synths = len(bottom_ids) + len(top_ids)
        if total_synths < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Not enough synths for auto-interview. Found {total_synths}, "
                f"need 10 (5 best + 5 worst).")

        # Combine extreme cases (bottom 5 first, then top 5)
        extreme_synth_ids = bottom_ids[:5] + top_ids[:5]

    # Create research execution request with extreme synth IDs
    auto_context = "Entrevista automática com casos extremos (5 piores + 5 melhores)"
    research_request = ResearchExecuteRequest(
        topic_name=f"exp_{experiment_id}_auto",
        experiment_id=experiment_id,
        additional_context=auto_context,
        synth_ids=extreme_synth_ids,
        max_turns=5,
        generate_summary=True)

    # Execute via research service
    research_service = get_research_service()
    try:
        return await research_service.execute_research(research_request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e))


# =============================================================================
# Exploration Endpoints
# =============================================================================


@router.get(
    "/{experiment_id}/explorations",
    response_model=list[ExplorationSummary])
async def list_explorations_for_experiment(
    experiment_id: str) -> list[ExplorationSummary]:
    """
    List all explorations for an experiment.

    Returns a list of exploration summaries ordered by start date (most recent first).

    Args:
        experiment_id: Experiment ID.

    Returns:
        List of exploration summaries.

    Raises:
        404: Experiment not found.
    """
    # Validate experiment exists
    exp_service = get_experiment_service()
    experiment = exp_service.get_experiment(experiment_id)
    if experiment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found")

    # Get explorations
    with get_session() as session:
        exploration_repo = ExplorationRepository(session=session)
        explorations = exploration_repo.list_explorations_by_experiment(experiment_id)

        return [
            ExplorationSummary(
                id=e.id,
                status=e.status.value,
                goal_value=e.goal.value,
                best_success_rate=e.best_success_rate,
                total_nodes=e.total_nodes,
                started_at=e.started_at,
                completed_at=e.completed_at)
            for e in explorations
        ]


@router.post(
    "/{experiment_id}/estimate-scorecard",
    response_model=ScorecardEstimateResponse,
    status_code=status.HTTP_200_OK)
async def estimate_scorecard_for_experiment(
    experiment_id: str) -> ScorecardEstimateResponse:
    """
    Use AI to estimate scorecard dimensions for an experiment.

    Takes the experiment's name, hypothesis, and description,
    and returns AI-generated estimates for all scorecard dimensions.
    """
    # Validate experiment exists and get details
    exp_service = get_experiment_service()
    experiment = exp_service.get_experiment(experiment_id)
    if experiment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found")

    # Use ScorecardEstimator service (handles LLM call with tracing)
    estimator = ScorecardEstimator()
    try:
        estimate = estimator.estimate_from_experiment(experiment)
        return ScorecardEstimateResponse(
            complexity=ScorecardDimensionSchema(
                score=estimate.complexity.value,
                rules_applied=[],
                lower_bound=estimate.complexity.min,
                upper_bound=estimate.complexity.max),
            initial_effort=ScorecardDimensionSchema(
                score=estimate.initial_effort.value,
                rules_applied=[],
                lower_bound=estimate.initial_effort.min,
                upper_bound=estimate.initial_effort.max),
            perceived_risk=ScorecardDimensionSchema(
                score=estimate.perceived_risk.value,
                rules_applied=[],
                lower_bound=estimate.perceived_risk.min,
                upper_bound=estimate.perceived_risk.max),
            time_to_value=ScorecardDimensionSchema(
                score=estimate.time_to_value.value,
                rules_applied=[],
                lower_bound=estimate.time_to_value.min,
                upper_bound=estimate.time_to_value.max),
            justification=getattr(estimate, "justification", ""),
            impact_hypotheses=getattr(estimate, "impact_hypotheses", []))
    except ScorecardEstimationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e))
