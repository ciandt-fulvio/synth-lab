"""
Pydantic schemas for Hypothesis API requests and responses.

References:
    - Spec: specs/035-causal-simulation/spec.md
    - Entity: domain/entities/hypothesis.py
"""

from datetime import datetime
from pydantic import BaseModel, Field


class DistributionParameters(BaseModel):
    """Distribution parameters schema."""

    distribution_type: str = Field(
        ...,
        description="Distribution type: normal, uniform, beta, lognormal, triangular",
    )
    min_value: float | None = Field(
        default=None,
        description="Minimum value",
    )
    max_value: float | None = Field(
        default=None,
        description="Maximum value",
    )
    mean: float | None = Field(
        default=None,
        description="Mean (for normal/lognormal)",
    )
    std_dev: float | None = Field(
        default=None,
        description="Standard deviation",
    )
    mode: float | None = Field(
        default=None,
        description="Mode (for triangular)",
    )
    alpha: float | None = Field(
        default=None,
        description="Alpha parameter (for beta)",
    )
    beta: float | None = Field(
        default=None,
        description="Beta parameter (for beta)",
    )


class CorrelationSchema(BaseModel):
    """Correlation with another variable."""

    target_variable: str = Field(..., description="Target variable name")
    correlation_coefficient: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Correlation coefficient",
    )
    relationship_type: str = Field(
        default="linear",
        description="Relationship type",
    )


class HypothesisSchema(BaseModel):
    """Schema for a single hypothesis."""

    id: str = Field(..., description="Hypothesis ID")
    simulation_id: str = Field(..., description="Parent simulation ID")
    variable_name: str = Field(..., description="Variable this quantifies")
    parameters: DistributionParameters = Field(
        ...,
        description="Distribution parameters",
    )
    correlations: list[CorrelationSchema] = Field(
        default_factory=list,
        description="Correlations with other variables",
    )
    version: int = Field(default=1, description="Hypothesis version")
    rationale: str | None = Field(
        default=None,
        description="LLM-generated rationale",
    )
    sources: list[str] = Field(
        default_factory=list,
        description="Evidence sources",
    )
    created_at: datetime = Field(..., description="Creation timestamp")


class HypothesisUpdateRequest(BaseModel):
    """Request schema for updating a hypothesis."""

    parameters: DistributionParameters | None = Field(
        default=None,
        description="Updated distribution parameters",
    )
    correlations: list[CorrelationSchema] | None = Field(
        default=None,
        description="Updated correlations",
    )
    rationale: str | None = Field(
        default=None,
        description="Updated rationale",
    )


class HypothesesBulkUpdateRequest(BaseModel):
    """Request schema for bulk hypothesis updates."""

    updates: dict[str, HypothesisUpdateRequest] = Field(
        ...,
        description="Updates keyed by variable name",
    )


class HypothesisVersionSchema(BaseModel):
    """Schema for hypothesis version summary."""

    version: int = Field(..., description="Version number")
    created_at: datetime = Field(..., description="Version timestamp")
    name: str | None = Field(default=None, description="Version name")
    description: str | None = Field(
        default=None,
        description="Version description",
    )
    changes_summary: str | None = Field(
        default=None,
        description="Summary of changes",
    )


class HypothesisVersionCreateRequest(BaseModel):
    """Request schema for creating a hypothesis version."""

    name: str = Field(..., description="Version name (e.g., 'Optimistic')")
    description: str | None = Field(
        default=None,
        description="Version description",
    )


class HypothesisCompareRequest(BaseModel):
    """Request schema for comparing hypothesis versions."""

    version_a: int = Field(..., description="First version to compare")
    version_b: int = Field(..., description="Second version to compare")


class HypothesisCompareResponse(BaseModel):
    """Response schema for hypothesis comparison."""

    changed_variables: list[str] = Field(
        default_factory=list,
        description="Variables with changed parameters",
    )
    parameter_changes: dict[str, dict] = Field(
        default_factory=dict,
        description="Detailed parameter changes per variable",
    )
    correlation_changes: dict[str, dict] = Field(
        default_factory=dict,
        description="Correlation changes per variable",
    )
