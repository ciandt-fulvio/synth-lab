"""
API schemas for experiment documents.

Pydantic models for request/response serialization.

References:
    - Entity: synth_lab.domain.entities.experiment_document
    - Router: synth_lab.api.routers.documents
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class DocumentTypeEnum(str, Enum):
    """Document types for API.

    Types are specific to their source:
    - EXPLORATION_*: Generated from exploration winning path
    - RESEARCH_*: Generated from interview research data
    - EXECUTIVE_SUMMARY: Experiment-level summary combining all data
    """

    # Exploration documents
    EXPLORATION_SUMMARY = "exploration_summary"
    EXPLORATION_PRFAQ = "exploration_prfaq"

    # Research documents (from interviews)
    RESEARCH_SUMMARY = "research_summary"
    RESEARCH_PRFAQ = "research_prfaq"

    # Experiment-level documents
    EXECUTIVE_SUMMARY = "executive_summary"


class DocumentStatusEnum(str, Enum):
    """Document status for API."""

    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class DocumentSummaryResponse(BaseModel):
    """Summary response for document listing."""

    id: str = Field(description="Document ID")
    document_type: DocumentTypeEnum = Field(description="Type of document")
    source_id: str | None = Field(
        default=None,
        description="Source ID (exploration_id or exec_id)"
    )
    status: DocumentStatusEnum = Field(description="Current status")
    generated_at: datetime = Field(description="Generation timestamp")
    model: str = Field(description="LLM model used")


class DocumentDetailResponse(BaseModel):
    """Full document response."""

    id: str = Field(description="Document ID")
    experiment_id: str = Field(description="Parent experiment ID")
    document_type: DocumentTypeEnum = Field(description="Type of document")
    source_id: str | None = Field(
        default=None,
        description="Source ID (exploration_id or exec_id)"
    )
    markdown_content: str = Field(description="Full markdown content")
    metadata: dict | None = Field(default=None, description="Type-specific metadata")
    generated_at: datetime = Field(description="Generation timestamp")
    model: str = Field(description="LLM model used")
    status: DocumentStatusEnum = Field(description="Current status")
    error_message: str | None = Field(default=None, description="Error if failed")


class DocumentAvailabilityStatus(BaseModel):
    """Availability status for a single document type."""

    available: bool = Field(description="Whether document is available (completed)")
    status: str | None = Field(
        description="Current status (generating, completed, failed, etc.)"
    )
    generated_at: str | None = Field(
        default=None, description="ISO timestamp when document was generated"
    )


class DocumentAvailabilityResponse(BaseModel):
    """Document availability status for all document types."""

    # Exploration documents
    exploration_summary: DocumentAvailabilityStatus = Field(
        description="Exploration Summary availability"
    )
    exploration_prfaq: DocumentAvailabilityStatus = Field(
        description="Exploration PRFAQ availability"
    )

    # Research documents (from interviews)
    research_summary: DocumentAvailabilityStatus = Field(
        description="Research Summary availability"
    )
    research_prfaq: DocumentAvailabilityStatus = Field(
        description="Research PRFAQ availability"
    )

    # Experiment-level documents
    executive_summary: DocumentAvailabilityStatus = Field(
        description="Executive Summary availability"
    )


class GenerateDocumentRequest(BaseModel):
    """Request to generate a document."""

    model: str = Field(default="gpt-4o-mini", description="LLM model to use")
    source_id: str | None = Field(
        default=None,
        description="Source ID (exploration_id or exec_id)"
    )


class GenerateDocumentResponse(BaseModel):
    """Response after starting document generation."""

    document_id: str | None = Field(description="Document ID if generation started")
    status: DocumentStatusEnum = Field(description="Current status")
    message: str = Field(description="Status message")
