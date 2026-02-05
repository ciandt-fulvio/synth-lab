"""
NarrativeResponse entity for narrative mechanism configuration.

Transient response from LLM narrative generation. Not persisted to database.

References:
    - Spec: specs/039-narrative-mechanism-config/spec.md
    - API: specs/039-narrative-mechanism-config/contracts/api.yaml
"""

from pydantic import BaseModel, Field


class SelectedMechanism(BaseModel):
    """A mechanism selected by the LLM with its default option.

    Attributes:
        key: Mechanism key (e.g., "irreversibility")
        default_option_id: UUID of the default option chosen by LLM
    """

    key: str = Field(..., description="Mechanism key")
    default_option_id: str = Field(..., description="UUID of the default option chosen by LLM")


class NarrativeResponse(BaseModel):
    """Response from LLM narrative generation.

    This is a transient entity used only in memory for API responses.
    It is NOT persisted to the database.

    Attributes:
        inferred_types: Feature types inferred by LLM (e.g., ["financial", "social"])
        narrative_template: Narrative text with {mechanism_key} placeholders
        selected_mechanisms: Mechanisms selected as relevant (2-4)
        excluded_mechanisms: Mechanism keys deemed not relevant
    """

    inferred_types: list[str] = Field(
        ...,
        description="Feature types inferred by LLM",
    )
    narrative_template: str = Field(
        ...,
        description="Narrative text with {mechanism_key} placeholders",
    )
    selected_mechanisms: list[SelectedMechanism] = Field(
        ...,
        min_length=2,
        max_length=4,
        description="Mechanisms selected as relevant (2-4)",
    )
    excluded_mechanisms: list[str] = Field(
        default_factory=list,
        description="Mechanism keys deemed not relevant",
    )
