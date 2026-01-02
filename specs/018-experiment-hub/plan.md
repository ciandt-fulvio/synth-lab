# Implementation Plan: Experiment Hub - Reorganização da Navegação

**Branch**: `018-experiment-hub` | **Date**: 2025-12-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/018-experiment-hub/spec.md`

## Summary

Reorganização da arquitetura de navegação do SynthLab para centralizar o conceito de "Experimento" como container principal de simulações e entrevistas. Implementa modelo "Single Hub" onde a home é a lista de experimentos, synths vão para menu secundário, e todas as simulações/entrevistas são vinculadas obrigatoriamente a um experimento.

## Technical Context

**Language/Version**: Python 3.13+ (backend), TypeScript 5.5.3 (frontend)
**Primary Dependencies**:
- Backend: FastAPI 0.109.0+, Pydantic 2.5.0+, OpenAI SDK 2.8.0+, PostgreSQL3
- Frontend: React 18.3.1, TanStack React Query 5.56, React Router DOM 6.26, shadcn/ui, Tailwind CSS 3.4

**Storage**: PostgreSQL 3 with JSON1 extension and WAL mode (`output/synthlab.db`)
**Testing**: pytest 8.0+ (backend), ESLint (frontend - sem testes automatizados)
**Target Platform**: Web application (Linux/macOS server + browser)
**Project Type**: Web application (backend + frontend separados)
**Performance Goals**: Resposta instantânea para navegação (<100ms), suporte a centenas de experimentos
**Constraints**: Single-user (sem colaboração), dados locais apenas
**Scale/Scope**: 100+ experimentos, 10+ simulações/entrevistas por experimento

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First Development (TDD/BDD) | PASS | Testes escritos antes da implementação para novos endpoints e componentes |
| II. Fast Test Battery (<5s) | PASS | Testes unitários para backend, sem testes frontend (mantém padrão existente) |
| III. Complete Test Battery Before PR | PASS | Todos os testes devem passar antes do PR |
| IV. Frequent Commits | PASS | Commits a cada tarefa concluída |
| V. Simplicity (<500 lines) | PASS | Novos arquivos seguirão limite de 500 linhas |
| VI. Language (EN code, PT docs) | PASS | Código em inglês, documentação em português |
| VII. Architecture | PASS | Segue estrutura existente: api/, domain/, infrastructure/, repositories/ |
| IX. Other Principles | PASS | Phoenix tracing, DRY, SOLID, KISS, YAGNI |

**Gate Status**: PASSED - Nenhuma violação identificada.

## Project Structure

### Documentation (this feature)

```text
specs/018-experiment-hub/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
backend/
├── src/synth_lab/
│   ├── api/
│   │   ├── routers/
│   │   │   ├── experiments.py     # NEW: CRUD experimentos
│   │   │   ├── synth_groups.py    # NEW: Listagem/criação de grupos
│   │   │   ├── research.py        # MODIFIED: Adiciona experiment_id
│   │   │   └── simulation.py      # MODIFIED: Adiciona experiment_id
│   │   └── schemas/
│   │       ├── experiments.py     # NEW: DTOs de experimentos
│   │       └── synth_groups.py    # NEW: DTOs de grupos
│   ├── domain/
│   │   └── entities/
│   │       ├── experiment.py      # NEW: Entidade Experiment
│   │       └── synth_group.py     # NEW: Entidade SynthGroup
│   ├── infrastructure/
│   │   └── database.py            # MODIFIED: Novas tabelas
│   └── repositories/
│       ├── experiment_repository.py    # NEW
│       └── synth_group_repository.py   # NEW
└── tests/
    ├── unit/
    │   ├── test_experiment_repository.py  # NEW
    │   └── test_synth_group_repository.py # NEW
    └── integration/
        └── test_experiments_api.py        # NEW

frontend/
├── src/
│   ├── components/
│   │   ├── experiments/
│   │   │   ├── ExperimentCard.tsx         # NEW
│   │   │   ├── ExperimentForm.tsx         # NEW
│   │   │   └── EmptyState.tsx             # NEW
│   │   └── layout/
│   │       └── Header.tsx                 # MODIFIED: Adiciona ícone Synths
│   ├── pages/
│   │   ├── Index.tsx                      # MODIFIED: ExperimentList
│   │   ├── ExperimentDetail.tsx           # NEW
│   │   ├── SimulationDetail.tsx           # NEW (ou move existente)
│   │   └── Synths.tsx                     # MODIFIED: Rota /synths
│   ├── hooks/
│   │   ├── useExperiments.ts              # NEW
│   │   └── useSynthGroups.ts              # NEW
│   ├── services/
│   │   ├── experimentsApi.ts              # NEW
│   │   └── synthGroupsApi.ts              # NEW
│   └── types/
│       ├── experiment.ts                  # NEW
│       └── synthGroup.ts                  # NEW
└── tests/
    └── (sem testes automatizados - segue padrão existente)
```

**Structure Decision**: Web application com backend Python (FastAPI) e frontend React/TypeScript separados. Mantém estrutura existente, adicionando novos módulos para experimentos e synth groups.

## Complexity Tracking

> **No violations identified - section not required**

---

## Constitution Check - Post-Design Review

*Re-evaluation after Phase 1 design completion.*

| Principle | Status | Post-Design Notes |
|-----------|--------|-------------------|
| I. Test-First Development (TDD/BDD) | PASS | Testes definidos para repositories e API endpoints. Acceptance scenarios em spec.md. |
| II. Fast Test Battery (<5s) | PASS | Testes unitários para repositories (~2s estimado). Sem testes frontend (padrão existente). |
| III. Complete Test Battery Before PR | PASS | Testes de integração para API incluídos no plano. |
| IV. Frequent Commits | PASS | Estrutura modular permite commits incrementais por componente. |
| V. Simplicity (<500 lines) | PASS | Design modular: repository (~150 linhas), router (~100 linhas), schemas (~80 linhas), pages (~300 linhas). |
| VI. Language (EN code, PT docs) | PASS | Código em inglês (ExperimentRepository, SynthGroup). Docs em português. |
| VII. Architecture | PASS | Segue estrutura existente. Novos módulos em api/routers/, repositories/, components/. |
| IX. Other Principles | PASS | DRY (reutiliza BaseRepository), KISS (endpoints simples), YAGNI (sem features extras). |

**Post-Design Gate Status**: PASSED

### Design Validation Summary

| Artifact | Status | Notes |
|----------|--------|-------|
| research.md | COMPLETE | 10 decisões documentadas com alternativas |
| data-model.md | COMPLETE | 5 entidades, schema SQL completo, queries comuns |
| contracts/openapi.yaml | COMPLETE | 11 endpoints, 18 schemas |
| quickstart.md | COMPLETE | Exemplos de uso via API e frontend |

### Files to Create/Modify (Summary)

| Type | Count | Description |
|------|-------|-------------|
| NEW Backend | 8 files | repositories (2), routers (2), schemas (2), domain entities (2) |
| MODIFIED Backend | 3 files | database.py, research router, simulation router |
| NEW Frontend | 10 files | pages (2), components (3), hooks (2), services (2), types (2) |
| MODIFIED Frontend | 3 files | App.tsx, Index.tsx, Header (novo ou existente) |
| NEW Tests | 3 files | unit tests (2), integration test (1) |

**Total**: ~27 arquivos (18 novos, 6+ modificados, 3 testes)
