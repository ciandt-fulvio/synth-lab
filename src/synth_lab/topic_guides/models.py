"""
Topic Guides Data Models

This module defines the core data structures for the topic guides feature:
- FileType enum for supported file types
- FileDescription for AI-generated file descriptions
- ContextFile for individual context files in a topic guide
- SummaryFile for summary.md representation
- TopicGuide for complete topic guide representation

Third-party dependencies: None (uses only standard library)

Sample Input:
    topic_guide = TopicGuide(
        name="amazon-ecommerce",
        path=Path("data/topic_guides/amazon-ecommerce"),
        files=[ContextFile(...), ContextFile(...)],
        ...
    )

Expected Output:
    Structured data models for validation and serialization
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class FileType(Enum):
    """Supported file types for topic guide context materials."""

    PNG = "png"
    JPEG = "jpeg"
    PDF = "pdf"
    MD = "md"
    TXT = "txt"

    @classmethod
    def from_extension(cls, extension: str) -> "FileType | None":
        """
        Convert file extension to FileType enum.

        Args:
            extension: File extension (with or without leading dot)

        Returns:
            FileType enum member or None if not supported
        """
        # Remove leading dot if present
        ext = extension.lower().lstrip(".")

        # Map common variations to canonical types
        ext_map = {
            "png": cls.PNG,
            "jpg": cls.JPEG,
            "jpeg": cls.JPEG,
            "pdf": cls.PDF,
            "md": cls.MD,
            "markdown": cls.MD,
            "txt": cls.TXT,
            "text": cls.TXT,
        }

        return ext_map.get(ext)


@dataclass
class FileDescription:
    """AI-generated description of a context file."""

    filename: str
    content_hash: str
    description: str
    generated_at: datetime
    is_placeholder: bool = False

    def to_markdown(self) -> str:
        """
        Convert to markdown format for summary.md FILE DESCRIPTION section.

        Stores full hash for accurate change detection, displays first 8 chars for readability.

        Returns:
            Markdown string with filename, hash, and description
        """
        lines = [
            f"- **{self.filename}** (hash: {self.content_hash})",
            f"  {self.description}",
        ]
        return "\n".join(lines)


@dataclass
class ContextFile:
    """Represents a single file in a topic guide directory."""

    filename: str
    path: Path
    file_type: FileType
    size_bytes: int
    content_hash: str
    is_documented: bool = False

    @property
    def is_supported(self) -> bool:
        """Check if file type is supported for documentation."""
        return self.file_type in [
            FileType.PNG,
            FileType.JPEG,
            FileType.PDF,
            FileType.MD,
            FileType.TXT,
        ]


@dataclass
class SummaryFile:
    """Represents the summary.md file structure."""

    path: Path
    context_description: str
    file_descriptions: list[FileDescription] = field(default_factory=list)

    def get_description_by_filename(self, filename: str) -> FileDescription | None:
        """
        Find file description by filename.

        Args:
            filename: Name of the file to find

        Returns:
            FileDescription if found, None otherwise
        """
        for desc in self.file_descriptions:
            if desc.filename == filename:
                return desc
        return None

    def get_description_by_hash(self, content_hash: str) -> FileDescription | None:
        """
        Find file description by content hash.

        Args:
            content_hash: MD5 hash of file content

        Returns:
            FileDescription if found, None otherwise
        """
        for desc in self.file_descriptions:
            if desc.content_hash == content_hash:
                return desc
        return None

    def to_markdown(self) -> str:
        """
        Convert to markdown format for writing to disk.

        Returns:
            Complete markdown content for summary.md
        """
        lines = [
            f"# contexto para o guide: {self.path.parent.name}",
            "",
            self.context_description,
            "",
            "## FILE DESCRIPTION",
            "",
        ]

        for desc in self.file_descriptions:
            lines.append(desc.to_markdown())
            lines.append("")

        return "\n".join(lines)


@dataclass
class TopicGuide:
    """Complete representation of a topic guide."""

    name: str
    path: Path
    summary_file: SummaryFile
    files: list[ContextFile] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def documented_count(self) -> int:
        """Count of files with AI-generated descriptions."""
        return sum(1 for f in self.files if f.is_documented)

    @property
    def undocumented_count(self) -> int:
        """Count of files without descriptions."""
        return sum(1 for f in self.files if not f.is_documented)

    @property
    def supported_files(self) -> list[ContextFile]:
        """Get all files with supported file types."""
        return [f for f in self.files if f.is_supported]

    @property
    def unsupported_files(self) -> list[ContextFile]:
        """Get all files with unsupported file types."""
        return [f for f in self.files if not f.is_supported]


if __name__ == "__main__":
    """Validation: Test all data models with real-world examples."""
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: FileType.from_extension with various inputs
    total_tests += 1
    test_cases = [
        (".png", FileType.PNG),
        ("jpg", FileType.JPEG),
        (".jpeg", FileType.JPEG),
        ("pdf", FileType.PDF),
        (".md", FileType.MD),
        ("markdown", FileType.MD),
        (".txt", FileType.TXT),
        ("svg", None),  # Unsupported
    ]
    for ext, expected in test_cases:
        result = FileType.from_extension(ext)
        if result != expected:
            all_validation_failures.append(
                f"FileType.from_extension('{ext}'): Expected {expected}, got {result}"
            )

    # Test 2: FileDescription.to_markdown format
    total_tests += 1
    desc = FileDescription(
        filename="test.png",
        content_hash="a3b5c7d9e1f3a5b7",
        description="A test image file",
        generated_at=datetime.now(),
        is_placeholder=False,
    )
    markdown = desc.to_markdown()
    if "**test.png**" not in markdown or "a3b5c7d9" not in markdown:
        all_validation_failures.append(
            f"FileDescription.to_markdown: Missing expected content in: {markdown}"
        )

    # Test 3: ContextFile.is_supported property
    total_tests += 1
    supported_file = ContextFile(
        filename="image.png",
        path=Path("data/topic_guides/test/image.png"),
        file_type=FileType.PNG,
        size_bytes=1024,
        content_hash="abc123",
    )
    if not supported_file.is_supported:
        all_validation_failures.append("ContextFile.is_supported: PNG should be supported")

    # Test 4: SummaryFile.get_description_by_filename
    total_tests += 1
    summary = SummaryFile(
        path=Path("data/topic_guides/test/summary.md"),
        context_description="Test context",
        file_descriptions=[desc],
    )
    found = summary.get_description_by_filename("test.png")
    if found != desc:
        all_validation_failures.append(
            f"SummaryFile.get_description_by_filename: Expected {desc}, got {found}"
        )

    # Test 5: SummaryFile.get_description_by_hash
    total_tests += 1
    found_by_hash = summary.get_description_by_hash("a3b5c7d9e1f3a5b7")
    if found_by_hash != desc:
        all_validation_failures.append(
            f"SummaryFile.get_description_by_hash: Expected {desc}, got {found_by_hash}"
        )

    # Test 6: SummaryFile.to_markdown format
    total_tests += 1
    markdown_output = summary.to_markdown()
    if "# contexto para o guide: test" not in markdown_output:
        all_validation_failures.append(
            "SummaryFile.to_markdown: Missing topic guide name in header"
        )
    if "## FILE DESCRIPTION" not in markdown_output:
        all_validation_failures.append(
            "SummaryFile.to_markdown: Missing FILE DESCRIPTION section"
        )

    # Test 7: TopicGuide.documented_count and properties
    total_tests += 1
    documented_file = ContextFile(
        filename="doc.pdf",
        path=Path("data/topic_guides/test/doc.pdf"),
        file_type=FileType.PDF,
        size_bytes=2048,
        content_hash="def456",
        is_documented=True,
    )
    guide = TopicGuide(
        name="test",
        path=Path("data/topic_guides/test"),
        summary_file=summary,
        files=[supported_file, documented_file],
    )
    if guide.documented_count != 1:
        all_validation_failures.append(
            f"TopicGuide.documented_count: Expected 1, got {guide.documented_count}"
        )
    if guide.undocumented_count != 1:
        all_validation_failures.append(
            f"TopicGuide.undocumented_count: Expected 1, got {guide.undocumented_count}"
        )
    if len(guide.supported_files) != 2:
        all_validation_failures.append(
            f"TopicGuide.supported_files: Expected 2, got {len(guide.supported_files)}"
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
        print("Models are validated and formal tests can now be written")
        sys.exit(0)
