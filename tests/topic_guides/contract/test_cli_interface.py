"""
Contract Tests: CLI Interface for Topic Guides

Tests the CLI command structure, parameters, and output formats according to the
CLI Interface Contract (specs/006-topic-guides/contracts/cli-interface.md).

These are contract tests - they verify the external interface remains stable.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


class TestCreateCommand:
    """Contract tests for 'synthlab topic-guide create' command."""

    def test_create_command_success(self, tmp_path):
        """
        Test successful topic guide creation via CLI.

        Contract Requirements (cli-interface.md):
        - Command: synthlab topic-guide create --name <name>
        - Exit code: 0 on success
        - Output: Success message with ✓ prefix and path
        """
        # Set temporary data directory
        data_dir = tmp_path / "data" / "topic_guides"
        env = os.environ.copy()
        env["TOPIC_GUIDES_DIR"] = str(data_dir)

        result = subprocess.run(
            ["uv", "run", "python", "-m", "synth_lab", "topic-guide", "create", "--name", "test-guide"],
            capture_output=True,
            text=True,
            env=env,
        )

        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert "✓" in result.stdout, "Success symbol not found in output"
        assert "test-guide" in result.stdout, "Topic guide name not in output"
        assert "created successfully" in result.stdout, "Success message not in output"
        assert "Path:" in result.stdout, "Path label not in output"
        # Verify directory was actually created
        assert (data_dir / "test-guide").exists(), "Topic guide directory not created"
        assert (data_dir / "test-guide" / "summary.md").exists(), "summary.md not created"

    def test_create_command_duplicate_fails(self, tmp_path):
        """
        Test creating duplicate topic guide returns error.

        Contract Requirements:
        - Exit code: 1 on duplicate
        - Output: Error message with ✗ prefix and 'already exists'
        """
        data_dir = tmp_path / "data" / "topic_guides"
        env = os.environ.copy()
        env["TOPIC_GUIDES_DIR"] = str(data_dir)

        # Create first time
        subprocess.run(
            ["uv", "run", "python", "-m", "synth_lab", "topic-guide", "create", "--name", "duplicate"],
            env=env,
        )

        # Try to create again
        result = subprocess.run(
            ["uv", "run", "python", "-m", "synth_lab", "topic-guide", "create", "--name", "duplicate"],
            capture_output=True,
            text=True,
            env=env,
        )

        assert result.returncode == 1
        assert "✗" in result.stderr or "✗" in result.stdout
        assert "already exists" in result.stderr or "already exists" in result.stdout

    def test_create_command_invalid_name_fails(self, tmp_path):
        """
        Test creating topic guide with invalid name returns error.

        Contract Requirements:
        - Exit code: 2 on invalid name
        - Output: Error message about invalid characters
        - Invalid characters: / \\ : * ? " < > |
        """
        data_dir = tmp_path / "data" / "topic_guides"
        env = os.environ.copy()
        env["TOPIC_GUIDES_DIR"] = str(data_dir)

        invalid_names = [
            "invalid/name",
            "invalid\\name",
            "invalid:name",
            "invalid*name",
            'invalid"name',
        ]

        for name in invalid_names:
            result = subprocess.run(
                ["uv", "run", "python", "-m", "synth_lab", "topic-guide", "create", "--name", name],
                capture_output=True,
                text=True,
                env=env,
            )

            assert result.returncode == 2, f"Invalid name '{name}' should fail with code 2"
            output = result.stderr + result.stdout
            assert "✗" in output
            assert "Invalid" in output or "invalid" in output

    def test_create_command_missing_name_fails(self):
        """
        Test create command without --name parameter fails.

        Contract Requirements:
        - Should fail with usage error (exit code 2)
        """
        result = subprocess.run(
            ["uv", "run", "python", "-m", "synth_lab", "topic-guide", "create"],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
        # Typer typically shows usage/help on missing required params


class TestUpdateCommand:
    """Contract tests for 'synthlab topic-guide update' command."""

    def test_update_command_success(self, tmp_path):
        """
        Test successful topic guide update via CLI.

        Contract Requirements:
        - Command: synthlab topic-guide update --name <name>
        - Exit code: 0 on success
        - Output: Summary of operations (files documented, skipped, failed)
        """
        data_dir = tmp_path / "data" / "topic_guides"
        env = os.environ.copy()
        env["TOPIC_GUIDES_DIR"] = str(data_dir)
        env["OPENAI_API_KEY"] = "sk-test-key"  # Fake key for testing

        # Create topic guide first
        subprocess.run(
            ["uv", "run", "python", "-m", "synth_lab", "topic-guide", "create", "--name", "test"],
            env=env,
        )

        # Add a test file
        (data_dir / "test" / "test.txt").write_text("Test content")

        # Run update command
        result = subprocess.run(
            ["uv", "run", "python", "-m", "synth_lab", "topic-guide", "update", "--name", "test"],
            capture_output=True,
            text=True,
            env=env,
        )

        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert "Summary:" in result.stdout or "Updating" in result.stdout

    def test_update_command_nonexistent_guide_fails(self, tmp_path):
        """
        Test updating non-existent topic guide returns error.

        Contract Requirements:
        - Exit code: 1 on topic guide not found
        - Output: Error message with ✗ prefix
        """
        data_dir = tmp_path / "data" / "topic_guides"
        env = os.environ.copy()
        env["TOPIC_GUIDES_DIR"] = str(data_dir)

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "synth_lab",
                "topic-guide",
                "update",
                "--name",
                "nonexistent",
            ],
            capture_output=True,
            text=True,
            env=env,
        )

        assert result.returncode == 1
        output = result.stderr + result.stdout
        assert "✗" in output or "not found" in output.lower()


# Additional contract tests can be added as we implement more commands
# (list, show) in future phases
