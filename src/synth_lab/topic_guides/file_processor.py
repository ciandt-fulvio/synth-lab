"""
File Processing Utilities for Topic Guides

This module provides utilities for processing files in topic guide directories:
- File type detection from extensions
- Content hashing for change detection
- Directory scanning and filtering

Third-party dependencies: None (uses only standard library)

Sample Input:
    file_path = Path("data/topic_guides/test/image.png")
    file_type = detect_file_type(file_path)  # Returns FileType.PNG
    content_hash = compute_file_hash(file_path)  # Returns MD5 hash string

Expected Output:
    FileType enum members and MD5 hash strings
"""

import hashlib
from pathlib import Path

from synth_lab.topic_guides.models import FileType
from synth_lab.trace_visualizer import Tracer, SpanType, SpanStatus


def detect_file_type(file_path: Path) -> FileType | None:
    """
    Detect file type from file extension.

    Args:
        file_path: Path to the file

    Returns:
        FileType enum member or None if unsupported

    Examples:
        >>> detect_file_type(Path("image.png"))
        FileType.PNG
        >>> detect_file_type(Path("doc.pdf"))
        FileType.PDF
        >>> detect_file_type(Path("logo.svg"))
        None
    """
    return FileType.from_extension(file_path.suffix)


def compute_file_hash(file_path: Path) -> str:
    """
    Compute MD5 hash of file content for change detection.

    MD5 is used (rather than SHA-256) because:
    - No security requirement (only deduplication)
    - Significantly faster for large files
    - Shorter hash strings in summary.md

    Args:
        file_path: Path to the file to hash

    Returns:
        MD5 hash as hexadecimal string

    Examples:
        >>> path = Path("data/topic_guides/test/file.txt")
        >>> hash1 = compute_file_hash(path)
        >>> # Modify file
        >>> hash2 = compute_file_hash(path)
        >>> hash1 != hash2
        True
    """
    md5_hash = hashlib.md5()

    with open(file_path, "rb") as f:
        # Read in 64KB chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(65536), b""):
            md5_hash.update(chunk)

    return md5_hash.hexdigest()


def scan_directory(directory: Path) -> list[Path]:
    """
    Scan directory for all files, excluding summary.md.

    Args:
        directory: Path to the topic guide directory

    Returns:
        List of Path objects for all files except summary.md

    Examples:
        >>> files = scan_directory(Path("data/topic_guides/test"))
        >>> "summary.md" in [f.name for f in files]
        False
    """
    if not directory.exists():
        return []

    all_files = [f for f in directory.iterdir() if f.is_file()]
    # Exclude summary.md
    return [f for f in all_files if f.name != "summary.md"]


def is_supported_type(file_path: Path) -> bool:
    """
    Check if file type is supported for documentation.

    Args:
        file_path: Path to the file to check

    Returns:
        True if file type is supported, False otherwise

    Examples:
        >>> is_supported_type(Path("image.png"))
        True
        >>> is_supported_type(Path("video.mp4"))
        False
    """
    file_type = detect_file_type(file_path)
    return file_type is not None


def extract_pdf_text(pdf_path: Path, max_pages: int = 2) -> str:
    """
    Extract text preview from PDF file using pdfplumber.

    Extracts text from first N pages for LLM summarization.

    Args:
        pdf_path: Path to PDF file
        max_pages: Maximum number of pages to extract (default: 2)

    Returns:
        Extracted text string, or empty string on error

    Examples:
        >>> text = extract_pdf_text(Path("doc.pdf"))
        >>> len(text) > 0
        True
    """
    import pdfplumber

    try:
        with pdfplumber.open(pdf_path) as pdf:
            text_parts = []
            for page_num, page in enumerate(pdf.pages[:max_pages]):
                text = page.extract_text()
                if text:
                    text_parts.append(text)

            return "\n\n".join(text_parts)
    except Exception:
        # Return empty string for corrupted/unreadable PDFs
        return ""


def encode_image_for_vision(image_path: Path) -> str:
    """
    Encode image file to base64 for OpenAI Vision API.

    Args:
        image_path: Path to PNG or JPEG image

    Returns:
        Base64 encoded string

    Examples:
        >>> encoded = encode_image_for_vision(Path("image.png"))
        >>> len(encoded) > 0
        True
    """
    import base64

    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def call_openai_api(
    prompt: str, image_base64: str | None = None, api_key: str | None = None, tracer: Tracer | None = None
) -> str:
    """
    Call OpenAI API with retry logic and exponential backoff.

    Uses gpt-4o-mini model with tenacity for retries.

    Args:
        prompt: Text prompt for the LLM
        image_base64: Optional base64-encoded image for Vision API
        api_key: OpenAI API key (uses OPENAI_API_KEY env var if not provided)
        tracer: Optional Tracer for recording trace data

    Returns:
        LLM response text

    Raises:
        APIError: After max retries exhausted
    """
    import os

    from openai import OpenAI
    from tenacity import retry, stop_after_attempt, wait_exponential

    # Get API key from parameter or environment
    if api_key is None:
        api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")

    client = OpenAI(api_key=api_key)

    # Start span if tracer provided
    span = None
    if tracer:
        span = tracer.start_span(SpanType.LLM_CALL, attributes={
            "prompt": prompt[:500] + "..." if len(prompt) > 500 else prompt,
            "model": "gpt-4o-mini",
            "has_image": image_base64 is not None,
        })

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _make_request():
        if image_base64:
            # Vision API call
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{image_base64}"},
                            },
                        ],
                    }
                ],
                max_tokens=60,
                temperature=0.2,
            )
        else:
            # Text-only API call
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=60,
                temperature=0.2,
            )

        return response

    try:
        response = _make_request()
        content = response.choices[0].message.content

        # Record response in span
        if span:
            span.set_attribute("response", content)
            if hasattr(response, 'usage') and response.usage:
                span.set_attribute("tokens_input", response.usage.prompt_tokens)
                span.set_attribute("tokens_output", response.usage.completion_tokens)
            span.set_status(SpanStatus.SUCCESS)

        return content
    except Exception as e:
        if span:
            span.set_status(SpanStatus.ERROR)
            span.set_attribute("error_message", str(e))
        raise
    finally:
        if span:
            span.__exit__(None, None, None)


def generate_file_description(file_path: Path, api_key: str | None = None) -> str | None:
    """
    Generate AI description for a file based on its type.

    Routes to appropriate LLM prompt based on file type (image, PDF, text).

    Args:
        file_path: Path to the file to describe
        api_key: Optional OpenAI API key

    Returns:
        Generated description, or None on API failure

    Examples:
        >>> desc = generate_file_description(Path("image.png"))
        >>> isinstance(desc, str)
        True
    """
    file_type = detect_file_type(file_path)

    if not file_type:
        return None

    try:
        if file_type in [FileType.PNG, FileType.JPEG]:
            # Image description via Vision API
            image_base64 = encode_image_for_vision(file_path)
            prompt = (
                "Describe this image in 1-2 sentences. Focus on what it shows, "
                "its purpose, and key visible elements. Be concise and specific."
            )
            return call_openai_api(prompt, image_base64=image_base64, api_key=api_key)

        elif file_type == FileType.PDF:
            # PDF description via text extraction
            text_preview = extract_pdf_text(file_path)
            if not text_preview:
                return "PDF document (content could not be extracted)"

            prompt = (
                f"Summarize this PDF content in 1-2 sentences:\n\n{text_preview[:2000]}"
            )
            return call_openai_api(prompt, api_key=api_key)

        elif file_type in [FileType.MD, FileType.TXT]:
            # Text/Markdown description
            text_content = file_path.read_text()[:2000]  # First 2000 chars
            prompt = f"Summarize this document in 1-2 sentences:\n\n{text_content}"
            return call_openai_api(prompt, api_key=api_key)

    except Exception:
        # Return None on any API failure
        return None

    return None


def generate_context_overview(file_descriptions: list[str], api_key: str | None = None) -> str | None:
    """
    Generate contextual overview based on all file descriptions in the topic guide.

    Analyzes all file descriptions and creates a 2-3 sentence summary of what
    the topic guide is about, what materials are included, and their purpose.

    Args:
        file_descriptions: List of individual file descriptions
        api_key: Optional OpenAI API key

    Returns:
        Generated context overview, or None on API failure

    Examples:
        >>> descriptions = ["Screenshot of homepage", "PDF user manual", "Wireframe mockup"]
        >>> overview = generate_context_overview(descriptions)
        >>> isinstance(overview, str)
        True
    """
    if not file_descriptions:
        return ""

    try:
        # Build prompt with all file descriptions
        files_list = "\n".join(f"- {desc}" for desc in file_descriptions)
        prompt = (
            f"Based on these files, write a 2-3 sentence overview describing what this "
            f"topic guide is about, what materials are included, and their purpose:\n\n"
            f"{files_list}\n\n"
            f"Be concise and focus on the overall context and purpose."
        )

        return call_openai_api(prompt, api_key=api_key)

    except Exception:
        # Return None on any API failure
        return None


if __name__ == "__main__":
    """Validation: Test file processing functions with real files."""
    import sys
    import tempfile

    all_validation_failures = []
    total_tests = 0

    # Test 1: detect_file_type with various extensions
    total_tests += 1
    test_cases = [
        (Path("test.png"), FileType.PNG),
        (Path("photo.jpg"), FileType.JPEG),
        (Path("photo.jpeg"), FileType.JPEG),
        (Path("doc.pdf"), FileType.PDF),
        (Path("readme.md"), FileType.MD),
        (Path("notes.txt"), FileType.TXT),
        (Path("logo.svg"), None),  # Unsupported
        (Path("video.mp4"), None),  # Unsupported
    ]

    for path, expected_type in test_cases:
        result = detect_file_type(path)
        if result != expected_type:
            all_validation_failures.append(
                f"detect_file_type({path}): Expected {expected_type}, got {result}"
            )

    # Test 2: compute_file_hash produces consistent hashes
    total_tests += 1
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as tmp_file:
        tmp_path = Path(tmp_file.name)
        tmp_file.write("Test content for hashing")

    try:
        hash1 = compute_file_hash(tmp_path)
        hash2 = compute_file_hash(tmp_path)

        if hash1 != hash2:
            all_validation_failures.append(
                f"compute_file_hash consistency: Two hashes of same file don't match"
            )

        if len(hash1) != 32:  # MD5 is always 32 hex chars
            all_validation_failures.append(
                f"compute_file_hash format: Expected 32 char hash, got {len(hash1)}"
            )
    finally:
        tmp_path.unlink()

    # Test 3: compute_file_hash detects changes
    total_tests += 1
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as tmp_file:
        tmp_path = Path(tmp_file.name)
        tmp_file.write("Original content")

    try:
        hash_before = compute_file_hash(tmp_path)

        # Modify file
        with open(tmp_path, "w") as f:
            f.write("Modified content")

        hash_after = compute_file_hash(tmp_path)

        if hash_before == hash_after:
            all_validation_failures.append(
                "compute_file_hash change detection: Hashes should differ after modification"
            )
    finally:
        tmp_path.unlink()

    # Test 4: compute_file_hash handles binary files (images)
    total_tests += 1
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".bin") as tmp_file:
        tmp_path = Path(tmp_file.name)
        # Write some binary data
        tmp_file.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00")

    try:
        binary_hash = compute_file_hash(tmp_path)
        if len(binary_hash) != 32:
            all_validation_failures.append(
                f"compute_file_hash binary: Expected 32 char hash, got {len(binary_hash)}"
            )
    finally:
        tmp_path.unlink()

    # Final validation result
    if all_validation_failures:
        print(
            f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:"
        )
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("File processor functions are validated and formal tests can now be written")
        sys.exit(0)
