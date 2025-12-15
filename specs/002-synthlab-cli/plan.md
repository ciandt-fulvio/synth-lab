# Implementation Plan: SynthLab CLI

**Branch**: `002-synthlab-cli` | **Date**: 2025-12-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-synthlab-cli/spec.md`

## Summary

Criar CLI `synthlab` com subcomando `gensynth` baseado no script existente `scripts/gen_synth.py`. O código será modularizado em múltiplos arquivos por semântica dentro de `src/synth_lab/gen_synth/`. A saída usará cores ANSI para melhorar a experiência do usuário no terminal.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: faker>=21.0.0, jsonschema>=4.20.0, rich (para output colorido)
**Storage**: JSON files em data/synths/
**Testing**: pytest com markers unit/integration
**Target Platform**: Linux/macOS/Windows (CLI cross-platform)
**Project Type**: Single project (CLI application)
**Performance Goals**: 100 synths em <10 segundos
**Constraints**: Nenhum arquivo >300 linhas, compatibilidade total com gen_synth.py existente
**Scale/Scope**: Geração local, sem limite de synths

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. DRY | PASS | Código modularizado elimina duplicação existente no arquivo monolítico |
| II. TDD | PASS | Testes serão escritos antes da implementação de cada módulo |
| III. Type Safety | PASS | Type hints completos em todas as funções (já presentes no original) |
| IV. Module Size | PASS | Máximo 300 linhas por arquivo (abaixo do limite de 500) |
| V. Real Data Validation | PASS | Cada módulo terá bloco `if __name__ == "__main__":` com validação real |
| VI. Repository Pattern | N/A | Não há banco de dados - apenas arquivos JSON |
| VII. Observability | PASS | Usaremos rich para output estruturado (sem print statements em produção) |

## Project Structure

### Documentation (this feature)

```text
specs/002-synthlab-cli/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (CLI contracts)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
└── synth_lab/
    ├── __init__.py              # Package init with version
    ├── __main__.py              # Entry point: python -m synth_lab
    └── gen_synth/
        ├── __init__.py          # Module exports
        ├── gen_synth.py         # Main orchestrator (assemble_synth, main)
        ├── config.py            # load_config_data, paths
        ├── utils.py             # gerar_id, weighted_choice, normal_distribution, escolaridade_*
        ├── demographics.py      # generate_demographics, generate_name, generate_coherent_*
        ├── psychographics.py    # generate_big_five, generate_psychographics
        ├── behavior.py          # generate_behavior
        ├── disabilities.py      # generate_disabilities
        ├── tech_capabilities.py # generate_tech_capabilities
        ├── biases.py            # generate_behavioral_biases
        ├── derivations.py       # derive_archetype, derive_lifestyle, derive_description
        ├── storage.py           # save_synth, load_synth
        ├── validation.py        # validate_synth, validate_single_file, validate_batch
        ├── analysis.py          # analyze_regional_distribution, analyze_age_distribution
        └── synth_builder.py     # assemble_synth (orquestrador)

tests/
├── conftest.py              # Shared fixtures
├── unit/
│   └── synth_lab/
│       └── gen_synth/
│           ├── test_config.py
│           ├── test_utils.py
│           ├── test_demographics.py
│           ├── test_psychographics.py
│           ├── test_behavior.py
│           ├── test_disabilities.py
│           ├── test_tech_capabilities.py
│           ├── test_biases.py
│           ├── test_derivations.py
│           ├── test_storage.py
│           ├── test_validation.py
│           └── test_analysis.py
└── integration/
    └── test_cli.py
```

**Structure Decision**: Single project com src layout padrão Python. O pacote `synth_lab` conterá o módulo `gen_synth` com todos os submódulos. Entry point via `__main__.py` permite execução como `python -m synth_lab` além do comando `synthlab`.

## Complexity Tracking

> Nenhuma violação de princípios constitucionais.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |
