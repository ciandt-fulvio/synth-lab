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


class ScenarioOptionSchema(BaseModel):
    """Schema for a user-friendly scenario option."""

    value: str = Field(..., description="Internal value identifier (e.g., 'low', 'medium', 'high')")
    label: str = Field(..., description="Display label (e.g., 'Econômico (R$29-39)')")
    distribution_params: DistributionParameters = Field(
        ...,
        description="Distribution parameters for this scenario",
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
    relevance: str = Field(
        default="medium",
        description="Variable relevance level: low, medium, or high",
        pattern="^(low|medium|high)$",
    )
    range_min: float | None = Field(
        default=None,
        description="Lower bound for clamping distribution samples",
    )
    range_max: float | None = Field(
        default=None,
        description="Upper bound for clamping distribution samples",
    )
    correlations: list[CorrelationSchema] = Field(
        default_factory=list,
        description="Correlations with other variables",
    )
    scenario_options: list[ScenarioOptionSchema] | None = Field(
        default=None,
        description="Pre-defined scenario options for controllable variables",
    )
    selected_scenario: str | None = Field(
        default=None,
        description="Currently selected scenario value",
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
    relevance: str | None = Field(
        default=None,
        description="Updated relevance level: low, medium, or high",
        pattern="^(low|medium|high)$",
    )
    range_min: float | None = Field(
        default=None,
        description="Updated lower bound for clamping (null to clear)",
    )
    range_max: float | None = Field(
        default=None,
        description="Updated upper bound for clamping (null to clear)",
    )
    correlations: list[CorrelationSchema] | None = Field(
        default=None,
        description="Updated correlations",
    )
    selected_scenario: str | None = Field(
        default=None,
        description="Selected scenario value (for controllable variables)",
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


# ============================================================================
# Wizard Schemas (Feature 036-simplified-hypothesis-wizard)
# ============================================================================


class WizardInitRequest(BaseModel):
    """Request to initialize hypothesis wizard with scenario profile."""

    scenario_profile: str = Field(
        ...,
        description="Scenario profile: conservative, realistic, or optimistic",
        pattern="^(conservative|realistic|optimistic)$",
    )


class ClarificationQuestionSchema(BaseModel):
    """Schema for a clarification question about a critical variable."""

    variable_name: str = Field(..., description="Variable identifier from DAG")
    question_text: str = Field(
        ..., description="Plain-language question asking about frequency or magnitude"
    )
    criticality_score: float = Field(..., ge=0, description="Ranking score (impact × uncertainty)")


class WizardInitResponse(BaseModel):
    """Response from wizard initialization with hypotheses and clarification questions."""

    hypotheses: list[HypothesisSchema] = Field(
        ..., description="Generated hypotheses for all DAG variables"
    )
    clarification_questions: list[ClarificationQuestionSchema] = Field(
        ...,
        description="3-5 questions about critical variables (may be empty if low uncertainty)",
    )


class ClarificationResponseSchema(BaseModel):
    """User response to a clarification question."""

    variable_name: str = Field(..., description="Variable identifier from DAG")
    response: str = Field(
        ...,
        description="Qualitative response: more, less, equal, or dont_know",
        pattern="^(more|less|equal|dont_know)$",
    )


class WizardClarifyRequest(BaseModel):
    """Request to apply clarification responses to hypotheses."""

    responses: list[ClarificationResponseSchema] = Field(
        ..., description="User responses to clarification questions (may be empty)"
    )


class WizardClarifyResponse(BaseModel):
    """Response from applying clarifications with updated hypotheses."""

    hypotheses: list[HypothesisSchema] = Field(
        ..., description="Updated hypotheses with clarification adjustments applied"
    )
