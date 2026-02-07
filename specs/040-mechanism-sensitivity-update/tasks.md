# Tasks: Mechanism & Sensitivity Update

**Input**: Design documents from `/specs/040-mechanism-sensitivity-update/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Included — Constitution mandates TDD (Principle I: Test-First Development).

**Organization**: Tasks grouped by user story (P1 → P2) for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Branch creation and shared configuration

- [ ] T001 Create feature branch `040-mechanism-sensitivity-update` from main
- [ ] T002 Create YAML sensitivity rules config file in `src/synth_lab/config/sensitivity_rules.yaml` with 7 sensitivities, base values, and conditional rules for Brazilian population demographics (age, education, family composition, disabilities) as defined in data-model.md

**Checkpoint**: Branch exists, YAML config file is valid and loadable.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Domain entities that ALL user stories depend on. MUST complete before any story begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T003 [P] Rewrite `UserSensitivities` entity in `src/synth_lab/domain/entities/user_sensitivities.py` — replace 6 fields (risk_aversion, social_dependency, institutional_trust_level, habit_plasticity, learning_tolerance, social_influence) with 7 fields (risk_aversion, social_dependency, institutional_trust_level, habit_plasticity, friction_tolerance, pragmatism, digital_capability), all default 0.5, range [0,1]. Include validation block.
- [ ] T004 [P] Extend `FeatureMechanisms` entity in `src/synth_lab/domain/entities/feature_mechanisms.py` — add 3 new fields (valor_intrinseco, friccao_operacional, frequencia_de_uso), all default 0.0, range [0,1]. Update `has_any_mechanism()` to include new fields. Include validation block.
- [ ] T005 [P] Rewrite `EmergentState` entity in `src/synth_lab/domain/entities/emergent_state.py` — replace 4 deltas (perceived_risk_delta, initial_effort_delta, trust_barrier, social_barrier) with 9 states: 7 barriers (perceived_risk, trust_barrier, habit_resistance, learning_frustration, friction_burden, social_pressure, network_barrier) + 2 appeals (intrinsic_appeal, frequency_value). Keep top_contributors and raw_interactions metadata. Include validation block.
- [ ] T006 Fix all import references across the codebase that use old `UserSensitivities` field names (learning_tolerance → digital_capability, social_influence → removed). Files to update: `services/simulation/mechanism_interaction.py` (INTERACTION_PAIRS + validation block), `services/simulation/engine.py` (validation block at L540-564), `domain/entities/emergent_state.py` (validation block references), `domain/entities/simulation_attributes.py` (imports UserSensitivities), `gen_synth/simulation_attributes.py` (generates sensitivities). Fix any existing tests that reference old field names. **Note**: `frontend/src/types/simulation.ts` UserSensitivities interface uses old field names but is NOT updated here — sensitivity fields are only consumed by the backend simulation; the frontend type update is deferred. Frontend FeatureMechanisms type IS updated in T014b (new mechanism fields are used by MechanismEditor sliders).

**Checkpoint**: All 3 domain entities compile, validation blocks pass, existing code that imports them still works.

---

## Phase 3: User Story 1 — Synths Are Created With Derived Sensitivities (Priority: P1)

**Goal**: When a synth is generated, derive 7 sensitivities from demographic data via YAML rules and persist them.

**Independent Test**: Generate a synth and verify it contains all 7 sensitivities with values [0,1] derived from demographics, with metadata.

### Tests for User Story 1

> **Write tests FIRST, ensure they FAIL before implementation**

- [ ] T007 [P] [US1] Write unit tests for sensitivity deriver in `tests/unit/services/test_sensitivity_deriver.py` — test cases: load config, get_nested_value for deep paths, evaluate_condition for all operators (>=, <=, >, <, ==, contains, contains_any, in), derive young person (25yo tech), derive elderly person (65yo with disabilities), derive single parent, missing fields default gracefully, all 7 sensitivities present, values clamped [0,1], metadata includes version/config/rules. Use parametrized tests for age ranges. Edge case tests: `test_load_config_missing_file_raises` (FileNotFoundError or clear error), `test_load_config_malformed_yaml_raises` (invalid YAML syntax), `test_load_config_missing_version_raises` (YAML without version field), `test_metadata_reflects_specific_config_version` (verify _meta.derivation_version matches YAML version field). (30+ test cases)
- [ ] T008 [P] [US1] Write integration test in `tests/integration/test_synth_sensitivity_integration.py` — test that `assemble_synth()` produces a synth dict containing `sensitivities` key with all 7 fields and `_meta` with derivation_version.

### Implementation for User Story 1

- [ ] T009 [US1] Create sensitivity deriver service in `src/synth_lab/services/sensitivity_deriver.py` — implement `load_sensitivity_rules(config_name)`, `get_nested_value(data, field_path)`, `evaluate_condition(condition, synth_data)`, `derive_sensitivities(synth_data, config_name)`. Support numeric operators (>=, <=, >, <, ==) and string operators (contains, contains_any, in). Clamp final values to [0,1]. Return dict with 7 sensitivities + `_meta` (derivation_version, config_name, applied_rules). Include validation block.
- [ ] T010 [US1] Integrate sensitivity derivation into synth builder in `src/synth_lab/gen_synth/synth_builder.py` — after generating demographics/psychographics/disabilities, call `derive_sensitivities(synth_data)` and add result to `synth_data["sensitivities"]`. Ensure existing synth schema is not broken.
- [ ] T011 [US1] Run all US1 tests and verify they pass — `pytest tests/unit/services/test_sensitivity_deriver.py tests/integration/test_synth_sensitivity_integration.py -v`

**Checkpoint**: Synths generated via `assemble_synth()` include 7 sensitivities + metadata. Young and elderly profiles produce meaningfully different sensitivity values (diff ≥ 0.15 average across 7 dimensions). All US1 tests pass.

---

## Phase 4: User Story 2 — Three New Feature Mechanisms Are Available (Priority: P1)

**Goal**: 9 mechanisms total (6 existing + 3 new) available for experiment configuration with backward compatibility.

**Independent Test**: Seed database, list mechanisms, verify 9 returned with correct options.

### Tests for User Story 2

- [ ] T012 [P] [US2] Write unit tests for extended FeatureMechanisms in `tests/unit/domain/test_feature_mechanisms.py` — test: 9 fields exist, defaults for new fields are 0.0, has_any_mechanism includes new fields, model_dump includes all 9 fields, backward compat (constructing with only 6 fields works, new fields default to 0.0), boundary values [0,1], rejection of values outside range.
- [ ] T013 [P] [US2] Write unit test for seed data in `tests/unit/scripts/test_seed_mechanisms.py` — test: MECHANISM_DEFINITIONS list has 9 entries, each has 5 options, valor_intrinseco ranges from "cosmetico"(0.0) to "transformador"(1.0), friccao_operacional ranges from "sem friccao"(0.0) to "friccao extrema"(1.0), frequencia_de_uso ranges from "rarissimo"(0.0) to "diario ou mais"(1.0).

### Implementation for User Story 2

- [ ] T014 [US2] Add 3 new mechanism definitions to seed script in `scripts/seed_mechanisms.py` — add valor_intrinseco (5 options: cosmético→transformador), friccao_operacional (5 options: sem fricção→fricção extrema), frequencia_de_uso (5 options: raríssimo→diário ou mais) to MECHANISM_DEFINITIONS list, matching labels/values from data-model.md and spec reference document.
- [ ] T014b [US2] Update frontend types and components for 3 new mechanisms — (a) Add 3 new fields to `FeatureMechanisms` interface in `frontend/src/types/simulation.ts` (valor_intrinseco, friccao_operacional, frequencia_de_uso, all `number`), (b) Add 3 new entries to `MECHANISM_CONFIGS` array in `frontend/src/components/experiments/MechanismEditor.tsx` with label, description, example (follow existing pattern), (c) Add 3 new keys to `DEFAULT_MECHANISMS` in same file (default 0). **Note**: `NarrativeMechanismEditor.tsx`, hooks, services and API are fully dynamic and need NO changes — they load mechanisms from the database.
- [ ] T015 [US2] Run all US2 tests and verify they pass — `pytest tests/unit/domain/test_feature_mechanisms.py tests/unit/scripts/test_seed_mechanisms.py -v`

**Checkpoint**: FeatureMechanisms has 9 fields. Seed script defines 9 mechanisms with 45 options total. Constructing FeatureMechanisms with only original 6 fields works (new default to 0.0). Frontend shows 9 mechanism sliders. Narrative mechanism system dynamically picks up new mechanisms from database. All US2 tests pass.

---

## Phase 5: User Story 3 — Emergent States Drive Monte Carlo Probability (Priority: P2)

**Goal**: New simulation engine calculates 9 emergent states from 9 mechanisms × 7 sensitivities (using Beta distributions) and adjusts adoption probability.

**Independent Test**: Run simulation for same feature with young/tech-savvy vs elderly populations — adoption rates differ by ≥ 10 percentage points.

### Tests for User Story 3

> **Write tests FIRST, ensure they FAIL before implementation**

- [ ] T016 [P] [US3] Write unit tests for emergent calculator in `tests/unit/services/simulation/test_emergent_calculator.py` — test cases: perceived_risk formula (irreversibility × risk_aversion), trust_barrier formula (institutional_trust × (1 − institutional_trust_level)), habit_resistance, learning_frustration, friction_burden, social_pressure, network_barrier, intrinsic_appeal (valor_intrinseco × pragmatism), frequency_value (frequencia_de_uso × pragmatism), all zeros → all zeros, top_contributors sorted by product, raw_interactions has 9 keys. Verify specific numeric values per spec FR-010.
- [ ] T017 [P] [US3] Write unit tests for feature Monte Carlo engine in `tests/unit/services/simulation/test_feature_monte_carlo.py` — test cases: Beta sampling (mean=0.0 stays 0.0, mean=0.5 ~Beta(7.5,7.5), mean=0.8 ~Beta(12,3), mean=1.0 stays 1.0), adoption probability formula (base 0.5 − barriers×0.15 + appeals×0.20), clamping [0,1], high barriers reduce adoption below 0.5, high appeals increase adoption above 0.5, reproducibility with same seed, performance (100×100 < 1s), different sensitivity profiles produce >10% adoption difference, all mechanisms at 0.0 → 50% base adoption, outcome is binary (adopted/not_adopted), SC-005 validation (same synth population: feature with high barriers + low appeal vs feature with low barriers + high appeal → adoption differs by ≥ 20%), synth without sensitivities derives on-demand.
- [ ] T018 [P] [US3] Write integration test in `tests/integration/test_simulation_sensitivity_integration.py` — test: create young tech-savvy synths (with derived sensitivities) and elderly synths, run simulation for same feature with high mechanisms, verify adoption rates differ by ≥ 10pp. Also test: synth without persisted sensitivities → derives on-demand, synth with pre-persisted sensitivities → uses stored.

### Implementation for User Story 3

- [ ] T019 [US3] Create emergent state calculator in `src/synth_lab/services/simulation/emergent_calculator.py` — implement `calculate_emergent_state(mechanisms: FeatureMechanisms, sensitivities: UserSensitivities) -> EmergentState` with 9 formulas per FR-010: 5 resistance barriers (mechanism × (1 − sensitivity)), 2 affinity barriers (mechanism × sensitivity), 2 appeals (mechanism × sensitivity). Track top 3 contributors and all raw interactions. Include validation block.
- [ ] T020 [US3] Create feature Monte Carlo engine in `src/synth_lab/services/simulation/feature_monte_carlo.py` — implement `FeatureMonteCarloEngine` with: `_sample_mechanisms()` using Beta(mean×15, (1-mean)×15) per mechanism (skip if mean=0.0 or mean=1.0, returning the mean directly), `_calculate_adoption_probability()` with base=0.5 − sum(barriers)×0.15 + sum(appeals)×0.20 clamped [0,1], `run_simulation(synths, mechanisms, n_executions)` that iterates synths × executions, samples mechanisms from Beta, calculates emergent states, samples Bernoulli(prob) for adoption. Support synths with or without pre-persisted sensitivities (derive on-demand if missing). Return SimulationResults with per-synth adoption rates and aggregate. Include validation block.
- [ ] T021 [US3] Deprecate old simulation files — add deprecation notice docstring to `src/synth_lab/services/simulation/engine.py`, `src/synth_lab/services/simulation/probability.py`, `src/synth_lab/services/simulation/sample_state.py`, `src/synth_lab/services/simulation/mechanism_interaction.py`. Docstring format: `"""DEPRECATED (040): Use feature_monte_carlo.py and emergent_calculator.py instead."""`
- [ ] T022 [US3] Run all US3 tests and verify they pass — `pytest tests/unit/services/simulation/test_emergent_calculator.py tests/unit/services/simulation/test_feature_monte_carlo.py tests/integration/test_simulation_sensitivity_integration.py -v`

**Checkpoint**: 9 emergent states calculated correctly per FR-010. Beta sampling produces meaningful variance. Different synth profiles produce ≥ 10% adoption difference. Synths without sensitivities derive on-demand. All US3 tests pass.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Cleanup, validation across all stories, and final verification.

- [ ] T023 Run full test suite and fix any regressions — `pytest tests/ -v --tb=short`
- [ ] T024 Run linting and fix issues — `ruff check src/synth_lab/services/sensitivity_deriver.py src/synth_lab/services/simulation/emergent_calculator.py src/synth_lab/services/simulation/feature_monte_carlo.py src/synth_lab/domain/entities/user_sensitivities.py src/synth_lab/domain/entities/feature_mechanisms.py src/synth_lab/domain/entities/emergent_state.py src/synth_lab/config/ && ruff format --check .`
- [ ] T025 Validate success criteria — verify SC-001 through SC-007 from spec.md: (1) all new synths have 7 sensitivities, (2) sensitivity profiles differ by ≥ 0.15 average, (3) 9 mechanisms available with backward compat, (4) different populations differ by ≥ 10pp, (5) high barriers vs high appeal differ by ≥ 20%, (6) all tests pass, (7) existing 6-mechanism experiments unaffected.
- [ ] T026 Run quickstart.md validation — follow all steps in `specs/040-mechanism-sensitivity-update/quickstart.md` and verify each phase works end-to-end.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user stories
- **Phase 3 (US1 - Sensitivities)**: Depends on Phase 2
- **Phase 4 (US2 - Mechanisms)**: Depends on Phase 2 (independent of US1)
- **Phase 5 (US3 - Emergent + MC)**: Depends on Phase 2, Phase 3 (needs sensitivities), Phase 4 (needs 9 mechanisms)
- **Phase 6 (Polish)**: Depends on all prior phases

### User Story Dependencies

```
Phase 1: Setup
    ↓
Phase 2: Foundational (entities)
    ↓         ↓
Phase 3: US1    Phase 4: US2     (US1 and US2 can run in PARALLEL)
    ↓              ↓
    └──────┬───────┘
           ↓
    Phase 5: US3                  (depends on BOTH US1 and US2)
           ↓
    Phase 6: Polish
```

### Within Each User Story

1. Tests MUST be written and FAIL before implementation (TDD)
2. Domain entities before services
3. Services before integration
4. Core implementation before integration testing
5. Story complete before moving to next priority

### Parallel Opportunities

- **Phase 2**: T003, T004, T005 can run in parallel (different entity files)
- **Phase 3 + Phase 4**: US1 and US2 can run in parallel after Phase 2
- **Within US1**: T007 and T008 can run in parallel (test files)
- **Within US2**: T012 and T013 can run in parallel (test files)
- **Within US3**: T016, T017, T018 can run in parallel (test files)

---

## Parallel Example: User Story 1

```bash
# Launch all US1 tests in parallel (they write to different files):
Task: "Write unit tests for sensitivity deriver in tests/unit/services/test_sensitivity_deriver.py"
Task: "Write integration test in tests/integration/test_synth_sensitivity_integration.py"

# Then implement sequentially (deriver before builder integration):
Task: "Create sensitivity deriver service in src/synth_lab/services/sensitivity_deriver.py"
Task: "Integrate sensitivity derivation into synth builder in src/synth_lab/gen_synth/synth_builder.py"
```

## Parallel Example: Phase 2 (Foundational)

```bash
# Launch all entity rewrites in parallel (different files):
Task: "Rewrite UserSensitivities entity in src/synth_lab/domain/entities/user_sensitivities.py"
Task: "Extend FeatureMechanisms entity in src/synth_lab/domain/entities/feature_mechanisms.py"
Task: "Rewrite EmergentState entity in src/synth_lab/domain/entities/emergent_state.py"

# Then fix references sequentially (depends on all 3 above):
Task: "Fix all import references across the codebase"
```

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- Each user story is independently testable at its checkpoint
- Constitution requires TDD — write tests first, verify they fail
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- YAML rules file should be created early (T002) as it's referenced by many tests
