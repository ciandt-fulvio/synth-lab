"""Pydantic schemas for sharing API endpoints."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class ShareExperimentRequest(BaseModel):
    """Request to share an experiment with a user."""

    user_id: str = Field(..., description="UUID of user to share with")
    permission_level: str = Field(
        ...,
        description="Permission level: 'viewer' or 'editor'",
    )

    @field_validator("permission_level")
    @classmethod
    def validate_permission_level(cls, v: str) -> str:
        """Validate permission level is valid."""
        if v not in ["viewer", "editor"]:
            raise ValueError("permission_level must be 'viewer' or 'editor'")
        return v


class ShareResponse(BaseModel):
    """Response for share operations."""

    share_id: str = Field(..., description="UUID of the share")
    experiment_id: str = Field(..., description="Experiment ID")
    user_id: str = Field(..., description="User ID who received access")
    email: Optional[str] = Field(None, description="Email of user who received access")
    display_name: Optional[str] = Field(None, description="Display name of user")
    profile_picture_url: Optional[str] = Field(None, description="Profile picture URL")
    permission_level: str = Field(..., description="Permission level granted")
    granted_at: str = Field(..., description="ISO 8601 timestamp when access was granted")
    granted_by_id: str = Field(..., description="UUID of user who granted access")


class ShareListResponse(BaseModel):
    """Response listing all shares for an experiment."""

    experiment_id: str = Field(..., description="Experiment ID")
    shares: list[ShareResponse] = Field(..., description="List of shares")
