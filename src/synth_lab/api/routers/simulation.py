"""
Simulation API router for synth-lab.

REST endpoints for feature scorecards, simulations, and scenarios.

References:
    - Spec: specs/016-feature-impact-simulation/spec.md
    - API contracts: specs/016-feature-impact-simulation/contracts/simulation-api.yaml
"""

import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from synth_lab.api.schemas.analysis import ClusterRequest, CutDendrogramRequest
from synth_lab.domain.entities import (
    ExtremeCasesTable,
    FailureHeatmapChart,
    FeatureScorecard,
    HierarchicalResult,
    KMeansResult,
    OutcomeDistributionChart,
    OutlierResult,
    PDPComparison,
    PDPResult,
    RadarChart,
    SankeyChart,
    ScatterCorrelationChart,
    Scenario,
    ShapExplanation,
    ShapSummary,
    SynthOutcome,
    TryVsSuccessChart,
)
# NOTE: ChartInsight entities temporarily disabled during feature 023 migration
# from synth_lab.domain.entities.chart_insight import (
#     ChartInsight,
#     ChartType,
#     SimulationInsights,
# )
from synth_lab.infrastructure.database import get_database
from synth_lab.repositories.scorecard_repository import ScorecardRepository
from synth_lab.services.simulation.chart_data_service import ChartDataService
from synth_lab.services.simulation.clustering_service import ClusteringService
from synth_lab.services.simulation.explainability_service import ExplainabilityService
# NOTE: InsightService temporarily disabled during feature 023 migration
# from synth_lab.services.simulation.insight_service import InsightGenerationError, InsightService
from synth_lab.services.simulation.outlier_service import OutlierService
from synth_lab.services.simulation.scorecard_llm import ScorecardLLM
from synth_lab.services.simulation.scorecard_service import (
    ScorecardNotFoundError,
    ScorecardService,
    ValidationError,
)
from synth_lab.services.simulation.simulation_service import SimulationService

router = APIRouter()


# --- Request/Response Models ---


class DimensionCreate(BaseModel):
    """Request model for creating a dimension."""

    score: float = Field(ge=0.0, le=1.0, description="Score value in [0,1]")
    rules_applied: list[str] = Field(default_factory=list, description="Rules applied")
    min_uncertainty: float = Field(default=0.0, ge=0.0, le=1.0)
    max_uncertainty: float = Field(default=0.0, ge=0.0, le=1.0)


class ScorecardCreate(BaseModel):
    """Request model for creating a scorecard."""

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


class ScorecardListResponse(BaseModel):
    """Response model for scorecard list."""

    scorecards: list[ScorecardResponse]
    total: int
    limit: int
    offset: int


class GenerateInsightsRequest(BaseModel):
    """Request model for generating insights."""

    generate_justification: bool = True
    generate_hypotheses: bool = True
    num_hypotheses: int = Field(default=3, ge=1, le=5)


class GenerateInsightsResponse(BaseModel):
    """Response model for generated insights."""

    justification: str | None
    impact_hypotheses: list[str]
    suggested_adjustments: list[str]


class ScenarioResponse(BaseModel):
    """Response model for a scenario."""

    id: str
    name: str
    description: str
    motivation_modifier: float
    trust_modifier: float
    friction_modifier: float
    task_criticality: float


# --- Simulation Request/Response Models ---


class SimulationConfigResponse(BaseModel):
    """Response model for simulation config."""

    n_synths: int
    n_executions: int
    sigma: float
    seed: int | None


class SimulationRequest(BaseModel):
    """Request model for running a simulation."""

    scorecard_id: str = Field(description="ID of the scorecard to use")
    scenario_id: str = Field(description="ID of the scenario to use")
    synth_ids: list[str] | None = Field(
        default=None,
        description="Optional list of synth IDs (default: all synths)",
    )
    n_executions: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="Number of Monte Carlo executions per synth",
    )
    sigma: float = Field(
        default=0.1,
        ge=0.01,
        le=0.5,
        description="Standard deviation for state sampling noise",
    )
    seed: int | None = Field(default=None, description="Random seed for reproducibility")


class AggregatedOutcomes(BaseModel):
    """Response model for aggregated outcomes."""

    did_not_try: float = Field(ge=0.0, le=1.0)
    failed: float = Field(ge=0.0, le=1.0)
    success: float = Field(ge=0.0, le=1.0)


class SimulationResponse(BaseModel):
    """Response model for a simulation run."""

    id: str
    scorecard_id: str
    scenario_id: str
    config: SimulationConfigResponse
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    total_synths: int
    aggregated_outcomes: AggregatedOutcomes | None
    execution_time_seconds: float | None


class SimulationListResponse(BaseModel):
    """Response model for simulation list."""

    simulations: list[SimulationResponse]
    total: int
    limit: int
    offset: int


class SynthOutcomeResponse(BaseModel):
    """Response model for a synth outcome."""

    synth_id: str
    did_not_try_rate: float
    failed_rate: float
    success_rate: float
    synth_attributes: dict[str, Any]


class SynthOutcomeListResponse(BaseModel):
    """Response model for synth outcome list."""

    outcomes: list[SynthOutcomeResponse]
    total: int
    limit: int
    offset: int


class RegionRuleResponse(BaseModel):
    """Response model for a region rule."""

    attribute: str
    operator: str
    threshold: float


class RegionAnalysisResponse(BaseModel):
    """Response model for a region analysis."""

    id: str
    simulation_id: str
    rules: list[RegionRuleResponse]
    rule_text: str
    synth_count: int
    synth_percentage: float
    did_not_try_rate: float
    failed_rate: float
    success_rate: float
    failure_delta: float


class RegionAnalysisListResponse(BaseModel):
    """Response model for region analysis list."""

    regions: list[RegionAnalysisResponse]
    total: int


class CompareSimulationRequest(BaseModel):
    """Request model for comparing simulations."""

    simulation_ids: list[str] = Field(
        min_length=2,
        max_length=5,
        description="List of simulation IDs to compare (2-5)",
    )


class CompareSimulationInfo(BaseModel):
    """Simulation info for comparison result."""

    id: str
    scenario_id: str
    aggregated_outcomes: dict[str, float]


class AffectedRegionResponse(BaseModel):
    """Response model for affected regions in comparison."""

    rule_text: str
    outcomes_by_scenario: dict[str, float]


class CompareResultResponse(BaseModel):
    """Response model for simulation comparison."""

    simulations: list[CompareSimulationInfo]
    most_affected_regions: list[AffectedRegionResponse]


class DimensionSensitivityResponse(BaseModel):
    """Response model for dimension sensitivity."""

    dimension: str
    baseline_value: float
    deltas_tested: list[float]
    outcomes_by_delta: dict[str, dict[str, float]]
    sensitivity_index: float
    rank: int


class SensitivityResultResponse(BaseModel):
    """Response model for sensitivity analysis result."""

    simulation_id: str
    analyzed_at: str
    deltas_used: list[float]
    dimensions: list[DimensionSensitivityResponse]
    baseline_success: float = Field(
        default=0.0, description="Baseline success rate from the original simulation"
    )


# --- Helper Functions ---


def get_scorecard_service() -> ScorecardService:
    """Get scorecard service instance."""
    db = get_database()
    repo = ScorecardRepository(db)
    return ScorecardService(repo)


def get_scorecard_llm() -> ScorecardLLM:
    """Get scorecard LLM instance."""
    return ScorecardLLM()


def get_simulation_service() -> SimulationService:
    """Get simulation service instance."""
    db = get_database()
    return SimulationService(db)


def scorecard_to_response(scorecard: FeatureScorecard) -> ScorecardResponse:
    """Convert FeatureScorecard entity to response model."""
    return ScorecardResponse(
        id=scorecard.id,
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


def load_scenarios() -> dict[str, Scenario]:
    """Load scenarios from JSON file."""
    from pathlib import Path

    # Load from project root data/config directory
    scenarios_path = (
        Path(__file__).parent.parent.parent.parent.parent
        / "data"
        / "config"
        / "scenarios.json"
    )

    if not scenarios_path.exists():
        return {}

    with open(scenarios_path, encoding="utf-8") as f:
        data = json.load(f)

    return {
        scenario_id: Scenario.model_validate({"id": scenario_id, **scenario_data})
        for scenario_id, scenario_data in data.items()
    }


# --- Scorecard Endpoints ---


@router.post("/scorecards", response_model=ScorecardResponse, status_code=201)
async def create_scorecard(request: ScorecardCreate) -> ScorecardResponse:
    """
    Create a new feature scorecard.

    Creates a scorecard with the provided dimensions and metadata.
    Returns the created scorecard with a generated ID.
    """
    service = get_scorecard_service()

    data = {
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

    try:
        scorecard = service.create_scorecard(data)
        return scorecard_to_response(scorecard)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/scorecards", response_model=ScorecardListResponse)
async def list_scorecards(
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    offset: int = Query(default=0, ge=0, description="Items to skip"),
) -> ScorecardListResponse:
    """
    List all feature scorecards with pagination.

    Returns a paginated list of scorecard summaries.
    """
    service = get_scorecard_service()
    result = service.list_scorecards(limit=limit, offset=offset)

    return ScorecardListResponse(
        scorecards=[scorecard_to_response(s) for s in result["scorecards"]],
        total=result["total"],
        limit=result["limit"],
        offset=result["offset"],
    )


@router.get("/scorecards/{scorecard_id}", response_model=ScorecardResponse)
async def get_scorecard(scorecard_id: str) -> ScorecardResponse:
    """
    Get a scorecard by ID.

    Returns the full scorecard with all dimensions and metadata.
    """
    service = get_scorecard_service()

    try:
        scorecard = service.get_scorecard(scorecard_id)
        return scorecard_to_response(scorecard)
    except ScorecardNotFoundError:
        raise HTTPException(status_code=404, detail=f"Scorecard {scorecard_id} not found")


@router.post(
    "/scorecards/{scorecard_id}/generate-insights",
    response_model=GenerateInsightsResponse,
)
async def generate_scorecard_insights(
    scorecard_id: str,
    request: GenerateInsightsRequest | None = None,
) -> GenerateInsightsResponse:
    """
    Generate LLM-powered insights for a scorecard.

    Generates justification, impact hypotheses, and suggested adjustments
    using the LLM. Results are persisted to the scorecard.
    """
    if request is None:
        request = GenerateInsightsRequest()

    service = get_scorecard_service()
    llm = get_scorecard_llm()

    try:
        scorecard = service.get_scorecard(scorecard_id)
    except ScorecardNotFoundError:
        raise HTTPException(status_code=404, detail=f"Scorecard {scorecard_id} not found")

    justification = None
    hypotheses: list[str] = []
    suggestions: list[str] = []

    if request.generate_justification:
        justification = llm.generate_justification(scorecard)

    if request.generate_hypotheses:
        hypotheses = llm.generate_impact_hypotheses(scorecard, request.num_hypotheses)

    # Always generate suggestions
    suggestions = llm.generate_suggested_adjustments(scorecard)

    # Persist insights to scorecard
    service.update_scorecard_insights(
        scorecard_id,
        justification=justification,
        impact_hypotheses=hypotheses,
    )

    return GenerateInsightsResponse(
        justification=justification,
        impact_hypotheses=hypotheses,
        suggested_adjustments=suggestions,
    )


# --- Scenario Endpoints ---


@router.get("/scenarios", response_model=list[ScenarioResponse])
async def list_scenarios() -> list[ScenarioResponse]:
    """
    List all available scenarios.

    Returns pre-defined scenarios (baseline, crisis, first-use).
    """
    scenarios = load_scenarios()

    return [
        ScenarioResponse(
            id=scenario.id,
            name=scenario.name,
            description=scenario.description,
            motivation_modifier=scenario.motivation_modifier,
            trust_modifier=scenario.trust_modifier,
            friction_modifier=scenario.friction_modifier,
            task_criticality=scenario.task_criticality,
        )
        for scenario in scenarios.values()
    ]


@router.get("/scenarios/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(scenario_id: str) -> ScenarioResponse:
    """
    Get a scenario by ID.

    Returns the scenario configuration with all modifiers.
    """
    scenarios = load_scenarios()

    if scenario_id not in scenarios:
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")

    scenario = scenarios[scenario_id]
    return ScenarioResponse(
        id=scenario.id,
        name=scenario.name,
        description=scenario.description,
        motivation_modifier=scenario.motivation_modifier,
        trust_modifier=scenario.trust_modifier,
        friction_modifier=scenario.friction_modifier,
        task_criticality=scenario.task_criticality,
    )


# --- Simulation Endpoints ---


def simulation_to_response(run: Any) -> SimulationResponse:
    """Convert SimulationRun entity to response model."""
    agg_outcomes = None
    if run.aggregated_outcomes:
        agg_outcomes = AggregatedOutcomes(
            did_not_try=run.aggregated_outcomes.get("did_not_try", 0.0),
            failed=run.aggregated_outcomes.get("failed", 0.0),
            success=run.aggregated_outcomes.get("success", 0.0),
        )

    return SimulationResponse(
        id=run.id,
        scorecard_id=run.scorecard_id,
        scenario_id=run.scenario_id,
        config=SimulationConfigResponse(
            n_synths=run.config.n_synths,
            n_executions=run.config.n_executions,
            sigma=run.config.sigma,
            seed=run.config.seed,
        ),
        status=run.status,
        started_at=run.started_at,
        completed_at=run.completed_at,
        total_synths=run.total_synths,
        aggregated_outcomes=agg_outcomes,
        execution_time_seconds=run.execution_time_seconds,
    )


@router.post("/simulations", response_model=SimulationResponse, status_code=201)
async def run_simulation(request: SimulationRequest) -> SimulationResponse:
    """
    Execute a Monte Carlo simulation.

    Runs N synths x M executions simulation and returns aggregated results.
    """
    service = get_simulation_service()

    try:
        run = service.execute_simulation(
            scorecard_id=request.scorecard_id,
            scenario_id=request.scenario_id,
            synth_ids=request.synth_ids,
            n_executions=request.n_executions,
            sigma=request.sigma,
            seed=request.seed,
        )
        return simulation_to_response(run)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


@router.get("/simulations", response_model=SimulationListResponse)
async def list_simulations_endpoint(
    scorecard_id: str | None = Query(default=None, description="Filter by scorecard"),
    scenario_id: str | None = Query(default=None, description="Filter by scenario"),
    status: str | None = Query(default=None, description="Filter by status"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    offset: int = Query(default=0, ge=0, description="Items to skip"),
) -> SimulationListResponse:
    """
    List simulation runs with optional filters.

    Returns a paginated list of simulation summaries.
    """
    service = get_simulation_service()
    result = service.list_simulations(
        scorecard_id=scorecard_id,
        scenario_id=scenario_id,
        status=status,
        limit=limit,
        offset=offset,
    )

    # Convert items back to SimulationRun objects for response conversion
    from synth_lab.domain.entities import SimulationRun

    simulations = []
    for item in result["items"]:
        run = SimulationRun.model_validate(item)
        simulations.append(simulation_to_response(run))

    return SimulationListResponse(
        simulations=simulations,
        total=result["total"],
        limit=result["limit"],
        offset=result["offset"],
    )


@router.get("/simulations/{simulation_id}", response_model=SimulationResponse)
async def get_simulation_endpoint(simulation_id: str) -> SimulationResponse:
    """
    Get a simulation run by ID.

    Returns the full simulation run with configuration and results.
    """
    service = get_simulation_service()
    run = service.get_simulation(simulation_id)

    if run is None:
        raise HTTPException(
            status_code=404, detail=f"Simulation {simulation_id} not found"
        )

    return simulation_to_response(run)


@router.get(
    "/simulations/{simulation_id}/outcomes",
    response_model=SynthOutcomeListResponse,
)
async def get_simulation_outcomes(
    simulation_id: str,
    limit: int = Query(default=100, ge=1, le=500, description="Items per page"),
    offset: int = Query(default=0, ge=0, description="Items to skip"),
) -> SynthOutcomeListResponse:
    """
    Get synth outcomes for a simulation.

    Returns paginated per-synth outcome rates.
    """
    service = get_simulation_service()

    # Verify simulation exists
    run = service.get_simulation(simulation_id)
    if run is None:
        raise HTTPException(
            status_code=404, detail=f"Simulation {simulation_id} not found"
        )

    result = service.get_simulation_outcomes(
        run_id=simulation_id,
        limit=limit,
        offset=offset,
    )

    outcomes = [
        SynthOutcomeResponse(
            synth_id=item["synth_id"],
            did_not_try_rate=item["did_not_try_rate"],
            failed_rate=item["failed_rate"],
            success_rate=item["success_rate"],
            synth_attributes=item["synth_attributes"],
        )
        for item in result["items"]
    ]

    return SynthOutcomeListResponse(
        outcomes=outcomes,
        total=result["total"],
        limit=result["limit"],
        offset=result["offset"],
    )


@router.get(
    "/simulations/{simulation_id}/regions",
    response_model=RegionAnalysisListResponse,
)
async def analyze_simulation_regions(
    simulation_id: str,
    min_failure_rate: float = Query(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum failure rate to identify problematic regions",
    ),
) -> RegionAnalysisListResponse:
    """
    Analyze simulation to identify high-failure regions.

    Uses Decision Tree Classifier to find synth attribute combinations
    that lead to high failure rates and returns interpretable rules.

    Args:
        simulation_id: ID of the simulation to analyze
        min_failure_rate: Minimum failure rate threshold (default: 0.5)

    Returns:
        List of regions with interpretable rules
    """
    from synth_lab.services.simulation.analyzer import RegionAnalyzer

    service = get_simulation_service()

    # Verify simulation exists
    run = service.get_simulation(simulation_id)
    if run is None:
        raise HTTPException(
            status_code=404, detail=f"Simulation {simulation_id} not found"
        )

    # Get simulation outcomes
    outcomes_result = service.get_simulation_outcomes(
        run_id=simulation_id,
        limit=1000,  # Get all outcomes for analysis
        offset=0,
    )

    if len(outcomes_result["items"]) < 40:  # min_samples_split from analyzer
        count = len(outcomes_result["items"])
        raise HTTPException(
            status_code=400,
            detail=f"Not enough outcomes ({count}) for region analysis. Need at least 40.",
        )

    # Run region analysis (no caching - always fresh results)
    analyzer = RegionAnalyzer()
    regions = analyzer.analyze_regions(
        outcomes=outcomes_result["items"],
        simulation_id=simulation_id,
        min_failure_rate=min_failure_rate,
    )

    # Persist regions to database for later comparison
    if regions:
        from synth_lab.repositories.region_repository import RegionRepository

        db = get_database()
        region_repo = RegionRepository(db)
        # Delete previous analyses for this simulation to avoid duplicates
        region_repo.delete_region_analyses(simulation_id)
        region_repo.save_region_analyses(regions)

    # Convert to response
    regions_response = [
        RegionAnalysisResponse(
            id=region.id,
            simulation_id=region.simulation_id,
            rules=[
                RegionRuleResponse(
                    attribute=rule.attribute,
                    operator=rule.operator,
                    threshold=rule.threshold,
                )
                for rule in region.rules
            ],
            rule_text=region.rule_text,
            synth_count=region.synth_count,
            synth_percentage=region.synth_percentage,
            did_not_try_rate=region.did_not_try_rate,
            failed_rate=region.failed_rate,
            success_rate=region.success_rate,
            failure_delta=region.failure_delta,
        )
        for region in regions
    ]

    return RegionAnalysisListResponse(
        regions=regions_response,
        total=len(regions_response),
    )


@router.post("/simulations/compare", response_model=CompareResultResponse)
async def compare_simulations(
    request: CompareSimulationRequest,
) -> CompareResultResponse:
    """
    Compare multiple simulations across scenarios.

    Identifies regions with highest variance across different scenarios
    to understand context-sensitive synth groups.

    Args:
        request: Request with list of simulation IDs to compare (2-5)

    Returns:
        Comparison result with simulations and most affected regions
    """
    from synth_lab.services.simulation.comparison_service import ComparisonService

    db = get_database()
    comparison_service = ComparisonService(db)

    try:
        result = comparison_service.compare_simulations(request.simulation_ids)

        # Convert to response models
        simulations_response = [
            CompareSimulationInfo(
                id=sim["id"],
                scenario_id=sim["scenario_id"],
                aggregated_outcomes=sim["aggregated_outcomes"],
            )
            for sim in result["simulations"]
        ]

        regions_response = [
            AffectedRegionResponse(
                rule_text=region["rule_text"],
                outcomes_by_scenario=region["outcomes_by_scenario"],
            )
            for region in result["most_affected_regions"]
        ]

        return CompareResultResponse(
            simulations=simulations_response,
            most_affected_regions=regions_response,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Comparison failed: {str(e)}"
        )


# NOTE: Sensitivity analysis results are persisted in the database
# (sensitivity_results table) for:
# - Persistence across server restarts
# - Multi-instance compatibility
# - Historical tracking
# - No memory leaks


@router.get(
    "/simulations/{simulation_id}/sensitivity",
    response_model=SensitivityResultResponse,
)
async def analyze_sensitivity(
    simulation_id: str,
    deltas: str = Query(
        default="0.05,0.10",
        description="Comma-separated delta values (e.g., '0.05,0.10')",
    ),
) -> SensitivityResultResponse:
    """
    Perform One-At-a-Time sensitivity analysis on a simulation.

    Varies each scorecard dimension independently to identify which has
    the greatest impact on outcomes.

    Args:
        simulation_id: ID of the baseline simulation
        deltas: Comma-separated delta values to test (default: "0.05,0.10")

    Returns:
        Sensitivity analysis results ranked by impact
    """
    from synth_lab.services.simulation.sensitivity import SensitivityAnalyzer

    db = get_database()
    analyzer = SensitivityAnalyzer(db)

    # Parse deltas
    try:
        delta_values = [float(d.strip()) for d in deltas.split(",")]
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid delta format. Use comma-separated floats (e.g., '0.05,0.10')",
        )

    # Validate deltas
    for delta in delta_values:
        if delta <= 0 or delta >= 1:
            raise HTTPException(
                status_code=400,
                detail=f"Delta values must be in range (0, 1), got {delta}",
            )

    try:
        result = analyzer.analyze_sensitivity(
            simulation_id=simulation_id, deltas=delta_values
        )

        # Note: Result is automatically persisted to database by analyzer

        # Convert to response
        dimensions_response = [
            DimensionSensitivityResponse(
                dimension=dim.dimension,
                baseline_value=dim.baseline_value,
                deltas_tested=dim.deltas_tested,
                outcomes_by_delta=dim.outcomes_by_delta,
                sensitivity_index=dim.sensitivity_index,
                rank=dim.rank,
            )
            for dim in result.dimensions
        ]

        return SensitivityResultResponse(
            simulation_id=result.simulation_id,
            analyzed_at=result.analyzed_at.isoformat(),
            deltas_used=result.deltas_used,
            dimensions=dimensions_response,
            baseline_success=result.baseline_success,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Sensitivity analysis failed: {str(e)}"
        )


# --- Analysis Chart Endpoints (User Story 1 & 2) ---


def get_chart_data_service() -> ChartDataService:
    """Get chart data service instance."""
    return ChartDataService()


def get_simulation_outcomes_as_entities(
    service: SimulationService, simulation_id: str, min_outcomes: int = 0
) -> list[SynthOutcome]:
    """
    Get all simulation outcomes as SynthOutcome entities.

    Args:
        service: SimulationService instance.
        simulation_id: ID of the simulation.
        min_outcomes: Minimum number of outcomes required. Raises HTTPException if not met.

    Returns:
        List of SynthOutcome entities.

    Raises:
        HTTPException: If fewer than min_outcomes outcomes are found.
    """
    from synth_lab.domain.entities import SimulationAttributes

    # Get all outcomes (up to 10000 for analysis)
    result = service.get_simulation_outcomes(run_id=simulation_id, limit=10000, offset=0)

    outcomes = []
    for item in result["items"]:
        outcome = SynthOutcome(
            simulation_id=simulation_id,
            synth_id=item["synth_id"],
            did_not_try_rate=item["did_not_try_rate"],
            failed_rate=item["failed_rate"],
            success_rate=item["success_rate"],
            synth_attributes=SimulationAttributes.model_validate(item["synth_attributes"]),
        )
        outcomes.append(outcome)

    if len(outcomes) < min_outcomes:
        raise HTTPException(
            status_code=400,
            detail=f"Simulation {simulation_id} has {len(outcomes)} outcomes, "
            f"but at least {min_outcomes} are required for this operation",
        )

    return outcomes


@router.get(
    "/simulations/{simulation_id}/charts/try-vs-success",
    response_model=TryVsSuccessChart,
)
async def get_try_vs_success_chart(
    simulation_id: str,
    attempt_rate_threshold: float = Query(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum attempt rate (1 - did_not_try_rate) for high engagement quadrants",
    ),
    success_rate_threshold: float = Query(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum success rate for high performance quadrants",
    ),
) -> TryVsSuccessChart:
    """
    Get Try vs Success scatter plot data.

    Each point represents one synth:
    - X-axis: attempt_rate = 1 - did_not_try_rate
    - Y-axis: success_rate

    Quadrants:
    - ok: high attempt, high success
    - usability_issue: high attempt, low success
    - discovery_issue: low attempt, high success
    - low_value: low attempt, low success
    """
    sim_service = get_simulation_service()
    chart_service = get_chart_data_service()

    # Verify simulation exists and is completed
    run = sim_service.get_simulation(simulation_id)
    if run is None:
        raise HTTPException(
            status_code=404, detail=f"Simulation {simulation_id} not found"
        )
    if run.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Simulation {simulation_id} not completed (status: {run.status})",
        )

    outcomes = get_simulation_outcomes_as_entities(sim_service, simulation_id)

    return chart_service.get_try_vs_success(
        simulation_id=simulation_id,
        outcomes=outcomes,
        attempt_rate_threshold=attempt_rate_threshold,
        success_rate_threshold=success_rate_threshold,
    )


@router.get(
    "/simulations/{simulation_id}/charts/distribution",
    response_model=OutcomeDistributionChart,
)
async def get_distribution_chart(
    simulation_id: str,
    sort_by: str = Query(
        default="success_rate",
        description="Field to sort by: success_rate, failed_rate, did_not_try_rate",
    ),
    order: str = Query(default="desc", description="Sort order: asc or desc"),
    limit: int = Query(default=50, ge=1, le=1000, description="Maximum results"),
) -> OutcomeDistributionChart:
    """
    Get outcome distribution chart data.

    Shows distribution of outcomes across synths, sorted by specified metric.
    """
    sim_service = get_simulation_service()
    chart_service = get_chart_data_service()

    # Verify simulation exists and is completed
    run = sim_service.get_simulation(simulation_id)
    if run is None:
        raise HTTPException(
            status_code=404, detail=f"Simulation {simulation_id} not found"
        )
    if run.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Simulation {simulation_id} not completed (status: {run.status})",
        )

    # Validate sort_by
    valid_sort_fields = ["success_rate", "failed_rate", "did_not_try_rate"]
    if sort_by not in valid_sort_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort_by: {sort_by}. Must be one of {valid_sort_fields}",
        )

    # Validate order
    if order not in ["asc", "desc"]:
        raise HTTPException(
            status_code=400, detail=f"Invalid order: {order}. Must be 'asc' or 'desc'"
        )

    outcomes = get_simulation_outcomes_as_entities(sim_service, simulation_id)

    return chart_service.get_outcome_distribution(
        simulation_id=simulation_id,
        outcomes=outcomes,
        sort_by=sort_by,  # type: ignore
        order=order,  # type: ignore
        limit=limit,
    )


@router.get(
    "/simulations/{simulation_id}/charts/sankey",
    response_model=SankeyChart,
)
async def get_sankey_chart(
    simulation_id: str,
) -> SankeyChart:
    """
    Get Sankey diagram data.

    Flow: All -> [Attempted, Not Attempted] -> [Success, Failed]
    """
    sim_service = get_simulation_service()
    chart_service = get_chart_data_service()

    # Verify simulation exists and is completed
    run = sim_service.get_simulation(simulation_id)
    if run is None:
        raise HTTPException(
            status_code=404, detail=f"Simulation {simulation_id} not found"
        )
    if run.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Simulation {simulation_id} not completed (status: {run.status})",
        )

    outcomes = get_simulation_outcomes_as_entities(sim_service, simulation_id)

    return chart_service.get_sankey(simulation_id=simulation_id, outcomes=outcomes)


@router.get(
    "/simulations/{simulation_id}/charts/failure-heatmap",
    response_model=FailureHeatmapChart,
)
async def get_failure_heatmap_chart(
    simulation_id: str,
    x_axis: str = Query(default="capability_mean", description="X-axis attribute"),
    y_axis: str = Query(default="trust_mean", description="Y-axis attribute"),
    bins: int = Query(default=5, ge=2, le=20, description="Number of bins per axis"),
    metric: str = Query(
        default="failed_rate",
        description="Metric to display: failed_rate, success_rate, did_not_try_rate",
    ),
) -> FailureHeatmapChart:
    """
    Get failure heatmap data.

    Creates a 2D binned heatmap showing metric values across two attributes.
    Useful for identifying problematic attribute combinations.
    """
    sim_service = get_simulation_service()
    chart_service = get_chart_data_service()

    # Verify simulation exists and is completed
    run = sim_service.get_simulation(simulation_id)
    if run is None:
        raise HTTPException(
            status_code=404, detail=f"Simulation {simulation_id} not found"
        )
    if run.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Simulation {simulation_id} not completed (status: {run.status})",
        )

    # Validate metric
    valid_metrics = ["failed_rate", "success_rate", "did_not_try_rate"]
    if metric not in valid_metrics:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid metric: {metric}. Must be one of {valid_metrics}",
        )

    outcomes = get_simulation_outcomes_as_entities(sim_service, simulation_id)

    return chart_service.get_failure_heatmap(
        simulation_id=simulation_id,
        outcomes=outcomes,
        x_axis=x_axis,
        y_axis=y_axis,
        bins=bins,
        metric=metric,  # type: ignore
    )


@router.get(
    "/simulations/{simulation_id}/charts/scatter",
    response_model=ScatterCorrelationChart,
)
async def get_scatter_correlation_chart(
    simulation_id: str,
    x_axis: str = Query(default="trust_mean", description="X-axis attribute"),
    y_axis: str = Query(default="success_rate", description="Y-axis attribute"),
    show_trendline: bool = Query(default=True, description="Include trend line"),
) -> ScatterCorrelationChart:
    """
    Get scatter correlation chart data.

    Shows correlation between two attributes with optional trend line.
    Includes Pearson correlation coefficient and p-value.
    """
    sim_service = get_simulation_service()
    chart_service = get_chart_data_service()

    # Verify simulation exists and is completed
    run = sim_service.get_simulation(simulation_id)
    if run is None:
        raise HTTPException(
            status_code=404, detail=f"Simulation {simulation_id} not found"
        )
    if run.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Simulation {simulation_id} not completed (status: {run.status})",
        )

    outcomes = get_simulation_outcomes_as_entities(sim_service, simulation_id)

    return chart_service.get_scatter_correlation(
        simulation_id=simulation_id,
        outcomes=outcomes,
        x_axis=x_axis,
        y_axis=y_axis,
        show_trendline=show_trendline,
    )


# --- Clustering Endpoints (User Story 3) ---


def get_clustering_service() -> ClusteringService:
    """Get clustering service instance."""
    return ClusteringService()


# Cache for clustering results (in-memory, per simulation)
# IMPORTANT: This cache has no expiration and will grow indefinitely.
# In production, consider using:
# - Redis with TTL
# - Database persistence
# - LRU cache with max size
# - Periodic cleanup task
#
# Current limitations:
# - Cache survives only during server lifetime (cleared on restart)
# - No automatic expiration (cleared only on server restart)
# - No size limit (can grow unbounded)
#
# To clear cache manually: restart the API server
# To clear programmatically: call _clear_clustering_cache() function below
_clustering_cache: dict[str, KMeansResult | HierarchicalResult] = {}


def _clear_clustering_cache() -> None:
    """Clear all cached clustering results. Useful for testing/debugging."""
    global _clustering_cache
    _clustering_cache.clear()


@router.post(
    "/simulations/{simulation_id}/clusters",
    response_model=KMeansResult | HierarchicalResult,
)
async def create_clustering(
    simulation_id: str,
    request: ClusterRequest,
) -> KMeansResult | HierarchicalResult:
    """
    Create clustering analysis for simulation.

    Supports both K-Means and Hierarchical clustering.
    Results are cached for subsequent requests.

    Args:
        simulation_id: ID of the simulation.
        request: Clustering parameters.

    Returns:
        KMeansResult or HierarchicalResult depending on method.
    """
    sim_service = get_simulation_service()
    clustering_service = get_clustering_service()

    # Verify simulation exists and is completed
    run = sim_service.get_simulation(simulation_id)
    if run is None:
        raise HTTPException(
            status_code=404, detail=f"Simulation {simulation_id} not found"
        )
    if run.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Simulation {simulation_id} not completed (status: {run.status})",
        )

    # Get outcomes
    outcomes = get_simulation_outcomes_as_entities(sim_service, simulation_id)

    if len(outcomes) < 10:
        raise HTTPException(
            status_code=400,
            detail=f"Clustering requires at least 10 synths, got {len(outcomes)}",
        )

    # Perform clustering
    if request.method == "kmeans":
        result = clustering_service.cluster_kmeans(
            simulation_id=simulation_id,
            outcomes=outcomes,
            n_clusters=request.n_clusters,
            features=request.features,
        )
    else:  # hierarchical
        result = clustering_service.cluster_hierarchical(
            simulation_id=simulation_id,
            outcomes=outcomes,
            features=request.features,
            linkage_method=request.linkage,
        )

    # Cache result
    cache_key = f"{simulation_id}:{request.method}"
    _clustering_cache[cache_key] = result

    return result


@router.get(
    "/simulations/{simulation_id}/clusters",
    response_model=KMeansResult | HierarchicalResult,
)
async def get_clustering(
    simulation_id: str,
) -> KMeansResult | HierarchicalResult:
    """
    Get cached clustering result for simulation.

    Returns the most recent clustering analysis (either K-Means or Hierarchical).

    Raises:
        404: If no clustering has been created yet.
    """
    # Try to find cached result (check both methods)
    kmeans_key = f"{simulation_id}:kmeans"
    hierarchical_key = f"{simulation_id}:hierarchical"

    if kmeans_key in _clustering_cache:
        return _clustering_cache[kmeans_key]
    elif hierarchical_key in _clustering_cache:
        return _clustering_cache[hierarchical_key]
    else:
        raise HTTPException(
            status_code=404,
            detail=f"No clustering found for simulation {simulation_id}. "
            "Create clustering first via POST /clusters",
        )


@router.get(
    "/simulations/{simulation_id}/clusters/elbow",
    response_model=list,
)
async def get_elbow_data(
    simulation_id: str,
) -> list:
    """
    Get elbow method data for determining optimal number of clusters.

    Returns elbow data from the most recent K-Means clustering.
    If no K-Means clustering exists, returns empty list.
    """
    cache_key = f"{simulation_id}:kmeans"

    if cache_key not in _clustering_cache:
        raise HTTPException(
            status_code=404,
            detail=f"No K-Means clustering found for simulation {simulation_id}. "
            "Create K-Means clustering first via POST /clusters with method='kmeans'",
        )

    result = _clustering_cache[cache_key]
    if isinstance(result, KMeansResult):
        return result.elbow_data
    else:
        raise HTTPException(
            status_code=400,
            detail="Elbow data only available for K-Means clustering",
        )


@router.get(
    "/simulations/{simulation_id}/clusters/dendrogram",
    response_model=HierarchicalResult,
)
async def get_dendrogram(
    simulation_id: str,
) -> HierarchicalResult:
    """
    Get dendrogram data for hierarchical clustering.

    Returns the hierarchical clustering result with full dendrogram.
    """
    cache_key = f"{simulation_id}:hierarchical"

    if cache_key not in _clustering_cache:
        raise HTTPException(
            status_code=404,
            detail=f"No hierarchical clustering found for simulation {simulation_id}. "
            "Create hierarchical clustering first via POST /clusters with method='hierarchical'",
        )

    result = _clustering_cache[cache_key]
    if isinstance(result, HierarchicalResult):
        return result
    else:
        raise HTTPException(
            status_code=400,
            detail="Dendrogram only available for hierarchical clustering",
        )


@router.get(
    "/simulations/{simulation_id}/clusters/{cluster_id}/radar",
    response_model=RadarChart,
)
async def get_cluster_radar(
    simulation_id: str,
    cluster_id: int,
) -> RadarChart:
    """
    Get radar chart for a specific cluster.

    Shows the feature profile of a single cluster compared to baseline.
    """
    clustering_service = get_clustering_service()

    # Get K-Means result from cache
    cache_key = f"{simulation_id}:kmeans"
    if cache_key not in _clustering_cache:
        raise HTTPException(
            status_code=404,
            detail=f"No K-Means clustering found for simulation {simulation_id}",
        )

    kmeans_result = _clustering_cache[cache_key]
    if not isinstance(kmeans_result, KMeansResult):
        raise HTTPException(
            status_code=400,
            detail="Radar chart only available for K-Means clustering",
        )

    # Verify cluster exists
    if cluster_id < 0 or cluster_id >= kmeans_result.n_clusters:
        raise HTTPException(
            status_code=404,
            detail=f"Cluster {cluster_id} not found. "
            f"Valid cluster IDs: 0 to {kmeans_result.n_clusters - 1}",
        )

    # Generate radar chart for all clusters, then filter
    full_radar = clustering_service.get_radar_chart(
        simulation_id=simulation_id,
        kmeans_result=kmeans_result,
    )

    # Return chart with only the requested cluster
    filtered_clusters = [c for c in full_radar.clusters if c.cluster_id == cluster_id]

    return RadarChart(
        simulation_id=simulation_id,
        clusters=filtered_clusters,
        axis_labels=full_radar.axis_labels,
        baseline=full_radar.baseline,
    )


@router.get(
    "/simulations/{simulation_id}/clusters/radar-comparison",
    response_model=RadarChart,
)
async def get_radar_comparison(
    simulation_id: str,
) -> RadarChart:
    """
    Get radar chart comparing all clusters.

    Shows feature profiles of all clusters side-by-side.
    """
    clustering_service = get_clustering_service()

    # Get K-Means result from cache
    cache_key = f"{simulation_id}:kmeans"
    if cache_key not in _clustering_cache:
        raise HTTPException(
            status_code=404,
            detail=f"No K-Means clustering found for simulation {simulation_id}",
        )

    kmeans_result = _clustering_cache[cache_key]
    if not isinstance(kmeans_result, KMeansResult):
        raise HTTPException(
            status_code=400,
            detail="Radar chart only available for K-Means clustering",
        )

    return clustering_service.get_radar_chart(
        simulation_id=simulation_id,
        kmeans_result=kmeans_result,
    )


@router.post(
    "/simulations/{simulation_id}/clusters/cut",
    response_model=HierarchicalResult,
)
async def cut_dendrogram(
    simulation_id: str,
    request: CutDendrogramRequest,
) -> HierarchicalResult:
    """
    Cut hierarchical clustering dendrogram at specified number of clusters.

    Updates the cached hierarchical result with cluster assignments.
    """
    clustering_service = get_clustering_service()

    # Get hierarchical result from cache
    cache_key = f"{simulation_id}:hierarchical"
    if cache_key not in _clustering_cache:
        raise HTTPException(
            status_code=404,
            detail=f"No hierarchical clustering found for simulation {simulation_id}. "
            "Create hierarchical clustering first.",
        )

    hierarchical_result = _clustering_cache[cache_key]
    if not isinstance(hierarchical_result, HierarchicalResult):
        raise HTTPException(
            status_code=400,
            detail="Cut operation only available for hierarchical clustering",
        )

    # Cut the dendrogram
    cut_result = clustering_service.cut_dendrogram(
        hierarchical_result=hierarchical_result,
        n_clusters=request.n_clusters,
    )

    # Update cache with cut result
    _clustering_cache[cache_key] = cut_result

    return cut_result


# --- Outlier Detection Endpoints (User Story 4) ---


def get_outlier_service() -> OutlierService:
    """Get outlier service instance."""
    return OutlierService()


@router.get(
    "/simulations/{simulation_id}/extreme-cases",
    response_model=ExtremeCasesTable,
)
async def get_extreme_cases(
    simulation_id: str,
    n_per_category: int = Query(
        10, ge=1, le=50, description="Number of synths per category"
    ),
) -> ExtremeCasesTable:
    """
    Get extreme cases for qualitative research.

    Returns top N worst failures, best successes, and unexpected cases
    for UX researchers to conduct qualitative interviews.

    Args:
        simulation_id: ID of the simulation.
        n_per_category: Number of synths per category (1-50, default: 10).

    Returns:
        ExtremeCasesTable with categorized synths and interview questions.
    """
    sim_service = get_simulation_service()
    outlier_service = get_outlier_service()

    # Verify simulation exists and is completed
    run = sim_service.get_simulation(simulation_id)
    if run is None:
        raise HTTPException(
            status_code=404, detail=f"Simulation {simulation_id} not found"
        )
    if run.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Simulation {simulation_id} not completed (status: {run.status})",
        )

    # Get outcomes
    outcomes = get_simulation_outcomes_as_entities(sim_service, simulation_id)

    if len(outcomes) < 10:
        raise HTTPException(
            status_code=400,
            detail=f"Extreme cases requires at least 10 synths, got {len(outcomes)}",
        )

    # Get extreme cases
    result = outlier_service.get_extreme_cases(
        simulation_id=simulation_id,
        outcomes=outcomes,
        n_per_category=n_per_category,
    )

    return result


@router.get(
    "/simulations/{simulation_id}/outliers",
    response_model=OutlierResult,
)
async def detect_outliers(
    simulation_id: str,
    contamination: float = Query(
        0.1,
        ge=0.01,
        le=0.5,
        description="Expected proportion of outliers (0.01-0.5)",
    ),
) -> OutlierResult:
    """
    Detect statistical outliers using Isolation Forest.

    Identifies synths with atypical profiles or unexpected outcomes
    for deeper qualitative analysis.

    Args:
        simulation_id: ID of the simulation.
        contamination: Expected proportion of outliers (0.01-0.5, default: 0.1).

    Returns:
        OutlierResult with detected outliers and classifications.
    """
    sim_service = get_simulation_service()
    outlier_service = get_outlier_service()

    # Verify simulation exists and is completed
    run = sim_service.get_simulation(simulation_id)
    if run is None:
        raise HTTPException(
            status_code=404, detail=f"Simulation {simulation_id} not found"
        )
    if run.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Simulation {simulation_id} not completed (status: {run.status})",
        )

    # Get outcomes
    outcomes = get_simulation_outcomes_as_entities(sim_service, simulation_id)

    if len(outcomes) < 10:
        raise HTTPException(
            status_code=400,
            detail=f"Outlier detection requires at least 10 synths, got {len(outcomes)}",
        )

    # Detect outliers
    result = outlier_service.detect_outliers(
        simulation_id=simulation_id,
        outcomes=outcomes,
        contamination=contamination,
    )

    return result


# --- Explainability Endpoints (User Story 5 - SHAP & PDP) ---


def get_explainability_service() -> ExplainabilityService:
    """Get explainability service instance."""
    return ExplainabilityService()


@router.get(
    "/simulations/{simulation_id}/shap/summary",
    response_model=ShapSummary,
)
async def get_shap_summary(
    simulation_id: str,
) -> ShapSummary:
    """
    Get global SHAP summary showing feature importance.

    Computes mean absolute SHAP values across all synths to rank
    features by their overall impact on success rate predictions.

    Args:
        simulation_id: ID of the simulation.

    Returns:
        ShapSummary with feature importances and top features.
    """
    sim_service = get_simulation_service()
    explain_service = get_explainability_service()

    # Verify simulation exists and is completed
    run = sim_service.get_simulation(simulation_id)
    if run is None:
        raise HTTPException(
            status_code=404, detail=f"Simulation {simulation_id} not found"
        )
    if run.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Simulation {simulation_id} not completed (status: {run.status})",
        )

    # Get outcomes
    outcomes = get_simulation_outcomes_as_entities(sim_service, simulation_id)

    if len(outcomes) < 20:
        raise HTTPException(
            status_code=400,
            detail=f"SHAP summary requires at least 20 synths, got {len(outcomes)}",
        )

    try:
        result = explain_service.get_shap_summary(
            simulation_id=simulation_id,
            outcomes=outcomes,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/simulations/{simulation_id}/shap/{synth_id}",
    response_model=ShapExplanation,
)
async def get_shap_explanation(
    simulation_id: str,
    synth_id: str,
) -> ShapExplanation:
    """
    Get SHAP explanation for a specific synth.

    Explains why the synth had its success rate by showing the contribution
    of each feature using SHAP (SHapley Additive exPlanations) values.

    Args:
        simulation_id: ID of the simulation.
        synth_id: ID of the synth to explain.

    Returns:
        ShapExplanation with feature contributions and explanation text.
    """
    sim_service = get_simulation_service()
    explain_service = get_explainability_service()

    # Verify simulation exists and is completed
    run = sim_service.get_simulation(simulation_id)
    if run is None:
        raise HTTPException(
            status_code=404, detail=f"Simulation {simulation_id} not found"
        )
    if run.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Simulation {simulation_id} not completed (status: {run.status})",
        )

    # Get outcomes
    outcomes = get_simulation_outcomes_as_entities(sim_service, simulation_id)

    if len(outcomes) < 20:
        raise HTTPException(
            status_code=400,
            detail=f"SHAP explanation requires at least 20 synths, got {len(outcomes)}",
        )

    try:
        result = explain_service.explain_synth(
            simulation_id=simulation_id,
            outcomes=outcomes,
            synth_id=synth_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/simulations/{simulation_id}/pdp",
    response_model=PDPResult,
)
async def get_pdp(
    simulation_id: str,
    feature: str = Query(
        ..., description="Feature name to analyze (e.g., 'trust_mean', 'capability_mean')"
    ),
    grid_resolution: int = Query(
        default=20, ge=5, le=100, description="Number of points in PDP curve"
    ),
) -> PDPResult:
    """
    Get Partial Dependence Plot for a feature.

    Shows how changing the feature value affects the predicted
    success rate, averaging over all other features.

    Args:
        simulation_id: ID of the simulation.
        feature: Feature name to analyze.
        grid_resolution: Number of points in PDP curve.

    Returns:
        PDPResult with PDP curve, effect type, and strength.
    """
    sim_service = get_simulation_service()
    explain_service = get_explainability_service()

    # Verify simulation exists and is completed
    run = sim_service.get_simulation(simulation_id)
    if run is None:
        raise HTTPException(
            status_code=404, detail=f"Simulation {simulation_id} not found"
        )
    if run.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Simulation {simulation_id} not completed (status: {run.status})",
        )

    # Get outcomes
    outcomes = get_simulation_outcomes_as_entities(sim_service, simulation_id)

    if len(outcomes) < 20:
        raise HTTPException(
            status_code=400,
            detail=f"PDP requires at least 20 synths, got {len(outcomes)}",
        )

    try:
        result = explain_service.calculate_pdp(
            simulation_id=simulation_id,
            outcomes=outcomes,
            feature=feature,
            grid_resolution=grid_resolution,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/simulations/{simulation_id}/pdp/comparison",
    response_model=PDPComparison,
)
async def get_pdp_comparison(
    simulation_id: str,
    features: str = Query(
        ...,
        description="Comma-separated features (e.g., 'trust_mean,capability_mean')",
    ),
    grid_resolution: int = Query(
        default=20, ge=5, le=100, description="Number of points in each PDP curve"
    ),
) -> PDPComparison:
    """
    Compare PDPs across multiple features.

    Shows how different features affect success rate predictions
    and ranks them by effect strength.

    Args:
        simulation_id: ID of the simulation.
        features: Comma-separated list of feature names.
        grid_resolution: Number of points in each PDP curve.

    Returns:
        PDPComparison with all PDPs and feature ranking.
    """
    sim_service = get_simulation_service()
    explain_service = get_explainability_service()

    # Verify simulation exists and is completed
    run = sim_service.get_simulation(simulation_id)
    if run is None:
        raise HTTPException(
            status_code=404, detail=f"Simulation {simulation_id} not found"
        )
    if run.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Simulation {simulation_id} not completed (status: {run.status})",
        )

    # Parse features
    feature_list = [f.strip() for f in features.split(",") if f.strip()]
    if len(feature_list) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 features required for comparison",
        )

    # Get outcomes
    outcomes = get_simulation_outcomes_as_entities(sim_service, simulation_id)

    if len(outcomes) < 20:
        raise HTTPException(
            status_code=400,
            detail=f"PDP comparison requires at least 20 synths, got {len(outcomes)}",
        )

    try:
        result = explain_service.compare_pdps(
            simulation_id=simulation_id,
            outcomes=outcomes,
            features=feature_list,
            grid_resolution=grid_resolution,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- LLM Insight Endpoints (Feature 023 - under construction) ---

# NOTE: These endpoints are temporarily commented out during feature 023 migration.
# They will be replaced with new insight endpoints in Phase 4 of the migration.

# def get_insight_service() -> InsightService:
#     """Get insight service instance."""
#     return InsightService()
#
#
# # Request/Response models for insights
# class GenerateChartInsightRequest(BaseModel):
#     """Request model for generating chart insight."""
#
#     chart_data: dict = Field(description="Chart data to analyze")
#     force_regenerate: bool = Field(
#         default=False, description="Force regenerate even if cached"
#     )
#
#
# class ExecutiveSummaryResponse(BaseModel):
#     """Response model for executive summary."""
#
#     simulation_id: str
#     summary: str | None
#     total_insights: int
#
#
# @router.get(
#     "/simulations/{simulation_id}/insights",
#     response_model=SimulationInsights,
# )
# async def get_all_insights(
#     simulation_id: str,
# ) -> SimulationInsights:
#     """
#     Get all cached insights for a simulation.
#
#     Returns all previously generated chart insights and metadata.
#     Use the POST endpoint to generate new insights.
#
#     Args:
#         simulation_id: ID of the simulation.
#
#     Returns:
#         SimulationInsights with all cached insights.
#     """
#     sim_service = get_simulation_service()
#
#     # Verify simulation exists
#     run = sim_service.get_simulation(simulation_id)
#     if run is None:
#         raise HTTPException(
#             status_code=404, detail=f"Simulation {simulation_id} not found"
#         )
#
#     insight_service = get_insight_service()
#     return insight_service.get_all_insights(simulation_id)
#
#
# # IMPORTANT: executive-summary must be defined BEFORE {chart_type} to avoid route conflict
# @router.post(
#     "/simulations/{simulation_id}/insights/executive-summary",
#     response_model=ExecutiveSummaryResponse,
# )
# async def generate_executive_summary(
#     simulation_id: str,
# ) -> ExecutiveSummaryResponse:
#     """
#     Generate executive summary across all insights.
#
#     Synthesizes all chart insights into a concise executive summary
#     highlighting key findings and prioritized recommendations.
#
#     Requires at least one insight to be generated first.
#
#     Args:
#         simulation_id: ID of the simulation.
#
#     Returns:
#         ExecutiveSummaryResponse with summary text.
#     """
#     sim_service = get_simulation_service()
#
#     # Verify simulation exists
#     run = sim_service.get_simulation(simulation_id)
#     if run is None:
#         raise HTTPException(
#             status_code=404, detail=f"Simulation {simulation_id} not found"
#         )
#
#     insight_service = get_insight_service()
#
#     # Check if there are any insights to summarize
#     all_insights = insight_service.get_all_insights(simulation_id)
#     if len(all_insights.insights) == 0:
#         raise HTTPException(
#             status_code=400,
#             detail="No insights available to summarize. Generate chart insights first.",
#         )
#
#     try:
#         summary = insight_service.generate_executive_summary(simulation_id)
#         return ExecutiveSummaryResponse(
#             simulation_id=simulation_id,
#             summary=summary,
#             total_insights=len(all_insights.insights),
#         )
#     except Exception as e:
#         raise HTTPException(
#             status_code=500, detail=f"Failed to generate executive summary: {e}"
#         )
#
#
# @router.post(
#     "/simulations/{simulation_id}/insights/{chart_type}",
#     response_model=ChartInsight,
# )
# async def generate_chart_insight(
#     simulation_id: str,
#     chart_type: ChartType,
#     request: GenerateChartInsightRequest,
# ) -> ChartInsight:
#     """
#     Generate LLM insight for a specific chart.
#
#     Analyzes the chart data and generates:
#     - Short caption (<=20 tokens)
#     - Detailed explanation (<=200 tokens)
#     - Evidence from data
#     - Actionable recommendation
#
#     Results are cached for subsequent requests.
#
#     Args:
#         simulation_id: ID of the simulation.
#         chart_type: Type of chart to analyze.
#         request: Chart data and options.
#
#     Returns:
#         ChartInsight with analysis.
#     """
#     sim_service = get_simulation_service()
#
#     # Verify simulation exists and is completed
#     run = sim_service.get_simulation(simulation_id)
#     if run is None:
#         raise HTTPException(
#             status_code=404, detail=f"Simulation {simulation_id} not found"
#         )
#     if run.status != "completed":
#         raise HTTPException(
#             status_code=400,
#             detail=f"Simulation {simulation_id} not completed (status: {run.status})",
#         )
#
#     insight_service = get_insight_service()
#
#     try:
#         insight = insight_service.generate_insight(
#             simulation_id=simulation_id,
#             chart_type=chart_type,
#             chart_data=request.chart_data,
#             force=request.force_regenerate,
#         )
#         return insight
#     except InsightGenerationError as e:
#         raise HTTPException(status_code=500, detail=str(e))
#
#
# @router.delete(
#     "/simulations/{simulation_id}/insights",
#     status_code=204,
# )
# async def clear_insights(
#     simulation_id: str,
# ) -> None:
#     """
#     Clear all cached insights for a simulation.
#
#     Removes all cached insights, requiring regeneration on next request.
#
#     Args:
#         simulation_id: ID of the simulation.
#     """
#     insight_service = get_insight_service()
#     insight_service.clear_insights(simulation_id=simulation_id)


if __name__ == "__main__":
    import sys

    print("=== Simulation Router Validation ===")

    all_validation_failures = []
    total_tests = 0

    # Test 1: Router has routes
    total_tests += 1
    try:
        if len(router.routes) < 10:
            all_validation_failures.append(
                f"Expected at least 10 routes, got {len(router.routes)}"
            )
        else:
            print(f"Test 1 PASSED: Router has {len(router.routes)} routes")
    except Exception as e:
        all_validation_failures.append(f"Router routes test failed: {e}")

    # Test 2: Check route paths
    total_tests += 1
    try:
        paths = [r.path for r in router.routes]
        expected_paths = [
            "/scorecards",
            "/scorecards/{scorecard_id}",
            "/scorecards/{scorecard_id}/generate-insights",
            "/scenarios",
            "/scenarios/{scenario_id}",
            "/simulations",
            "/simulations/{simulation_id}",
            "/simulations/{simulation_id}/outcomes",
        ]
        missing = [p for p in expected_paths if p not in paths]
        if missing:
            all_validation_failures.append(f"Missing routes: {missing}")
        else:
            print("Test 2 PASSED: All expected routes present")
    except Exception as e:
        all_validation_failures.append(f"Route paths test failed: {e}")

    # Test 3: ScorecardCreate validation
    total_tests += 1
    try:
        data = ScorecardCreate(
            feature_name="Test",
            use_scenario="Test",
            description_text="Test description",
        )
        if data.feature_name != "Test":
            all_validation_failures.append("ScorecardCreate feature_name mismatch")
        else:
            print("Test 3 PASSED: ScorecardCreate model works")
    except Exception as e:
        all_validation_failures.append(f"ScorecardCreate validation failed: {e}")

    # Test 4: DimensionCreate validation
    total_tests += 1
    try:
        dim = DimensionCreate(score=0.5, rules_applied=["rule1"])
        if dim.score != 0.5:
            all_validation_failures.append("DimensionCreate score mismatch")
        else:
            print("Test 4 PASSED: DimensionCreate model works")
    except Exception as e:
        all_validation_failures.append(f"DimensionCreate validation failed: {e}")

    # Test 5: Load scenarios
    total_tests += 1
    try:
        scenarios = load_scenarios()
        if len(scenarios) != 3:
            all_validation_failures.append(
                f"Expected 3 scenarios, got {len(scenarios)}"
            )
        elif "baseline" not in scenarios:
            all_validation_failures.append("Missing baseline scenario")
        else:
            print(f"Test 5 PASSED: Loaded {len(scenarios)} scenarios")
    except Exception as e:
        all_validation_failures.append(f"Load scenarios failed: {e}")

    # Test 6: Scenario to response conversion
    total_tests += 1
    try:
        scenarios = load_scenarios()
        if scenarios:
            response = ScenarioResponse(
                id=scenarios["baseline"].id,
                name=scenarios["baseline"].name,
                description=scenarios["baseline"].description,
                motivation_modifier=scenarios["baseline"].motivation_modifier,
                trust_modifier=scenarios["baseline"].trust_modifier,
                friction_modifier=scenarios["baseline"].friction_modifier,
                task_criticality=scenarios["baseline"].task_criticality,
            )
            if response.id != "baseline":
                all_validation_failures.append("Scenario response ID mismatch")
            else:
                print("Test 6 PASSED: Scenario response conversion works")
    except Exception as e:
        all_validation_failures.append(f"Scenario response test failed: {e}")

    # Final result
    print()
    if all_validation_failures:
        print(
            f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:"
        )
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
