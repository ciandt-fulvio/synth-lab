# Implementation Plan: Frontend para Exploracao de Cenarios com Visualizacao de Arvore

**Branch**: `025-exploration-frontend` | **Date**: 2025-12-31 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/025-exploration-frontend/spec.md`

## Summary

Implementar frontend React para visualizacao e interacao com exploracoes de cenarios. A feature consome a API backend implementada em spec 024 e oferece:
- Visualizacao interativa de arvore hierarquica com zoom/pan
- Detalhes de nos via painel lateral
- Destaque de caminho vencedor
- Progresso em tempo real via polling
- Formulario para iniciar novas exploracoes

## Technical Context

**Language/Version**: TypeScript 5.5+ (frontend)
**Primary Dependencies**: React 18.3+, TanStack Query 5.56+, react-d3-tree 3.6.6, shadcn/ui
**Storage**: N/A (dados via API backend)
**Testing**: Vitest + React Testing Library (futuro)
**Target Platform**: Browser (Chrome, Firefox, Safari modernos)
**Project Type**: web (frontend only - backend ja existe)
**Performance Goals**: Tree render < 2s para 50 nos; polling interval 3-5s
**Constraints**: Arvores com ate 100 nos; polling nao deve degradar UX
**Scale/Scope**: Pagina de exploracao acessivel via /experiments/:id/explorations/:explorationId

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First (TDD/BDD) | ⚠️ | Frontend tests serao escritos apos componentes estabilizarem |
| II. Fast Test Battery | ⏸️ | N/A para fase inicial de frontend |
| III. Complete Tests Before PR | ⏸️ | Aplicavel ao final da implementacao |
| IV. Frequent Commits | ✅ | Commits a cada fase completa |
| V. Simplicity | ✅ | Usar componentes existentes (shadcn/ui) |
| VI. Language | ✅ | Codigo em ingles, UI em portugues |
| VII. Architecture | ✅ | Seguir arquitetura frontend (docs/arquitetura_front.md) |
| VIII. Other Principles | ✅ | DRY, SOLID, KISS, YAGNI |

## Project Structure

### Documentation (this feature)

```text
specs/025-exploration-frontend/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (frontend types)
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (API types)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── pages/
│   │   └── ExplorationDetail.tsx       # Nova pagina de exploracao
│   │
│   ├── components/
│   │   └── exploration/                # Componentes da feature
│   │       ├── ExplorationTree.tsx     # Visualizacao da arvore
│   │       ├── NodeDetailsPanel.tsx    # Painel de detalhes do no
│   │       ├── WinningPathPanel.tsx    # Painel do caminho vencedor
│   │       ├── ExplorationProgress.tsx # Indicadores de progresso
│   │       ├── NewExplorationForm.tsx  # Formulario de nova exploracao
│   │       ├── ExplorationList.tsx     # Lista de exploracoes
│   │       └── ActionCatalogDialog.tsx # Modal do catalogo de acoes
│   │
│   ├── hooks/
│   │   └── use-exploration.ts          # Hooks React Query
│   │
│   ├── services/
│   │   └── exploration-api.ts          # Chamadas API
│   │
│   └── types/
│       └── exploration.ts              # TypeScript types
│
└── package.json                        # +react-d3-tree dependency
```

**Structure Decision**: Adicionar componentes em `components/exploration/` seguindo padrao existente (ex: `components/experiments/`). Nova pagina em `pages/`. Hooks e services em arquivos dedicados.

## Constitution Check (Post-Design)

*Re-evaluated after Phase 1 design completion.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First (TDD/BDD) | ⚠️ | Frontend tests serao escritos apos componentes estabilizarem (justificado abaixo) |
| II. Fast Test Battery | ⏸️ | N/A para fase inicial de frontend |
| III. Complete Tests Before PR | ✅ | Sera aplicado ao final da implementacao |
| IV. Frequent Commits | ✅ | Commits a cada componente/hook completo |
| V. Simplicity | ✅ | Usa react-d3-tree (lib madura), shadcn/ui (existente), React Query (padrao do projeto) |
| VI. Language | ✅ | Codigo em ingles (types, hooks, components), UI em portugues (labels, mensagens) |
| VII. Architecture | ✅ | Design segue docs/arquitetura_front.md (pages, components, hooks, services, types) |
| VIII. Other Principles | ✅ | DRY (query keys centralizados), KISS (polling simples), YAGNI (sem WebSocket) |

**Architectural Compliance Verification**:
- ✅ Pages: composição de componentes + hooks (ExplorationDetail.tsx)
- ✅ Components: puros, recebem props (ExplorationTree, NodeDetailsPanel)
- ✅ Hooks: encapsulam React Query (useExploration, useExplorationTree)
- ✅ Services: funções API usando fetchAPI (exploration-api.ts)
- ✅ Query Keys: centralizadas em lib/query-keys.ts

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| TDD relaxado | Frontend visual exploratório | Componentes visuais estabilizam após iteração de design; tests agregam mais valor depois |

## Design Artifacts Summary

| Artifact | Path | Status |
|----------|------|--------|
| Research | [research.md](./research.md) | ✅ Complete |
| Data Model | [data-model.md](./data-model.md) | ✅ Complete |
| API Contract | [contracts/api-client.md](./contracts/api-client.md) | ✅ Complete |
| Hooks Contract | [contracts/hooks.md](./contracts/hooks.md) | ✅ Complete |
| Quickstart | [quickstart.md](./quickstart.md) | ✅ Complete |

## Backend Dependency

**NOTA**: O endpoint `GET /api/experiments/{id}/explorations` precisa ser adicionado ao backend para listar exploracoes de um experimento. Ver [contracts/api-client.md](./contracts/api-client.md) para sugestao de implementacao.
