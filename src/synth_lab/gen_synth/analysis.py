"""
Analysis module for Synth Lab.

This module analyzes demographic distributions of generated synths
and compares them against IBGE reference data.

Functions:
- analyze_regional_distribution(): Analyze regional distribution vs IBGE
- analyze_age_distribution(): Analyze age distribution vs IBGE

Sample Input:
    from synth_lab.gen_synth.analysis import analyze_regional_distribution
    result = analyze_regional_distribution()

Expected Output:
    {
        "total": 100,
        "regions": {
            "Sudeste": {"ibge": 42.0, "actual": 43.5, "count": 43, "error": 1.5},
            "Nordeste": {"ibge": 27.0, "actual": 25.0, "count": 25, "error": 2.0},
            ...
        }
    }

Third-party packages:
- None (uses standard library only)
"""

import json
from pathlib import Path
from typing import Any

from .config import SYNTHS_DIR, load_config_data


def analyze_regional_distribution(synths_dir: Path = SYNTHS_DIR) -> dict[str, Any]:
    """
    Analisa distribuição regional dos Synths gerados vs IBGE.

    Compares the regional distribution of generated synths against
    IBGE reference data to verify statistical accuracy.

    Args:
        synths_dir: Directory containing synth JSON files

    Returns:
        dict: Analysis results with total count and per-region statistics
    """
    config = load_config_data()
    ibge_dist = config["ibge"]["regioes"]

    json_files = list(synths_dir.glob("*.json"))
    if not json_files:
        return {"error": "Nenhum Synth encontrado"}

    region_counts: dict[str, int] = {}
    for file_path in json_files:
        with open(file_path, "r", encoding="utf-8") as f:
            synth = json.load(f)
            regiao = synth["demografia"]["localizacao"]["regiao"]
            region_counts[regiao] = region_counts.get(regiao, 0) + 1

    total = len(json_files)
    analysis: dict[str, Any] = {}
    for regiao, ibge_pct in ibge_dist.items():
        actual_count = region_counts.get(regiao, 0)
        actual_pct = (actual_count / total) * 100
        error = abs(actual_pct - (ibge_pct * 100))
        analysis[regiao] = {
            "ibge": ibge_pct * 100,
            "actual": actual_pct,
            "count": actual_count,
            "error": error,
        }

    return {"total": total, "regions": analysis}


def analyze_age_distribution(synths_dir: Path = SYNTHS_DIR) -> dict[str, Any]:
    """
    Analisa distribuição etária dos Synths gerados vs IBGE.

    Compares the age distribution of generated synths against
    IBGE reference data to verify statistical accuracy.

    Args:
        synths_dir: Directory containing synth JSON files

    Returns:
        dict: Analysis results with total count and per-age-group statistics
    """
    config = load_config_data()
    ibge_dist = config["ibge"]["faixas_etarias"]

    json_files = list(synths_dir.glob("*.json"))
    if not json_files:
        return {"error": "Nenhum Synth encontrado"}

    age_counts: dict[str, int] = {}
    for file_path in json_files:
        with open(file_path, "r", encoding="utf-8") as f:
            synth = json.load(f)
            idade = synth["demografia"]["idade"]
            if idade < 15:
                faixa = "0-14"
            elif idade < 30:
                faixa = "15-29"
            elif idade < 45:
                faixa = "30-44"
            elif idade < 60:
                faixa = "45-59"
            else:
                faixa = "60+"
            age_counts[faixa] = age_counts.get(faixa, 0) + 1

    total = len(json_files)
    analysis: dict[str, Any] = {}
    for faixa, ibge_pct in ibge_dist.items():
        actual_count = age_counts.get(faixa, 0)
        actual_pct = (actual_count / total) * 100
        error = abs(actual_pct - (ibge_pct * 100))
        analysis[faixa] = {
            "ibge": ibge_pct * 100,
            "actual": actual_pct,
            "count": actual_count,
            "error": error,
        }

    return {"total": total, "age_groups": analysis}


if __name__ == "__main__":
    """Validation block - test with real data."""
    import sys
    import tempfile

    from .storage import save_synth

    print("=== Analysis Module Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Test 1: Analyze regional distribution with sample data
    total_tests += 1
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir)

            # Create sample synths from different regions
            regions = ["Sudeste", "Sudeste", "Nordeste", "Sul", "Norte"]
            for i, regiao in enumerate(regions):
                synth = {
                    "id": f"test{i:02d}",
                    "nome": f"Person {i}",
                    "demografia": {
                        "idade": 30,
                        "localizacao": {
                            "pais": "Brasil",
                            "regiao": regiao,
                            "estado": "XX",
                            "cidade": "City",
                        },
                    },
                }
                save_synth(synth, test_dir)

            # Analyze
            result = analyze_regional_distribution(test_dir)

            if "error" in result:
                all_validation_failures.append(f"Analysis returned error: {result['error']}")
            elif "total" not in result:
                all_validation_failures.append("Analysis missing 'total' field")
            elif result["total"] != 5:
                all_validation_failures.append(f"Expected total=5, got {result['total']}")
            elif "regions" not in result:
                all_validation_failures.append("Analysis missing 'regions' field")
            else:
                # Verify Sudeste has 2 synths (40%)
                if result["regions"]["Sudeste"]["count"] != 2:
                    all_validation_failures.append(
                        f"Sudeste should have 2 synths, got {result['regions']['Sudeste']['count']}"
                    )
                if abs(result["regions"]["Sudeste"]["actual"] - 40.0) > 0.1:
                    all_validation_failures.append(
                        f"Sudeste should be 40%, got {result['regions']['Sudeste']['actual']}"
                    )

            if not any(f.startswith("Test 1") for f in all_validation_failures):
                print(
                    f"Test 1: analyze_regional_distribution() -> total={result['total']}, "
                    f"Sudeste={result['regions']['Sudeste']['count']}"
                )
    except Exception as e:
        all_validation_failures.append(f"Test 1 (analyze regional): {str(e)}")

    # Test 2: Analyze age distribution with sample data
    total_tests += 1
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir)

            # Create sample synths from different age groups
            ages = [10, 25, 35, 50, 70]
            expected_groups = ["0-14", "15-29", "30-44", "45-59", "60+"]
            for i, idade in enumerate(ages):
                synth = {
                    "id": f"age{i:02d}",
                    "nome": f"Person {i}",
                    "demografia": {
                        "idade": idade,
                        "localizacao": {
                            "pais": "Brasil",
                            "regiao": "Sudeste",
                            "estado": "SP",
                            "cidade": "São Paulo",
                        },
                    },
                }
                save_synth(synth, test_dir)

            # Analyze
            result = analyze_age_distribution(test_dir)

            if "error" in result:
                all_validation_failures.append(f"Age analysis returned error: {result['error']}")
            elif "total" not in result:
                all_validation_failures.append("Age analysis missing 'total' field")
            elif result["total"] != 5:
                all_validation_failures.append(f"Expected total=5, got {result['total']}")
            elif "age_groups" not in result:
                all_validation_failures.append("Age analysis missing 'age_groups' field")
            else:
                # Verify each age group has 1 synth (20%)
                for faixa in expected_groups:
                    if result["age_groups"][faixa]["count"] != 1:
                        all_validation_failures.append(
                            f"Age group {faixa} should have 1 synth, "
                            f"got {result['age_groups'][faixa]['count']}"
                        )

            if not any(f.startswith("Test 2") for f in all_validation_failures):
                print(
                    f"Test 2: analyze_age_distribution() -> total={result['total']}, "
                    f"groups={len(result['age_groups'])}"
                )
    except Exception as e:
        all_validation_failures.append(f"Test 2 (analyze age): {str(e)}")

    # Test 3: Handle empty directory
    total_tests += 1
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_dir = Path(tmpdir) / "empty"
            empty_dir.mkdir()

            result = analyze_regional_distribution(empty_dir)

            if "error" not in result:
                all_validation_failures.append("Empty directory should return error")
            elif result["error"] != "Nenhum Synth encontrado":
                all_validation_failures.append(
                    f"Wrong error message: {result['error']}"
                )
            else:
                print(f"Test 3: analyze_regional_distribution() handles empty directory")
    except Exception as e:
        all_validation_failures.append(f"Test 3 (empty directory regional): {str(e)}")

    # Test 4: Handle empty directory for age analysis
    total_tests += 1
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_dir = Path(tmpdir) / "empty"
            empty_dir.mkdir()

            result = analyze_age_distribution(empty_dir)

            if "error" not in result:
                all_validation_failures.append("Empty directory should return error")
            elif result["error"] != "Nenhum Synth encontrado":
                all_validation_failures.append(
                    f"Wrong error message: {result['error']}"
                )
            else:
                print(f"Test 4: analyze_age_distribution() handles empty directory")
    except Exception as e:
        all_validation_failures.append(f"Test 4 (empty directory age): {str(e)}")

    # Test 5: Verify error calculation
    total_tests += 1
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir)

            # Create 10 synths all from Sudeste
            for i in range(10):
                synth = {
                    "id": f"sud{i:02d}",
                    "nome": f"Person {i}",
                    "demografia": {
                        "idade": 30,
                        "localizacao": {
                            "pais": "Brasil",
                            "regiao": "Sudeste",
                            "estado": "SP",
                            "cidade": "São Paulo",
                        },
                    },
                }
                save_synth(synth, test_dir)

            result = analyze_regional_distribution(test_dir)

            # Sudeste should be 100% actual
            if result["regions"]["Sudeste"]["actual"] != 100.0:
                all_validation_failures.append(
                    f"Sudeste actual should be 100%, got {result['regions']['Sudeste']['actual']}"
                )

            # IBGE percentage for Sudeste (should be around 42%)
            ibge_pct = result["regions"]["Sudeste"]["ibge"]
            expected_error = abs(100.0 - ibge_pct)
            actual_error = result["regions"]["Sudeste"]["error"]

            if abs(actual_error - expected_error) > 0.1:
                all_validation_failures.append(
                    f"Error calculation wrong: expected {expected_error}, got {actual_error}"
                )

            if not any(f.startswith("Test 5") for f in all_validation_failures):
                print(
                    f"Test 5: Error calculation correct -> "
                    f"ibge={ibge_pct:.1f}%, actual=100%, error={actual_error:.1f}%"
                )
    except Exception as e:
        all_validation_failures.append(f"Test 5 (error calculation): {str(e)}")

    # Test 6: Verify age group boundaries
    total_tests += 1
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir)

            # Test boundary ages
            boundary_tests = [
                (14, "0-14"),
                (15, "15-29"),
                (29, "15-29"),
                (30, "30-44"),
                (44, "30-44"),
                (45, "45-59"),
                (59, "45-59"),
                (60, "60+"),
                (100, "60+"),
            ]

            for i, (idade, expected_group) in enumerate(boundary_tests):
                synth = {
                    "id": f"bound{i:02d}",
                    "nome": f"Person {i}",
                    "demografia": {
                        "idade": idade,
                        "localizacao": {
                            "pais": "Brasil",
                            "regiao": "Sudeste",
                            "estado": "SP",
                            "cidade": "São Paulo",
                        },
                    },
                }
                save_synth(synth, test_dir)

            result = analyze_age_distribution(test_dir)

            # Verify counts for each expected group
            expected_counts = {"0-14": 1, "15-29": 2, "30-44": 2, "45-59": 2, "60+": 2}
            for group, expected_count in expected_counts.items():
                actual_count = result["age_groups"][group]["count"]
                if actual_count != expected_count:
                    all_validation_failures.append(
                        f"Age group {group} should have {expected_count} synths, got {actual_count}"
                    )

            if not any(f.startswith("Test 6") for f in all_validation_failures):
                print(f"Test 6: Age group boundaries correct")
    except Exception as e:
        all_validation_failures.append(f"Test 6 (age boundaries): {str(e)}")

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
