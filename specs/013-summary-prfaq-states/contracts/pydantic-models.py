"""
Pydantic model definitions for Summary and PR-FAQ State Management.

Feature Branch: 013-summary-prfaq-states
Date: 2025-12-21

These models should be added to src/synth_lab/api/schemas/
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================


class ArtifactStateEnum(str, Enum):
    """Current state of an artifact (summary or PR-FAQ)."""

    UNAVAILABLE = "unavailable"
    GENERATING = "generating"
    AVAILABLE = "available"
    FAILED = "failed"


class ArtifactType(str, Enum):
    """Type of artifact."""

    SUMMARY = "summary"
    PRFAQ = "prfaq"


class PRFAQStatus(str, Enum):
    """PR-FAQ generation status."""

    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


# =============================================================================
# Response Models
# =============================================================================


class ArtifactState(BaseModel):
    """State information for a single artifact."""

    artifact_type: ArtifactType = Field(description="Type of artifact")
    state: ArtifactStateEnum = Field(description="Current state")
    can_generate: bool = Field(
        default=False, description="Whether generate action is available"
    )
    can_view: bool = Field(
        default=False, description="Whether view action is available"
    )
    prerequisite_met: bool = Field(
        default=True, description="Whether prerequisites are satisfied"
    )
    prerequisite_message: Optional[str] = Field(
        default=None, description="Message if prerequisite not met"
    )
    error_message: Optional[str] = Field(
        default=None, description="Last error message if failed"
    )
    started_at: Optional[datetime] = Field(
        default=None, description="Generation start timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="Generation completion timestamp"
    )


class ArtifactStatesResponse(BaseModel):
    """Response from GET /research/{exec_id}/artifacts."""

    exec_id: str = Field(description="Research execution ID")
    summary: ArtifactState = Field(description="Summary artifact state")
    prfaq: ArtifactState = Field(description="PR-FAQ artifact state")


class PRFAQGenerateRequest(BaseModel):
    """Request body for POST /prfaq/generate."""

    exec_id: str = Field(description="Research execution ID")
    model: str = Field(
        default="gpt-4o-mini", description="LLM model to use for generation"
    )


class PRFAQGenerateResponse(BaseModel):
    """Response from POST /prfaq/generate."""

    exec_id: str = Field(description="Research execution ID")
    status: PRFAQStatus = Field(description="Current generation status")
    message: Optional[str] = Field(default=None, description="Status message")
    generated_at: Optional[datetime] = Field(
        default=None, description="Completion timestamp if completed"
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if failed"
    )


# =============================================================================
# Factory Functions
# =============================================================================


def compute_summary_state(
    execution_status: str,
    summary_content: Optional[str],
) -> ArtifactState:
    """
    Compute summary artifact state from execution data.

    Args:
        execution_status: Current execution status
        summary_content: Summary markdown content (nullable)

    Returns:
        ArtifactState for summary
    """
    from synth_lab.api.schemas.research import ExecutionStatus

    has_summary = summary_content is not None and len(summary_content) > 0

    if execution_status == ExecutionStatus.GENERATING_SUMMARY:
        state = ArtifactStateEnum.GENERATING
    elif has_summary:
        state = ArtifactStateEnum.AVAILABLE
    elif execution_status == ExecutionStatus.FAILED:
        state = ArtifactStateEnum.FAILED
    else:
        state = ArtifactStateEnum.UNAVAILABLE

    return ArtifactState(
        artifact_type=ArtifactType.SUMMARY,
        state=state,
        can_generate=False,  # Summary is auto-generated
        can_view=state == ArtifactStateEnum.AVAILABLE,
        prerequisite_met=True,  # No prerequisites for summary
    )


def compute_prfaq_state(
    summary_available: bool,
    prfaq_metadata: Optional[dict],
) -> ArtifactState:
    """
    Compute PR-FAQ artifact state from execution and prfaq data.

    Args:
        summary_available: Whether summary is available
        prfaq_metadata: PR-FAQ metadata row (nullable)

    Returns:
        ArtifactState for PR-FAQ
    """
    if prfaq_metadata is None:
        # No PR-FAQ record exists
        return ArtifactState(
            artifact_type=ArtifactType.PRFAQ,
            state=ArtifactStateEnum.UNAVAILABLE,
            can_generate=summary_available,
            can_view=False,
            prerequisite_met=summary_available,
            prerequisite_message=(
                "Summary necessario para gerar PR-FAQ" if not summary_available else None
            ),
        )

    status = prfaq_metadata.get("status", "completed")
    error_message = prfaq_metadata.get("error_message")
    started_at = prfaq_metadata.get("started_at")
    generated_at = prfaq_metadata.get("generated_at")

    if status == PRFAQStatus.GENERATING.value:
        state = ArtifactStateEnum.GENERATING
    elif status == PRFAQStatus.FAILED.value:
        state = ArtifactStateEnum.FAILED
    else:
        state = ArtifactStateEnum.AVAILABLE

    return ArtifactState(
        artifact_type=ArtifactType.PRFAQ,
        state=state,
        can_generate=state in (ArtifactStateEnum.UNAVAILABLE, ArtifactStateEnum.FAILED)
        and summary_available,
        can_view=state == ArtifactStateEnum.AVAILABLE,
        prerequisite_met=summary_available,
        prerequisite_message=(
            "Summary necessario para gerar PR-FAQ" if not summary_available else None
        ),
        error_message=error_message,
        started_at=started_at,
        completed_at=generated_at,
    )
