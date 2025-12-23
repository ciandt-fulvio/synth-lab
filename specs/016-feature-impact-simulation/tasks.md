# Tasks: Sistema de Simulacao de Impacto de Features

**Input**: Design documents from `/specs/016-feature-impact-simulation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/simulation-api.yaml, quickstart.md

**Organization**: Tasks grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependencies

- [x] T001 Add numpy>=1.26.0, scikit-learn>=1.4.0 to pyproject.toml dependencies
- [x] T002 Run `uv lock` and `uv sync` to install new dependencies
- [x] T003 [P] Create src/synth_lab/services/simulation/ directory structure with __init__.py
- [x] T004 [P] Create src/synth_lab/data/ directory if not exists

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Create src/synth_lab/domain/entities/simulation_attributes.py with SimulationObservables, SimulationLatentTraits, SimulationAttributes Pydantic models (from data-model.md)
- [x] T006 [P] Create src/synth_lab/domain/entities/feature_scorecard.py with ScorecardDimension, ScorecardIdentification, FeatureScorecard Pydantic models
- [x] T007 [P] Create src/synth_lab/domain/entities/scenario.py with Scenario model and PREDEFINED_SCENARIOS dict
- [x] T008 [P] Create src/synth_lab/domain/entities/simulation_run.py with SimulationConfig, SimulationRun models
- [x] T009 [P] Create src/synth_lab/domain/entities/synth_outcome.py with SynthOutcome model
- [x] T010 [P] Create src/synth_lab/domain/entities/region_analysis.py with RegionRule, RegionAnalysis models
- [x] T011 [P] Create src/synth_lab/domain/entities/sensitivity_result.py with DimensionSensitivity, SensitivityResult models
- [x] T012 [P] Create src/synth_lab/domain/entities/assumption_log.py with LogEntry, AssumptionLog models
- [x] T013 Update src/synth_lab/domain/entities/__init__.py to export all new entities
- [x] T014 Create database migration for new tables (feature_scorecards, simulation_runs, synth_outcomes, region_analyses, assumption_log) per data-model.md SQL schema
- [x] T015 Create src/synth_lab/data/scenarios.json with 3 keys: baseline, crisis, first-use (all scenario definitions)

**Checkpoint**: Foundation ready - all domain entities and database schema in place

---

## Phase 3: User Story 1 - Estender Gensynth com Atributos de Simulacao (Priority: P1)

**Goal**: Every synth generated via gensynth includes simulation_attributes with observables and latent traits

**Independent Test**: Generate a synth via gensynth and verify JSON contains simulation_attributes with all 9 fields in [0,1]

### Implementation for User Story 1

- [x] T018 [US1] Create src/synth_lab/gen_synth/simulation_attributes.py with:
  - generate_observables(rng, disabilities_data) function using Beta distributions
  - derive_latent_traits(observables) function with weighted formulas
  - generate_simulation_attributes(rng, disabilities_data) main function
- [x] T019 [US1] Implement digital_literacy_to_alfabetizacao_digital(dl: float) -> int translation function in simulation_attributes.py
- [x] T020 [US1] Implement motor_ability_from_disability(tipo: str) -> float derivation function in simulation_attributes.py
- [x] T021 [US1] Modify src/synth_lab/gen_synth/synth_builder.py to call generate_simulation_attributes() during synth assembly
- [x] T022 [US1] Update synth_builder.py to populate capacidades_tecnologicas.alfabetizacao_digital from digital_literacy translation
- [x] T023 [US1] Add simulation_attributes section to synth JSON output in synth_builder.py
- [x] T024 [US1] Add validation in simulation_attributes.py to ensure all values are in [0,1]
- [x] T025 [US1] Create tests/unit/gen_synth/test_simulation_attributes.py with validation tests for:
  - Beta distribution outputs in [0,1]
  - Latent trait derivation formulas correctness
  - motor_ability derivation from disability types
  - digital_literacy to alfabetizacao_digital translation

**Checkpoint**: Synths now include simulation_attributes - ready for simulation (COMPLETE)

**Implementation Note (2025-12-23)**: The approach was modified from the original plan:
- **Original Plan**: Generate `simulation_attributes` during gensynth and save permanently in synth JSON
- **Actual Implementation**: Generate `simulation_attributes` on-the-fly during simulation from real synth data
- **Location**: `simulation_service._generate_simulation_attributes()` derives attributes from demografia, psicografia, capacidades_tecnologicas, deficiencias
- **Benefits**: More flexible (can adjust derivation formulas), ensures consistency with synth data, works with existing synths
- **Precision**: All values rounded to 3 decimal places for consistency

---

## Phase 4: User Story 2 - Criar Feature Scorecard (Priority: P1)

**Goal**: PM can create and persist feature scorecards with LLM-assisted insights

**Independent Test**: Create a scorecard via API and verify all sections are populated, scores have rules, and LLM generates justifications

### Implementation for User Story 2

- [x] T026 [US2] Create src/synth_lab/repositories/scorecard_repository.py with:
  - create_scorecard(scorecard: FeatureScorecard) -> str
  - get_scorecard(id: str) -> FeatureScorecard | None
  - list_scorecards(limit, offset) -> tuple[list, int]
- [x] T027 [US2] Create src/synth_lab/services/simulation/scorecard_service.py with:
  - create_scorecard(data: dict) -> FeatureScorecard
  - get_scorecard(id: str) -> FeatureScorecard
  - list_scorecards(limit, offset) -> ScorecardList
- [x] T028 [US2] Create src/synth_lab/services/simulation/scorecard_llm.py with:
  - generate_justification(scorecard: FeatureScorecard) -> str
  - generate_impact_hypotheses(scorecard: FeatureScorecard) -> list[str]
  - generate_suggested_adjustments(scorecard: FeatureScorecard) -> list[str]
- [x] T029 [US2] Add Phoenix tracing to scorecard_llm.py for LLM calls (FR-012, FR-013)
- [x] T030 [US2] Create src/synth_lab/api/routers/simulation.py with:
  - POST /api/v1/scorecards (createScorecard)
  - GET /api/v1/scorecards (listScorecards)
  - GET /api/v1/scorecards/{scorecard_id} (getScorecard)
  - POST /api/v1/scorecards/{scorecard_id}/generate-insights (generateScorecardInsights)
- [x] T031 [US2] Register simulation router in src/synth_lab/api/main.py
- [x] T032 [US2] Add validation for uncertainty intervals (min <= max, values in [0,1]) in scorecard_service.py
- [x] T033 [US2] Create tests/unit/simulation/test_scorecard_service.py with validation tests

**Checkpoint**: Scorecards can be created and persisted with LLM insights (COMPLETE)

---

## Phase 5: User Story 3 - Executar Simulacao de Impacto (Priority: P1)

**Goal**: Execute Monte Carlo simulation (N synths x M executions) and produce outcomes per synth

**Independent Test**: Run simulation with 100 synths x 100 executions, verify outcomes sum to 1.0 per synth

### Implementation for User Story 3

- [x] T034 [US3] Create src/synth_lab/services/simulation/sample_state.py with:
  - sample_user_state(latent_traits, scenario, sigma, rng) function
  - Add noise via Normal distributions to latent traits
  - Apply scenario modifiers (trust, friction, motivation)
- [x] T035 [US3] Create src/synth_lab/services/simulation/probability.py with:
  - sigmoid(x) helper function
  - calculate_p_attempt(user_state, scorecard) -> float
  - calculate_p_success(user_state, scorecard) -> float
  - sample_outcome(p_attempt, p_success, rng) -> str
- [x] T036 [US3] Create src/synth_lab/services/simulation/engine.py with:
  - MonteCarloEngine class
  - run_simulation(synths, scorecard, scenario, config) -> SimulationRun
  - Vectorized operations using NumPy for performance
- [x] T037 [US3] Implement reproducibility with configurable seed in engine.py using np.random.default_rng(seed)
- [x] T038 [US3] Create src/synth_lab/repositories/simulation_repository.py with:
  - create_simulation_run(run: SimulationRun) -> str
  - update_simulation_run(run: SimulationRun)
  - get_simulation_run(id: str) -> SimulationRun | None
  - list_simulation_runs(filters, limit, offset) -> tuple[list, int]
  - save_synth_outcomes(outcomes: list[SynthOutcome])
  - get_synth_outcomes(simulation_id, limit, offset) -> tuple[list, int]
- [x] T039 [US3] Create src/synth_lab/services/simulation/simulation_service.py with:
  - execute_simulation(scorecard_id, scenario_id, ...) -> SimulationRun
  - get_simulation(id: str) -> SimulationRun
  - list_simulations(filters) -> SimulationList
  - get_synth_outcomes(simulation_id, limit, offset) -> OutcomeList
  - _generate_simulation_attributes() - derives attributes from synth data on-the-fly
- [x] T040 [US3] Add simulation endpoints to src/synth_lab/api/routers/simulation.py:
  - POST /simulation/simulations (runSimulation)
  - GET /simulation/simulations (listSimulations)
  - GET /simulation/simulations/{simulation_id} (getSimulation)
  - GET /simulation/simulations/{simulation_id}/outcomes (getSimulationOutcomes)
- [x] T041 [US3] Add scenario endpoints to src/synth_lab/api/routers/simulation.py:
  - GET /simulation/scenarios (listScenarios)
  - GET /simulation/scenarios/{scenario_id} (getScenario)
- [ ] T042 [US3] Create tests/unit/simulation/test_sample_state.py with state sampling tests
- [ ] T043 [P] [US3] Create tests/unit/simulation/test_probability.py with probability calculation tests
- [ ] T044 [P] [US3] Create tests/unit/simulation/test_engine.py with engine tests including:
  - Performance test: 100x100 <= 1 seconds (SC-003)
  - Reproducibility test: same seed = same results (SC-007)

**Checkpoint**: Monte Carlo simulation executes and produces valid outcomes - core functionality COMPLETE

**Status (2025-12-23)**: Phase 5 implementation complete (8/11 tasks)
- ✅ Core simulation engine (sample_state, probability, engine)
- ✅ Repository and service layers (simulation_repository, simulation_service)
- ✅ API endpoints (simulations + scenarios)
- ⚠️ Unit tests pending (T042-T044) - basic validation exists via `__main__` blocks
- 🔧 Recent fixes: Precision (3 decimals), attribute generation from real synth data

---

## Phase 6: User Story 4 - Analisar Resultados por Regiao do Espaco (Priority: P2)

**Goal**: Identify synth regions with high failure rates using interpretable rules

**Independent Test**: Analyze simulation results and verify groups are identified with rules like "capability < 0.48 AND trust < 0.4"

### Implementation for User Story 4

- [x] T045 [US4] Create src/synth_lab/services/simulation/analyzer.py with:
  - RegionAnalyzer class using sklearn DecisionTreeClassifier
  - analyze_regions(outcomes, min_failure_rate, max_depth) -> list[RegionAnalysis]
  - extract_rules(tree, feature_names) -> list[RegionRule]
  - format_rule_text(rules) -> str
- [x] T046 [US4] Configure DecisionTreeClassifier with:
  - max_depth=4, min_samples_leaf=20, min_samples_split=40
  - class_weight='balanced' (as per research.md)
- [x] T047 [US4] Create src/synth_lab/repositories/region_repository.py with:
  - save_region_analyses(analyses: list[RegionAnalysis])
  - get_region_analyses(simulation_id) -> list[RegionAnalysis]
- [x] T048 [US4] Add region analysis endpoint to src/synth_lab/api/routers/simulation.py:
  - GET /simulation/simulations/{simulation_id}/regions (analyzeRegions)
- [ ] T049 [US4] Create tests/unit/simulation/test_analyzer.py with:
  - Rule extraction tests
  - Failure rate threshold filtering tests

**Checkpoint**: Region analysis identifies groups with interpretable rules

---

## Phase 7: User Story 5 - Comparar Resultados entre Cenarios (Priority: P2)

**Goal**: Compare simulation results across different pre-defined scenarios

**Independent Test**: Run same scorecard with baseline, crisis, first-use scenarios and compare outcomes

### Implementation for User Story 5

- [x] T050 [US5] Create src/synth_lab/services/simulation/scenario_loader.py with:
  - load_scenario(scenario_id: str) -> Scenario
  - list_scenarios() -> list[Scenario]
  - Load from data/config/scenarios.json
- [x] T051 [US5] Create src/synth_lab/services/simulation/comparison_service.py with:
  - compare_simulations(simulation_ids: list[str]) -> CompareResult
  - Calculate outcomes_by_scenario
  - Identify most_affected_regions
- [x] T052 [US5] Add comparison endpoint to src/synth_lab/api/routers/simulation.py:
  - POST /simulations/compare (compareSimulations)
- [ ] T053 [US5] Create tests/unit/simulation/test_comparison_service.py with comparison tests

**Checkpoint**: Scenario comparison reveals context-sensitive synth groups

---

## Phase 8: User Story 6 - Explorar Sensibilidade de Variaveis (Priority: P3)

**Goal**: Identify which scorecard dimension has the greatest impact on outcomes

**Independent Test**: Vary complexity by +/-0.1 and verify delta is calculated correctly

### Implementation for User Story 6

- [x] T054 [US6] Create src/synth_lab/services/simulation/sensitivity.py with:
  - SensitivityAnalyzer class
  - analyze_sensitivity(simulation_id, deltas) -> SensitivityResult
  - OAT (One-At-a-Time) methodology per research.md
  - calculate_sensitivity_index(baseline_outcomes, delta_outcomes, delta_size) -> float
- [x] T055 [US6] Implement ranking of dimensions by sensitivity_index
- [x] T056 [US6] Add sensitivity endpoint to src/synth_lab/api/routers/simulation.py:
  - GET /simulations/{simulation_id}/sensitivity (analyzeSensitivity)
- [ ] T057 [US6] Create tests/unit/simulation/test_sensitivity.py with:
  - OAT calculation tests
  - Sensitivity index tests
  - Performance test: < 10 seconds (SC-005)

**Checkpoint**: Sensitivity analysis identifies most impactful dimension

---

## Phase 9: User Story 7 - Registrar Decisoes e Premissas (Priority: P3)

**Goal**: Maintain auditable log of all scorecards, simulations, and decisions

**Independent Test**: Create scorecard, run simulation, verify all actions logged with timestamps

### Implementation for User Story 7

- [ ] T058 [US7] Create src/synth_lab/repositories/audit_repository.py with:
  - add_log_entry(entry: LogEntry) -> str
  - get_log_entries(filters, limit) -> list[LogEntry]
  - search_by_scorecard_id(scorecard_id) -> list[LogEntry]
  - search_by_date_range(from_date, to_date) -> list[LogEntry]
- [ ] T059 [US7] Create src/synth_lab/services/simulation/audit_service.py with:
  - log_action(action: str, **kwargs) -> LogEntry
  - get_audit_log(filters, limit) -> list[LogEntry]
- [ ] T060 [US7] Add audit logging calls to:
  - scorecard_service.py (create_scorecard, generate_insights)
  - simulation_service.py (run_simulation)
  - comparison_service.py (compare_simulations)
- [ ] T061 [US7] Add audit endpoint to src/synth_lab/api/routers/simulation.py:
  - GET /api/v1/audit/log (getAuditLog)
- [ ] T062 [US7] Create tests/unit/simulation/test_audit_service.py with logging tests

**Checkpoint**: All actions are auditable with full history

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements and validation

- [ ] T063 [P] Run ruff check and fix any linting issues
- [ ] T064 [P] Run ruff format on all new files
- [ ] T065 Create tests/integration/simulation/test_full_simulation.py with end-to-end test
- [ ] T066 Create tests/contract/test_simulation_api.py to validate endpoints against contracts/simulation-api.yaml
- [ ] T067 Validate quickstart.md examples work correctly
- [ ] T068 Add docstrings to all public functions following Google style
- [ ] T069 Verify SC-003: 100x100 simulation <= 1 seconds
- [ ] T070 [P] Verify SC-005: sensitivity analysis < 10 seconds
- [ ] T071 [P] Verify SC-007: reproducibility with same seed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Stories (Phase 3-9)**: All depend on Foundational completion
- **Polish (Phase 10)**: Depends on all desired user stories being complete

### User Story Dependencies

| Story | Priority | Can Start After | Dependencies on Other Stories |
|-------|----------|-----------------|------------------------------|
| US1 | P1 | Phase 2 | None - generates synth attributes |
| US2 | P1 | Phase 2 | None - creates scorecards |
| US3 | P1 | Phase 2 | US1 (needs synths with attrs), US2 (needs scorecards) |
| US4 | P2 | Phase 2 | US3 (needs simulation results) |
| US5 | P2 | Phase 2 | US3 (needs simulation results) |
| US6 | P3 | Phase 2 | US3 (needs simulation results) |
| US7 | P3 | Phase 2 | None - but integrates with US2, US3, US5 |

### Parallel Opportunities

**Within Phase 2 (Foundational)**:
- T006, T007, T008, T009, T010, T011, T012 can all run in parallel (different entity files)

**US1 and US2 can run in parallel** - they have no dependencies on each other

**Within Phase 3 (US1)**:
- T018-T024 are sequential (build on each other)

**Within Phase 4 (US2)**:
- T026, T028 can run in parallel (repository vs LLM service)

**Within Phase 5 (US3)**:
- T034, T035 can run in parallel (sample_state vs probability)
- T042, T043, T044 can all run in parallel (different test files)

**US4, US5, US6 can run in parallel** after US3 is complete

**Within Phase 10 (Polish)**:
- T063, T064 can run in parallel (lint vs format)
- T069, T070, T071 can run in parallel (different performance tests)

---

## Summary

| Metric | Value |
|--------|-------|
| **Total Tasks** | 69 |
| **Phase 1 (Setup)** | 4 |
| **Phase 2 (Foundational)** | 11 |
| **US1 Tasks** | 8 |
| **US2 Tasks** | 8 |
| **US3 Tasks** | 11 |
| **US4 Tasks** | 5 |
| **US5 Tasks** | 4 |
| **US6 Tasks** | 4 |
| **US7 Tasks** | 5 |
| **Phase 10 (Polish)** | 9 |

### MVP Scope (P1 Stories Only)

**Minimum Viable Product**: Phases 1-5 (US1 + US2 + US3)
- **Tasks**: 42 tasks
- **Deliverables**:
  - Synths with simulation attributes
  - Feature scorecards with LLM insights
  - Monte Carlo simulation execution
  - Basic outcomes per synth
- **Success Criteria Met**: SC-001, SC-003, SC-007

### Full Feature Scope

**Complete Implementation**: All phases
- **Tasks**: 69 tasks
- **Additional Deliverables**:
  - Region analysis with interpretable rules (US4)
  - Scenario comparison (US5)
  - Sensitivity analysis (US6)
  - Audit logging (US7)
- **All Success Criteria Met**: SC-001 through SC-009


