"""
Storage module for Synth Lab.

This module handles saving synth data to JSON files.

Functions:
- save_synth(): Save synth to JSON file

Sample Input:
    synth_dict = {"id": "abc123", "nome": "Maria Silva", ...}
    save_synth(synth_dict)

Expected Output:
    File saved at: data/synths/abc123.json
    Print confirmation message

Third-party packages:
- None (uses standard library only)
"""

import json
from pathlib import Path
from typing import Any

from .config import SYNTHS_DIR


def save_synth(synth_dict: dict[str, Any], output_dir: Path = SYNTHS_DIR) -> None:
    """
    Salva Synth como {id}.json no diretório especificado.

    Creates the output directory if it doesn't exist, then saves the synth
    dictionary as a formatted JSON file.

    Args:
        synth_dict: Dictionary containing complete synth data (must have "id" key)
        output_dir: Directory path where synth JSON will be saved (default: data/synths/)

    Raises:
        KeyError: If synth_dict doesn't contain "id" key
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{synth_dict['id']}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(synth_dict, f, ensure_ascii=False, indent=2)

    print(f"Synth salvo: {output_path}")


if __name__ == "__main__":
    """Validation block - test with real data."""
    import sys
    import tempfile

    print("=== Storage Module Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Test 1: Save synth to default directory
    total_tests += 1
    try:
        # Create a test synth
        test_synth = {
            "id": "test01",
            "nome": "Test Person",
            "idade": 30,
            "ocupacao": "Tester",
        }

        # Save it
        save_synth(test_synth)

        # Verify file was created
        expected_path = SYNTHS_DIR / "test01.json"
        if not expected_path.exists():
            all_validation_failures.append(f"File not created: {expected_path}")
        else:
            # Verify content
            with open(expected_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if loaded["id"] != "test01":
                all_validation_failures.append(
                    f"Saved synth has wrong id: {loaded['id']}"
                )
            if loaded["nome"] != "Test Person":
                all_validation_failures.append(
                    f"Saved synth has wrong nome: {loaded['nome']}"
                )

            # Clean up
            expected_path.unlink()

        if not any(f.startswith("Test 1") for f in all_validation_failures):
            print(f"Test 1: save_synth() saved to default directory successfully")
    except Exception as e:
        all_validation_failures.append(f"Test 1 (save to default dir): {str(e)}")

    # Test 2: Save synth to custom directory
    total_tests += 1
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_dir = Path(tmpdir) / "custom_synths"

            test_synth = {
                "id": "test02",
                "nome": "Custom Test",
                "idade": 25,
            }

            # Save to custom directory
            save_synth(test_synth, custom_dir)

            # Verify file was created
            expected_path = custom_dir / "test02.json"
            if not expected_path.exists():
                all_validation_failures.append(
                    f"File not created in custom dir: {expected_path}"
                )
            else:
                # Verify content
                with open(expected_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if loaded["id"] != "test02":
                    all_validation_failures.append(
                        f"Custom save has wrong id: {loaded['id']}"
                    )

        if not any(f.startswith("Test 2") for f in all_validation_failures):
            print(f"Test 2: save_synth() saved to custom directory successfully")
    except Exception as e:
        all_validation_failures.append(f"Test 2 (save to custom dir): {str(e)}")

    # Test 3: Verify JSON formatting (ensure_ascii=False, indent=2)
    total_tests += 1
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir)

            # Create synth with Portuguese characters
            test_synth = {
                "id": "test03",
                "nome": "José da Silva",
                "descrição": "Pessoa com acentuação",
            }

            save_synth(test_synth, test_dir)

            # Read raw file content
            file_path = test_dir / "test03.json"
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Verify UTF-8 characters are preserved (not escaped)
            if "Jos\\u00e9" in content:
                all_validation_failures.append(
                    "JSON should use ensure_ascii=False (found escaped UTF-8)"
                )

            # Verify indentation
            if '"id"' in content and '\n  "id"' not in content:
                all_validation_failures.append(
                    "JSON should be indented with 2 spaces"
                )

        if not any(f.startswith("Test 3") for f in all_validation_failures):
            print(f"Test 3: JSON formatting correct (UTF-8, indented)")
    except Exception as e:
        all_validation_failures.append(f"Test 3 (JSON formatting): {str(e)}")

    # Test 4: Verify directory creation
    total_tests += 1
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a path with nested directories that don't exist
            nested_dir = Path(tmpdir) / "level1" / "level2" / "synths"

            test_synth = {"id": "test04", "nome": "Nested Test"}

            # Should create all parent directories
            save_synth(test_synth, nested_dir)

            # Verify file exists
            expected_path = nested_dir / "test04.json"
            if not expected_path.exists():
                all_validation_failures.append(
                    f"Failed to create nested directories: {expected_path}"
                )

        if not any(f.startswith("Test 4") for f in all_validation_failures):
            print(f"Test 4: Directory creation works (mkdir parents=True)")
    except Exception as e:
        all_validation_failures.append(f"Test 4 (directory creation): {str(e)}")

    # Test 5: Test with complex synth data
    total_tests += 1
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir)

            # Create a more complex synth
            complex_synth = {
                "id": "test05",
                "nome": "Complex Person",
                "demografia": {
                    "idade": 35,
                    "localizacao": {
                        "cidade": "São Paulo",
                        "estado": "SP",
                    },
                },
                "psicografia": {
                    "valores": ["honestidade", "família"],
                    "hobbies": ["leitura", "corrida"],
                },
            }

            save_synth(complex_synth, test_dir)

            # Load and verify structure
            file_path = test_dir / "test05.json"
            with open(file_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)

            if "demografia" not in loaded:
                all_validation_failures.append("Complex synth missing demografia")
            elif "localizacao" not in loaded["demografia"]:
                all_validation_failures.append("Complex synth missing nested localizacao")

            if "psicografia" not in loaded:
                all_validation_failures.append("Complex synth missing psicografia")
            elif loaded["psicografia"]["valores"] != ["honestidade", "família"]:
                all_validation_failures.append(
                    f"Complex synth valores mismatch: {loaded['psicografia']['valores']}"
                )

        if not any(f.startswith("Test 5") for f in all_validation_failures):
            print(f"Test 5: Complex nested synth saved correctly")
    except Exception as e:
        all_validation_failures.append(f"Test 5 (complex synth): {str(e)}")

    # Test 6: Verify error handling for missing id
    total_tests += 1
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir)

            # Create synth without id
            invalid_synth = {"nome": "No ID Person"}

            # Should raise KeyError
            try:
                save_synth(invalid_synth, test_dir)
                all_validation_failures.append(
                    "Should raise KeyError for synth without 'id'"
                )
            except KeyError:
                # This is expected
                print(f"Test 6: Correctly raises KeyError for missing 'id'")
    except KeyError:
        # Expected error, test passed
        print(f"Test 6: Correctly raises KeyError for missing 'id'")
    except Exception as e:
        all_validation_failures.append(f"Test 6 (missing id error): {str(e)}")

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
