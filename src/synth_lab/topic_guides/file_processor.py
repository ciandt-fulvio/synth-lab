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
