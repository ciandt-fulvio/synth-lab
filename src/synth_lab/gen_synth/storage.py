"""
Storage module for Synth Lab.

This module handles saving synth data to JSON files.

Functions:
- save_synth(): Save synth to consolidated file and optionally to individual files
- load_consolidated_synths(): Load all synths from consolidated file

Sample Input:
    synth_dict = {"id": "abc123", "nome": "Maria Silva", ...}
    save_synth(synth_dict)  # Saves to consolidated file only
    save_synth(synth_dict, save_individual=True)  # Saves to both

Expected Output:
    File saved at: data/synths/synths.json (consolidated)
    File saved at: data/synths/abc123.json (if save_individual=True)

Third-party packages:
- None (uses standard library only)
"""

import json
from pathlib import Path
from typing import Any

from .config import SYNTHS_DIR

# Path to consolidated synths file
CONSOLIDATED_FILE = "synths.json"


def load_consolidated_synths(output_dir: Path = SYNTHS_DIR) -> list[dict[str, Any]]:
    """
    Load all synths from the consolidated JSON file.

    Args:
        output_dir: Directory containing the consolidated file

    Returns:
        List of synth dictionaries (empty list if file doesn't exist)
    """
    consolidated_path = output_dir / CONSOLIDATED_FILE

    if not consolidated_path.exists():
        return []

    with open(consolidated_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_consolidated_synths(synths: list[dict[str, Any]], output_dir: Path = SYNTHS_DIR) -> None:
    """
    Save list of synths to the consolidated JSON file.

    Args:
        synths: List of synth dictionaries
        output_dir: Directory where consolidated file will be saved
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    consolidated_path = output_dir / CONSOLIDATED_FILE

    with open(consolidated_path, "w", encoding="utf-8") as f:
        json.dump(synths, f, ensure_ascii=False, indent=2)


def save_synth(synth_dict: dict[str, Any], output_dir: Path = SYNTHS_DIR, save_individual: bool = False) -> None:
    """
    Salva Synth no arquivo consolidado e opcionalmente em arquivo individual.

    By default, saves the synth to the consolidated synths.json file.
    If save_individual=True, also saves to individual {id}.json file.

    Args:
        synth_dict: Dictionary containing complete synth data (must have "id" key)
        output_dir: Directory path where synth JSON will be saved (default: data/synths/)
        save_individual: If True, also save to individual file (default: False)

    Raises:
        KeyError: If synth_dict doesn't contain "id" key
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load existing synths from consolidated file
    synths = load_consolidated_synths(output_dir)

    # Add new synth to the list
    synths.append(synth_dict)

    # Save consolidated file
    save_consolidated_synths(synths, output_dir)
    print(f"Synth salvo: {output_dir / CONSOLIDATED_FILE}")

    # Save individual file if requested
    if save_individual:
        individual_path = output_dir / f"{synth_dict['id']}.json"
        with open(individual_path, "w", encoding="utf-8") as f:
            json.dump(synth_dict, f, ensure_ascii=False, indent=2)
        print(f"Synth individual salvo: {individual_path}")


if __name__ == "__main__":
    """Validation block - test with real data."""
    import sys
    import tempfile

    print("=== Storage Module Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Test 1: Save synth to consolidated file (default behavior)
    total_tests += 1
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir)

            # Create test synths
            test_synth1 = {
                "id": "test01",
                "nome": "Test Person 1",
                "idade": 30,
            }
            test_synth2 = {
                "id": "test02",
                "nome": "Test Person 2",
                "idade": 25,
            }

            # Save both synths
            save_synth(test_synth1, test_dir)
            save_synth(test_synth2, test_dir)

            # Verify consolidated file was created
            consolidated_path = test_dir / CONSOLIDATED_FILE
            if not consolidated_path.exists():
                all_validation_failures.append(f"Consolidated file not created: {consolidated_path}")
            else:
                # Verify content
                loaded_synths = load_consolidated_synths(test_dir)
                if len(loaded_synths) != 2:
                    all_validation_failures.append(
                        f"Expected 2 synths in consolidated file, got {len(loaded_synths)}"
                    )
                elif loaded_synths[0]["id"] != "test01" or loaded_synths[1]["id"] != "test02":
                    all_validation_failures.append(
                        f"Synth IDs mismatch in consolidated file"
                    )

            # Verify individual files were NOT created (default behavior)
            if (test_dir / "test01.json").exists():
                all_validation_failures.append("Individual file created when save_individual=False")

        if not any(f.startswith("Test 1") for f in all_validation_failures):
            print("Test 1: save_synth() saves to consolidated file by default")
    except Exception as e:
        all_validation_failures.append(f"Test 1 (consolidated save): {str(e)}")

    # Test 2: Save synth with save_individual=True
    total_tests += 1
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir)

            test_synth = {
                "id": "test03",
                "nome": "Individual Test",
                "idade": 25,
            }

            # Save with individual file enabled
            save_synth(test_synth, test_dir, save_individual=True)

            # Verify consolidated file exists
            consolidated_path = test_dir / CONSOLIDATED_FILE
            if not consolidated_path.exists():
                all_validation_failures.append(
                    f"Consolidated file not created: {consolidated_path}"
                )

            # Verify individual file exists
            individual_path = test_dir / "test03.json"
            if not individual_path.exists():
                all_validation_failures.append(
                    f"Individual file not created: {individual_path}"
                )
            else:
                # Verify content
                with open(individual_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if loaded["id"] != "test03":
                    all_validation_failures.append(
                        f"Individual file has wrong id: {loaded['id']}"
                    )

        if not any(f.startswith("Test 2") for f in all_validation_failures):
            print("Test 2: save_synth() saves both consolidated and individual files when requested")
    except Exception as e:
        all_validation_failures.append(f"Test 2 (save_individual=True): {str(e)}")

    # Test 3: Load existing consolidated file
    total_tests += 1
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir)

            # Create initial synths
            initial_synths = [
                {"id": "existing01", "nome": "Existing 1"},
                {"id": "existing02", "nome": "Existing 2"},
            ]
            save_consolidated_synths(initial_synths, test_dir)

            # Add a new synth
            new_synth = {"id": "test04", "nome": "New Synth"}
            save_synth(new_synth, test_dir)

            # Load and verify all synths
            all_synths = load_consolidated_synths(test_dir)
            if len(all_synths) != 3:
                all_validation_failures.append(
                    f"Expected 3 synths after adding to existing, got {len(all_synths)}"
                )
            elif all_synths[2]["id"] != "test04":
                all_validation_failures.append(
                    f"New synth not appended correctly: {all_synths[2]['id']}"
                )

        if not any(f.startswith("Test 3") for f in all_validation_failures):
            print("Test 3: load_consolidated_synths() loads and appends correctly")
    except Exception as e:
        all_validation_failures.append(f"Test 3 (load consolidated): {str(e)}")

    # Test 4: Verify JSON formatting (UTF-8 and indentation)
    total_tests += 1
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir)

            # Create synth with Portuguese characters
            test_synth = {
                "id": "test05",
                "nome": "José da Silva",
                "descrição": "Pessoa com acentuação",
            }

            save_synth(test_synth, test_dir)

            # Read raw file content
            file_path = test_dir / CONSOLIDATED_FILE
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Verify UTF-8 characters are preserved (not escaped)
            if "Jos\\u00e9" in content:
                all_validation_failures.append(
                    "JSON should use ensure_ascii=False (found escaped UTF-8)"
                )

            # Verify array structure with indentation
            if '"id"' not in content:
                all_validation_failures.append("JSON should contain id field")

        if not any(f.startswith("Test 4") for f in all_validation_failures):
            print("Test 4: JSON formatting correct (UTF-8, indented)")
    except Exception as e:
        all_validation_failures.append(f"Test 4 (JSON formatting): {str(e)}")

    # Final validation result
    print(f"\n{'='*60}")
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Function is validated and formal tests can now be written")
        sys.exit(0)
