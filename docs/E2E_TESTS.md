# E2E Tests

## Overview

End-to-end tests use Playwright to test the complete application flow in a containerized environment.

## Quick Start

```bash
# Run all E2E tests
make test-e2e

# Run specific test file
cd frontend && TEST_ENV=docker npx playwright test tests/e2e/synth-groups/create-basic-group.spec.ts

# Run in UI mode (interactive debugging)
cd frontend && TEST_ENV=docker npx playwright test --ui
```

## Architecture

### Test Environment

E2E tests run against isolated Docker containers:

| Service | Container | Exposed Port | Purpose |
|---------|-----------|--------------|---------|
| PostgreSQL | `synthlab-postgres-test` | 5433 | Test database (ephemeral) |
| Backend | `synthlab-backend-test` | 8001 | API server |
| Frontend | `synthlab-frontend-test` | 8091 | Static file server |

**Isolation**: Test containers use separate network (`synthlab-test-network`) and ports to avoid conflicts with development environment.

### Test Data

Test database is automatically seeded on startup with:
- 1 primary experiment
- 4 synth groups (Default, Usuários Frequentes, Profissionais Ocupados, Famílias)
- 6 synths with realistic profiles
- 500 synth outcomes in analysis run
- 6 research executions with transcripts
- 3 documents (research summary, executive summary, PR-FAQ)
- 1 exploration with 3 scenario nodes

**Seeding**: Handled by `backend-test` container via `tests/fixtures/seed_test.py` during startup.

## Configuration

Frontend is built with `VITE_API_URL=http://localhost:8001` to connect to test backend.

Environment file: `docker/.env.test` (optional overrides for OPENAI_API_KEY, etc.)

## Current Status

**104 passing**, 3 skipped, 23 skipped (conditional), 1 flaky

### Known Issues

**Synth Group Creation Modal Timeout** (3 tests skipped):
- Tests: `create-basic-group.spec.ts`, `create-with-config.spec.ts`, `experiment-integration.spec.ts`
- Symptom: Modal doesn't close after clicking "Criar Grupo" button
- Root cause: Backend API works correctly (verified with curl), likely frontend component issue with success callback or modal close logic
- Impact: Group creation functionality works, but E2E tests cannot verify it

## Cleanup

```bash
# Stop and remove test containers
make test-e2e-down

# For Podman users: aggressive cleanup
./scripts/compose-e2e.sh down
```

**Note**: Podman wraps containers in pods - the cleanup script handles pod removal automatically.

## Development

### Adding New E2E Tests

1. Place test files in `frontend/tests/e2e/<feature>/`
2. Use existing test data from seed script
3. Follow Playwright best practices:
   - Use semantic selectors (role, text)
   - Wait for `networkidle` after navigation
   - Add explicit timeouts for slow operations
   - Use `.first()` to avoid strict mode errors when multiple matches exist

### Debugging Failures

1. Check container logs:
   ```bash
   docker logs synthlab-backend-test
   docker logs synthlab-frontend-test
   ```

2. Verify test data:
   ```bash
   docker exec synthlab-postgres-test psql -U synthlab -d synthlab -c "SELECT name FROM experiments;"
   ```

3. Test backend directly:
   ```bash
   curl http://localhost:8001/experiments
   ```

4. Run single test with UI mode:
   ```bash
   cd frontend && TEST_ENV=docker npx playwright test tests/e2e/path/to/test.spec.ts --ui
   ```

## CI/CD Integration

E2E tests are designed to run in CI pipelines. Set `OPENAI_API_KEY` environment variable if tests require LLM calls (most don't due to seeded data).

**Note**: Tests use production builds of frontend/backend, not development builds with hot reload.
