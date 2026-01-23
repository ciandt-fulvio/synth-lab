# Implementation Plan: User Login with Google SSO and Access Control

**Branch**: `034-user-login` | **Date**: 2026-01-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/034-user-login/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement Google OAuth 2.0 authentication with email/domain whitelist access control. Users will authenticate exclusively via Google SSO, with automatic account creation on first login. All experiments and synth_groups will be assigned to owners, with sharing capabilities that allow collaboration. Administrators (identified via configuration file) can manage the whitelist through an admin interface. The implementation follows the existing synth-lab architecture using FastAPI, SQLAlchemy, React, and PostgreSQL.

## Technical Context

**Language/Version**: Python 3.13+ (backend), TypeScript 5.5+ (frontend)
**Primary Dependencies**:
- Backend: FastAPI 0.109+, SQLAlchemy 2.0+, Pydantic, authlib (OAuth client), python-jose (JWT)
- Frontend: React 18, TanStack Query 5.56, @react-oauth/google
**Storage**: PostgreSQL 14+ (user accounts, whitelist, sharing relationships)
**Testing**: pytest (backend), Vitest (frontend)
**Target Platform**: Web application (Linux server backend, browser frontend)
**Project Type**: Web (existing backend + frontend structure)
**Performance Goals**: <500ms authentication flow, <100ms permission checks
**Constraints**: Secure session management, HTTPS required for OAuth, CSRF protection
**Scale/Scope**: Support 100+ concurrent users, whitelist entries up to 1000, sharing relationships up to 10k

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ Test-First Development (TDD/BDD)
- **Status**: PASS
- **Evidence**: Plan includes test contracts before implementation
- **Action**: Write tests first for all authentication flows, permission checks, and sharing logic

### ✅ Fast Test Battery on Every Commit
- **Status**: PASS
- **Evidence**: Unit tests for permission logic, OAuth validation will be under 5s
- **Action**: Integration tests with real OAuth will be in slow battery

### ✅ Complete Test Battery Before Pull Requests
- **Status**: PASS
- **Evidence**: Plan includes both fast (unit) and slow (integration with OAuth) tests
- **Action**: Document test results in PR description

### ✅ Frequent Version Control Commits
- **Status**: PASS
- **Evidence**: Tasks will be broken into atomic commits (backend models, frontend components, etc.)
- **Action**: Commit after each logical milestone (e.g., user model, OAuth flow, whitelist API)

### ✅ Simplicity and Code Quality
- **Status**: PASS
- **Evidence**: Following existing patterns, minimal new dependencies
- **Action**: Keep service methods < 30 lines, use existing repository pattern

### ✅ Language Requirements
- **Status**: PASS
- **Evidence**: Code in English, docs in Portuguese (following project convention)
- **Action**: All documentation in Portuguese, code/variables in English

### ✅ Architecture - Backend Rules
- **Status**: PASS
- **Evidence**:
  - Router: request → service.method() → response
  - Business logic in services (AuthService, SharingService)
  - Data access in repositories (UserRepository, WhitelistRepository)
  - No LLM calls in this feature (OAuth only)
  - SQL parametrized via SQLAlchemy ORM
- **Action**: Follow existing service/repository pattern from synth_service.py

### ✅ Architecture - Frontend Rules
- **Status**: PASS
- **Evidence**:
  - Pages: Login page, admin whitelist page
  - Components: Pure UI (GoogleLoginButton, WhitelistTable)
  - Hooks: useAuth, useWhitelist with React Query
  - Services: authService.login(), whitelistService.add()
- **Action**: Follow existing pattern from synth components

### ✅ Alembic for Database Migrations
- **Status**: PASS
- **Evidence**: New tables (users, whitelist, shares) will be added via Alembic migration
- **Action**: Generate migration for new auth tables

### ✅ Phoenix Tracing
- **Status**: N/A
- **Evidence**: No LLM calls in this feature (OAuth authentication only)

## Project Structure

### Documentation (this feature)

```text
specs/034-user-login/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── auth-api.yaml    # OpenAPI spec for auth endpoints
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# Web application (existing structure)
src/synth_lab/
├── domain/
│   └── entities/
│       ├── user.py              # NEW: User entity
│       └── share.py             # NEW: ExperimentShare, SynthGroupShare entities
├── repositories/
│   ├── user_repository.py       # NEW: User CRUD
│   └── share_repository.py      # NEW: Sharing CRUD
├── services/
│   ├── auth_service.py          # NEW: OAuth flow, session management, whitelist validation
│   └── permission_service.py    # NEW: Permission checks
├── api/
│   └── routers/
│       └── auth.py              # NEW: /auth/login, /auth/callback, /auth/logout
└── infrastructure/
    ├── auth/
    │   ├── oauth_client.py      # NEW: Google OAuth client wrapper
    │   ├── session_manager.py   # NEW: Session/JWT handling
    │   └── whitelist.py         # NEW: Whitelist validation from env var
    └── middleware/
        └── auth_middleware.py   # NEW: Authentication middleware

frontend/src/
├── pages/
│   └── LoginPage.tsx            # NEW: Login page with Google button
├── components/
│   └── auth/
│       ├── GoogleLoginButton.tsx    # NEW: Google OAuth button
│       └── ProtectedRoute.tsx       # NEW: Route guard
├── hooks/
│   └── useAuth.ts               # NEW: Auth state, login/logout
└── services/
    └── authService.ts           # NEW: Auth API calls

tests/
├── unit/
│   ├── test_auth_service.py         # NEW: Auth logic unit tests
│   ├── test_permission_service.py   # NEW: Permission checks
│   └── test_oauth_client.py         # NEW: OAuth client mocking
├── integration/
│   ├── test_auth_flow.py            # NEW: Full OAuth flow (slow)
│   └── test_sharing.py              # NEW: Sharing with permissions
└── e2e/
    └── test_login_flow.py           # NEW: Browser-based login test

migrations/
└── versions/
    └── XXXX_add_user_auth_tables.py # NEW: Alembic migration
```

**Structure Decision**: Using existing web application structure (backend/ + frontend/). New code follows established patterns:
- Backend: domain/entities, repositories, services, api/routers
- Frontend: pages, components, hooks, services
- Tests: unit (fast), integration (slow), e2e

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitutional violations. All checks pass.

---

## Post-Design Constitution Re-evaluation

*Re-evaluated after Phase 1 design completion (2026-01-22)*

### ✅ Test-First Development (TDD/BDD)
- **Status**: PASS
- **Design Impact**: Test contracts defined in auth-api.yaml cover all endpoints
- **Action Items**:
  - Unit tests for whitelist validation (in-memory parsing)
  - Unit tests for permission service logic
  - Integration tests for OAuth flow (mocked Google responses)
  - E2E tests for full login workflow

### ✅ Fast Test Battery on Every Commit
- **Status**: PASS
- **Design Impact**: Clear separation between fast (unit) and slow (integration) tests
- **Fast Tests**:
  - Whitelist email/domain matching logic
  - Permission checks (mocked repos)
  - JWT creation/validation
  - Share business logic validation
- **Estimated Time**: <3 seconds (well under 5s limit)

### ✅ Complete Test Battery Before Pull Requests
- **Status**: PASS
- **Design Impact**: Comprehensive test coverage defined
- **Slow Tests**:
  - OAuth callback flow with mocked Google API
  - Database integration (users, shares tables)
  - Full sharing workflows with permission checks
- **E2E Tests**:
  - Browser-based login via Playwright
  - End-to-end experiment sharing workflow

### ✅ Frequent Version Control Commits
- **Status**: PASS
- **Design Impact**: Clear atomic commit boundaries identified
- **Commit Milestones**:
  1. Database migration (users, shares tables)
  2. User entity and repository
  3. Share entities and repository
  4. Whitelist validation infrastructure
  5. OAuth client and session manager
  6. Auth service (OAuth flow)
  7. Permission service
  8. Auth router (endpoints)
  9. Auth middleware
  10. Frontend: Google login button component
  11. Frontend: useAuth hook
  12. Frontend: Protected route component
  13. Frontend: Login page
  14. Tests for each component

### ✅ Simplicity and Code Quality
- **Status**: PASS
- **Design Impact**:
  - No admin UI (WHITELIST env var only) - significant simplification
  - No database table for whitelist - reduced complexity
  - Leveraging existing service/repository patterns
  - Minimal new dependencies (authlib, python-jose, @react-oauth/google)
- **File Size Estimates**:
  - auth_service.py: ~250 lines (OAuth flow + whitelist validation)
  - permission_service.py: ~150 lines (access checks)
  - whitelist.py: ~50 lines (env var parsing)
  - All within <500 line limit

### ✅ Language Requirements
- **Status**: PASS
- **Evidence**:
  - quickstart.md written in Portuguese ✓
  - API contracts in English (standard for OpenAPI) ✓
  - Code/variables will be in English ✓

### ✅ Architecture - Backend Rules
- **Status**: PASS
- **Design Verification**:
  - **Router**: auth.py contains only `request → service → response` ✓
  - **Service**: auth_service.py has OAuth logic, permission_service.py has access control ✓
  - **Repository**: user_repository.py, share_repository.py handle SQL ✓
  - **No LLM calls**: Feature uses only OAuth, no Phoenix tracing needed ✓
  - **SQL**: All queries via SQLAlchemy ORM with parameterized queries ✓
- **New Files Conform**: All designed files follow established patterns from synth_service.py

### ✅ Architecture - Frontend Rules
- **Status**: PASS
- **Design Verification**:
  - **Pages**: LoginPage.tsx composes components ✓
  - **Components**: GoogleLoginButton, ProtectedRoute are pure (props → JSX) ✓
  - **Hooks**: useAuth.ts encapsulates React Query logic ✓
  - **Services**: authService.ts uses fetchAPI pattern ✓
- **New Files Conform**: Follow patterns from existing synth components

### ✅ Alembic for Database Migrations
- **Status**: PASS
- **Design Details**:
  - Single migration creates: users, experiment_shares, synth_group_shares tables
  - Adds owner_id to experiments and synth_groups tables
  - Creates PermissionLevel ENUM type
  - All documented in data-model.md

### ✅ Phoenix Tracing
- **Status**: N/A
- **Confirmation**: No LLM calls in this feature (OAuth authentication only)

---

## Final Design Approval

**Constitution Status**: ✅ ALL CHECKS PASS

**Design Artifacts Generated**:
- ✅ plan.md (this file)
- ✅ research.md (technology decisions)
- ✅ data-model.md (entities, relationships, validation rules)
- ✅ contracts/auth-api.yaml (OpenAPI specification)
- ✅ quickstart.md (setup guide in Portuguese)

**Next Phase**: Ready for `/speckit.tasks` to generate implementation tasks.

**No Blockers**: All architectural decisions made, no unresolved questions remain.

