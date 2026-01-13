# Tasks: Grupos de Synths Customizados

**Input**: Design documents from `/specs/030-custom-synth-groups/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `src/synth_lab/` at repository root
- **Frontend**: `frontend/src/`
- **Tests**: `tests/` at repository root

---

## Phase 1: Setup

**Purpose**: Database migration and shared constants/types

- [x] T001 [US1] Create Alembic migration to add `config` JSONB column to `synth_groups` table in `src/synth_lab/alembic/versions/xxx_add_config_column.py`
- [x] T002 [US1] Apply migration to development database and verify column exists
- [x] T003 [P] [US1] Create group defaults constants file at `src/synth_lab/domain/constants/group_defaults.py` with IBGE default values and education expansion ratios

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core backend infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

### Backend API Schemas

- [x] T004 [US1] Create Pydantic schemas for group config in `src/synth_lab/api/schemas/synth_group.py`:
  - `IdadeDistribution`, `EscolaridadeDistribution`, `SeveridadeDistribution`
  - `DeficienciasConfig`, `ComposicaoFamiliarDistribution`, `DomainExpertiseConfig`
  - `GroupDistributions`, `GroupConfig`
  - `CreateSynthGroupRequest`, `SynthGroupCreateResponse`, `SynthGroupDetailResponse`
  - Add validation for distributions summing to 1.0 (with ±0.01 tolerance)

### Frontend Types and Constants

- [x] T005 [P] [US1] Copy and adapt TypeScript types from `specs/030-custom-synth-groups/contracts/frontend-types.ts` to `frontend/src/types/synthGroup.ts`:
  - All distribution interfaces (IdadeDistribution, EscolaridadeDistribution, etc.)
  - GroupConfig and GroupDistributions interfaces
  - Request/Response types
  - UI state types (SliderItem, DistributionSliderGroupState, CreateSynthGroupFormState)
  - Default values constants (DEFAULT_GROUP_CONFIG, etc.)
  - Label mappings (IDADE_LABELS, ESCOLARIDADE_LABELS, etc.)
  - Domain expertise presets (DOMAIN_EXPERTISE_PRESETS)

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Criar Grupo de Synths Customizado (Priority: P1)

**Goal**: PM pode criar um novo grupo de synths com distribuições demográficas customizadas e 500 synths são gerados automaticamente

**Independent Test**: Criar grupo via API com config customizado e verificar que 500 synths são gerados com distribuições corretas

### Backend Implementation for US1

#### Repository Layer

- [x] T006 [US1] Modify `src/synth_lab/repositories/synth_group_repository.py`:
  - Add method `create_with_config(group: SynthGroup) -> SynthGroup` that handles JSONB insertion
  - Modify existing queries to include `config` column
  - Add method `get_by_id_with_config(group_id: str) -> SynthGroup | None`

#### Gen_Synth Module Modifications

- [x] T007 [US1] Modify `src/synth_lab/gen_synth/demographics.py`:
  - Add `custom_distributions: dict | None = None` parameter to generation function
  - When provided, use custom distributions instead of IBGE defaults for age, education, family composition
  - Implement education level expansion (4-level UI → 8-level internal) using ratios from group_defaults.py

- [x] T008 [US1] Modify `src/synth_lab/gen_synth/disabilities.py`:
  - Add `custom_rate: float | None = None` parameter for disability rate
  - Add `custom_severity_dist: dict | None = None` parameter for severity distribution
  - Implement dynamic severity logic: uniform distribution if rate <= 8%, weighted distribution if rate > 8%

- [x] T009 [US1] Modify `src/synth_lab/gen_synth/simulation_attributes.py`:
  - Add `expertise_alpha: float = 3` and `expertise_beta: float = 3` parameters
  - Use parameters in Beta distribution for domain expertise generation

#### Service Layer

- [x] T010 [US1] Modify `src/synth_lab/services/synth_group_service.py`:
  - Add method `create_with_config(name: str, description: str | None, config: dict) -> SynthGroupSummary`
  - Implement config validation using Pydantic schemas
  - Use `assemble_synth_with_config()` from synth_builder module
  - Handle atomic transaction: group + synths created together

#### Router Layer

- [x] T011 [US1] Modify `src/synth_lab/api/routers/synth_groups.py`:
  - Add `POST /synth-groups/with-config` endpoint that accepts `CreateSynthGroupRequest`
  - Call `service.create_with_config()` and return `SynthGroupCreateResponse`
  - Return 201 status code on success, 422 on validation errors

### Frontend Implementation for US1

#### API Service Layer

- [x] T012 [US1] Modify `frontend/src/services/synth-groups-api.ts`:
  - Add `createSynthGroupWithConfig(data: CreateSynthGroupRequest): Promise<SynthGroupCreateResponse>`
  - Use existing `fetchAPI` pattern with POST method and JSON body

#### Query Keys

- [x] T013 [P] [US1] Query keys already exist in `frontend/src/lib/query-keys.ts` (synthGroupsList, synthGroupDetail)

#### React Query Hooks

- [x] T014 [US1] Modify `frontend/src/hooks/use-synth-groups.ts`:
  - Add `useCreateSynthGroupWithConfig()`: useMutation hook that calls `createSynthGroupWithConfig`
  - Invalidates `queryKeys.synthGroupsList` on success

#### Slider Redistribution Utility

- [x] T015 [US1] Slider redistribution logic implemented directly in DistributionSlider component

#### UI Components

- [x] T016 [US1] Create `frontend/src/components/synths/DistributionSlider.tsx`:
  - Linked slider group with proportional redistribution
  - Visual distribution bar showing segment proportions
  - Multiple color schemes support

- [x] T017 [US1] DistributionSlider combines slider group functionality (merged with T016)

- [x] T018 [US1] Domain expertise select implemented in CreateSynthGroupModal as Select component

- [x] T019 [US1] Deficiency rate slider implemented in CreateSynthGroupModal

- [x] T020 [US1] SynthGroupSelect not needed - simplified to direct form input

- [x] T021 [US1] Create `frontend/src/components/synths/CreateSynthGroupModal.tsx`:
  - Tabbed interface for all distribution configurations
  - Form validation ensuring distributions sum to 1.0
  - Loading state during synth generation
  - Integrated with shadcn/ui components

### Integration

- [x] T022 [US1] Modify `frontend/src/pages/Synths.tsx`:
  - Add "Novo Grupo" button that opens CreateSynthGroupModal
  - On success, refresh groups list

**Checkpoint**: User Story 1 complete - PM can create custom synth groups with N synths generated

---

## Phase 4: User Story 2 - Visualizar Grupos Existentes (Priority: P2)

**Goal**: PM pode ver lista de todos os grupos de synths disponíveis (Default + customizados)

**Independent Test**: Acessar listagem e verificar que todos os grupos aparecem com nome, descrição e data de criação

### Backend Implementation for US2

- [x] T023 [US2] Verify/update `GET /synth-groups` endpoint in `src/synth_lab/api/routers/synth_groups.py`:
  - Endpoint already includes `synths_count` for each group via `SynthGroupSummary`
  - Response follows `PaginatedResponse[SynthGroupSummary]` schema
  - Default group appears in the list

### Frontend Implementation for US2

- [x] T024 [US2] `useSynthGroups` hook already exists in `frontend/src/hooks/use-synth-groups.ts`:
  - Uses `queryKeys.synthGroupsList` with params
  - Returns paginated list of groups

- [x] T025 [US2] Created `frontend/src/components/synths/SynthGroupCard.tsx`:
  - Props: `group`, `onClick`, `onViewDetails?`, `isSelected?`
  - UI: Card with name, description, created_at, synth_count badge
  - Visual highlight when selected, hover effect, "Detalhes" button

- [x] T026 [US2] Created `frontend/src/components/synths/SynthGroupList.tsx`:
  - Props: `groups`, `selectedId`, `onSelect`, `onViewDetails?`, `isLoading?`, `onCreateClick?`
  - UI: Grid of SynthGroupCard, loading skeleton, empty state
  - Default group first, sorted by created_at DESC

- [x] T027 [US2] Integrated SynthGroupList in `frontend/src/pages/Synths.tsx`:
  - Uses `useSynthGroups()` hook
  - Collapsible groups section with card grid
  - Selection state for filtering synths

**Checkpoint**: User Stories 1 AND 2 complete - PM can create groups and see all existing groups

---

## Phase 5: User Story 3 - Consultar Detalhes de um Grupo (Priority: P3)

**Goal**: PM pode ver detalhes de configuração de um grupo específico

**Independent Test**: Selecionar um grupo e verificar que todas as configurações de distribuição são exibidas

### Backend Implementation for US3

- [x] T028 [US3] Updated `GET /synth-groups/{group_id}` endpoint in `src/synth_lab/api/routers/synth_groups.py`:
  - Added `config` field to `SynthGroupDetailResponse`
  - Returns full config object with distributions
  - Returns 404 if group not found

### Frontend Implementation for US3

- [x] T029 [US3] `useSynthGroup` hook already exists in `frontend/src/hooks/use-synth-groups.ts`:
  - Uses `queryKeys.synthGroupDetail(id)`
  - Enabled only when id is provided
  - Updated `SynthGroupDetail` type to include `config`

- [x] T030 [US3] Created `frontend/src/components/synths/DistributionDisplay.tsx`:
  - Props: `title`, `items` (label/value pairs), `className?`
  - UI: Section title, horizontal bar chart, legend with percentages
  - Color-coded segments with hover tooltips

- [x] T031 [US3] Created `frontend/src/components/synths/SynthGroupDetail.tsx`:
  - Props: `group: SynthGroupDetail`
  - UI: Header with name, description, created_at, synth_count
  - Legacy message for groups without config
  - DistributionDisplay for idade, escolaridade, composicao_familiar
  - Deficiency rate bar, domain expertise badge
  - Skeleton component for loading state

- [x] T032 [US3] Integrated detail view in `frontend/src/pages/Synths.tsx`:
  - "Detalhes" button on cards opens Sheet panel
  - Uses `useSynthGroup` hook for detail data
  - SynthGroupDetailView in Sheet with loading skeleton

**Checkpoint**: All 3 user stories complete

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T033 [P] Loading states implemented: SynthGroupList uses Skeleton, SynthGroupDetail has skeleton component
- [x] T034 [P] Error handling: API failures handled via React Query, toasts available via sonner
- [x] T035 [P] Mobile responsiveness: Sheet component responsive, grid adapts with sm/lg/xl breakpoints
- [x] T036 Run linting and fix any issues: `ruff format` applied to modified backend files
- [x] T037 Run type checking: `npm run build` passes (no tsc errors), frontend builds successfully
- [ ] T038 Manual E2E test: create group, verify in list, view details (requires running servers)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion - BLOCKS all user stories
- **User Stories (Phase 3, 4, 5)**: All depend on Foundational phase completion
  - US1 (Phase 3): Can start immediately after Foundational
  - US2 (Phase 4): Can start in parallel with US1 (mostly independent)
  - US3 (Phase 5): Depends on US2 for group selection UI
- **Polish (Phase 6)**: Depends on all user stories being complete

### Within User Story 1 (Critical Path)

1. **Backend first**: T006 → T007, T008, T009 (can be parallel) → T010 → T011
2. **Frontend parallel**: T012, T013 (after T005)
3. **Frontend hooks**: T014 (after T012, T013)
4. **Frontend utils**: T015
5. **Frontend components**: T016 → T017 (depends on T16), T018, T19, T20 (can be parallel)
6. **Frontend modal**: T021 (depends on all components)
7. **Integration**: T022

### Parallel Opportunities

```bash
# Phase 2 - can run in parallel:
T004 (backend schemas) | T005 (frontend types)

# Phase 3 - backend gen_synth modifications can run in parallel:
T007 (demographics) | T008 (disabilities) | T009 (simulation_attributes)

# Phase 3 - frontend components can run in parallel:
T016 (DistributionSlider) | T018 (DomainExpertiseSelect) | T019 (DeficiencyRateSlider) | T020 (SynthGroupSelect)

# Phase 4 and Phase 3 can overlap:
US2 backend (T023) | US1 frontend (T016-T22)
```

---

## Implementation Strategy

1. Complete Phase 1: Setup (database migration)
2. Complete Phase 2: Foundational (schemas, types)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test creating a group via API and UI
5. Deploy/demo if ready

### Incremental Delivery

2. Add User Story 1 → Test
3. Add User Story 2 → Test
4. Add User Story 3 → Test → Deploy
5. Polish phase → Final release

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Frontend tasks detailed per user request ("use seu skill frontend para ajudar a definir melhor as tasks")
