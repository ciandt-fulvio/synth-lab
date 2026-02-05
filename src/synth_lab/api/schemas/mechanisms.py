"""
Pydantic schemas for Mechanism Configuration API requests and responses.

References:
    - Spec: specs/039-narrative-mechanism-config/spec.md
    - API contract: specs/039-narrative-mechanism-config/contracts/api.yaml
    - Entities: domain/entities/mechanism_definition.py, feature_type.py, narrative_response.py
"""

from pydantic import BaseModel, Field


# ============================================================================
# Mechanism Schemas (GET /mechanisms)
# ============================================================================


class MechanismOptionSchema(BaseModel):
    """API schema for a mechanism option."""

    id: str = Field(..., description="Unique option identifier (UUID)")
    label: str = Field(..., description="Display text for the option")
    value: float = Field(..., ge=0.0, le=1.0, description="Numeric value [0.0, 1.0]")
    display_order: int = Field(..., description="Order in dropdown (ascending)")


class MechanismDefinitionSchema(BaseModel):
    """API schema for a mechanism definition with its options."""

    id: str = Field(..., description="Unique mechanism identifier (UUID)")
    key: str = Field(..., description="Programmatic key (e.g., 'irreversibility')")
    label_pt: str = Field(..., description="Portuguese label for display")
    description: str = Field(..., description="Explanation of what this mechanism measures")
    options: list[MechanismOptionSchema] = Field(
        ..., description="Available options for this mechanism"
    )


class MechanismListResponse(BaseModel):
    """Response for GET /mechanisms."""

    mechanisms: list[MechanismDefinitionSchema] = Field(
        ..., description="List of all mechanism definitions with options"
    )


# ============================================================================
# Feature Type Schemas (GET /mechanisms/feature-types)
# ============================================================================


class FeatureTypeSchema(BaseModel):
    """API schema for a feature type."""

    id: str = Field(..., description="Unique feature type identifier (UUID)")
    key: str = Field(..., description="Programmatic key (e.g., 'financial')")
    label_pt: str = Field(..., description="Portuguese label for display")
    description: str | None = Field(None, description="Description of this feature type")
    amplifies_mechanisms: list[str] = Field(
        ..., description="List of mechanism keys this type amplifies"
    )


class FeatureTypeListResponse(BaseModel):
    """Response for GET /mechanisms/feature-types."""

    feature_types: list[FeatureTypeSchema] = Field(
        ..., description="List of all feature types"
    )


# ============================================================================
# Narrative Generation Schemas (POST /experiments/generate-narrative)
# ============================================================================


class GenerateNarrativeRequest(BaseModel):
    """Request body for POST /experiments/generate-narrative."""

    name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Feature name",
    )
    hypothesis: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Hypothesis to test",
    )
    description: str | None = Field(
        None,
        max_length=2000,
        description="Additional context",
    )


class SelectedMechanismSchema(BaseModel):
    """A mechanism selected by the LLM with its default option."""

    key: str = Field(..., description="Mechanism key (e.g., 'irreversibility')")
    default_option_id: str = Field(..., description="UUID of the default option chosen by LLM")


class GenerateNarrativeResponse(BaseModel):
    """Response for POST /experiments/generate-narrative."""

    inferred_types: list[str] = Field(
        ..., description="Feature types inferred by LLM (e.g., ['financial', 'social'])"
    )
    narrative_template: str = Field(
        ...,
        description="Narrative text with {mechanism_key} placeholders",
    )
    selected_mechanisms: list[SelectedMechanismSchema] = Field(
        ..., description="Mechanisms selected as relevant (2-4)"
    )
    excluded_mechanisms: list[str] = Field(
        ..., description="Mechanism keys deemed not relevant"
    )


# ============================================================================
# Admin Schemas (US4 - Admin CRUD operations)
# ============================================================================


class CreateMechanismRequest(BaseModel):
    """Request body for POST /mechanisms (create mechanism)."""

    key: str = Field(
        ...,
        max_length=50,
        pattern=r"^[a-z_]+$",
        description="Programmatic key (lowercase with underscores)",
    )
    label_pt: str = Field(
        ...,
        max_length=100,
        description="Portuguese label for display",
    )
    description: str = Field(
        ...,
        description="Explanation of what this mechanism measures",
    )


class UpdateMechanismRequest(BaseModel):
    """Request body for PUT /mechanisms/{key} (update mechanism)."""

    label_pt: str | None = Field(
        None,
        max_length=100,
        description="Portuguese label for display",
    )
    description: str | None = Field(
        None,
        description="Explanation of what this mechanism measures",
    )


class CreateOptionRequest(BaseModel):
    """Request body for POST /mechanisms/{key}/options (add option)."""

    label: str = Field(
        ...,
        max_length=100,
        description="Display text for the option",
    )
    value: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Numeric value [0.0, 1.0]",
    )
    display_order: int = Field(
        ...,
        ge=1,
        description="Order in dropdown (ascending)",
    )


class UpdateOptionRequest(BaseModel):
    """Request body for PUT /mechanisms/{key}/options/{option_id} (update option)."""

    label: str | None = Field(
        None,
        max_length=100,
        description="Display text for the option",
    )
    value: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Numeric value [0.0, 1.0]",
    )
    display_order: int | None = Field(
        None,
        ge=1,
        description="Order in dropdown (ascending)",
    )
