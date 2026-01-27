"""
SimulatedWorld and Evidence entities for causal simulation system.

Represents individual simulation executions, aggregated evidence, failure modes,
and behavioral clusters for comprehensive uncertainty analysis.

References:
    - Spec: specs/035-causal-simulation/spec.md
    - Data model: specs/035-causal-simulation/data-model.md
    - NumPy percentiles: https://numpy.org/doc/stable/reference/generated/numpy.percentile.html
    - scikit-learn clustering: https://scikit-learn.org/stable/modules/clustering.html
"""

import secrets
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


def generate_world_id() -> str:
    """
    Generate a world ID with world_ prefix and 8-char hex suffix.

    Returns:
        str: ID in format world_[a-f0-9]{8}
    """
    return f"world_{secrets.token_hex(4)}"


def generate_evidence_id() -> str:
    """
    Generate an evidence ID with evd_ prefix and 8-char hex suffix.

    Returns:
        str: ID in format evd_[a-f0-9]{8}
    """
    return f"evd_{secrets.token_hex(4)}"


def generate_failure_mode_id() -> str:
    """
    Generate a failure mode ID with fm_ prefix and 8-char hex suffix.

    Returns:
        str: ID in format fm_[a-f0-9]{8}
    """
    return f"fm_{secrets.token_hex(4)}"


def generate_cluster_id() -> str:
    """
    Generate a cluster ID with clust_ prefix and 8-char hex suffix.

    Returns:
        str: ID in format clust_[a-f0-9]{8}
    """
    return f"clust_{secrets.token_hex(4)}"


class SeverityLevel(str, Enum):
    """Severity level for failure modes."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class OutcomeStats(BaseModel):
    """
    Statistical summary for an outcome variable.

    Attributes:
        mean: Mean value
        std: Standard deviation
        p5: 5th percentile
        p50: 50th percentile (median)
        p95: 95th percentile
    """

    mean: float = Field(..., description="Mean value")
    std: float = Field(..., description="Standard deviation")
    p5: float = Field(..., description="5th percentile")
    p50: float = Field(..., description="50th percentile (median)")
    p95: float = Field(..., description="95th percentile")


class SimulatedWorld(BaseModel):
    """
    Single execution of simulation with specific parameter draws.

    Attributes:
        id: Unique identifier (world_[a-f0-9]{8})
        simulation_id: Parent simulation ID
        world_number: Sequential world number (1-500)
        world_parameters: Sampled world-level variable values (JSONB)
        aggregated_outcomes: Aggregated outcomes across population (JSONB)
        random_seed: Seed for this world's randomness
        created_at: ISO 8601 timestamp of creation
    """

    id: str = Field(
        default_factory=generate_world_id,
        pattern=r"^world_[a-f0-9]{8}$",
        description="Unique world ID",
    )

    simulation_id: str = Field(
        ...,
        pattern=r"^sim_[a-f0-9]{8}$",
        description="Parent simulation ID",
    )

    world_number: int = Field(
        ..., ge=1, description="Sequential world number (1-500)"
    )

    world_parameters: dict[str, float] = Field(
        default_factory=dict,
        description="Sampled world-level variable values (variable_id: value)",
    )

    aggregated_outcomes: dict[str, OutcomeStats] = Field(
        default_factory=dict,
        description="Aggregated outcomes across population (outcome_name: stats)",
    )

    random_seed: int = Field(
        ..., description="Seed for this world's randomness"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp (UTC)",
    )


class PercentileDistribution(BaseModel):
    """
    Percentile distribution for an outcome.

    Attributes:
        p5: 5th percentile
        p25: 25th percentile
        p50: 50th percentile (median)
        p75: 75th percentile
        p95: 95th percentile
        mean: Mean value
        std: Standard deviation
    """

    p5: float = Field(..., description="5th percentile")
    p25: float = Field(..., description="25th percentile")
    p50: float = Field(..., description="50th percentile (median)")
    p75: float = Field(..., description="75th percentile")
    p95: float = Field(..., description="95th percentile")
    mean: float = Field(..., description="Mean value")
    std: float = Field(..., description="Standard deviation")


class VarianceContribution(BaseModel):
    """
    Variance contribution for a variable (sensitivity analysis).

    Attributes:
        variable_name: Name of the variable
        variance_explained: Proportion of variance explained (0-1)
        rank: Importance rank (1 = most important)
    """

    variable_name: str = Field(..., description="Name of the variable")

    variance_explained: float = Field(
        ..., ge=0, le=1, description="Proportion of variance explained (0-1)"
    )

    rank: int = Field(..., ge=1, description="Importance rank (1 = most)")


class Evidence(BaseModel):
    """
    Aggregated statistics from all simulated worlds.

    Attributes:
        id: Unique identifier (evd_[a-f0-9]{8})
        simulation_id: Parent simulation ID (one-to-one)
        outcome_distributions: Percentile distributions for outcomes (JSONB)
        variance_explained: Sensitivity analysis results (JSONB)
        correlation_matrix: Correlations between variables and outcomes (JSONB)
        created_at: ISO 8601 timestamp of creation
    """

    id: str = Field(
        default_factory=generate_evidence_id,
        pattern=r"^evd_[a-f0-9]{8}$",
        description="Unique evidence ID",
    )

    simulation_id: str = Field(
        ...,
        pattern=r"^sim_[a-f0-9]{8}$",
        description="Parent simulation ID (one-to-one)",
    )

    outcome_distributions: dict[str, PercentileDistribution] = Field(
        default_factory=dict,
        description="Percentile distributions for outcomes (outcome_name: distribution)",
    )

    variance_explained: list[VarianceContribution] = Field(
        default_factory=list, description="Sensitivity analysis results"
    )

    correlation_matrix: dict[str, dict[str, float]] = Field(
        default_factory=dict,
        description="Correlations: variable_name → {outcome_name: coefficient}",
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp (UTC)",
    )


class VariableCondition(BaseModel):
    """
    Condition on a variable (for failure mode patterns).

    Attributes:
        operator: Comparison operator (<, <=, >, >=, ==)
        value: Threshold value
    """

    operator: str = Field(
        ..., pattern=r"^(<|<=|>|>=|==)$", description="Comparison operator"
    )

    value: float = Field(..., description="Threshold value")


class OutcomeThreshold(BaseModel):
    """
    Threshold condition for an outcome (defines failure).

    Attributes:
        operator: Comparison operator
        value: Threshold value
    """

    operator: str = Field(
        ..., pattern=r"^(<|<=|>|>=|==)$", description="Comparison operator"
    )

    value: float = Field(..., description="Threshold value")


class FailureMode(BaseModel):
    """
    Detected pattern where specific variable conditions predict poor outcomes.

    Attributes:
        id: Unique identifier (fm_[a-f0-9]{8})
        evidence_id: Parent evidence ID
        pattern: Conditional pattern (variable ranges)
        outcome_threshold: Outcome threshold that defines failure
        frequency: Percentage of worlds matching pattern (0-1)
        severity: Impact severity level
        description: Natural language description
        created_at: ISO 8601 timestamp of creation
    """

    id: str = Field(
        default_factory=generate_failure_mode_id,
        pattern=r"^fm_[a-f0-9]{8}$",
        description="Unique failure mode ID",
    )

    evidence_id: str = Field(
        ...,
        pattern=r"^evd_[a-f0-9]{8}$",
        description="Parent evidence ID",
    )

    pattern: dict[str, VariableCondition] = Field(
        default_factory=dict,
        description="Variable conditions (variable_name: condition)",
    )

    outcome_threshold: dict[str, OutcomeThreshold] = Field(
        default_factory=dict,
        description="Outcome thresholds (outcome_name: threshold)",
    )

    frequency: float = Field(
        ...,
        ge=0,
        le=1,
        description="Percentage of worlds matching pattern (0-1)",
    )

    severity: SeverityLevel = Field(..., description="Impact severity level")

    description: str = Field(
        ..., description="Natural language description of failure mode"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp (UTC)",
    )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class ClusterOutcomeStats(BaseModel):
    """
    Outcome statistics for a behavioral cluster.

    Attributes:
        mean: Mean value for this cluster
        std: Standard deviation for this cluster
        p50: Median value for this cluster
    """

    mean: float = Field(..., description="Mean value")
    std: float = Field(..., description="Standard deviation")
    p50: float = Field(..., description="Median value")


class BehavioralCluster(BaseModel):
    """
    Group of simulated worlds with similar variable patterns and outcomes.

    Attributes:
        id: Unique identifier (clust_[a-f0-9]{8})
        evidence_id: Parent evidence ID
        cluster_number: Sequential cluster number (1-N)
        world_ids: Array of world IDs in this cluster
        centroid: Representative variable values (JSONB)
        outcome_stats: Outcome distributions for this cluster (JSONB)
        size: Number of worlds in cluster
        percentage: Percentage of total worlds (0-1)
        label: Human-readable cluster label
        created_at: ISO 8601 timestamp of creation
    """

    id: str = Field(
        default_factory=generate_cluster_id,
        pattern=r"^clust_[a-f0-9]{8}$",
        description="Unique cluster ID",
    )

    evidence_id: str = Field(
        ...,
        pattern=r"^evd_[a-f0-9]{8}$",
        description="Parent evidence ID",
    )

    cluster_number: int = Field(
        ..., ge=1, description="Sequential cluster number (1-N)"
    )

    world_ids: list[str] = Field(
        default_factory=list, description="World IDs in this cluster"
    )

    centroid: dict[str, float] = Field(
        default_factory=dict,
        description="Representative variable values (variable_name: mean)",
    )

    outcome_stats: dict[str, ClusterOutcomeStats] = Field(
        default_factory=dict,
        description="Outcome stats for cluster (outcome_name: stats)",
    )

    size: int = Field(..., ge=1, description="Number of worlds in cluster")

    percentage: float = Field(
        ..., ge=0, le=1, description="Percentage of total worlds (0-1)"
    )

    label: str = Field(..., description="Human-readable cluster label")

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp (UTC)",
    )
