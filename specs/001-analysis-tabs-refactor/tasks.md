# Tasks: Analysis Tabs Refactor

**Input**: Design documents from `/specs/001-analysis-tabs-refactor/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/api.md, quickstart.md

**Tests**: Following TDD/BDD approach as specified in Constitution

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

---

## ⚠️ PHASE 1 AUDIT RESULTS (CRITICAL - READ FIRST)

**Current Phase Structure** (6 phases - see AnalysisPhaseTabs.tsx):
1. **visao-geral** → "Geral" (PhaseOverview.tsx)
2. **localizacao** → "Influência" (PhaseLocation.tsx) ← Contains AttributeCorrelationSection
3. **segmentacao** → "Segmentos" (PhaseSegmentation.tsx)
4. **casos-especiais** → "Especiais" (PhaseEdgeCases.tsx)
5. **aprofundamento** → "Deep Dive" (PhaseExplainability.tsx) ← Contains SHAP+PDP
6. **insights** → "Insights" (PhaseInsights.tsx)

**FILE NAME CORRECTIONS** (Spec assumed wrong names):
- ❌ Spec said "PhaseDeepDive.tsx" → ✅ ACTUAL: "PhaseExplainability.tsx"
- ❌ Spec said "PhaseInfluence.tsx" → ✅ ACTUAL: "PhaseLocation.tsx" (id: 'localizacao')
- ❌ Spec said "PhaseSpecial.tsx" → ✅ ACTUAL: "PhaseEdgeCases.tsx" (id: 'casos-especiais')

**CHARTS AUDIT**:
- ✅ AttributeCorrelationChart.tsx EXISTS (used by PhaseLocation)
- ❌ AttributeImportanceChart.tsx DOES NOT EXIST
- ✅ ShapSummarySection EXISTS (in PhaseExplainability)
- ✅ PDPSection EXISTS (in PhaseExplainability)
- ✅ ShapWaterfallSection EXISTS (in PhaseExplainability)

**ENDPOINTS AUDIT**:
- ✅ `attribute-correlation` endpoint EXISTS (used by PhaseLocation)
- ⚠️ `attribute-importance` endpoint NOT FOUND (may not exist)

**REFACTOR MAPPING** (What needs to move):
- **FROM PhaseExplainability (Deep Dive)** → **TO PhaseLocation (Influência)**:
  - ShapSummarySection
  - PDPSection

- **FROM PhaseLocation (Influência)** → **DELETE**:
  - AttributeCorrelationSection
  - ScatterSection (check if should be deleted)

- **FROM PhaseExplainability (Deep Dive)** → **TO PhaseEdgeCases (Especiais)**:
  - ShapWaterfallSection (remove dropdown, add click-to-explain)

**NAVIGATION CHANGES**:
- Remove "aprofundamento" phase (Deep Dive / PhaseExplainability.tsx)
- Update "6 fases" → "5 fases" in AnalysisPhaseTabs.tsx (line 171)
- Delete PhaseExplainability from ExperimentDetail.tsx and ANALYSIS_PHASES array

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US5)
- Include exact file paths in descriptions

## Implementation Strategy

**Complete Feature Delivery**: Implementar todas as user stories em sequência

**User Stories** (em ordem de implementação):
- US5 (P1): Navegação com 5 fases (remove Deep Dive)
- US1 (P1): Visualizar Influência (move SHAP/PDP)
- US2 (P1): Click-to-explain em Casos Extremos
- US3 (P2): Auto-interview creation
- US4 (P2): Simplificar Outliers

**Commit Strategy**: 1 commit ao final de cada Phase (9 commits no total)

---

## Phase 1: Setup & Code Audit

**Purpose**: Understand existing codebase and prepare for refactor

- [ ] T001 Audit existing code to identify files using attribute-importance and attribute-correlation endpoints in frontend/src/
- [ ] T002 Audit existing code to identify backend services/endpoints for attribute-importance and attribute-correlation in src/synth_lab/api/
- [ ] T003 [P] Document current usage of PhaseDeepDive.tsx and its references in frontend/src/components/experiments/results/
- [ ] T004 [P] Identify all imports/usages of AttributeImportanceChart and AttributeCorrelationChart in frontend/src/

**Checkpoint**: Code audit complete - safe removal targets identified

---

## Phase 2: Foundational (Backend Preparation)

**Purpose**: Prepare backend for auto-interview feature (needed by US3)

**⚠️ NOTE**: This can be done in parallel with frontend refactors (US1, US2, US5)

- [ ] T005 [P] Add get_extreme_cases() method to SynthRepository in src/synth_lab/repositories/synth_repository.py
- [ ] T006 [P] Add TypeScript types for AutoInterviewRequest and AutoInterviewResponse in frontend/src/types/experiment.ts

**Checkpoint**: Backend repository ready for auto-interview logic

---

## Phase 3: User Story 5 - Navegação Simplificada (Priority: P1)

**Goal**: Remove aba "Deep Dive" e atualizar indicador para "5 fases"

**Independent Test**: Usuário vê exatamente 5 abas e indicador mostra "5 fases de investigação"

### Implementation for US5

- [ ] T007 [US5] Delete frontend/src/components/experiments/results/PhaseDeepDive.tsx
- [ ] T008 [US5] Remove PhaseDeepDive import and route from frontend/src/pages/ExperimentDetail.tsx (or equivalent)
- [ ] T009 [US5] Update phase indicator text from "6 fases" to "5 fases" in frontend/src/pages/ExperimentDetail.tsx
- [ ] T010 [US5] Verify navigation only shows 5 tabs: Geral, Influência, Segmentos, Especiais, Insights

**Checkpoint**: US5 complete - Navigation shows exactly 5 phases

---

## Phase 4: User Story 1 - Visualizar Influência (Priority: P1)

**Goal**: Mover SHAP Summary e PDP para aba Influência, remover gráficos antigos

**Independent Test**: Usuário clica em "Influência" e vê SHAP Summary + PDP (não vê Attribute Importance/Correlation)

### Implementation for US1

- [ ] T011 [P] [US1] Move ShapSummarySection import from PhaseDeepDive (or current location) to PhaseInfluence in frontend/src/components/experiments/results/PhaseInfluence.tsx
- [ ] T012 [P] [US1] Move PDPSection import from PhaseDeepDive (or current location) to PhaseInfluence in frontend/src/components/experiments/results/PhaseInfluence.tsx
- [ ] T013 [US1] Add ShapSummarySection and PDPSection to PhaseInfluence component JSX in frontend/src/components/experiments/results/PhaseInfluence.tsx
- [ ] T014 [US1] Remove AttributeImportanceSection from PhaseInfluence component in frontend/src/components/experiments/results/PhaseInfluence.tsx
- [ ] T015 [US1] Remove AttributeCorrelationSection from PhaseInfluence component in frontend/src/components/experiments/results/PhaseInfluence.tsx
- [ ] T016 [US1] Delete frontend/src/components/experiments/results/charts/AttributeImportanceChart.tsx (if not used elsewhere per T001)
- [ ] T017 [US1] Delete frontend/src/components/experiments/results/charts/AttributeCorrelationChart.tsx (if not used elsewhere per T001)
- [ ] T018 [US1] Remove unused imports and update component structure in PhaseInfluence.tsx
- [ ] T019 [US1] Test: Verify aba Influência shows SHAP Summary and PDP charts loading correctly

**Checkpoint**: US1 complete - Influência tab shows correct charts

---

## Phase 5: User Story 2 - Click-to-Explain (Priority: P1)

**Goal**: Adicionar click-to-explain em casos extremos, mover SHAP Waterfall para aba Especiais

**Independent Test**: Usuário clica em card de caso extremo e vê SHAP Waterfall logo abaixo

### Implementation for US2

- [ ] T020 [P] [US2] Add useState for selectedSynthId in frontend/src/components/experiments/results/PhaseSpecial.tsx
- [ ] T021 [P] [US2] Add click handler function handleSynthClick(synthId: string) in PhaseSpecial.tsx
- [ ] T022 [US2] Modify ExtremeCasesSection to receive onClick prop in frontend/src/components/experiments/results/ExtremeCasesSection.tsx
- [ ] T023 [US2] Remove "Perguntas Sugeridas" section from ExtremeCasesSection.tsx
- [ ] T024 [US2] Remove "Casos Inesperados" column from ExtremeCasesSection.tsx
- [ ] T025 [US2] Add onClick={handleSynthClick} to each extreme case card in ExtremeCasesSection.tsx
- [ ] T026 [US2] Move SHAPWaterfallSection import to PhaseSpecial.tsx (if not already there)
- [ ] T027 [US2] Add SHAPWaterfallSection below ExtremeCasesSection in PhaseSpecial.tsx
- [ ] T028 [US2] Modify SHAPWaterfallSection to receive selectedSynthId via props (remove dropdown) in frontend/src/components/experiments/results/SHAPWaterfallSection.tsx
- [ ] T029 [US2] Remove dropdown "Selecione um synth" from SHAPWaterfallSection.tsx
- [ ] T030 [US2] Add conditional rendering: only show SHAP Waterfall if selectedSynthId is not null
- [ ] T031 [US2] Add loading state when switching between synths in SHAPWaterfallSection.tsx
- [ ] T032 [US2] Test: Click on extreme case card and verify SHAP Waterfall updates

**Checkpoint**: US2 complete - Click-to-explain works for extreme cases

---

## Phase 6: Backend Cleanup (Post US1/US2/US5)

**Purpose**: Remove unused backend code after frontend refactor is complete

**⚠️ Dependencies**: Must complete US1 first to ensure frontend no longer uses these endpoints

- [ ] T033 Verify attribute-importance endpoint is not used (grep codebase per T001 results)
- [ ] T034 Verify attribute-correlation endpoint is not used (grep codebase per T001 results)
- [ ] T035 Remove GET /analysis/charts/attribute-importance endpoint from src/synth_lab/api/routers/analysis.py (if T033 confirms not used)
- [ ] T036 Remove GET /analysis/charts/attribute-correlation endpoint from src/synth_lab/api/routers/analysis.py (if T034 confirms not used)
- [ ] T037 [P] Remove attribute-importance service method from src/synth_lab/services/explainability_service.py (if only used by removed endpoints)
- [ ] T038 [P] Remove attribute-correlation service method from src/synth_lab/services/explainability_service.py (if only used by removed endpoints)
- [ ] T039 Test: Run backend tests to ensure no regressions from removals

**Checkpoint**: Backend cleanup complete - unused code removed

---

## Phase 7: User Story 3 - Auto-Interview (Priority: P2)

**Goal**: Adicionar botão para criar entrevista automática com casos extremos

**Independent Test**: Usuário clica em "Entrevistar Casos Extremos" e recebe link para entrevista criada

**⚠️ Dependencies**: Requires T005 (get_extreme_cases repository method)

### Backend for US3

- [ ] T040 [P] [US3] Write failing test for create_auto_interview() in tests/unit/test_interview_service.py
- [ ] T041 [US3] Implement create_auto_interview() in src/synth_lab/services/interview_service.py
- [ ] T042 [US3] Add POST /experiments/{id}/interviews/auto endpoint in src/synth_lab/api/routers/experiments.py (or analysis.py)
- [ ] T043 [US3] Test endpoint returns 201 with interview_id in tests/integration/test_analysis_api.py
- [ ] T044 [US3] Test endpoint returns 400 if less than 10 synths available
- [ ] T045 [US3] Test endpoint returns 404 if experiment not found

### Frontend for US3

- [ ] T046 [P] [US3] Create AutoInterviewButton component in frontend/src/components/experiments/results/AutoInterviewButton.tsx
- [ ] T047 [P] [US3] Add createAutoInterview() to frontend/src/services/experiments-api.ts
- [ ] T048 [P] [US3] Add useCreateAutoInterview() hook in frontend/src/hooks/use-experiments.ts
- [ ] T049 [US3] Add AutoInterviewButton to PhaseSpecial below ExtremeCasesSection in PhaseSpecial.tsx
- [ ] T050 [US3] Implement loading state in AutoInterviewButton.tsx during interview creation
- [ ] T051 [US3] Show link "Ver Entrevista" after successful creation in AutoInterviewButton.tsx
- [ ] T052 [US3] Show error toast if creation fails in AutoInterviewButton.tsx
- [ ] T053 [US3] Test: Click button, verify loading, verify link appears with correct interview ID

**Checkpoint**: US3 complete - Auto-interview creation works

---

## Phase 8: User Story 4 - Simplificar Outliers (Priority: P2)

**Goal**: Simplificar UI de outliers e adicionar click-to-explain

**Independent Test**: Usuário ajusta slider, clica em outlier, vê SHAP Waterfall

### Implementation for US4

- [ ] T054 [P] [US4] Rename slider label to "Sensibilidade de Detecção" in frontend/src/components/experiments/results/OutliersSection.tsx
- [ ] T055 [P] [US4] Remove anomaly bar from outlier cards in OutliersSection.tsx
- [ ] T056 [P] [US4] Remove or clarify orange number at top of outlier cards in OutliersSection.tsx
- [ ] T057 [P] [US4] Remove "Perfil Atípico" tag/chip from outlier cards in OutliersSection.tsx
- [ ] T058 [US4] Add onClick handler to outlier cards (reuse handleSynthClick from US2) in PhaseSpecial.tsx
- [ ] T059 [US4] Connect outlier card clicks to SHAPWaterfallSection (already added in US2)
- [ ] T060 [US4] Test: Adjust slider, verify outliers update dynamically
- [ ] T061 [US4] Test: Click outlier card, verify SHAP Waterfall appears

**Checkpoint**: US4 complete - Outliers simplified with click-to-explain

---

## Phase 9: Polish & Testing

**Purpose**: Cross-cutting concerns and final validation

- [ ] T062 [P] Add empty state for PhaseInfluence if SHAP/PDP data not available
- [ ] T063 [P] Add empty state for OutliersSection if no outliers detected at current sensitivity
- [ ] T064 [P] Add debounce to prevent rapid clicks on extreme case/outlier cards
- [ ] T065 [P] Cancel previous SHAP Waterfall request when user clicks different card
- [ ] T066 Run full test suite (backend + frontend) and verify all tests pass
- [ ] T067 Manual test: Complete user journey through all 5 phases
- [ ] T068 Performance test: Verify SHAP/PDP load in < 2s, SHAP Waterfall in < 3s
- [ ] T069 [P] Update documentation if needed (quickstart.md already created)
- [ ] T070 Final commit: Refactor complete

**Checkpoint**: Feature complete and tested

---

## Dependency Graph

```
Phase 1 (Setup) → Phase 2 (Foundational) → Phases 3-5 can run in PARALLEL
                                                ↓
Phase 3 (US5 - Remove Deep Dive)               |
Phase 4 (US1 - Move SHAP/PDP)                  |
Phase 5 (US2 - Click-to-Explain)               |
                                                ↓
                                         Phase 6 (Backend Cleanup)
                                                ↓
                                         Phase 7 (US3 - Auto-Interview) *
                                         Phase 8 (US4 - Simplify Outliers)
                                                ↓
                                         Phase 9 (Polish)

* Phase 7 depends on Phase 2 (foundational)
```

**Critical Path**: Phase 1 → Phase 2 → (US1, US2, US5 in parallel) → Phase 6 → Phase 7 → Phase 9

**Parallel Opportunities**:
- US1, US2, US5 are INDEPENDENT and can be done in parallel
- US3 and US4 are INDEPENDENT and can be done in parallel
- Backend cleanup (Phase 6) only depends on US1 completion

---

## Execution Recommendations

### Implementation Strategy

**Complete Feature**: Implementar todas as fases em sequência, sem MVP intermediário.

**Commit Strategy**:
- **1 commit ao final de cada Phase** (9 commits no total)
- Cada commit deve incluir todos os tasks da fase completos
- Mensagens de commit devem referenciar a Phase (ex: "feat: Phase 3 - Remove Deep Dive tab")

### Sequential Execution with Parallel Tasks

Execute as fases em ordem, mas dentro de cada fase, execute tasks [P] em paralelo quando possível:

**Phase 1** (Setup):
- Execute T001-T004 em paralelo → **Commit 1**: "chore: Phase 1 - Code audit complete"

**Phase 2** (Foundational):
- Execute T005-T006 em paralelo → **Commit 2**: "feat: Phase 2 - Backend preparation"

**Phases 3-5** (US5/US1/US2 - podem ser executadas em paralelo):
- Execute todas as 3 fases simultaneamente
- **Commit 3**: "feat: Phase 3 - Remove Deep Dive tab (US5)"
- **Commit 4**: "feat: Phase 4 - Move SHAP/PDP to Influência (US1)"
- **Commit 5**: "feat: Phase 5 - Add click-to-explain for extreme cases (US2)"

**Phase 6** (Backend Cleanup):
- Execute T033-T039 → **Commit 6**: "refactor: Phase 6 - Remove unused backend code"

**Phase 7** (US3 - Auto-interview):
- Execute T040-T053 → **Commit 7**: "feat: Phase 7 - Add auto-interview creation (US3)"

**Phase 8** (US4 - Outliers):
- Execute T054-T061 → **Commit 8**: "feat: Phase 8 - Simplify outliers UI (US4)"

**Phase 9** (Polish):
- Execute T062-T070 → **Commit 9**: "polish: Phase 9 - Final testing and polish"

---

## Summary

**Total Tasks**: 70
- Phase 1 (Setup): 4 tasks
- Phase 2 (Foundational): 2 tasks
- Phase 3 (US5): 4 tasks
- Phase 4 (US1): 9 tasks
- Phase 5 (US2): 13 tasks
- Phase 6 (Backend Cleanup): 7 tasks
- Phase 7 (US3): 14 tasks
- Phase 8 (US4): 8 tasks
- Phase 9 (Polish): 9 tasks

**Parallel Opportunities**: ~40% of tasks marked [P] can run in parallel

**Commit Strategy**: 9 commits (1 per Phase)

**Implementation**: Complete feature delivery - todas as fases devem ser implementadas em sequência
