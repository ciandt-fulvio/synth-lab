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

from synth_lab.domain.entities import (
    FeatureScorecard,
    RegionAnalysis,
    Scenario,
)
from synth_lab.infrastructure.database import get_database
from synth_lab.repositories.scorecard_repository import ScorecardRepository
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
    from synth_lab.repositories.region_repository import RegionRepository
    from synth_lab.services.simulation.analyzer import RegionAnalyzer

    db = get_database()
    service = get_simulation_service()
    region_repo = RegionRepository(db)

    # Verify simulation exists
    run = service.get_simulation(simulation_id)
    if run is None:
        raise HTTPException(
            status_code=404, detail=f"Simulation {simulation_id} not found"
        )

    # Check if analysis already exists
    existing_regions = region_repo.get_region_analyses(simulation_id)
    if existing_regions:
        # Return cached results
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
            for region in existing_regions
        ]

        return RegionAnalysisListResponse(
            regions=regions_response,
            total=len(regions_response),
        )

    # Get simulation outcomes
    outcomes_result = service.get_simulation_outcomes(
        run_id=simulation_id,
        limit=1000,  # Get all outcomes for analysis
        offset=0,
    )

    if len(outcomes_result["items"]) < 40:  # min_samples_split from analyzer
        raise HTTPException(
            status_code=400,
            detail=f"Not enough outcomes ({len(outcomes_result['items'])}) for region analysis. Need at least 40.",
        )

    # Run region analysis
    analyzer = RegionAnalyzer()
    regions = analyzer.analyze_regions(
        outcomes=outcomes_result["items"],
        simulation_id=simulation_id,
        min_failure_rate=min_failure_rate,
    )

    # Save results
    if regions:
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
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Sensitivity analysis failed: {str(e)}"
        )


if __name__ == "__main__":
    import sys

    print("=== Simulation Router Validation ===\n")

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
