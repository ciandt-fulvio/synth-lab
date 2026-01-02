# Testing Guide

## Test Database Setup

### 🚨 CRITICAL: Database Isolation

**Integration tests use a SEPARATE test database** to prevent data loss. Tests that perform destructive operations (DROP, TRUNCATE) will **NEVER** touch your development or production database.

### Quick Start

1. **Create the test database:**
   ```bash
   make db-test
   ```

   This will:
   - Create `synthlab_test` database in PostgreSQL
   - Apply all migrations
   - Display the test database URL

2. **Run tests:**
   ```bash
   make test-full    # All tests with verbose output
   make test         # All tests
   make test-unit    # Unit tests only (no DB required)
   make test-integration  # Integration tests only
   ```

3. **Reset test database** (if needed):
   ```bash
   make db-test-reset
   ```

### Configuration

The test database is configured in:

**`.env` file:**
```bash
# Development database (NEVER used by tests)
DATABASE_URL=postgresql://synthlab:synthlab_dev@localhost:5432/synthlab

# Test database (ISOLATED - for running tests safely)
DATABASE_TEST_URL=postgresql://synthlab:synthlab_dev@localhost:5432/synthlab_test
```

**`Makefile`:**
```makefile
POSTGRES_TEST_DB := synthlab_test
DATABASE_TEST_URL := postgresql://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@localhost:$(POSTGRES_PORT)/$(POSTGRES_TEST_DB)
```

### Safety Mechanisms

**1. Automatic database validation** (`tests/conftest.py`):
```python
@pytest.fixture(scope="session")
def test_database_url() -> str:
    """Ensures tests NEVER use development database."""
    postgres_url = os.getenv("POSTGRES_URL")

    # CRITICAL: Verify we're using test database
    if "synthlab_test" not in postgres_url:
        raise ValueError(
            f"POSTGRES_URL must point to 'synthlab_test' database!\n"
            f"Current: {postgres_url}"
        )

    return postgres_url
```

**2. Test commands use test database:**
```makefile
test-full:
    POSTGRES_URL="$(DATABASE_TEST_URL)" uv run pytest tests/ -v --tb=short
```

**3. Pre-push hook protection:**

The `.githooks/pre-push` hook runs `make test-full`, which automatically uses the test database.

### Writing Integration Tests

**✅ CORRECT - Use test_database_url fixture:**
```python
def test_something(test_database_url: str):
    """Test that uses the isolated test database."""
    config = get_alembic_config(test_database_url)
    # ... test code that may DROP/TRUNCATE tables
```

**❌ INCORRECT - Direct environment access:**
```python
def test_something():
    """DANGEROUS: May use development database!"""
    postgres_url = os.getenv("POSTGRES_URL")  # ⚠️ NO SAFETY CHECK!
    # ... test code
```

### Test Structure

```
tests/
├── conftest.py          # Shared fixtures (includes test_database_url)
├── unit/                # Unit tests (no database)
├── integration/         # Integration tests (use test_database_url)
│   ├── test_alembic_migrations.py
│   ├── test_postgres_connection.py
│   └── repositories/
└── contract/            # Contract tests
```

### Common Tasks

**Run specific test file:**
```bash
POSTGRES_URL="postgresql://synthlab:synthlab_dev@localhost:5432/synthlab_test" \
    uv run pytest tests/integration/test_alembic_migrations.py -v
```

**Run with coverage:**
```bash
make test-full --cov=synth_lab --cov-report=html
```

**Debug failing test:**
```bash
POSTGRES_URL="postgresql://synthlab:synthlab_dev@localhost:5432/synthlab_test" \
    uv run pytest tests/integration/test_alembic_migrations.py::TestAlembicMigrationsPostgres::test_experiments_table_schema -vv
```

### Troubleshooting

**Error: "POSTGRES_URL not set"**
```bash
# Run make db-test first
make db-test
```

**Error: "POSTGRES_URL must point to 'synthlab_test'"**
```bash
# Check your test command - it should use DATABASE_TEST_URL
# Correct:
make test-full

# Incorrect:
POSTGRES_URL="$DATABASE_URL" pytest  # Uses dev DB!
```

**Test database has stale schema:**
```bash
make db-test-reset
```

**PostgreSQL container not running:**
```bash
make db      # Start development database
make db-test # Create test database
```

### CI/CD Integration

In CI environments, you should:

1. Create a temporary test database
2. Set `POSTGRES_URL` to point to it
3. Run migrations
4. Run tests
5. Destroy the database

**Example GitHub Actions:**
```yaml
- name: Setup test database
  run: |
    make db
    make db-test

- name: Run tests
  run: make test-full
```

### Best Practices

1. **Always use `test_database_url` fixture** for integration tests
2. **Never mock database operations** - use real test DB
3. **Clean up test data** in teardown or use transactions
4. **Run tests locally** before pushing (pre-push hook does this)
5. **Keep test database isolated** - never point to dev/prod

### Migration Testing

When testing migrations:

```python
def test_migration(test_database_url: str):
    """Test migration up/down cycle."""
    config = get_alembic_config(test_database_url)

    # Safe to drop - we're on test database!
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    # Verify schema
    engine = create_engine(test_database_url)
    # ... assertions
```

### What NOT to Do

❌ **Don't bypass safety checks:**
```python
# NEVER do this:
postgres_url = os.getenv("DATABASE_URL")  # Might be dev DB!
```

❌ **Don't use development database for tests:**
```bash
# NEVER do this:
POSTGRES_URL="postgresql://localhost/synthlab" pytest
```

❌ **Don't skip the pre-push hook:**
```bash
# Avoid using --no-verify unless absolutely necessary
git push --no-verify  # Skips tests!
```

### Resources

- [pytest documentation](https://docs.pytest.org/)
- [SQLAlchemy testing](https://docs.sqlalchemy.org/en/20/core/connections.html#test-suite-connections)
- [Alembic cookbook](https://alembic.sqlalchemy.org/en/latest/cookbook.html)
