"""
Configuration module for SynthLab.

This module defines paths and loads configuration data from JSON files.

Paths:
- DATA_DIR: Base data directory (read-only config/schemas)
- OUTPUT_DIR: Base output directory (generated files)
- CONFIG_DIR: Configuration files directory
- SCHEMAS_DIR: JSON schema files directory
- SYNTHS_DIR: Generated synths output directory (in OUTPUT_DIR)
- SCHEMA_PATH: Main synth schema file path

Functions:
- load_config_data(): Load all configuration files

Sample usage:
    from synth_lab.gen_synth import config
    data = config.load_config_data()
    print(data.keys())  # ['ibge', 'occupations', 'interests_hobbies']
"""

import json
from pathlib import Path
from typing import Any

# Configuration paths
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
OUTPUT_DIR = Path(__file__).parent.parent.parent.parent / "output"
CONFIG_DIR = DATA_DIR / "config"
SCHEMAS_DIR = DATA_DIR / "schemas"
SYNTHS_DIR = OUTPUT_DIR / "synths"
SCHEMA_PATH = SCHEMAS_DIR / "synth-schema-v1.json"


def load_config_data() -> dict[str, Any]:
    """
    Carrega todos os arquivos de configuração JSON do diretório data/config/.

    Se existir um arquivo custom_distribution.json, suas chaves são mescladas
    com as distribuições IBGE, tendo prioridade sobre os valores originais.

    Returns:
        dict[str, Any]: Dicionário com todas as configurações carregadas
            - ibge: Distribuições demográficas (IBGE + custom overrides)
            - occupations: Lista estruturada de ocupações
            - interests_hobbies: Listas de interesses, hobbies e valores
    """
    config_files = {
        "ibge": CONFIG_DIR / "ibge_distributions.json",
        "occupations": CONFIG_DIR / "occupations_structured.json",
        "interests_hobbies": CONFIG_DIR / "interests_hobbies.json",
    }

    config = {}
    for key, path in config_files.items():
        with open(path, "r", encoding="utf-8") as f:
            config[key] = json.load(f)

    # Merge custom_distribution.json if it exists (takes priority over IBGE)
    custom_distribution_path = CONFIG_DIR / "custom_distribution.json"
    if custom_distribution_path.exists():
        with open(custom_distribution_path, "r", encoding="utf-8") as f:
            custom_data = json.load(f)
        # Custom keys override IBGE keys
        config["ibge"].update(custom_data)

    return config


if __name__ == "__main__":
    """Validation block - test with real data."""
    print("=== Config Module Validation ===\n")

    # Test: Load config data
    try:
        config = load_config_data()
        assert isinstance(config, dict), "Config must be a dict"
        assert "ibge" in config, "Config must have 'ibge' key"
        assert "occupations" in config, "Config must have 'occupations' key"
        assert "interests_hobbies" in config, "Config must have 'interests_hobbies' key"
        print("✓ load_config_data() returns dict with all required keys")
    except Exception as e:
        print(f"✗ load_config_data() failed: {e}")
        exit(1)

    # Test: Verify paths exist
    try:
        assert DATA_DIR.exists(), f"DATA_DIR does not exist: {DATA_DIR}"
        assert CONFIG_DIR.exists(), f"CONFIG_DIR does not exist: {CONFIG_DIR}"
        assert SCHEMAS_DIR.exists(), f"SCHEMAS_DIR does not exist: {SCHEMAS_DIR}"
        assert SCHEMA_PATH.exists(), f"SCHEMA_PATH does not exist: {SCHEMA_PATH}"
        print("✓ All paths exist and are accessible")
    except Exception as e:
        print(f"✗ Path validation failed: {e}")
        exit(1)

    # Test: Verify config structure
    try:
        assert "regioes" in config["ibge"], "IBGE config must have 'regioes'"
        assert "ocupacoes" in config["occupations"], "Occupations must have 'ocupacoes'"
        assert "valores" in config["interests_hobbies"], "Interests must have 'valores'"
        print("✓ Config files have expected structure")
    except Exception as e:
        print(f"✗ Config structure validation failed: {e}")
        exit(1)

    # Test: Verify custom_distribution is merged if exists
    custom_path = CONFIG_DIR / "custom_distribution.json"
    if custom_path.exists():
        try:
            with open(custom_path, "r", encoding="utf-8") as f:
                custom_data = json.load(f)
            # Check that custom keys override IBGE keys
            for key, value in custom_data.items():
                assert config["ibge"][key] == value, f"Custom key '{key}' not merged correctly"
            print(f"✓ custom_distribution.json merged ({len(custom_data)} keys override IBGE)")
        except Exception as e:
            print(f"✗ Custom distribution merge validation failed: {e}")
            exit(1)
    else:
        print("○ custom_distribution.json not found (optional)")

    print("\n✓ All validation checks passed")
