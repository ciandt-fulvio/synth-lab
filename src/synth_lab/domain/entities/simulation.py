"""
Simulation entity for causal simulation system.

Represents the root aggregate for a complete causal simulation session, from
natural language question to actionable insights.

References:
    - Spec: specs/035-causal-simulation/spec.md
    - Data model: specs/035-causal-simulation/data-model.md
"""

import secrets
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


def generate_simulation_id() -> str:
    """
    Generate a simulation ID with sim_ prefix and 8-char hex suffix.

    Returns:
        str: ID in format sim_[a-f0-9]{8}
    """
    return f"sim_{secrets.token_hex(4)}"


class SimulationStatus(str, Enum):
    """Status of a simulation run."""

    PARSING = "parsing"
    AWAITING_QUESTION_VALIDATION = "awaiting_question_validation"
    DAG_CONSTRUCTION = "dag_construction"
    AWAITING_DAG_VALIDATION = "awaiting_dag_validation"
    HYPOTHESIS_GENERATION = "hypothesis_generation"
    AWAITING_HYPOTHESIS_VALIDATION = "awaiting_hypothesis_validation"
    READY_TO_RUN = "ready_to_run"
    SIMULATING = "simulating"
    COMPLETED = "completed"
    FAILED = "failed"


class ProblemDecomposition(BaseModel):
    """
    Structured representation of the business problem.

    Attributes:
        intervention: What action/change is being evaluated
        primary_outcome: Main metric of interest
        secondary_outcomes: Additional metrics to track
        unit_of_analysis: Level of analysis (e.g., 'user', 'customer')
        time_horizon: Timeframe for forecast (e.g., '3 months', '1 year')
        decision_type: Category of decision being made
    """

    intervention: str = Field(
        ..., description="What action/change is being evaluated"
    )
    primary_outcome: str = Field(..., description="Main metric of interest")
    secondary_outcomes: list[str] = Field(
        default_factory=list, description="Additional metrics to track"
    )
    unit_of_analysis: str = Field(
        ..., description="Level of analysis (e.g., 'user', 'customer')"
    )
    time_horizon: str = Field(
        ..., description="Timeframe for forecast (e.g., '3 months')"
    )
    decision_type: str = Field(
        ..., description="Category of decision (e.g., 'product_launch')"
    )


class Simulation(BaseModel):
    """
    Simulation entity representing a complete causal simulation session.

    Attributes:
        id: Unique identifier (sim_[a-f0-9]{8})
        question_text: Original natural language question
        problem_decomposition: Structured problem breakdown
        status: Current status of the simulation
        random_seed: Master random seed for reproducibility
        n_worlds: Number of synthetic worlds to simulate
        created_at: ISO 8601 timestamp of creation
        completed_at: ISO 8601 timestamp of completion
        error_message: Error details if status = failed
    """

    id: str = Field(
        default_factory=generate_simulation_id,
        pattern=r"^sim_[a-f0-9]{8}$",
        description="Unique simulation ID",
    )

    question_text: str = Field(
        ...,
        max_length=2000,
        description="Original natural language business question",
    )

    problem_decomposition: Optional[ProblemDecomposition] = Field(
        default=None,
        description="Structured problem: intervention, outcomes, time horizon",
    )

    status: SimulationStatus = Field(
        default=SimulationStatus.PARSING,
        description="Current stage of simulation pipeline",
    )

    random_seed: Optional[int] = Field(
        default=None,
        description="Master random seed for deterministic reproducibility",
    )

    n_worlds: Optional[int] = Field(
        default=500, description="Number of synthetic worlds to generate"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp (UTC)",
    )

    completed_at: Optional[datetime] = Field(
        default=None, description="Completion timestamp (UTC)"
    )

    error_message: Optional[str] = Field(
        default=None, description="Error details if status = failed"
    )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
