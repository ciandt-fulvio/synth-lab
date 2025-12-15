"""
Validation module for Synth Lab.

This module validates synth data against JSON Schema and validates
individual files or batches of synth files.

Functions:
- validate_synth(): Validate synth dict against JSON Schema
- validate_single_file(): Validate a single JSON file
- validate_batch(): Validate all JSON files in a directory

Sample Input:
    synth_dict = {"id": "abc123", "nome": "Maria", ...}
    is_valid, errors = validate_synth(synth_dict)

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
            path = " -> ".join(str(p) for p in error.path) if error.path else "root"
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
                stats["errors"].append({"file": file_path.name, "errors": errors})

        except Exception as e:
            stats["invalid"] += 1
            error_msg = f"Erro ao processar {file_path.name}: {str(e)}"
            print(f"✗ {error_msg}")
            stats["errors"].append({"file": file_path.name, "errors": [error_msg]})

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
            "arquetipo": "Adulto Sudeste Criativo",
            "descricao": "Test description that is longer than 50 characters to meet the minimum requirement.",
            "link_photo": "https://ui-avatars.com/api/?name=Test+Person&size=256",
            "created_at": "2024-01-01T00:00:00Z",
            "version": "1.0.0",
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
                "valores": ["honestidade", "família", "liberdade"],
                "interesses": ["tecnologia", "esportes"],
                "hobbies": ["leitura", "corrida"],
                "estilo_vida": "Equilibrado e moderado",
                "inclinacao_politica": 0,
                "inclinacao_religiosa": "católica",
            },
            "comportamento": {
                "habitos_consumo": {
                    "frequencia_compras": "semanal",
                    "preferencia_canal": "híbrido",
                    "categorias_preferidas": ["eletrônicos", "livros"],
                },
                "uso_tecnologia": {
                    "smartphone": True,
                    "computador": True,
                    "tablet": False,
                    "smartwatch": False,
                },
                "padroes_midia": {
                    "tv_aberta": 10,
                    "streaming": 30,
                    "redes_sociais": 40,
                },
                "fonte_noticias": ["portais online", "redes sociais"],
                "comportamento_compra": {"impulsivo": 50, "pesquisa_antes_comprar": 60},
                "lealdade_marca": 50,
                "engajamento_redes_sociais": {
                    "plataformas": ["Instagram", "WhatsApp"],
                    "frequencia_posts": "ocasional",
                },
            },
            "deficiencias": {
                "visual": {"tipo": "nenhuma"},
                "auditiva": {"tipo": "nenhuma"},
                "motora": {"tipo": "nenhuma", "usa_cadeira_rodas": False},
                "cognitiva": {"tipo": "nenhuma"},
            },
            "capacidades_tecnologicas": {
                "alfabetizacao_digital": 75,
                "dispositivos": {"principal": "smartphone", "qualidade": "novo"},
                "preferencias_acessibilidade": {
                    "zoom_fonte": 100,
                    "alto_contraste": False,
                },
                "velocidade_digitacao": 60,
                "frequencia_internet": "diária",
                "familiaridade_plataformas": {
                    "e_commerce": 70,
                    "banco_digital": 65,
                    "redes_sociais": 80,
                },
            },
            "vieses": {
                "aversao_perda": 50,
                "desconto_hiperbolico": 50,
                "suscetibilidade_chamariz": 50,
                "ancoragem": 50,
                "vies_confirmacao": 50,
                "vies_status_quo": 50,
                "sobrecarga_informacao": 50,
            },
        }

        is_valid, errors = validate_synth(valid_synth)

        if not is_valid:
            all_validation_failures.append(f"Valid synth failed validation: {errors}")
        else:
            print(f"Test 1: validate_synth() accepts valid synth")
    except Exception as e:
        all_validation_failures.append(f"Test 1 (validate valid synth): {str(e)}")

    # Test 2: Validate an invalid synth (missing required field)
    total_tests += 1
    try:
        invalid_synth = {"id": "test02", "nome": "Missing Fields"}

        is_valid, errors = validate_synth(invalid_synth)

        if is_valid:
            all_validation_failures.append("Invalid synth should fail validation")
        elif len(errors) == 0:
            all_validation_failures.append("Invalid synth should have error messages")
        else:
            print(f"Test 2: validate_synth() rejects invalid synth ({len(errors)} errors)")
    except Exception as e:
        all_validation_failures.append(f"Test 2 (validate invalid synth): {str(e)}")

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

            print(f"Test 3: validate_single_file() completed without error")
    except Exception as e:
        all_validation_failures.append(f"Test 3 (validate_single_file): {str(e)}")

    # Test 4: Validate single file - file not found
    total_tests += 1
    try:
        nonexistent_file = Path("/tmp/nonexistent_synth_file_12345.json")

        # Should handle FileNotFoundError gracefully
        validate_single_file(nonexistent_file)

        print(f"Test 4: validate_single_file() handles missing file gracefully")
    except Exception as e:
        all_validation_failures.append(f"Test 4 (validate_single_file missing): {str(e)}")

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
            invalid_synth = {"id": "invalid01", "nome": "Missing required fields"}
            invalid_file = test_dir / "invalid01.json"
            with open(invalid_file, "w", encoding="utf-8") as f:
                json.dump(invalid_synth, f)

            # Validate batch
            stats = validate_batch(test_dir)

            if stats["total"] != 2:
                all_validation_failures.append(f"Expected 2 total files, got {stats['total']}")
            if stats["valid"] != 1:
                all_validation_failures.append(f"Expected 1 valid file, got {stats['valid']}")
            if stats["invalid"] != 1:
                all_validation_failures.append(f"Expected 1 invalid file, got {stats['invalid']}")

            if not any(f.startswith("Test 5") for f in all_validation_failures):
                print(
                    f"Test 5: validate_batch() -> total={stats['total']}, "
                    f"valid={stats['valid']}, invalid={stats['invalid']}"
                )
    except Exception as e:
        all_validation_failures.append(f"Test 5 (validate_batch mixed): {str(e)}")

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
                print(f"Test 6: validate_batch() handles empty directory")
    except Exception as e:
        all_validation_failures.append(f"Test 6 (validate_batch empty): {str(e)}")

    # Test 7: Test error handling for missing schema
    total_tests += 1
    try:
        test_synth = {"id": "test07"}
        nonexistent_schema = Path("/tmp/nonexistent_schema_12345.json")

        is_valid, errors = validate_synth(test_synth, nonexistent_schema)

        if is_valid:
            all_validation_failures.append("Should return False when schema not found")
        if not any("Schema não encontrado" in err for err in errors):
            all_validation_failures.append(
                f"Should have 'Schema não encontrado' error, got: {errors}"
            )
        else:
            print(f"Test 7: validate_synth() handles missing schema gracefully")
    except Exception as e:
        all_validation_failures.append(f"Test 7 (missing schema): {str(e)}")

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
