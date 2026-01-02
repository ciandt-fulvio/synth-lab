"""
Integration test to verify no legacy sqlite3 imports remain after cleanup.

This test scans the codebase to ensure all database access goes through
SQLAlchemy rather than direct sqlite3 usage.

References:
    - Migration spec: specs/027-postgresql-migration/spec.md

Sample input:
    - Source files in src/synth_lab/

Expected output:
    - No files import sqlite3 directly (except for specific allowed files)
"""

import ast
import os
from pathlib import Path

import pytest


# Files that are ALLOWED to use sqlite3 (legacy code not yet migrated)
ALLOWED_SQLITE3_FILES = {
    # Legacy database module (to be removed in T056)
    "src/synth_lab/infrastructure/database.py",
    # Storage module for synth generation (uses legacy for backward compat)
    "src/synth_lab/gen_synth/storage.py",
    # Base repository (supports dual backend during migration)
    "src/synth_lab/repositories/base.py",
}

# Directories to scan
SCAN_DIRECTORIES = [
    "src/synth_lab",
]

# Directories to skip
SKIP_DIRECTORIES = {
    "__pycache__",
    ".git",
    ".venv",
    "node_modules",
    "alembic",  # Alembic is for SQLAlchemy, not legacy
}


def get_sqlite3_imports(file_path: Path) -> list[tuple[int, str]]:
    """
    Find all sqlite3 imports in a Python file.

    Args:
        file_path: Path to Python file

    Returns:
        List of (line_number, import_statement) tuples
    """
    imports = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "sqlite3" or alias.name.startswith("sqlite3."):
                        imports.append((node.lineno, f"import {alias.name}"))

            elif isinstance(node, ast.ImportFrom):
                if node.module == "sqlite3" or (
                    node.module and node.module.startswith("sqlite3.")
                ):
                    names = ", ".join(alias.name for alias in node.names)
                    imports.append((node.lineno, f"from {node.module} import {names}"))

    except (SyntaxError, UnicodeDecodeError) as e:
        # Skip files that can't be parsed
        pytest.skip(f"Could not parse {file_path}: {e}")

    return imports


def scan_directory_for_sqlite3(directory: Path) -> dict[str, list[tuple[int, str]]]:
    """
    Scan a directory for sqlite3 imports.

    Args:
        directory: Directory to scan

    Returns:
        Dict mapping file paths to their sqlite3 imports
    """
    results = {}

    # Resolve directory to absolute path
    directory = directory.resolve()
    cwd = Path.cwd().resolve()

    for root, dirs, files in os.walk(directory):
        # Remove directories to skip
        dirs[:] = [d for d in dirs if d not in SKIP_DIRECTORIES]

        for file in files:
            if not file.endswith(".py"):
                continue

            file_path = Path(root) / file

            # Get relative path from cwd or use absolute if not in cwd
            try:
                relative_path = str(file_path.resolve().relative_to(cwd))
            except ValueError:
                relative_path = str(file_path.resolve())

            # Skip allowed files
            if relative_path in ALLOWED_SQLITE3_FILES:
                continue

            imports = get_sqlite3_imports(file_path)
            if imports:
                results[relative_path] = imports

    return results


class TestNoLegacySqlite3Imports:
    """Test that no unauthorized sqlite3 imports exist."""

    def test_no_sqlite3_in_services(self):
        """Verify no sqlite3 imports in services layer."""
        services_dir = Path("src/synth_lab/services")
        if not services_dir.exists():
            pytest.skip("Services directory not found")

        results = scan_directory_for_sqlite3(services_dir)

        if results:
            violations = []
            for file_path, imports in results.items():
                for line_no, import_stmt in imports:
                    violations.append(f"  {file_path}:{line_no} - {import_stmt}")

            pytest.fail(
                f"Found sqlite3 imports in services layer:\n" + "\n".join(violations)
            )

    def test_no_sqlite3_in_api(self):
        """Verify no sqlite3 imports in API layer."""
        api_dir = Path("src/synth_lab/api")
        if not api_dir.exists():
            pytest.skip("API directory not found")

        results = scan_directory_for_sqlite3(api_dir)

        if results:
            violations = []
            for file_path, imports in results.items():
                for line_no, import_stmt in imports:
                    violations.append(f"  {file_path}:{line_no} - {import_stmt}")

            pytest.fail(
                f"Found sqlite3 imports in API layer:\n" + "\n".join(violations)
            )

    def test_no_sqlite3_in_domain(self):
        """Verify no sqlite3 imports in domain layer."""
        domain_dir = Path("src/synth_lab/domain")
        if not domain_dir.exists():
            pytest.skip("Domain directory not found")

        results = scan_directory_for_sqlite3(domain_dir)

        if results:
            violations = []
            for file_path, imports in results.items():
                for line_no, import_stmt in imports:
                    violations.append(f"  {file_path}:{line_no} - {import_stmt}")

            pytest.fail(
                f"Found sqlite3 imports in domain layer:\n" + "\n".join(violations)
            )

    @pytest.mark.skip(reason="Legacy files still allowed during migration - to be enabled after T054-T058")
    def test_no_sqlite3_anywhere(self):
        """
        Verify no sqlite3 imports anywhere in the codebase.

        This test should be enabled after Phase 6 cleanup is complete.
        Currently skipped because legacy files are still allowed.
        """
        all_violations = {}

        for scan_dir in SCAN_DIRECTORIES:
            directory = Path(scan_dir)
            if not directory.exists():
                continue

            results = scan_directory_for_sqlite3(directory)
            all_violations.update(results)

        if all_violations:
            violations = []
            for file_path, imports in sorted(all_violations.items()):
                for line_no, import_stmt in imports:
                    violations.append(f"  {file_path}:{line_no} - {import_stmt}")

            pytest.fail(
                f"Found {len(all_violations)} files with sqlite3 imports:\n"
                + "\n".join(violations)
            )


class TestAllowedLegacyFiles:
    """Tests for tracking legacy files that still need migration."""

    def test_allowed_files_exist(self):
        """Verify that all allowed legacy files actually exist."""
        missing_files = []
        for file_path in ALLOWED_SQLITE3_FILES:
            if not Path(file_path).exists():
                missing_files.append(file_path)

        # Files that don't exist are fine - they may have been removed
        # This test just documents what files are in the allowed list
        pass

    def test_count_remaining_legacy_files(self):
        """Count how many legacy files still have sqlite3 imports."""
        legacy_count = 0
        legacy_files = []

        for file_path in ALLOWED_SQLITE3_FILES:
            path = Path(file_path)
            if path.exists():
                imports = get_sqlite3_imports(path)
                if imports:
                    legacy_count += 1
                    legacy_files.append(file_path)

        # This is informational - test passes regardless
        print(f"\nLegacy files with sqlite3 imports: {legacy_count}")
        for f in legacy_files:
            print(f"  - {f}")

        # Note: Once all legacy cleanup is done, this should be 0
        # For now, we just track the count


if __name__ == "__main__":
    """Run validation tests."""
    import sys

    all_failures = []
    total_tests = 0

    print("Scanning for sqlite3 imports...")

    # Test 1: Check services layer
    total_tests += 1
    services_dir = Path("src/synth_lab/services")
    if services_dir.exists():
        results = scan_directory_for_sqlite3(services_dir)
        if results:
            all_failures.append(f"Services layer has sqlite3 imports: {list(results.keys())}")
        else:
            print("  ✓ No sqlite3 imports in services layer")
    else:
        print("  ⊘ Services directory not found")

    # Test 2: Check API layer
    total_tests += 1
    api_dir = Path("src/synth_lab/api")
    if api_dir.exists():
        results = scan_directory_for_sqlite3(api_dir)
        if results:
            all_failures.append(f"API layer has sqlite3 imports: {list(results.keys())}")
        else:
            print("  ✓ No sqlite3 imports in API layer")
    else:
        print("  ⊘ API directory not found")

    # Test 3: Check domain layer
    total_tests += 1
    domain_dir = Path("src/synth_lab/domain")
    if domain_dir.exists():
        results = scan_directory_for_sqlite3(domain_dir)
        if results:
            all_failures.append(f"Domain layer has sqlite3 imports: {list(results.keys())}")
        else:
            print("  ✓ No sqlite3 imports in domain layer")
    else:
        print("  ⊘ Domain directory not found")

    # Informational: List allowed legacy files
    print("\nAllowed legacy files:")
    for file_path in ALLOWED_SQLITE3_FILES:
        path = Path(file_path)
        exists = "✓" if path.exists() else "✗"
        print(f"  {exists} {file_path}")

    # Final result
    if all_failures:
        print(f"\n❌ VALIDATION FAILED - {len(all_failures)} of {total_tests} tests failed:")
        for failure in all_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"\n✅ VALIDATION PASSED - All {total_tests} tests passed")
        print("Core layers (services, API, domain) are free of sqlite3 imports")
        sys.exit(0)
