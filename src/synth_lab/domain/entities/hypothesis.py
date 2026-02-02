"""
Hypothesis and HypothesisVersion entities for causal simulation system.

Represents quantitative parametrization of variables with distributions, ranges,
correlations, and versioned snapshots for scenario planning.

References:
    - Spec: specs/035-causal-simulation/spec.md
    - Data model: specs/035-causal-simulation/data-model.md
    - SciPy distributions: https://docs.scipy.org/doc/scipy/reference/stats.html
    - NumPy random: https://numpy.org/doc/stable/reference/random/index.html
"""

import secrets
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, Field


def generate_hypothesis_id() -> str:
    """
    Generate a hypothesis ID with hyp_ prefix and 8-char hex suffix.

    Returns:
        str: ID in format hyp_[a-f0-9]{8}
    """
    return f"hyp_{secrets.token_hex(4)}"


def generate_hypothesis_version_id() -> str:
    """
    Generate a hypothesis version ID with hv_ prefix and 8-char hex suffix.

    Returns:
        str: ID in format hv_[a-f0-9]{8}
    """
    return f"hv_{secrets.token_hex(4)}"


class DistributionType(str, Enum):
    """Supported probability distributions for variable sampling."""

    UNIFORM = "uniform"  # Uniform(low, high)
    NORMAL = "normal"  # Normal(mean, std)
    BETA = "beta"  # Beta(alpha, beta) - bounded [0, 1]
    LOGNORMAL = "lognormal"  # LogNormal(mean, sigma) - positive values
    BERNOULLI = "bernoulli"  # Bernoulli(p) - binary outcomes
    TRIANGULAR = "triangular"  # Triangular(min, mode, max) - three-point estimate


class TemporalityType(str, Enum):
    """Types of time-dependent behavior for variables."""

    LINEAR = "linear"  # Linear growth/decay
    EXPONENTIAL = "exponential"  # Exponential growth/decay
    SEASONAL = "seasonal"  # Periodic seasonal patterns


class Relevance(str, Enum):
    """Relevância da variável para o resultado da simulação."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ScenarioProfile(str, Enum):
    """Predefined scenario profiles for hypothesis generation wizard."""

    CONSERVATIVE = "conservative"  # Worse-than-average outcomes, higher uncertainty
    REALISTIC = "realistic"  # Market-average parameters (default)
    OPTIMISTIC = "optimistic"  # Better-than-average outcomes, lower uncertainty


class ResponseType(str, Enum):
    """Qualitative response options for clarification questions."""

    MORE = "more"  # Higher frequency/magnitude than expected
    LESS = "less"  # Lower frequency/magnitude than expected
    EQUAL = "equal"  # Matches expectation (profile default)
    DONT_KNOW = "dont_know"  # High uncertainty, increase variance


class UniformParams(BaseModel):
    """Parameters for uniform distribution."""

    low: float = Field(..., description="Lower bound")
    high: float = Field(..., description="Upper bound")


class NormalParams(BaseModel):
    """Parameters for normal distribution."""

    mean: float = Field(..., description="Mean (center)")
    std: float = Field(..., gt=0, description="Standard deviation (spread)")


class BetaParams(BaseModel):
    """Parameters for beta distribution (bounded [0, 1])."""

    alpha: float = Field(..., gt=0, description="Alpha parameter (shape)")
    beta: float = Field(..., gt=0, description="Beta parameter (shape)")


class LogNormalParams(BaseModel):
    """Parameters for lognormal distribution (positive values)."""

    mean: float = Field(..., description="Mean of underlying normal")
    sigma: float = Field(..., gt=0, description="Std of underlying normal")


class BernoulliParams(BaseModel):
    """Parameters for Bernoulli distribution (binary outcomes)."""

    p: float = Field(..., ge=0, le=1, description="Probability of success")


class Correlation(BaseModel):
    """
    Declared correlation with another variable.

    Attributes:
        with_variable_id: ID of correlated variable
        with_variable_name: Name of correlated variable (cached)
        correlation: Correlation coefficient (-1 to 1)
        rationale: Explanation for this correlation
    """

    with_variable_id: str = Field(..., description="ID of correlated variable")

    with_variable_name: str = Field(..., description="Name of correlated variable (cached)")

    correlation: float = Field(..., ge=-1, le=1, description="Correlation coefficient (-1 to 1)")

    rationale: str = Field(..., description="Explanation for this correlation")


class Temporality(BaseModel):
    """
    Time-dependent behavior specification.

    Attributes:
        type: Type of temporal behavior
        parameters: Type-specific parameters
    """

    type: TemporalityType = Field(..., description="Type of temporal behavior")

    parameters: dict[str, float] = Field(
        default_factory=dict, description="Type-specific parameters"
    )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class TriangularParams(BaseModel):
    """Parameters for triangular distribution (user-friendly scenarios)."""

    min_value: float = Field(..., description="Minimum value")
    mode: float = Field(..., description="Most likely value")
    max_value: float = Field(..., description="Maximum value")


# Type alias for hypothesis parameters union
HypothesisParameters = Union[
    UniformParams,
    NormalParams,
    BetaParams,
    LogNormalParams,
    BernoulliParams,
    TriangularParams,
]


class ScenarioOption(BaseModel):
    """
    User-friendly scenario option for controllable variables.

    Attributes:
        value: Internal value identifier (e.g., 'low', 'medium', 'high')
        label: Display label (e.g., 'Econômico (R$29-39)')
        distribution_params: Distribution parameters for this scenario
    """

    value: str = Field(..., description="Internal value identifier")

    label: str = Field(..., description="Display label for the scenario")

    distribution_params: TriangularParams = Field(
        ..., description="Distribution parameters for this scenario"
    )


class Hypothesis(BaseModel):
    """
    Quantitative parametrization of a variable with distribution.

    Attributes:
        id: Unique identifier (hyp_[a-f0-9]{8})
        simulation_id: Parent simulation ID
        variable_id: References DAG node ID
        variable_name: Cached for convenience
        distribution_type: Type of probability distribution
        parameters: Distribution-specific parameters
        correlations: Declared correlations with other variables
        temporality: Time-dependent behavior if applicable
        version: Version for hypothesis edits
        created_at: ISO 8601 timestamp of creation
    """

    id: str = Field(
        default_factory=generate_hypothesis_id,
        pattern=r"^hyp_[a-f0-9]{8}$",
        description="Unique hypothesis ID",
    )

    simulation_id: str = Field(
        ...,
        pattern=r"^sim_[a-f0-9]{8}$",
        description="Parent simulation ID",
    )

    variable_id: str = Field(..., description="References DAG node ID")

    variable_name: str = Field(..., description="Cached for convenience")

    distribution_type: DistributionType = Field(..., description="Type of probability distribution")

    parameters: Union[
        UniformParams,
        NormalParams,
        BetaParams,
        LogNormalParams,
        BernoulliParams,
        TriangularParams,
    ] = Field(..., description="Distribution-specific parameters")

    relevance: Relevance = Field(
        default=Relevance.MEDIUM,
        description="Variable relevance level for simulation outcome (low, medium, high)",
    )

    range_min: Optional[float] = Field(
        default=None,
        description="Lower bound for clamping distribution samples",
    )

    range_max: Optional[float] = Field(
        default=None,
        description="Upper bound for clamping distribution samples",
    )

    correlations: list[Correlation] = Field(
        default_factory=list,
        description="Declared correlations with other variables",
    )

    temporality: Optional[Temporality] = Field(
        default=None, description="Time-dependent behavior if applicable"
    )

    scenario_options: Optional[list[ScenarioOption]] = Field(
        default=None,
        description="Pre-defined scenario options for controllable variables",
    )

    selected_scenario: Optional[str] = Field(
        default=None,
        description="Currently selected scenario value (references ScenarioOption.value)",
    )

    version: int = Field(default=1, description="Version for hypothesis edits")

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp (UTC)",
    )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class HypothesisSnapshot(BaseModel):
    """
    Complete snapshot of hypotheses and DAG version.

    Attributes:
        hypotheses: Array of complete Hypothesis objects
        dag_version: Version of DAG at snapshot time
    """

    hypotheses: list[Hypothesis] = Field(
        default_factory=list, description="Complete hypothesis set"
    )

    dag_version: int = Field(..., description="DAG version at snapshot time")


class HypothesisVersion(BaseModel):
    """
    Named snapshot of complete hypothesis set for scenario planning.

    Attributes:
        id: Unique identifier (hv_[a-f0-9]{8})
        simulation_id: Parent simulation ID
        name: User-provided name (e.g., "Optimistic Case")
        description: User-provided description
        snapshot: Complete state of all hypotheses
        dag_snapshot: Complete state of DAG at this version
        created_at: ISO 8601 timestamp of creation
    """

    id: str = Field(
        default_factory=generate_hypothesis_version_id,
        pattern=r"^hv_[a-f0-9]{8}$",
        description="Unique hypothesis version ID",
    )

    simulation_id: str = Field(
        ...,
        pattern=r"^sim_[a-f0-9]{8}$",
        description="Parent simulation ID",
    )

    name: str = Field(
        ...,
        max_length=100,
        description="User-provided name (e.g., 'Optimistic Case')",
    )

    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="User-provided description",
    )

    snapshot: HypothesisSnapshot = Field(..., description="Complete state of all hypotheses")

    dag_snapshot: dict = Field(
        default_factory=dict,
        description="Complete state of DAG at this version (JSONB)",
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp (UTC)",
    )
