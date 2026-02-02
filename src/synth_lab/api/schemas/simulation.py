"""
Pydantic schemas for simulation API requests and responses.

References:
    - Spec: specs/035-causal-simulation/spec.md
    - Data model: specs/035-causal-simulation/data-model.md
"""

from datetime import datetime

from pydantic import BaseModel, Field

from synth_lab.domain.entities.simulated_world import PercentileDistribution
from synth_lab.domain.entities.simulation import (
    ProblemDecomposition,
    SimulationStatus,
)


class SimulationCreate(BaseModel):
    """Request schema for creating a new simulation."""

    question_text: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Natural language business question",
        examples=["What will be the adoption rate for a weekly meal subscription?"],
    )

    random_seed: int | None = Field(
        default=42,
        description="Master random seed for reproducibility",
    )

    n_worlds: int | None = Field(
        default=500,
        ge=100,
        le=10000,
        description="Number of synthetic worlds to simulate",
    )


class SimulationResponse(BaseModel):
    """Response schema for simulation details."""

    id: str = Field(..., description="Simulation ID")

    question_text: str = Field(..., description="Original question")

    problem_decomposition: ProblemDecomposition | None = Field(
        default=None,
        description="Structured problem breakdown",
    )

    status: SimulationStatus = Field(..., description="Current status")

    random_seed: int | None = Field(
        default=None, description="Random seed used"
    )

    n_worlds: int | None = Field(
        default=None, description="Number of worlds"
    )

    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class ProblemDecompositionUpdate(BaseModel):
    """Request schema for updating problem decomposition."""

    intervention: str | None = Field(
        default=None,
        max_length=500,
        description="Updated intervention description",
    )

    primary_outcome: str | None = Field(
        default=None,
        max_length=200,
        description="Updated primary outcome metric",
    )

    secondary_outcomes: list[str] | None = Field(
        default=None,
        description="Updated secondary outcomes list",
    )

    unit_of_analysis: str | None = Field(
        default=None,
        description="Updated unit of analysis",
    )

    time_horizon: str | None = Field(
        default=None,
        max_length=100,
        description="Updated time horizon",
    )

    decision_type: str | None = Field(
        default=None,
        description="Updated decision type",
    )


class ConfirmDAGRequest(BaseModel):
    """Request schema for confirming DAG with optional scenario profile."""

    scenario_profile: str | None = Field(
        default=None,
        description="Scenario profile: conservative, realistic, or optimistic",
    )


class ClarificationQuestionOut(BaseModel):
    """Clarification question in confirm-dag response."""

    variable_name: str = Field(..., description="Variable identifier from DAG")
    question_text: str = Field(..., description="Plain-language question")
    criticality_score: float = Field(..., ge=0, description="Ranking score")


class ConfirmDAGResponse(SimulationResponse):
    """Response schema for confirm-dag with optional clarification questions."""

    clarification_questions: list[ClarificationQuestionOut] = Field(
        default_factory=list,
        description="Clarification questions for critical variables (empty if no profile)",
    )


class SimulationRunRequest(BaseModel):
    """Request schema for running a simulation (optional parameters)."""

    n_worlds: int | None = Field(
        default=None,
        ge=100,
        le=10000,
        description="Override number of worlds",
    )


class SimulationRunResponse(BaseModel):
    """Response schema for simulation run results."""

    simulation_id: str = Field(..., description="Simulation ID")

    status: str = Field(..., description="Run status")

    n_worlds: int = Field(..., description="Number of worlds generated")

    n_insights: int = Field(..., description="Number of insights generated")

    outcome_distributions: dict[str, PercentileDistribution] = Field(
        default_factory=dict,
        description="Percentile distributions for outcomes",
    )

    class Config:
        """Pydantic configuration."""

        from_attributes = True
