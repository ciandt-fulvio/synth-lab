# Research: SynthLab CLI

**Branch**: `002-synthlab-cli` | **Date**: 2025-12-15

## Research Tasks

### 1. CLI Framework Selection

**Question**: Qual framework usar para o CLI?

**Decision**: `argparse` (stdlib)

**Rationale**:
- O código existente já usa argparse e funciona bem
- Não adiciona dependências externas
- Suficiente para estrutura de subcomandos
- Constitution prefere simplicidade e evitar dependências desnecessárias

**Alternatives Considered**:
- `typer`: Mais moderno, mas adiciona dependência. Rejeitado por simplicidade.
- `click`: Popular, mas também adiciona dependência.

---

### 2. Output Colorido

**Question**: Como implementar output colorido no terminal?

**Decision**: `rich` library

**Rationale**:
- Biblioteca madura e bem mantida
- Auto-detecta suporte a cores no terminal
- Suporta tabelas formatadas (útil para análise de distribuição)
- Suporta progress bars
- Cross-platform (Windows, macOS, Linux)
- Constitution exige observabilidade - rich facilita logs estruturados

**Alternatives Considered**:
- ANSI codes diretos: Complexo para manter, não detecta suporte automático
- `colorama`: Mais simples, mas não tem tabelas nem progress bars
- `termcolor`: Similar ao colorama, limitado

**Implementation Notes**:
```python
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

console = Console()
console.print("[green]Success![/green]")
console.print("[red]Error![/red]")
```

---

### 3. Estrutura de Módulos

**Question**: Como dividir o gen_synth.py monolítico (1363 linhas)?

**Decision**: Dividir por semântica de domínio

**Rationale**:
- Cada arquivo terá responsabilidade única (SRP)
- Facilita manutenção e testes
- Permite imports seletivos
- Constitution exige arquivos <500 linhas

**Module Breakdown**:

| Módulo | Linhas Estimadas | Funções |
|--------|------------------|---------|
| config.py | ~40 | load_config_data, path constants |
| utils.py | ~60 | gerar_id, weighted_choice, normal_distribution, escolaridade_* |
| demographics.py | ~200 | generate_demographics, generate_name, generate_coherent_gender, generate_coherent_family, generate_coherent_occupation |
| psychographics.py | ~80 | generate_big_five, generate_psychographics |
| behavior.py | ~80 | generate_behavior |
| disabilities.py | ~50 | generate_disabilities |
| tech_capabilities.py | ~50 | generate_tech_capabilities |
| biases.py | ~30 | generate_behavioral_biases |
| derivations.py | ~80 | derive_archetype, derive_lifestyle, derive_description, generate_photo_link |
| storage.py | ~40 | save_synth |
| validation.py | ~100 | validate_synth, validate_single_file, validate_batch |
| analysis.py | ~100 | analyze_regional_distribution, analyze_age_distribution |
| synth_builder.py | ~60 | assemble_synth |
| gen_synth.py | ~300 | main(), cli_main() com argparse |

**Total**: ~1270 linhas distribuídas em 14 arquivos (~90 linhas/arquivo em média)

---

### 4. Entry Point Configuration

**Question**: Como configurar o entry point do CLI?

**Decision**: Usar `project.scripts` no pyproject.toml + `__main__.py`

**Rationale**:
- pyproject.toml é o padrão moderno para configuração de pacotes Python
- `__main__.py` permite `python -m synth_lab`
- Ambos métodos coexistem sem conflito

**Implementation**:

```toml
# pyproject.toml
[project.scripts]
synthlab = "synth_lab.__main__:main"
```

```python
# src/synth_lab/__main__.py
from .gen_synth import cli_main

def main():
    cli_main()

if __name__ == "__main__":
    main()
```

---

### 5. Package Structure with src Layout

**Question**: Como estruturar o pacote Python?

**Decision**: src layout padrão

**Rationale**:
- Evita conflitos de import durante desenvolvimento
- Padrão recomendado pela comunidade Python
- Facilita testes isolados
- Compatible com setuptools e pip install -e

**Implementation**:

```toml
# pyproject.toml
[tool.setuptools.packages.find]
where = ["src"]
```

---

### 6. Backward Compatibility

**Question**: Como manter compatibilidade com scripts/gen_synth.py?

**Decision**: Manter script original como wrapper deprecado

**Rationale**:
- Não quebra workflows existentes
- Período de transição para usuários
- Eventualmente pode ser removido

**Implementation**:
```python
# scripts/gen_synth.py (deprecated wrapper)
#!/usr/bin/env python3
"""
DEPRECATED: Use 'synthlab gensynth' instead.
This script is kept for backward compatibility.
"""
import warnings
warnings.warn(
    "scripts/gen_synth.py is deprecated. Use 'synthlab gensynth' instead.",
    DeprecationWarning
)

from synth_lab.gen_synth import cli_main
cli_main()
```

---

## Dependencies Update

**New dependencies required**:
```toml
dependencies = [
    "faker>=21.0.0",
    "jsonschema>=4.20.0",
    "rich>=13.0.0",  # NEW: for colored output
]
```

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Breaking existing workflows | Low | Medium | Wrapper script + clear deprecation warning |
| Module import issues | Low | High | Comprehensive tests before release |
| Performance regression | Low | Medium | Benchmark tests comparing old vs new |
| Windows color support | Low | Low | rich handles this automatically |

---

## Conclusion

Todas as questões técnicas foram resolvidas:
- CLI: argparse (já existente)
- Cores: rich library
- Estrutura: src layout com módulos separados por semântica
- Entry point: pyproject.toml scripts + __main__.py
- Compatibilidade: wrapper script deprecado
