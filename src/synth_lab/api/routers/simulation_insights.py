"""
Simulation Insights API router for causal simulation system.

REST endpoints for retrieving insights with full traceability.

References:
    - Spec: specs/035-causal-simulation/spec.md
    - Data model: specs/035-causal-simulation/data-model.md
"""

from fastapi import APIRouter, HTTPException, status, Depends
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from synth_lab.api.schemas.simulation_insight import (
    EvidenceResponse,
    PercentileDistributionSchema,
    VarianceContributionSchema,
    FailureModeSchema,
    VariableConditionSchema,
    OutcomeThresholdSchema,
    BehavioralClusterSchema,
    ClusterOutcomeStatsSchema,
)
from synth_lab.infrastructure.database_v2 import get_db_session
from synth_lab.repositories.causal_dag_repository import CausalDAGRepository
from synth_lab.repositories.hypothesis_repository import HypothesisRepository
from synth_lab.repositories.simulation_insight_repository import (
    SimulationInsightRepository,
)
from synth_lab.repositories.simulation_repository import SimulationRepository
from synth_lab.services.simulation.evidence_calculator_service import (
    EvidenceCalculatorService,
)
from synth_lab.services.simulation.simulation_engine_service import (
    SimulationEngineService,
)

router = APIRouter(prefix="/simulations", tags=["insights"])


class InsightResponse(BaseModel):
    """Response schema for simulation insight."""

    id: str = Field(..., description="Insight ID")

    simulation_id: str = Field(..., description="Parent simulation ID")

    insight_type: str = Field(
        ...,
        description="Type: key_driver, failure_mode, cluster_finding, recommendation",
    )

    title: str = Field(..., description="Brief summary")

    description: str = Field(..., description="Detailed explanation")

    evidence_references: dict = Field(
        default_factory=dict,
        description="Links to statistical evidence",
    )

    recommended_actions: list[dict] = Field(
        default_factory=list,
        description="Actionable next steps",
    )

    created_at: str = Field(..., description="Creation timestamp")


class InsightTraceResponse(BaseModel):
    """Response schema for insight traceability."""

    insight_id: str = Field(..., description="Insight ID")

    simulation_id: str = Field(..., description="Parent simulation ID")

    evidence_references: dict = Field(
        ..., description="Statistical evidence links"
    )

    statistical_support: dict = Field(
        default_factory=dict,
        description="Correlation, variance explained, sample size",
    )

    affected_worlds: list[str] = Field(
        default_factory=list,
        description="World IDs supporting this insight",
    )


# =============================================================================
# Endpoints
# =============================================================================


@router.get(
    "/{simulation_id}/evidence",
    response_model=EvidenceResponse,
    summary="Get simulation evidence",
    description="Retrieve statistical evidence including percentiles, sensitivity, failure modes, and clusters",
)
async def get_simulation_evidence(
    simulation_id: str,
    db: Session = Depends(get_db_session),
) -> EvidenceResponse:
    """
    Get simulation evidence with all statistical analysis.

    This endpoint returns:
    - Percentile distributions (p5, p25, p50, p75, p95)
    - Variance explained (sensitivity analysis)
    - Correlation matrix
    - Failure modes
    - Behavioral clusters

    Args:
        simulation_id: Simulation ID
        db: Database session

    Returns:
        Complete evidence with failure modes and clusters

    Raises:
        HTTPException: If simulation not found or evidence not available
    """
    # Initialize repositories
    sim_repo = SimulationRepository(session=db)
    dag_repo = CausalDAGRepository(session=db)
    hyp_repo = HypothesisRepository(session=db)

    # Get simulation
    simulation = sim_repo.get(simulation_id)
    if simulation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation {simulation_id} not found",
        )

    # Get DAG and hypotheses
    dag = dag_repo.get_by_simulation_id(simulation_id)
    if dag is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No DAG found for simulation",
        )

    hypotheses = hyp_repo.get_by_simulation_id(simulation_id)
    if not hypotheses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hypotheses found for simulation",
        )

    # Re-run simulation to get evidence (in production, cache this)
    logger.info(f"Computing evidence for simulation {simulation_id}")

    try:
        # Run simulation
        engine = SimulationEngineService()
        worlds = engine.run(
            simulation_id=simulation_id,
            dag=dag,
            hypotheses=hypotheses,
            n_worlds=simulation.n_worlds or 500,
            random_seed=simulation.random_seed or 42,
        )

        # Calculate evidence
        evidence_service = EvidenceCalculatorService()
        evidence, failure_modes, clusters = evidence_service.aggregate(
            simulation_id, dag, worlds
        )

        # Convert to response schema
        outcome_distributions = {
            name: PercentileDistributionSchema(
                p5=dist.p5,
                p25=dist.p25,
                p50=dist.p50,
                p75=dist.p75,
                p95=dist.p95,
                mean=dist.mean,
                std=dist.std,
            )
            for name, dist in evidence.outcome_distributions.items()
        }

        variance_explained = [
            VarianceContributionSchema(
                variable_name=vc.variable_name,
                variance_explained=vc.variance_explained,
                rank=vc.rank,
            )
            for vc in evidence.variance_explained
        ]

        failure_mode_schemas = [
            FailureModeSchema(
                id=fm.id,
                evidence_id=fm.evidence_id,
                pattern={
                    name: VariableConditionSchema(
                        operator=cond.operator,
                        value=cond.value,
                    )
                    for name, cond in fm.pattern.items()
                },
                outcome_threshold={
                    name: OutcomeThresholdSchema(
                        operator=thresh.operator,
                        value=thresh.value,
                    )
                    for name, thresh in fm.outcome_threshold.items()
                },
                frequency=fm.frequency,
                severity=fm.severity,
                description=fm.description,
                created_at=fm.created_at.isoformat(),
            )
            for fm in failure_modes
        ]

        cluster_schemas = [
            BehavioralClusterSchema(
                id=cluster.id,
                evidence_id=cluster.evidence_id,
                cluster_number=cluster.cluster_number,
                world_ids=cluster.world_ids,
                centroid=cluster.centroid,
                outcome_stats={
                    name: ClusterOutcomeStatsSchema(
                        mean=stats.mean,
                        std=stats.std,
                        p50=stats.p50,
                    )
                    for name, stats in cluster.outcome_stats.items()
                },
                size=cluster.size,
                percentage=cluster.percentage,
                label=cluster.label,
                created_at=cluster.created_at.isoformat(),
            )
            for cluster in clusters
        ]

        return EvidenceResponse(
            id=evidence.id,
            simulation_id=simulation_id,
            outcome_distributions=outcome_distributions,
            variance_explained=variance_explained,
            correlation_matrix=evidence.correlation_matrix,
            failure_modes=failure_mode_schemas,
            clusters=cluster_schemas,
            created_at=evidence.created_at.isoformat(),
        )

    except Exception as e:
        logger.error(f"Evidence calculation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute evidence: {str(e)}",
        )


@router.get(
    "/{simulation_id}/insights",
    response_model=list[InsightResponse],
    summary="Get simulation insights",
    description="Retrieve all insights for a simulation with recommendations",
)
async def get_simulation_insights(
    simulation_id: str,
    db: Session = Depends(get_db_session),
) -> list[InsightResponse]:
    """
    Get all insights for a simulation.

    Args:
        simulation_id: Simulation ID
        db: Database session

    Returns:
        List of insights with evidence and recommendations

    Raises:
        HTTPException: If simulation not found
    """
    insight_repo = SimulationInsightRepository(session=db)
    insights = insight_repo.get_by_simulation_id(simulation_id)

    if not insights:
        # Return empty list if no insights found (not an error)
        logger.info(f"No insights found for simulation {simulation_id}")
        return []

    return [
        InsightResponse(
            id=insight["id"],
            simulation_id=insight["simulation_id"],
            insight_type=insight["insight_type"],
            title=insight["title"],
            description=insight["description"],
            evidence_references=insight["evidence_references"],
            recommended_actions=insight["recommended_actions"],
            created_at=insight["created_at"],
        )
        for insight in insights
    ]


@router.get(
    "/insights/{insight_id}/trace",
    response_model=InsightTraceResponse,
    summary="Get insight traceability",
    description="Retrieve full traceability for an insight back to statistical evidence",
)
async def get_insight_trace(
    insight_id: str,
    db: Session = Depends(get_db_session),
) -> InsightTraceResponse:
    """
    Get insight traceability details.

    This endpoint provides full audit trail showing:
    - Statistical evidence (variance explained, correlations)
    - Affected world IDs
    - Failure modes and clusters referenced

    Args:
        insight_id: Insight ID
        db: Database session

    Returns:
        Traceability details

    Raises:
        HTTPException: If insight not found
    """
    insight_repo = SimulationInsightRepository(session=db)
    insight = insight_repo.get(insight_id)

    if insight is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Insight {insight_id} not found",
        )

    # Extract statistical support if available
    statistical_support = {}
    evidence_refs = insight.get("evidence_references", {})

    # Build affected worlds list from evidence
    affected_worlds = evidence_refs.get("affected_world_ids", [])

    return InsightTraceResponse(
        insight_id=insight["id"],
        simulation_id=insight["simulation_id"],
        evidence_references=evidence_refs,
        statistical_support=statistical_support,
        affected_worlds=affected_worlds,
    )
