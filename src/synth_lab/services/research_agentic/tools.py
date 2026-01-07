"""
Function tools for agentic interview system.

This module provides tools that agents can use during interviews,
such as loading images from topic guides for visual analysis and
loading experiment materials (images, PDFs, videos) for reference.

References:
- OpenAI Agents SDK Tools: https://openai.github.io/openai-agents-python/tools/
- Vision API: https://platform.openai.com/docs/guides/vision
- contracts/materials_tool.yaml: Materials tool contract

Sample usage:
```python
from .tools import create_image_loader_tool, create_materials_tool

# Topic guide images
tool = create_image_loader_tool(
    topic_guide_name="compra-amazon",
    available_images=["01_homepage.PNG", "02_cart.PNG"]
)

# Experiment materials
materials_tool = create_materials_tool(
    experiment_id="exp_123",
    material_repository=repo,
    s3_client=s3
)

agent = Agent(name="Interviewee", tools=[tool, materials_tool])
```
"""

import base64
from pathlib import Path
from typing import Literal

from agents import FunctionTool, function_tool
from loguru import logger
from pydantic import BaseModel

from synth_lab.infrastructure.phoenix_tracing import get_tracer

# Phoenix tracer for observability
_tracer = get_tracer("materials-tool")


def load_image_base64(filename: str, topic_guide_name: str) -> str:
    """
    Load image file and encode to base64 for Vision API.

    Args:
        filename: Name of the image file (e.g., '01_homepage.PNG')
        topic_guide_name: Name of the topic guide directory

    Returns:
        Base64-encoded image data

    Raises:
        FileNotFoundError: If image file doesn't exist
    """
    from synth_lab.infrastructure.config import resolve_topic_guide_path

    guide_path = resolve_topic_guide_path(topic_guide_name)
    if guide_path is None:
        logger.error(f"Topic guide not found: {topic_guide_name}")
        raise FileNotFoundError(f"Topic guide '{topic_guide_name}' not found")

    image_path = guide_path / filename

    if not image_path.exists():
        logger.error(f"Image not found: {image_path}")
        raise FileNotFoundError(
            f"Image file '{filename}' not found in topic guide '{topic_guide_name}'"
        )

    # Read and encode image
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    logger.info(f"Loaded image: {filename} ({len(image_data)} bytes base64)")
    return image_data


def create_image_loader_tool(
    topic_guide_name: str,
    available_images: list[str]) -> FunctionTool:
    """
    Create a function tool for loading images from a topic guide.

    The tool allows agents to request specific images from the topic guide
    directory for visual analysis during interviews.

    Args:
        topic_guide_name: Name of the topic guide directory
        available_images: List of available image filenames

    Returns:
        FunctionTool configured to load images from the topic guide

    Sample usage:
    ```python
    tool = create_image_loader_tool(
        topic_guide_name="compra-amazon",
        available_images=["01_homepage.PNG", "02_cart.PNG"]
    )
    ```
    """
    # Format available images for description
    images_list = ", ".join(available_images) if available_images else "nenhuma"

    @function_tool(
        name_override="ver_imagem",
        description_override=(
            f"Carrega uma imagem do guia de tópicos para visualização. "
            f"Use esta ferramenta quando quiser ver uma imagem específica "
            f"que está sendo discutida na entrevista. "
            f"Imagens disponíveis: {images_list}"
        ))
    def load_image(filename: str) -> str:
        """
        Load an image from the topic guide for visual analysis.

        Args:
            filename: Name of the image file to load (e.g., '01_homepage.PNG')

        Returns:
            Base64-encoded image data with data URI prefix
        """
        image_data = load_image_base64(filename, topic_guide_name)

        # Determine MIME type from extension
        ext = Path(filename).suffix.lower()
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        mime_type = mime_types.get(ext, "image/png")

        return f"data:{mime_type};base64,{image_data}"

    return load_image


def get_available_images(topic_guide_name: str) -> list[str]:
    """
    Get list of available image files in a topic guide directory.

    Args:
        topic_guide_name: Name of the topic guide directory

    Returns:
        List of image filenames available in the topic guide

    Sample usage:
    ```python
    images = get_available_images("compra-amazon")
    # Returns: ["01_homepage.PNG", "02_cart.PNG", ...]
    ```
    """
    from synth_lab.infrastructure.config import resolve_topic_guide_path

    guide_path = resolve_topic_guide_path(topic_guide_name)

    if guide_path is None:
        logger.warning(f"Topic guide directory not found: {topic_guide_name}")
        return []

    image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
    images = [
        f.name for f in guide_path.iterdir() if f.is_file() and f.suffix.lower() in image_extensions
    ]

    logger.info(f"Found {len(images)} images in topic guide '{topic_guide_name}'")
    return sorted(images)


#  ============================================================================
# Materials Tool (for Experiment Materials)
# ============================================================================

class MaterialToolResponse(BaseModel):
    """Response format from material retrieval tool."""

    status: Literal["success", "error"]
    material_id: str
    data_uri: str | None  # "data:image/png;base64,..." or None if error
    error_message: str | None
    mime_type: str | None
    file_name: str | None

    @classmethod
    def success(cls, material_id: str, data_uri: str, mime_type: str, file_name: str):
        """Create success response."""
        return cls(
            status="success",
            material_id=material_id,
            data_uri=data_uri,
            error_message=None,
            mime_type=mime_type,
            file_name=file_name
        )

    @classmethod
    def error(cls, material_id: str, error_message: str):
        """Create error response."""
        return cls(
            status="error",
            material_id=material_id,
            data_uri=None,
            error_message=error_message,
            mime_type=None,
            file_name=None
        )


def _load_material_content(
    material_id: str,
    experiment_id: str,
    material_repository,
    s3_client
) -> str:
    """
    Core business logic for loading material content.

    This function is separated from the tool wrapper for testability.

    Args:
        material_id: ID of the material to load
        experiment_id: ID of the experiment (for validation)
        material_repository: Repository for fetching material metadata
        s3_client: S3 client for downloading files

    Returns:
        Data URI with base64-encoded content or error message
    """
    with _tracer.start_as_current_span(
        "Load Material",
        attributes={
            "material_id": material_id,
            "experiment_id": experiment_id
        }
    ):
        try:
            # Fetch material metadata
            material = material_repository.get_by_id(material_id)

            if material is None:
                error_msg = f"Material {material_id} não encontrado neste experimento."
                logger.warning(error_msg)
                return error_msg

            # Validate material belongs to this experiment
            if material.experiment_id != experiment_id:
                error_msg = f"Material {material_id} não encontrado neste experimento."
                logger.warning(
                    f"Material {material_id} belongs to {material.experiment_id}, "
                    f"not {experiment_id}"
                )
                return error_msg

            # Check file size (50MB limit)
            if material.file_size > 50_000_000:
                error_msg = (
                    f"Material muito grande (>50MB). "
                    f"Use a descrição do material como referência: {material.description}"
                )
                logger.warning(f"Material {material_id} too large: {material.file_size} bytes")
                return error_msg

            # Download file from S3
            try:
                file_content = s3_client.download_from_s3(material.file_url)
            except TimeoutError as e:
                error_msg = "Timeout ao carregar material. Tente novamente ou escolha outro material."
                logger.error(f"Timeout downloading material {material_id}: {e}")
                return error_msg
            except Exception as e:
                error_msg = "Material não encontrado. Arquivo pode ter sido removido do armazenamento."
                logger.error(f"S3 download failed for {material_id}: {e}")
                return error_msg

            # Encode to base64
            try:
                encoded_content = base64.b64encode(file_content).decode("utf-8")
            except Exception as e:
                error_msg = "Erro ao processar material. Arquivo pode estar corrompido."
                logger.error(f"Base64 encoding failed for {material_id}: {e}")
                return error_msg

            # Return data URI
            data_uri = f"data:{material.mime_type};base64,{encoded_content}"

            logger.info(
                f"Loaded material {material_id}: {material.file_name} "
                f"({len(encoded_content)} bytes base64)"
            )

            return data_uri

        except Exception as e:
            error_msg = f"Erro ao carregar material: {str(e)}"
            logger.error(f"Unexpected error loading material {material_id}: {e}")
            return error_msg


def create_materials_tool(
    experiment_id: str,
    material_repository,
    s3_client
) -> FunctionTool:
    """
    Create a function tool for loading experiment materials.

    The tool allows agents to request specific materials (images, PDFs, videos)
    from the experiment for visual analysis during interviews.

    Args:
        experiment_id: ID of the current experiment
        material_repository: Repository for fetching material metadata
        s3_client: S3 client for downloading files

    Returns:
        FunctionTool configured to load materials from S3

    Sample usage:
    ```python
    from synth_lab.repositories.experiment_material_repository import ExperimentMaterialRepository

    tool = create_materials_tool(
        experiment_id="exp_123",
        material_repository=ExperimentMaterialRepository(session),
        s3_client=material_service
    )
    ```
    """

    @function_tool(
        name_override="ver_material",
        description_override=(
            "Visualiza um material anexado ao experimento. "
            "Use o material_id da lista de materiais disponíveis "
            "no contexto do experimento para carregar e visualizar "
            "imagens, documentos ou vídeos."
        ))
    def view_material(material_id: str) -> str:
        """
        Load material from experiment for visual analysis.

        Args:
            material_id: ID do material (e.g., 'mat_abc123def456')

        Returns:
            Data URI with base64-encoded content or error message
        """
        return _load_material_content(
            material_id=material_id,
            experiment_id=experiment_id,
            material_repository=material_repository,
            s3_client=s3_client
        )

    return view_material


if __name__ == "__main__":
    """Validation with real data."""
    import sys

    print("=== Tools Module Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Test 1: Get available images from existing topic guide
    total_tests += 1
    try:
        images = get_available_images("compra-amazon")
        if images and len(images) > 0:
            print(f"✓ get_available_images found {len(images)} images")
            print(f"  Images: {images[:3]}...")
        else:
            all_validation_failures.append("get_available_images: No images found in compra-amazon")
    except Exception as e:
        all_validation_failures.append(f"get_available_images: {e}")

    # Test 2: Get available images from non-existent topic guide
    total_tests += 1
    try:
        images = get_available_images("nonexistent-guide")
        if images == []:
            print("✓ get_available_images returns empty list for non-existent guide")
        else:
            all_validation_failures.append(
                "get_available_images: Should return empty list for non-existent guide"
            )
    except Exception as e:
        all_validation_failures.append(f"get_available_images (nonexistent): {e}")

    # Test 3: Create image loader tool
    total_tests += 1
    try:
        available = get_available_images("compra-amazon")
        tool = create_image_loader_tool("compra-amazon", available)
        if isinstance(tool, FunctionTool):
            print("✓ create_image_loader_tool returns FunctionTool")
            print(f"  Tool name: {tool.name}")
        else:
            all_validation_failures.append(
                f"create_image_loader_tool: Expected FunctionTool, got {type(tool)}"
            )
    except Exception as e:
        all_validation_failures.append(f"create_image_loader_tool: {e}")

    # Test 4: Load actual image (if available)
    total_tests += 1
    try:
        available = get_available_images("compra-amazon")
        if available:
            image_data = load_image_base64(available[0], "compra-amazon")
            if image_data and len(image_data) > 100:
                print(f"✓ load_image_base64 loaded image ({len(image_data)} bytes)")
            else:
                all_validation_failures.append("load_image_base64: Image data too small or empty")
        else:
            print("⚠ Skipping load_image_base64 test - no images available")
    except Exception as e:
        all_validation_failures.append(f"load_image_base64: {e}")

    # Test 5: Load non-existent image should raise error
    total_tests += 1
    try:
        load_image_base64("nonexistent.png", "compra-amazon")
        all_validation_failures.append(
            "load_image_base64: Should raise FileNotFoundError for non-existent image"
        )
    except FileNotFoundError:
        print("✓ load_image_base64 raises FileNotFoundError for non-existent image")
    except Exception as e:
        all_validation_failures.append(
            f"load_image_base64 (error handling): Unexpected error type {type(e)}"
        )

    # Final validation result
    print()
    if all_validation_failures:
        print(
            f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:"
        )
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Tools module is validated and ready for use")
        sys.exit(0)
