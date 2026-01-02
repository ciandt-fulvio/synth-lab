# Implementation Plan: Sistema de Simulacao de Impacto de Features

**Branch**: `016-feature-impact-simulation` | **Date**: 2025-12-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/016-feature-impact-simulation/spec.md`

## Summary

Sistema de simulacao Monte Carlo para avaliar impacto de decisoes de design de produto sobre diferentes perfis de synths. O sistema:
1. Estende o processo de geracao de synths (gensynth) com atributos observaveis e latentes para simulacao
2. Permite cadastro de Feature Scorecards com assistencia de LLM
3. Executa simulacoes Monte Carlo (N synths x M execucoes)
4. Analisa resultados por regiao do espaco de synths
5. Compara cenarios pre-definidos (baseline, crisis, first-use)

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**:
- Existentes: FastAPI 0.109.0+, OpenAI SDK 2.8.0+, NumPy (a adicionar), SciPy (a adicionar para distribuicoes Beta)
- Rich, Typer, Loguru (CLI e logging)
- Pydantic 2.5.0+ (validacao)
**Storage**: PostgreSQL 3 com JSON1 extension (output/synthlab.db) - WAL mode
**Testing**: pytest 8.0.0+ com pytest-asyncio
**Target Platform**: Linux/macOS server, CLI inicial
**Project Type**: Single project (backend Python)
**Performance Goals**:
- Simulacao 500 synths x 100 execucoes < 30 segundos (SC-003)
- Analise de sensibilidade < 10 segundos (SC-005)
**Constraints**:
- Integracao com gensynth existente (synth_builder.py)
- Manter compatibilidade com schema de synth existente
- Cenarios pre-definidos em JSON (sem CRUD)
**Scale/Scope**:
- Populacao tipica: 500-1000 synths
- Execucoes tipicas: 100-500 por simulacao

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Test-First Development (TDD/BDD) - NON-NEGOTIABLE
- ✅ Spec define acceptance scenarios em formato Given-When-Then
- ✅ Tests serao escritos ANTES da implementacao
- ✅ BDD acceptance criteria definidos para todas as User Stories

### II. Fast Test Battery on Every Commit
- ✅ Unit tests para modulos de simulacao devem completar < 5s
- ✅ Tests serao executados via pre-commit hooks

### III. Complete Test Battery Before Pull Requests
- ✅ All tests (fast + slow) pass before PR
- ✅ Coverage minima sera definida no plan

### IV. Frequent Version Control Commits
- ✅ Commits atomicos por tarefa
- ✅ Mensagens claras descrevendo o que foi feito

### V. Simplicity and Code Quality
- ✅ Funcoes < 30 linhas
- ✅ Arquivos < 500 linhas
- ✅ Sem dependencias desnecessarias
- ⚠️ Complexidade justificada: Monte Carlo requer numpy/scipy para performance

### VI. Language
- ✅ Codigo em ingles (classes, variaveis, funcoes)
- ✅ Documentacao em portugues
- ✅ i18n ready (strings externalizadas)

### VII. Architecture
- ✅ Segue estrutura existente: src/synth_lab/
- ✅ Novos modulos em services/simulation/
- ✅ Domain models em domain/entities/
- ✅ API endpoints em api/routers/

### IX. Other Principles
- ✅ Phoenix tracing para LLM calls (FR-012, FR-013)
- ✅ DRY, SOLID, KISS, YAGNI
- ✅ Alembic para migrations se necessario (schema extension)

**GATE RESULT**: ✅ PASS - All principles satisfied or justified

## Project Structure

### Documentation (this feature)

```text
specs/016-feature-impact-simulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── simulation-api.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/synth_lab/
├── gen_synth/
│   ├── synth_builder.py          # MODIFICAR: adicionar simulation_attributes
│   ├── simulation_attributes.py  # NOVO: gerar atributos observaveis/latentes
│   └── ...
├── domain/
│   └── entities/
│       ├── feature_scorecard.py  # NOVO: entidade FeatureScorecard
│       ├── scenario.py           # NOVO: entidade Scenario
│       ├── simulation_run.py     # NOVO: entidade SimulationRun
│       └── synth_outcome.py      # NOVO: entidade SynthOutcome
├── services/
│   └── simulation/               # NOVO: modulo de simulacao
│       ├── __init__.py
│       ├── engine.py             # Monte Carlo engine
│       ├── sample_state.py       # sample_user_state function
│       ├── probability.py        # p_attempt, p_success calculations
│       ├── analyzer.py           # Region analysis
│       ├── sensitivity.py        # Sensitivity analysis
│       └── scorecard_llm.py      # LLM integration for scorecards
├── repositories/
│   ├── scorecard_repository.py   # NOVO: persistencia de scorecards
│   └── simulation_repository.py  # NOVO: persistencia de simulacoes
├── api/
│   └── routers/
│       └── simulation.py         # NOVO: endpoints REST
└── data/
    └── scenarios/                # NOVO: cenarios pre-definidos
        ├── baseline.json
        ├── crisis.json
        └── first-use.json

tests/
├── unit/
│   └── simulation/
│       ├── test_simulation_attributes.py
│       ├── test_engine.py
│       ├── test_sample_state.py
│       ├── test_probability.py
│       └── test_analyzer.py
├── integration/
│   └── simulation/
│       └── test_full_simulation.py
└── contract/
    └── test_simulation_api.py
```

**Structure Decision**: Single project structure, extending existing synth-lab codebase. New simulation module added under services/ following existing patterns.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| NumPy/SciPy dependencies | Beta distributions and Monte Carlo require vectorized operations for performance (500x100 = 50k iterations < 30s) | Pure Python loops would be too slow |
| sklearn dependency | DecisionTree para analise de regioes com regras interpretaveis | Implementar manualmente nao vale o esforco |
| LLM integration for scorecards | FR-012/FR-013 require LLM to generate justificativas e hipoteses | Manual text is not scalable |

---

## Constitution Check - Post-Design Re-evaluation

*Re-avaliacao apos Phase 1 design completada.*

### I. Test-First Development (TDD/BDD)
- ✅ data-model.md define entidades claras para testar
- ✅ contracts/simulation-api.yaml define contrato para contract tests
- ✅ quickstart.md fornece cenarios de uso para BDD

### II. Fast Test Battery
- ✅ Arquitetura modular permite unit tests isolados
- ✅ services/simulation/*.py podem ser testados independentemente
- ✅ Estimativa: 20-30 unit tests, < 5s total

### III. Complete Test Battery
- ✅ integration/test_full_simulation.py para E2E
- ✅ contract/test_simulation_api.py para validar OpenAPI

### V. Simplicity and Code Quality
- ✅ Modulos separados (engine, probability, analyzer) < 500 linhas cada
- ✅ Responsabilidades claras por arquivo
- ⚠️ Justificado: numpy + sklearn para performance

### VII. Architecture
- ✅ Segue Clean Architecture existente
- ✅ Domain entities independentes de infra
- ✅ Repositories abstraem persistencia
- ✅ Services contem logica de negocio

**POST-DESIGN GATE RESULT**: ✅ PASS - Design alinhado com Constitution

---

## Dependencies to Add

```toml
# pyproject.toml - [project.dependencies]
"numpy>=1.26.0",
"scikit-learn>=1.4.0",
```

---

## Next Steps

Execute `/speckit.tasks` para gerar o task breakdown detalhado baseado neste plano.
