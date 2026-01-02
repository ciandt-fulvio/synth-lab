# Implementation Plan: Refatoração do Modelo Experimento-Análise-Entrevista

**Branch**: `019-experiment-refactor` | **Date**: 2025-12-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/019-experiment-refactor/spec.md`

## Summary

Refatorar o modelo de dados para consolidar o scorecard dentro do experimento (em vez de entidade separada), estabelecer relação 1:1 entre experimento e análise quantitativa (renomeando "simulação"), manter relação 1:N com entrevistas, e restaurar streaming SSE funcional para acompanhamento de entrevistas em tempo real.

## Technical Context

**Language/Version**: Python 3.13+ (backend), TypeScript 5.5+ (frontend)
**Primary Dependencies**: FastAPI 0.109+, Pydantic 2.5+, React 18, TanStack Query 5.56+, shadcn/ui
**Storage**: PostgreSQL 3 com JSON1 extension e WAL mode (`output/synthlab.db`)
**Testing**: pytest 8+ (backend), vitest (frontend se configurado)
**Target Platform**: Web application (Linux/macOS/Windows server + modern browsers)
**Project Type**: Web (backend + frontend)
**Performance Goals**: SSE latency < 2s, scorecard estimation < 10s, analysis < 2min
**Constraints**: Manter compatibilidade com dados existentes via migração
**Scale/Scope**: Usuário único ou poucos concurrent, centenas de experimentos

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Pre-Design | Post-Design | Notes |
|-----------|------------|-------------|-------|
| I. TDD/BDD - Tests before code | ⏳ Pending | ⏳ | Tests must be written first |
| II. Fast test battery < 5s | ⏳ Pending | ⏳ | Unit tests for refactored services |
| III. Complete tests before PR | ⏳ Pending | ⏳ | All acceptance scenarios covered |
| IV. Frequent commits | ⏳ Pending | ⏳ | Commit per task phase |
| V. Simplicity (< 500 lines) | ✅ Pass | ⏳ | Existing patterns followed |
| VI. Language (EN code, PT docs) | ✅ Pass | ⏳ | Matches existing codebase |
| VII. Architecture NON-NEGOTIABLE | ✅ Pass | ⏳ | See details below |
| VIII. Tracing, DRY, SOLID, KISS | ⏳ Pending | ⏳ | Phoenix tracing for LLM calls |

### Architecture Compliance Checklist (NON-NEGOTIABLE)

**Backend:**
- [ ] Router só faz `request → service → response`
- [ ] Validações de negócio em services (não em routers)
- [ ] SQL em repositories (não em services/routers)
- [ ] Queries SQL parametrizadas (`?` placeholders)
- [ ] Prompts LLM em services (não em routers)
- [ ] Chamadas LLM com Phoenix tracing (`_tracer.start_as_current_span()`)

**Frontend:**
- [ ] Pages usam hooks para dados (não fetch direto)
- [ ] Componentes são puros (props → JSX)
- [ ] Hooks encapsulam React Query (useQuery, useMutation)
- [ ] Query keys em `lib/query-keys.ts`
- [ ] Services usam `fetchAPI` base

## Project Structure

### Documentation (this feature)

```text
specs/019-experiment-refactor/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── experiment-api.yaml
│   ├── analysis-api.yaml
│   └── interview-api.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
# Backend (Python)
src/synth_lab/
├── api/
│   ├── routers/
│   │   ├── experiments.py      # MODIFY: Add scorecard to experiment
│   │   ├── simulation.py       # RENAME concepts to "analysis"
│   │   └── research.py         # SSE streaming (exists, verify frontend)
│   └── schemas/
│       ├── experiments.py      # MODIFY: Include scorecard dimensions
│       └── simulation.py       # NEW: Move inline schemas here
├── domain/entities/
│   ├── experiment.py           # NEW: With embedded scorecard
│   └── analysis_run.py         # NEW: Replaces simulation_run.py
├── repositories/
│   ├── experiment_repository.py    # NEW: Handle embedded scorecard
│   └── analysis_repository.py      # NEW: Replaces simulation_repository.py
├── services/
│   ├── experiment_service.py       # NEW: Scorecard + analysis orchestration
│   └── analysis/                   # NEW: Analysis domain
│       └── analysis_service.py     # NEW: Core analysis logic
└── infrastructure/
    └── database.py                 # NEW: Create new schema from scratch

# Frontend (TypeScript)
frontend/src/
├── pages/
│   ├── ExperimentDetail.tsx        # MODIFY: Show scorecard, rename UI
│   └── InterviewDetail.tsx         # VERIFY: SSE connection working
├── components/
│   ├── experiments/
│   │   ├── ExperimentCard.tsx      # MODIFY: Show scorecard summary
│   │   ├── NewExperimentDialog.tsx # MODIFY: Include scorecard form
│   │   └── ScorecardForm.tsx       # NEW: Embedded scorecard editor
│   └── interviews/
│       └── LiveInterviewGrid.tsx   # VERIFY: SSE working
├── hooks/
│   ├── use-experiments.ts          # MODIFY: Include scorecard ops
│   ├── use-sse.ts                  # VERIFY: Connection working
│   └── use-live-interviews.ts      # VERIFY: State management
├── services/
│   └── experiments-api.ts          # MODIFY: Scorecard endpoints
├── types/
│   ├── experiment.ts               # MODIFY: Include scorecard types
│   └── sse-events.ts               # EXISTS: Verify correct
└── lib/
    └── query-keys.ts               # MODIFY: Add scorecard keys
```

**Structure Decision**: Mantém estrutura existente com modificações incrementais. Não cria novos diretórios. Renomeia "simulation" → "analysis" apenas na UI e documentação, mantém nomes técnicos internos por compatibilidade.

## Complexity Tracking

> **No violations requiring justification at this point**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |

## Key Changes Summary

### Model Changes

| Entity | Before | After |
|--------|--------|-------|
| Experiment | name, hypothesis, description | + scorecard dimensions embedded |
| Scorecard | Separate entity (feature_scorecards) | Embedded in experiment JSON |
| Simulation | N simulações per experiment | 1 análise quantitativa per experiment |
| Interview | N entrevistas per experiment | N entrevistas per experiment (unchanged) |

### API Changes

| Endpoint | Before | After |
|----------|--------|-------|
| POST /experiments | Create basic experiment | Create experiment with scorecard |
| POST /experiments/{id}/estimate-scorecard | Exists, calls scorecard service | Move logic to experiment service |
| POST /experiments/{id}/simulations | Create N simulations | POST /experiments/{id}/analysis (single) |
| GET /experiments/{id}/simulations | List N simulations | GET /experiments/{id}/analysis (single) |
| GET /research/{id}/stream | SSE streaming (exists) | Verify frontend connects correctly |

### UI Terminology Changes

| Before | After |
|--------|-------|
| Simulação | Análise Quantitativa |
| Simular | Executar Análise |
| Nova Simulação | Executar Análise |

## Database Strategy

**NOTA**: Banco de dados está vazio. Criar estrutura nova do zero, sem migração.

### Nova Estrutura

1. **experiments**: Hub central com scorecard embutido (JSON)
2. **analysis_runs**: Uma análise por experimento (1:1), referencia experiment_id diretamente
3. **synth_outcomes**: Resultados por synth da análise
4. **research_executions**: Entrevistas (N por experimento)
5. **transcripts**: Transcrições das entrevistas

### Tabelas Removidas/Obsoletas

- `feature_scorecards`: Não será criada (scorecard embutido no experiment)
- `simulation_runs`: Renomeada para `analysis_runs` com estrutura simplificada
