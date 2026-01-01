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
    """Document types for API."""

    SUMMARY = "summary"
    PRFAQ = "prfaq"
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
    status: DocumentStatusEnum = Field(description="Current status")
    generated_at: datetime = Field(description="Generation timestamp")
    model: str = Field(description="LLM model used")


class DocumentDetailResponse(BaseModel):
    """Full document response."""

    id: str = Field(description="Document ID")
    experiment_id: str = Field(description="Parent experiment ID")
    document_type: DocumentTypeEnum = Field(description="Type of document")
    markdown_content: str = Field(description="Full markdown content")
    metadata: dict | None = Field(default=None, description="Type-specific metadata")
    generated_at: datetime = Field(description="Generation timestamp")
    model: str = Field(description="LLM model used")
    status: DocumentStatusEnum = Field(description="Current status")
    error_message: str | None = Field(default=None, description="Error if failed")


class DocumentAvailabilityResponse(BaseModel):
    """Document availability status."""

    summary: dict = Field(description="Summary availability")
    prfaq: dict = Field(description="PRFAQ availability")
    executive_summary: dict = Field(description="Executive Summary availability")


class GenerateDocumentRequest(BaseModel):
    """Request to generate a document."""

    model: str = Field(default="gpt-4o-mini", description="LLM model to use")


class GenerateDocumentResponse(BaseModel):
    """Response after starting document generation."""

    document_id: str | None = Field(description="Document ID if generation started")
    status: DocumentStatusEnum = Field(description="Current status")
    message: str = Field(description="Status message")
