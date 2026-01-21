# Tasks: Docker Containerization

**Input**: Design documents from `/specs/033-docker-containerization/`
**Prerequisites**: plan.md (required), spec.md (required), research.md

**Tests**: Not explicitly requested for this infrastructure feature. Manual validation is included in each user story.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `src/synth_lab/` at repository root
- **Frontend**: `frontend/src/`
- **Docker**: `docker/` directory for compose, `Dockerfile` at root for Railway

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create directory structure and consolidate existing Docker files

- [x] T001 Create docker directory structure at `docker/`
- [x] T002 [P] Create environment template at `docker/.env.dev` based on `.env.example`
- [x] T003 [P] Create test environment template at `docker/.env.test` based on `.env.e2e`
- [x] T004 [P] Create postgres init-scripts directory at `docker/postgres/init-scripts/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core Docker infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Create unified docker-compose.yml at `docker/docker-compose.yml` with base postgres service (no profile)
- [x] T006 Add health check configuration to postgres service in `docker/docker-compose.yml`
- [x] T007 Create shared Docker network configuration in `docker/docker-compose.yml`
- [x] T008 [P] Create test data seeding script at `docker/postgres/init-scripts/seed-test-data.sql`

**Checkpoint**: Base infrastructure ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Local Development with Hot Reload () 🎯 MVP

**Goal**: Developers can run the complete application stack locally using Docker with hot reload for both frontend and backend

**Independent Test**: Run `docker compose --profile dev up`, edit a source file, verify change appears without restart

### Implementation for User Story 1

- [x] T009 [US1] Create backend development Dockerfile at `docker/backend/Dockerfile.dev` with volume mount support
- [x] T010 [US1] Add backend-dev service to `docker/docker-compose.yml` with profile "dev"
- [x] T011 [US1] Configure uvicorn --reload with WATCHFILES_FORCE_POLLING in backend-dev service
- [x] T012 [US1] Add volume mounts for `./src:/app/src:cached` in backend-dev service
- [x] T013 [P] [US1] Create frontend development Dockerfile at `docker/frontend/Dockerfile.dev` with HMR support
- [x] T014 [US1] Add frontend-dev service to `docker/docker-compose.yml` with profile "dev"
- [x] T015 [US1] Configure Vite HMR with CHOKIDAR_USEPOLLING in frontend-dev service
- [x] T016 [US1] Add volume mounts for `./frontend:/app` and anonymous `/app/node_modules` in frontend-dev service
- [x] T017 [US1] Update `frontend/vite.config.ts` to support Docker HMR (host 0.0.0.0, hmr.clientPort)
- [x] T018 [US1] Add postgres-dev service to `docker/docker-compose.yml` with persistent volume and profile "dev"
- [x] T019 [US1] Configure depends_on with service_healthy condition for backend-dev on postgres-dev
- [x] T020 [US1] Add port mappings: frontend 8080, backend 8000, postgres 5432 in dev services
- [x] T021 [US1] Validate: Run `docker compose --profile dev up` and verify all services start
- [x] T022 [US1] Validate: Edit Python file in `src/` and verify uvicorn reloads
- [x] T023 [US1] Validate: Edit TypeScript file in `frontend/src/` and verify HMR works

**Checkpoint**: User Story 1 complete - developers can now use Docker for local development with hot reload

---

## Phase 4: User Story 2 - Isolated Testing Environment ()

**Goal**: QA and developers can run E2E tests in containerized environment using production build artifacts

**Independent Test**: Run `docker compose --profile test up`, execute E2E tests, tear down and verify clean state

### Implementation for User Story 2

- [x] T024 [US2] Add backend-test service to `docker/docker-compose.yml` using root `Dockerfile` (production build)
- [x] T025 [US2] Configure backend-test WITHOUT volume mounts (containerized files only)
- [x] T026 [US2] Add frontend-test service to `docker/docker-compose.yml` using `frontend/Dockerfile` (production build)
- [x] T027 [US2] Configure frontend-test WITHOUT volume mounts (containerized files only)
- [x] T028 [US2] Add postgres-test service to `docker/docker-compose.yml` with NO persistent volume (ephemeral)
- [x] T029 [US2] Configure postgres-test to run `seed-test-data.sql` on init
- [x] T030 [US2] Add test profile to all test services in `docker/docker-compose.yml`
- [x] T031 [US2] Configure depends_on with service_healthy condition for backend-test on postgres-test
- [x] T032 [US2] Add separate port mappings for test: frontend 8091, backend 8001, postgres 5433
- [x] T033 [US2] Create test network separate from dev network in `docker/docker-compose.yml`
- [x] T034 [US2] Update Makefile to add `test-e2e-docker` target using `--profile test`
- [x] T035 [US2] Validate: Run `docker compose --profile test up -d` and verify containers start with built images
- [x] T036 [US2] Validate: Run `docker compose --profile test down -v` and verify clean teardown

**Checkpoint**: User Story 2 complete - E2E tests can now run in isolated containerized environment

---

## Phase 5: User Story 3 - Production Deployment to Railway ()

**Goal**: Same Docker images used in test environment deploy to Railway production

**Independent Test**: Deploy to Railway staging, verify services connect, run smoke tests

### Implementation for User Story 3

- [x] T037 [P] [US3] Update root `Dockerfile` to ensure PORT environment variable is used
- [x] T038 [P] [US3] Update `frontend/Dockerfile` to ensure PORT environment variable is used
- [x] T039 [US3] Update `railway.toml` with health check configuration (healthcheckPath, timeout)
- [x] T040 [US3] Update `frontend/railway.toml` with health check and VITE_API_URL build arg
- [x] T041 [US3] Verify backend uses `os.getenv("PORT", 8000)` in `src/synth_lab/api/main.py`
- [x] T042 [US3] Verify frontend serve uses PORT in `frontend/Dockerfile` CMD
- [x] T043 [US3] Update `.github/workflows/deploy.yml` to build and deploy Docker images
- [ ] T044 [US3] Validate: Deploy to Railway staging and verify /health endpoint responds
- [ ] T045 [US3] Validate: Verify frontend connects to backend on Railway
- [ ] T046 [US3] Validate: Verify backend connects to Railway PostgreSQL

**Checkpoint**: User Story 3 complete - production deployments use same images as test environment

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Cleanup, documentation, and removal of deprecated files

- [x] T047 [P] Delete deprecated `Dockerfile.backend` (merged into docker/backend/Dockerfile.dev) - N/A: file doesn't exist
- [x] T048 [P] Delete deprecated `docker-compose.e2e.yml` (replaced by docker-compose.yml --profile test) - N/A: file doesn't exist
- [x] T049 [P] Delete deprecated `docker/docker-compose.postgres.yml` (merged into main compose) - DELETED
- [x] T050 [P] Rename `.env.e2e` to `.env.docker.test` for consistency - N/A: file doesn't exist
- [x] T051 Update `Makefile` with new Docker commands (dev-up, dev-down, test-up, test-down)
- [x] T052 Update `README.md` with Docker development section
- [x] T053 Run quickstart.md validation - N/A: file doesn't exist
- [x] T054 Create `docs/docker-development.md` with detailed Docker usage guide

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase
- **User Story 2 (Phase 4)**: Depends on Foundational phase (can run parallel to US1)
- **User Story 3 (Phase 5)**: Depends on Foundational phase (can run parallel to US1, US2)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational - Independent of US1 (uses different services)
- **User Story 3 (P3)**: Can start after Foundational - Benefits from US2 images but can test independently

### Within Each User Story

- Dockerfile creation before service definition
- Service definition before configuration
- Configuration before validation
- Validation confirms story is complete

### Parallel Opportunities

**Setup phase** (all T001-T004 can run in parallel):
- T002, T003, T004 marked [P] - different files

**User Story 1** - some parallel opportunities:
- T009 (backend Dockerfile) and T013 (frontend Dockerfile) can run in parallel
- Validation tasks (T021-T023) must be sequential after implementation

**User Story 3** - parallel opportunities:
- T037 (root Dockerfile) and T038 (frontend Dockerfile) can run in parallel

**Polish phase** (T047-T050 can run in parallel):
- All deletion/rename tasks are independent files

---

## Parallel Example: Setup Phase

```bash
# Launch all setup tasks together:
Task: "Create environment template at docker/.env.dev based on .env.example"
Task: "Create test environment template at docker/.env.test based on .env.e2e"
Task: "Create postgres init-scripts directory at docker/postgres/init-scripts/"
```

## Parallel Example: User Story 1 Dockerfiles

```bash
# Launch both Dockerfiles in parallel:
Task: "Create backend development Dockerfile at docker/backend/Dockerfile.dev with volume mount support"
Task: "Create frontend development Dockerfile at docker/frontend/Dockerfile.dev with HMR support"
```

---

### Recommended Execution Order

Since this is infrastructure work (not parallelizable by multiple developers):

1. **Day 1**: Setup (T001-T004) + Foundational (T005-T008)
2. **Day 2**: User Story 1 (T009-T023) - dev environment with hot reload
3. **Day 3**: User Story 2 (T024-T036) - test environment
4. **Day 4**: User Story 3 (T037-T046) - Railway production
5. **Day 5**: Polish (T047-T054) - cleanup and docs

---
