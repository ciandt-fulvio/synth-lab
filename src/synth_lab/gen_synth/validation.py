"""
Validation module for SynthLab.

This module validates synth data against JSON Schema and validates
individual files or batches of synth files. Also includes personality-bias
coherence validation (User Story 3).

Functions:
- validate_synth(): Validate synth dict against JSON Schema
- validate_coherence(): Validate personality-bias coherence
- validate_synth_full(): Validate both schema and coherence
- validate_single_file(): Validate a single JSON file
- validate_batch(): Validate all JSON files in a directory

Sample Input:
    synth_dict = {"id": "abc123", "nome": "Maria", ...}
    is_valid, errors = validate_synth(synth_dict)

    # With coherence validation:
    is_valid, errors = validate_synth_full(synth_dict, strict=False)

Expected Output:
    (True, []) if valid
    (False, ["error message 1", "error message 2"]) if invalid

Third-party packages:
- jsonschema: https://python-jsonschema.readthedocs.io/
"""

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .config import SCHEMA_PATH, SYNTHS_DIR


# Custom exception for coherence validation errors (User Story 3)
class CoherenceError(Exception):
    """
    Exception raised when synth fails personality-bias coherence validation.

    This exception is raised when strict=True and the synth has biases
    that are psychologically inconsistent with the personality traits.
    """
    pass


def validate_coherence(
    synth_dict: dict[str, Any], strict: bool = False
) -> tuple[bool, list[str]] | bool:
    """
    Valida coerência entre personalidade Big Five e vieses cognitivos.

    Verifica se os valores dos vieses estão coerentes com os traços de
    personalidade usando as regras de coerência definidas no módulo de vieses.

    Args:
        synth_dict: Dicionário do Synth a validar
        strict: Se True, lança CoherenceError em caso de violação.
                Se False, retorna (False, errors) em caso de violação.

    Returns:
        bool | tuple[bool, list[str]]:
            - Se strict=True e válido: retorna True
            - Se strict=False: retorna (is_valid, error_messages)

    Raises:
        CoherenceError: Se strict=True e há violações de coerência

    Example:
        >>> synth = {"psicografia": {...}, "vieses": {...}}
        >>> is_valid, errors = validate_coherence(synth, strict=False)
        >>> if not is_valid:
        ...     print(f"Violations: {errors}")
    """
    from .biases import get_coherence_expectations

    errors = []

    # Extract personality and biases
    try:
        personality = synth_dict["psicografia"]["personalidade_big_five"]
        biases = synth_dict["vieses"]
    except KeyError as e:
        error_msg = f"Missing required field for coherence validation: {e}"
        if strict:
            raise CoherenceError(error_msg)
        return (False, [error_msg])

    # Get expected ranges for this personality
    expectations = get_coherence_expectations(personality)

    # Check each bias against expected range
    for bias_name, bias_value in biases.items():
        if bias_name not in expectations:
            continue  # Skip biases not affected by coherence rules

        expected = expectations[bias_name]
        expected_min = expected["min"]
        expected_max = expected["max"]

        # Check if bias value is within expected range
        if not (expected_min <= bias_value <= expected_max):
            # Find which personality traits are affecting this bias
            affecting_traits = _get_affecting_traits(personality, bias_name)

            error_msg = (
                f"Inconsistent personality-bias relationship: "
                f"bias '{bias_name}' has value {bias_value}, but personality traits "
                f"{affecting_traits} expect range [{expected_min}-{expected_max}]"
            )
            errors.append(error_msg)

    # Return results based on strict mode
    if errors:
        if strict:
            raise CoherenceError(
                f"Coherence validation failed with {len(errors)} violation(s): " +
                "; ".join(errors[:3])  # Show first 3 errors
            )
        return (False, errors)

    if strict:
        return True
    return (True, [])


def _get_affecting_traits(personality: dict[str, int], bias_name: str) -> str:
    """
    Identifica quais traços de personalidade afetam um determinado viés.

    Helper function para mensagens de erro mais descritivas.

    Args:
        personality: Dictionary com traços Big Five
        bias_name: Nome do viés

    Returns:
        str: Descrição dos traços que afetam esse viés
    """
    from .biases import COHERENCE_RULES

    affecting = []
    for trait_name, trait_range, rule_bias_name, _ in COHERENCE_RULES:
        if rule_bias_name != bias_name:
            continue

        trait_value = personality.get(trait_name, 50)
        trait_min, trait_max = trait_range

        if trait_min <= trait_value <= trait_max:
            if trait_max >= 70:
                level = "high"
            elif trait_min <= 30:
                level = "low"
            else:
                level = "moderate"

            affecting.append(f"{level} {trait_name} ({trait_value})")

    return ", ".join(affecting) if affecting else "personality"


def validate_synth_full(
    synth_dict: dict[str, Any],
    strict: bool = False,
    schema_path: Path = SCHEMA_PATH
) -> tuple[bool, list[str]]:
    """
    Valida Synth contra JSON Schema E regras de coerência personalidade-viés.

    Esta função combina validação de schema (estrutural) com validação de
    coerência (semântica) para garantir que synths sejam válidos E psicologicamente
    realistas.

    Args:
        synth_dict: Dicionário do Synth a validar
        strict: Se True, lança exceções em caso de violação de coerência
        schema_path: Caminho para o arquivo de schema JSON

    Returns:
        tuple[bool, list[str]]: (is_valid, error_messages)
            - Retorna (True, []) se passar ambas validações
            - Retorna (False, errors) se falhar em qualquer validação

    Example:
        >>> synth = {"id": "123", "nome": "Maria", ...}
        >>> is_valid, errors = validate_synth_full(synth, strict=False)
        >>> if not is_valid:
        ...     for error in errors:
        ...         print(f"  - {error}")
    """
    all_errors = []

    # Step 1: Validate against JSON Schema
    schema_valid, schema_errors = validate_synth(synth_dict, schema_path)
    if not schema_valid:
        all_errors.extend([f"[Schema] {err}" for err in schema_errors])

    # Step 2: Validate coherence (only if schema is valid)
    # Note: We validate coherence even if schema fails, to provide complete feedback
    try:
        coherence_result = validate_coherence(synth_dict, strict=False)

        # Handle both return formats (bool or tuple)
        if isinstance(coherence_result, tuple):
            coherence_valid, coherence_errors = coherence_result
        else:
            coherence_valid = coherence_result
            coherence_errors = []

        if not coherence_valid:
            all_errors.extend(
                [f"[Coherence] {err}" for err in coherence_errors])
    except CoherenceError as e:
        # This shouldn't happen since strict=False, but handle it anyway
        all_errors.append(f"[Coherence] {str(e)}")

    # Step 3: Check for removed fields (backward compatibility - T049)
    compat_errors = _check_removed_fields(synth_dict)
    if compat_errors:
        all_errors.extend([f"[Compatibility] {err}" for err in compat_errors])

    return (len(all_errors) == 0, all_errors)


def _check_removed_fields(synth_dict: dict[str, Any]) -> list[str]:
    """
    Verifica se synth contém campos removidos no schema v2.0.0.

    Esta função detecta campos que foram removidos na migração de v1.0.0 para
    v2.0.0 e retorna avisos (não erros) para ajudar na migração.

    Args:
        synth_dict: Dicionário do Synth a verificar

    Returns:
        list[str]: Lista de avisos sobre campos removidos (pode estar vazia)

    Example:
        >>> v1_synth = {"version": "1.0.0", "psicografia": {"valores": [...]}}
        >>> warnings = _check_removed_fields(v1_synth)
        >>> # warnings: ["Field 'psicografia.valores' was removed in v2.0.0"]
    """
    warnings = []

    # Only check if this is an old version synth
    version = synth_dict.get("version", "1.0.0")
    if version != "1.0.0":
        return warnings  # No need to check v2.0.0 synths

    # Check for removed fields in psicografia
    psicografia = synth_dict.get("psicografia", {})
    removed_psico_fields = ["valores", "hobbies", "estilo_vida"]
    for field in removed_psico_fields:
        if field in psicografia:
            warnings.append(
                f"Field 'psicografia.{field}' was removed in v2.0.0. "
                f"Consider migrating to new schema."
            )

    # Check for removed fields in comportamento
    comportamento = synth_dict.get("comportamento", {})
    removed_comp_fields = ["uso_tecnologia", "comportamento_compra"]
    for field in removed_comp_fields:
        if field in comportamento:
            warnings.append(
                f"Field 'comportamento.{field}' was removed in v2.0.0. "
                f"Consider migrating to new schema."
            )

    return warnings


def validate_synth(
    synth_dict: dict[str, Any], schema_path: Path = SCHEMA_PATH
) -> tuple[bool, list[str]]:
    """
    Valida Synth contra JSON Schema e retorna status e lista de erros.

    Args:
        synth_dict: Dicionário do Synth a validar
        schema_path: Caminho para o arquivo de schema JSON

    Returns:
        tuple[bool, list[str]]: (is_valid, error_messages)
    """
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        validator = Draft202012Validator(schema)
        errors = []

        for error in validator.iter_errors(synth_dict):
            path = " -> ".join(str(p)
                               for p in error.path) if error.path else "root"
            errors.append(f"{path}: {error.message}")

        return (len(errors) == 0, errors)

    except FileNotFoundError:
        return (False, [f"Schema não encontrado: {schema_path}"])
    except json.JSONDecodeError as e:
        return (False, [f"Erro ao parsear schema: {str(e)}"])


def validate_single_file(file_path: Path, schema_path: Path = SCHEMA_PATH) -> None:
    """
    Valida um único arquivo JSON de Synth contra o schema.

    Prints validation results to stdout.

    Args:
        file_path: Caminho para o arquivo JSON do Synth
        schema_path: Caminho para o schema JSON
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            synth_data = json.load(f)

        is_valid, errors = validate_synth(synth_data, schema_path)

        if is_valid:
            print(f"✓ {file_path.name}: VÁLIDO")
        else:
            print(f"✗ {file_path.name}: FALHOU")
            for error in errors:
                print(f"  - {error}")

    except FileNotFoundError:
        print(f"✗ {file_path.name}: Arquivo não encontrado")
    except json.JSONDecodeError as e:
        print(f"✗ {file_path.name}: JSON inválido - {str(e)}")


def validate_batch(
    synths_dir: Path = SYNTHS_DIR, schema_path: Path = SCHEMA_PATH
) -> dict[str, Any]:
    """
    Valida todos os arquivos JSON em um diretório contra o schema.

    Args:
        synths_dir: Directory containing synth JSON files
        schema_path: Path to JSON schema file

    Returns:
        dict: Estatísticas de validação (total, valid, invalid, errors)
    """
    json_files = list(synths_dir.glob("*.json"))

    if not json_files:
        print(f"Nenhum arquivo JSON encontrado em {synths_dir}")
        return {"total": 0, "valid": 0, "invalid": 0, "errors": []}

    stats = {"total": len(json_files), "valid": 0, "invalid": 0, "errors": []}

    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                synth_data = json.load(f)

            is_valid, errors = validate_synth(synth_data, schema_path)

            if is_valid:
                stats["valid"] += 1
                print(f"✓ {file_path.name}")
            else:
                stats["invalid"] += 1
                print(f"✗ {file_path.name}")
                for error in errors:
                    print(f"  - {error}")
                stats["errors"].append(
                    {"file": file_path.name, "errors": errors})

        except Exception as e:
            stats["invalid"] += 1
            error_msg = f"Erro ao processar {file_path.name}: {str(e)}"
            print(f"✗ {error_msg}")
            stats["errors"].append(
                {"file": file_path.name, "errors": [error_msg]})

    return stats


if __name__ == "__main__":
    """Validation block - test with real data."""
    import sys
    import tempfile

    print("=== Validation Module Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Test 1: Validate a valid synth dict (create minimal valid synth)
    total_tests += 1
    try:
        # Create a minimal valid synth based on the schema
        valid_synth = {
            "id": "test01",
            "nome": "Test Person",
            "descricao": "Test description that is longer than 50 characters to meet the minimum requirement.",
            "link_photo": "https://ui-avatars.com/api/?name=Test+Person&size=256",
            "created_at": "2024-01-01T00:00:00Z",
            "version": "2.0.0",
            "demografia": {
                "idade": 30,
                "genero_biologico": "feminino",
                "identidade_genero": "mulher cis",
                "raca_etnia": "branca",
                "localizacao": {
                    "pais": "Brasil",
                    "regiao": "Sudeste",
                    "estado": "SP",
                    "cidade": "São Paulo",
                },
                "escolaridade": "Superior completo",
                "renda_mensal": 5000.0,
                "ocupacao": "Analista",
                "estado_civil": "solteiro",
                "composicao_familiar": {"tipo": "unipessoal", "numero_pessoas": 1},
            },
            "psicografia": {
                "personalidade_big_five": {
                    "abertura": 50,
                    "conscienciosidade": 50,
                    "extroversao": 50,
                    "amabilidade": 50,
                    "neuroticismo": 50,
                },
                "interesses": ["tecnologia", "esportes"],
            },
            "deficiencias": {
                "visual": {"tipo": "nenhuma"},
                "auditiva": {"tipo": "nenhuma"},
                "motora": {"tipo": "nenhuma", "usa_cadeira_rodas": False},
                "cognitiva": {"tipo": "nenhuma"},
            },
            "capacidades_tecnologicas": {
                "alfabetizacao_digital": 75,
            },
        }

        is_valid, errors = validate_synth(valid_synth)

        if not is_valid:
            all_validation_failures.append(
                f"Valid synth failed validation: {errors}")
        else:
            print("Test 1: validate_synth() accepts valid synth")
    except Exception as e:
        all_validation_failures.append(
            f"Test 1 (validate valid synth): {str(e)}")

    # Test 2: Validate an invalid synth (missing required field)
    total_tests += 1
    try:
        invalid_synth = {"id": "test02", "nome": "Missing Fields"}

        is_valid, errors = validate_synth(invalid_synth)

        if is_valid:
            all_validation_failures.append(
                "Invalid synth should fail validation")
        elif len(errors) == 0:
            all_validation_failures.append(
                "Invalid synth should have error messages")
        else:
            print(
                f"Test 2: validate_synth() rejects invalid synth ({len(errors)} errors)")
    except Exception as e:
        all_validation_failures.append(
            f"Test 2 (validate invalid synth): {str(e)}")

    # Test 3: Validate single file
    total_tests += 1
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir)

            # Use the valid synth from Test 1
            valid_synth["id"] = "test03"
            test_file = test_dir / "test03.json"

            with open(test_file, "w", encoding="utf-8") as f:
                json.dump(valid_synth, f)

            # Validate should print success message
            # We can't easily capture print output, so just verify it doesn't crash
            validate_single_file(test_file)

            print("Test 3: validate_single_file() completed without error")
    except Exception as e:
        all_validation_failures.append(
            f"Test 3 (validate_single_file): {str(e)}")

    # Test 4: Validate single file - file not found
    total_tests += 1
    try:
        nonexistent_file = Path("/tmp/nonexistent_synth_file_12345.json")

        # Should handle FileNotFoundError gracefully
        validate_single_file(nonexistent_file)

        print("Test 4: validate_single_file() handles missing file gracefully")
    except Exception as e:
        all_validation_failures.append(
            f"Test 4 (validate_single_file missing): {str(e)}")

    # Test 5: Validate batch with mixed valid/invalid files
    total_tests += 1
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir)

            # Create valid file
            valid_synth["id"] = "valid01"
            valid_file = test_dir / "valid01.json"
            with open(valid_file, "w", encoding="utf-8") as f:
                json.dump(valid_synth, f)

            # Create invalid file
            invalid_synth = {"id": "invalid01",
                             "nome": "Missing required fields"}
            invalid_file = test_dir / "invalid01.json"
            with open(invalid_file, "w", encoding="utf-8") as f:
                json.dump(invalid_synth, f)

            # Validate batch
            stats = validate_batch(test_dir)

            if stats["total"] != 2:
                all_validation_failures.append(
                    f"Expected 2 total files, got {stats['total']}")
            if stats["valid"] != 1:
                all_validation_failures.append(
                    f"Expected 1 valid file, got {stats['valid']}")
            if stats["invalid"] != 1:
                all_validation_failures.append(
                    f"Expected 1 invalid file, got {stats['invalid']}")

            if not any(f.startswith("Test 5") for f in all_validation_failures):
                print(
                    f"Test 5: validate_batch() -> total={stats['total']}, "
                    f"valid={stats['valid']}, invalid={stats['invalid']}"
                )
    except Exception as e:
        all_validation_failures.append(
            f"Test 5 (validate_batch mixed): {str(e)}")

    # Test 6: Validate batch with empty directory
    total_tests += 1
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_dir = Path(tmpdir) / "empty"
            empty_dir.mkdir()

            stats = validate_batch(empty_dir)

            if stats["total"] != 0:
                all_validation_failures.append(
                    f"Empty directory should have 0 total files, got {stats['total']}"
                )
            if stats["valid"] != 0:
                all_validation_failures.append(
                    f"Empty directory should have 0 valid files, got {stats['valid']}"
                )

            if not any(f.startswith("Test 6") for f in all_validation_failures):
                print("Test 6: validate_batch() handles empty directory")
    except Exception as e:
        all_validation_failures.append(
            f"Test 6 (validate_batch empty): {str(e)}")

    # Test 7: Test error handling for missing schema
    total_tests += 1
    try:
        test_synth = {"id": "test07"}
        nonexistent_schema = Path("/tmp/nonexistent_schema_12345.json")

        is_valid, errors = validate_synth(test_synth, nonexistent_schema)

        if is_valid:
            all_validation_failures.append(
                "Should return False when schema not found")
        if not any("Schema não encontrado" in err for err in errors):
            all_validation_failures.append(
                f"Should have 'Schema não encontrado' error, got: {errors}"
            )
        else:
            print("Test 7: validate_synth() handles missing schema gracefully")
    except Exception as e:
        all_validation_failures.append(f"Test 7 (missing schema): {str(e)}")

    # Final validation result
    print(f"\n{'='*60}")
    if all_validation_failures:
        print(
            f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(
            f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Function is validated and formal tests can now be written")
        sys.exit(0)
