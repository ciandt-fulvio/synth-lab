"""
API schemas for synth groups.

Pydantic schemas for synth group API request/response handling.
Includes schemas for custom group configuration with demographic distributions.

References:
    - OpenAPI: specs/018-experiment-hub/contracts/openapi.yaml
    - Data model: specs/018-experiment-hub/data-model.md
    - Custom groups: specs/030-custom-synth-groups/contracts/synth-groups-api.yaml
"""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator

from synth_lab.models.pagination import PaginationMeta


# =============================================================================
# Distribution Configuration Schemas
# =============================================================================


class IdadeDistribution(BaseModel):
    """Age distribution weights (must sum to 1.0)."""

    faixa_15_29: float = Field(
        alias="15-29",
        ge=0,
        le=1,
        description="Weight for age group 15-29",
    )
    faixa_30_44: float = Field(
        alias="30-44",
        ge=0,
        le=1,
        description="Weight for age group 30-44",
    )
    faixa_45_59: float = Field(
        alias="45-59",
        ge=0,
        le=1,
        description="Weight for age group 45-59",
    )
    faixa_60_plus: float = Field(
        alias="60+",
        ge=0,
        le=1,
        description="Weight for age group 60+",
    )

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_sum(self) -> "IdadeDistribution":
        """Validate that weights sum to 1.0 (with tolerance)."""
        total = (
            self.faixa_15_29
            + self.faixa_30_44
            + self.faixa_45_59
            + self.faixa_60_plus
        )
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Age distribution must sum to 1.0, got {total}")
        return self


class EscolaridadeDistribution(BaseModel):
    """Education distribution weights (must sum to 1.0)."""

    sem_instrucao: float = Field(
        ge=0,
        le=1,
        description="Weight for no education",
    )
    fundamental: float = Field(
        ge=0,
        le=1,
        description="Weight for fundamental education",
    )
    medio: float = Field(
        ge=0,
        le=1,
        description="Weight for medium education",
    )
    superior: float = Field(
        ge=0,
        le=1,
        description="Weight for higher education",
    )

    @model_validator(mode="after")
    def validate_sum(self) -> "EscolaridadeDistribution":
        """Validate that weights sum to 1.0 (with tolerance)."""
        total = self.sem_instrucao + self.fundamental + self.medio + self.superior
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Education distribution must sum to 1.0, got {total}")
        return self


class SeveridadeDistribution(BaseModel):
    """Disability severity distribution weights (must sum to 1.0)."""

    nenhuma: float = Field(ge=0, le=1, description="Weight for no severity")
    leve: float = Field(ge=0, le=1, description="Weight for light severity")
    moderada: float = Field(ge=0, le=1, description="Weight for moderate severity")
    severa: float = Field(ge=0, le=1, description="Weight for severe severity")
    total: float = Field(ge=0, le=1, description="Weight for total severity")

    @model_validator(mode="after")
    def validate_sum(self) -> "SeveridadeDistribution":
        """Validate that weights sum to 1.0 (with tolerance)."""
        total = self.nenhuma + self.leve + self.moderada + self.severa + self.total
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Severity distribution must sum to 1.0, got {total}")
        return self


class DeficienciasConfig(BaseModel):
    """Disability configuration."""

    taxa_com_deficiencia: float = Field(
        ge=0,
        le=1,
        description="Percentage of synths with disabilities (0.0 to 1.0)",
    )
    distribuicao_severidade: SeveridadeDistribution = Field(
        description="Severity distribution for those with disabilities",
    )


class ComposicaoFamiliarDistribution(BaseModel):
    """Family composition distribution weights (must sum to 1.0)."""

    unipessoal: float = Field(ge=0, le=1, description="Weight for single person")
    casal_sem_filhos: float = Field(ge=0, le=1, description="Weight for couple without children")
    casal_com_filhos: float = Field(ge=0, le=1, description="Weight for couple with children")
    monoparental: float = Field(ge=0, le=1, description="Weight for single parent")
    multigeracional: float = Field(ge=0, le=1, description="Weight for multigenerational")

    @model_validator(mode="after")
    def validate_sum(self) -> "ComposicaoFamiliarDistribution":
        """Validate that weights sum to 1.0 (with tolerance)."""
        total = (
            self.unipessoal
            + self.casal_sem_filhos
            + self.casal_com_filhos
            + self.monoparental
            + self.multigeracional
        )
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Family composition must sum to 1.0, got {total}")
        return self


class DomainExpertiseConfig(BaseModel):
    """Beta distribution parameters for domain expertise."""

    alpha: float = Field(
        ge=0.1,
        le=10,
        description="Alpha shape parameter for Beta distribution",
    )
    beta: float = Field(
        ge=0.1,
        le=10,
        description="Beta shape parameter for Beta distribution",
    )


class GroupDistributions(BaseModel):
    """All distribution configurations for a synth group."""

    idade: IdadeDistribution = Field(description="Age distribution")
    escolaridade: EscolaridadeDistribution = Field(description="Education distribution")
    deficiencias: DeficienciasConfig = Field(description="Disability configuration")
    composicao_familiar: ComposicaoFamiliarDistribution = Field(
        description="Family composition distribution"
    )
    domain_expertise: DomainExpertiseConfig = Field(
        description="Domain expertise Beta distribution parameters"
    )


class GroupConfig(BaseModel):
    """Complete group configuration for synth generation."""

    n_synths: Annotated[int, Field(ge=1, le=1000)] = Field(
        default=500,
        description="Number of synths to generate",
    )
    distributions: GroupDistributions = Field(
        description="Distribution configurations for all demographic attributes",
    )


# =============================================================================
# Request/Response Schemas for Custom Groups
# =============================================================================


class CreateSynthGroupRequest(BaseModel):
    """Request schema for creating a new synth group with custom distributions."""

    name: str = Field(
        min_length=1,
        max_length=23,
        description="Group name (required)",
        examples=["Aposentados 60+"],
    )
    description: str | None = Field(
        default=None,
        max_length=50,
        description="Optional description",
        examples=["Grupo para simular previdência"],
    )
    config: GroupConfig = Field(
        description="Distribution configuration for synth generation",
    )


class SynthGroupCreateResponse(BaseModel):
    """Response schema after creating a synth group."""

    id: str = Field(
        description="Generated group ID",
        examples=["grp_a1b2c3d4"],
    )
    name: str = Field(description="Group name")
    description: str | None = Field(default=None, description="Group description")
    created_at: datetime = Field(description="Creation timestamp")
    synths_count: int = Field(
        description="Number of synths generated (should be 500)",
    )


class SynthGroupDetailResponse(BaseModel):
    """Response schema for synth group details including config."""

    id: str = Field(description="Group ID")
    name: str = Field(description="Group name")
    description: str | None = Field(default=None, description="Group description")
    created_at: datetime = Field(description="Creation timestamp")
    synths_count: int = Field(description="Number of synths in group")
    config: GroupConfig | None = Field(
        default=None,
        description="Distribution configuration (null for legacy groups)",
    )


# =============================================================================
# Original Schemas (maintained for backward compatibility)
# =============================================================================


class SynthGroupCreate(BaseModel):
    """Schema for creating a new synth group."""

    id: str | None = Field(
        default=None,
        pattern=r"^grp_[a-f0-9]{8}$",
        description="Optional ID. If not provided, will be generated.",
        examples=["grp_a1b2c3d4"])

    name: str = Field(
        min_length=1,
        max_length=23,
        description="Descriptive name for the group.",
        examples=["Geração Dezembro 2025"])

    description: str | None = Field(
        default=None,
        description="Description of the purpose/context.",
        examples=["Synths gerados para testes de checkout"])


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
        description="Synths in this group.")


class PaginatedSynthGroup(BaseModel):
    """Paginated list of synth group summaries."""

    data: list[SynthGroupSummary] = Field(description="List of synth groups.")
    pagination: PaginationMeta = Field(description="Pagination metadata.")
