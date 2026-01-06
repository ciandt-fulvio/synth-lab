"""
ExperimentMaterial entity for synth-lab.

Represents a file (image, video, document) attached to an experiment
for synth interview context.

References:
    - data-model.md: ExperimentMaterial entity definition
    - Plan: specs/001-experiment-materials/plan.md
"""

import secrets
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class FileType(str, Enum):
    """Type of uploaded file.

    - IMAGE: PNG, JPG, JPEG, WebP, GIF
    - VIDEO: MP4, MOV, WebM
    - DOCUMENT: PDF, TXT, MD
    """

    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"


class MaterialType(str, Enum):
    """Category/purpose of the material.

    - DESIGN: Wireframes, mockups, final designs
    - PROTOTYPE: Interactive prototypes, demos
    - COMPETITOR: Competitor analysis
    - SPEC: Specifications, documentation
    - OTHER: Other materials
    """

    DESIGN = "design"
    PROTOTYPE = "prototype"
    COMPETITOR = "competitor"
    SPEC = "spec"
    OTHER = "other"


class DescriptionStatus(str, Enum):
    """Status of AI-generated description."""

    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


# MIME type to FileType mapping
MIME_TYPE_MAP: dict[str, FileType] = {
    # Images
    "image/png": FileType.IMAGE,
    "image/jpeg": FileType.IMAGE,
    "image/jpg": FileType.IMAGE,
    "image/webp": FileType.IMAGE,
    "image/gif": FileType.IMAGE,
    # Videos
    "video/mp4": FileType.VIDEO,
    "video/quicktime": FileType.VIDEO,
    "video/webm": FileType.VIDEO,
    # Documents
    "application/pdf": FileType.DOCUMENT,
    "text/plain": FileType.DOCUMENT,
    "text/markdown": FileType.DOCUMENT,
}


def generate_material_id() -> str:
    """
    Generate a unique material ID.

    Returns:
        str: Material ID in format 'mat_XXXXXXXXXXXX' (12 hex chars).

    Example:
        >>> mat_id = generate_material_id()
        >>> mat_id.startswith('mat_')
        True
        >>> len(mat_id)
        16
    """
    return f"mat_{secrets.token_hex(6)}"


def get_file_type_from_mime(mime_type: str) -> FileType | None:
    """
    Get FileType from MIME type.

    Args:
        mime_type: MIME type string (e.g., "image/png").

    Returns:
        FileType or None if not supported.
    """
    return MIME_TYPE_MAP.get(mime_type)


class ExperimentMaterial(BaseModel):
    """
    Material file attached to an experiment.

    Stores metadata for images, videos, and documents uploaded by researchers
    for synth interview context. Actual files are stored in S3.

    Attributes:
        id: Unique material ID (mat_XXXXXXXXXXXX format).
        experiment_id: Parent experiment ID.
        file_type: Category - image, video, or document.
        file_url: Full S3 URL of the uploaded file.
        thumbnail_url: Optional S3 URL of generated thumbnail.
        file_name: Original filename.
        file_size: File size in bytes.
        mime_type: MIME type (e.g., "image/png").
        material_type: Purpose - design, prototype, competitor, spec, other.
        description: AI-generated description (up to 30 words).
        description_status: pending, generating, completed, failed.
        display_order: Order for display (0-indexed).
        created_at: Timestamp when material was created.
    """

    id: str = Field(
        default_factory=generate_material_id,
        pattern=r"^mat_[a-f0-9]{12}$",
        description="Material ID in format mat_XXXXXXXXXXXX",
    )
    experiment_id: str = Field(
        pattern=r"^exp_[a-f0-9]{8}$",
        description="Parent experiment ID",
    )
    file_type: FileType = Field(
        description="Type of file: image, video, or document",
    )
    file_url: str = Field(
        description="Full S3 URL of the uploaded file",
    )
    thumbnail_url: str | None = Field(
        default=None,
        description="S3 URL of generated thumbnail",
    )
    file_name: str = Field(
        max_length=255,
        description="Original filename",
    )
    file_size: int = Field(
        gt=0,
        description="File size in bytes",
    )
    mime_type: str = Field(
        description="MIME type of the file",
    )
    material_type: MaterialType = Field(
        description="Purpose/category of the material",
    )
    description: str | None = Field(
        default=None,
        description="AI-generated description (max 30 words)",
    )
    description_status: DescriptionStatus = Field(
        default=DescriptionStatus.PENDING,
        description="Status of description generation",
    )
    display_order: int = Field(
        ge=0,
        description="Order for display (0-indexed)",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when material was created",
    )

    @field_validator("file_size")
    @classmethod
    def validate_file_size(cls, v: int) -> int:
        """Validate file size doesn't exceed absolute maximum."""
        max_size = 104_857_600  # 100MB absolute max
        if v > max_size:
            raise ValueError(f"File size {v} exceeds maximum {max_size}")
        return v

    def to_db_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary for database storage.

        Returns:
            dict: Database-ready dictionary with serialized fields.
        """
        return {
            "id": self.id,
            "experiment_id": self.experiment_id,
            "file_type": self.file_type.value,
            "file_url": self.file_url,
            "thumbnail_url": self.thumbnail_url,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "material_type": self.material_type.value,
            "description": self.description,
            "description_status": self.description_status.value,
            "display_order": self.display_order,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> "ExperimentMaterial":
        """
        Create from database row.

        Args:
            row: Database row as dictionary.

        Returns:
            ExperimentMaterial: Parsed material entity.
        """
        created_at = row["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        return cls(
            id=row["id"],
            experiment_id=row["experiment_id"],
            file_type=FileType(row["file_type"]),
            file_url=row["file_url"],
            thumbnail_url=row.get("thumbnail_url"),
            file_name=row["file_name"],
            file_size=row["file_size"],
            mime_type=row["mime_type"],
            material_type=MaterialType(row["material_type"]),
            description=row.get("description"),
            description_status=DescriptionStatus(row.get("description_status", "pending")),
            display_order=row["display_order"],
            created_at=created_at,
        )


class ExperimentMaterialSummary(BaseModel):
    """
    Summary view of a material for listing.

    Lightweight representation for gallery displays.
    """

    id: str = Field(description="Material ID")
    file_type: FileType = Field(description="Type of file")
    file_name: str = Field(description="Original filename")
    file_size: int = Field(description="File size in bytes")
    thumbnail_url: str | None = Field(default=None, description="Thumbnail URL")
    material_type: MaterialType = Field(description="Purpose/category")
    description: str | None = Field(default=None, description="AI description")
    description_status: DescriptionStatus = Field(description="Description status")
    display_order: int = Field(description="Display order")

    @classmethod
    def from_material(cls, material: ExperimentMaterial) -> "ExperimentMaterialSummary":
        """Create summary from full material."""
        return cls(
            id=material.id,
            file_type=material.file_type,
            file_name=material.file_name,
            file_size=material.file_size,
            thumbnail_url=material.thumbnail_url,
            material_type=material.material_type,
            description=material.description,
            description_status=material.description_status,
            display_order=material.display_order,
        )


# Material type display names (Portuguese)
MATERIAL_TYPE_LABELS: dict[MaterialType, str] = {
    MaterialType.DESIGN: "Design",
    MaterialType.PROTOTYPE: "Protótipo",
    MaterialType.COMPETITOR: "Concorrente",
    MaterialType.SPEC: "Especificação",
    MaterialType.OTHER: "Outro",
}


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Generate material ID
    total_tests += 1
    try:
        mat_id = generate_material_id()
        if not mat_id.startswith("mat_"):
            all_validation_failures.append(f"ID should start with 'mat_': {mat_id}")
        if len(mat_id) != 16:
            all_validation_failures.append(f"ID should be 16 chars: {len(mat_id)}")
    except Exception as e:
        all_validation_failures.append(f"Generate material ID failed: {e}")

    # Test 2: Create material with required fields
    total_tests += 1
    try:
        material = ExperimentMaterial(
            id="mat_1234567890ab",
            experiment_id="exp_12345678",
            file_type=FileType.IMAGE,
            file_url="https://storage.railway.app/attachments/test.png",
            file_name="test.png",
            file_size=1024,
            mime_type="image/png",
            material_type=MaterialType.DESIGN,
            display_order=0,
        )
        if material.description_status != DescriptionStatus.PENDING:
            all_validation_failures.append(
                f"Default status should be PENDING: {material.description_status}"
            )
        if material.description is not None:
            all_validation_failures.append("Default description should be None")
    except Exception as e:
        all_validation_failures.append(f"Create material failed: {e}")

    # Test 3: File type enum values
    total_tests += 1
    try:
        expected_types = ["image", "video", "document"]
        actual_types = [t.value for t in FileType]
        if set(actual_types) != set(expected_types):
            all_validation_failures.append(
                f"FileType values mismatch: {actual_types} vs {expected_types}"
            )
    except Exception as e:
        all_validation_failures.append(f"FileType enum test failed: {e}")

    # Test 4: Material type enum values
    total_tests += 1
    try:
        expected_types = ["design", "prototype", "competitor", "spec", "other"]
        actual_types = [t.value for t in MaterialType]
        if set(actual_types) != set(expected_types):
            all_validation_failures.append(
                f"MaterialType values mismatch: {actual_types} vs {expected_types}"
            )
    except Exception as e:
        all_validation_failures.append(f"MaterialType enum test failed: {e}")

    # Test 5: Description status enum values
    total_tests += 1
    try:
        expected_statuses = ["pending", "generating", "completed", "failed"]
        actual_statuses = [s.value for s in DescriptionStatus]
        if set(actual_statuses) != set(expected_statuses):
            all_validation_failures.append(
                f"DescriptionStatus values mismatch: {actual_statuses} vs {expected_statuses}"
            )
    except Exception as e:
        all_validation_failures.append(f"DescriptionStatus enum test failed: {e}")

    # Test 6: to_db_dict and from_db_row roundtrip
    total_tests += 1
    try:
        original = ExperimentMaterial(
            id="mat_abcdef123456",
            experiment_id="exp_12345678",
            file_type=FileType.VIDEO,
            file_url="https://storage.railway.app/attachments/video.mp4",
            thumbnail_url="https://storage.railway.app/attachments/video_thumb.jpg",
            file_name="demo_video.mp4",
            file_size=50_000_000,
            mime_type="video/mp4",
            material_type=MaterialType.PROTOTYPE,
            description="Video showing prototype interaction",
            description_status=DescriptionStatus.COMPLETED,
            display_order=2,
        )
        db_dict = original.to_db_dict()
        restored = ExperimentMaterial.from_db_row(db_dict)

        if restored.id != original.id:
            all_validation_failures.append(f"ID mismatch: {restored.id} != {original.id}")
        if restored.file_type != original.file_type:
            all_validation_failures.append("File type mismatch")
        if restored.material_type != original.material_type:
            all_validation_failures.append("Material type mismatch")
        if restored.description != original.description:
            all_validation_failures.append("Description mismatch after roundtrip")
        if restored.thumbnail_url != original.thumbnail_url:
            all_validation_failures.append("Thumbnail URL mismatch")
    except Exception as e:
        all_validation_failures.append(f"Roundtrip test failed: {e}")

    # Test 7: get_file_type_from_mime
    total_tests += 1
    try:
        test_cases = [
            ("image/png", FileType.IMAGE),
            ("image/jpeg", FileType.IMAGE),
            ("video/mp4", FileType.VIDEO),
            ("video/webm", FileType.VIDEO),
            ("application/pdf", FileType.DOCUMENT),
            ("text/markdown", FileType.DOCUMENT),
            ("unknown/type", None),
        ]
        for mime, expected in test_cases:
            result = get_file_type_from_mime(mime)
            if result != expected:
                all_validation_failures.append(
                    f"MIME mapping failed for {mime}: {result} != {expected}"
                )
    except Exception as e:
        all_validation_failures.append(f"MIME type mapping test failed: {e}")

    # Test 8: ExperimentMaterialSummary
    total_tests += 1
    try:
        material = ExperimentMaterial(
            id="mat_1234567890ab",
            experiment_id="exp_12345678",
            file_type=FileType.DOCUMENT,
            file_url="https://storage.railway.app/attachments/spec.pdf",
            file_name="specification.pdf",
            file_size=2_000_000,
            mime_type="application/pdf",
            material_type=MaterialType.SPEC,
            display_order=1,
        )
        summary = ExperimentMaterialSummary.from_material(material)
        if summary.id != material.id:
            all_validation_failures.append("Summary ID mismatch")
        if summary.file_type != material.file_type:
            all_validation_failures.append("Summary file_type mismatch")
        if summary.material_type != material.material_type:
            all_validation_failures.append("Summary material_type mismatch")
    except Exception as e:
        all_validation_failures.append(f"ExperimentMaterialSummary test failed: {e}")

    # Test 9: File size validation
    total_tests += 1
    try:
        # Should raise for file > 100MB
        try:
            ExperimentMaterial(
                id="mat_1234567890ab",
                experiment_id="exp_12345678",
                file_type=FileType.VIDEO,
                file_url="https://storage.railway.app/test.mp4",
                file_name="huge.mp4",
                file_size=200_000_000,  # 200MB - over limit
                mime_type="video/mp4",
                material_type=MaterialType.OTHER,
                display_order=0,
            )
            all_validation_failures.append(
                "Should have raised ValueError for file_size > 100MB"
            )
        except ValueError:
            # Expected - validation working
            pass
    except Exception as e:
        all_validation_failures.append(f"File size validation test failed: {e}")

    # Test 10: MATERIAL_TYPE_LABELS
    total_tests += 1
    try:
        if MATERIAL_TYPE_LABELS[MaterialType.DESIGN] != "Design":
            all_validation_failures.append("DESIGN label mismatch")
        if MATERIAL_TYPE_LABELS[MaterialType.PROTOTYPE] != "Protótipo":
            all_validation_failures.append("PROTOTYPE label mismatch")
        if MATERIAL_TYPE_LABELS[MaterialType.SPEC] != "Especificação":
            all_validation_failures.append("SPEC label mismatch")
    except Exception as e:
        all_validation_failures.append(f"Labels test failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(
            f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:"
        )
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("ExperimentMaterial entity is validated and ready for use")
        sys.exit(0)
