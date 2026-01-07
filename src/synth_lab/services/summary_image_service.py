"""
Summary Image Generation Service for synth-lab.

Generates cover images for summary documents using AI image generation.
Images are based on the summary content (excluding certain sections).

Usage:
    from synth_lab.services.summary_image_service import SummaryImageService

    service = SummaryImageService()
    updated_markdown = service.generate_and_append_image(
        markdown_content=summary_markdown,
        experiment_id="exp_12345678",
        doc_id="doc_abcdef12",
    )

References:
    - ImageGenerator: infrastructure/image_generator.py
    - Config: infrastructure/config.py
"""

import re
from pathlib import Path

from loguru import logger

from synth_lab.infrastructure.config import OUTPUT_DIR
from synth_lab.infrastructure.image_generator import ImageGenerator, get_image_generator
from synth_lab.infrastructure.phoenix_tracing import get_tracer

# Phoenix/OpenTelemetry tracer for observability
_tracer = get_tracer("summary-image-service")

# Directory for storing generated images
IMAGES_DIR = OUTPUT_DIR / "document" / "images"

# Sections to exclude from image prompt
EXCLUDED_SECTIONS = ["Resumo Executivo", "Recomendações"]


def extract_image_prompt(markdown_content: str) -> str:
    """
    Extract content for image generation prompt from markdown.

    Removes the 'Resumo Executivo' and 'Recomendações' sections,
    returning the remaining content as the image prompt.

    Args:
        markdown_content: Full markdown content of the summary.

    Returns:
        Cleaned content suitable for image generation prompt.

    Example:
        >>> content = '''
        ... # Summary
        ... ## Resumo Executivo
        ... This is executive summary.
        ... ## Main Content
        ... This is main content.
        ... ## Recomendações
        ... These are recommendations.
        ... '''
        >>> extract_image_prompt(content)
        '# Summary\\n## Main Content\\nThis is main content.'
    """
    if not markdown_content:
        return ""

    lines = markdown_content.split("\n")
    result_lines = []
    skip_section = False
    current_section_level = 0

    for line in lines:
        # Check if this is a header line
        header_match = re.match(r"^(#{1,6})\s+(.+)$", line)

        if header_match:
            header_level = len(header_match.group(1))
            header_text = header_match.group(2).strip()

            # Check if entering an excluded section
            if any(excluded in header_text for excluded in EXCLUDED_SECTIONS):
                skip_section = True
                current_section_level = header_level
                continue

            # Check if leaving the excluded section (same or higher level header)
            if skip_section and header_level <= current_section_level:
                skip_section = False

        # Only add line if not in an excluded section
        if not skip_section:
            result_lines.append(line)

    # Clean up and limit length for image prompt
    result = "\n".join(result_lines).strip()

    # Remove multiple blank lines
    result = re.sub(r"\n{3,}", "\n\n", result)

    return result


def build_image_prompt(content: str, max_length: int = 30000, materials: list | None = None) -> str:
    """
    Build the final prompt for image generation.

    Prepends context instructions and truncates if necessary.

    Args:
        content: Extracted content from markdown.
        max_length: Maximum length of the prompt.
        materials: Optional list of ExperimentMaterial objects for context.

    Returns:
        Final prompt for image generation.
    """
    # Include materials context if provided
    materials_context = ""
    if materials:
        from synth_lab.services.materials_context import format_materials_for_prompt

        materials_context = format_materials_for_prompt(
            materials=materials,
            context="exploration",
            include_tool_instructions=False,
        )
        materials_context = f"\n\n{materials_context}\n\n"

    # Combine materials context with content
    full_content = f"{materials_context}{content}"

    # Truncate if too long
    if len(full_content) > max_length:
        full_content = full_content[:max_length] + "..."

    return full_content


class SummaryImageService:
    """Service for generating and managing summary cover images."""

    def __init__(
        self,
        image_generator: ImageGenerator | None = None,
        images_dir: Path | None = None,
    ):
        """
        Initialize summary image service.

        Args:
            image_generator: ImageGenerator instance for image creation.
            images_dir: Directory for storing images. Defaults to OUTPUT_DIR/document/images.
        """
        self._image_generator = image_generator or get_image_generator()
        self._images_dir = images_dir or IMAGES_DIR
        self._logger = logger.bind(component="summary_image_service")

    def _ensure_images_dir(self) -> None:
        """Ensure the images directory exists."""
        self._images_dir.mkdir(parents=True, exist_ok=True)

    def _get_image_path(
        self,
        experiment_id: str,
        doc_id: str,
        extension: str = "png",
    ) -> Path:
        """
        Build the path for saving an image.

        Args:
            experiment_id: Experiment ID (e.g., "exp_12345678").
            doc_id: Document ID (e.g., "doc_abcdef12").
            extension: Image file extension.

        Returns:
            Path object for the image file.
        """
        filename = f"{experiment_id}_{doc_id}.{extension}"
        return self._images_dir / filename

    def generate_image(
        self,
        markdown_content: str,
        experiment_id: str,
        doc_id: str,
        output_format: str = "png",
        materials: list | None = None,
    ) -> Path | None:
        """
        Generate an image from summary content and save it.

        Args:
            markdown_content: Full markdown content of the summary.
            experiment_id: Experiment ID for filename.
            doc_id: Document ID for filename.
            output_format: Image format (png, jpeg, webp).
            materials: Optional list of ExperimentMaterial objects for context.

        Returns:
            Path to the saved image, or None if generation failed.
        """
        prompt_preview = markdown_content[:100] if markdown_content else ""

        with _tracer.start_as_current_span(
            "Generate Summary Image",
            attributes={
                "operation_type": "summary_image_generation",
                "experiment_id": experiment_id,
                "doc_id": doc_id,
                "output_format": output_format,
                "input.value": prompt_preview,
            },
        ) as span:
            try:
                # 1. Extract content for image prompt
                extracted_content = extract_image_prompt(markdown_content)
                if not extracted_content.strip():
                    self._logger.warning(f"No content extracted for image generation: {doc_id}")
                    return None

                # 2. Build final prompt
                image_prompt = build_image_prompt(extracted_content, materials=materials)
                self._logger.debug(f"Image prompt length: {len(image_prompt)} chars")

                if span:
                    span.set_attribute("prompt_length", len(image_prompt))

                # 3. Ensure directory exists
                self._ensure_images_dir()

                # 4. Generate image
                image_bytes = self._image_generator.generate_bytes(
                    prompt=image_prompt,
                    output_format=output_format,
                    size="1536x1024",
                    quality="auto",
                )

                # 5. Save to file
                image_path = self._get_image_path(experiment_id, doc_id, output_format)
                image_path.write_bytes(image_bytes)

                self._logger.info(
                    f"Generated summary image: {image_path} ({len(image_bytes)} bytes)"
                )

                if span:
                    span.set_attribute("image_path", str(image_path))
                    span.set_attribute("image_bytes", len(image_bytes))
                    span.set_attribute("success", True)

                return image_path

            except Exception as e:
                self._logger.error(f"Failed to generate summary image for {doc_id}: {e}")
                if span:
                    span.set_attribute("success", False)
                    span.set_attribute("error", str(e))
                return None

    def append_image_to_markdown(
        self,
        markdown_content: str,
        image_path: Path,
    ) -> str:
        """
        Append an image section to the markdown content.

        Args:
            markdown_content: Original markdown content.
            image_path: Path to the generated image.

        Returns:
            Updated markdown with image section appended.
        """
        # Convert local path to static URL
        image_url = f"/static/document/images/{image_path.name}"
        image_section = f"""

---

## Ilustração

![Ilustração do Sumário]({image_url})
"""
        return markdown_content.rstrip() + image_section

    def generate_and_append_image(
        self,
        markdown_content: str,
        experiment_id: str,
        doc_id: str,
        output_format: str = "png",
        materials: list | None = None,
    ) -> str:
        """
        Generate image and append it to the markdown content.

        This is the main method to use for integrating image generation
        into summary workflows.

        Args:
            markdown_content: Full markdown content of the summary.
            experiment_id: Experiment ID for filename.
            doc_id: Document ID for filename.
            output_format: Image format (png, jpeg, webp).
            materials: Optional list of ExperimentMaterial objects for context.

        Returns:
            Updated markdown with image section appended.
            If image generation fails, returns original markdown unchanged.
        """
        image_path = self.generate_image(
            markdown_content=markdown_content,
            experiment_id=experiment_id,
            doc_id=doc_id,
            output_format=output_format,
            materials=materials,
        )

        if image_path is None:
            self._logger.warning(
                f"Image generation failed for {doc_id}, returning original markdown"
            )
            return markdown_content

        return self.append_image_to_markdown(markdown_content, image_path)


# Singleton instance
_summary_image_service: SummaryImageService | None = None


def get_summary_image_service() -> SummaryImageService:
    """
    Get or create the global summary image service.

    Returns:
        SummaryImageService: Global service instance.
    """
    global _summary_image_service
    if _summary_image_service is None:
        _summary_image_service = SummaryImageService()
    return _summary_image_service


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: extract_image_prompt - removes Resumo Executivo
    total_tests += 1
    test_md = """# Title

## Resumo Executivo
This should be removed.

## Main Content
This should stay.

## Another Section
This should also stay.
"""
    result = extract_image_prompt(test_md)
    if "Resumo Executivo" in result:
        all_validation_failures.append("extract_image_prompt should remove 'Resumo Executivo'")
    if "Main Content" not in result:
        all_validation_failures.append("extract_image_prompt should keep 'Main Content'")

    # Test 2: extract_image_prompt - removes Recomendações
    total_tests += 1
    test_md2 = """# Title

## Some Section
Content here.

## Recomendações
Recommendations to remove.

## Final Section
This should stay.
"""
    result2 = extract_image_prompt(test_md2)
    if "Recomendações" in result2:
        all_validation_failures.append("extract_image_prompt should remove 'Recomendações'")
    if "Final Section" not in result2:
        all_validation_failures.append("extract_image_prompt should keep 'Final Section'")

    # Test 3: extract_image_prompt - handles both excluded sections
    total_tests += 1
    test_md3 = """# Summary

## Resumo Executivo
Executive summary content.

## Key Findings
Important findings here.

## Recomendações
Recommendations here.
"""
    result3 = extract_image_prompt(test_md3)
    if "Resumo Executivo" in result3 or "Recomendações" in result3:
        all_validation_failures.append("extract_image_prompt should remove both excluded sections")
    if "Key Findings" not in result3:
        all_validation_failures.append("extract_image_prompt should keep 'Key Findings'")

    # Test 4: build_image_prompt - includes content
    total_tests += 1
    prompt = build_image_prompt("Test content")
    if "Test content" not in prompt:
        all_validation_failures.append("build_image_prompt should include original content")

    # Test 5: build_image_prompt - truncates long content
    total_tests += 1
    long_content = "A" * 5000
    truncated_prompt = build_image_prompt(long_content, max_length=1000)
    # Allow small overflow due to "..." suffix
    if len(truncated_prompt) > 1010:
        all_validation_failures.append(
            f"build_image_prompt should truncate near max_length, got {len(truncated_prompt)}"
        )
    if "..." not in truncated_prompt:
        all_validation_failures.append("build_image_prompt should add '...' when truncating")

    # Test 6: SummaryImageService instantiation
    total_tests += 1
    try:
        service = SummaryImageService()
        if service._image_generator is None:
            all_validation_failures.append("SummaryImageService should have image_generator")
    except Exception as e:
        all_validation_failures.append(f"SummaryImageService instantiation failed: {e}")

    # Test 7: _get_image_path format
    total_tests += 1
    try:
        service = SummaryImageService()
        path = service._get_image_path("exp_12345678", "doc_abcdef12", "png")
        expected_name = "exp_12345678_doc_abcdef12.png"
        if path.name != expected_name:
            all_validation_failures.append(f"Image path should be {expected_name}, got {path.name}")
    except Exception as e:
        all_validation_failures.append(f"_get_image_path test failed: {e}")

    # Test 8: append_image_to_markdown uses static URL
    total_tests += 1
    try:
        service = SummaryImageService()
        original = "# Summary\n\nContent here."
        updated = service.append_image_to_markdown(
            original, Path("/any/path/to/exp_123_doc_456.png")
        )
        if "## Ilustração" not in updated:
            all_validation_failures.append("append_image_to_markdown should add Ilustração section")
        if "/static/document/images/exp_123_doc_456.png" not in updated:
            all_validation_failures.append("append_image_to_markdown should use static URL path")
    except Exception as e:
        all_validation_failures.append(f"append_image_to_markdown test failed: {e}")

    # Test 9: get_summary_image_service singleton
    total_tests += 1
    try:
        import synth_lab.services.summary_image_service as svc_module

        svc_module._summary_image_service = None
        svc1 = get_summary_image_service()
        svc2 = get_summary_image_service()
        if svc1 is not svc2:
            all_validation_failures.append("get_summary_image_service should return singleton")
    except Exception as e:
        all_validation_failures.append(f"Singleton test failed: {e}")

    # Test 10: IMAGES_DIR is correctly set
    total_tests += 1
    expected_suffix = Path("output") / "document" / "images"
    if not str(IMAGES_DIR).endswith(str(expected_suffix)):
        all_validation_failures.append(
            f"IMAGES_DIR should end with {expected_suffix}, got {IMAGES_DIR}"
        )

    # Final validation result
    if all_validation_failures:
        failed = len(all_validation_failures)
        print(f"❌ VALIDATION FAILED - {failed} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Function is validated and formal tests can now be written")
        sys.exit(0)
