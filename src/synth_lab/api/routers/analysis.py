"""
Analysis API router for synth-lab.

REST endpoints for quantitative analysis (1:1 with experiments).

References:
    - Spec: specs/019-experiment-refactor/spec.md
    - OpenAPI: specs/019-experiment-refactor/contracts/analysis-api.yaml
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from synth_lab.api.schemas.analysis_run import (
    AggregatedOutcomesSchema,
    AnalysisConfigSchema,
    AnalysisResponse,
    InsightSchema,
    InsightsResponse,
    InterviewSuggestionsResponse,
    PaginatedSynthOutcomes,
    RegionAnalysisResponse,
    SynthAttributesSchema,
    SynthOutcomeResponse,
)
from synth_lab.domain.entities.chart_data import (
    OutcomeDistributionChart,
    SankeyChart,
    TryVsSuccessChart,
)
from synth_lab.repositories.analysis_outcome_repository import AnalysisOutcomeRepository
from synth_lab.services.simulation.chart_data_service import ChartDataService
from synth_lab.domain.entities.analysis_run import AggregatedOutcomes, AnalysisConfig
from synth_lab.infrastructure.database import get_database
from synth_lab.models.pagination import PaginationParams
from synth_lab.repositories.analysis_repository import AnalysisRepository
from synth_lab.repositories.experiment_repository import ExperimentRepository
from synth_lab.services.analysis.analysis_service import AnalysisService
from synth_lab.services.analysis.analysis_execution_service import AnalysisExecutionService
from synth_lab.services.experiment_service import ExperimentService

router = APIRouter()


# =============================================================================
# Helper Functions
# =============================================================================


def get_analysis_service() -> AnalysisService:
    """Get analysis service instance."""
    db = get_database()
    return AnalysisService(
        db=db,
        analysis_repo=AnalysisRepository(db),
        experiment_repo=ExperimentRepository(db),
    )


def get_experiment_service() -> ExperimentService:
    """Get experiment service instance."""
    return ExperimentService()


def get_execution_service() -> AnalysisExecutionService:
    """Get analysis execution service instance."""
    return AnalysisExecutionService()


def get_chart_data_service() -> ChartDataService:
    """Get chart data service instance."""
    return ChartDataService()


def get_outcome_repository() -> AnalysisOutcomeRepository:
    """Get analysis outcome repository instance."""
    return AnalysisOutcomeRepository()


def _convert_config_schema_to_domain(schema: AnalysisConfigSchema) -> AnalysisConfig:
    """Convert API schema to domain entity."""
    return AnalysisConfig(
        n_synths=schema.n_synths,
        n_executions=schema.n_executions,
        sigma=schema.sigma,
        seed=schema.seed,
    )


def _convert_config_to_schema(config: AnalysisConfig) -> AnalysisConfigSchema:
    """Convert domain entity to API schema."""
    return AnalysisConfigSchema(
        n_synths=config.n_synths,
        n_executions=config.n_executions,
        sigma=config.sigma,
        seed=config.seed,
    )


def _convert_outcomes_to_schema(
    outcomes: AggregatedOutcomes,
) -> AggregatedOutcomesSchema:
    """Convert domain entity to API schema."""
    return AggregatedOutcomesSchema(
        did_not_try_rate=outcomes.did_not_try_rate,
        failed_rate=outcomes.failed_rate,
        success_rate=outcomes.success_rate,
    )


# =============================================================================
# Request Models
# =============================================================================


class RunAnalysisRequest(BaseModel):
    """Request model for running analysis."""

    n_synths: int = Field(
        default=500,
        ge=10,
        le=10000,
        description="Number of synths to simulate.",
    )
    n_executions: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="Number of Monte Carlo executions per synth.",
    )
    sigma: float = Field(
        default=0.05,
        ge=0.0,
        le=0.5,
        description="Standard deviation for noise.",
    )
    seed: int | None = Field(
        default=None,
        description="Random seed for reproducibility.",
    )


# =============================================================================
# Analysis Endpoints
# =============================================================================


@router.get("/{experiment_id}/analysis", response_model=AnalysisResponse)
async def get_analysis(experiment_id: str) -> AnalysisResponse:
    """
    Get the analysis for an experiment.

    Returns the unique quantitative analysis (1:1 relationship).
    """
    service = get_analysis_service()
    analysis = service.get_analysis(experiment_id)

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No analysis found for experiment {experiment_id}",
        )

    # Convert to response
    outcomes_schema = None
    if analysis.aggregated_outcomes:
        outcomes_schema = _convert_outcomes_to_schema(analysis.aggregated_outcomes)

    return AnalysisResponse(
        id=analysis.id,
        experiment_id=analysis.experiment_id,
        config=_convert_config_to_schema(analysis.config),
        status=analysis.status,
        started_at=analysis.started_at,
        completed_at=analysis.completed_at,
        total_synths=analysis.total_synths,
        aggregated_outcomes=outcomes_schema,
        execution_time_seconds=analysis.execution_time_seconds,
    )


@router.post(
    "/{experiment_id}/analysis",
    response_model=AnalysisResponse,
    status_code=status.HTTP_201_CREATED,
)
async def run_analysis(
    experiment_id: str,
    request: RunAnalysisRequest | None = None,
) -> AnalysisResponse:
    """
    Execute (or re-execute) quantitative analysis.

    Runs a Monte Carlo simulation for the experiment. If an analysis already
    exists, it is deleted and replaced (re-run).

    Requires the experiment to have a scorecard.
    """
    service = get_analysis_service()
    execution_service = get_execution_service()

    # Check if already running
    existing = service.get_analysis(experiment_id)
    if existing and existing.status == "running":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Analysis for experiment {experiment_id} is already running",
        )

    # Build config
    config = None
    if request:
        config = AnalysisConfig(
            n_synths=request.n_synths,
            n_executions=request.n_executions,
            sigma=request.sigma,
            seed=request.seed,
        )

    try:
        # Execute the analysis (this actually runs Monte Carlo!)
        analysis = execution_service.execute_analysis(experiment_id, config)

        # Convert outcomes if present
        outcomes_schema = None
        if analysis.aggregated_outcomes:
            outcomes_schema = _convert_outcomes_to_schema(analysis.aggregated_outcomes)

        return AnalysisResponse(
            id=analysis.id,
            experiment_id=analysis.experiment_id,
            config=_convert_config_to_schema(analysis.config),
            status=analysis.status,
            started_at=analysis.started_at,
            completed_at=analysis.completed_at,
            total_synths=analysis.total_synths,
            aggregated_outcomes=outcomes_schema,
            execution_time_seconds=analysis.execution_time_seconds,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis execution failed: {str(e)}",
        )


@router.delete(
    "/{experiment_id}/analysis",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_analysis(experiment_id: str) -> None:
    """
    Delete the analysis for an experiment.

    Removes the analysis and all associated results.
    """
    service = get_analysis_service()
    deleted = service.delete_analysis(experiment_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No analysis found for experiment {experiment_id}",
        )


# =============================================================================
# Outcomes Endpoints
# =============================================================================


@router.get(
    "/{experiment_id}/analysis/outcomes",
    response_model=PaginatedSynthOutcomes,
)
async def list_outcomes(
    experiment_id: str,
    limit: int = Query(default=50, ge=1, le=500, description="Items per page"),
    offset: int = Query(default=0, ge=0, description="Items to skip"),
) -> PaginatedSynthOutcomes:
    """
    List synth outcomes for an analysis.

    Returns paginated individual synth results.
    """
    service = get_analysis_service()
    analysis = service.get_analysis(experiment_id)

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No analysis found for experiment {experiment_id}",
        )

    # Get outcomes from repository
    db = get_database()
    from synth_lab.repositories.synth_outcome_repository import SynthOutcomeRepository

    outcome_repo = SynthOutcomeRepository(db)
    result = outcome_repo.list_by_analysis_id(
        analysis_id=analysis.id,
        params=PaginationParams(limit=limit, offset=offset),
    )

    # Convert to response
    outcomes = []
    for outcome in result.data:
        # Convert SimulationAttributes to schema dictionaries
        observables_dict = {}
        latent_traits_dict = {}
        if outcome.synth_attributes:
            observables_dict = outcome.synth_attributes.observables.model_dump()
            latent_traits_dict = outcome.synth_attributes.latent_traits.model_dump()

        attrs = SynthAttributesSchema(
            observables=observables_dict,
            latent_traits=latent_traits_dict,
        )
        outcomes.append(
            SynthOutcomeResponse(
                id=outcome.id,
                synth_id=outcome.synth_id,
                did_not_try_rate=outcome.did_not_try_rate,
                failed_rate=outcome.failed_rate,
                success_rate=outcome.success_rate,
                synth_attributes=attrs,
            )
        )

    return PaginatedSynthOutcomes(
        data=outcomes,
        pagination=result.pagination,
    )


# =============================================================================
# Region Analysis Endpoints
# =============================================================================


@router.get(
    "/{experiment_id}/analysis/regions",
    response_model=RegionAnalysisResponse,
)
async def analyze_regions(
    experiment_id: str,
    min_failure_rate: float = Query(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Minimum failure rate for high-risk regions",
    ),
) -> RegionAnalysisResponse:
    """
    Analyze high-risk regions in the analysis.

    Identifies clusters of synths with high failure rates.
    """
    service = get_analysis_service()
    analysis = service.get_analysis(experiment_id)

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No analysis found for experiment {experiment_id}",
        )

    if analysis.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Analysis must be completed to analyze regions (status: {analysis.status})",
        )

    # TODO: Implement region analysis using clustering
    # For now, return empty regions
    return RegionAnalysisResponse(regions=[])


# =============================================================================
# Interview Suggestions Endpoints
# =============================================================================


@router.get(
    "/{experiment_id}/analysis/interview-suggestions",
    response_model=InterviewSuggestionsResponse,
)
async def get_interview_suggestions(
    experiment_id: str,
    max_suggestions: int = Query(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of suggestions",
    ),
) -> InterviewSuggestionsResponse:
    """
    Get interview suggestions based on analysis.

    Suggests representative synths for qualitative interviews
    based on high-risk regions.
    """
    service = get_analysis_service()
    analysis = service.get_analysis(experiment_id)

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No analysis found for experiment {experiment_id}",
        )

    if analysis.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Analysis must be completed for interview suggestions "
            f"(status: {analysis.status})",
        )

    # TODO: Implement interview suggestions based on region analysis
    # For now, return empty suggestions
    return InterviewSuggestionsResponse(suggestions=[])


# =============================================================================
# Insights Endpoints
# =============================================================================


@router.get(
    "/{experiment_id}/analysis/insights",
    response_model=InsightsResponse,
)
async def get_insights(
    experiment_id: str,
) -> InsightsResponse:
    """
    Get AI-generated insights from the analysis.

    Returns previously generated insights.
    """
    service = get_analysis_service()
    analysis = service.get_analysis(experiment_id)

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No analysis found for experiment {experiment_id}",
        )

    # TODO: Implement insights retrieval from database
    # For now, return empty insights
    return InsightsResponse(
        insights=[],
        generated_at=datetime.now(timezone.utc),
    )


@router.post(
    "/{experiment_id}/analysis/insights",
    response_model=InsightsResponse,
)
async def generate_insights(
    experiment_id: str,
) -> InsightsResponse:
    """
    Generate AI insights from analysis results.

    Uses LLM to analyze outcomes and generate actionable insights.
    """
    service = get_analysis_service()
    analysis = service.get_analysis(experiment_id)

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No analysis found for experiment {experiment_id}",
        )

    if analysis.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Analysis must be completed to generate insights (status: {analysis.status})",
        )

    # TODO: Implement LLM insight generation
    # For now, return placeholder insights
    return InsightsResponse(
        insights=[
            InsightSchema(
                type="recommendation",
                title="Analysis Complete",
                description="Analysis completed successfully. Full insight generation coming soon.",
                confidence=0.5,
            )
        ],
        generated_at=datetime.now(timezone.utc),
    )


# =============================================================================
# Chart Endpoints
# =============================================================================


@router.get(
    "/{experiment_id}/analysis/charts/try-vs-success",
    response_model=TryVsSuccessChart,
)
async def get_try_vs_success_chart(
    experiment_id: str,
    attempt_rate_threshold: float = Query(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum attempt rate for high engagement quadrants",
    ),
    success_rate_threshold: float = Query(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum success rate for high performance quadrants",
    ),
) -> TryVsSuccessChart:
    """
    Get Try vs Success scatter plot data for an analysis.

    Each point represents one synth with attempt rate vs success rate.
    """
    service = get_analysis_service()
    chart_service = get_chart_data_service()
    outcome_repo = get_outcome_repository()

    analysis = service.get_analysis(experiment_id)
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No analysis found for experiment {experiment_id}",
        )

    if analysis.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Analysis must be completed (status: {analysis.status})",
        )

    outcomes, _ = outcome_repo.get_outcomes(analysis.id)
    if not outcomes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No outcomes found for this analysis",
        )

    return chart_service.get_try_vs_success(
        simulation_id=analysis.id,
        outcomes=outcomes,
        x_threshold=attempt_rate_threshold,
        y_threshold=success_rate_threshold,
    )


@router.get(
    "/{experiment_id}/analysis/charts/distribution",
    response_model=OutcomeDistributionChart,
)
async def get_distribution_chart(
    experiment_id: str,
    sort_by: str = Query(
        default="success_rate",
        description="Field to sort by: success_rate, failed_rate, did_not_try_rate",
    ),
    order: str = Query(default="desc", description="Sort order: asc or desc"),
    limit: int = Query(default=50, ge=1, le=1000, description="Maximum results"),
) -> OutcomeDistributionChart:
    """
    Get outcome distribution chart data for an analysis.

    Shows distribution of outcomes across synths.
    """
    service = get_analysis_service()
    chart_service = get_chart_data_service()
    outcome_repo = get_outcome_repository()

    analysis = service.get_analysis(experiment_id)
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No analysis found for experiment {experiment_id}",
        )

    if analysis.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Analysis must be completed (status: {analysis.status})",
        )

    outcomes, _ = outcome_repo.get_outcomes(analysis.id)
    if not outcomes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No outcomes found for this analysis",
        )

    return chart_service.get_outcome_distribution(
        simulation_id=analysis.id,
        outcomes=outcomes,
        sort_by=sort_by,
        order=order,
        limit=limit,
    )


@router.get(
    "/{experiment_id}/analysis/charts/sankey",
    response_model=SankeyChart,
)
async def get_sankey_chart(
    experiment_id: str,
) -> SankeyChart:
    """
    Get Sankey diagram data for an analysis.

    Shows the flow of users through try/success/fail states.
    """
    service = get_analysis_service()
    chart_service = get_chart_data_service()
    outcome_repo = get_outcome_repository()

    analysis = service.get_analysis(experiment_id)
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No analysis found for experiment {experiment_id}",
        )

    if analysis.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Analysis must be completed (status: {analysis.status})",
        )

    outcomes, _ = outcome_repo.get_outcomes(analysis.id)
    if not outcomes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No outcomes found for this analysis",
        )

    return chart_service.get_sankey(
        simulation_id=analysis.id,
        outcomes=outcomes,
    )


# =============================================================================
# Validation
# =============================================================================

if __name__ == "__main__":
    import sys

    print("=== Analysis Router Validation ===")

    all_validation_failures = []
    total_tests = 0

    # Test 1: Router has routes
    total_tests += 1
    try:
        if len(router.routes) < 5:
            all_validation_failures.append(
                f"Expected at least 5 routes, got {len(router.routes)}"
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
            "/{experiment_id}/analysis",
            "/{experiment_id}/analysis/outcomes",
            "/{experiment_id}/analysis/regions",
            "/{experiment_id}/analysis/interview-suggestions",
            "/{experiment_id}/analysis/insights",
        ]
        missing = [p for p in expected_paths if p not in paths]
        if missing:
            all_validation_failures.append(f"Missing routes: {missing}")
        else:
            print("Test 2 PASSED: All expected routes present")
    except Exception as e:
        all_validation_failures.append(f"Route paths test failed: {e}")

    # Test 3: RunAnalysisRequest validation
    total_tests += 1
    try:
        request = RunAnalysisRequest(n_synths=100, n_executions=50, sigma=0.1)
        if request.n_synths != 100:
            all_validation_failures.append("RunAnalysisRequest n_synths mismatch")
        else:
            print("Test 3 PASSED: RunAnalysisRequest model works")
    except Exception as e:
        all_validation_failures.append(f"RunAnalysisRequest validation failed: {e}")

    # Test 4: RunAnalysisRequest defaults
    total_tests += 1
    try:
        request = RunAnalysisRequest()
        if request.n_synths != 500:
            all_validation_failures.append(
                f"RunAnalysisRequest default n_synths mismatch: {request.n_synths}"
            )
        elif request.n_executions != 100:
            all_validation_failures.append(
                f"RunAnalysisRequest default n_executions mismatch: {request.n_executions}"
            )
        else:
            print("Test 4 PASSED: RunAnalysisRequest defaults work")
    except Exception as e:
        all_validation_failures.append(f"RunAnalysisRequest defaults failed: {e}")

    # Test 5: Config conversion
    total_tests += 1
    try:
        config = AnalysisConfig(n_synths=200, n_executions=75, sigma=0.08, seed=42)
        schema = _convert_config_to_schema(config)
        if schema.n_synths != 200:
            all_validation_failures.append("Config to schema n_synths mismatch")
        elif schema.seed != 42:
            all_validation_failures.append("Config to schema seed mismatch")
        else:
            print("Test 5 PASSED: Config conversion works")
    except Exception as e:
        all_validation_failures.append(f"Config conversion failed: {e}")

    # Test 6: Outcomes conversion
    total_tests += 1
    try:
        outcomes = AggregatedOutcomes(
            did_not_try_rate=0.2,
            failed_rate=0.3,
            success_rate=0.5,
        )
        schema = _convert_outcomes_to_schema(outcomes)
        if schema.success_rate != 0.5:
            all_validation_failures.append("Outcomes to schema success_rate mismatch")
        else:
            print("Test 6 PASSED: Outcomes conversion works")
    except Exception as e:
        all_validation_failures.append(f"Outcomes conversion failed: {e}")

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
