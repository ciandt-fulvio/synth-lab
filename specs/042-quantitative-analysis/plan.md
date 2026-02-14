# Implementation Plan: Análise Quantitativa (Modelagem Causal + Monte Carlo)

**Branch**: `042-quantitative-analysis` | **Date**: 2026-02-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/042-quantitative-analysis/spec.md`

## Summary

Implementar análise quantitativa no synth-lab: o PM gera um modelo causal (DAG) via LLM (gpt-5.1), calibra premissas via Likert, roda simulação Monte Carlo server-side usando synths reais como população, e obtém resultados com interpretações AI (gpt-4o-mini). O interview_guide é auto-gerado a partir das premissas mais sensíveis. Tudo em uma aba única "Análise Quanti" na página de detalhe do experimento.

## Technical Context

**Language/Version**: Python 3.13+ (backend), TypeScript 5.5+ (frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0+, Pydantic, OpenAI SDK, NumPy (simulação), React 18, TanStack Query, Recharts, shadcn/ui
**Storage**: PostgreSQL 14+ (Alembic migrations)
**Testing**: pytest (unit + integration), Playwright (E2E)
**Target Platform**: Docker containers → Railway (AMD64 production)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: Simulação < 15s para 500 synths × 3.000 iterações; DAG generation < 10s; Interpretações < 5s cada (paralelo)
**Constraints**: LLM timeout 30s; arquivos < 500 linhas; funções < 30 linhas; Phoenix tracing obrigatório
**Scale/Scope**: 1 experimento por vez; até 500 synths/grupo; 10 userVars fixas; 7-10 edges por DAG

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Status | Notas |
|-----------|--------|-------|
| I. TDD (NON-NEGOTIABLE) | ✅ PASS | Testes antes de implementação. Mocks para OpenAI, real DB para integration. |
| II. Fast Tests < 5s | ✅ PASS | Unit tests com mocks. Monte Carlo testado com seed fixo e N pequeno. |
| III. Complete Tests Before PR | ✅ PASS | Unit + integration + E2E cobrirão fluxo completo. |
| IV. Frequent Commits | ✅ PASS | 1 commit por entidade/serviço/endpoint/componente. |
| V. Simplicity | ✅ PASS | Service split em métodos < 30 linhas. SimulationEngine isolado. |
| VI. Language | ✅ PASS | Code em English, docs em Portuguese, UI strings em Portuguese BR. |
| VII. Architecture (NON-NEGOTIABLE) | ✅ PASS | Router → Service → Repository. LLM com Phoenix tracing. |

**Resultado**: Todos os gates passam. Nenhuma violação.

## Project Structure

### Documentation (this feature)

```text
specs/042-quantitative-analysis/
├── plan.md              # This file
├── spec.md              # Feature specification
├── ADR.md               # Architecture decisions
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (API contracts)
│   └── api.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/synth_lab/
├── domain/entities/
│   ├── causal_model.py          # CausalModel, CausalEdge entities
│   └── simulation_run.py        # SimulationRun, AnalysisInterpretation entities
├── models/orm/
│   ├── causal_model.py          # CausalModel ORM + CausalEdge ORM
│   └── simulation_run.py        # SimulationRun ORM + AnalysisInterpretation ORM
├── repositories/
│   ├── causal_model_repository.py
│   └── simulation_run_repository.py
├── services/
│   ├── quantitative_analysis_service.py   # Orquestração (generate DAG, run sim, interp)
│   └── simulation_engine.py               # Monte Carlo puro (sem I/O, sem LLM)
├── api/
│   ├── routers/quantitative_analysis.py   # REST endpoints
│   └── schemas/quantitative_analysis.py   # Request/Response schemas
└── infrastructure/database/migrations/versions/
    └── xxxx_add_causal_model_tables.py    # Alembic migration

frontend/src/
├── components/quantitative/
│   ├── CausalDAGView.tsx          # DAG visualization (nodes + edges)
│   ├── LikertAssertions.tsx       # Likert scale inputs per edge
│   ├── SimulationResults.tsx      # Distribution + segments + sensitivity
│   ├── DistributionChart.tsx      # Histogram + stats
│   ├── SegmentCards.tsx           # 9 segment cards (age × income × edu)
│   └── SensitivityBars.tsx        # Horizontal bar chart by impact
├── hooks/
│   └── use-quantitative-analysis.ts   # React Query hooks
├── services/
│   └── quantitative-analysis-api.ts   # fetchAPI calls
├── types/
│   └── quantitative-analysis.ts       # TypeScript types
└── lib/query-keys.ts                  # Add quantitative keys

tests/
├── unit/
│   ├── test_simulation_engine.py      # Monte Carlo logic (deterministic with seed)
│   ├── test_causal_model_entity.py    # Entity validation
│   └── test_uservar_extractors.py     # Normalization logic
├── integration/
│   ├── test_quantitative_analysis_service.py  # Service with mocked LLM
│   ├── test_causal_model_repository.py        # Repository with real DB
│   └── test_simulation_run_repository.py
└── e2e/
    └── quantitative-analysis.spec.ts  # Playwright flow
```

**Structure Decision**: Web application — backend (Python/FastAPI) + frontend (React/TypeScript). Segue estrutura existente do synth-lab. A simulation_engine.py é separada do service para manter lógica pura de simulação testável sem mocks de LLM.

## Complexity Tracking

> Nenhuma violação da Constitution. Nenhuma justificativa necessária.
