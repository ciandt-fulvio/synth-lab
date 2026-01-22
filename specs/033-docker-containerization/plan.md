# Implementation Plan: Docker Containerization

**Branch**: `033-docker-containerization` | **Date**: 2026-01-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/033-docker-containerization/spec.md`

## Summary

Containerize the complete synth-lab application for three deployment scenarios:
1. **Development** - Docker Compose with volume mounts for hot reload (frontend Vite, backend uvicorn --reload)
2. **Testing** - Docker Compose with production images (no volume mounts) for E2E and manual testing
3. **Production** - Railway deployment using the same Docker images as testing

The project already has partial Docker infrastructure (Dockerfile, docker-compose.e2e.yml, railway.toml). This plan consolidates and completes the containerization story.

## Technical Context

**Language/Version**: Python 3.13+ (backend), TypeScript 5.5+ / Node.js 20 (frontend)
**Primary Dependencies**: FastAPI 0.109+, React 18, Vite 6.3, SQLAlchemy 2.0+, TanStack Query 5.56
**Storage**: PostgreSQL 14+ (local container for dev/test, Railway PostgreSQL for prod)
**Testing**: pytest (backend), Playwright + Vitest (frontend)
**Target Platform**: Linux containers (Docker), Railway PaaS
**Project Type**: Web application (separate backend + frontend)
**Performance Goals**: Dev environment startup < 2 minutes, hot reload < 5 seconds
**Constraints**: Single command startup, production parity between test and prod images
**Scale/Scope**: Development team with local environments, Railway production deployment

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First Development | ✅ PASS | Docker configuration will be validated with tests before implementation |
| II. Fast Test Battery | ✅ PASS | No impact on fast test battery (< 5s) |
| III. Complete Test Battery Before PR | ✅ PASS | E2E tests will run in Docker environment |
| IV. Frequent Version Control Commits | ✅ PASS | Each Docker config file committed atomically |
| V. Simplicity and Code Quality | ✅ PASS | Single docker-compose.yml with profiles (not multiple files) |
| VI. Language | ✅ PASS | Config files in English, docs in Portuguese |
| VII. Architecture | ✅ PASS | No backend/frontend architecture changes |

**Gate Status**: ✅ PASSED - No violations, proceed to Phase 0

## Project Structure

### Documentation (this feature)

```text
specs/033-docker-containerization/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (N/A - no data model changes)
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (N/A - no API changes)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
# Existing structure (unchanged)
src/synth_lab/           # Backend Python code
├── api/                 # FastAPI routers
├── services/            # Business logic
├── repositories/        # Data access
├── infrastructure/      # Config, database, external clients
├── models/              # ORM models
└── alembic/             # Database migrations

frontend/                # Frontend TypeScript code
├── src/
│   ├── pages/           # Route pages
│   ├── components/      # UI components
│   ├── hooks/           # React Query hooks
│   └── services/        # API clients
└── Dockerfile           # Existing (will be updated)

# Docker configuration (new/updated)
docker/                  # Docker configuration directory
├── docker-compose.yml   # NEW: Main compose file with profiles (dev, test)
├── backend/
│   └── Dockerfile       # MOVE: From root Dockerfile.backend
├── frontend/
│   └── Dockerfile       # KEEP: frontend/Dockerfile (or move here)
└── postgres/
    └── init-scripts/    # NEW: Test data seeding scripts

Dockerfile               # KEEP: Simple backend Dockerfile for Railway
Dockerfile.backend       # DELETE: Merged into docker/backend/Dockerfile
docker-compose.e2e.yml   # DELETE: Replaced by docker-compose.yml --profile test
```

**Structure Decision**: Consolidate Docker configs into `docker/` directory with a single `docker-compose.yml` using profiles for dev/test modes. Keep root `Dockerfile` for Railway compatibility.

## Complexity Tracking

> No violations identified - no tracking needed.

## Existing Docker Assets Analysis

| File | Purpose | Action |
|------|---------|--------|
| `Dockerfile` | Backend (single-stage, Railway) | KEEP - used by railway.toml |
| `Dockerfile.backend` | Backend (multi-stage) | MERGE into docker/backend/Dockerfile |
| `frontend/Dockerfile` | Frontend (multi-stage) | KEEP - already well structured |
| `docker-compose.e2e.yml` | E2E testing environment | REPLACE with docker-compose.yml --profile test |
| `docker/docker-compose.postgres.yml` | PostgreSQL only | MERGE into main docker-compose.yml |
| `scripts/docker-entrypoint-backend.sh` | Backend init | KEEP - reuse for all environments |
| `.env.e2e` | E2E environment vars | RENAME to .env.docker.test |
| `.env.example` | Development template | ADD .env.docker.dev template |

## Implementation Phases

### Phase 0: Research ✅ COMPLETE

- [x] Docker Compose profiles best practices
- [x] Vite hot reload in Docker (volume mounts, polling)
- [x] uvicorn --reload in Docker
- [x] PostgreSQL healthcheck patterns
- [x] Railway Docker image deployment

**Output**: [research.md](./research.md)

### Phase 1: Design ✅ COMPLETE

- [x] docker-compose.yml with profiles (dev, test)
- [x] Environment variable strategy
- [x] Volume mount configuration for hot reload
- [x] Health check implementation
- [x] Database seeding scripts

**Outputs**:
- [data-model.md](./data-model.md) - N/A (no data model changes)
- [contracts/](./contracts/) - N/A (no API changes)
- [quickstart.md](./quickstart.md) - Usage documentation

### Phase 2: Tasks (via /speckit.tasks)

Ready to generate implementation tasks.

---

## Post-Design Constitution Check

*Re-evaluation after Phase 1 design completion.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First Development | ✅ PASS | Tests will validate Docker configs before production use |
| II. Fast Test Battery | ✅ PASS | Docker setup does not affect fast test execution |
| III. Complete Test Battery Before PR | ✅ PASS | E2E tests will use `--profile test` environment |
| IV. Frequent Version Control Commits | ✅ PASS | Plan calls for atomic commits per config file |
| V. Simplicity and Code Quality | ✅ PASS | Single docker-compose.yml with profiles vs multiple files |
| VI. Language | ✅ PASS | Config in English, quickstart.md in Portuguese |
| VII. Architecture | ✅ PASS | No changes to backend/frontend code architecture |

**Final Gate Status**: ✅ ALL PASSED - Ready for task generation

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Compose strategy | Single file + profiles | Avoids config drift |
| File watching | Polling (CHOKIDAR/WATCHFILES) | Only reliable method in Docker |
| Dockerfile location | Root for Railway, docker/ for local | Railway expects root path |
| PostgreSQL wait | depends_on + healthcheck | Ensures proper startup order |
| Test data isolation | Ephemeral volume in test profile | Clean state per test run |

## Next Steps

Run `/speckit.tasks` to generate implementation tasks based on this plan.
