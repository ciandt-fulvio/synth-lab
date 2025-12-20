"""
Summary File Management for Topic Guides

This module provides functions for creating, parsing, and writing summary.md files:
- create_initial_summary: Generate new summary.md with template content
- parse_summary: Read and parse existing summary.md files
- write_summary: Serialize SummaryFile to disk

Third-party dependencies: None (uses only standard library)

Sample Input:
    summary_file = create_initial_summary("test-guide", Path("data/topic_guides/test/summary.md"))
    write_summary(summary_file)

Expected Output:
    SummaryFile objects and disk I/O operations
"""

import re
from datetime import datetime
from pathlib import Path

from .internal_models import FileDescription, SummaryFile


def create_initial_summary(guide_name: str, summary_path: Path) -> SummaryFile:
    """
    Create a new SummaryFile with template content for a topic guide.

    Args:
        guide_name: Name of the topic guide
        summary_path: Path where summary.md will be created

    Returns:
        SummaryFile with empty context and no file descriptions

    Examples:
        >>> summary = create_initial_summary("test", Path("/tmp/summary.md"))
        >>> summary.context_description
        ''
        >>> len(summary.file_descriptions)
        0
    """
    return SummaryFile(
        path=summary_path,
        context_description="",
        file_descriptions=[],
    )


def parse_summary(summary_path: Path) -> SummaryFile:
    """
    Parse an existing summary.md file into a SummaryFile object.

    The parser handles:
    - Context description (text between header and FILE DESCRIPTION)
    - File descriptions in the FILE DESCRIPTION section
    - Missing FILE DESCRIPTION section (auto-appends on write)

    Format:
        # contexto para o guide: <name>

        <context description>

        ## FILE DESCRIPTION

        - **filename.ext** (hash: abc123...)
          Description text here

    Args:
        summary_path: Path to existing summary.md file

    Returns:
        SummaryFile object with parsed content

    Examples:
        >>> path = Path("data/topic_guides/test/summary.md")
        >>> summary = parse_summary(path)
        >>> summary.context_description
        'This is the context...'
    """
    content = summary_path.read_text()

    # Extract context description (text between header and FILE DESCRIPTION section)
    context_match = re.search(
        r"# contexto para o guide:.*?\n\n(.*?)(?=\n## FILE DESCRIPTION|\Z)",
        content,
        re.DOTALL,
    )
    context_description = context_match.group(1).strip() if context_match else ""

    # Parse file descriptions
    file_descriptions = []

    # Find FILE DESCRIPTION section
    file_desc_match = re.search(r"## FILE DESCRIPTION\n+(.*)", content, re.DOTALL)

    if file_desc_match:
        file_desc_section = file_desc_match.group(1)

        # Pattern: - **filename** (hash: full_hash_string)
        #            Description text
        pattern = r"- \*\*(.+?)\*\* \(hash: ([a-f0-9]+)\)\n  (.+?)(?=\n- \*\*|\Z)"

        for match in re.finditer(pattern, file_desc_section, re.DOTALL):
            filename = match.group(1)
            content_hash = match.group(2)  # Full MD5 hash (32 chars)
            description = match.group(3).strip()

            file_descriptions.append(
                FileDescription(
                    filename=filename,
                    content_hash=content_hash,
                    description=description,
                    generated_at=datetime.now(),
                    is_placeholder=False,
                )
            )

    return SummaryFile(
        path=summary_path,
        context_description=context_description,
        file_descriptions=file_descriptions,
    )


def add_file_description(
    summary_file: SummaryFile, file_description: FileDescription
) -> None:
    """
    Add or update file description in the summary file.

    If a description for the same filename AND different hash exists, it's replaced.
    If a description for the same filename AND same hash exists, skip (no update needed).
    Otherwise, the new description is appended.

    Args:
        summary_file: SummaryFile object to modify
        file_description: FileDescription to add or update

    Examples:
        >>> summary = SummaryFile(...)
        >>> desc = FileDescription(...)
        >>> add_file_description(summary, desc)
        >>> len(summary.file_descriptions) > 0
        True
    """
    # Check if description for this filename already exists
    for i, existing_desc in enumerate(summary_file.file_descriptions):
        if existing_desc.filename == file_description.filename:
            # If hash is the same, don't update (file unchanged)
            if existing_desc.content_hash == file_description.content_hash:
                return
            # If hash is different, replace (file was modified)
            summary_file.file_descriptions[i] = file_description
            return

    # Add new description (new file)
    summary_file.file_descriptions.append(file_description)


def has_file(summary_file: SummaryFile, content_hash: str) -> bool:
    """
    Check if file with matching content hash exists in summary.

    Used to skip unchanged files during update.

    Args:
        summary_file: SummaryFile object to check
        content_hash: MD5 hash of file content

    Returns:
        True if file with this hash is already documented

    Examples:
        >>> summary = SummaryFile(...)
        >>> has_file(summary, "abc123")
        False
    """
    return summary_file.get_description_by_hash(content_hash) is not None


def write_summary(summary_file: SummaryFile) -> None:
    """
    Write a SummaryFile object to disk.

    Creates parent directories if they don't exist.

    Args:
        summary_file: SummaryFile object to write

    Examples:
        >>> summary = SummaryFile(...)
        >>> write_summary(summary)
        # Writes to summary.path
    """
    # Ensure parent directory exists
    summary_file.path.parent.mkdir(parents=True, exist_ok=True)

    # Write markdown content
    content = summary_file.to_markdown()
    summary_file.path.write_text(content)


def load_topic_guide_context(topic_guide_name: str, base_dir: Path | None = None) -> str:
    """
    Load topic guide context for use in interviews.

    Parses summary.md and returns formatted file descriptions.

    Args:
        topic_guide_name: Name of the topic guide to load
        base_dir: Base directory for topic guides (defaults to data/topic_guides/)

    Returns:
        Formatted string with file descriptions, or empty string if not found

    Examples:
        >>> context = load_topic_guide_context("amazon-ecommerce")
        >>> "Available Context Materials:" in context
        True
    """
    if base_dir is None:
        from synth_lab.infrastructure.config import resolve_topic_guide_path

        guide_path = resolve_topic_guide_path(topic_guide_name)
        if guide_path is None:
            return ""
    else:
        guide_path = base_dir / topic_guide_name
    summary_path = guide_path / "summary.md"

    if not summary_path.exists():
        return ""

    try:
        summary_file = parse_summary(summary_path)

        if not summary_file.file_descriptions:
            return ""

        # Format for LLM context
        lines = []

        # Add context overview if available
        if summary_file.context_description:
            lines.append("CONTEXT OVERVIEW:")
            lines.append(summary_file.context_description)
            lines.append("")  # Blank line for readability

        # Add file descriptions
        lines.append("Available Context Materials:")
        for desc in summary_file.file_descriptions:
            lines.append(f"- {desc.filename}: {desc.description}")

        return "\n".join(lines)

    except Exception:
        return ""


if __name__ == "__main__":
    """Validation: Test summary file management with real files."""
    import sys
    import tempfile

    all_validation_failures = []
    total_tests = 0

    # Test 1: create_initial_summary generates correct structure
    total_tests += 1
    summary = create_initial_summary("test-guide", Path("/tmp/test/summary.md"))

    if summary.context_description != "":
        all_validation_failures.append(
            f"create_initial_summary context: Expected empty string, got '{summary.context_description}'"
        )

    if len(summary.file_descriptions) != 0:
        all_validation_failures.append(
            f"create_initial_summary file_descriptions: Expected 0, got {len(summary.file_descriptions)}"
        )

    markdown = summary.to_markdown()
    if "# contexto para o guide: test" not in markdown:
        all_validation_failures.append(
            "create_initial_summary markdown: Missing guide name in header"
        )

    if "## FILE DESCRIPTION" not in markdown:
        all_validation_failures.append(
            "create_initial_summary markdown: Missing FILE DESCRIPTION section"
        )

    # Test 2: write_summary creates file on disk
    total_tests += 1
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Path structure: .../write-test/summary.md so parent.name = "write-test"
        tmp_path = Path(tmp_dir) / "write-test" / "summary.md"
        summary = create_initial_summary("write-test", tmp_path)

        write_summary(summary)

        if not tmp_path.exists():
            all_validation_failures.append("write_summary: File was not created")

        content = tmp_path.read_text()
        if "# contexto para o guide: write-test" not in content:
            all_validation_failures.append("write_summary: Incorrect content written")

    # Test 3: parse_summary with empty FILE DESCRIPTION
    total_tests += 1
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / "summary.md"
        tmp_path.write_text(
            """# contexto para o guide: parse-test

This is a test context description.

## FILE DESCRIPTION
"""
        )

        parsed = parse_summary(tmp_path)

        if "test context description" not in parsed.context_description:
            all_validation_failures.append(
                f"parse_summary context: Expected context text, got '{parsed.context_description}'"
            )

        if len(parsed.file_descriptions) != 0:
            all_validation_failures.append(
                f"parse_summary file_descriptions: Expected 0, got {len(parsed.file_descriptions)}"
            )

    # Test 4: parse_summary with file descriptions
    total_tests += 1
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / "summary.md"
        tmp_path.write_text(
            """# contexto para o guide: with-files

Context here.

## FILE DESCRIPTION

- **image.png** (hash: abc123def456...)
  Screenshot of the homepage

- **doc.pdf** (hash: 789xyz123...)
  Technical documentation
"""
        )

        parsed = parse_summary(tmp_path)

        if len(parsed.file_descriptions) != 2:
            all_validation_failures.append(
                f"parse_summary with files: Expected 2 descriptions, got {len(parsed.file_descriptions)}"
            )

        if parsed.file_descriptions:
            first_desc = parsed.file_descriptions[0]
            if first_desc.filename != "image.png":
                all_validation_failures.append(
                    f"parse_summary filename: Expected 'image.png', got '{first_desc.filename}'"
                )

            if not first_desc.content_hash.startswith("abc123"):
                all_validation_failures.append(
                    f"parse_summary hash: Expected hash starting with 'abc123', got '{first_desc.content_hash}'"
                )

            if "Screenshot" not in first_desc.description:
                all_validation_failures.append(
                    "parse_summary description: Expected 'Screenshot' in description"
                )

    # Test 5: parse_summary missing FILE DESCRIPTION section
    total_tests += 1
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / "summary.md"
        tmp_path.write_text(
            """# contexto para o guide: missing-section

Just a context, no FILE DESCRIPTION section.
"""
        )

        parsed = parse_summary(tmp_path)

        if len(parsed.file_descriptions) != 0:
            all_validation_failures.append(
                f"parse_summary missing section: Expected 0 descriptions, got {len(parsed.file_descriptions)}"
            )

        # When written back, should include the section
        write_summary(parsed)
        content = tmp_path.read_text()

        if "## FILE DESCRIPTION" not in content:
            all_validation_failures.append(
                "parse_summary missing section: Should auto-append FILE DESCRIPTION on write"
            )

    # Test 6: Round-trip test (write and parse)
    total_tests += 1
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / "summary.md"

        # Create with file descriptions
        desc = FileDescription(
            filename="test.png",
            content_hash="abc123",
            description="A test file",
            generated_at=datetime.now(),
        )

        original = SummaryFile(
            path=tmp_path,
            context_description="Round trip test",
            file_descriptions=[desc],
        )

        write_summary(original)
        parsed = parse_summary(tmp_path)

        if len(parsed.file_descriptions) != 1:
            all_validation_failures.append(
                f"Round-trip test: Expected 1 description, got {len(parsed.file_descriptions)}"
            )

        if parsed.file_descriptions and parsed.file_descriptions[0].filename != "test.png":
            all_validation_failures.append(
                "Round-trip test: Filename mismatch after round-trip"
            )

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
        print("Summary manager functions are validated and formal tests can now be written")
        sys.exit(0)
