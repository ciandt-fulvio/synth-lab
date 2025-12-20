"""
Gen Synth - Módulo de geração de personas sintéticas.

Este módulo contém todas as funções e classes para gerar personas
sintéticas brasileiras com dados coerentes.

Módulos disponíveis:
- config: Configurações e paths
- utils: Funções utilitárias
- demographics: Geração demográfica
- psychographics: Geração psicográfica
- behavior: Geração comportamental
- disabilities: Geração de deficiências
- tech_capabilities: Geração de capacidades tecnológicas
- biases: Geração de vieses comportamentais
- derivations: Derivações (arquétipo, lifestyle, descrição)
- storage: Salvamento de synths
- validation: Validação de synths
- analysis: Análise de distribuições
- synth_builder: Orquestrador de geração completa
- gen_synth: CLI e interface principal
"""

# Core modules
from synth_lab.gen_synth import (
    analysis,
    behavior,
    biases,
    config,
    demographics,
    derivations,
    disabilities,
    psychographics,
    storage,
    synth_builder,
    tech_capabilities,
    utils,
    validation,
)

# Analysis
from synth_lab.gen_synth.analysis import (
    analyze_age_distribution,
    analyze_regional_distribution,
)

# Configuration
from synth_lab.gen_synth.config import (
    CONFIG_DIR,
    DATA_DIR,
    SCHEMA_PATH,
    SCHEMAS_DIR,
    SYNTHS_DIR,
    load_config_data,
)

# Main API
from synth_lab.gen_synth.gen_synth import cli_main, main

# Storage
from synth_lab.gen_synth.storage import save_synth

# Synth Builder (main orchestrator)
from synth_lab.gen_synth.synth_builder import assemble_synth

# Utilities
from synth_lab.gen_synth.utils import (
    ESCOLARIDADE_ORDEM,
    escolaridade_compativel,
    escolaridade_index,
    gerar_id,
    normal_distribution,
    weighted_choice,
)

# Validation
from synth_lab.gen_synth.validation import (
    validate_batch,
    validate_single_file,
    validate_synth,
)

__all__ = [
    # Modules
    "config",
    "utils",
    "demographics",
    "psychographics",
    "behavior",
    "disabilities",
    "tech_capabilities",
    "biases",
    "derivations",
    "storage",
    "validation",
    "analysis",
    "synth_builder",
    # Main API
    "main",
    "cli_main",
    # Config
    "DATA_DIR",
    "CONFIG_DIR",
    "SCHEMAS_DIR",
    "SYNTHS_DIR",
    "SCHEMA_PATH",
    "load_config_data",
    # Utils
    "ESCOLARIDADE_ORDEM",
    "gerar_id",
    "weighted_choice",
    "normal_distribution",
    "escolaridade_index",
    "escolaridade_compativel",
    # Synth Builder
    "assemble_synth",
    # Storage
    "save_synth",
    # Validation
    "validate_synth",
    "validate_single_file",
    "validate_batch",
    # Analysis
    "analyze_regional_distribution",
    "analyze_age_distribution",
]
