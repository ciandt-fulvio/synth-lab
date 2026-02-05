# Scripts Directory

Automation scripts for development, testing, and deployment.

## Testing Scripts (⭐ Smart Execution)

### Smart Test Runners

These scripts provide intelligent test execution with failure prioritization:

**run-tests-smart.sh** - Backend test runner
```bash
./scripts/run-tests-smart.sh
# Or via Makefile
make test
```

**run-e2e-tests-smart.sh** - E2E test runner
```bash
./scripts/run-e2e-tests-smart.sh
# Or via Makefile
make test-e2e
```

**How it works**:
1. Runs previously failed tests first (fail-fast: stops on first failure)
2. If all pass, runs full suite (no fail-fast: discovers all issues)
3. Provides 40-50% faster feedback during development

**validate-smart-tests.sh** - Validates smart test configuration
```bash
./scripts/validate-smart-tests.sh
```

📖 **Documentation**: `docs/smart-test-execution.md`

### Environment Management

**compose-e2e.sh** - Docker Compose wrapper for E2E environment
```bash
./scripts/compose-e2e.sh up-detached  # Start environment
./scripts/compose-e2e.sh down         # Stop environment
./scripts/compose-e2e.sh logs         # View logs
```

Features:
- Auto-detects Docker/Podman
- Incremental rebuild (only changed services)
- Cleanup helpers for Podman

## Git Workflow Scripts

**merge-to-main.sh** - Safe merge helper with preview
```bash
./scripts/merge-to-main.sh <branch-name>
```

Features:
- Pre-merge validation (uncommitted changes, branch exists)
- Commit preview before merge
- Interactive confirmation
- Push reminder (where pre-push hook will run)

**pre-push-hook.sh** - Automated validation before pushing to main
```bash
# Runs automatically on: git push origin main
# Bypass: git push origin main --no-verify
```

Steps:
1. Build Docker images
2. Run backend tests (smart mode)
3. Run E2E tests (smart mode)
4. Push images to GHCR
5. Allow push if all pass

**test-pre-push-hook.sh** - Diagnose pre-push hook issues
```bash
./scripts/test-pre-push-hook.sh
```

📖 **Documentation**: See `CLAUDE.md` (Git Workflow & Merge section)

## Development Scripts

**auto-update-docs.sh** - Update documentation from commits
```bash
./scripts/auto-update-docs.sh --last-commit
```

**auto-update-tests.sh** - Generate tests from code changes
```bash
./scripts/auto-update-tests.sh
```

## Infrastructure Scripts

**docker-entrypoint-backend.sh** - Backend container entrypoint
- Waits for PostgreSQL health check
- Runs Alembic migrations
- Starts FastAPI with Uvicorn

**railway-deploy-image.sh** - Deploy pre-built images to Railway
```bash
./scripts/railway-deploy-image.sh backend <commit-sha>
./scripts/railway-deploy-image.sh frontend <commit-sha>
```

**setup-github-secrets.sh** - Configure GitHub Actions secrets
```bash
./scripts/setup-github-secrets.sh
```

**setup-railway-secrets.sh** - Configure Railway environment variables
```bash
./scripts/setup-railway-secrets.sh <environment> <service>
```

📖 **Documentation**: `scripts/SECRETS_SETUP.md`

## Installation Scripts

**install-hooks.sh** - Configure Git hooks
```bash
./scripts/install-hooks.sh
# Or via Makefile
make setup-hooks
```

## Best Practices

### 1. Always Use Smart Test Runners

During development, use Makefile commands that leverage smart execution:

```bash
# ✅ Good - Uses smart mode
make test
make test-e2e

# ❌ Avoid - Bypasses optimization
uv run pytest
cd frontend && npm run test:e2e
```

### 2. Use Merge Helper for Branches

```bash
# ✅ Good - Safe with preview
./scripts/merge-to-main.sh 039-feature-name

# ❌ Risky - Manual merge without checks
git checkout main && git merge 039-feature-name
```

### 3. Let Pre-Push Hook Run

The pre-push hook catches issues locally before CI:

```bash
# ✅ Good - Full validation locally
git push origin main

# ⚠️ Use sparingly - Bypasses validation
git push origin main --no-verify
```

### 4. Validate After Changes

After modifying test configuration:

```bash
./scripts/validate-smart-tests.sh
```

## Quick Reference

| Task | Command | Time Saved |
|------|---------|------------|
| Backend tests (dev) | `make test` | ~40% faster |
| E2E tests (dev) | `make test-e2e` | ~50% faster |
| Merge branch | `./scripts/merge-to-main.sh <branch>` | Prevents errors |
| Validate setup | `./scripts/validate-smart-tests.sh` | Catches issues |
| Push to main | `git push origin main` | Auto-validated |

## Documentation Index

- **Smart Testing**: `docs/smart-test-execution.md`
- **Git Workflow**: `CLAUDE.md` (Git Workflow & Merge section)
- **Pre-Push Hook**: `docs/testing-pre-push-hook.md`
- **CI/CD Pipeline**: `CLAUDE.md` (CI/CD Pipeline section)
- **Secrets Setup**: `scripts/SECRETS_SETUP.md`
