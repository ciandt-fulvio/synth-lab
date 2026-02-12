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
    SynthAttributesSchema,
    SynthOutcomeResponse,
)
from synth_lab.domain.entities.analysis_cache import CacheKeys
from synth_lab.domain.entities.analysis_run import AggregatedOutcomes, AnalysisConfig
from synth_lab.domain.entities.chart_data import (
    FailureHeatmapChart,
    OutcomeDistributionChart,
    ScatterCorrelationChart,
)
from synth_lab.domain.entities.explainability import ShapExplanation, ShapSummary
from synth_lab.domain.entities.outlier_result import ExtremeCasesTable, OutlierResult
from synth_lab.infrastructure.database_v2 import get_session
from synth_lab.models.pagination import PaginationParams
from synth_lab.repositories.analysis_outcome_repository import AnalysisOutcomeRepository
from synth_lab.services.analysis.analysis_cache_service import AnalysisCacheService
from synth_lab.services.analysis.analysis_execution_service import AnalysisExecutionService
from synth_lab.services.analysis.analysis_service import AnalysisService
from synth_lab.services.experiment_service import ExperimentService
from synth_lab.services.simulation.chart_data_service import ChartDataService
from synth_lab.services.simulation.explainability_service import ExplainabilityService
from synth_lab.services.simulation.outlier_service import OutlierService

router = APIRouter()


# =============================================================================
# Helper Functions
# =============================================================================


def get_analysis_service() -> AnalysisService:
    """Get analysis service instance."""
    return AnalysisService()


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


def get_cache_service() -> AnalysisCacheService:
    """Get analysis cache service instance."""
    return AnalysisCacheService()


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


def _convert_outcomes_to_schema(outcomes: AggregatedOutcomes) -> AggregatedOutcomesSchema:
    """Convert domain entity to API schema."""
    return AggregatedOutcomesSchema(
        adopted_rate=outcomes.adopted_rate, not_adopted_rate=outcomes.not_adopted_rate
    )


def _fetch_synth_names(synth_ids: list[str]) -> dict[str, str]:
    """Fetch synth names via lightweight SQL query.

    Uses direct SQL instead of SynthRepository.get_by_id() to avoid
    Pydantic validation errors on older synths with missing fields.
    """
    from sqlalchemy import select

    from synth_lab.models.orm.synth import Synth as SynthORM

    if not synth_ids:
        return {}

    names: dict[str, str] = {}
    with get_session() as session:
        stmt = select(SynthORM.id, SynthORM.nome).where(SynthORM.id.in_(synth_ids))
        for row in session.execute(stmt).all():
            names[row[0]] = row[1]
    return names


# =============================================================================
# Request Models
# =============================================================================


class RunAnalysisRequest(BaseModel):
    """Request model for running analysis."""

    n_synths: int = Field(default=500, ge=10, le=10000, description="Number of synths to simulate.")
    n_executions: int = Field(
        default=100, ge=10, le=1000, description="Number of Monte Carlo executions per synth."
    )
    sigma: float = Field(default=0.05, ge=0.0, le=0.5, description="Standard deviation for noise.")
    seed: int | None = Field(default=None, description="Random seed for reproducibility.")


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
    experiment_id: str, request: RunAnalysisRequest | None = None
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis execution failed: {str(e)}",
        )


@router.delete("/{experiment_id}/analysis", status_code=status.HTTP_204_NO_CONTENT)
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


@router.get("/{experiment_id}/analysis/outcomes", response_model=PaginatedSynthOutcomes)
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
    from synth_lab.repositories.synth_outcome_repository import SynthOutcomeRepository

    with get_session() as session:
        outcome_repo = SynthOutcomeRepository(session=session)
        result = outcome_repo.list_by_analysis_id(
            analysis_id=analysis.id, params=PaginationParams(limit=limit, offset=offset)
        )

    # Convert to response
    outcomes = []
    for outcome in result.data:
        # Convert SimulationAttributes to schema dictionaries
        observables_dict = {}
        latent_traits_dict = {}
        if outcome.synth_attributes:
            if outcome.synth_attributes.observables is not None:
                observables_dict = outcome.synth_attributes.observables.model_dump()
            if outcome.synth_attributes.latent_traits is not None:
                latent_traits_dict = outcome.synth_attributes.latent_traits.model_dump()

        attrs = SynthAttributesSchema(
            observables=observables_dict, latent_traits=latent_traits_dict
        )
        outcomes.append(
            SynthOutcomeResponse(
                id=outcome.id,
                synth_id=outcome.synth_id,
                adopted_rate=outcome.adopted_rate,
                not_adopted_rate=outcome.not_adopted_rate,
                synth_attributes=attrs,
            )
        )

    return PaginatedSynthOutcomes(data=outcomes, pagination=result.pagination)


# =============================================================================
# Interview Suggestions Endpoints
# =============================================================================


@router.get(
    "/{experiment_id}/analysis/interview-suggestions", response_model=InterviewSuggestionsResponse
)
async def get_interview_suggestions(
    experiment_id: str,
    max_suggestions: int = Query(
        default=5, ge=1, le=20, description="Maximum number of suggestions"
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


@router.get("/{experiment_id}/analysis/insights", response_model=InsightsResponse)
async def get_insights(experiment_id: str) -> InsightsResponse:
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
    return InsightsResponse(insights=[], generated_at=datetime.now(timezone.utc))


@router.post("/{experiment_id}/analysis/insights", response_model=InsightsResponse)
async def generate_insights(experiment_id: str) -> InsightsResponse:
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
    "/{experiment_id}/analysis/charts/distribution", response_model=OutcomeDistributionChart
)
async def get_distribution_chart(
    experiment_id: str,
    sort_by: str = Query(
        default="adopted_rate", description="Field to sort by: adopted_rate, not_adopted_rate"
    ),
    order: str = Query(default="desc", description="Sort order: asc or desc"),
    limit: int = Query(default=50, ge=1, le=1000, description="Maximum results"),
) -> OutcomeDistributionChart:
    """
    Get outcome distribution chart data for an analysis.

    Shows distribution of outcomes across synths.
    Uses cache for default parameters.
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
            detail=f"Analysis must be completed (status: {analysis.status})",
        )

    # Check cache for default parameters
    is_default = sort_by == "adopted_rate" and order == "desc" and limit == 50
    if is_default:
        cache_service = get_cache_service()
        cached = cache_service.get_cached(analysis.id, CacheKeys.DISTRIBUTION)
        if cached:
            return OutcomeDistributionChart.model_validate(cached)

    # Compute on-demand
    chart_service = get_chart_data_service()
    outcome_repo = get_outcome_repository()

    outcomes, _ = outcome_repo.get_outcomes(analysis.id)
    if not outcomes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No outcomes found for this analysis"
        )

    return chart_service.get_outcome_distribution(
        simulation_id=analysis.id, outcomes=outcomes, sort_by=sort_by, order=order, limit=limit
    )


@router.get("/{experiment_id}/analysis/charts/failure-heatmap", response_model=FailureHeatmapChart)
async def get_failure_heatmap_chart(
    experiment_id: str,
    x_axis: str = Query(default="digital_literacy", description="X-axis attribute"),
    y_axis: str = Query(default="trust_mean", description="Y-axis attribute"),
    bins: int = Query(default=5, ge=2, le=20, description="Number of bins per axis"),
    metric: str = Query(
        default="not_adopted_rate", description="Metric to display: adopted_rate, not_adopted_rate"
    ),
) -> FailureHeatmapChart:
    """
    Get failure heatmap data for an analysis.

    Creates a 2D binned heatmap showing metric values across two attributes.
    Uses cache for default parameters.
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
            detail=f"Analysis must be completed (status: {analysis.status})",
        )

    valid_metrics = ["adopted_rate", "not_adopted_rate"]
    if metric not in valid_metrics:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid metric: {metric}. Must be one of {valid_metrics}",
        )

    # Check cache for default parameters
    is_default = (
        x_axis == "digital_literacy"
        and y_axis == "trust_mean"
        and bins == 5
        and metric == "not_adopted_rate"
    )
    if is_default:
        cache_service = get_cache_service()
        cached = cache_service.get_cached(analysis.id, CacheKeys.HEATMAP)
        if cached:
            return FailureHeatmapChart.model_validate(cached)

    # Compute on-demand
    chart_service = get_chart_data_service()
    outcome_repo = get_outcome_repository()

    outcomes, _ = outcome_repo.get_outcomes(analysis.id)
    if not outcomes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No outcomes found for this analysis"
        )

    return chart_service.get_failure_heatmap(
        simulation_id=analysis.id,
        outcomes=outcomes,
        x_axis=x_axis,
        y_axis=y_axis,
        bins=bins,
        metric=metric,
    )


@router.get("/{experiment_id}/analysis/charts/scatter", response_model=ScatterCorrelationChart)
async def get_scatter_correlation_chart(
    experiment_id: str,
    x_axis: str = Query(default="capability_mean", description="X-axis attribute"),
    y_axis: str = Query(default="adopted_rate", description="Y-axis attribute"),
    show_trendline: bool = Query(default=True, description="Include trend line"),
) -> ScatterCorrelationChart:
    """
    Get scatter correlation chart data for an analysis.

    Shows correlation between two attributes with optional trend line.
    Uses cache for default parameters.
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
            detail=f"Analysis must be completed (status: {analysis.status})",
        )

    # Check cache for default parameters
    is_default = x_axis == "capability_mean" and y_axis == "adopted_rate"
    if is_default:
        cache_service = get_cache_service()
        cached = cache_service.get_cached(analysis.id, CacheKeys.SCATTER)
        if cached:
            return ScatterCorrelationChart.model_validate(cached)

    # Compute on-demand
    chart_service = get_chart_data_service()
    outcome_repo = get_outcome_repository()

    outcomes, _ = outcome_repo.get_outcomes(analysis.id)
    if not outcomes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No outcomes found for this analysis"
        )

    return chart_service.get_scatter_correlation(
        simulation_id=analysis.id,
        outcomes=outcomes,
        x_axis=x_axis,
        y_axis=y_axis,
        show_trendline=show_trendline,
    )


# =============================================================================
# Phase 3: Edge Cases Endpoints
# =============================================================================


def get_outlier_service() -> OutlierService:
    """Get outlier service instance."""
    return OutlierService()


def get_explainability_service() -> ExplainabilityService:
    """Get explainability service instance."""
    return ExplainabilityService()


@router.get("/{experiment_id}/analysis/extreme-cases", response_model=ExtremeCasesTable)
async def get_analysis_extreme_cases(
    experiment_id: str, n_per_category: int = Query(default=10, ge=1, le=50)
) -> ExtremeCasesTable:
    """Get extreme cases for qualitative research."""
    service = get_analysis_service()
    outlier_service = get_outlier_service()
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
    if not outcomes or len(outcomes) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Extreme cases requires at least 10 synths",
        )

    result = outlier_service.get_extreme_cases(
        simulation_id=analysis.id, outcomes=outcomes, n_per_category=n_per_category
    )

    # Collect all synth IDs to fetch names
    all_synth_ids = set()
    for synth in result.worst_failures:
        all_synth_ids.add(synth.synth_id)
    for synth in result.best_successes:
        all_synth_ids.add(synth.synth_id)
    for synth in result.unexpected_cases:
        all_synth_ids.add(synth.synth_id)

    # Fetch synth names via lightweight SQL (avoids full model validation)
    synth_names = _fetch_synth_names(list(all_synth_ids))

    # Enrich extreme synths with names
    for synth in result.worst_failures:
        synth.synth_name = synth_names.get(synth.synth_id, "")
    for synth in result.best_successes:
        synth.synth_name = synth_names.get(synth.synth_id, "")
    for synth in result.unexpected_cases:
        synth.synth_name = synth_names.get(synth.synth_id, "")

    return result


@router.get("/{experiment_id}/analysis/outliers", response_model=OutlierResult)
async def get_analysis_outliers(
    experiment_id: str, contamination: float = Query(default=0.1, ge=0.01, le=0.5)
) -> OutlierResult:
    """Get statistical outliers using Isolation Forest."""
    service = get_analysis_service()
    outlier_service = get_outlier_service()
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
    if not outcomes or len(outcomes) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Outlier detection requires at least 10 synths",
        )

    result = outlier_service.detect_outliers(
        simulation_id=analysis.id, outcomes=outcomes, contamination=contamination
    )

    # Enrich outlier synths with names
    outlier_ids = [o.synth_id for o in result.outliers]
    synth_names = _fetch_synth_names(outlier_ids)
    for outlier in result.outliers:
        outlier.synth_name = synth_names.get(outlier.synth_id, "")

    return result


# =============================================================================
# Phase 4: Explainability Endpoints (SHAP)
# =============================================================================


@router.get("/{experiment_id}/analysis/shap/summary", response_model=ShapSummary)
async def get_analysis_shap_summary(experiment_id: str) -> ShapSummary:
    """Get global SHAP summary showing feature importance."""
    service = get_analysis_service()
    explain_service = get_explainability_service()
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
    if not outcomes or len(outcomes) < 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SHAP summary requires at least 20 synths",
        )

    return explain_service.get_shap_summary(simulation_id=analysis.id, outcomes=outcomes)


@router.get("/{experiment_id}/analysis/shap/{synth_id}", response_model=ShapExplanation)
async def get_analysis_shap_explanation(experiment_id: str, synth_id: str) -> ShapExplanation:
    """Get SHAP explanation for a specific synth."""
    service = get_analysis_service()
    explain_service = get_explainability_service()
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
    if not outcomes or len(outcomes) < 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SHAP explanation requires at least 20 synths",
        )

    # Find the target synth
    target_synth = next((o for o in outcomes if o.synth_id == synth_id), None)
    if target_synth is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Synth {synth_id} not found in analysis"
        )

    return explain_service.get_shap_explanation(
        simulation_id=analysis.id, outcomes=outcomes, synth_id=synth_id
    )


# =============================================================================
# Insights Endpoints (Feature 023 - under construction)
# =============================================================================

# NOTE: These endpoints are temporarily commented out during feature 023 migration.
# They will be replaced with new insight endpoints in Phase 4 of the migration.

# NOTE: Insight endpoints moved to routers/insights.py in feature 023
# Legacy endpoints removed to avoid duplication


# =============================================================================
# Mechanism-Based Segment Explanation (038-mechanism-based-simulation)
# =============================================================================


class SegmentExplanationResponse(BaseModel):
    """Response for segment explanation via mechanism×sensitivity interactions."""

    segment_size: int = Field(description="Number of synths in the segment.")
    segment_avg_adopted: float = Field(description="Average adopted rate of the segment.")
    population_avg_adopted: float = Field(description="Average adopted rate of the population.")
    top_differentiating_factors: list[dict] = Field(
        default_factory=list,
        description="Top factors differentiating this segment from population.",
    )
    explanation_text: str = Field(description="Human-readable explanation.")


class ExplainSegmentRequestBody(BaseModel):
    """Request body for explaining segment behavior."""

    synth_ids: list[str] = Field(
        min_length=1, description="List of synth IDs that define the segment."
    )
    compare_to_population: bool = Field(
        default=True, description="Whether to compare segment to full population."
    )


@router.post("/{experiment_id}/analysis/explain-segment", response_model=SegmentExplanationResponse)
async def explain_segment(
    experiment_id: str,
    request: ExplainSegmentRequestBody,
) -> SegmentExplanationResponse:
    """
    Explain why a segment of synths behaves differently via mechanism×sensitivity interactions.

    Returns top differentiating factors and human-readable explanation text.

    Reference: specs/038-mechanism-based-simulation/spec.md
    """
    from synth_lab.services.analysis.explanation_service import (
        explain_segment as explain_segment_service,
    )

    service = get_analysis_service()
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
            detail="No outcomes available for this analysis",
        )

    # Convert to list of dicts for the service
    outcomes_dicts = [o.model_dump() for o in outcomes]

    result = explain_segment_service(
        synth_outcomes=outcomes_dicts,
        segment_synth_ids=request.synth_ids,
        compare_to_population=request.compare_to_population,
    )

    # Convert dataclass to response
    return SegmentExplanationResponse(
        segment_size=result.segment_size,
        segment_avg_adopted=result.segment_avg_adopted,
        population_avg_adopted=result.population_avg_adopted,
        top_differentiating_factors=[
            {
                "interaction": {
                    "mechanism": f.interaction.mechanism,
                    "sensitivity": f.interaction.sensitivity,
                    "product": f.interaction.product,
                },
                "segment_avg": f.segment_avg,
                "population_avg": f.population_avg,
                "delta": f.delta,
            }
            for f in result.top_differentiating_factors
        ],
        explanation_text=result.explanation_text,
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
            all_validation_failures.append(f"Expected at least 5 routes, got {len(router.routes)}")
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
        outcomes = AggregatedOutcomes(adopted_rate=0.5, not_adopted_rate=0.5)
        schema = _convert_outcomes_to_schema(outcomes)
        if schema.adopted_rate != 0.5:
            all_validation_failures.append("Outcomes to schema adopted_rate mismatch")
        else:
            print("Test 6 PASSED: Outcomes conversion works")
    except Exception as e:
        all_validation_failures.append(f"Outcomes conversion failed: {e}")

    # Final result
    print()
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
