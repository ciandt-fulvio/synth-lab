"""
API schemas for experiments.

Pydantic schemas for experiment API request/response handling.

References:
    - OpenAPI: specs/019-experiment-refactor/contracts/experiment-api.yaml
    - Data model: specs/019-experiment-refactor/data-model.md
"""

from datetime import datetime

from pydantic import BaseModel, Field

from synth_lab.domain.entities.synth_group import DEFAULT_SYNTH_GROUP_ID
from synth_lab.models.pagination import PaginationMeta

# =============================================================================
# Experiment Request Schemas
# =============================================================================


class ExperimentCreate(BaseModel):
    """Schema for creating a new experiment."""

    name: str = Field(
        max_length=100,
        description="Short name of the feature.",
        examples=["Novo Fluxo de Checkout"])

    hypothesis: str = Field(
        max_length=500,
        description="Description of the hypothesis to test.",
        examples=["Reduzir etapas do checkout aumentara conversao em 15%"])

    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Additional context, links, references.",
        examples=["Baseado em feedback de usuarios e analise de abandono"])

    synth_group_id: str = Field(
        default=DEFAULT_SYNTH_GROUP_ID,
        min_length=1,
        max_length=50,
        description="ID of the synth group to use for this experiment. Defaults to the default group.",
        examples=["grp_00000001", "grp_abc123"])


class ExperimentUpdate(BaseModel):
    """Schema for updating an experiment."""

    name: str | None = Field(
        default=None,
        max_length=100,
        description="Short name of the feature.")

    hypothesis: str | None = Field(
        default=None,
        max_length=500,
        description="Description of the hypothesis to test.")

    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Additional context, links, references.")

    synth_group_id: str | None = Field(
        default=None,
        description="ID of the synth group to use for this experiment.")


# =============================================================================
# Related Entity Summaries (for ExperimentDetail)
# =============================================================================


class InterviewSummary(BaseModel):
    """Summary of an interview linked to an experiment."""

    exec_id: str = Field(description="Execution ID.")
    topic_name: str = Field(description="Research topic name.")
    status: str = Field(description="Interview status.")
    synth_count: int = Field(description="Number of synths interviewed.")
    total_turns: int = Field(default=0, description="Total turns across all transcripts.")
    has_summary: bool = Field(default=False, description="Whether summary is available.")
    has_prfaq: bool = Field(default=False, description="Whether PR-FAQ is available.")
    additional_context: str | None = Field(
        default=None, description="Additional context text (if provided)."
    )
    synth_selection_type: str | None = Field(
        default=None, description="Synth selection strategy (random, propensos, resistentes, indecisos, sensiveis)."
    )
    started_at: datetime = Field(description="Start timestamp.")
    completed_at: datetime | None = Field(default=None, description="Completion timestamp.")


# =============================================================================
# Experiment Response Schemas
# =============================================================================


class ExperimentResponse(BaseModel):
    """Response schema for experiment data."""

    id: str = Field(description="Experiment ID.", examples=["exp_a1b2c3d4"])
    name: str = Field(description="Short name of the feature.")
    hypothesis: str = Field(description="Hypothesis description.")
    description: str | None = Field(default=None, description="Additional context.")
    synth_group_id: str = Field(description="ID of the synth group used for this experiment.")
    synth_group_name: str = Field(description="Name of the synth group used for this experiment.")
    has_interview_guide: bool = Field(
        default=False, description="Whether interview guide is configured."
    )
    tags: list[str] = Field(default_factory=list, description="Tag names associated with this experiment.")
    created_at: datetime = Field(description="Creation timestamp.")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp.")


class ExperimentSummary(BaseModel):
    """Summary of an experiment for list display."""

    id: str = Field(description="Experiment ID.", examples=["exp_a1b2c3d4"])
    name: str = Field(description="Short name of the feature.")
    hypothesis: str = Field(description="Hypothesis description.")
    description: str | None = Field(default=None, description="Additional context.")
    synth_group_id: str = Field(description="ID of the synth group used for this experiment.")
    synth_group_name: str = Field(description="Name of the synth group used for this experiment.")
    has_interview_guide: bool = Field(
        default=False, description="Whether interview guide is configured."
    )
    interview_count: int = Field(default=0, description="Number of linked interviews.")
    tags: list[str] = Field(default_factory=list, description="Tag names associated with this experiment.")
    created_at: datetime = Field(description="Creation timestamp.")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp.")


class ExperimentDetail(ExperimentResponse):
    """Full experiment details including linked interviews."""

    interviews: list[InterviewSummary] = Field(
        default_factory=list,
        description="Linked interviews (N:1 relationship).")
    interview_count: int = Field(default=0, description="Number of linked interviews.")


class PaginatedExperimentSummary(BaseModel):
    """Paginated list of experiment summaries."""

    data: list[ExperimentSummary] = Field(description="List of experiments.")
    pagination: PaginationMeta = Field(description="Pagination metadata.")
