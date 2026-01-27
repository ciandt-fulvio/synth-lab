"""
Pydantic schemas for simulation insights, evidence, failure modes, and clusters.

Provides API request/response schemas for the simulation evidence endpoints.

References:
    - Spec: specs/035-causal-simulation/spec.md
    - Entities: domain/entities/simulated_world.py
"""

from pydantic import BaseModel, Field


class PercentileDistributionSchema(BaseModel):
    """Response schema for percentile distribution."""

    p5: float = Field(..., description="5th percentile")
    p25: float = Field(..., description="25th percentile")
    p50: float = Field(..., description="50th percentile (median)")
    p75: float = Field(..., description="75th percentile")
    p95: float = Field(..., description="95th percentile")
    mean: float = Field(..., description="Mean value")
    std: float = Field(..., description="Standard deviation")


class VarianceContributionSchema(BaseModel):
    """Response schema for variance contribution (sensitivity analysis)."""

    variable_name: str = Field(..., description="Name of the variable")
    variance_explained: float = Field(
        ..., ge=0, le=1, description="Proportion of variance explained (0-1)"
    )
    rank: int = Field(..., ge=1, description="Importance rank (1 = most)")


class VariableConditionSchema(BaseModel):
    """Response schema for variable condition in failure mode pattern."""

    operator: str = Field(..., description="Comparison operator (<, <=, >, >=, ==)")
    value: float = Field(..., description="Threshold value")


class OutcomeThresholdSchema(BaseModel):
    """Response schema for outcome threshold in failure mode."""

    operator: str = Field(..., description="Comparison operator")
    value: float = Field(..., description="Threshold value")


class FailureModeSchema(BaseModel):
    """Response schema for failure mode."""

    id: str = Field(..., description="Failure mode ID")
    evidence_id: str = Field(..., description="Parent evidence ID")
    pattern: dict[str, VariableConditionSchema] = Field(
        ..., description="Variable conditions (variable_name: condition)"
    )
    outcome_threshold: dict[str, OutcomeThresholdSchema] = Field(
        ..., description="Outcome thresholds (outcome_name: threshold)"
    )
    frequency: float = Field(
        ..., ge=0, le=1, description="Percentage of worlds matching pattern (0-1)"
    )
    severity: str = Field(..., description="Impact severity level (low, medium, high, critical)")
    description: str = Field(..., description="Natural language description")
    created_at: str = Field(..., description="Creation timestamp")


class ClusterOutcomeStatsSchema(BaseModel):
    """Response schema for cluster outcome statistics."""

    mean: float = Field(..., description="Mean value")
    std: float = Field(..., description="Standard deviation")
    p50: float = Field(..., description="Median value")


class BehavioralClusterSchema(BaseModel):
    """Response schema for behavioral cluster."""

    id: str = Field(..., description="Cluster ID")
    evidence_id: str = Field(..., description="Parent evidence ID")
    cluster_number: int = Field(..., ge=1, description="Sequential cluster number")
    world_ids: list[str] = Field(..., description="World IDs in this cluster")
    centroid: dict[str, float] = Field(
        ..., description="Representative variable values (variable_name: mean)"
    )
    outcome_stats: dict[str, ClusterOutcomeStatsSchema] = Field(
        ..., description="Outcome stats for cluster"
    )
    size: int = Field(..., ge=1, description="Number of worlds in cluster")
    percentage: float = Field(..., ge=0, le=1, description="Percentage of total worlds")
    label: str = Field(..., description="Human-readable cluster label")
    created_at: str = Field(..., description="Creation timestamp")


class EvidenceResponse(BaseModel):
    """Response schema for simulation evidence."""

    id: str = Field(..., description="Evidence ID")
    simulation_id: str = Field(..., description="Parent simulation ID")
    outcome_distributions: dict[str, PercentileDistributionSchema] = Field(
        ..., description="Percentile distributions for outcomes"
    )
    variance_explained: list[VarianceContributionSchema] = Field(
        ..., description="Sensitivity analysis results"
    )
    correlation_matrix: dict[str, dict[str, float]] = Field(
        ..., description="Correlations between variables and outcomes"
    )
    failure_modes: list[FailureModeSchema] = Field(
        ..., description="Detected failure patterns"
    )
    clusters: list[BehavioralClusterSchema] = Field(
        ..., description="Behavioral clusters"
    )
    created_at: str = Field(..., description="Creation timestamp")


class InsightSchema(BaseModel):
    """Response schema for a single insight."""

    id: str = Field(..., description="Insight ID")
    simulation_id: str = Field(..., description="Parent simulation ID")
    insight_type: str = Field(
        ..., description="Type: key_driver, failure_mode, cluster_finding, recommendation"
    )
    title: str = Field(..., description="Brief summary")
    description: str = Field(..., description="Detailed explanation")
    evidence_references: dict = Field(
        default_factory=dict, description="Links to statistical evidence"
    )
    recommended_actions: list[dict] = Field(
        default_factory=list, description="Actionable next steps"
    )
    confidence: float = Field(
        default=0.0, ge=0, le=1, description="Confidence score (0-1)"
    )
    created_at: str = Field(..., description="Creation timestamp")


class InsightTraceSchema(BaseModel):
    """Response schema for insight traceability."""

    insight_id: str = Field(..., description="Insight ID")
    simulation_id: str = Field(..., description="Parent simulation ID")
    evidence_references: dict = Field(..., description="Statistical evidence links")
    statistical_support: dict = Field(
        default_factory=dict,
        description="Correlation, variance explained, sample size",
    )
    affected_worlds: list[str] = Field(
        default_factory=list, description="World IDs supporting this insight"
    )
