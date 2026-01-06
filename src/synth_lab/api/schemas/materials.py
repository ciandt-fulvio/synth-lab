"""
API schemas for experiment materials.

Pydantic models for request/response serialization.

References:
    - Entity: synth_lab.domain.entities.experiment_material
    - Router: synth_lab.api.routers.materials
    - OpenAPI: specs/001-experiment-materials/contracts/materials-api.yaml
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class FileTypeEnum(str, Enum):
    """File type for API."""

    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"


class MaterialTypeEnum(str, Enum):
    """Material type/purpose for API."""

    DESIGN = "design"
    PROTOTYPE = "prototype"
    COMPETITOR = "competitor"
    SPEC = "spec"
    OTHER = "other"


class DescriptionStatusEnum(str, Enum):
    """Description status for API."""

    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


# Request schemas


class MaterialUploadRequest(BaseModel):
    """Request for presigned upload URL."""

    file_name: str = Field(max_length=255, description="Original filename")
    file_size: int = Field(
        gt=0, le=104_857_600, description="File size in bytes (max 100MB)"
    )
    mime_type: str = Field(description="MIME type of the file")
    material_type: MaterialTypeEnum = Field(description="Purpose/category of material")


class MaterialConfirmRequest(BaseModel):
    """Confirm upload completion."""

    material_id: str = Field(description="Material ID from upload request")
    object_key: str = Field(description="S3 object key from upload")


class MaterialReorderRequest(BaseModel):
    """Request to reorder materials."""

    material_ids: list[str] = Field(
        description="Material IDs in the new display order"
    )


# Response schemas


class MaterialUploadResponse(BaseModel):
    """Response with presigned URL for upload."""

    material_id: str = Field(description="Material ID for confirmation")
    upload_url: str = Field(description="Presigned S3 URL for PUT upload")
    object_key: str = Field(description="S3 object key")
    expires_in: int = Field(description="URL expiration time in seconds")


class MaterialResponse(BaseModel):
    """Material data for API responses."""

    id: str = Field(description="Material ID")
    experiment_id: str = Field(description="Parent experiment ID")
    file_type: FileTypeEnum = Field(description="Type of file")
    file_url: str = Field(description="S3 URL of the file")
    thumbnail_url: str | None = Field(default=None, description="S3 URL of thumbnail")
    file_name: str = Field(description="Original filename")
    file_size: int = Field(description="File size in bytes")
    mime_type: str = Field(description="MIME type")
    material_type: MaterialTypeEnum = Field(description="Purpose/category")
    description: str | None = Field(default=None, description="AI-generated description")
    description_status: DescriptionStatusEnum = Field(
        description="Status of description generation"
    )
    display_order: int = Field(description="Display order (0-indexed)")
    created_at: datetime = Field(description="Creation timestamp")


class MaterialSummaryResponse(BaseModel):
    """Material summary for listing (without full URLs)."""

    id: str = Field(description="Material ID")
    file_type: FileTypeEnum = Field(description="Type of file")
    file_name: str = Field(description="Original filename")
    file_size: int = Field(description="File size in bytes")
    thumbnail_url: str | None = Field(default=None, description="Thumbnail URL")
    material_type: MaterialTypeEnum = Field(description="Purpose/category")
    description: str | None = Field(default=None, description="AI description")
    description_status: DescriptionStatusEnum = Field(description="Description status")
    display_order: int = Field(description="Display order")


class MaterialListResponse(BaseModel):
    """Response for listing materials."""

    materials: list[MaterialSummaryResponse] = Field(description="List of materials")
    total: int = Field(description="Total number of materials")
    total_size: int = Field(description="Total file size in bytes")


class MaterialViewUrlResponse(BaseModel):
    """Response with presigned view URL."""

    material_id: str = Field(description="Material ID")
    view_url: str = Field(description="Presigned S3 URL for viewing")
    thumbnail_url: str | None = Field(default=None, description="Thumbnail URL")
    expires_in: int = Field(description="URL expiration time in seconds")


class RetryDescriptionResponse(BaseModel):
    """Response after retrying description generation."""

    material_id: str = Field(description="Material ID")
    status: DescriptionStatusEnum = Field(description="New status")
    message: str = Field(description="Status message")


class MaterialLimitsResponse(BaseModel):
    """Response with current usage and limits."""

    current_count: int = Field(description="Current number of materials")
    max_count: int = Field(description="Maximum allowed materials")
    current_size: int = Field(description="Current total size in bytes")
    max_size: int = Field(description="Maximum total size in bytes")
    can_upload: bool = Field(description="Whether more materials can be uploaded")


# Display labels (Portuguese)
MATERIAL_TYPE_LABELS: dict[MaterialTypeEnum, str] = {
    MaterialTypeEnum.DESIGN: "Design",
    MaterialTypeEnum.PROTOTYPE: "Protótipo",
    MaterialTypeEnum.COMPETITOR: "Concorrente",
    MaterialTypeEnum.SPEC: "Especificação",
    MaterialTypeEnum.OTHER: "Outro",
}

FILE_TYPE_LABELS: dict[FileTypeEnum, str] = {
    FileTypeEnum.IMAGE: "Imagem",
    FileTypeEnum.VIDEO: "Vídeo",
    FileTypeEnum.DOCUMENT: "Documento",
}
