# Smart Test Execution Strategy

## Overview

The smart test execution strategy optimizes test runtime by prioritizing previously failed tests. This provides faster feedback during development while maintaining comprehensive test coverage.

## Strategy

### Phase 1: Failed Tests First (Fail-Fast)

When you run tests, the system first checks for previously failed tests:

1. **Detects failed tests** from previous runs
2. **Runs only those tests** with fail-fast mode (`--maxfail=1` for pytest, `--max-failures=1` for Playwright)
3. **Stops immediately** if any test fails again
4. This gives you **instant feedback** on whether your fixes worked

### Phase 2: Full Suite (Continue on Failure)

If all previously failed tests pass:

1. **Runs complete test suite** without fail-fast
2. **Continues through all tests** even if some fail
3. **Discovers new failures** that might have been introduced
4. **Updates failed test cache** for next run

## Benefits

| Benefit | Description |
|---------|-------------|
| **Fast Feedback** | Failed tests run first, giving immediate results (often <30s vs 5+ min) |
| **Efficient Iteration** | No need to wait for full suite when fixing specific tests |
| **Full Coverage** | Still runs complete suite to catch new regressions |
| **Smart Caching** | Automatically tracks which tests need attention |

## Usage

### Backend Tests (pytest)

```bash
# Smart mode (automatic with make test)
make test

# Or directly
./scripts/run-tests-smart.sh

# Traditional mode (no optimization)
DATABASE_URL="postgresql://..." uv run pytest
```

**Cache location**: `.pytest_cache/v/cache/lastfailed`

### E2E Tests (Playwright)

```bash
# Smart mode (automatic with make test-e2e)
make test-e2e

# Or directly
./scripts/run-e2e-tests-smart.sh

# Traditional mode (no optimization)
cd frontend && TEST_ENV=docker npm run test:e2e
```

**Cache location**: `frontend/.last-run.json`

## Example Workflow

### Scenario: Fixing 3 Failed Tests

**Without smart mode**:
```
Run all 134 tests → Wait 5 min → See 3 failures → Fix → Repeat
Total: 5 min × iterations = 15-25 min
```

**With smart mode**:
```
Run 3 failed tests → Wait 30s → See results → Fix → Repeat
After fixes pass → Run full suite (5 min) → Done
Total: 30s × 3 iterations + 5 min = ~7 min (52% faster)
```

## Integration

### Makefile Commands

All test commands use smart mode by default:

- `make test` - Backend tests with smart mode
- `make test-e2e` - E2E tests with smart mode
- `make test-fast` - Fast subset (no smart mode needed, already optimized)

### Pre-Push Hook

The `.githooks/pre-push` hook uses smart mode for both backend and E2E tests:

```bash
git push origin main
# → Builds images
# → Runs backend tests (smart mode)
# → Runs E2E tests (smart mode)
# → Pushes images to GHCR
# → Allows push
```

### CI/CD Pipeline

GitHub Actions workflows continue to run full suites without smart mode, ensuring complete validation in CI environment.

## Technical Details

### Backend (pytest)

Smart mode uses pytest's built-in `--last-failed` and `--maxfail` flags:

```bash
# Phase 1: Run only failed tests, stop on first failure
pytest --last-failed --maxfail=1 -v

# Phase 2: Run all tests, continue on failures
pytest -v
```

Pytest automatically caches failed tests in `.pytest_cache/v/cache/lastfailed` as JSON:

```json
{
  "tests/test_something.py::test_function": true,
  "tests/test_other.py::test_another": true
}
```

### E2E (Playwright)

Smart mode uses Playwright's `--last-failed` and `--max-failures` flags:

```bash
# Phase 1: Run only failed tests, stop on first failure
playwright test --last-failed --max-failures=1

# Phase 2: Run all tests, continue on failures
playwright test
```

Playwright tracks test results in `frontend/.last-run.json` and `test-results/` directory.

## Disabling Smart Mode

If you need to run tests without smart mode optimization:

### Backend
```bash
# Direct pytest (bypasses smart mode)
DATABASE_URL="postgresql://..." uv run pytest
```

### E2E
```bash
# Direct Playwright (bypasses smart mode)
cd frontend && TEST_ENV=docker npm run test:e2e
```

## Troubleshooting

### Cache Issues

If the cache becomes stale or incorrect:

**Backend**:
```bash
# Clear pytest cache
rm -rf .pytest_cache
```

**E2E**:
```bash
# Clear Playwright results
rm -rf frontend/test-results frontend/.last-run.json
```

### False Positives

If a test passes locally but smart mode thinks it failed:

1. Clear the cache (see above)
2. Run full suite once to reset: `make test` or `make test-e2e`

## Performance Metrics

Based on actual project data:

| Test Type | Full Suite | Smart Mode (3 failures) | Improvement |
|-----------|-----------|------------------------|-------------|
| Backend | ~2 min | ~30s (failed) + 2 min (full) | ~40% faster |
| E2E | ~5 min | ~1 min (failed) + 5 min (full) | ~45% faster |
| Pre-Push | ~10 min | ~2 min (failed) + 10 min (full) | ~50% faster |

*Improvement calculation based on typical 2-3 iterations before full pass*

## Best Practices

1. **Trust the System**: Let smart mode guide your workflow - if it runs failed tests, pay attention to those first

2. **Don't Skip Full Suite**: Always let the full suite run after fixing failures - this catches new regressions

3. **Clean Cache Occasionally**: If you feel the cache is stale, clear it and run full suite once

4. **Use in Development**: Smart mode is optimized for local development - CI still runs full suites

5. **Commit Often**: Failed test cache is local (.gitignore'd) - commit working code to preserve state
