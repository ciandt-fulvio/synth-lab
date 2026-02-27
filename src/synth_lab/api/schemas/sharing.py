"""Pydantic schemas for sharing API endpoints."""
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ShareByEmailRequest(BaseModel):
    """Request to share a resource with a user by email."""

    email: str = Field(..., description="Email of user to share with")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate and normalize email."""
        v = v.lower().strip()
        if not v or "@" not in v:
            raise ValueError("Invalid email address")
        return v


class ShareExperimentRequest(BaseModel):
    """Request to share an experiment with a user (legacy, by user_id)."""

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


class ShareResultResponse(BaseModel):
    """Response for share-by-email operations."""

    status: str = Field(..., description="'shared' (active) or 'pending' (invite)")
    email: str = Field(..., description="Email of invited user")
    permission_level: str = Field(default="editor", description="Permission level")
    share_id: Optional[str] = Field(None, description="Share ID (if active)")
    invite_id: Optional[str] = Field(None, description="Invite ID (if pending)")
    user_id: Optional[str] = Field(None, description="User ID (if active)")
    granted_at: Optional[str] = Field(None, description="Timestamp (if active)")
    created_at: Optional[str] = Field(None, description="Timestamp (if pending)")


class ActiveShareItem(BaseModel):
    """An active share (user has account)."""

    share_id: str
    user_id: str
    email: str
    display_name: Optional[str] = None
    profile_picture_url: Optional[str] = None
    permission_level: str = "editor"
    granted_at: str
    status: str = "active"


class PendingInviteItem(BaseModel):
    """A pending invite (user hasn't registered yet)."""

    invite_id: str
    email: str
    permission_level: str = "editor"
    created_at: str
    status: str = "pending"


class ShareListResponse(BaseModel):
    """Response listing all shares and pending invites for a resource."""

    resource_id: str = Field(..., description="Resource ID")
    shares: list[ActiveShareItem] = Field(default_factory=list)
    pending: list[PendingInviteItem] = Field(default_factory=list)


# Legacy response (kept for backward compat)
class ShareResponse(BaseModel):
    """Response for share operations (legacy)."""

    share_id: str = Field(..., description="UUID of the share")
    experiment_id: str = Field(..., description="Experiment ID")
    user_id: str = Field(..., description="User ID who received access")
    email: Optional[str] = Field(None, description="Email of user who received access")
    display_name: Optional[str] = Field(None, description="Display name of user")
    profile_picture_url: Optional[str] = Field(None, description="Profile picture URL")
    permission_level: str = Field(..., description="Permission level granted")
    granted_at: str = Field(..., description="ISO 8601 timestamp when access was granted")
    granted_by_id: str = Field(..., description="UUID of user who granted access")
