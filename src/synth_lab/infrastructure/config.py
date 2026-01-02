"""
Centralized configuration for synth-lab.

Environment variables and default settings for database, logging, and LLM client.

Environment Variables:
    DATABASE_URL: PostgreSQL connection string (REQUIRED)
        Format: "postgresql://user:pass@host:5432/dbname"
    LOG_LEVEL: Logging level (default: INFO) - set by Makefile based on ENV
    SYNTHLAB_DEFAULT_MODEL: Default LLM model (default: gpt-4o-mini)
    OPENAI_API_KEY: OpenAI API key (required for LLM operations)
    SQL_ECHO: Set to "true" to enable SQL query logging
    WORKERS: Number of workers for connection pool sizing (default: 4)
"""

import os
import sys
from pathlib import Path

# Base paths
# __file__ is src/synth_lab/infrastructure/config.py
# parent chain: infrastructure -> synth_lab -> src -> project_root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
DATA_DIR = PROJECT_ROOT / "data"

# Database configuration
# DATABASE_URL is REQUIRED and must be a PostgreSQL URL
DATABASE_URL = os.getenv("DATABASE_URL")

# Output directories (execution data, not versioned)
SYNTHS_DIR = OUTPUT_DIR / "synths"
SYNTHS_JSON_PATH = SYNTHS_DIR / "synths.json"
AVATARS_DIR = SYNTHS_DIR / "avatar"
TOPIC_GUIDES_DIR = OUTPUT_DIR / "topic_guides"
TRACES_DIR = OUTPUT_DIR / "traces"

# Logging configuration
# LOG_LEVEL from Makefile (ENV-based), fallback to SYNTHLAB_LOG_LEVEL
LOG_LEVEL = os.getenv("LOG_LEVEL", os.getenv(
    "SYNTHLAB_LOG_LEVEL", "INFO")).upper()


def configure_logging() -> None:
    """
    Configure loguru with the LOG_LEVEL from environment.

    Removes default handler and adds a new one with proper level and format.
    Should be called once at application startup.
    """
    from loguru import logger

    # Remove default handler
    logger.remove()

    # Add handler with configured level
    logger.add(
        sys.stderr,
        level=LOG_LEVEL,
        format="<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>",
        colorize=True,
    )

    logger.debug(f"Logging configured with level: {LOG_LEVEL}")


# LLM configuration
DEFAULT_MODEL = os.getenv("SYNTHLAB_DEFAULT_MODEL", "gpt-4o-mini")
REASONING_MODEL = "gpt-4.1-mini"  # Fast model for executive summary generation
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_TIMEOUT = float(os.getenv("SYNTHLAB_LLM_TIMEOUT", "120.0"))
LLM_MAX_RETRIES = int(os.getenv("SYNTHLAB_LLM_MAX_RETRIES", "3"))

# API configuration
API_HOST = os.getenv("SYNTHLAB_API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("SYNTHLAB_API_PORT", "8000"))


def ensure_directories() -> None:
    """Ensure all required directories exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SYNTHS_DIR.mkdir(parents=True, exist_ok=True)
    AVATARS_DIR.mkdir(parents=True, exist_ok=True)
    TOPIC_GUIDES_DIR.mkdir(parents=True, exist_ok=True)
    TRACES_DIR.mkdir(parents=True, exist_ok=True)


def resolve_topic_guide_path(topic_guide_name: str) -> Path | None:
    """
    Resolve topic guide path with fallback to examples directory.

    Searches for the topic guide in:
    1. TOPIC_GUIDES_DIR / topic_guide_name (user-created guides)
    2. TOPIC_GUIDES_DIR / "examples" / topic_guide_name (versioned examples)

    Args:
        topic_guide_name: Name of the topic guide directory

    Returns:
        Path to the topic guide directory, or None if not found
    """
    # Try user-created guides first
    user_path = TOPIC_GUIDES_DIR / topic_guide_name
    if user_path.exists():
        return user_path

    # Fall back to examples directory
    examples_path = TOPIC_GUIDES_DIR / "examples" / topic_guide_name
    if examples_path.exists():
        return examples_path

    return None


if __name__ == "__main__":
    import sys

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Test 1: PROJECT_ROOT exists
    total_tests += 1
    if not PROJECT_ROOT.exists():
        all_validation_failures.append(
            f"PROJECT_ROOT does not exist: {PROJECT_ROOT}")

    # Test 2: OUTPUT_DIR can be created
    total_tests += 1
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        all_validation_failures.append(f"Cannot create OUTPUT_DIR: {e}")

    # Test 3: Default values are set
    total_tests += 1
    if DEFAULT_MODEL != "gpt-4o-mini":
        all_validation_failures.append(
            f"DEFAULT_MODEL should be gpt-4o-mini, got {DEFAULT_MODEL}")

    # Test 4: LOG_LEVEL is valid
    total_tests += 1
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if LOG_LEVEL.upper() not in valid_levels:
        all_validation_failures.append(
            f"LOG_LEVEL {LOG_LEVEL} not in {valid_levels}")

    # Test 5: ensure_directories works
    total_tests += 1
    try:
        ensure_directories()
    except Exception as e:
        all_validation_failures.append(f"ensure_directories failed: {e}")

    # Test 6: resolve_topic_guide_path returns None for non-existent
    total_tests += 1
    result = resolve_topic_guide_path("nonexistent-guide-xyz")
    if result is not None:
        all_validation_failures.append(
            f"resolve_topic_guide_path should return None for non-existent, got {result}"
        )

    # Test 7: resolve_topic_guide_path finds examples directory
    total_tests += 1
    examples_dir = TOPIC_GUIDES_DIR / "examples"
    if examples_dir.exists():
        # Find any existing example
        existing_examples = [
            d.name for d in examples_dir.iterdir() if d.is_dir()]
        if existing_examples:
            example_name = existing_examples[0]
            result = resolve_topic_guide_path(example_name)
            expected = examples_dir / example_name
            if result != expected:
                all_validation_failures.append(
                    f"resolve_topic_guide_path({example_name}): expected {expected}, got {result}"
                )

    # Final validation result
    if all_validation_failures:
        print(
            f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(
            f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        print(f"  PROJECT_ROOT: {PROJECT_ROOT}")
        print(f"  DATABASE_URL: {DATABASE_URL or '(not set - required for runtime)'}")
        print(f"  DEFAULT_MODEL: {DEFAULT_MODEL}")
        sys.exit(0)
