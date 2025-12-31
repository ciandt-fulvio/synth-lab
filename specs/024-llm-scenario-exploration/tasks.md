# Tasks: Simulation-Driven Scenario Exploration (LLM-Assisted)

**Input**: Design documents from `/specs/024-llm-scenario-exploration/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/exploration-api.yaml

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Project structure and shared infrastructure for exploration feature

- [ ] T001 Create feature branch `024-llm-scenario-exploration` from main
- [ ] T002 [P] Create directories: `src/synth_lab/services/exploration/`, `tests/unit/services/exploration/`
- [ ] T003 [P] Create `data/action_catalog.json` with 5 categories (UX/Interface, Onboarding, Fluxo, Comunicacao, Operacional)

---

## Phase 2: Foundational (Database & Base Entities)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create database migration for `explorations` table in `src/synth_lab/infrastructure/database.py`
  - Fields: id, experiment_id, baseline_analysis_id, goal (JSON), config (JSON), status, current_depth, total_nodes, total_llm_calls, best_success_rate, started_at, completed_at
  - Constraints: CHECK for status enum, CHECK for id pattern `expl_[a-f0-9]{8}`
  - Indexes: idx_explorations_experiment, idx_explorations_status

- [ ] T005 Create database migration for `scenario_nodes` table in `src/synth_lab/infrastructure/database.py`
  - Fields: id, exploration_id, parent_id (self-ref), depth, action_applied, action_category, rationale, scorecard_params (JSON), simulation_results (JSON), execution_time_seconds, node_status, created_at
  - Constraints: CHECK for node_status enum, CHECK for id pattern `node_[a-f0-9]{8}`, FOREIGN KEY to explorations and self
  - Indexes: idx_scenario_nodes_exploration, idx_scenario_nodes_parent, idx_scenario_nodes_status, idx_scenario_nodes_depth

- [ ] T006 [P] Create `Exploration` entity in `src/synth_lab/domain/entities/exploration.py`
  - Pydantic model with Goal (metric, operator, value) and ExplorationConfig (beam_width, max_depth, max_llm_calls, n_executions, sigma, seed)
  - ExplorationStatus enum: running, goal_achieved, depth_limit_reached, cost_limit_reached, no_viable_paths
  - ID generation with `expl_` prefix

- [ ] T007 [P] Create `ScenarioNode` entity in `src/synth_lab/domain/entities/scenario_node.py`
  - Pydantic model with ScorecardParams (complexity, initial_effort, perceived_risk, time_to_value)
  - SimulationResults (success_rate, fail_rate, did_not_try_rate)
  - NodeStatus enum: active, dominated, winner, expansion_failed
  - ID generation with `node_` prefix

- [ ] T008 [P] Create `ActionProposal` value object in `src/synth_lab/domain/entities/action_proposal.py`
  - Pydantic model with action, category, rationale, impacts dict
  - Validation: impacts values in [-0.10, +0.10], at least one non-zero impact

- [ ] T009 Create `ExplorationRepository` in `src/synth_lab/repositories/exploration_repository.py`
  - Methods: create_exploration, update_exploration, get_by_id, create_node, update_node_status
  - Methods: get_nodes_by_exploration, get_frontier_nodes (status=active), get_path_to_node (recursive CTE)
  - Methods: count_nodes_by_status, get_best_node_by_success_rate

- [ ] T010 [P] Create `ActionCatalog` service in `src/synth_lab/services/exploration/action_catalog.py`
  - Load categories from `data/action_catalog.json`
  - Methods: get_categories, get_category_by_id, validate_category, get_prompt_context

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Iniciar Exploracao (Priority: P1)

**Goal**: PM can start exploration from experiment with baseline analysis, defining goal and config

**Independent Test**: Create exploration from experiment with analysis baseline, verify root node created with baseline results

### Unit Tests for US1

- [ ] T011 [P] [US1] Unit test for Exploration entity validation in `tests/unit/domain/test_exploration.py`
  - Test Goal validation (metric=success_rate, operator>=, value 0-1)
  - Test ExplorationConfig defaults and constraints

- [ ] T012 [P] [US1] Unit test for ExplorationRepository in `tests/unit/repositories/test_exploration_repository.py`
  - Test create_exploration, get_by_id, update_exploration
  - Test create_node, get_frontier_nodes

### Implementation for US1

- [ ] T013 [US1] Create `ExplorationService.start_exploration()` in `src/synth_lab/services/exploration/exploration_service.py`
  - Accept experiment_id, goal_value, optional config params
  - Validate experiment has scorecard_data (FR-003)
  - Validate experiment has at least one completed AnalysisRun (FR-003)
  - Create Exploration entity with status=running
  - Create root ScenarioNode from baseline analysis results

- [ ] T014 [US1] Create `TreeManager` in `src/synth_lab/services/exploration/tree_manager.py`
  - Method: create_root_node(exploration, experiment, analysis_run) -> ScenarioNode
  - Extract scorecard_params from experiment.scorecard_data
  - Extract simulation_results from analysis_run.aggregated_outcomes

- [ ] T015 [US1] Create API schemas in `src/synth_lab/api/schemas/exploration.py`
  - ExplorationCreate (experiment_id, goal_value, beam_width?, max_depth?, max_llm_calls?, n_executions?, seed?)
  - ExplorationResponse (id, experiment_id, baseline_analysis_id, goal, config, status, current_depth, total_nodes, total_llm_calls, best_success_rate, started_at, completed_at)

- [ ] T016 [US1] Create `POST /api/explorations` endpoint in `src/synth_lab/api/routers/exploration.py`
  - Validate request, call ExplorationService.start_exploration()
  - Return 201 with ExplorationResponse
  - Error 404 if experiment not found, 422 if no scorecard or no baseline

- [ ] T017 [US1] Register exploration router in `src/synth_lab/api/main.py`

- [ ] T018 [US1] Handle edge case: goal already achieved at start
  - If root node success_rate >= goal_value, set status=goal_achieved immediately

**Checkpoint**: US1 complete - can start exploration and create root node from baseline

---

## Phase 4: User Story 2 - Gerar Propostas LLM (Priority: P1)

**Goal**: LLM generates 1-2 improvement proposals for each scenario in frontier

**Independent Test**: Send scenario to LLM, verify returns structured proposals with valid categories

### Unit Tests for US2

- [ ] T019 [P] [US2] Unit test for ActionProposal validation in `tests/unit/domain/test_action_proposal.py`
  - Test impacts range [-0.10, +0.10]
  - Test category validation against catalog
  - Test at least one non-zero impact required

- [ ] T020 [P] [US2] Unit test for ActionProposalService in `tests/unit/services/exploration/test_action_proposal_service.py`
  - Test prompt building with experiment context
  - Test response parsing and validation
  - Test error handling for invalid LLM responses

### Implementation for US2

- [ ] T021 [US2] Create `ActionProposalService` in `src/synth_lab/services/exploration/action_proposal_service.py`
  - Constructor: inject LLMClient, ActionCatalog
  - Method: generate_proposals(scenario_node, experiment) -> list[ActionProposal]
  - Use Phoenix tracing: `_tracer.start_as_current_span("generate_proposals")`

- [ ] T022 [US2] Implement prompt building in ActionProposalService
  - Build system prompt: Product & UX Strategist persona
  - Build user prompt: experiment name, hypothesis, current params, results, catalog context
  - Request JSON output with schema: [{action, category, rationale, impacts}]

- [ ] T023 [US2] Implement response parsing in ActionProposalService
  - Parse JSON response from LLM
  - Validate each proposal: category exists, impacts in range
  - Log and discard invalid proposals without stopping

- [ ] T024 [US2] Implement 30s timeout and retry logic
  - Timeout individual LLM calls at 30 seconds
  - Retry once on timeout, then mark as failed
  - Log errors with full context for debugging

- [ ] T025 [US2] Configure gpt-4.1-mini as initial model
  - Add model parameter to ActionProposalService
  - Default to gpt-4.1-mini, allow override via config

**Checkpoint**: US2 complete - can generate validated proposals from LLM

---

## Phase 5: User Story 3 - Traduzir Propostas em Cenarios (Priority: P1)

**Goal**: Each LLM proposal becomes a child scenario with applied impacts and new simulation results

**Independent Test**: Apply proposal impacts to parent scorecard, verify child params are updated and clamped

### Unit Tests for US3

- [ ] T026 [P] [US3] Unit test for TreeManager.expand_node in `tests/unit/services/exploration/test_tree_manager.py`
  - Test applying impacts to scorecard params
  - Test clamping values to [0, 1]
  - Test child node creation with correct depth and parent_id

- [ ] T027 [P] [US3] Unit test for async parallel execution in `tests/unit/services/exploration/test_parallel_expansion.py`
  - Test multiple sibling nodes expand in parallel
  - Test timeout handling for individual nodes

### Implementation for US3

- [ ] T028 [US3] Add `TreeManager.expand_node()` method
  - Apply proposal impacts to parent scorecard_params
  - Clamp resulting values to [0, 1] (FR-012)
  - Create ScenarioNode with action_applied, category, rationale, depth+1

- [ ] T029 [US3] Integrate simulation for child nodes
  - Call existing MonteCarloEngine to simulate child scenario
  - Store simulation_results in child node
  - Record execution_time_seconds

- [ ] T030 [US3] Implement async parallel expansion for sibling nodes
  - Method: expand_frontier(frontier_nodes) -> list[ScenarioNode]
  - Use asyncio.gather with return_exceptions=True
  - Global timeout of 120s for frontier expansion

- [ ] T031 [US3] Handle expansion failures gracefully
  - Mark node as expansion_failed if LLM or simulation fails
  - Continue with other nodes in frontier
  - Log detailed errors for debugging

**Checkpoint**: US3 complete - proposals become simulated child scenarios

---

## Phase 6: User Story 4 - Filtrar Pareto + Beam Search (Priority: P1)

**Goal**: After expansion, filter dominated scenarios and keep only K best via beam search

**Independent Test**: Given 5 scenarios, verify dominated ones removed and only K=3 best remain

### Unit Tests for US4

- [ ] T032 [P] [US4] Unit test for Pareto dominance in `tests/unit/services/exploration/test_pareto_filter.py`
  - Test A dominates B (A >= B all dims, A > B at least one)
  - Test non-dominated frontier identification
  - Test 3-dimensional comparison (success_rate, complexity, risk)

- [ ] T033 [P] [US4] Unit test for beam search selection in `tests/unit/services/exploration/test_pareto_filter.py`
  - Test selection by delta_success_rate (primary)
  - Test tiebreaker by accumulated risk (secondary)
  - Test K selection from larger set

### Implementation for US4

- [ ] T034 [US4] Create `ParetoFilter` in `src/synth_lab/services/exploration/pareto_filter.py`
  - Method: dominates(a: ScenarioNode, b: ScenarioNode) -> bool
  - Compare: success_rate (higher better), complexity (lower better), perceived_risk (lower better)

- [ ] T035 [US4] Add filter_dominated() method to ParetoFilter
  - Remove nodes that are dominated by any other node
  - Mark removed nodes as node_status=dominated
  - Return non-dominated frontier

- [ ] T036 [US4] Add beam_select() method to ParetoFilter
  - Sort by delta_success_rate vs parent (descending)
  - Tiebreaker: accumulated perceived_risk (ascending)
  - Return top K nodes

- [ ] T037 [US4] Implement pragmatic early filter (FR-017)
  - Discard immediately if: no success_rate increase AND (complexity increase OR risk increase)
  - Apply before full Pareto filter for efficiency

- [ ] T038 [US4] Integrate ParetoFilter into ExplorationService
  - After expanding frontier, apply filter_dominated
  - Then apply beam_select(K=beam_width)
  - Update node statuses in repository

**Checkpoint**: US4 complete - exploration maintains focused frontier via Pareto + beam search

---

## Phase 7: User Story 5 - Controlar Limites (Priority: P2)

**Goal**: Exploration respects depth, cost, and viability limits, terminating appropriately

**Independent Test**: Start exploration with max_depth=2, verify terminates after 2 levels

### Unit Tests for US5

- [ ] T039 [P] [US5] Unit test for termination conditions in `tests/unit/services/exploration/test_exploration_service.py`
  - Test goal_achieved when success_rate >= goal
  - Test depth_limit_reached when depth == max_depth
  - Test cost_limit_reached when llm_calls >= max_llm_calls
  - Test no_viable_paths when frontier is empty

### Implementation for US5

- [ ] T040 [US5] Implement `ExplorationService.run_iteration()` method
  - Get frontier nodes (status=active)
  - Generate proposals for each via ActionProposalService
  - Expand nodes and run simulations
  - Apply Pareto filter and beam search
  - Update exploration stats (current_depth, total_nodes, total_llm_calls)

- [ ] T041 [US5] Implement termination checks in run_iteration
  - Check goal_achieved: any node success_rate >= goal_value
  - Check depth_limit_reached: current_depth >= max_depth
  - Check cost_limit_reached: total_llm_calls >= max_llm_calls
  - Check no_viable_paths: frontier empty after filtering

- [ ] T042 [US5] Create `POST /api/explorations/{id}/iterate` endpoint
  - Execute single iteration for debugging/manual control
  - Return IterationResultResponse with stats

- [ ] T043 [US5] Implement automatic iteration loop
  - In start_exploration or separate run_to_completion method
  - Loop run_iteration until termination condition met
  - Update best_success_rate after each iteration

- [ ] T044 [US5] Update exploration status on completion
  - Set completed_at timestamp
  - Mark winner node if goal_achieved
  - Set final status based on termination reason

**Checkpoint**: US5 complete - exploration runs to completion with proper limits

---

## Phase 8: User Story 6 - Visualizar Arvore (Priority: P2)

**Goal**: PM can retrieve full exploration tree and winning path

**Independent Test**: Export tree JSON with all nodes, relationships, and statuses

### Unit Tests for US6

- [ ] T045 [P] [US6] Unit test for tree retrieval in `tests/unit/repositories/test_exploration_repository.py`
  - Test get_nodes_by_exploration returns all nodes
  - Test get_path_to_node returns ancestor chain

### Implementation for US6

- [ ] T046 [US6] Create API schemas for tree visualization
  - ScenarioNodeResponse (all node fields)
  - ExplorationTreeResponse (exploration + nodes list + node_count_by_status)
  - PathStep (depth, action, category, rationale, success_rate, delta_success_rate)
  - WinningPathResponse (exploration_id, winner_node_id, path, total_improvement)

- [ ] T047 [US6] Create `GET /api/explorations/{id}` endpoint
  - Return ExplorationResponse with current status and stats

- [ ] T048 [US6] Create `GET /api/explorations/{id}/tree` endpoint
  - Return ExplorationTreeResponse with all nodes
  - Include node_count_by_status summary

- [ ] T049 [US6] Create `GET /api/explorations/{id}/winning-path` endpoint
  - Return 404 if no winner (status != goal_achieved)
  - Return WinningPathResponse with ordered path from root to winner
  - Calculate delta_success_rate for each step

- [ ] T050 [US6] Implement path reconstruction in repository
  - Use recursive CTE to get path from winner to root
  - Order by depth ascending
  - Calculate cumulative metrics along path

**Checkpoint**: US6 complete - full tree and winning path retrievable via API

---

## Phase 9: User Story 7 - Catalogo de Acoes (Priority: P2)

**Goal**: System provides action catalog to anchor LLM proposals

**Independent Test**: Verify catalog has 5 categories with examples and typical impacts

### Unit Tests for US7

- [ ] T051 [P] [US7] Unit test for ActionCatalog in `tests/unit/services/exploration/test_action_catalog.py`
  - Test loading from JSON file
  - Test get_categories returns all 5
  - Test validate_category accepts valid, rejects invalid

### Implementation for US7

- [ ] T052 [US7] Populate `data/action_catalog.json` with full content
  - Category: ux_interface (tooltips, visual feedback, etc.)
  - Category: onboarding (tutorials, checklists, etc.)
  - Category: flow (remove steps, smart defaults, etc.)
  - Category: communication (clear errors, confirmations, etc.)
  - Category: operational (feature flags, gradual rollout, etc.)
  - Each with 3-5 example actions and typical_impacts

- [ ] T053 [US7] Create API schema for catalog
  - ActionCategoryResponse (id, name, description, examples)
  - ActionExampleResponse (action, typical_impacts)
  - ActionCatalogResponse (version, categories)

- [ ] T054 [US7] Create `GET /api/action-catalog` endpoint
  - Return ActionCatalogResponse
  - Include version for cache invalidation

**Checkpoint**: US7 complete - action catalog available via API

---

## Phase 10: Integration & Polish

**Purpose**: End-to-end testing and cross-cutting concerns

- [ ] T055 [P] Integration test: full exploration flow in `tests/integration/test_exploration_flow.py`
  - Start exploration with mock experiment and analysis
  - Run iterations until goal achieved or limit reached
  - Verify tree structure and winning path

- [ ] T056 [P] Contract tests for all endpoints in `tests/contract/test_exploration_api.py`
  - Test POST /api/explorations
  - Test GET /api/explorations/{id}
  - Test GET /api/explorations/{id}/tree
  - Test GET /api/explorations/{id}/winning-path
  - Test POST /api/explorations/{id}/iterate
  - Test GET /api/action-catalog

- [ ] T057 Validate quickstart.md examples work end-to-end
  - Run curl examples from quickstart.md
  - Verify responses match documented format

- [ ] T058 Add logging throughout exploration service
  - Log start/end of exploration
  - Log each iteration with stats
  - Log LLM calls with tracing IDs

- [ ] T059 Performance validation
  - Verify depth=3, beam_width=3 completes in <5 minutes (SC-001)
  - Profile and optimize if needed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - start immediately
- **Phase 2 (Foundational)**: Depends on Setup - BLOCKS all user stories
- **Phases 3-9 (User Stories)**: All depend on Phase 2 completion
  - US1-US4 (P1) should complete before US5-US7 (P2)
  - Within same priority, stories can proceed in parallel if staffed
- **Phase 10 (Polish)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (Iniciar Exploracao)**: Foundation only - can start immediately after Phase 2
- **US2 (Gerar Propostas LLM)**: Foundation only - can run parallel with US1
- **US3 (Traduzir Propostas)**: Requires US2 (needs proposals to translate)
- **US4 (Filtrar Pareto)**: Requires US3 (needs child nodes to filter)
- **US5 (Controlar Limites)**: Requires US1, US2, US3, US4 (full iteration loop)
- **US6 (Visualizar Arvore)**: Requires US1 (needs exploration and nodes to exist)
- **US7 (Catalogo de Acoes)**: Foundation only - can run parallel with US1

### Critical Path

```
Phase 1 → Phase 2 → US1 → US2 → US3 → US4 → US5 → Phase 10
                  ↘ US6 (parallel after US1)
                  ↘ US7 (parallel after Phase 2)
```

### Parallel Opportunities

Within each phase, tasks marked [P] can run in parallel:
- T002, T003 (Setup)
- T006, T007, T008, T010 (Foundational entities)
- T011, T012 (US1 tests)
- T019, T020 (US2 tests)
- T026, T027 (US3 tests)
- T032, T033 (US4 tests)
- T055, T056 (Integration tests)

---

## Implementation Strategy

### MVP First (US1-US4 only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete US1: Can start exploration
4. Complete US2: Can generate LLM proposals
5. Complete US3: Can translate to child scenarios
6. Complete US4: Can filter and select best
7. **VALIDATE**: Manual iteration via API works
8. Deploy/demo MVP

### Full Feature Delivery

1. MVP complete (US1-US4)
2. Add US5: Automatic iteration with limits
3. Add US6: Tree visualization
4. Add US7: Action catalog API
5. Complete Phase 10: Integration tests and polish
6. Final validation against quickstart.md

---

## Notes

- All LLM calls MUST use Phoenix tracing
- All database queries MUST use parameterized SQL (no string interpolation)
- Router endpoints only do: request → service → response
- Business logic stays in services, never in routers
- Reuse existing MonteCarloEngine and SimulationService from spec 016
- Use async/parallel execution for sibling nodes (asyncio.gather)
- Default model: gpt-4.1-mini with 30s timeout
