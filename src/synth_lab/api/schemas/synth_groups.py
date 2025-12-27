"""
T008 API schemas for synth groups.

Pydantic schemas for synth group API request/response handling.

References:
    - OpenAPI: specs/018-experiment-hub/contracts/openapi.yaml
    - Data model: specs/018-experiment-hub/data-model.md
"""

from datetime import datetime

from pydantic import BaseModel, Field

from synth_lab.models.pagination import PaginationMeta


class SynthGroupCreate(BaseModel):
    """Schema for creating a new synth group."""

    id: str | None = Field(
        default=None,
        pattern=r"^grp_[a-f0-9]{8}$",
        description="Optional ID. If not provided, will be generated.",
        examples=["grp_a1b2c3d4"],
    )

    name: str = Field(
        description="Descriptive name for the group.",
        examples=["Geração Dezembro 2025"],
    )

    description: str | None = Field(
        default=None,
        description="Description of the purpose/context.",
        examples=["Synths gerados para testes de checkout"],
    )


class SynthSummary(BaseModel):
    """Summary of a synth for list display."""

    id: str = Field(description="Synth ID.")
    nome: str = Field(description="Synth name.")
    descricao: str | None = Field(default=None, description="Synth description.")
    avatar_path: str | None = Field(default=None, description="Path to avatar image.")
    synth_group_id: str | None = Field(default=None, description="Group ID.")
    created_at: datetime = Field(description="Creation timestamp.")


class SynthGroupSummary(BaseModel):
    """Summary of a synth group for list display."""

    id: str = Field(description="Group ID.", examples=["grp_a1b2c3d4"])
    name: str = Field(description="Group name.")
    description: str | None = Field(default=None, description="Group description.")
    synth_count: int = Field(default=0, description="Number of synths in group.")
    created_at: datetime = Field(description="Creation timestamp.")


class SynthGroupDetail(SynthGroupSummary):
    """Full synth group details including synth list."""

    synths: list[SynthSummary] = Field(
        default_factory=list,
        description="Synths in this group.",
    )


class PaginatedSynthGroup(BaseModel):
    """Paginated list of synth group summaries."""

    data: list[SynthGroupSummary] = Field(description="List of synth groups.")
    pagination: PaginationMeta = Field(description="Pagination metadata.")
