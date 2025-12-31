# Tasks: Frontend para Exploracao de Cenarios com Visualizacao de Arvore

**Input**: Design documents from `/specs/025-exploration-frontend/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: TDD relaxado para frontend visual - testes serao adicionados apos estabilizacao dos componentes.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Frontend**: `frontend/src/` (React TypeScript)
- Types: `frontend/src/types/`
- Services: `frontend/src/services/`
- Hooks: `frontend/src/hooks/`
- Components: `frontend/src/components/exploration/`
- Pages: `frontend/src/pages/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Instalar dependencias e criar estrutura base

- [ ] T001 Install react-d3-tree dependency: `cd frontend && npm install react-d3-tree`
- [ ] T002 [P] Create exploration types in `frontend/src/types/exploration.ts` (copy from data-model.md)
- [ ] T003 [P] Add exploration query keys to `frontend/src/lib/query-keys.ts`
- [ ] T004 [P] Create exploration API service in `frontend/src/services/exploration-api.ts`
- [ ] T005 Create exploration hooks in `frontend/src/hooks/use-exploration.ts`

**Checkpoint**: Foundation ready - types, services, and hooks available for components

---

## Phase 2: Foundational (Backend Dependency)

**Purpose**: Adicionar endpoint necessario no backend

**⚠️ CRITICAL**: O endpoint de listagem e necessario para US6, mas as outras stories podem ser desenvolvidas sem ele

- [ ] T006 Add backend endpoint GET /api/experiments/{id}/explorations in `src/synth_lab/api/routers/experiment.py`
- [ ] T007 Add ExplorationSummary schema in `src/synth_lab/api/schemas/exploration.py`
- [ ] T008 Add repository method get_by_experiment in `src/synth_lab/repositories/exploration_repository.py`

**Checkpoint**: Backend endpoint disponivel para lista de exploracoes

---

## Phase 3: User Story 1 - Iniciar Nova Exploracao (Priority: P1) 🎯 MVP

**Goal**: PM consegue iniciar uma nova exploracao a partir da pagina de experimento

**Independent Test**: Acessar experimento com analise baseline, clicar "Iniciar Exploracao", preencher meta 40%, verificar que exploracao e criada

### Implementation for User Story 1

- [ ] T009 [P] [US1] Create NewExplorationDialog component in `frontend/src/components/exploration/NewExplorationDialog.tsx`
- [ ] T010 [P] [US1] Create NewExplorationForm component with Zod validation in `frontend/src/components/exploration/NewExplorationForm.tsx`
- [ ] T011 [US1] Create ExplorationSection component for experiment page in `frontend/src/components/experiments/ExplorationSection.tsx`
- [ ] T012 [US1] Integrate ExplorationSection into ExperimentDetail page in `frontend/src/pages/ExperimentDetail.tsx`
- [ ] T013 [US1] Add button disabled state when no baseline analysis exists

**Checkpoint**: US1 complete - PM pode iniciar exploracao a partir do experimento

---

## Phase 4: User Story 2 - Visualizar Arvore de Cenarios (Priority: P1) 🎯 MVP

**Goal**: PM ve arvore hierarquica com nos coloridos por status

**Independent Test**: Acessar exploracao concluida, verificar arvore renderiza com cores corretas e conexoes visiveis

### Implementation for User Story 2

- [ ] T014 [P] [US2] Create tree data transformation utility in `frontend/src/lib/exploration-utils.ts`
- [ ] T015 [P] [US2] Create CustomTreeNode component for react-d3-tree in `frontend/src/components/exploration/CustomTreeNode.tsx`
- [ ] T016 [US2] Create ExplorationTree component with zoom/pan in `frontend/src/components/exploration/ExplorationTree.tsx`
- [ ] T017 [US2] Create ExplorationDetail page structure in `frontend/src/pages/ExplorationDetail.tsx`
- [ ] T018 [US2] Add route /experiments/:id/explorations/:explorationId to `frontend/src/App.tsx`
- [ ] T019 [US2] Implement node status color mapping (green=winner, blue=active, gray=dominated, red=failed)

**Checkpoint**: US2 complete - Arvore renderiza com cores e navegacao zoom/pan

---

## Phase 5: User Story 3 - Inspecionar Detalhes de um No (Priority: P1) 🎯 MVP

**Goal**: PM clica em no e ve detalhes no painel lateral

**Independent Test**: Clicar em no da arvore, verificar painel lateral exibe acao, categoria, rationale, parametros e resultados

### Implementation for User Story 3

- [ ] T020 [P] [US3] Create NodeDetailsPanel component (Sheet lateral) in `frontend/src/components/exploration/NodeDetailsPanel.tsx`
- [ ] T021 [P] [US3] Create ScorecardParamsDisplay sub-component in `frontend/src/components/exploration/ScorecardParamsDisplay.tsx`
- [ ] T022 [P] [US3] Create SimulationResultsDisplay sub-component in `frontend/src/components/exploration/SimulationResultsDisplay.tsx`
- [ ] T023 [US3] Integrate NodeDetailsPanel with ExplorationTree (onNodeClick handler)
- [ ] T024 [US3] Add delta calculation display (comparison with parent node)
- [ ] T025 [US3] Handle root node special case ("Cenario Inicial (Baseline)")

**Checkpoint**: US3 complete - Detalhes de nos acessiveis via clique

---

## Phase 6: User Story 4 - Visualizar Caminho Vencedor (Priority: P2)

**Goal**: PM ve caminho destacado do raiz ate no vencedor

**Independent Test**: Em exploracao com status "goal_achieved", verificar caminho destacado e lista de passos

### Implementation for User Story 4

- [ ] T026 [P] [US4] Create WinningPathPanel component in `frontend/src/components/exploration/WinningPathPanel.tsx`
- [ ] T027 [P] [US4] Create PathStepCard sub-component in `frontend/src/components/exploration/PathStepCard.tsx`
- [ ] T028 [US4] Add winning path highlight logic to ExplorationTree (edges and nodes)
- [ ] T029 [US4] Integrate WinningPathPanel with ExplorationDetail page
- [ ] T030 [US4] Implement "click step to select node" interaction

**Checkpoint**: US4 complete - Caminho vencedor visivel e interativo

---

## Phase 7: User Story 5 - Acompanhar Progresso da Exploracao (Priority: P2)

**Goal**: PM ve progresso em tempo real durante execucao

**Independent Test**: Iniciar exploracao, verificar indicadores atualizam automaticamente sem refresh

### Implementation for User Story 5

- [ ] T031 [P] [US5] Create ExplorationProgress component in `frontend/src/components/exploration/ExplorationProgress.tsx`
- [ ] T032 [P] [US5] Create ExplorationStatusBadge component in `frontend/src/components/exploration/ExplorationStatusBadge.tsx`
- [ ] T033 [US5] Integrate ExplorationProgress with ExplorationDetail page
- [ ] T034 [US5] Add toast notification when exploration completes (onSuccess from polling)
- [ ] T035 [US5] Configure polling intervals (3s status, 5s tree) in hooks

**Checkpoint**: US5 complete - Progresso atualiza em tempo real

---

## Phase 8: User Story 6 - Listar Exploracoes do Experimento (Priority: P2)

**Goal**: PM ve historico de exploracoes com status e resultados

**Independent Test**: Acessar experimento com multiplas exploracoes, verificar lista com todas ordenadas por data

### Implementation for User Story 6

- [ ] T036 [P] [US6] Create ExplorationList component in `frontend/src/components/exploration/ExplorationList.tsx`
- [ ] T037 [P] [US6] Create ExplorationListItem sub-component in `frontend/src/components/exploration/ExplorationListItem.tsx`
- [ ] T038 [US6] Integrate ExplorationList with ExplorationSection in experiment page
- [ ] T039 [US6] Add navigation to exploration detail on item click
- [ ] T040 [US6] Add "running" indicator animation for active explorations

**Checkpoint**: US6 complete - Lista de exploracoes funcional

---

## Phase 9: User Story 7 - Consultar Catalogo de Acoes (Priority: P3)

**Goal**: PM consulta catalogo de categorias de acoes

**Independent Test**: Clicar "Ver Catalogo de Acoes", verificar modal lista 5 categorias com exemplos

### Implementation for User Story 7

- [ ] T041 [P] [US7] Create ActionCatalogDialog component in `frontend/src/components/exploration/ActionCatalogDialog.tsx`
- [ ] T042 [P] [US7] Create CategoryCard sub-component in `frontend/src/components/exploration/CategoryCard.tsx`
- [ ] T043 [P] [US7] Create ImpactRangeDisplay sub-component in `frontend/src/components/exploration/ImpactRangeDisplay.tsx`
- [ ] T044 [US7] Integrate ActionCatalogDialog with ExplorationDetail page
- [ ] T045 [US7] Add search/filter functionality for categories

**Checkpoint**: US7 complete - Catalogo de acoes acessivel

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Melhorias finais e edge cases

- [ ] T046 [P] Add loading skeletons for all components
- [ ] T047 [P] Add error states and retry buttons
- [ ] T048 Handle edge case: experiment without baseline (disabled button with tooltip)
- [ ] T049 Handle edge case: large trees (>100 nodes) with performance optimization
- [ ] T050 Handle edge case: long rationale text (truncate with "ver mais")
- [ ] T051 [P] Add responsive design for mobile (Sheet bottom drawer)
- [ ] T052 Run quickstart.md validation scenarios
- [ ] T053 Code cleanup and component documentation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Backend work - can be done in parallel with frontend setup
- **User Stories (Phase 3-9)**: All depend on Phase 1 completion
  - US1, US2, US3 are P1 - implement in order for MVP
  - US4, US5, US6 are P2 - can be parallelized after US1-3
  - US7 is P3 - lowest priority
- **Polish (Phase 10)**: After all user stories complete

### User Story Dependencies

- **US1 (Iniciar Exploracao)**: No dependencies - entry point
- **US2 (Visualizar Arvore)**: Can start after Phase 1 - needs ExplorationDetail page
- **US3 (Detalhes do No)**: Depends on US2 (needs tree component for click handling)
- **US4 (Caminho Vencedor)**: Depends on US2 (needs tree to highlight path)
- **US5 (Progresso)**: Can start after Phase 1 - independent
- **US6 (Lista Exploracoes)**: Depends on Phase 2 (backend endpoint) and US1
- **US7 (Catalogo)**: No dependencies - can be done anytime after Phase 1

### Within Each User Story

- Types and utilities before components
- Pure components before integrated components
- Core functionality before edge case handling

### Parallel Opportunities

Within Phase 1 (Setup):
```bash
# All can run in parallel:
Task T002: Create exploration types
Task T003: Add query keys
Task T004: Create API service
```

Within User Story 3 (Node Details):
```bash
# All can run in parallel:
Task T020: Create NodeDetailsPanel
Task T021: Create ScorecardParamsDisplay
Task T022: Create SimulationResultsDisplay
```

---

## Implementation Strategy

### MVP First (US1 + US2 + US3)

1. Complete Phase 1: Setup
2. Complete Phase 3: US1 - Iniciar Exploracao
3. Complete Phase 4: US2 - Visualizar Arvore
4. Complete Phase 5: US3 - Detalhes do No
5. **STOP and VALIDATE**: Test MVP flow end-to-end
6. Deploy/demo if ready

### Incremental Delivery

1. **MVP (US1-3)**: PM pode iniciar exploracao, ver arvore, inspecionar nos
2. **+US4 (Caminho Vencedor)**: Destaque visual do resultado
3. **+US5 (Progresso)**: Feedback em tempo real
4. **+US6 (Lista)**: Historico de exploracoes
5. **+US7 (Catalogo)**: Referencia informativa

### Task Count Summary

| Phase | User Story | Task Count |
|-------|------------|------------|
| 1 | Setup | 5 |
| 2 | Foundational | 3 |
| 3 | US1 - Iniciar Exploracao | 5 |
| 4 | US2 - Visualizar Arvore | 6 |
| 5 | US3 - Detalhes do No | 6 |
| 6 | US4 - Caminho Vencedor | 5 |
| 7 | US5 - Progresso | 5 |
| 8 | US6 - Lista Exploracoes | 5 |
| 9 | US7 - Catalogo | 5 |
| 10 | Polish | 8 |
| **Total** | | **53** |

---

## Notes

- [P] tasks = different files, no dependencies, can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- MVP = US1 + US2 + US3 (17 tasks after setup)
