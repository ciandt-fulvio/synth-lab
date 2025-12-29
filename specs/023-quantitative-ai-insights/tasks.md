# Tasks: AI-Generated Insights for Quantitative Analysis

**Input**: Design documents from `/specs/023-quantitative-ai-insights/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Included per Constitution Principle I (TDD/BDD). Tests written BEFORE implementation.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

---

## 📊 Progress Summary

**Last Updated**: 2025-12-29

### Completed Phases

- ✅ **Phase 1: Setup** (T001-T003) - 3/3 tasks complete
  - Feature branch created
  - REASONING_MODEL constant added to config
  - CacheKeys enum extended with 8 new insight keys

- ✅ **Phase 2: Foundational** (T004-T013) - 10/10 tasks complete
  - ChartInsight and ExecutiveSummary entities created with validation
  - AnalysisCacheRepository extended with insight methods
  - Frontend TypeScript types and query keys added
  - Old feature 017 insight service temporarily disabled
  - All 484 tests passing

### In Progress

- 🔄 **Phase 3: User Story 3 - Backend Infrastructure** (T014-T041) - 0/28 tasks
  - Next: Create unit tests for entities and services
  - Then: Implement InsightService and ExecutiveSummaryService
  - Then: Hook into analysis workflow for automatic generation

### Total Progress: 13/107 tasks (12%)

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Backend: `src/synth_lab/`
- Frontend: `frontend/src/`
- Tests: `tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and configuration

- [x] T001 Create feature branch `023-quantitative-ai-insights` from main
- [x] T002 Add REASONING_MODEL constant in src/synth_lab/infrastructure/config.py (value: "o1-mini")
- [x] T003 [P] Extend CacheKeys enum in src/synth_lab/repositories/analysis_repository.py with insight cache keys

**Checkpoint**: Configuration ready for development

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core entities and repository methods that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 [P] Create ChartInsight entity in src/synth_lab/domain/entities/chart_insight.py
- [x] T005 [P] Create ExecutiveSummary entity in src/synth_lab/domain/entities/executive_summary.py
- [x] T006 [P] Update __init__.py in src/synth_lab/domain/entities/ to export new entities
- [x] T007 Add store_chart_insight() method to AnalysisCacheRepository in src/synth_lab/repositories/analysis_cache_repository.py
- [x] T008 Add get_chart_insight() method to AnalysisCacheRepository in src/synth_lab/repositories/analysis_cache_repository.py
- [x] T009 Add get_all_chart_insights() method to AnalysisCacheRepository in src/synth_lab/repositories/analysis_cache_repository.py
- [x] T010 Add store_executive_summary() method to AnalysisCacheRepository in src/synth_lab/repositories/analysis_cache_repository.py
- [x] T011 Add get_executive_summary() method to AnalysisCacheRepository in src/synth_lab/repositories/analysis_cache_repository.py
- [x] T012 [P] Create TypeScript types in frontend/src/types/insights.ts (ChartInsight, ExecutiveSummary, ChartTypeWithInsight)
- [x] T013 Add insight query keys to frontend/src/lib/query-keys.ts

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 3 - Automatic Insight Generation Workflow

**Goal**: Implement backend infrastructure to automatically generate insights in background after chart data is cached

**Independent Test**: Run simulation → Monitor logs → Verify insights generated automatically within 2 minutes → Verify parallel execution for all 7 chart types

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T014 [P] [US3] Unit test for ChartInsight entity in tests/unit/domain/entities/test_chart_insight.py (validate structure, JSON serialization)
- [ ] T015 [P] [US3] Unit test for ExecutiveSummary entity in tests/unit/domain/entities/test_executive_summary.py (validate structure, JSON serialization)
- [ ] T016 [P] [US3] Unit test for InsightService._build_prompt_try_vs_success() in tests/unit/services/test_insight_service.py (mocked LLM)
- [ ] T017 [P] [US3] Unit test for InsightService._parse_insight_response() in tests/unit/services/test_insight_service.py
- [ ] T018 [P] [US3] Unit test for ExecutiveSummaryService.generate_summary() in tests/unit/services/test_executive_summary_service.py (mocked LLM)
- [ ] T019 [P] [US3] Integration test for repository insight methods in tests/integration/repositories/test_analysis_repository_insights.py
- [ ] T020 [US3] Integration test for automatic trigger workflow in tests/integration/services/test_insight_workflow.py (verify parallel execution)

### Implementation for User Story 3

- [ ] T021 [P] [US3] Create InsightService class skeleton in src/synth_lab/services/insight_service.py (init, logger, tracer)
- [ ] T022 [P] [US3] Create ExecutiveSummaryService class skeleton in src/synth_lab/services/executive_summary_service.py
- [ ] T023 [US3] Implement InsightService._build_prompt_try_vs_success() for Try vs Success chart
- [ ] T024 [US3] Implement InsightService._build_prompt_shap_summary() for SHAP Summary chart
- [ ] T025 [US3] Implement InsightService._build_prompt_pdp() for PDP chart
- [ ] T026 [US3] Implement InsightService._build_prompt_pca_scatter() for PCA Scatter chart
- [ ] T027 [US3] Implement InsightService._build_prompt_radar_comparison() for Radar Comparison chart
- [ ] T028 [US3] Implement InsightService._build_prompt_extreme_cases() for Extreme Cases chart
- [ ] T029 [US3] Implement InsightService._build_prompt_outliers() for Outliers chart
- [ ] T030 [US3] Implement InsightService._parse_insight_response() to parse LLM JSON response into ChartInsight
- [ ] T031 [US3] Implement InsightService.generate_insight() main method (read chart data, build prompt, call LLM with o1-mini, parse, store)
- [ ] T032 [US3] Add Phoenix tracing to InsightService.generate_insight() with span per chart type
- [ ] T033 [US3] Implement ExecutiveSummaryService._build_synthesis_prompt() to combine all insights
- [ ] T034 [US3] Implement ExecutiveSummaryService.generate_summary() (read all insights, build prompt, call LLM, parse, store)
- [ ] T035 [US3] Add Phoenix tracing to ExecutiveSummaryService.generate_summary()
- [ ] T036 [US3] Add error handling to InsightService with retry logic (catch LLM errors, mark as failed, continue)
- [ ] T037 [US3] Add error handling to ExecutiveSummaryService (handle partial insights, < 3 charts)
- [ ] T038 [US3] Implement _trigger_insight_generation() in src/synth_lab/services/simulation/analysis_service.py
- [ ] T039 [US3] Implement _generate_insights_parallel() async method in analysis_service.py (parallel asyncio tasks for 7 charts)
- [ ] T040 [US3] Hook _trigger_insight_generation() into _pre_compute_cache() in analysis_service.py (daemon thread pattern)
- [ ] T041 [US3] Add logging for insight generation start/completion in analysis_service.py

**Checkpoint**: Backend automatically generates insights after analysis completes. Verify with manual simulation run.

---

## Phase 4: User Story 1 - View Individual Chart Insights

**Goal**: Display AI-generated insights directly within each chart card with collapsible sections

**Independent Test**: Run simulation → Navigate to Try vs Success chart → Verify "Insights de IA" section appears → Expand section → Verify all insight fields displayed (problem understanding, trends, findings, summary)

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T042 [P] [US1] Contract test for GET /experiments/{id}/insights/{chart_type} in tests/contract/test_insights_contracts.py
- [ ] T043 [P] [US1] Integration test for GET /experiments/{id}/insights/try_vs_success in tests/integration/api/test_insights_router.py
- [ ] T044 [P] [US1] Integration test for GET /experiments/{id}/insights (all insights) in tests/integration/api/test_insights_router.py
- [ ] T045 [P] [US1] Frontend unit test for useChartInsight hook in frontend/src/hooks/__tests__/use-chart-insight.test.ts
- [ ] T046 [P] [US1] Frontend component test for InsightSection in frontend/src/components/experiments/results/__tests__/InsightSection.test.tsx

### Implementation for User Story 1

#### Backend API

- [ ] T047 [P] [US1] Create insights router in src/synth_lab/api/routers/insights.py (FastAPI router setup)
- [ ] T048 [US1] Implement GET /experiments/{id}/insights/{chart_type} endpoint in insights.py
- [ ] T049 [US1] Implement GET /experiments/{id}/insights endpoint (all insights with stats) in insights.py
- [ ] T050 [US1] Add error handling for invalid chart_type in insights.py (400 Bad Request)
- [ ] T051 [US1] Add 404 handling for missing insights in insights.py
- [ ] T052 [US1] Register insights router in src/synth_lab/api/main.py

#### Frontend API Client

- [ ] T053 [P] [US1] Create insights-api.ts service in frontend/src/services/insights-api.ts
- [ ] T054 [US1] Implement getChartInsight() function in insights-api.ts
- [ ] T055 [US1] Implement getAllChartInsights() function in insights-api.ts

#### Frontend Hooks

- [ ] T056 [P] [US1] Create useChartInsight hook in frontend/src/hooks/use-chart-insight.ts
- [ ] T057 [US1] Add auto-refresh logic to useChartInsight (every 10s if status="pending")
- [ ] T058 [US1] Add staleTime caching (5 minutes for completed insights) to useChartInsight

#### Frontend Components

- [ ] T059 [P] [US1] Create InsightSection component in frontend/src/components/experiments/results/InsightSection.tsx
- [ ] T060 [US1] Implement collapsed state (default) in InsightSection with Collapsible from shadcn/ui
- [ ] T061 [US1] Implement loading state in InsightSection (Loader2 spinner, "Gerando insights...")
- [ ] T062 [US1] Implement error state in InsightSection (Alert component, "Insights indisponíveis")
- [ ] T063 [US1] Implement failed state in InsightSection (status="failed" → destructive Alert)
- [ ] T064 [US1] Implement completed state in InsightSection (4 sections: problem understanding, trends, findings, summary)
- [ ] T065 [US1] Add metadata footer to InsightSection (model name, timestamp with formatDistanceToNow)
- [ ] T066 [US1] Add InsightSection to PhaseOverview.tsx (Try vs Success chart)
- [ ] T067 [US1] Add InsightSection to PDPSection.tsx
- [ ] T068 [US1] Add InsightSection to RadarSection.tsx (Radar Comparison chart)
- [ ] T069 [US1] Add InsightSection to PCAScatterSection.tsx
- [ ] T070 [US1] Add InsightSection to ExtremeCasesSection.tsx
- [ ] T071 [US1] Add InsightSection to OutliersSection.tsx
- [ ] T072 [US1] Add InsightSection to DendrogramSection.tsx (SHAP Summary chart - assuming this is the correct section)

**Checkpoint**: User can view individual chart insights in all 7 supported chart types. Test each chart independently.

---

## Phase 5: User Story 2 - Access Executive Summary

**Goal**: Display executive summary synthesizing all insights in a modal/drawer accessible from results page header

**Independent Test**: Run simulation → Wait for all insights to complete → Click "Ver Resumo Executivo" button → Verify modal opens with 4 sections (overview, explainability, segmentation, edge cases) + recommendations

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T073 [P] [US2] Contract test for GET /experiments/{id}/insights/summary in tests/contract/test_insights_contracts.py
- [ ] T074 [P] [US2] Integration test for GET /experiments/{id}/insights/summary in tests/integration/api/test_insights_router.py
- [ ] T075 [P] [US2] Integration test for partial summary (< 3 insights) in tests/integration/api/test_insights_router.py
- [ ] T076 [P] [US2] Frontend unit test for useExecutiveSummary hook in frontend/src/hooks/__tests__/use-executive-summary.test.ts
- [ ] T077 [P] [US2] Frontend component test for ExecutiveSummaryModal in frontend/src/components/experiments/results/__tests__/ExecutiveSummaryModal.test.tsx

### Implementation for User Story 2

#### Backend API

- [ ] T078 [US2] Implement GET /experiments/{id}/insights/summary endpoint in src/synth_lab/api/routers/insights.py
- [ ] T079 [US2] Add 404 handling for missing summary in insights.py
- [ ] T080 [US2] Add logic to return partial summary with warning if < 3 insights available

#### Frontend API Client

- [ ] T081 [US2] Implement getExecutiveSummary() function in frontend/src/services/insights-api.ts

#### Frontend Hooks

- [ ] T082 [P] [US2] Create useExecutiveSummary hook in frontend/src/hooks/use-executive-summary.ts
- [ ] T083 [US2] Add auto-refresh logic to useExecutiveSummary (every 15s if status="pending" or "partial")
- [ ] T084 [US2] Add staleTime caching (5 minutes for completed summaries) to useExecutiveSummary

#### Frontend Components

- [ ] T085 [P] [US2] Create ExecutiveSummaryModal component in frontend/src/components/experiments/results/ExecutiveSummaryModal.tsx
- [ ] T086 [US2] Implement Sheet layout (right side panel) in ExecutiveSummaryModal using shadcn/ui Sheet
- [ ] T087 [US2] Implement loading state in ExecutiveSummaryModal (centered Loader2, "Gerando resumo executivo...")
- [ ] T088 [US2] Implement partial summary state in ExecutiveSummaryModal (warning Alert with chart count)
- [ ] T089 [US2] Implement completed state with 4 main sections in ExecutiveSummaryModal (Overview, Explainability, Segmentation, Edge Cases)
- [ ] T090 [US2] Add recommendations section to ExecutiveSummaryModal (numbered list with primary badge for each item)
- [ ] T091 [US2] Add metadata footer to ExecutiveSummaryModal (model, included chart types, timestamp)
- [ ] T092 [P] [US2] Create ViewSummaryButton component in frontend/src/components/experiments/results/ViewSummaryButton.tsx
- [ ] T093 [US2] Implement button state in ViewSummaryButton (disabled if no summary, loading indicator, "Novo" badge)
- [ ] T094 [US2] Wire ViewSummaryButton to ExecutiveSummaryModal (open state management)
- [ ] T095 [US2] Add ViewSummaryButton to ExperimentResultsPage header (alongside existing action buttons)

**Checkpoint**: User can access executive summary from results page. Verify modal opens, sections displayed correctly, auto-refresh works.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements, cleanup, and validation

- [ ] T096 [P] Remove "Insights" tab from phase navigation in frontend (FR-013 compliance)
- [ ] T097 [P] Remove "Gerar Insight" button from individual chart cards in frontend (FR-013 compliance)
- [ ] T098 [P] Add unit tests for all prompt builder methods in tests/unit/services/test_insight_service.py
- [ ] T099 [P] Add unit tests for ExecutiveSummary prompt builder in tests/unit/services/test_executive_summary_service.py
- [ ] T100 [P] Add E2E test for complete workflow (simulation → charts → insights → summary) in tests/integration/test_e2e_insights.py
- [ ] T101 Verify all tests pass (pytest tests/ -v)
- [ ] T102 Run quickstart.md validation scenarios (manual testing walkthrough)
- [ ] T103 [P] Performance test: Verify insights generated within 2 minutes of chart caching
- [ ] T104 [P] Performance test: Verify summary generated within 30 seconds of last insight
- [ ] T105 [P] Verify Phoenix tracing works for all LLM calls (check traces in Phoenix UI)
- [ ] T106 Code review: Verify all architecture patterns followed (Router→Service→Repository, pure components, etc.)
- [ ] T107 Final commit: feat: Add AI-generated insights for quantitative analysis

**Checkpoint**: Feature complete, all tests pass, ready for PR/deployment

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 3 (Phase 3)**: Depends on Foundational - Backend infrastructure for automatic generation
- **User Story 1 (Phase 4)**: Depends on Foundational - Can start in parallel with US3 backend, requires US3 API endpoints for full integration
- **User Story 2 (Phase 5)**: Depends on Foundational + US3 backend (executive summary generation)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 3 (P1 - Infrastructure)**: Independent - Provides backend services for US1 and US2
- **User Story 1 (P1 - Chart Insights)**: Depends on US3 backend being complete (API endpoints needed)
- **User Story 2 (P2 - Executive Summary)**: Depends on US3 backend being complete (summary generation service)

### Within Each User Story

- Tests MUST be written and FAIL before implementation (TDD)
- Backend entities before services
- Backend services before API endpoints
- API endpoints before frontend services
- Frontend services before hooks
- Hooks before components
- Core components before integration into existing pages

### Parallel Opportunities

**Phase 1 (Setup)**: All tasks marked [P] can run in parallel (T003)

**Phase 2 (Foundational)**:
- T004, T005, T006 (entities) can run in parallel
- T007-T011 (repository methods) can run after entities, in parallel with each other
- T012, T013 (frontend types and query keys) can run in parallel with repository work

**Phase 3 (User Story 3)**:
- All test files (T014-T020) can be written in parallel
- Prompt builders (T023-T029) can be implemented in parallel after T021
- Error handling (T036, T037) can be done in parallel

**Phase 4 (User Story 1)**:
- All test files (T042-T046) can be written in parallel
- Frontend components for different charts (T066-T072) can be implemented in parallel

**Phase 5 (User Story 2)**:
- All test files (T073-T077) can be written in parallel
- ExecutiveSummaryModal (T085) and ViewSummaryButton (T092) can be implemented in parallel

**Phase 6 (Polish)**:
- Most cleanup tasks (T096-T105) can run in parallel after core implementation

---

## Parallel Example: User Story 3 Backend

```bash
# Launch all prompt builder methods together (different chart types, no dependencies):
Task: "T023 [US3] Implement InsightService._build_prompt_try_vs_success()"
Task: "T024 [US3] Implement InsightService._build_prompt_shap_summary()"
Task: "T025 [US3] Implement InsightService._build_prompt_pdp()"
Task: "T026 [US3] Implement InsightService._build_prompt_pca_scatter()"
Task: "T027 [US3] Implement InsightService._build_prompt_radar_comparison()"
Task: "T028 [US3] Implement InsightService._build_prompt_extreme_cases()"
Task: "T029 [US3] Implement InsightService._build_prompt_outliers()"
```

---

## Parallel Example: User Story 1 Frontend

```bash
# Launch all chart modifications together (different files, no dependencies):
Task: "T066 [US1] Add InsightSection to PhaseOverview.tsx"
Task: "T067 [US1] Add InsightSection to PDPSection.tsx"
Task: "T068 [US1] Add InsightSection to RadarSection.tsx"
Task: "T069 [US1] Add InsightSection to PCAScatterSection.tsx"
Task: "T070 [US1] Add InsightSection to ExtremeCasesSection.tsx"
Task: "T071 [US1] Add InsightSection to OutliersSection.tsx"
Task: "T072 [US1] Add InsightSection to DendrogramSection.tsx"
```

---

## Implementation Strategy


1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T013) - **CRITICAL BLOCKER**
3. Complete Phase 3: User Story 3 - Backend infrastructure (T014-T041)
4. Complete Phase 4: User Story 1 - Chart insights UI (T042-T072)
5. Test complete workflow:
   - Run simulation
   - Verify insights generated automatically
   - Verify insights displayed in all 7 chart cards
   - Verify loading/error/completed states work


### Parallel Team Strategy

With multiple developers:

1. **Team completes Setup + Foundational together** (Phases 1-2)
2. Once Foundational is done:
   - **Developer A**: User Story 3 backend (T014-T041)
   - **Developer B**: User Story 1 frontend tests + components (T042-T046, T059-T072) - waits for US3 API
   - **Developer C**: User Story 2 summary feature (T073-T095) - waits for US3 backend
3. **Integration**: After US3 backend completes, US1 and US2 can integrate and test
4. **Polish**: All developers contribute to Phase 6 tasks

---

## Notes

- **[P]** tasks = different files, no dependencies, safe for parallel execution
- **[Story]** label maps task to specific user story for traceability
- Each user story should be independently testable
- Verify tests **FAIL** before implementing (Red-Green-Refactor)
- Commit frequently (after each task or logical group per Constitution Principle IV)
- Stop at any checkpoint to validate story independently
- All LLM calls **MUST** use Phoenix tracing (Constitution Principle VIII)
- All prompts in Portuguese (user-facing), code in English (Constitution Principle VI)

---

**Total Tasks**: 107
**Tests**: 26 (TDD approach per Constitution)
**User Story Breakdown**:
- Setup: 3 tasks
- Foundational: 10 tasks
- User Story 3 (Infrastructure): 28 tasks (7 tests + 21 implementation)
- User Story 1 (Chart Insights): 31 tasks (5 tests + 26 implementation)
- User Story 2 (Executive Summary): 23 tasks (5 tests + 18 implementation)
- Polish: 12 tasks (4 tests + 8 cleanup)

**Parallel Opportunities**: 45+ tasks can run in parallel across phases
**MVP Scope**: Phases 1-4 (42 tasks - Setup + Foundational + US3 + US1)
**Estimated MVP Effort**: ~2-3 weeks with test-first approach
