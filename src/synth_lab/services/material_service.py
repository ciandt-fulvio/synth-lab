"""
Material service for synth-lab.

Manages experiment materials (images, videos, documents) including
presigned URL generation, upload confirmation, thumbnail generation,
and limit validation.

References:
    - Repository: synth_lab.repositories.experiment_material_repository
    - Entity: synth_lab.domain.entities.experiment_material
    - Storage: synth_lab.infrastructure.storage_client
    - Pillow: https://pillow.readthedocs.io/en/stable/
    - pdf2image: https://pdf2image.readthedocs.io/en/latest/
    - moviepy: https://zulko.github.io/moviepy/
"""

from datetime import datetime, timezone
from io import BytesIO

from loguru import logger
from PIL import Image

from synth_lab.domain.entities.experiment_material import (
    DescriptionStatus,
    ExperimentMaterial,
    ExperimentMaterialSummary,
    FileType,
    MaterialType,
    generate_material_id,
    get_file_type_from_mime,
)
from synth_lab.infrastructure import config
from synth_lab.infrastructure.storage_client import (
    check_object_exists,
    delete_object,
    generate_upload_url,
    generate_view_url,
    get_object_bytes,
    upload_object,
)
from synth_lab.repositories.experiment_material_repository import (
    ExperimentMaterialRepository,
    MaterialLimitExceededError,
    MaterialNotFoundError,
)


class UnsupportedFileTypeError(Exception):
    """Raised when file type is not supported."""

    def __init__(self, mime_type: str):
        self.mime_type = mime_type
        super().__init__(f"Unsupported file type: {mime_type}")


class FileSizeLimitError(Exception):
    """Raised when file size exceeds limit."""

    def __init__(self, file_size: int, max_size: int, file_type: str):
        self.file_size = file_size
        self.max_size = max_size
        super().__init__(
            f"File size {file_size} exceeds maximum {max_size} for {file_type}"
        )


class MaterialService:
    """
    Service for managing experiment materials.

    Provides presigned URL generation, upload confirmation,
    and material CRUD operations with limit validation.
    """

    def __init__(
        self,
        repository: ExperimentMaterialRepository | None = None,
    ):
        self.repository = repository or ExperimentMaterialRepository()
        self.logger = logger.bind(component="material_service")

    def request_upload_url(
        self,
        experiment_id: str,
        file_name: str,
        file_size: int,
        mime_type: str,
        material_type: MaterialType,
    ) -> dict:
        """
        Request a presigned URL for uploading a file.

        Creates a pending material record and returns presigned URL
        for direct S3 upload.

        Args:
            experiment_id: Experiment ID.
            file_name: Original filename.
            file_size: File size in bytes.
            mime_type: MIME type of the file.
            material_type: Purpose/category of material.

        Returns:
            Dict with material_id, upload_url, object_key, expires_in.

        Raises:
            UnsupportedFileTypeError: If MIME type is not supported.
            FileSizeLimitError: If file size exceeds limit for type.
            MaterialLimitExceededError: If experiment limits exceeded.
        """
        # Validate file type
        file_type = get_file_type_from_mime(mime_type)
        if file_type is None:
            raise UnsupportedFileTypeError(mime_type)

        # Validate file size
        self._validate_file_size(file_size, file_type)

        # Validate experiment limits
        self._validate_experiment_limits(experiment_id, file_size)

        # Generate IDs and paths
        material_id = generate_material_id()
        extension = file_name.rsplit(".", 1)[-1] if "." in file_name else ""
        object_key = f"materials/{experiment_id}/{material_id}.{extension}"

        # Generate presigned upload URL
        upload_url = generate_upload_url(
            object_key=object_key,
            content_type=mime_type,
            expires_in=config.PRESIGNED_URL_EXPIRATION,
        )

        # Get next display order
        display_order = self.repository.get_next_display_order(experiment_id)

        # Create pending material record
        material = ExperimentMaterial(
            id=material_id,
            experiment_id=experiment_id,
            file_type=file_type,
            file_url="",  # Will be set on confirmation
            file_name=file_name,
            file_size=file_size,
            mime_type=mime_type,
            material_type=material_type,
            description_status=DescriptionStatus.PENDING,
            display_order=display_order,
            created_at=datetime.now(timezone.utc),
        )
        self.repository.create(material)

        self.logger.info(
            f"Created upload URL for material {material_id} "
            f"({file_name}, {file_size} bytes) in experiment {experiment_id}"
        )

        return {
            "material_id": material_id,
            "upload_url": upload_url,
            "object_key": object_key,
            "expires_in": config.PRESIGNED_URL_EXPIRATION,
        }

    def confirm_upload(
        self,
        experiment_id: str,
        material_id: str,
        object_key: str,
    ) -> ExperimentMaterial:
        """
        Confirm that upload has completed.

        Verifies file exists in S3 and updates material record.
        Queues description generation.

        Args:
            experiment_id: Experiment ID.
            material_id: Material ID from request_upload_url.
            object_key: S3 object key from request_upload_url.

        Returns:
            Updated material with file_url set.

        Raises:
            MaterialNotFoundError: If material doesn't exist.
            ValueError: If object not found in S3.
        """
        # Get material
        material = self.repository.get_by_id(material_id)
        if material is None:
            raise MaterialNotFoundError(material_id)

        if material.experiment_id != experiment_id:
            raise ValueError(
                f"Material {material_id} does not belong to experiment {experiment_id}"
            )

        # Verify file exists in S3
        if not check_object_exists(object_key):
            raise ValueError(f"Object {object_key} not found in S3")

        # Build file URL
        endpoint = config.S3_ENDPOINT_URL.replace('https://', '')
        file_url = f"https://{endpoint}/{config.BUCKET_NAME}/{object_key}"

        # Update material with file URL
        self.repository.update_file_url(material_id, file_url)

        # Get updated material
        updated_material = self.repository.get_by_id(material_id)

        self.logger.info(
            f"Confirmed upload for material {material_id} in experiment {experiment_id}"
        )

        # Generate thumbnail (T043)
        # This runs synchronously for now; can be made async in Phase 7
        try:
            self.generate_thumbnail(material_id)
        except Exception as e:
            self.logger.warning(f"Thumbnail generation failed for {material_id}: {e}")
            # Don't fail the upload if thumbnail generation fails

        # Generate AI description
        # This runs synchronously for now; can be made async in Phase 7
        try:
            self.generate_description(material_id)
        except Exception as e:
            self.logger.warning(f"Description generation failed for {material_id}: {e}")
            # Don't fail the upload if description generation fails

        return updated_material

    def get_material(self, material_id: str) -> ExperimentMaterial:
        """
        Get a material by ID.

        Args:
            material_id: Material ID.

        Returns:
            ExperimentMaterial.

        Raises:
            MaterialNotFoundError: If material doesn't exist.
        """
        material = self.repository.get_by_id(material_id)
        if material is None:
            raise MaterialNotFoundError(material_id)
        return material

    def list_materials(
        self,
        experiment_id: str,
    ) -> list[ExperimentMaterialSummary]:
        """
        List all materials for an experiment.

        Args:
            experiment_id: Experiment ID.

        Returns:
            List of material summaries ordered by display_order.
        """
        return self.repository.list_summaries_by_experiment(experiment_id)

    def list_materials_full(
        self,
        experiment_id: str,
    ) -> list[ExperimentMaterial]:
        """
        List all materials with full data.

        Args:
            experiment_id: Experiment ID.

        Returns:
            List of full materials ordered by display_order.
        """
        return self.repository.list_by_experiment(experiment_id)

    def get_view_url(
        self,
        material_id: str,
        expires_in: int = 3600,
    ) -> dict:
        """
        Get presigned URL for viewing a material.

        Args:
            material_id: Material ID.
            expires_in: URL expiration time in seconds.

        Returns:
            Dict with material_id, view_url, thumbnail_url, expires_in.

        Raises:
            MaterialNotFoundError: If material doesn't exist.
        """
        material = self.repository.get_by_id(material_id)
        if material is None:
            raise MaterialNotFoundError(material_id)

        # Extract object key from file_url
        if not material.file_url:
            raise ValueError(f"Material {material_id} has no file URL")

        # Parse object key from URL
        # URL format: https://endpoint/bucket/key
        url_parts = material.file_url.split("/")
        object_key = "/".join(url_parts[4:])  # Skip https:, empty, endpoint, bucket

        view_url = generate_view_url(object_key, expires_in=expires_in)

        thumbnail_url = None
        if material.thumbnail_url:
            thumb_parts = material.thumbnail_url.split("/")
            thumb_key = "/".join(thumb_parts[4:])
            thumbnail_url = generate_view_url(thumb_key, expires_in=expires_in)

        return {
            "material_id": material_id,
            "view_url": view_url,
            "thumbnail_url": thumbnail_url,
            "expires_in": expires_in,
        }

    def reorder_materials(
        self,
        experiment_id: str,
        material_ids: list[str],
    ) -> list[ExperimentMaterialSummary]:
        """
        Reorder materials for an experiment.

        Args:
            experiment_id: Experiment ID.
            material_ids: Material IDs in new display order.

        Returns:
            Updated list of materials.
        """
        self.repository.reorder(experiment_id, material_ids)
        return self.repository.list_summaries_by_experiment(experiment_id)

    def delete_material(
        self,
        experiment_id: str,
        material_id: str,
    ) -> bool:
        """
        Delete a material.

        Args:
            experiment_id: Experiment ID.
            material_id: Material ID.

        Returns:
            True if deleted.

        Raises:
            MaterialNotFoundError: If material doesn't exist.
        """
        material = self.repository.get_by_id(material_id)
        if material is None:
            raise MaterialNotFoundError(material_id)

        if material.experiment_id != experiment_id:
            raise ValueError(
                f"Material {material_id} does not belong to experiment {experiment_id}"
            )

        # Delete from S3 if file exists
        if material.file_url:
            url_parts = material.file_url.split("/")
            object_key = "/".join(url_parts[4:])
            try:
                delete_object(object_key)
            except Exception as e:
                self.logger.warning(f"Failed to delete S3 object {object_key}: {e}")

        # Delete thumbnail if exists
        if material.thumbnail_url:
            thumb_parts = material.thumbnail_url.split("/")
            thumb_key = "/".join(thumb_parts[4:])
            try:
                delete_object(thumb_key)
            except Exception as e:
                self.logger.warning(f"Failed to delete thumbnail {thumb_key}: {e}")

        self.repository.delete(material_id)

        self.logger.info(
            f"Deleted material {material_id} from experiment {experiment_id}"
        )

        return True

    def get_limits(self, experiment_id: str) -> dict:
        """
        Get current usage and limits for an experiment.

        Args:
            experiment_id: Experiment ID.

        Returns:
            Dict with current_count, max_count, current_size, max_size, can_upload.
        """
        current_count = self.repository.count_by_experiment(experiment_id)
        current_size = self.repository.get_total_size_by_experiment(experiment_id)

        return {
            "current_count": current_count,
            "max_count": config.MAX_MATERIALS_PER_EXPERIMENT,
            "current_size": current_size,
            "max_size": config.MAX_TOTAL_SIZE_PER_EXPERIMENT,
            "can_upload": (
                current_count < config.MAX_MATERIALS_PER_EXPERIMENT
                and current_size < config.MAX_TOTAL_SIZE_PER_EXPERIMENT
            ),
        }

    def _validate_file_size(self, file_size: int, file_type: FileType) -> None:
        """Validate file size against type-specific limits."""
        if file_type == FileType.IMAGE:
            max_size = config.MAX_IMAGE_SIZE
        elif file_type == FileType.VIDEO:
            max_size = config.MAX_VIDEO_SIZE
        else:
            max_size = config.MAX_DOCUMENT_SIZE

        if file_size > max_size:
            raise FileSizeLimitError(file_size, max_size, file_type.value)

    def _validate_experiment_limits(
        self,
        experiment_id: str,
        new_file_size: int,
    ) -> None:
        """Validate experiment doesn't exceed material limits."""
        current_count = self.repository.count_by_experiment(experiment_id)
        if current_count >= config.MAX_MATERIALS_PER_EXPERIMENT:
            raise MaterialLimitExceededError(
                f"Experiment {experiment_id} has reached maximum of "
                f"{config.MAX_MATERIALS_PER_EXPERIMENT} materials"
            )

        current_size = self.repository.get_total_size_by_experiment(experiment_id)
        if current_size + new_file_size > config.MAX_TOTAL_SIZE_PER_EXPERIMENT:
            raise MaterialLimitExceededError(
                f"Adding {new_file_size} bytes would exceed maximum of "
                f"{config.MAX_TOTAL_SIZE_PER_EXPERIMENT} bytes per experiment"
            )

    # -------------------------------------------------------------------------
    # Thumbnail Generation (T039-T043)
    # -------------------------------------------------------------------------

    def generate_thumbnail(
        self,
        material_id: str,
        thumbnail_size: tuple[int, int] = (200, 200),
    ) -> str | None:
        """
        Generate thumbnail for a material and upload to S3.

        Dispatches to appropriate method based on file type:
        - Image: Resize with Pillow
        - Video: Extract first frame with moviepy
        - Document: Extract first page with pdf2image

        Args:
            material_id: Material ID.
            thumbnail_size: Target thumbnail dimensions (width, height).

        Returns:
            Thumbnail URL if successful, None if generation failed.
        """
        material = self.repository.get_by_id(material_id)
        if material is None:
            self.logger.error(f"Material {material_id} not found for thumbnail")
            return None

        if not material.file_url:
            self.logger.error(f"Material {material_id} has no file URL")
            return None

        # Extract object key from file_url
        url_parts = material.file_url.split("/")
        object_key = "/".join(url_parts[4:])

        try:
            if material.file_type == FileType.IMAGE:
                thumbnail_bytes = self._generate_image_thumbnail(object_key, thumbnail_size)
            elif material.file_type == FileType.VIDEO:
                thumbnail_bytes = self._generate_video_thumbnail(object_key, thumbnail_size)
            elif material.file_type == FileType.DOCUMENT:
                thumbnail_bytes = self._generate_document_thumbnail(object_key, thumbnail_size)
            else:
                self.logger.warning(f"No thumbnail generator for type {material.file_type}")
                return None

            if thumbnail_bytes is None:
                return None

            # Upload thumbnail
            thumb_key = f"thumbnails/{material.experiment_id}/{material_id}.png"
            success = upload_object(thumb_key, thumbnail_bytes, "image/png")

            if not success:
                self.logger.error(f"Failed to upload thumbnail for {material_id}")
                return None

            # Build thumbnail URL
            endpoint = config.S3_ENDPOINT_URL.replace('https://', '')
            thumbnail_url = f"https://{endpoint}/{config.BUCKET_NAME}/{thumb_key}"

            # Update material with thumbnail URL
            self.repository.update_thumbnail(material_id, thumbnail_url)

            self.logger.info(f"Generated thumbnail for material {material_id}")
            return thumbnail_url

        except Exception as e:
            self.logger.error(f"Failed to generate thumbnail for {material_id}: {e}")
            return None

    def _generate_image_thumbnail(
        self,
        object_key: str,
        size: tuple[int, int],
    ) -> bytes | None:
        """
        Generate thumbnail from image using Pillow.

        Args:
            object_key: S3 object key for the image.
            size: Target thumbnail dimensions.

        Returns:
            PNG bytes of thumbnail, or None if failed.
        """
        image_bytes = get_object_bytes(object_key)
        if image_bytes is None:
            self.logger.error(f"Could not download image {object_key}")
            return None

        try:
            with Image.open(BytesIO(image_bytes)) as img:
                # Convert to RGB if necessary (for PNG with transparency)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                # Use thumbnail() to maintain aspect ratio
                img.thumbnail(size, Image.Resampling.LANCZOS)

                # Save to bytes
                output = BytesIO()
                img.save(output, format="PNG", optimize=True)
                return output.getvalue()

        except Exception as e:
            self.logger.error(f"Failed to process image {object_key}: {e}")
            return None

    def _generate_video_thumbnail(
        self,
        object_key: str,
        size: tuple[int, int],
    ) -> bytes | None:
        """
        Generate thumbnail from video by extracting first frame.

        Uses moviepy to extract frame at t=0.

        Args:
            object_key: S3 object key for the video.
            size: Target thumbnail dimensions.

        Returns:
            PNG bytes of thumbnail, or None if failed.
        """
        video_bytes = get_object_bytes(object_key)
        if video_bytes is None:
            self.logger.error(f"Could not download video {object_key}")
            return None

        try:
            # moviepy requires a file, so we use a temp file
            import tempfile
            from moviepy.editor import VideoFileClip

            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=True) as tmp:
                tmp.write(video_bytes)
                tmp.flush()

                with VideoFileClip(tmp.name) as clip:
                    # Extract frame at t=0
                    frame = clip.get_frame(0)

                    # Convert numpy array to PIL Image
                    img = Image.fromarray(frame)
                    img.thumbnail(size, Image.Resampling.LANCZOS)

                    output = BytesIO()
                    img.save(output, format="PNG", optimize=True)
                    return output.getvalue()

        except Exception as e:
            self.logger.error(f"Failed to extract video frame from {object_key}: {e}")
            return None

    def _generate_document_thumbnail(
        self,
        object_key: str,
        size: tuple[int, int],
    ) -> bytes | None:
        """
        Generate thumbnail from PDF by rendering first page.

        Uses pdf2image to convert first page to image.

        Args:
            object_key: S3 object key for the PDF.
            size: Target thumbnail dimensions.

        Returns:
            PNG bytes of thumbnail, or None if failed.
        """
        doc_bytes = get_object_bytes(object_key)
        if doc_bytes is None:
            self.logger.error(f"Could not download document {object_key}")
            return None

        try:
            from pdf2image import convert_from_bytes

            # Convert only first page
            images = convert_from_bytes(
                doc_bytes,
                first_page=1,
                last_page=1,
                dpi=72,  # Low DPI for thumbnail
            )

            if not images:
                self.logger.error(f"No pages extracted from {object_key}")
                return None

            img = images[0]
            img.thumbnail(size, Image.Resampling.LANCZOS)

            output = BytesIO()
            img.save(output, format="PNG", optimize=True)
            return output.getvalue()

        except Exception as e:
            self.logger.error(f"Failed to render PDF {object_key}: {e}")
            return None

    # -------------------------------------------------------------------------
    # AI Description Generation
    # -------------------------------------------------------------------------

    def generate_description(self, material_id: str) -> str | None:
        """
        Generate AI description for a material using vision-capable LLM.

        Dispatches to appropriate method based on file type:
        - Image: Vision API with full image
        - Video: Vision API with first frame
        - Document: Text extraction + standard LLM

        Args:
            material_id: Material ID.

        Returns:
            Generated description (max 30 words) if successful, None if failed.
        """
        material = self.repository.get_by_id(material_id)
        if material is None:
            self.logger.error(f"Material {material_id} not found for description")
            return None

        if not material.file_url:
            self.logger.error(f"Material {material_id} has no file URL")
            return None

        # Extract object key from file_url
        url_parts = material.file_url.split("/")
        object_key = "/".join(url_parts[4:])

        try:
            if material.file_type == FileType.IMAGE:
                description = self._generate_image_description(object_key)
            elif material.file_type == FileType.VIDEO:
                description = self._generate_video_description(object_key)
            elif material.file_type == FileType.DOCUMENT:
                description = self._generate_document_description(object_key)
            else:
                self.logger.warning(f"No description generator for type {material.file_type}")
                return None

            if description is None:
                return None

            # Update material with description
            from synth_lab.domain.entities.experiment_material import DescriptionStatus
            self.repository.update_description(
                material_id=material_id,
                description=description,
                status=DescriptionStatus.COMPLETED,
            )

            self.logger.info(f"Generated description for material {material_id}")
            return description

        except Exception as e:
            self.logger.error(f"Failed to generate description for {material_id}: {e}")
            # Mark as failed
            from synth_lab.domain.entities.experiment_material import DescriptionStatus
            self.repository.update_description(
                material_id=material_id,
                description=None,
                status=DescriptionStatus.FAILED,
            )
            return None

    def _generate_image_description(self, object_key: str) -> str | None:
        """
        Generate description from image using vision API.

        Args:
            object_key: S3 object key for the image.

        Returns:
            Description text, or None if failed.
        """
        import base64
        from synth_lab.infrastructure.llm_client import get_llm_client
        from synth_lab.infrastructure.phoenix_tracing import get_tracer

        _tracer = get_tracer("material-description")

        image_bytes = get_object_bytes(object_key)
        if image_bytes is None:
            self.logger.error(f"Could not download image {object_key}")
            return None

        try:
            # Encode image to base64
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")

            # Prepare messages for vision API
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Describe this material in exactly 30 words. Focus on what it shows, its purpose, and key visible elements. Be concise and specific.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}",
                                "detail": "high",
                            },
                        },
                    ],
                }
            ]

            with _tracer.start_as_current_span(
                "Generate Material Description (Image)",
                attributes={
                    "operation_type": "material_description",
                    "file_type": "image",
                    "object_key": object_key,
                },
            ):
                llm_client = get_llm_client()
                description = llm_client.complete(
                    messages=messages,
                    model="gpt-4o-mini",
                    temperature=0.7,
                    max_tokens=100,
                )

                return description.strip()

        except Exception as e:
            self.logger.error(f"Failed to generate image description for {object_key}: {e}")
            return None

    def _generate_video_description(self, object_key: str) -> str | None:
        """
        Generate description from video by analyzing first frame.

        Args:
            object_key: S3 object key for the video.

        Returns:
            Description text, or None if failed.
        """
        import base64
        import tempfile
        from moviepy.editor import VideoFileClip
        from synth_lab.infrastructure.llm_client import get_llm_client
        from synth_lab.infrastructure.phoenix_tracing import get_tracer

        _tracer = get_tracer("material-description")

        video_bytes = get_object_bytes(object_key)
        if video_bytes is None:
            self.logger.error(f"Could not download video {object_key}")
            return None

        try:
            # Extract first frame
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=True) as tmp:
                tmp.write(video_bytes)
                tmp.flush()

                with VideoFileClip(tmp.name) as clip:
                    frame = clip.get_frame(0)
                    img = Image.fromarray(frame)

                    # Convert frame to base64
                    output = BytesIO()
                    img.save(output, format="PNG")
                    frame_base64 = base64.b64encode(output.getvalue()).decode("utf-8")

            # Prepare messages for vision API
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Describe this video material in exactly 30 words based on this frame. Focus on what it shows, its purpose, and key visible elements. Be concise and specific.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{frame_base64}",
                                "detail": "high",
                            },
                        },
                    ],
                }
            ]

            with _tracer.start_as_current_span(
                "Generate Material Description (Video)",
                attributes={
                    "operation_type": "material_description",
                    "file_type": "video",
                    "object_key": object_key,
                },
            ):
                llm_client = get_llm_client()
                description = llm_client.complete(
                    messages=messages,
                    model="gpt-4o-mini",
                    temperature=0.7,
                    max_tokens=100,
                )

                return description.strip()

        except Exception as e:
            self.logger.error(f"Failed to generate video description for {object_key}: {e}")
            return None

    def _generate_document_description(self, object_key: str) -> str | None:
        """
        Generate description from document by extracting text.

        Args:
            object_key: S3 object key for the document.

        Returns:
            Description text, or None if failed.
        """
        from synth_lab.infrastructure.llm_client import get_llm_client
        from synth_lab.infrastructure.phoenix_tracing import get_tracer

        _tracer = get_tracer("material-description")

        doc_bytes = get_object_bytes(object_key)
        if doc_bytes is None:
            self.logger.error(f"Could not download document {object_key}")
            return None

        try:
            # Extract text from PDF
            from pdf2image import convert_from_bytes
            import pytesseract

            # Convert first page to image
            images = convert_from_bytes(
                doc_bytes,
                first_page=1,
                last_page=1,
                dpi=150,
            )

            if not images:
                self.logger.error(f"No pages extracted from {object_key}")
                return None

            # OCR the first page
            text = pytesseract.image_to_string(images[0])
            text_preview = text[:1000]  # First 1000 chars

            # Generate description
            messages = [
                {
                    "role": "user",
                    "content": f"Based on this document excerpt, create a 30-word description focusing on its purpose and key content:\n\n{text_preview}",
                }
            ]

            with _tracer.start_as_current_span(
                "Generate Material Description (Document)",
                attributes={
                    "operation_type": "material_description",
                    "file_type": "document",
                    "object_key": object_key,
                    "text_length": len(text),
                },
            ):
                llm_client = get_llm_client()
                description = llm_client.complete(
                    messages=messages,
                    model="gpt-4o-mini",
                    temperature=0.7,
                    max_tokens=100,
                )

                return description.strip()

        except Exception as e:
            self.logger.error(f"Failed to generate document description for {object_key}: {e}")
            return None


if __name__ == "__main__":
    import sys

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Test 1: Service initialization
    total_tests += 1
    try:
        service = MaterialService()
        if not hasattr(service, "logger"):
            all_validation_failures.append("Service should have logger")
        if not hasattr(service, "repository"):
            all_validation_failures.append("Service should have repository")
    except Exception as e:
        all_validation_failures.append(f"Service init failed: {e}")

    # Test 2: Methods exist
    total_tests += 1
    try:
        service = MaterialService()
        methods = [
            "request_upload_url",
            "confirm_upload",
            "get_material",
            "list_materials",
            "list_materials_full",
            "get_view_url",
            "reorder_materials",
            "delete_material",
            "get_limits",
            "_validate_file_size",
            "_validate_experiment_limits",
            "generate_thumbnail",
            "_generate_image_thumbnail",
            "_generate_video_thumbnail",
            "_generate_document_thumbnail",
        ]
        for method in methods:
            if not hasattr(service, method):
                all_validation_failures.append(f"Missing method: {method}")
    except Exception as e:
        all_validation_failures.append(f"Method check failed: {e}")

    # Test 3: Exception classes
    total_tests += 1
    try:
        err = UnsupportedFileTypeError("application/octet-stream")
        if "application/octet-stream" not in str(err):
            all_validation_failures.append(
                "UnsupportedFileTypeError should include MIME type"
            )

        size_err = FileSizeLimitError(50_000_000, 25_000_000, "image")
        if "50000000" not in str(size_err) or "25000000" not in str(size_err):
            all_validation_failures.append(
                "FileSizeLimitError should include sizes"
            )
    except Exception as e:
        all_validation_failures.append(f"Exception class test failed: {e}")

    # Test 4: File size validation logic
    total_tests += 1
    try:
        service = MaterialService()

        # Test valid image size
        try:
            service._validate_file_size(10_000_000, FileType.IMAGE)  # 10MB
        except FileSizeLimitError:
            all_validation_failures.append("10MB image should be valid")

        # Test invalid image size
        try:
            service._validate_file_size(30_000_000, FileType.IMAGE)  # 30MB
            all_validation_failures.append("30MB image should raise FileSizeLimitError")
        except FileSizeLimitError:
            pass  # Expected

        # Test valid video size
        try:
            service._validate_file_size(50_000_000, FileType.VIDEO)  # 50MB
        except FileSizeLimitError:
            all_validation_failures.append("50MB video should be valid")

    except Exception as e:
        all_validation_failures.append(f"File size validation test failed: {e}")

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
        print("MaterialService is validated and ready for use")
        sys.exit(0)
