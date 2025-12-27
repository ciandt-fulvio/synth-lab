"""
T007 API schemas for experiments.

Pydantic schemas for experiment API request/response handling.

References:
    - OpenAPI: specs/018-experiment-hub/contracts/openapi.yaml
    - Data model: specs/018-experiment-hub/data-model.md
"""

from datetime import datetime

from pydantic import BaseModel, Field

from synth_lab.models.pagination import PaginationMeta


class ExperimentCreate(BaseModel):
    """Schema for creating a new experiment."""

    name: str = Field(
        max_length=100,
        description="Short name of the feature.",
        examples=["Novo Fluxo de Checkout"],
    )

    hypothesis: str = Field(
        max_length=500,
        description="Description of the hypothesis to test.",
        examples=["Reduzir etapas do checkout aumentará conversão em 15%"],
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Additional context, links, references.",
        examples=["Baseado em feedback de usuários e análise de abandono"],
    )


class ExperimentUpdate(BaseModel):
    """Schema for updating an experiment."""

    name: str | None = Field(
        default=None,
        max_length=100,
        description="Short name of the feature.",
    )

    hypothesis: str | None = Field(
        default=None,
        max_length=500,
        description="Description of the hypothesis to test.",
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Additional context, links, references.",
    )


class SimulationSummary(BaseModel):
    """Summary of a simulation linked to an experiment."""

    id: str = Field(description="Simulation run ID.")
    scenario_id: str = Field(description="Scenario identifier.")
    status: str = Field(description="Simulation status.")
    has_insights: bool = Field(default=False, description="Whether insights are available.")
    started_at: datetime = Field(description="Start timestamp.")
    completed_at: datetime | None = Field(default=None, description="Completion timestamp.")
    score: float | None = Field(default=None, description="Aggregated score (0-100).")


class InterviewSummary(BaseModel):
    """Summary of an interview linked to an experiment."""

    exec_id: str = Field(description="Execution ID.")
    topic_name: str = Field(description="Research topic name.")
    status: str = Field(description="Interview status.")
    synth_count: int = Field(description="Number of synths interviewed.")
    has_summary: bool = Field(default=False, description="Whether summary is available.")
    has_prfaq: bool = Field(default=False, description="Whether PR-FAQ is available.")
    started_at: datetime = Field(description="Start timestamp.")
    completed_at: datetime | None = Field(default=None, description="Completion timestamp.")


class ExperimentSummary(BaseModel):
    """Summary of an experiment for list display."""

    id: str = Field(description="Experiment ID.", examples=["exp_a1b2c3d4"])
    name: str = Field(description="Short name of the feature.")
    hypothesis: str = Field(description="Hypothesis description.")
    simulation_count: int = Field(default=0, description="Number of linked simulations.")
    interview_count: int = Field(default=0, description="Number of linked interviews.")
    created_at: datetime = Field(description="Creation timestamp.")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp.")


class ExperimentDetail(ExperimentSummary):
    """Full experiment details including linked simulations and interviews."""

    description: str | None = Field(default=None, description="Additional context.")
    simulations: list[SimulationSummary] = Field(
        default_factory=list,
        description="Linked simulations.",
    )
    interviews: list[InterviewSummary] = Field(
        default_factory=list,
        description="Linked interviews.",
    )


class PaginatedExperimentSummary(BaseModel):
    """Paginated list of experiment summaries."""

    data: list[ExperimentSummary] = Field(description="List of experiments.")
    pagination: PaginationMeta = Field(description="Pagination metadata.")
