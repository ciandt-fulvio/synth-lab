# Tasks: User Login with Google SSO and Access Control

**Input**: Design documents from `/specs/034-user-login/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/auth-api.yaml

**⚠️ Test-First Development**: ALL tests MUST be written FIRST and MUST FAIL before implementation begins

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `src/synth_lab/` at repository root
- **Frontend**: `frontend/src/`
- **Tests**: `tests/` (unit, integration, e2e)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency setup

- [X] T001 Add backend dependencies (authlib, python-jose, slowapi) to pyproject.toml via `uv add`
- [X] T002 [P] Add frontend dependency (@react-oauth/google) to frontend/package.json via `npm install`
- [X] T003 [P] Create .env.example with OAuth and JWT environment variables
- [X] T004 [P] Update .gitignore to exclude .env.local files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Database Setup

- [X] T005 Create Alembic migration for users table in migrations/versions/
- [X] T006 [P] Create Alembic migration for experiment_shares table in migrations/versions/
- [X] T007 [P] Create Alembic migration for synth_group_shares table in migrations/versions/
- [X] T008 [P] Create Alembic migration to add owner_id to experiments table in migrations/versions/
- [X] T009 [P] Create Alembic migration to add owner_id to synth_groups table in migrations/versions/
- [ ] T010 Apply all migrations via `uv run alembic upgrade head`

### Infrastructure - Whitelist

- [ ] T011 Write unit test for whitelist email validation in tests/unit/test_whitelist.py (MUST FAIL)
- [ ] T012 Write unit test for whitelist domain validation in tests/unit/test_whitelist.py (MUST FAIL)
- [ ] T013 Implement whitelist parsing and validation in src/synth_lab/infrastructure/auth/whitelist.py

### Infrastructure - JWT Session Manager

- [ ] T014 Write unit test for JWT token creation in tests/unit/test_session_manager.py (MUST FAIL)
- [ ] T015 Write unit test for JWT token validation in tests/unit/test_session_manager.py (MUST FAIL)
- [ ] T016 Write unit test for JWT token expiration in tests/unit/test_session_manager.py (MUST FAIL)
- [ ] T017 Implement SessionManager in src/synth_lab/infrastructure/auth/session_manager.py

### Infrastructure - OAuth Client

- [ ] T018 Write unit test for OAuth client initialization in tests/unit/test_oauth_client.py (MUST FAIL)
- [ ] T019 Write unit test for OAuth authorization URL generation in tests/unit/test_oauth_client.py (MUST FAIL)
- [ ] T020 Implement OAuth client wrapper in src/synth_lab/infrastructure/auth/oauth_client.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - First-time Login via Google (Priority: P1) 🎯 MVP

**Goal**: Users can authenticate via Google OAuth, whitelisted users get access, user accounts are auto-created

**Independent Test**: Navigate to login page → click Google sign-in → complete OAuth → verify authenticated session with user data

### Tests for User Story 1 (Test-First Development - WRITE FIRST) ⚠️

> **CRITICAL: Write ALL tests in this section FIRST, ensure they FAIL before ANY implementation**

#### Unit Tests (Fast Battery < 5s)

- [X] T021 [P] [US1] Write unit test for User entity validation in tests/unit/test_user_entity.py (MUST FAIL)
- [X] T022 [P] [US1] Write unit test for UserRepository.create() in tests/unit/test_user_repository.py (MUST FAIL)
- [X] T023 [P] [US1] Write unit test for UserRepository.get_by_email() in tests/unit/test_user_repository.py (MUST FAIL)
- [X] T024 [P] [US1] Write unit test for UserRepository.get_by_google_id() in tests/unit/test_user_repository.py (MUST FAIL)
- [X] T025 [P] [US1] Write unit test for AuthService.create_user_from_google() in tests/unit/test_auth_service.py (MUST FAIL)
- [X] T026 [P] [US1] Write unit test for AuthService.validate_whitelist() in tests/unit/test_auth_service.py (MUST FAIL)
- [X] T027 [P] [US1] Write unit test for AuthService.handle_oauth_callback() in tests/unit/test_auth_service.py (MUST FAIL)

#### Integration Tests (Slow Battery)

- [X] T028 [P] [US1] Write integration test for complete OAuth flow in tests/integration/test_auth_flow.py (MUST FAIL)
- [X] T029 [P] [US1] Write integration test for whitelist rejection in tests/integration/test_auth_flow.py (MUST FAIL)
- [X] T030 [P] [US1] Write integration test for domain whitelist match in tests/integration/test_auth_flow.py (MUST FAIL)

#### Contract Tests

- [X] T031 [P] [US1] Write contract test for GET /auth/login endpoint in tests/contract/test_auth_api.py (MUST FAIL)
- [X] T032 [P] [US1] Write contract test for GET /auth/callback endpoint in tests/contract/test_auth_api.py (MUST FAIL)
- [X] T033 [P] [US1] Write contract test for GET /auth/me endpoint in tests/contract/test_auth_api.py (MUST FAIL)
- [X] T034 [P] [US1] Write contract test for POST /auth/logout endpoint in tests/contract/test_auth_api.py (MUST FAIL)

#### E2E Tests

- [X] T035 [US1] Write E2E test for full login flow in tests/e2e/test_login_flow.py (MUST FAIL)

### Implementation for User Story 1 (ONLY AFTER ALL TESTS ARE WRITTEN AND FAILING)

**⚠️ GATE: DO NOT proceed with implementation until ALL tests above (T021-T035) are written and failing**

#### Backend - Domain Layer

- [X] T036 [US1] Implement User entity in src/synth_lab/domain/entities/user.py
- [X] T037 [US1] Implement UserRepository in src/synth_lab/repositories/user_repository.py

#### Backend - Service Layer

- [X] T038 [US1] Implement AuthService.create_user_from_google() in src/synth_lab/services/auth_service.py
- [X] T039 [US1] Implement AuthService.validate_whitelist() in src/synth_lab/services/auth_service.py
- [X] T040 [US1] Implement AuthService.handle_oauth_callback() in src/synth_lab/services/auth_service.py
- [X] T041 [US1] Implement AuthService.get_current_user() in src/synth_lab/services/auth_service.py
- [X] T042 [US1] Implement AuthService.logout() in src/synth_lab/services/auth_service.py

#### Backend - API Layer

- [X] T043 [US1] Implement GET /auth/login endpoint in src/synth_lab/api/routers/auth.py
- [X] T044 [US1] Implement GET /auth/callback endpoint in src/synth_lab/api/routers/auth.py
- [X] T045 [US1] Implement GET /auth/me endpoint in src/synth_lab/api/routers/auth.py
- [X] T046 [US1] Implement POST /auth/logout endpoint in src/synth_lab/api/routers/auth.py
- [X] T047 [US1] Register auth router in src/synth_lab/api/main.py

#### Backend - Middleware

- [X] T048 [US1] Implement authentication middleware in src/synth_lab/infrastructure/middleware/auth_middleware.py
- [X] T049 [US1] Add auth middleware to FastAPI app in src/synth_lab/api/main.py

#### Frontend - Services

- [X] T050 [P] [US1] Implement authService.login() in frontend/src/services/authService.ts
- [X] T051 [P] [US1] Implement authService.getCurrentUser() in frontend/src/services/authService.ts
- [X] T052 [P] [US1] Implement authService.logout() in frontend/src/services/authService.ts

#### Frontend - Hooks

- [X] T053 [US1] Implement useAuth hook in frontend/src/hooks/useAuth.ts

#### Frontend - Components

- [X] T054 [P] [US1] Implement GoogleLoginButton component in frontend/src/components/auth/GoogleLoginButton.tsx
- [X] T055 [P] [US1] Implement ProtectedRoute component in frontend/src/components/auth/ProtectedRoute.tsx

#### Frontend - Pages

- [X] T056 [US1] Implement LoginPage in frontend/src/pages/LoginPage.tsx
- [X] T057 [US1] Add routes for LoginPage and protected routes in frontend/src/App.tsx

#### Validation

- [ ] T058 [US1] Run all US1 unit tests - verify ALL pass
- [ ] T059 [US1] Run all US1 integration tests - verify ALL pass
- [ ] T060 [US1] Run all US1 contract tests - verify ALL pass
- [ ] T061 [US1] Run all US1 E2E tests - verify ALL pass
- [ ] T062 [US1] Manual test: Complete full OAuth flow from login page to authenticated app

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (MVP ready!)

---

## Phase 4: User Story 2 - Create Owned Experiment (Priority: P1) 🎯 MVP

**Goal**: Authenticated users can create experiments that are automatically assigned to them as owner

**Independent Test**: Login → create experiment → verify experiment appears in "My Experiments" with current user as owner

### Tests for User Story 2 (Test-First Development - WRITE FIRST) ⚠️

> **CRITICAL: Write ALL tests in this section FIRST, ensure they FAIL before ANY implementation**

#### Unit Tests (Fast Battery < 5s)

- [X] T063 [P] [US2] Write unit test for adding owner_id to Experiment entity in tests/unit/test_experiment_entity.py (MUST FAIL)
- [X] T064 [P] [US2] Write unit test for adding owner_id to SynthGroup entity in tests/unit/test_synth_group_entity.py (MUST FAIL)
- [X] T065 [P] [US2] Write unit test for PermissionService.can_access_experiment() in tests/unit/test_permission_service.py (MUST FAIL)
- [X] T066 [P] [US2] Write unit test for PermissionService.can_edit_experiment() in tests/unit/test_permission_service.py (MUST FAIL)
- [X] T067 [P] [US2] Write unit test for PermissionService.can_access_synth_group() in tests/unit/test_permission_service.py (MUST FAIL)

#### Integration Tests (Slow Battery)

- [X] T068 [P] [US2] Write integration test for creating experiment with owner in tests/integration/test_experiment_ownership.py (MUST FAIL)
- [X] T069 [P] [US2] Write integration test for creating synth_group with owner in tests/integration/test_synth_group_ownership.py (MUST FAIL)
- [X] T070 [P] [US2] Write integration test for permission checks on owned resources in tests/integration/test_permissions.py (MUST FAIL)

### Implementation for User Story 2 (ONLY AFTER ALL TESTS ARE WRITTEN AND FAILING)

**⚠️ GATE: DO NOT proceed with implementation until ALL tests above (T063-T070) are written and failing**

#### Backend - Domain Layer

- [X] T071 [US2] Add owner_id field to Experiment entity in src/synth_lab/domain/entities/experiment.py
- [X] T072 [US2] Add owner_id field to SynthGroup entity in src/synth_lab/domain/entities/synth_group.py

#### Backend - Service Layer

- [X] T073 [US2] Implement PermissionService.can_access_experiment() in src/synth_lab/services/permission_service.py
- [X] T074 [US2] Implement PermissionService.can_edit_experiment() in src/synth_lab/services/permission_service.py
- [X] T075 [US2] Implement PermissionService.can_access_synth_group() in src/synth_lab/services/permission_service.py
- [X] T076 [US2] Implement PermissionService.can_edit_synth_group() in src/synth_lab/services/permission_service.py
- [X] T077 [US2] Update ExperimentService to set owner_id on create in src/synth_lab/services/experiment_service.py
- [X] T078 [US2] Update SynthGroupService to set owner_id on create in src/synth_lab/services/synth_group_service.py

#### Backend - API Layer

- [X] T079 [US2] Add permission checks to experiment endpoints in src/synth_lab/api/routers/experiments.py
- [X] T080 [US2] Add permission checks to synth_group endpoints in src/synth_lab/api/routers/synth_groups.py

#### Validation

- [ ] T081 [US2] Run all US2 unit tests - verify ALL pass
- [ ] T082 [US2] Run all US2 integration tests - verify ALL pass
- [ ] T083 [US2] Manual test: Create experiment and verify owner assignment

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Share Experiment with Another User (Priority: P2)

**Goal**: Experiment owners can share with other whitelisted users, automatically sharing associated synth_group

**Independent Test**: Create experiment as User A → share with User B → login as User B → verify access to experiment

### Tests for User Story 3 (Test-First Development - WRITE FIRST) ⚠️

> **CRITICAL: Write ALL tests in this section FIRST, ensure they FAIL before ANY implementation**

#### Unit Tests (Fast Battery < 5s)

- [X] T084 [P] [US3] Write unit test for ExperimentShare entity validation in tests/unit/test_experiment_share_entity.py (MUST FAIL)
- [X] T085 [P] [US3] Write unit test for SynthGroupShare entity validation in tests/unit/test_synth_group_share_entity.py (MUST FAIL)
- [X] T086 [P] [US3] Write unit test for ShareRepository.create_experiment_share() in tests/unit/test_share_repository.py (MUST FAIL)
- [X] T087 [P] [US3] Write unit test for ShareRepository.create_synth_group_share() in tests/unit/test_share_repository.py (MUST FAIL)
- [X] T088 [P] [US3] Write unit test for ShareRepository.revoke_experiment_share() in tests/unit/test_share_repository.py (MUST FAIL)
- [X] T089 [P] [US3] Write unit test for ShareRepository.get_experiment_shares() in tests/unit/test_share_repository.py (MUST FAIL)
- [X] T090 [P] [US3] Write unit test for PermissionService with shared experiments in tests/unit/test_permission_service.py (MUST FAIL)
- [X] T091 [P] [US3] Write unit test for share validation (no self-sharing) in tests/unit/test_share_repository.py (MUST FAIL)
- [X] T092 [P] [US3] Write unit test for share validation (whitelist check) in tests/unit/test_share_repository.py (MUST FAIL)

#### Integration Tests (Slow Battery)

- [X] T093 [P] [US3] Write integration test for sharing experiment in tests/integration/test_sharing.py (MUST FAIL)
- [X] T094 [P] [US3] Write integration test for automatic synth_group sharing in tests/integration/test_sharing.py (MUST FAIL)
- [X] T095 [P] [US3] Write integration test for accessing shared experiment in tests/integration/test_sharing.py (MUST FAIL)
- [X] T096 [P] [US3] Write integration test for revoking experiment access in tests/integration/test_sharing.py (MUST FAIL)
- [X] T097 [P] [US3] Write integration test for whitelist validation on share in tests/integration/test_sharing.py (MUST FAIL)

#### Contract Tests

- [X] T098 [P] [US3] Write contract test for POST /experiments/{id}/shares in tests/contract/test_sharing_api.py (MUST FAIL)
- [X] T099 [P] [US3] Write contract test for GET /experiments/{id}/shares in tests/contract/test_sharing_api.py (MUST FAIL)
- [X] T100 [P] [US3] Write contract test for DELETE /experiments/{id}/shares/{user_id} in tests/contract/test_sharing_api.py (MUST FAIL)

### Implementation for User Story 3 (ONLY AFTER ALL TESTS ARE WRITTEN AND FAILING)

**⚠️ GATE: DO NOT proceed with implementation until ALL tests above (T084-T100) are written and failing**

#### Backend - Domain Layer

- [X] T101 [P] [US3] Implement ExperimentShare entity in src/synth_lab/domain/entities/share.py
- [X] T102 [P] [US3] Implement SynthGroupShare entity in src/synth_lab/domain/entities/share.py

#### Backend - Repository Layer

- [X] T103 [US3] Implement ShareRepository.create_experiment_share() in src/synth_lab/repositories/share_repository.py
- [X] T104 [US3] Implement ShareRepository.create_synth_group_share() in src/synth_lab/repositories/share_repository.py
- [X] T105 [US3] Implement ShareRepository.get_experiment_shares() in src/synth_lab/repositories/share_repository.py
- [X] T106 [US3] Implement ShareRepository.get_synth_group_shares() in src/synth_lab/repositories/share_repository.py
- [X] T107 [US3] Implement ShareRepository.revoke_experiment_share() in src/synth_lab/repositories/share_repository.py
- [X] T108 [US3] Implement ShareRepository.get_experiment_share() in src/synth_lab/repositories/share_repository.py

#### Backend - Service Layer

- [X] T109 [US3] Update PermissionService to check shares in can_access_experiment()
- [X] T110 [US3] Update PermissionService to check shares in can_edit_experiment()
- [X] T111 [US3] Implement share_experiment() with automatic synth_group sharing in src/synth_lab/services/sharing_service.py
- [X] T112 [US3] Implement revoke_experiment_share() in service layer
- [X] T113 [US3] Implement list_experiment_shares() in service layer

#### Backend - API Layer

- [X] T114 [US3] Implement POST /experiments/{id}/shares endpoint in src/synth_lab/api/routers/auth.py
- [X] T115 [US3] Implement GET /experiments/{id}/shares endpoint in src/synth_lab/api/routers/auth.py
- [X] T116 [US3] Implement DELETE /experiments/{id}/shares/{user_id} endpoint in src/synth_lab/api/routers/auth.py

#### Validation

- [ ] T117 [US3] Run all US3 unit tests - verify ALL pass
- [ ] T118 [US3] Run all US3 integration tests - verify ALL pass
- [ ] T119 [US3] Run all US3 contract tests - verify ALL pass
- [ ] T120 [US3] Manual test: Share experiment and verify synth_group is auto-shared

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Share Synth Group Independently (Priority: P2)

**Goal**: Synth_group owners can share synth_groups independently of experiments

**Independent Test**: Create synth_group as User A → share with User B → login as User B → verify can select shared synth_group

### Tests for User Story 4 (Test-First Development - WRITE FIRST) ⚠️

> **CRITICAL: Write ALL tests in this section FIRST, ensure they FAIL before ANY implementation**

#### Unit Tests (Fast Battery < 5s)

- [X] T121 [P] [US4] Write unit test for independent synth_group sharing in tests/unit/test_share_repository.py (MUST FAIL)
- [X] T122 [P] [US4] Write unit test for PermissionService with shared synth_groups in tests/unit/test_permission_service.py (MUST FAIL)

#### Integration Tests (Slow Battery)

- [X] T123 [P] [US4] Write integration test for sharing synth_group independently in tests/integration/test_sharing.py (MUST FAIL)
- [X] T124 [P] [US4] Write integration test for revoking synth_group access in tests/integration/test_sharing.py (MUST FAIL)
- [X] T125 [P] [US4] Write integration test for independent revocation (experiment vs synth_group) in tests/integration/test_sharing.py (MUST FAIL)

#### Contract Tests

- [X] T126 [P] [US4] Write contract test for POST /synth-groups/{id}/shares in tests/contract/test_sharing_api.py (MUST FAIL)
- [X] T127 [P] [US4] Write contract test for GET /synth-groups/{id}/shares in tests/contract/test_sharing_api.py (MUST FAIL)
- [X] T128 [P] [US4] Write contract test for DELETE /synth-groups/{id}/shares/{user_id} in tests/contract/test_sharing_api.py (MUST FAIL)

### Implementation for User Story 4 (ONLY AFTER ALL TESTS ARE WRITTEN AND FAILING)

**⚠️ GATE: DO NOT proceed with implementation until ALL tests above (T121-T128) are written and failing**

#### Backend - Service Layer

- [X] T129 [US4] Update PermissionService to check synth_group shares in can_access_synth_group()
- [X] T130 [US4] Implement share_synth_group() independently in service layer
- [X] T131 [US4] Implement revoke_synth_group_share() in service layer
- [X] T132 [US4] Implement list_synth_group_shares() in service layer

#### Backend - API Layer

- [X] T133 [US4] Implement POST /synth-groups/{id}/shares endpoint in src/synth_lab/api/routers/auth.py
- [X] T134 [US4] Implement GET /synth-groups/{id}/shares endpoint in src/synth_lab/api/routers/auth.py
- [X] T135 [US4] Implement DELETE /synth-groups/{id}/shares/{user_id} endpoint in src/synth_lab/api/routers/auth.py

#### Validation

- [ ] T136 [US4] Run all US4 unit tests - verify ALL pass
- [ ] T137 [US4] Run all US4 integration tests - verify ALL pass
- [ ] T138 [US4] Run all US4 contract tests - verify ALL pass
- [ ] T139 [US4] Manual test: Share synth_group independently and verify experiments not shared

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T140 [P] Add error handling for OAuth failures with user-friendly messages
- [X] T141 [P] Add rate limiting to /auth/callback endpoint via slowapi
- [X] T142 [P] Add logging for all authentication attempts (success/failure)
- [X] T143 [P] Add logging for all sharing operations
- [ ] T144 [P] Update API documentation in OpenAPI spec
- [ ] T145 [P] Run complete test battery (all unit + integration + contract + e2e tests)
- [ ] T146 [P] Verify quickstart.md instructions work end-to-end
- [ ] T147 Code review and refactoring for code quality (<30 lines per function, <500 per file)
- [ ] T148 Security audit: verify HTTPS, HTTP-only cookies, CSRF protection
- [ ] T149 Performance testing: verify <500ms auth flow, <100ms permission checks
- [ ] T150 Create data migration script for existing experiments/synth_groups (assign owner_id)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User Story 1 (P1): Can start after Foundational - No dependencies on other stories ✅ MVP
  - User Story 2 (P1): Can start after Foundational - No dependencies on other stories ✅ MVP
  - User Story 3 (P2): Can start after Foundational - Depends on User entities from US1, ownership from US2
  - User Story 4 (P2): Can start after Foundational - Depends on User entities from US1, ownership from US2
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

```
US1 (First-time Login)
  ↓
US2 (Create Owned Experiment) - depends on US1 for User entity
  ↓
US3 (Share Experiment) - depends on US1 for User, US2 for ownership
  ↓
US4 (Share Synth Group) - depends on US1 for User, US2 for ownership
```

### Within Each User Story

**CRITICAL TDD Flow**:
1. **Tests FIRST** - Write ALL tests for the story (unit, integration, contract, e2e)
2. **Verify FAIL** - Run tests, ensure they all fail (red phase)
3. **Implementation** - Implement code to make tests pass (green phase)
4. **Validation** - Run all tests, ensure they all pass
5. **Refactor** - Clean up code while keeping tests green

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- **Within a user story's test phase**: All tests marked [P] can be written in parallel
- **Within a user story's implementation phase**: All tasks marked [P] can run in parallel
- **Across user stories**: Once Foundational completes:
  - US1 and US2 can start in parallel (both P1)
  - US3 and US4 can start in parallel after US1+US2 complete (both P2)

---

## Parallel Example: User Story 1 Tests

```bash
# Write all US1 tests in parallel (all MUST fail initially):
Task T021: "Write unit test for User entity validation"
Task T022: "Write unit test for UserRepository.create()"
Task T023: "Write unit test for UserRepository.get_by_email()"
Task T024: "Write unit test for UserRepository.get_by_google_id()"
Task T025: "Write unit test for AuthService.create_user_from_google()"
Task T026: "Write unit test for AuthService.validate_whitelist()"
Task T027: "Write unit test for AuthService.handle_oauth_callback()"

# Then verify ALL fail before proceeding to implementation
```

## Parallel Example: User Story 1 Implementation

```bash
# After tests fail, implement models in parallel:
Task T036: "Implement User entity"
Task T037: "Implement UserRepository"

# Then implement services:
Task T038: "Implement AuthService.create_user_from_google()"
Task T039: "Implement AuthService.validate_whitelist()"

# Then implement frontend in parallel with backend:
Task T050: "Implement authService.login()"
Task T051: "Implement authService.getCurrentUser()"
Task T054: "Implement GoogleLoginButton component"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T020) - CRITICAL BLOCKER
3. Complete Phase 3: User Story 1 (T021-T062) - Authentication
4. Complete Phase 4: User Story 2 (T063-T083) - Ownership
5. **STOP and VALIDATE**: Test US1+US2 independently
6. Deploy/demo if ready - users can login and create owned experiments

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready (T001-T020)
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!) (T021-T062)
3. Add User Story 2 → Test independently → Deploy/Demo (Enhanced MVP) (T063-T083)
4. Add User Story 3 → Test independently → Deploy/Demo (Collaboration v1) (T084-T120)
5. Add User Story 4 → Test independently → Deploy/Demo (Collaboration v2) (T121-T139)
6. Polish → Production ready (T140-T150)

### Parallel Team Strategy

With multiple developers (after Foundational phase completes):

**Round 1 (P1 Stories)**:
- Developer A: User Story 1 (T021-T062)
- Developer B: User Story 2 (T063-T083)

**Round 2 (P2 Stories, after Round 1 completes)**:
- Developer A: User Story 3 (T084-T120)
- Developer B: User Story 4 (T121-T139)

---

## Test-First Development Checklist

Before proceeding with ANY implementation task, verify:

- [ ] ALL tests for the current user story are written
- [ ] ALL tests have been run and FAIL (red phase)
- [ ] Test failure messages confirm what needs to be implemented
- [ ] Tests cover: unit (fast), integration (slow), contract, e2e

After completing implementation for a user story:

- [ ] ALL unit tests pass (fast battery < 5s)
- [ ] ALL integration tests pass (slow battery)
- [ ] ALL contract tests pass
- [ ] ALL e2e tests pass
- [ ] Manual testing confirms user story acceptance criteria met

---

## Notes

- **[P] tasks** = different files, no dependencies, can run in parallel
- **[Story] label** maps task to specific user story for traceability
- **Test-First is NON-NEGOTIABLE**: Tests MUST be written before implementation
- **Verify tests fail** before implementing to ensure they're testing the right thing
- **Each user story** should be independently completable and testable
- **Commit frequently**: After each test file, after each implementation file
- **Stop at checkpoints** to validate story independently
- **Fast tests (<5s)** run on every commit, slow tests run before PR

---

## Summary

- **Total Tasks**: 150
- **User Story 1 (P1)**: 42 tasks (T021-T062) - Authentication MVP
- **User Story 2 (P1)**: 21 tasks (T063-T083) - Ownership MVP
- **User Story 3 (P2)**: 37 tasks (T084-T120) - Experiment Sharing
- **User Story 4 (P2)**: 19 tasks (T121-T139) - Independent Synth Group Sharing
- **Setup + Foundation**: 20 tasks (T001-T020)
- **Polish**: 11 tasks (T140-T150)

**MVP Scope**: User Stories 1 + 2 (63 tasks total including setup/foundation)
**Full Feature**: All 4 user stories (139 tasks + 11 polish)

**Parallel Opportunities**:
- 87 tasks marked [P] can run in parallel within their phase
- User Stories 1+2 can run in parallel (both P1)
- User Stories 3+4 can run in parallel (both P2) after 1+2 complete

**Test Coverage**:
- 72 test tasks (48% of total) written BEFORE implementation
- All user stories have unit, integration, contract, and e2e tests
