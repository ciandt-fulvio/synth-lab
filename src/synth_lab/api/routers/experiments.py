"""
T020 Experiments API router for synth-lab.

REST endpoints for experiment management.

References:
    - Spec: specs/018-experiment-hub/spec.md
    - OpenAPI: specs/018-experiment-hub/contracts/openapi.yaml
"""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from synth_lab.infrastructure.database import DatabaseManager, get_database
from synth_lab.models.pagination import PaginatedResponse, PaginationParams
from synth_lab.models.research import ResearchExecuteRequest, ResearchExecuteResponse
from synth_lab.repositories.experiment_repository import ExperimentSummary
from synth_lab.repositories.research_repository import ResearchRepository
from synth_lab.repositories.scorecard_repository import ScorecardRepository
from synth_lab.repositories.simulation_repository import SimulationRepository
from synth_lab.services.experiment_service import ExperimentService
from synth_lab.services.research_service import ResearchService
from synth_lab.services.simulation.scorecard_service import ScorecardService, ValidationError

router = APIRouter()


# Request/Response Schemas

class ExperimentCreate(BaseModel):
    """Request schema for creating an experiment."""

    name: str = Field(
        min_length=1,
        max_length=100,
        description="Short name of the feature.",
    )
    hypothesis: str = Field(
        min_length=1,
        max_length=500,
        description="Description of the hypothesis to test.",
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Additional context, links, references.",
    )


class ExperimentUpdate(BaseModel):
    """Request schema for updating an experiment."""

    name: str | None = Field(
        default=None,
        max_length=100,
        description="Short name of the feature.",
    )
    hypothesis: str | None = Field(
        default=None,
        max_length=500,
        description="Description of the hypothesis to test.",
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Additional context, links, references.",
    )


class SimulationSummary(BaseModel):
    """Summary of a simulation for experiment detail."""

    id: str
    scenario_id: str | None = None
    status: str = "pending"
    has_insights: bool = False
    started_at: datetime | None = None
    completed_at: datetime | None = None
    score: float | None = None


class InterviewSummary(BaseModel):
    """Summary of an interview for experiment detail."""

    exec_id: str
    topic_name: str
    status: str = "pending"
    synth_count: int = 0
    has_summary: bool = False
    has_prfaq: bool = False
    started_at: datetime | None = None
    completed_at: datetime | None = None


class ExperimentDetailResponse(BaseModel):
    """Response schema for experiment detail."""

    id: str
    name: str
    hypothesis: str
    description: str | None = None
    simulation_count: int = 0
    interview_count: int = 0
    created_at: datetime
    updated_at: datetime | None = None
    simulations: list[SimulationSummary] = Field(default_factory=list)
    interviews: list[InterviewSummary] = Field(default_factory=list)


class ExperimentResponse(BaseModel):
    """Response schema for experiment."""

    id: str
    name: str
    hypothesis: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime | None = None


# Scorecard schemas for experiment-linked scorecards

class DimensionCreate(BaseModel):
    """Request model for creating a dimension."""

    score: float = Field(ge=0.0, le=1.0, description="Score value in [0,1]")
    rules_applied: list[str] = Field(default_factory=list, description="Rules applied")
    min_uncertainty: float = Field(default=0.0, ge=0.0, le=1.0)
    max_uncertainty: float = Field(default=0.0, ge=0.0, le=1.0)


class ScorecardCreateRequest(BaseModel):
    """Request model for creating a scorecard linked to an experiment."""

    feature_name: str = Field(description="Name of the feature")
    use_scenario: str = Field(description="Usage scenario")
    description_text: str = Field(description="Feature description")
    evaluators: list[str] = Field(default_factory=list, description="List of evaluators")
    description_media_urls: list[str] = Field(
        default_factory=list, description="Media URLs"
    )
    complexity: DimensionCreate | None = None
    initial_effort: DimensionCreate | None = None
    perceived_risk: DimensionCreate | None = None
    time_to_value: DimensionCreate | None = None


class ScorecardResponse(BaseModel):
    """Response model for a scorecard."""

    id: str
    experiment_id: str | None = None
    feature_name: str
    use_scenario: str
    description_text: str
    complexity_score: float
    initial_effort_score: float
    perceived_risk_score: float
    time_to_value_score: float
    justification: str | None
    impact_hypotheses: list[str]
    created_at: datetime
    updated_at: datetime | None


def get_experiment_service() -> ExperimentService:
    """Get experiment service instance."""
    return ExperimentService()


@router.post("", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED)
async def create_experiment(data: ExperimentCreate) -> ExperimentResponse:
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
        )
        return ExperimentResponse(
            id=experiment.id,
            name=experiment.name,
            hypothesis=experiment.hypothesis,
            description=experiment.description,
            created_at=experiment.created_at,
            updated_at=experiment.updated_at,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.get("/list", response_model=PaginatedResponse[ExperimentSummary])
async def list_experiments(
    limit: int = Query(default=50, ge=1, le=200, description="Maximum items per page"),
    offset: int = Query(default=0, ge=0, description="Number of items to skip"),
) -> PaginatedResponse[ExperimentSummary]:
    """
    List all experiments with pagination.

    Returns a paginated list of experiments with simulation and interview counts.
    """
    service = get_experiment_service()
    params = PaginationParams(
        limit=limit,
        offset=offset,
        sort_by="created_at",
        sort_order="desc",
    )
    return service.list_experiments(params)


@router.get("/{experiment_id}", response_model=ExperimentDetailResponse)
async def get_experiment(experiment_id: str) -> ExperimentDetailResponse:
    """
    Get an experiment by ID with full details.

    Returns the experiment with linked simulations and interviews.
    """
    service = get_experiment_service()

    # Get experiment detail (with counts)
    experiment = service.get_experiment_detail(experiment_id)
    if experiment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found",
        )

    # Fetch actual simulations (via scorecards)
    db = get_database()
    sim_repo = SimulationRepository(db)
    simulation_runs, _ = sim_repo.list_by_experiment_id(experiment_id, limit=100)
    simulations = [
        SimulationSummary(
            id=run.id,
            scenario_id=run.scenario_id,
            status=run.status,
            has_insights=run.aggregated_outcomes is not None,
            started_at=run.started_at,
            completed_at=run.completed_at,
            score=(
                _calculate_simulation_score(run.aggregated_outcomes)
                if run.aggregated_outcomes
                else None
            ),
        )
        for run in simulation_runs
    ]

    # Fetch actual interviews
    research_repo = ResearchRepository(db)
    interview_response = research_repo.list_executions_by_experiment(
        experiment_id, PaginationParams(limit=100)
    )

    # Batch check for summary and prfaq existence
    exec_ids = [exec.exec_id for exec in interview_response.data]
    summary_exists = _check_summaries_exist(db, exec_ids)
    prfaq_exists = _check_prfaqs_exist(db, exec_ids)

    interviews = [
        InterviewSummary(
            exec_id=exec.exec_id,
            topic_name=exec.topic_name,
            status=exec.status.value if hasattr(exec.status, 'value') else str(exec.status),
            synth_count=exec.synth_count,
            has_summary=summary_exists.get(exec.exec_id, False),
            has_prfaq=prfaq_exists.get(exec.exec_id, False),
            started_at=exec.started_at,
            completed_at=exec.completed_at,
        )
        for exec in interview_response.data
    ]

    return ExperimentDetailResponse(
        id=experiment.id,
        name=experiment.name,
        hypothesis=experiment.hypothesis,
        description=experiment.description,
        simulation_count=experiment.simulation_count,
        interview_count=experiment.interview_count,
        created_at=experiment.created_at,
        updated_at=experiment.updated_at,
        simulations=simulations,
        interviews=interviews,
    )


def _check_summaries_exist(db: DatabaseManager, exec_ids: list[str]) -> dict[str, bool]:
    """Check which executions have summary_content.

    Args:
        db: Database manager.
        exec_ids: List of execution IDs to check.

    Returns:
        Dict mapping exec_id to True if summary exists.
    """
    if not exec_ids:
        return {}

    placeholders = ",".join("?" * len(exec_ids))
    rows = db.fetchall(
        f"""
        SELECT exec_id
        FROM research_executions
        WHERE exec_id IN ({placeholders})
        AND summary_content IS NOT NULL
        AND summary_content != ''
        """,
        tuple(exec_ids),
    )
    return {row["exec_id"]: True for row in rows}


def _check_prfaqs_exist(db: DatabaseManager, exec_ids: list[str]) -> dict[str, bool]:
    """Check which executions have prfaq_metadata.

    Args:
        db: Database manager.
        exec_ids: List of execution IDs to check.

    Returns:
        Dict mapping exec_id to True if prfaq exists.
    """
    if not exec_ids:
        return {}

    placeholders = ",".join("?" * len(exec_ids))
    rows = db.fetchall(
        f"""
        SELECT exec_id
        FROM prfaq_metadata
        WHERE exec_id IN ({placeholders})
        AND status = 'completed'
        """,
        tuple(exec_ids),
    )
    return {row["exec_id"]: True for row in rows}


def _calculate_simulation_score(aggregated_outcomes: dict) -> float | None:
    """Calculate a simple score from aggregated outcomes (success rate * 100)."""
    if not aggregated_outcomes:
        return None
    success_rate = aggregated_outcomes.get("success", 0)
    return round(success_rate * 100, 1)


@router.put("/{experiment_id}", response_model=ExperimentResponse)
async def update_experiment(
    experiment_id: str,
    data: ExperimentUpdate,
) -> ExperimentResponse:
    """
    Update an experiment.

    Returns the updated experiment.
    """
    service = get_experiment_service()
    try:
        updated = service.update_experiment(
            experiment_id,
            name=data.name,
            hypothesis=data.hypothesis,
            description=data.description,
        )
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experiment {experiment_id} not found",
            )
        return ExperimentResponse(
            id=updated.id,
            name=updated.name,
            hypothesis=updated.hypothesis,
            description=updated.description,
            created_at=updated.created_at,
            updated_at=updated.updated_at,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


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
            detail=f"Experiment {experiment_id} not found",
        )


# --- Scorecard Endpoints ---


def get_scorecard_service() -> ScorecardService:
    """Get scorecard service instance."""
    db = get_database()
    repo = ScorecardRepository(db)
    return ScorecardService(repo)


@router.post(
    "/{experiment_id}/scorecards",
    response_model=ScorecardResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_scorecard_for_experiment(
    experiment_id: str,
    request: ScorecardCreateRequest,
) -> ScorecardResponse:
    """
    Create a new scorecard linked to an experiment.

    The scorecard is automatically associated with the specified experiment.
    Returns the created scorecard with a generated ID.
    """
    # Validate experiment exists
    exp_service = get_experiment_service()
    experiment = exp_service.get_experiment_detail(experiment_id)
    if experiment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found",
        )

    # Build scorecard data with experiment_id
    data = {
        "experiment_id": experiment_id,
        "feature_name": request.feature_name,
        "use_scenario": request.use_scenario,
        "description_text": request.description_text,
        "evaluators": request.evaluators,
        "description_media_urls": request.description_media_urls,
    }

    if request.complexity:
        data["complexity"] = request.complexity.model_dump()
    if request.initial_effort:
        data["initial_effort"] = request.initial_effort.model_dump()
    if request.perceived_risk:
        data["perceived_risk"] = request.perceived_risk.model_dump()
    if request.time_to_value:
        data["time_to_value"] = request.time_to_value.model_dump()

    # Create scorecard
    scorecard_service = get_scorecard_service()
    try:
        scorecard = scorecard_service.create_scorecard(data)
        return ScorecardResponse(
            id=scorecard.id,
            experiment_id=scorecard.experiment_id,
            feature_name=scorecard.identification.feature_name,
            use_scenario=scorecard.identification.use_scenario,
            description_text=scorecard.description_text,
            complexity_score=scorecard.complexity.score,
            initial_effort_score=scorecard.initial_effort.score,
            perceived_risk_score=scorecard.perceived_risk.score,
            time_to_value_score=scorecard.time_to_value.score,
            justification=scorecard.justification,
            impact_hypotheses=scorecard.impact_hypotheses,
            created_at=scorecard.created_at,
            updated_at=scorecard.updated_at,
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


# --- Interview Endpoints ---


class InterviewCreateRequest(BaseModel):
    """Request model for creating an interview linked to an experiment."""

    topic_name: str = Field(description="Topic guide name")
    additional_context: str | None = Field(
        default=None,
        description="Additional context to complement the research scenario",
    )
    synth_ids: list[str] | None = Field(
        default=None,
        description="Specific synth IDs to interview",
    )
    synth_count: int | None = Field(
        default=5,
        ge=1,
        le=50,
        description="Number of random synths (if synth_ids not provided)",
    )
    max_turns: int = Field(
        default=6,
        ge=1,
        le=20,
        description="Max interview turns (each turn = 1 question + 1 answer)",
    )
    generate_summary: bool = Field(default=True, description="Generate summary after completion")


def get_research_service() -> ResearchService:
    """Get research service instance."""
    return ResearchService()


@router.post(
    "/{experiment_id}/interviews",
    response_model=ResearchExecuteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_interview_for_experiment(
    experiment_id: str,
    request: InterviewCreateRequest,
) -> ResearchExecuteResponse:
    """
    Create a new interview linked to an experiment.

    The interview is automatically associated with the specified experiment.
    Returns the execution details with ID and initial status.
    """
    # Validate experiment exists
    exp_service = get_experiment_service()
    experiment = exp_service.get_experiment_detail(experiment_id)
    if experiment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found",
        )

    # Create research execution request with experiment_id
    research_request = ResearchExecuteRequest(
        topic_name=request.topic_name,
        experiment_id=experiment_id,
        additional_context=request.additional_context,
        synth_ids=request.synth_ids,
        synth_count=request.synth_count,
        max_turns=request.max_turns,
        generate_summary=request.generate_summary,
    )

    # Execute via research service
    research_service = get_research_service()
    return await research_service.execute_research(research_request)
