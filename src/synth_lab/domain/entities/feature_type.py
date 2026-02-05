"""
FeatureType entity for narrative mechanism configuration.

Categorizes features (e.g., financial, social) and specifies which mechanisms
are amplified for that type.

References:
    - Spec: specs/039-narrative-mechanism-config/spec.md
    - Data model: specs/039-narrative-mechanism-config/data-model.md
"""

import secrets
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


def generate_feature_type_id() -> str:
    """Generate a feature type ID with ft_ prefix and 8-char hex suffix."""
    return f"ft_{secrets.token_hex(4)}"


class FeatureType(BaseModel):
    """Categorizes features and specifies amplified mechanisms.

    Attributes:
        id: Unique feature type identifier (UUID)
        key: Programmatic key (e.g., "financial")
        label_pt: Portuguese label for display
        description: Description of this feature type
        amplifies_mechanisms: List of mechanism keys this type amplifies
        created_at: Creation timestamp
    """

    id: str = Field(
        default_factory=generate_feature_type_id,
        description="Unique feature type identifier",
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
    description: Optional[str] = Field(
        default=None,
        description="Description of this feature type",
    )
    amplifies_mechanisms: list[str] = Field(
        default_factory=list,
        description="List of mechanism keys this type amplifies",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp (UTC)",
    )

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
        }
