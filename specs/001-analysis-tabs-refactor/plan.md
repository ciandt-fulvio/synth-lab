# Implementation Plan: Analysis Tabs Refactor

**Branch**: `001-analysis-tabs-refactor` | **Date**: 2025-12-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-analysis-tabs-refactor/spec.md`

## Summary

Reorganizar abas de análise quantitativa do experimento, movendo gráficos entre fases, simplificando casos especiais, e adicionando capacidade de entrevistar automaticamente casos extremos. Remove aba "Deep Dive", move SHAP/PDP para aba Influência, adiciona click-to-explain para casos extremos e outliers, e cria entrevistas automáticas com 10 synths (top/bottom 5).

**Technical Approach**: Refatoração de componentes React existentes + backend cleanup de APIs não utilizadas + nova funcionalidade de criar entrevistas via API.

## Technical Context

**Language/Version**: Python 3.13+ (backend), TypeScript 5.5+ (frontend)
**Primary Dependencies**:
- Backend: FastAPI 0.109+, Pydantic 2.5+
- Frontend: React 18, TanStack Query 5.56+, shadcn/ui, Recharts 2.12.7+

**Storage**: PostgreSQL 3 with JSON1 extension (output/synthlab.db)
**Testing**: pytest (backend), React Testing Library (frontend)
**Target Platform**: Web application (frontend + backend)
**Project Type**: Web
**Performance Goals**: < 3s para carregar gráficos, < 10s para criar entrevista automática
**Constraints**: Manter compatibilidade com dados existentes
**Scale/Scope**: 5 componentes de página refatorados, ~10 componentes de gráfico reorganizados, 1 endpoint novo, 2-3 endpoints removidos

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**✅ Test-First Development (TDD/BDD)**:
- Testes de componentes React para validar reorganização de abas
- Testes de integração para validar remoção de APIs antigas
- Testes E2E para validar fluxo de click-to-explain
- Testes de API para nova funcionalidade de entrevista automática

**✅ Fast Test Battery**:
- Testes unitários de componentes React < 0.5s cada
- Total fast battery < 5s

**✅ Frequent Commits**:
- Commit após cada refatoração de componente
- Commit após cada remoção de API
- Commit após implementação de nova feature

**✅ Simplicity**:
- Componentes React < 500 linhas (alguns podem chegar a 1000 por serem TSX)
- Funções < 30 linhas
- Remover código não utilizado (cleanup)

**✅ Architecture Compliance**:
- **Frontend**: Pages compõem componentes, hooks encapsulam React Query
- **Backend**: Routers → services → repositories
- Services contêm lógica de criação de entrevista automática
- Repositories acessam dados de synths para extremos

**No violations** - Refatoração segue padrões existentes

## Project Structure

### Documentation (this feature)

```text
specs/001-analysis-tabs-refactor/
├── plan.md              # This file
├── data-model.md        # Entities (minimal - usa estruturas existentes)
├── quickstart.md        # User guide
└── checklists/
    └── requirements.md  # Already created
```

### Source Code (repository root)

```text
# Backend
src/synth_lab/
├── api/routers/
│   └── analysis.py           # MODIFY: remove unused endpoints
├── services/
│   └── interview_service.py  # MODIFY: add create_auto_interview()
└── repositories/
    └── synth_repository.py   # MODIFY: add get_extreme_cases()

# Frontend
frontend/src/
├── components/experiments/results/
│   ├── PhaseInfluence.tsx           # MODIFY: add SHAP + PDP
│   ├── PhaseSpecial.tsx             # MODIFY: add click-to-explain + auto-interview button
│   ├── PhaseSegmentation.tsx        # NO CHANGE
│   ├── PhaseOverview.tsx            # NO CHANGE
│   ├── PhaseDeepDive.tsx            # DELETE
│   ├── ExtremeCasesSection.tsx      # MODIFY: remove suggestions + add click handler
│   ├── OutliersSection.tsx          # MODIFY: simplify UI + add click handler
│   ├── SHAPWaterfallSection.tsx     # MODIFY: remove dropdown + receive selected synth via props
│   ├── charts/
│   │   ├── AttributeImportanceChart.tsx  # DELETE (não usado)
│   │   ├── AttributeCorrelationChart.tsx # DELETE (não usado)
│   │   ├── ShapSummaryChart.tsx          # MOVE to PhaseInfluence
│   │   └── PDPChart.tsx                  # MOVE to PhaseInfluence
│   └── AutoInterviewButton.tsx      # CREATE: new component
├── hooks/
│   └── use-experiments.ts           # MODIFY: add useCreateAutoInterview()
├── services/
│   └── experiments-api.ts           # MODIFY: add createAutoInterview()
└── types/
    └── experiment.ts                # MODIFY: add AutoInterviewRequest type

# Tests
tests/
├── unit/
│   └── test_interview_service.py    # CREATE: test auto-interview creation
└── integration/
    └── test_analysis_api.py         # MODIFY: test new endpoint + remove old tests

frontend/src/components/__tests__/
├── PhaseInfluence.test.tsx          # MODIFY: validate SHAP + PDP
├── PhaseSpecial.test.tsx            # MODIFY: validate click-to-explain
└── AutoInterviewButton.test.tsx     # CREATE: test auto-interview button
```

**Structure Decision**: Web application (Option 2) - existing structure maintained with targeted modifications

## Complexity Tracking

> No violations - refactoring follows existing patterns and simplifies codebase by removing unused code

---

## Phase 0: Research (MINIMAL)

Esta é uma refatoração de código existente, não requer pesquisa de novas tecnologias.

**Decisões já tomadas**:
- Usar padrões React existentes (hooks + React Query)
- Usar serviços existentes de interview creation
- Usar APIs existentes de extreme cases e outliers
- Remover código não utilizado (backend + frontend)

**Nenhum NEEDS CLARIFICATION** - escopo claro do spec.

---

## Phase 1: Design & Contracts

### Data Model (Minimal)

Ver `data-model.md` - usa entidades existentes (Synth, Interview, ExtremeCase, Outlier)

### API Contracts

Ver `contracts/` - define:
- POST `/experiments/{id}/interviews/auto` - criar entrevista automática
- Remoção de endpoints não utilizados (Attribute Importance/Correlation se não usados em outros lugares)

### Quickstart

Ver `quickstart.md` - guia do usuário para nova jornada de análise

---

## Next Steps

After `/speckit.plan` completion:
1. Run `/speckit.tasks` to generate implementation task list
2. Execute tasks following TDD/BDD principles
3. Validate Constitution compliance during code review
