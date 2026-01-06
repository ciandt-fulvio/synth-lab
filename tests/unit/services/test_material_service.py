"""
Unit tests for MaterialService.

Tests material upload flow, confirmation, and limit validation.

References:
    - Service: src/synth_lab/services/material_service.py
    - Repository: src/synth_lab/repositories/experiment_material_repository.py
    - Spec: specs/001-experiment-materials/spec.md
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from synth_lab.domain.entities.experiment_material import (
    DescriptionStatus,
    ExperimentMaterial,
    FileType,
    MaterialType,
)
from synth_lab.repositories.experiment_material_repository import (
    MaterialLimitExceededError,
    MaterialNotFoundError,
)
from synth_lab.services.material_service import (
    FileSizeLimitError,
    MaterialService,
    UnsupportedFileTypeError,
)


@pytest.fixture
def mock_repository():
    """Mock material repository for testing."""
    return MagicMock()


@pytest.fixture
def material_service(mock_repository):
    """Create MaterialService with mocked repository."""
    return MaterialService(repository=mock_repository)


@pytest.fixture
def sample_material():
    """Sample material entity for testing."""
    return ExperimentMaterial(
        id="mat_a1b2c3d4e5f6",  # Valid format: mat_ + 12 hex chars
        experiment_id="exp_abc12345",  # Valid format: exp_ + 8 hex chars
        file_type=FileType.IMAGE,
        file_url="https://s3.endpoint.com/bucket/materials/exp_abc12345/mat_a1b2c3d4e5f6.png",
        file_name="test.png",
        file_size=1024000,
        mime_type="image/png",
        material_type=MaterialType.DESIGN,
        description_status=DescriptionStatus.PENDING,
        display_order=0,
        created_at=datetime.now(timezone.utc),
    )


class TestRequestUploadUrl:
    """Test request_upload_url method (T013)."""

    @patch("synth_lab.services.material_service.generate_upload_url")
    @patch("synth_lab.services.material_service.generate_material_id")
    def test_creates_presigned_url_for_valid_file(
        self, mock_gen_id, mock_gen_url, material_service, mock_repository
    ):
        """Should create presigned URL and pending material record for valid file."""
        mock_gen_id.return_value = "mat_a1b2c3d4e5f6"
        mock_gen_url.return_value = "https://presigned-url.com/upload"
        mock_repository.get_next_display_order.return_value = 0
        mock_repository.count_by_experiment.return_value = 0
        mock_repository.get_total_size_by_experiment.return_value = 0

        result = material_service.request_upload_url(
            experiment_id="exp_abc12345",
            file_name="test.png",
            file_size=1024000,
            mime_type="image/png",
            material_type=MaterialType.DESIGN,
        )

        # Should return upload URL data
        assert result["material_id"] == "mat_a1b2c3d4e5f6"
        assert result["upload_url"] == "https://presigned-url.com/upload"
        assert "object_key" in result
        assert "materials/exp_abc12345/mat_a1b2c3d4e5f6.png" in result["object_key"]
        assert "expires_in" in result

        # Should create material record
        mock_repository.create.assert_called_once()
        created_material = mock_repository.create.call_args[0][0]
        assert created_material.id == "mat_a1b2c3d4e5f6"
        assert created_material.experiment_id == "exp_abc12345"
        assert created_material.file_name == "test.png"
        assert created_material.file_size == 1024000
        assert created_material.file_type == FileType.IMAGE
        assert created_material.description_status == DescriptionStatus.PENDING

    @patch("synth_lab.services.material_service.generate_upload_url")
    @patch("synth_lab.services.material_service.generate_material_id")
    def test_handles_different_file_types(
        self, mock_gen_id, mock_gen_url, material_service, mock_repository
    ):
        """Should handle images, videos, and documents."""
        mock_gen_id.return_value = "mat_fedcba987654"
        mock_gen_url.return_value = "https://presigned.com"
        mock_repository.get_next_display_order.return_value = 0
        mock_repository.count_by_experiment.return_value = 0
        mock_repository.get_total_size_by_experiment.return_value = 0

        test_cases = [
            ("image/png", FileType.IMAGE, "test.png"),
            ("video/mp4", FileType.VIDEO, "test.mp4"),
            ("application/pdf", FileType.DOCUMENT, "test.pdf"),
        ]

        for mime_type, expected_type, file_name in test_cases:
            result = material_service.request_upload_url(
                experiment_id="exp_aabbccdd",
                file_name=file_name,
                file_size=1000000,
                mime_type=mime_type,
                material_type=MaterialType.DESIGN,
            )

            created_material = mock_repository.create.call_args[0][0]
            assert created_material.file_type == expected_type

    def test_rejects_unsupported_file_type(self, material_service, mock_repository):
        """Should raise UnsupportedFileTypeError for invalid MIME type."""
        mock_repository.count_by_experiment.return_value = 0
        mock_repository.get_total_size_by_experiment.return_value = 0

        with pytest.raises(UnsupportedFileTypeError) as exc_info:
            material_service.request_upload_url(
                experiment_id="exp_11223344",
                file_name="test.exe",
                file_size=1000000,
                mime_type="application/x-msdownload",
                material_type=MaterialType.OTHER,
            )

        assert "application/x-msdownload" in str(exc_info.value)

    def test_validates_file_size_limits(self, material_service, mock_repository):
        """Should reject files exceeding size limits (T015)."""
        mock_repository.count_by_experiment.return_value = 0
        mock_repository.get_total_size_by_experiment.return_value = 0

        # Image too large (>25MB)
        with pytest.raises(FileSizeLimitError) as exc_info:
            material_service.request_upload_url(
                experiment_id="exp_22334455",
                file_name="large.png",
                file_size=30_000_000,  # 30MB
                mime_type="image/png",
                material_type=MaterialType.DESIGN,
            )
        assert "30000000" in str(exc_info.value)

        # Video too large (>100MB)
        with pytest.raises(FileSizeLimitError):
            material_service.request_upload_url(
                experiment_id="exp_33445566",
                file_name="large.mp4",
                file_size=110_000_000,  # 110MB
                mime_type="video/mp4",
                material_type=MaterialType.PROTOTYPE,
            )

    def test_validates_experiment_material_count_limit(
        self, material_service, mock_repository
    ):
        """Should reject uploads when experiment reaches 10 materials (T015)."""
        # Mock repository to return 10 materials already
        mock_repository.count_by_experiment.return_value = 10
        mock_repository.get_total_size_by_experiment.return_value = 0

        with pytest.raises(MaterialLimitExceededError) as exc_info:
            material_service.request_upload_url(
                experiment_id="exp_44556677",
                file_name="test.png",
                file_size=1000000,
                mime_type="image/png",
                material_type=MaterialType.DESIGN,
            )

        assert "maximum" in str(exc_info.value).lower()

    def test_validates_experiment_total_size_limit(
        self, material_service, mock_repository
    ):
        """Should reject uploads when total size exceeds 250MB (T015)."""
        # Mock repository to return total size near limit
        mock_repository.count_by_experiment.return_value = 5
        mock_repository.get_total_size_by_experiment.return_value = 250_000_000  # 250MB

        with pytest.raises(MaterialLimitExceededError) as exc_info:
            material_service.request_upload_url(
                experiment_id="exp_55667788",
                file_name="test.png",
                file_size=20_000_000,  # Adding 20MB would exceed 250MB limit (total 270MB)
                mime_type="image/png",
                material_type=MaterialType.DESIGN,
            )

        assert "exceed" in str(exc_info.value).lower()


class TestConfirmUpload:
    """Test confirm_upload method (T014)."""

    @patch("synth_lab.services.material_service.check_object_exists")
    def test_confirms_upload_and_updates_material(
        self, mock_check_exists, material_service, mock_repository, sample_material
    ):
        """Should verify S3 object exists and update material with file URL."""
        mock_check_exists.return_value = True
        mock_repository.get_by_id.return_value = sample_material

        updated_material = ExperimentMaterial(
            **{**sample_material.__dict__, "file_url": "https://s3.endpoint.com/bucket/materials/exp_abc12345/mat_a1b2c3d4e5f6.png"}
        )
        mock_repository.get_by_id.side_effect = [sample_material, updated_material]

        # Mock thumbnail and description generation to avoid side effects
        with patch.object(material_service, 'generate_thumbnail'):
            with patch.object(material_service, 'generate_description'):
                result = material_service.confirm_upload(
                    experiment_id="exp_abc12345",
                    material_id="mat_a1b2c3d4e5f6",
                    object_key="materials/exp_abc12345/mat_a1b2c3d4e5f6.png",
                )

        # Should verify object exists in S3
        mock_check_exists.assert_called_once_with(
            "materials/exp_abc12345/mat_a1b2c3d4e5f6.png"
        )

        # Should update file URL
        mock_repository.update_file_url.assert_called_once()
        call_args = mock_repository.update_file_url.call_args[0]
        assert call_args[0] == "mat_a1b2c3d4e5f6"
        assert "materials/exp_abc12345/mat_a1b2c3d4e5f6.png" in call_args[1]

    @patch("synth_lab.services.material_service.check_object_exists")
    def test_raises_error_if_material_not_found(
        self, mock_check_exists, material_service, mock_repository
    ):
        """Should raise MaterialNotFoundError if material doesn't exist."""
        mock_repository.get_by_id.return_value = None

        with pytest.raises(MaterialNotFoundError) as exc_info:
            material_service.confirm_upload(
                experiment_id="exp_66778899",
                material_id="mat_000000000000",
                object_key="materials/exp_66778899/mat_000000000000.png",
            )

        assert "mat_000000000000" in str(exc_info.value)

    @patch("synth_lab.services.material_service.check_object_exists")
    def test_raises_error_if_object_not_in_s3(
        self, mock_check_exists, material_service, mock_repository, sample_material
    ):
        """Should raise ValueError if S3 object doesn't exist."""
        mock_check_exists.return_value = False
        mock_repository.get_by_id.return_value = sample_material

        with pytest.raises(ValueError) as exc_info:
            material_service.confirm_upload(
                experiment_id="exp_abc12345",
                material_id="mat_a1b2c3d4e5f6",
                object_key="materials/exp_abc12345/mat_a1b2c3d4e5f6.png",
            )

        assert "not found in S3" in str(exc_info.value)

    @patch("synth_lab.services.material_service.check_object_exists")
    def test_validates_material_belongs_to_experiment(
        self, mock_check_exists, material_service, mock_repository, sample_material
    ):
        """Should raise error if material doesn't belong to specified experiment."""
        mock_repository.get_by_id.return_value = sample_material

        with pytest.raises(ValueError) as exc_info:
            material_service.confirm_upload(
                experiment_id="exp_99887766",
                material_id="mat_a1b2c3d4e5f6",
                object_key="materials/exp_abc12345/mat_a1b2c3d4e5f6.png",
            )

        assert "does not belong" in str(exc_info.value)

    @patch("synth_lab.services.material_service.check_object_exists")
    def test_triggers_thumbnail_generation(
        self, mock_check_exists, material_service, mock_repository, sample_material
    ):
        """Should trigger thumbnail generation after confirmation."""
        mock_check_exists.return_value = True
        mock_repository.get_by_id.return_value = sample_material

        updated_material = ExperimentMaterial(
            **{**sample_material.__dict__, "file_url": "https://s3.endpoint.com/bucket/materials/exp_abc12345/mat_a1b2c3d4e5f6.png"}
        )
        mock_repository.get_by_id.side_effect = [sample_material, updated_material]

        with patch.object(material_service, 'generate_thumbnail') as mock_thumb:
            with patch.object(material_service, 'generate_description'):
                material_service.confirm_upload(
                    experiment_id="exp_abc12345",
                    material_id="mat_a1b2c3d4e5f6",
                    object_key="materials/exp_abc12345/mat_a1b2c3d4e5f6.png",
                )

        mock_thumb.assert_called_once_with("mat_a1b2c3d4e5f6")

    @patch("synth_lab.services.material_service.check_object_exists")
    def test_handles_thumbnail_generation_failure_gracefully(
        self, mock_check_exists, material_service, mock_repository, sample_material
    ):
        """Should not fail upload if thumbnail generation fails."""
        mock_check_exists.return_value = True
        mock_repository.get_by_id.return_value = sample_material

        updated_material = ExperimentMaterial(
            **{**sample_material.__dict__, "file_url": "https://s3.endpoint.com/bucket/materials/exp_abc12345/mat_a1b2c3d4e5f6.png"}
        )
        mock_repository.get_by_id.side_effect = [sample_material, updated_material]

        with patch.object(material_service, 'generate_thumbnail', side_effect=Exception("Thumbnail failed")):
            with patch.object(material_service, 'generate_description'):
                # Should not raise exception
                result = material_service.confirm_upload(
                    experiment_id="exp_abc12345",
                    material_id="mat_a1b2c3d4e5f6",
                    object_key="materials/exp_abc12345/mat_a1b2c3d4e5f6.png",
                )

        # Should still return material
        assert result is not None


class TestGetLimits:
    """Test get_limits method (T015)."""

    def test_returns_current_usage_and_limits(self, material_service, mock_repository):
        """Should return current count, size, and limits."""
        mock_repository.count_by_experiment.return_value = 3
        mock_repository.get_total_size_by_experiment.return_value = 50_000_000  # 50MB

        result = material_service.get_limits("exp_aabbccdd")

        assert result["current_count"] == 3
        assert result["current_size"] == 50_000_000
        assert result["max_count"] == 10  # From config
        assert result["max_size"] == 262_144_000  # 250MB from config
        assert result["can_upload"] is True

    def test_can_upload_false_when_limit_reached(
        self, material_service, mock_repository
    ):
        """Should set can_upload to False when limits reached."""
        # At count limit
        mock_repository.count_by_experiment.return_value = 10
        mock_repository.get_total_size_by_experiment.return_value = 100_000_000

        result = material_service.get_limits("exp_ddeeffaa")
        assert result["can_upload"] is False

        # At size limit
        mock_repository.count_by_experiment.return_value = 5
        mock_repository.get_total_size_by_experiment.return_value = 262_144_000

        result = material_service.get_limits("exp_bbccddee")
        assert result["can_upload"] is False


class TestThumbnailGeneration:
    """Test thumbnail generation methods (T036)."""

    @patch("synth_lab.services.material_service.get_object_bytes")
    @patch("synth_lab.services.material_service.upload_object")
    def test_generate_thumbnail_for_image(
        self, mock_upload, mock_get_bytes, material_service, mock_repository, sample_material
    ):
        """Should generate thumbnail for image material."""
        # Mock S3 download - return a small PNG image bytes
        from io import BytesIO
        from PIL import Image

        # Create a small test image
        img = Image.new("RGB", (400, 400), color="red")
        img_bytes = BytesIO()
        img.save(img_bytes, format="PNG")
        mock_get_bytes.return_value = img_bytes.getvalue()

        # Mock successful upload
        mock_upload.return_value = True

        # Mock repository
        mock_repository.get_by_id.return_value = sample_material
        mock_repository.update_thumbnail.return_value = None

        result = material_service.generate_thumbnail("mat_a1b2c3d4e5f6")

        # Should download original file
        mock_get_bytes.assert_called_once()

        # Should upload thumbnail
        mock_upload.assert_called_once()
        upload_args = mock_upload.call_args[0]
        assert "thumbnails/" in upload_args[0]
        assert upload_args[2] == "image/png"

        # Should update material with thumbnail URL
        mock_repository.update_thumbnail.assert_called_once()
        assert result is not None
        assert "thumbnails/" in result

    @patch("synth_lab.services.material_service.get_object_bytes")
    def test_generate_thumbnail_for_video_handles_errors_gracefully(
        self, mock_get_bytes, material_service, mock_repository
    ):
        """Should handle video thumbnail generation errors gracefully."""
        from datetime import datetime, timezone

        video_material = ExperimentMaterial(
            id="mat_fedcba987654",
            experiment_id="exp_abc12345",
            file_type=FileType.VIDEO,
            file_url="https://s3.com/bucket/materials/exp_abc12345/mat_fedcba987654.mp4",
            file_name="test.mp4",
            file_size=5000000,
            mime_type="video/mp4",
            material_type=MaterialType.PROTOTYPE,
            description_status=DescriptionStatus.PENDING,
            display_order=0,
            created_at=datetime.now(timezone.utc),
        )

        mock_repository.get_by_id.return_value = video_material

        # Mock S3 download failure for video
        mock_get_bytes.return_value = None

        result = material_service.generate_thumbnail("mat_fedcba987654")

        # Should return None on video processing errors
        assert result is None

    @patch("synth_lab.services.material_service.get_object_bytes")
    @patch("synth_lab.services.material_service.upload_object")
    def test_generate_thumbnail_for_pdf(
        self, mock_upload, mock_get_bytes, material_service, mock_repository
    ):
        """Should generate thumbnail from PDF first page."""
        from datetime import datetime, timezone

        pdf_material = ExperimentMaterial(
            id="mat_112233445566",
            experiment_id="exp_abc12345",
            file_type=FileType.DOCUMENT,
            file_url="https://s3.com/bucket/materials/exp_abc12345/mat_112233445566.pdf",
            file_name="test.pdf",
            file_size=1000000,
            mime_type="application/pdf",
            material_type=MaterialType.SPEC,
            description_status=DescriptionStatus.PENDING,
            display_order=0,
            created_at=datetime.now(timezone.utc),
        )

        mock_get_bytes.return_value = b"fake_pdf_data"
        mock_upload.return_value = True
        mock_repository.get_by_id.return_value = pdf_material
        mock_repository.update_thumbnail.return_value = None

        # Mock pdf2image conversion
        with patch("pdf2image.convert_from_bytes") as mock_convert:
            from PIL import Image

            # Create a fake page image
            fake_page = Image.new("RGB", (200, 200), color="white")
            mock_convert.return_value = [fake_page]

            result = material_service.generate_thumbnail("mat_112233445566")

            # Should convert PDF page
            mock_convert.assert_called_once()

            # Should upload thumbnail
            assert result is not None
            mock_repository.update_thumbnail.assert_called_once()

    def test_generate_thumbnail_returns_none_for_missing_material(
        self, material_service, mock_repository
    ):
        """Should return None if material doesn't exist."""
        mock_repository.get_by_id.return_value = None

        result = material_service.generate_thumbnail("mat_nonexistent00")

        assert result is None

    @patch("synth_lab.services.material_service.get_object_bytes")
    def test_generate_thumbnail_handles_s3_download_failure(
        self, mock_get_bytes, material_service, mock_repository, sample_material
    ):
        """Should return None if S3 download fails."""
        mock_repository.get_by_id.return_value = sample_material
        mock_get_bytes.return_value = None  # Simulate download failure

        result = material_service.generate_thumbnail("mat_a1b2c3d4e5f6")

        assert result is None

    @patch("synth_lab.services.material_service.get_object_bytes")
    @patch("synth_lab.services.material_service.upload_object")
    def test_generate_thumbnail_handles_upload_failure(
        self, mock_upload, mock_get_bytes, material_service, mock_repository, sample_material
    ):
        """Should return None if thumbnail upload fails."""
        from io import BytesIO
        from PIL import Image

        # Create valid image bytes
        img = Image.new("RGB", (100, 100), color="blue")
        img_bytes = BytesIO()
        img.save(img_bytes, format="PNG")
        mock_get_bytes.return_value = img_bytes.getvalue()

        # Mock upload failure
        mock_upload.return_value = False
        mock_repository.get_by_id.return_value = sample_material

        result = material_service.generate_thumbnail("mat_a1b2c3d4e5f6")

        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
