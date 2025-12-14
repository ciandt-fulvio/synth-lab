# Tasks: Gerar Synths Realistas

**Input**: Design documents from `/specs/001-generate-synths/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/synth-schema.json ✅

**Tests**: Tests are OPTIONAL for this feature - formal pytest tests are not required per constitution. All implementation files must include validation functions in `if __name__ == "__main__":` blocks.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure (scripts/, data/synths/, data/config/, data/schemas/)
- [X] T002 [P] Initialize pyproject.toml with dependencies (faker>=21.0.0, jsonschema>=4.20.0)
- [X] T003 [P] Create .gitignore with entries for venv/, data/synths/, .ipynb_checkpoints/
- [X] T004 [P] Create README.md with project overview and setup instructions

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Copy JSON Schema from specs/001-generate-synths/contracts/synth-schema.json to data/schemas/synth-schema.json
- [X] T006 [P] Create data/config/ibge_distributions.json with IBGE Censo 2022 + PNAD 2023 distributions (regions, age, race, education, income)
- [X] T007 [P] Create data/config/brazilian_names.json with Brazilian names by region and gender
- [X] T008 [P] Create data/config/occupations.json with CBO 2022 occupations list (~200 common occupations)
- [X] T009 [P] Create data/config/interests_hobbies.json with curated lists (valores ~30-50 items, interesses ~100 items, hobbies ~50-80 items based on TIM+USP research)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Gerar Synth Individual com Atributos Completos (Priority: P1) 🎯 MVP

**Goal**: Generate a single complete Synth with all demographic, psychographic, behavioral, and cognitive attributes saved as JSON

**Independent Test**: Execute the script to generate one Synth and validate that the JSON contains all mandatory fields with realistic values within expected domains (e.g., age 0-120, positive monthly income, valid enum values)

### Implementation for User Story 1

- [X] T010 [P] [US1] Create function `load_config_data()` to load all JSON config files from data/config/ in scripts/gen_synth.py
- [X] T011 [P] [US1] Create function `gerar_id(tamanho=6)` to generate 6-char alphanumeric ID using random and string libraries in scripts/gen_synth.py
- [X] T012 [P] [US1] Create function `generate_demographics(ibge_data)` to generate all demographic attributes using IBGE distributions in scripts/gen_synth.py
- [X] T013 [P] [US1] Create function `generate_name(demographics, names_data)` to generate Brazilian name based on region/gender in scripts/gen_synth.py
- [X] T014 [P] [US1] Create function `generate_big_five()` to generate personality traits with Normal(μ=50, σ=15) in scripts/gen_synth.py
- [X] T015 [P] [US1] Create function `generate_psychographics(big_five, config_data)` to generate valores, interesses, hobbies, inclinacao_politica, inclinacao_religiosa in scripts/gen_synth.py
- [X] T016 [P] [US1] Create function `generate_behavior(demographics)` to generate habitos_consumo, uso_tecnologia, padroes_midia, fonte_noticias, comportamento_compra, lealdade_marca, engajamento_redes_sociais in scripts/gen_synth.py
- [X] T017 [P] [US1] Create function `generate_disabilities()` to generate deficiencias using IBGE PNS 2019 distributions (8.4% with at least one) in scripts/gen_synth.py
- [X] T018 [P] [US1] Create function `generate_tech_capabilities(demographics, disabilities)` to generate alfabetizacao_digital, dispositivos, preferencias_acessibilidade, velocidade_digitacao, frequencia_internet, familiaridade_plataformas in scripts/gen_synth.py
- [X] T019 [P] [US1] Create function `generate_behavioral_biases()` to generate all 7 vieses with Normal(μ=50, σ=20) in scripts/gen_synth.py
- [X] T020 [US1] Create function `derive_archetype(demographics, big_five)` to generate arquetipo field automatically in scripts/gen_synth.py (depends on T012, T014)
- [X] T021 [US1] Create function `derive_description(synth_data)` to generate descricao field automatically in scripts/gen_synth.py (depends on T012-T019)
- [X] T022 [US1] Create function `derive_lifestyle(big_five)` to generate estilo_vida field from personality traits in scripts/gen_synth.py (depends on T014)
- [X] T023 [US1] Create function `generate_photo_link(name)` to generate link_photo using ui-avatars.com API in scripts/gen_synth.py (depends on T013)
- [X] T024 [US1] Create function `assemble_synth(all_attributes)` to combine all generated attributes into complete Synth dictionary in scripts/gen_synth.py (depends on T010-T023)
- [X] T025 [US1] Create function `validate_synth(synth_dict, schema_path)` to validate Synth against JSON Schema using jsonschema library in scripts/gen_synth.py
- [X] T026 [US1] Create function `save_synth(synth_dict, output_dir)` to save Synth as {id}.json in data/synths/ in scripts/gen_synth.py (depends on T024)
- [X] T027 [US1] Create main() function with argparse to accept --count parameter (default=1) and orchestrate single Synth generation in scripts/gen_synth.py (depends on T010-T026)
- [X] T028 [US1] Add if __name__ == "__main__": block to validate single Synth generation with real data (execute main() with count=1 and verify output) in scripts/gen_synth.py (depends on T027)

**Checkpoint**: At this point, User Story 1 should be fully functional - script can generate one complete, valid Synth and save it as JSON

---

## Phase 4: User Story 2 - Validar Schema JSON dos Synths (Priority: P2)

**Goal**: Ensure generated Synths follow a consistent and well-documented JSON Schema for integration with other tools

**Independent Test**: Load the JSON Schema in a validator (jsonschema library) and validate that generated Synths pass validation without errors, plus verify that the schema documents all domains and types

**Note**: JSON Schema was already created in Phase 2 (T005). This story focuses on validation infrastructure.

### Implementation for User Story 2

- [X] T029 [US2] Add CLI flag `--validate <file_path>` to validate a single Synth JSON file against schema in scripts/gen_synth.py
- [X] T030 [US2] Add CLI flag `--validate-all` to validate all Synths in data/synths/ directory against schema in scripts/gen_synth.py
- [X] T031 [US2] Enhance validate_synth() function to return detailed error messages with field path when validation fails in scripts/gen_synth.py (depends on T025)
- [X] T032 [US2] Create function `validate_batch(synths_dir, schema_path)` to validate multiple Synth files and report summary statistics in scripts/gen_synth.py
- [X] T033 [US2] Add validation success/failure logging with clear error messages in scripts/gen_synth.py (depends on T031)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - can generate Synths and validate them against schema

---

## Phase 5: User Story 3 - Gerar Batch de Synths Representativos (Priority: P3)

**Goal**: Generate 100+ Synths that represent Brazilian demographic diversity for testing marketing campaigns, with distributions matching IBGE data

**Independent Test**: Execute script with `--count 100` and validate that: (a) 100 valid JSON files are created, (b) aggregate demographic distribution approximates IBGE proportions (e.g., regional distribution, age distribution) within 10% margin of error

### Implementation for User Story 3

- [X] T034 [US3] Modify main() function to support batch generation loop for --count > 1 in scripts/gen_synth.py (depends on T027)
- [X] T035 [US3] Add progress indicator/logging for batch generation (e.g., "Generated 50/100 Synths...") in scripts/gen_synth.py (depends on T034)
- [X] T036 [US3] Implement ID uniqueness check to prevent duplicate IDs in batch generation in scripts/gen_synth.py (depends on T011, T034)
- [X] T037 [US3] Add CLI flag `--analyze` with options (region, age, all) to analyze demographic distribution of generated Synths in scripts/gen_synth.py
- [X] T038 [US3] Create function `analyze_regional_distribution(synths_dir)` to compare Synth regional distribution vs IBGE data with error calculation in scripts/gen_synth.py
- [X] T039 [US3] Create function `analyze_age_distribution(synths_dir)` to compare Synth age distribution vs IBGE pyramid with error calculation in scripts/gen_synth.py
- [ ] T040 [US3] Create function `analyze_income_distribution(synths_dir)` to compare Synth income distribution vs PNAD data in scripts/gen_synth.py
- [ ] T041 [US3] Create function `analyze_race_distribution(synths_dir)` to compare Synth race/ethnicity distribution vs IBGE data in scripts/gen_synth.py
- [X] T042 [US3] Add performance optimization for batch generation (target: 100 Synths in <2 minutes per SC-003) in scripts/gen_synth.py (depends on T034)
- [X] T043 [US3] Validate batch generation with 100 Synths and verify distributions are within 10% margin per SC-004 in if __name__ block in scripts/gen_synth.py (depends on T034, T038-T041)

**Checkpoint**: All three priority user stories should now be independently functional - can generate single Synth, validate schema, and generate batches with realistic distributions

---

## Phase 6: User Story 4 - Consultar Documentação dos Atributos (Priority: P4)

**Goal**: Provide clear documentation explaining each Synth attribute, its purpose, data type, valid domain, and examples for new users

**Independent Test**: Provide the documentation to a new user and measure if they can correctly interpret the meaning of each attribute in a generated Synth without needing additional support

### Implementation for User Story 4

- [ ] T044 [P] [US4] Create docs/synth_attributes.md with comprehensive documentation of all Synth fields in docs/synth_attributes.md
- [ ] T045 [US4] Document Identificação section (7 fields) with descriptions, types, examples in docs/synth_attributes.md (depends on T044)
- [ ] T046 [US4] Document Demografia section (14 fields) with IBGE sources, distributions, valid enums in docs/synth_attributes.md (depends on T044)
- [ ] T047 [US4] Document Psicografia section (8 fields) including Big Five explanation, valores source (Schwartz Theory), inclinacao_politica scale in docs/synth_attributes.md (depends on T044)
- [ ] T048 [US4] Document Comportamento section (9 fields) with practical examples for UX testing contexts in docs/synth_attributes.md (depends on T044)
- [ ] T049 [US4] Document Limitações Físicas e Cognitivas section (5 fields) with IBGE PNS 2019 prevalence data in docs/synth_attributes.md (depends on T044)
- [ ] T050 [US4] Document Capacidades Tecnológicas section (10 fields) with TIC Domicílios 2023 sources and correlation rules in docs/synth_attributes.md (depends on T044)
- [ ] T051 [US4] Document Vieses Comportamentais section (7 fields) with behavioral economics literature sources and UX implications in docs/synth_attributes.md (depends on T044)
- [ ] T052 [US4] Add usage examples section showing how to interpret Synth attributes for UX testing scenarios in docs/synth_attributes.md (depends on T045-T051)
- [ ] T053 [US4] Add cross-references to data-model.md, research.md, and JSON Schema in docs/synth_attributes.md (depends on T044)

**Checkpoint**: All user stories are complete - documentation is available for attribute interpretation

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T054 [P] Add CLI flag `--output <dir>` to specify custom output directory for generated Synths in scripts/gen_synth.py
- [ ] T055 [P] Add CLI flag `--quiet` for silent mode (minimal logging) in scripts/gen_synth.py
- [ ] T056 [P] Add CLI flag `--setup` to auto-create directory structure and sample config files in scripts/gen_synth.py
- [ ] T057 [P] Enhance error handling for missing config files with clear error messages in scripts/gen_synth.py
- [ ] T058 [P] Add performance benchmarking output (total time, Synths/second) in scripts/gen_synth.py
- [ ] T059 Validate all functions respect ≤25 line limit per constitution in scripts/gen_synth.py
- [ ] T060 Run validation with 1000 Synths to verify SC-004 (distribution within 10% IBGE) and SC-007 (60%+ psychographic variation)
- [ ] T061 Run validation with 10000 Synths to verify SC-005 (no duplicate IDs) and SC-010 (no memory failure/corruption)
- [ ] T062 Verify single Synth generation time is <5 seconds per SC-001
- [ ] T063 Run all quickstart.md usage examples to verify functionality
- [ ] T064 [P] Code cleanup: remove any debug print statements, ensure PEP 8 compliance in scripts/gen_synth.py
- [ ] T065 Final commit: "Feature 001-generate-synths complete - all user stories validated"

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories CAN proceed in parallel (different files within scripts/gen_synth.py as functions)
  - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Uses validation infrastructure from US1 (T025) but is independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Extends US1 with batch capabilities but is independently testable
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Pure documentation, no code dependencies

### Within Each User Story

**User Story 1 (US1)**:
- T010-T019 can run in parallel (different generator functions)
- T020-T023 depend on prior generators
- T024 depends on all generators (T010-T023)
- T025-T026 can run in parallel (validation vs save)
- T027 depends on all functions (T010-T026)
- T028 depends on T027 (validation block)

**User Story 2 (US2)**:
- T029-T030 can run in parallel (different CLI flags)
- T031 enhances T025 (must come after)
- T032-T033 can run in parallel

**User Story 3 (US3)**:
- T034 extends T027
- T035-T036 enhance T034
- T037-T041 can run in parallel (different analysis functions)
- T042-T043 depend on prior tasks

**User Story 4 (US4)**:
- T044 creates base file
- T045-T051 can run in parallel (documenting different sections)
- T052-T053 depend on T045-T051

### Parallel Opportunities

- **Phase 1**: T002, T003, T004 can run in parallel
- **Phase 2**: T006, T007, T008, T009 can run in parallel (different config files)
- **Phase 3 (US1)**: T010-T019 can run in parallel (different generator functions)
- **Phase 4 (US2)**: T029-T030 can run in parallel, T032-T033 can run in parallel
- **Phase 5 (US3)**: T037-T041 can run in parallel (different analysis functions)
- **Phase 6 (US4)**: T045-T051 can run in parallel (documenting different sections)
- **Phase 7**: T054-T058 can run in parallel, T064 can run in parallel with others

---

## Parallel Example: User Story 1 (Core Generators)

```bash
# Launch all core generator functions together:
Task: "Create function generate_demographics(ibge_data) in scripts/gen_synth.py"
Task: "Create function generate_name(demographics, names_data) in scripts/gen_synth.py"
Task: "Create function generate_big_five() in scripts/gen_synth.py"
Task: "Create function generate_psychographics(big_five, config_data) in scripts/gen_synth.py"
Task: "Create function generate_behavior(demographics) in scripts/gen_synth.py"
Task: "Create function generate_disabilities() in scripts/gen_synth.py"
Task: "Create function generate_tech_capabilities(demographics, disabilities) in scripts/gen_synth.py"
Task: "Create function generate_behavioral_biases() in scripts/gen_synth.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T009) - CRITICAL, blocks all stories
3. Complete Phase 3: User Story 1 (T010-T028)
4. **STOP and VALIDATE**: Test single Synth generation independently
   - Run: `uv run scripts/gen_synth.py --count 1`
   - Verify: Valid JSON file created in data/synths/ with all required fields
   - Verify: Passes JSON Schema validation
5. **MVP ACHIEVED** - Can generate one complete, valid Synth

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (T010-T028) → Test independently → **MVP Delivered!**
3. Add User Story 2 (T029-T033) → Test independently → Schema validation available
4. Add User Story 3 (T034-T043) → Test independently → Batch generation with distributions
5. Add User Story 4 (T044-T053) → Documentation complete
6. Polish (T054-T065) → Production ready
7. Each story adds value without breaking previous stories

### Single Developer Strategy (Sequential)

Recommended order for solo implementation:

1. **Week 1**: Setup + Foundational + US1 core (T001-T024)
2. **Week 1-2**: US1 validation + save (T025-T028) → **MVP Complete**
3. **Week 2**: US2 validation infrastructure (T029-T033)
4. **Week 2-3**: US3 batch generation (T034-T036)
5. **Week 3**: US3 distribution analysis (T037-T043)
6. **Week 3**: US4 documentation (T044-T053) - can do in parallel with US3
7. **Week 4**: Polish and performance optimization (T054-T065)

---

## Success Criteria Validation Checklist

After completing all tasks, verify the following success criteria from spec.md:

- [ ] **SC-001**: Single Synth generation completes in <5 seconds (run T062)
- [ ] **SC-002**: 100% of generated Synths pass JSON Schema validation (run T060)
- [ ] **SC-003**: Batch of 100 Synths generates in <2 minutes (run T043)
- [ ] **SC-004**: 1000 Synths have demographic distribution within 10% IBGE error (run T060)
- [ ] **SC-005**: No duplicate IDs in 10,000 generations (run T061)
- [ ] **SC-006**: 95% of new users can interpret attributes using docs only (manual user test with T044-T053 deliverable)
- [ ] **SC-007**: 60%+ psychographic variation within same demographics (run T060)
- [ ] **SC-008**: All generated names are valid Brazilian names (manual validation of samples)
- [ ] **SC-009**: 100% of Synths have all required fields non-null (run T060)
- [ ] **SC-010**: 10,000 Synths generation succeeds without memory failure (run T061)

---

## Notes

- [P] tasks = different files/functions, no dependencies - can run in parallel
- [Story] label (US1, US2, US3, US4) maps task to specific user story for traceability
- Each user story should be independently completable and testable
- All functions MUST include validation in `if __name__ == "__main__":` blocks per constitution
- All functions MUST respect ≤25 line limit per constitution (T059)
- Commit after each task or logical group of parallel tasks
- Stop at any checkpoint to validate story independently before proceeding
- **No formal pytest tests** - constitution requires validation functions instead
- Avoid: vague tasks, functions >25 lines, missing validation blocks
