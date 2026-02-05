"""
MechanismDefinition entity for narrative mechanism configuration.

Represents a mechanism (e.g., irreversibility, network_effect) that can be
configured by users via narrative dropdowns.

References:
    - Spec: specs/039-narrative-mechanism-config/spec.md
    - Data model: specs/039-narrative-mechanism-config/data-model.md
"""

import secrets
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


def generate_mechanism_definition_id() -> str:
    """Generate a mechanism definition ID with mech_ prefix and 8-char hex suffix."""
    return f"mech_{secrets.token_hex(4)}"


class MechanismOption(BaseModel):
    """A text option for a mechanism with a mapped numeric value.

    Attributes:
        id: Unique option identifier (UUID)
        label: Display text for the option (e.g., "totalmente reversível")
        value: Numeric value mapped to this option [0.0, 1.0]
        display_order: Order in dropdown (ascending)
    """

    id: str = Field(..., description="Unique option identifier (UUID)")
    label: str = Field(..., max_length=100, description="Display text for the option")
    value: float = Field(..., ge=0.0, le=1.0, description="Numeric value [0.0, 1.0]")
    display_order: int = Field(..., ge=1, description="Order in dropdown (ascending)")


class MechanismDefinition(BaseModel):
    """Defines a mechanism that can be configured via narrative dropdowns.

    Attributes:
        id: Unique mechanism identifier (UUID)
        key: Programmatic key (e.g., "irreversibility")
        label_pt: Portuguese label for display
        description: Explanation of what this mechanism measures
        options: Available text options for this mechanism
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: str = Field(
        default_factory=generate_mechanism_definition_id,
        description="Unique mechanism identifier",
    )
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
    options: list[MechanismOption] = Field(
        default_factory=list,
        description="Available text options for this mechanism",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp (UTC)",
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Last update timestamp (UTC)",
    )

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
        }
