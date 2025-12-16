"""
CLI Commands for Topic Guides

This module implements the Typer CLI interface for topic guide management:
- create: Create new topic guide directory with summary.md
- update: Scan directory and generate AI descriptions (Phase 4)
- list: List all topic guides (Phase 6)
- show: Display topic guide details (Phase 6)

Third-party dependencies:
- typer: https://typer.tiangolo.com/
- rich: https://rich.readthedocs.io/
- loguru: https://loguru.readthedocs.io/

Sample Input:
    $ synthlab topic-guide create --name amazon-ecommerce

Expected Output:
    ✓ Topic guide 'amazon-ecommerce' created successfully
      Path: data/topic_guides/amazon-ecommerce
"""

import os
import re
import sys
from pathlib import Path

import typer
from loguru import logger
from rich.console import Console

from synth_lab.topic_guides.summary_manager import create_initial_summary, write_summary

# Create Typer app for topic-guide subcommand group
# This becomes the "synthlab topic-guide" command with sub-commands like "create", "update", etc.
app = typer.Typer(
    help="Manage topic guides with multi-modal context materials",
    no_args_is_help=True,
)

console = Console()

# Configure loguru
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO",
)

# Default base directory for topic guides
DEFAULT_BASE_DIR = Path("data/topic_guides")


def get_base_dir() -> Path:
    """Get topic guides base directory from env var or default."""
    env_dir = os.environ.get("TOPIC_GUIDES_DIR")
    return Path(env_dir) if env_dir else DEFAULT_BASE_DIR


def validate_topic_guide_name(name: str) -> bool:
    """
    Validate topic guide name according to contract.

    Invalid characters: / \\ : * ? " < > |

    Args:
        name: Topic guide name to validate

    Returns:
        True if valid, False otherwise
    """
    # Pattern for invalid characters
    invalid_chars = r'[/\\:*?"<>|]'
    return not re.search(invalid_chars, name)


def create_topic_guide(name: str, base_dir: Path | None = None) -> Path:
    """
    Create a new topic guide directory with initialized summary.md.

    This is the core implementation function called by the CLI command.

    Args:
        name: Name of the topic guide
        base_dir: Base directory for topic guides (defaults to data/topic_guides)

    Returns:
        Path to the created topic guide directory

    Raises:
        FileExistsError: If topic guide already exists
        ValueError: If name is invalid

    Examples:
        >>> guide_path = create_topic_guide("test-guide")
        >>> guide_path.exists()
        True
        >>> (guide_path / "summary.md").exists()
        True
    """
    if not validate_topic_guide_name(name):
        raise ValueError(
            f"Invalid topic guide name '{name}'. "
            "Name cannot contain special characters: / \\ : * ? \" < > |"
        )

    if base_dir is None:
        base_dir = get_base_dir()

    guide_path = base_dir / name

    # Check if already exists
    if guide_path.exists():
        raise FileExistsError(f"Topic guide '{name}' already exists at {guide_path}")

    try:
        # Create directory structure (parents=True creates base_dir if needed)
        guide_path.mkdir(parents=True, exist_ok=False)
        logger.info(f"Created topic guide directory: {guide_path}")

        # Create and write initial summary.md
        summary_path = guide_path / "summary.md"
        summary_file = create_initial_summary(name, summary_path)
        write_summary(summary_file)
        logger.info(f"Initialized summary.md: {summary_path}")

        return guide_path

    except PermissionError as e:
        logger.error(f"Permission denied creating topic guide: {e}")
        raise
    except OSError as e:
        logger.error(f"File system error creating topic guide: {e}")
        raise


@app.command("create")
def create_command(
    name: str = typer.Option(..., "--name", help="Name of the topic guide to create"),
) -> None:
    """
    Create a new topic guide directory with initialized summary.md file.

    The topic guide directory will be created at data/topic_guides/<name>/ with an
    empty summary.md file ready for contextual materials.

    Examples:
        synthlab topic-guide create --name amazon-ecommerce
        synthlab topic-guide create --name mobile-app-study
    """
    try:
        guide_path = create_topic_guide(name)

        # Success message (Contract: ✓ prefix, includes path, usage hint)
        console.print(f"✓ Topic guide '[cyan]{name}[/cyan]' created successfully", style="green")
        console.print(f"  Path: {guide_path}")
        console.print(
            f"  Add files to this directory and run "
            f"'[bold]synthlab topic-guide update --name {name}[/bold]'"
        )

        sys.exit(0)

    except FileExistsError:
        # Contract: Exit code 1 for duplicate, ✗ prefix
        console.print(f"✗ Error: Topic guide '[cyan]{name}[/cyan]' already exists", style="red")
        console.print(
            f"  Use '[bold]synthlab topic-guide update --name {name}[/bold]' to update it"
        )
        sys.exit(1)

    except ValueError as e:
        # Contract: Exit code 2 for invalid name
        console.print(f"✗ Error: {e}", style="red")
        sys.exit(2)

    except (PermissionError, OSError) as e:
        # Contract: Exit code 3 for file system errors
        console.print(f"✗ Error: File system error", style="red")
        console.print(f"  {e}")
        sys.exit(3)


@app.command("update")
def update_command(
    name: str = typer.Option(..., "--name", help="Name of the topic guide to update"),
    force: bool = typer.Option(
        False, "--force", help="Re-process all files even if unchanged"
    ),
) -> None:
    """
    Update topic guide with AI descriptions for files.

    Scans the topic guide directory for new/modified files and generates AI descriptions
    using OpenAI's gpt-4o-mini model.

    Examples:
        synthlab topic-guide update --name amazon-ecommerce
        synthlab topic-guide update --name mobile-study --force
    """
    import os
    from datetime import datetime

    from synth_lab.topic_guides.file_processor import (
        compute_file_hash,
        generate_file_description,
        is_supported_type,
        scan_directory,
    )
    from synth_lab.topic_guides.models import FileDescription
    from synth_lab.topic_guides.summary_manager import (
        add_file_description,
        has_file,
        parse_summary,
        write_summary,
    )

    try:
        # Check if topic guide exists
        base_dir = get_base_dir()
        guide_path = base_dir / name

        if not guide_path.exists():
            console.print(
                f"✗ Error: Topic guide '[cyan]{name}[/cyan]' not found", style="red"
            )
            console.print(
                f"  Create it first: [bold]synthlab topic-guide create --name {name}[/bold]"
            )
            sys.exit(1)

        # Check for OPENAI_API_KEY
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            console.print("✗ Error: OpenAI API key not found", style="red")
            console.print("  Set OPENAI_API_KEY environment variable")
            sys.exit(1)

        console.print(f"Updating topic guide '[cyan]{name}[/cyan]'...\n")
        logger.info(f"Starting update for topic guide: {guide_path}")

        # Load summary.md
        summary_path = guide_path / "summary.md"
        summary_file = parse_summary(summary_path)

        # Scan directory for files
        files = scan_directory(guide_path)
        logger.info(f"Found {len(files)} files in directory")

        # Track statistics
        documented_count = 0
        unchanged_count = 0
        skipped_count = 0
        failed_count = 0
        unsupported_files = []

        console.print("Processing files:")

        # Process each file
        for file_path in files:
            filename = file_path.name

            # Check if supported type
            if not is_supported_type(file_path):
                console.print(f"  ⚠ {filename} - unsupported file type (skipped)", style="yellow")
                unsupported_files.append(filename)
                skipped_count += 1
                continue

            # Compute hash
            try:
                content_hash = compute_file_hash(file_path)
            except Exception as e:
                logger.error(f"Failed to compute hash for {filename}: {e}")
                console.print(f"  ⚠ {filename} - corrupted file (skipped)", style="yellow")
                skipped_count += 1
                continue

            # Check if file already documented with same hash
            if not force and has_file(summary_file, content_hash):
                console.print(f"  ⊘ {filename} - unchanged (skipped)")
                unchanged_count += 1
                continue

            # Generate description via LLM
            try:
                description = generate_file_description(file_path, api_key=api_key)

                if description is None:
                    # API failure - add placeholder
                    description = "API failure - manual documentation needed"
                    is_placeholder = True
                    console.print(f"  ⚠ {filename} - API failure (placeholder added)", style="yellow")
                    failed_count += 1
                else:
                    is_placeholder = False
                    console.print(f"  ✓ {filename} - described successfully", style="green")
                    documented_count += 1

                # Add to summary
                file_desc = FileDescription(
                    filename=filename,
                    content_hash=content_hash,
                    description=description,
                    generated_at=datetime.now(),
                    is_placeholder=is_placeholder,
                )
                add_file_description(summary_file, file_desc)

            except Exception as e:
                logger.error(f"Failed to process {filename}: {e}")
                # Add placeholder on error
                file_desc = FileDescription(
                    filename=filename,
                    content_hash=content_hash,
                    description="Error during processing - manual documentation needed",
                    generated_at=datetime.now(),
                    is_placeholder=True,
                )
                add_file_description(summary_file, file_desc)
                console.print(f"  ⚠ {filename} - processing error (placeholder added)", style="yellow")
                failed_count += 1

        # Write updated summary
        write_summary(summary_file)
        logger.info(f"Updated summary file: {summary_path}")

        # Display summary
        console.print(f"\n[bold]Summary:[/bold]")
        if documented_count > 0:
            console.print(f"  - {documented_count} file(s) documented", style="green")
        if unchanged_count > 0:
            console.print(f"  - {unchanged_count} file(s) unchanged")
        if skipped_count > 0:
            console.print(f"  - {skipped_count} file(s) skipped (unsupported/corrupted)", style="yellow")
        if failed_count > 0:
            console.print(f"  - {failed_count} file(s) failed (placeholders added)", style="yellow")

        console.print(f"\nUpdated: [cyan]{summary_path}[/cyan]")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Update command failed: {e}")
        console.print(f"✗ Error: {e}", style="red")
        sys.exit(1)


@app.command("list")
def list_command(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed information"),
) -> None:
    """
    List all topic guides.

    Shows all topic guides in the data directory with optional details.

    Examples:
        synthlab topic-guide list
        synthlab topic-guide list --verbose
    """
    from synth_lab.topic_guides.summary_manager import parse_summary

    try:
        base_dir = get_base_dir()

        if not base_dir.exists():
            console.print("No topic guides found.\n")
            console.print("Create your first topic guide:")
            console.print("  [bold]synthlab topic-guide create --name my-first-guide[/bold]")
            sys.exit(0)

        # Scan for topic guide directories
        guides = [d for d in base_dir.iterdir() if d.is_dir()]

        if not guides:
            console.print("No topic guides found.\n")
            console.print("Create your first topic guide:")
            console.print("  [bold]synthlab topic-guide create --name my-first-guide[/bold]")
            sys.exit(0)

        console.print("[bold]Topic Guides:[/bold]\n")

        for guide_dir in sorted(guides):
            guide_name = guide_dir.name

            if verbose:
                # Show detailed information
                summary_path = guide_dir / "summary.md"
                if summary_path.exists():
                    try:
                        summary = parse_summary(summary_path)
                        file_count = len(summary.file_descriptions)
                        console.print(f"[cyan]{guide_name}[/cyan]")
                        console.print(f"  Path: {guide_dir}")
                        console.print(f"  Files documented: {file_count}")
                        console.print()
                    except Exception:
                        console.print(f"  - [cyan]{guide_name}[/cyan] (error reading summary)")
                else:
                    console.print(f"  - [cyan]{guide_name}[/cyan] (no summary.md)")
            else:
                # Simple list
                console.print(f"  - {guide_name}")

        console.print(f"\nTotal: {len(guides)} topic guide(s)")
        sys.exit(0)

    except Exception as e:
        logger.error(f"List command failed: {e}")
        console.print(f"✗ Error: {e}", style="red")
        sys.exit(1)


@app.command("show")
def show_command(
    name: str = typer.Option(..., "--name", help="Name of the topic guide to display"),
) -> None:
    """
    Show topic guide details.

    Displays detailed information about a specific topic guide including
    context description and all file descriptions.

    Examples:
        synthlab topic-guide show --name amazon-ecommerce
    """
    from synth_lab.topic_guides.summary_manager import parse_summary

    try:
        base_dir = get_base_dir()
        guide_path = base_dir / name

        if not guide_path.exists():
            console.print(
                f"✗ Error: Topic guide '[cyan]{name}[/cyan]' not found", style="red"
            )
            console.print(
                f"  Create it: [bold]synthlab topic-guide create --name {name}[/bold]"
            )
            sys.exit(1)

        summary_path = guide_path / "summary.md"
        if not summary_path.exists():
            console.print(f"✗ Error: summary.md not found in '{name}'", style="red")
            sys.exit(1)

        summary = parse_summary(summary_path)

        # Display header
        console.print(f"[bold]Topic Guide:[/bold] [cyan]{name}[/cyan]")
        console.print(f"Path: {guide_path}\n")

        # Display context description
        if summary.context_description:
            console.print("[bold]Context Description:[/bold]")
            console.print(f"  {summary.context_description}\n")

        # Display file count
        file_count = len(summary.file_descriptions)
        console.print(f"[bold]Files ({file_count}):[/bold]")

        if file_count == 0:
            console.print("  No files documented yet.")
            console.print(
                f"\n  Add files and run: [bold]synthlab topic-guide update --name {name}[/bold]"
            )
        else:
            console.print()
            for desc in summary.file_descriptions:
                console.print(f"[cyan]{desc.filename}[/cyan] (hash: {desc.content_hash[:8]}...):")
                console.print(f"  {desc.description}")
                if desc.is_placeholder:
                    console.print("  [yellow]⚠ Placeholder - needs manual documentation[/yellow]")
                console.print()

        sys.exit(0)

    except Exception as e:
        logger.error(f"Show command failed: {e}")
        console.print(f"✗ Error: {e}", style="red")
        sys.exit(1)


if __name__ == "__main__":
    """Validation: Test CLI functions with real file system operations."""
    import tempfile

    all_validation_failures = []
    total_tests = 0

    # Test 1: create_topic_guide creates correct structure
    total_tests += 1
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        guide_path = create_topic_guide("test-guide", base_dir=base)

        if not guide_path.exists():
            all_validation_failures.append("create_topic_guide: Directory not created")

        summary_path = guide_path / "summary.md"
        if not summary_path.exists():
            all_validation_failures.append("create_topic_guide: summary.md not created")

        content = summary_path.read_text()
        if "# contexto para o guide: test-guide" not in content:
            all_validation_failures.append(
                "create_topic_guide: Incorrect summary.md content"
            )

    # Test 2: create_topic_guide raises FileExistsError for duplicates
    total_tests += 1
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        create_topic_guide("duplicate", base_dir=base)

        try:
            create_topic_guide("duplicate", base_dir=base)
            all_validation_failures.append(
                "create_topic_guide duplicate: Should raise FileExistsError"
            )
        except FileExistsError:
            pass  # Expected

    # Test 3: create_topic_guide raises ValueError for invalid names
    total_tests += 1
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        invalid_names = ["invalid/name", "invalid\\name", "invalid:name"]

        for invalid_name in invalid_names:
            try:
                create_topic_guide(invalid_name, base_dir=base)
                all_validation_failures.append(
                    f"create_topic_guide: Should reject invalid name '{invalid_name}'"
                )
            except ValueError:
                pass  # Expected

    # Test 4: create_topic_guide creates parent directories
    total_tests += 1
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Use a non-existent parent path
        base = Path(tmp_dir) / "nested" / "topic_guides"
        guide_path = create_topic_guide("nested-guide", base_dir=base)

        if not guide_path.exists():
            all_validation_failures.append(
                "create_topic_guide: Should create parent directories"
            )

        if not (guide_path / "summary.md").exists():
            all_validation_failures.append(
                "create_topic_guide: summary.md missing in nested structure"
            )

    # Test 5: validate_topic_guide_name function
    total_tests += 1
    valid_names = ["test", "test-guide", "amazon_ecommerce", "mobile123"]
    invalid_names = ["test/guide", "test\\guide", "test:guide", 'test"guide']

    for name in valid_names:
        if not validate_topic_guide_name(name):
            all_validation_failures.append(
                f"validate_topic_guide_name: '{name}' should be valid"
            )

    for name in invalid_names:
        if validate_topic_guide_name(name):
            all_validation_failures.append(
                f"validate_topic_guide_name: '{name}' should be invalid"
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
        print("CLI functions are validated and formal tests can now be written")
        sys.exit(0)
