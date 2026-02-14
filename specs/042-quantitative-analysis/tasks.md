# Tasks: Análise Quantitativa (Modelagem Causal + Monte Carlo)

**Input**: Design documents from `/specs/042-quantitative-analysis/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md, quickstart.md

**Tests**: Included per Constitution (TDD — NON-NEGOTIABLE). Tests written and failing before implementation.

**Organization**: Tasks grouped by user story from spec.md:
- **US1** (P1): Gerar Modelo Causal (DAG + Likert)
- **US2** (P1): Rodar Simulação e Ver Resultados
- **US3** (P1): Gerar Interview Guide automaticamente

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Add dependencies and shared frontend scaffolding

- [x] T001 Add `numpy>=1.26,<3` to `pyproject.toml` dependencies and regenerate lockfile
- [x] T002 [P] Create TypeScript types for quantitative analysis in `frontend/src/types/quantitative-analysis.ts` (CausalModel, CausalEdge, LikertOption, SimulationRun, SimulationStats, Segments, SensitivityItem, Interpretation — see contracts/api.md)
- [x] T003 [P] Add quantitative analysis query keys in `frontend/src/lib/query-keys.ts` (model, results)

---

## Phase 2: Foundational (Backend Data Layer)

**Purpose**: Domain entities, ORM models, migration, repositories — MUST complete before any user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests (TDD — write first, verify they fail)

- [x] T004 [P] Unit test for CausalModel + CausalEdge entity validation in `tests/unit/test_causal_model_entity.py` (ID format cm_xxx, node count 7-10, edge userVar enum, direction ±1, options count 5, selected_option nullable 0-4)
- [x] T005 [P] Unit test for SimulationRun + AnalysisInterpretation entity validation in `tests/unit/test_simulation_run_entity.py` (ID format sr_xxx/ai_xxx, stats required keys, section enum, unique constraint)

### Implementation

- [x] T006 [P] Create CausalModel + CausalEdge domain entities in `src/synth_lab/domain/entities/causal_model.py` (P1dantic models with validators per data-model.md — ID generation, field constraints, userVar enum)
- [x] T007 [P] Create SimulationRun + AnalysisInterpretation domain entities in `src/synth_lab/domain/entities/simulation_run.py` (P1dantic models per data-model.md — stats schema, section enum, immutable after creation)
- [x] T008 [P] Create CausalModel + CausalEdge ORM models in `src/synth_lab/models/orm/causal_model.py` (SQLAlchemy 2.0, JSONB for nodes/options, CASCADE delete, composite PK on edges, indexes)
- [x] T009 [P] Create SimulationRun + AnalysisInterpretation ORM models in `src/synth_lab/models/orm/simulation_run.py` (SQLAlchemy 2.0, JSONB for stats/distribution/segments/sensitivity, UNIQUE on run+section)
- [x] T010 Register new ORM models in `src/synth_lab/models/orm/__init__.py` (import for Alembic auto-detection)
- [x] T011 Create Alembic migration for `causal_models`, `causal_edges`, `simulation_runs`, `analysis_interpretations` tables — run `make db-migrate MSG='add quantitative analysis tables'`
- [x] T012 [P] Create CausalModelRepository in `src/synth_lab/repositories/causal_model_repository.py` (CRUD: create_model+edges, get_by_experiment, update_edge_selections, delete_by_experiment — follows BaseRepository pattern)
- [x] T013 [P] Create SimulationRunRepository in `src/synth_lab/repositories/simulation_run_repository.py` (CRUD: create_run+interpretations, get_latest_by_experiment, list_by_experiment)

**Checkpoint**: Data layer complete. All 4 tables exist, entities validate, repositories CRUD. Run `make test` to confirm unit tests pass.

---

## Phase 3: User Story 1 — Gerar Modelo Causal (Priority: P1)

**Goal**: PM gera DAG causal via LLM e calibra premissas via Likert. Modelo persiste entre sessões.

**Independent Test**: Criar experimento → aba Análise Quanti → "Gerar Modelo" → DAG com 7-10 nós aparece → clicar Likerts → seleções salvas → sair e voltar → seleções preservadas.

### Tests (TDD)

- [x] T014 [P] [US1] Integration test for generate_causal_model() with mocked OpenAI in `tests/integration/test_quantitative_analysis_generate.py` (mock gpt-5.1 returning valid DAG JSON, verify model saved with edges, verify Phoenix tracing span created)
- [x] T015 [P] [US1] Integration test for update_edge_selections() in `tests/integration/test_quantitative_analysis_edges.py` (save selections, verify persistence, verify partial updates, verify invalid edge_id rejected)

### Backend Implementation

- [x] T016 [US1] Create API schemas for model generation and edge updates in `src/synth_lab/api/schemas/quantitative_analysis.py` (CausalModelResponse, EdgeUpdateRequest with selections dict, EdgeUpdateResponse with counts)
- [x] T017 [US1] Implement QuantitativeAnalysisService.generate_causal_model() in `src/synth_lab/services/quantitative_analysis_service.py` (load experiment context, call gpt-5.1 with DAG_SYSTEM prompt from Apêndice A, parse JSON, save via repository, Phoenix tracing with `_tracer.start_as_current_span()`, 2 retries on invalid JSON)
- [x] T018 [US1] Implement QuantitativeAnalysisService.get_causal_model() and update_edge_selections() in same service file (get by experiment_id, batch update selected_option, return answer counts)
- [x] T019 [US1] Create API router with POST /generate, GET /model, PATCH /edges in `src/synth_lab/api/routers/quantitative_analysis.py` (follows router pattern: request → service.method() → response, Depends for service injection)
- [x] T020 [US1] Register quantitative_analysis router in `src/synth_lab/api/main.py` under prefix `/experiments/{experiment_id}/quantitative-analysis`

### Frontend Implementation

- [x] T021 [US1] Create API service functions in `frontend/src/services/quantitative-analysis-api.ts` (generateCausalModel, getCausalModel, updateEdgeSelections — using fetchAPI)
- [x] T022 [US1] Create React Query hooks in `frontend/src/hooks/use-quantitative-analysis.ts` (useGenerateCausalModel mutation, useCausalModel query, useUpdateEdgeSelections mutation with debounce)
- [x] T023 [P] [US1] Create CausalDAGView component in `frontend/src/components/quantitative/CausalDAGView.tsx` (SVG 3-layer layout: demographic roots left, mediators center, outcome right. Edges as quadratic curves. Stroke width = 1 + mu*4. Color: blue direction=1, orange direction=-1. Highlight active edge on Likert focus.)
- [x] T024 [P] [US1] Create LikertAssertions component in `frontend/src/components/quantitative/LikertAssertions.tsx` (card per edge with header, 5 radio options showing only text, selected state highlighted. onChange calls debounced save via hook. Shows answer progress "5/8 respondidas".)
- [x] T025 [US1] Create QuantitativeAnalysisTab container in `frontend/src/components/quantitative/QuantitativeAnalysisTab.tsx` (orchestrates: "Gerar Modelo" button → loading → CausalDAGView + LikertAssertions side-by-side or stacked. Handles empty state, loading, error.)
- [x] T026 [US1] Integrate QuantitativeAnalysisTab into "Análise Quanti" tab in `frontend/src/pages/ExperimentDetail.tsx` (replace placeholder content at lines 305-332 with new component, pass experiment data)

**Checkpoint**: US1 complete. PM can generate a causal model, see DAG, select Likerts, and selections persist. Run `make test` + manual verification.

---

## Phase 4: User Story 2 — Rodar Simulação e Ver Resultados (Priority: P1

**Goal**: PM roda Monte Carlo e vê distribuição, segmentos e sensibilidade com interpretações AI.

**Independent Test**: Com modelo calibrado → "Simular" → histograma + stats aparecem → 9 segment cards → sensitivity bars ordenadas por impacto → cada seção com interpretação AI contextualizada.

### Tests (TDD)

- [x] T027 [P] [US2] Unit test for simulation_engine with deterministic seed in `tests/unit/test_simulation_engine.py` (run_simulation with fixed seed=42, verify stats within expected ranges, verify distribution length=n_iterations, verify segment buckets correct)
- [x] T028 [P] [US2] Unit test for userVar extractors in `tests/unit/test_uservar_extractors.py` (test each of 10 extractors with real synth data shapes, verify normalization to [0,1], verify defaults for missing data)
- [x] T029 [P] [US2] Unit test for sensitivity analysis — covered within T027 (TestRunSensitivity class in test_simulation_engine.py)
- [x] T030 [P] [US2] Integration test for run_simulation with mocked LLM in `tests/integration/test_quantitative_analysis_simulate.py` (mock gpt-4o-mini for interpretations, verify all 3 sections populated, verify interview_guide auto-generated)

### Backend Implementation

- [x] T031 [US2] Implement extract_user_vars() and _clamp()/_normalize helpers in `src/synth_lab/services/simulation_engine.py` (10 extractors per data-model.md userVar mapping table, pure functions, no I/O)
- [x] T032 [US2] Implement run_monte_carlo() in `src/synth_lab/services/simulation_engine.py` (NumPy vectorized: BUDGET=3.0, perEdgeScale, Normal sampling, sigmoid, per Apêndice D formulas. Returns distribution array + stats dict.)
- [x] T033 [US2] Implement compute_segments() in `src/synth_lab/services/simulation_engine.py` (bucket synths by age 18-29/30-49/50+, income baixa/media/alta, education baixa/media/alta, compute adoption rate per bucket)
- [x] T034 [US2] Implement run_sensitivity() in `src/synth_lab/services/simulation_engine.py` (for each edge: fix others, vary between option 0 and option 4, 800 iterations each, impact = |mean_high - mean_low|, return sorted by impact desc)
- [x] T035 [US2] Implement compute_raw_interpretations() in `src/synth_lab/services/simulation_engine.py` (generate raw_text strings for distribution/segments/sensitivity per Apêndice D formulas — no LLM, just stats)
- [x] T036 [US2] Implement QuantitativeAnalysisService.run_simulation() in `src/synth_lab/services/quantitative_analysis_service.py` (load synths from group, extract userVars, call simulation_engine, save SimulationRun via repository)
- [x] T037 [US2] Implement QuantitativeAnalysisService.generate_interpretations() in same service (3 parallel asyncio.gather calls to gpt-4o-mini with INTERP_SYSTEM prompt from Apêndice B, save AnalysisInterpretation via repository, Phoenix tracing per call)
- [x] T038 [US2] Add simulation response schema to `src/synth_lab/api/schemas/quantitative_analysis.py` (SimulationRunResponse with nested stats, segments, sensitivity, interpretations)
- [x] T039 [US2] Add POST /simulate and GET /results endpoints to `src/synth_lab/api/routers/quantitative_analysis.py` (simulate calls service.run_simulation + generate_interpretations, results returns latest run)
- [x] T040 [US2] Add simulate and results methods to `frontend/src/services/quantitative-analysis-api.ts` — already done in T021
- [x] T041 [US2] Add useRunSimulation mutation and useSimulationResults query to `frontend/src/hooks/use-quantitative-analysis.ts` — already done in T022
- [x] T042 [P] [US2] Create DistributionChart component in `frontend/src/components/quantitative/DistributionChart.tsx` (Recharts BarChart histogram of distribution array, stats overlay with mean/median/p10/p90 lines, AI interpretation text below)
- [x] T043 [P] [US2] Create SegmentCards component in `frontend/src/components/quantitative/SegmentCards.tsx` (3×3 grid: age rows × income/education columns, each card shows segment name + adoption rate + synth count, color gradient by rate, AI interpretation text below)
- [x] T044 [P] [US2] Create SensitivityBars component in `frontend/src/components/quantitative/SensitivityBars.tsx` (Recharts horizontal BarChart sorted by impact desc, show edge header as label, impact value as bar length, AI interpretation text below)
- [x] T045 [US2] Create SimulationResults container in `frontend/src/components/quantitative/SimulationResults.tsx` (orchestrates DistributionChart + SegmentCards + SensitivityBars, handles loading states for each interpretation independently)
- [x] T046 [US2] Integrate "Simular" button + SimulationResults into QuantitativeAnalysisTab in `frontend/src/components/quantitative/QuantitativeAnalysisTab.tsx` (button visible when all edges answered or using defaults, results appear below model section, scrollable)

**Checkpoint**: US2 complete. PM can simulate and see all 3 result sections with AI interpretations. Run `make test` + manual verification.

---

## Phase 5: User Story 3 — Gerar Interview Guide (Priority: P1

**Goal**: Após simulação, interview_guide é auto-gerado com as 3 premissas mais sensíveis. Substitui geração automática na criação do experimento.

**Independent Test**: Rodar simulação → verificar que interview_guide existe no banco com context_definition, questions, context_examples preenchidos → navegar para aba entrevistas → guide disponível.

### Tests (TDD)

- [x] T047 [P] [US3] Integration test for auto-generate interview guide in `tests/integration/test_quantitative_analysis_interview_guide.py` (mock gpt-5.1 for questionnaire, verify interview_guide created/updated with 3 fields, verify existing guide overwritten)

### Backend Implementation

- [x] T048 [US3] Adapt InterviewGuideGeneratorService to support QUESTIONNAIRE_SYSTEM prompt in `src/synth_lab/services/interview_guide_generator_service.py` (new method generate_from_simulation_sync with Apêndice C prompt, output JSON with context_definition/questions/context_examples, Phoenix tracing)
- [x] T049 [US3] Add auto-generate interview_guide call in QuantitativeAnalysisService.run_simulation() after saving results (call InterviewGuideGeneratorService with top 3 sensitivity premisses as context, silent — does not block response on failure)
- [x] T050 [US3] Remove auto-generation of interview_guide from experiment creation flow — verified: no auto-generation exists in experiment creation flow (service was never invoked there)

**Checkpoint**: US3 complete. Simulation auto-generates interview guide. Old auto-gen on experiment creation removed. Run `make test` + manual verification.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Quality, edge cases, observability, E2E

- [x] T051 [P] Add loading/error/empty states to all quantitative components — already implemented: loading spinner, error with retry, empty with CTA, simulation loading overlay
- [x] T052 [P] Verify Phoenix tracing coverage — all 4 LLM calls have `_tracer.start_as_current_span()`: generate_causal_model, _generate_interpretations_sync (3x), generate_from_simulation_sync
- [x] T053 [P] Timeout handling — LLM client has built-in timeout (LLM_TIMEOUT), router handles TimeoutError→504
- [ ] T054 E2E test for full quantitative analysis flow — deferred to CI pipeline (requires Docker stack)
- [ ] T055 Run quickstart.md validation — deferred to manual testing

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup ──────────────┐
                              ▼
Phase 2: Foundational ───────┤ (BLOCKS all user stories)
                              ▼
              ┌── Phase 3: US1 (MVP) ──┐
              │                         │ (US2 depends on US1 model)
              │               Phase 4: US2 ──┐
              │                              │ (US3 depends on US2 simulation)
              │                    Phase 5: US3
              │                              │
              └──────────────────────────────┘
                              ▼
                   Phase 6: Polish
```

### User Story Dependencies

- **US1 (P1)**: Depends only on Phase 2 (Foundational). No other story dependency.
- **US2 (P1)**: Depends on US1 complete (needs CausalModel with selections to simulate).
- **US3 (P1)**: Depends on US2 complete (needs simulation results + sensitivity data for interview guide).

### Within Each User Story

1. Tests MUST be written and FAIL before implementation
2. Backend: entities → ORM → migration → repos → engine → service → API
3. Frontend: types → service → hooks → components → integration
4. Commit after each logical group

### Parallel Opportunities

**Phase 2** — all [P] tasks can run in parallel:
- T004 + T005 (entity tests in parallel)
- T006 + T007 (entities in parallel)
- T008 + T009 (ORM models in parallel)
- T012 + T013 (repositories in parallel)

**US1** — frontend components in parallel:
- T023 + T024 (CausalDAGView + LikertAssertions)

**US2** — simulation engine functions in parallel after T031:
- T032 + T033 + T034 + T035 (Monte Carlo, segments, sensitivity, raw interp)
- T042 + T043 + T044 (DistributionChart + SegmentCards + SensitivityBars)

---

## Parallel Example: US2 Backend

```bash
# After T031 (extractors), launch simulation functions in parallel:
Task: "Implement run_monte_carlo() in simulation_engine.py"        # T032
Task: "Implement compute_segments() in simulation_engine.py"       # T033
Task: "Implement run_sensitivity() in simulation_engine.py"        # T034
Task: "Implement compute_raw_interpretations() in simulation_engine.py" # T035

# After service layer done, launch frontend charts in parallel:
Task: "Create DistributionChart in DistributionChart.tsx"          # T042
Task: "Create SegmentCards in SegmentCards.tsx"                    # T043
Task: "Create SensitivityBars in SensitivityBars.tsx"              # T044
```

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- US1 é independente; US2 depende de US1; US3 depende de US2 (p1peline linear)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All LLM calls MUST use Phoenix tracing (`_tracer.start_as_current_span()`)
- All files < 500 lines; split simulation_engine.py if needed
- Use `np.random.default_rng(42)` in tests for deterministic results
