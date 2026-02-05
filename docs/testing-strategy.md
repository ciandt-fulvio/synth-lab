# Testing Strategy - Backend

## Overview

Synth-lab uses a multi-layered testing strategy to ensure quality while maintaining fast feedback loops:

1. **Unit Tests** - Fast, isolated, no external dependencies
2. **Integration Tests** - Mock external APIs (OpenAI, S3), real database
3. **Smoke Tests** - Real API calls, production readiness validation
4. **Contract Tests** - API schema validation
5. **E2E Tests** - Full stack tests via Playwright

## Test Markers

Tests are organized using pytest markers for fine-grained control:

| Marker | Purpose | External Calls | Speed | Cost |
|--------|---------|----------------|-------|------|
| `integration` | Integration tests with mocked APIs | No (mocked) | Fast (<1s) | Free |
| `smoke` | Critical path validation | No (unless combined with `real_api`) | Fast | Free |
| `real_api` | Tests making REAL API calls | Yes | Slow (5-10s) | ~$0.02 |
| `slow` | Tests taking >5 seconds | Varies | Slow | Varies |
| `contract` | API contract/schema tests | No | Fast | Free |
| `schema` | Schema validation tests | No | Fast | Free |

## Running Tests

### Fast Development Loop (Default)

```bash
# Run all fast tests (excludes real API calls)
make test

# Or directly with pytest
pytest

# Exclude slow tests explicitly
pytest -m "not slow"

# Run only integration tests (fast, mocked)
pytest -m integration
```

**Time**: ~1-2 minutes
**Cost**: $0

### Include Slow Tests (No Real API)

```bash
# Run all tests including slow ones (but still mocked)
pytest -m "not real_api"
```

**Time**: ~2-3 minutes
**Cost**: $0

### Smoke Tests Only (Real API Calls)

```bash
# Run only smoke tests with real APIs
pytest -m "smoke and real_api"

# Or specific smoke test file
pytest tests/smoke/test_openai_integration.py
```

**Time**: ~15-20 seconds
**Cost**: ~$0.02 (OpenAI API calls)

⚠️  **Only run in CI or when explicitly validating production readiness**

### Full Suite (Including Real API)

```bash
# Run everything (not recommended locally)
pytest -m ""

# Or explicitly include slow and real_api
pytest
```

**Time**: ~3-5 minutes
**Cost**: ~$0.02

## Test Structure

### Unit Tests (`tests/unit/`)

Pure functions, no external dependencies, no database.

```python
def test_calculate_block_count():
    """Test block calculation logic (pure function)."""
    from synth_lab.gen_synth.avatar_generator import calculate_block_count
    assert calculate_block_count(9, blocks=None) == 1
```

**Characteristics**:
- Very fast (<0.1s each)
- No mocking needed
- Tests pure logic

### Integration Tests (`tests/integration/`)

Test complete workflows with mocked external APIs.

```python
@pytest.mark.integration
class TestAvatarGeneration:
    def test_generate_avatars(self, mock_openai_client, mock_s3_storage):
        """Test avatar generation with mocked OpenAI and S3."""
        # Uses real database, mocked APIs
        result = generate_avatars(synths, ...)
        assert len(result) == 9
```

**Characteristics**:
- Fast (<1s each)
- Real database operations
- Mocked: OpenAI, S3, HTTP requests
- Uses fixtures from `tests/fixtures/llm_mocks.py`

### Smoke Tests (`tests/smoke/`)

Minimal validation with real APIs (production readiness).

```python
@pytest.mark.slow
@pytest.mark.real_api
@pytest.mark.smoke
def test_openai_hello_world():
    """Verify OpenAI API key works with minimal 'hello world' call."""
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hi"}],
        max_tokens=5
    )
    assert response.choices[0].message.content is not None
```

**Characteristics**:
- Slow (5-10s each)
- REAL API calls (costs money!)
- Minimal coverage (just connectivity)
- Skipped if API keys not configured

## Mocking Strategy

### LLM Mocking (OpenAI)

Use centralized fixtures from `tests/fixtures/llm_mocks.py`:

```python
def test_my_service(mock_llm_client):
    """Test service with mocked LLM."""
    service = MyService(llm_client=mock_llm_client)
    result = service.generate()

    # Verify LLM was called
    mock_llm_client.complete.assert_called_once()
```

Available fixtures:
- `mock_llm_client` - Generic LLM client
- `mock_openai_client` - OpenAI-specific client (chat completions)
- `mock_openai_image` - OpenAI DALL-E image generation
- `mock_s3_storage` - S3 operations
- `mock_http_image_download` - HTTP image downloads

### When to Mock vs Real

| Component | Development | CI/CD | Rationale |
|-----------|-------------|-------|-----------|
| **LLM Calls (Text)** | Always mock | Always mock | Fast, cheap, deterministic |
| **LLM Calls (Images)** | Always mock | Always mock | Slow, expensive ($0.02/call) |
| **S3 Operations** | Always mock | Always mock | Fast, no cost, deterministic |
| **Database** | Real (isolated) | Real (isolated) | Fast with PostgreSQL, tests real queries |
| **HTTP Requests** | Mock | Mock | Fast, no external dependencies |
| **Smoke Tests** | Skip (no API key) | Real (has API key) | Validates production readiness |

## CI/CD Integration

### Pre-Push Hook (Local)

```bash
# Runs automatically on: git push origin main
# Tests: backend (mocked) + E2E (mocked)
# Time: ~3-5 minutes
# Cost: $0
```

### GitHub Actions (CI)

```yaml
# .github/workflows/test.yml
steps:
  - name: Backend Tests (Mocked)
    run: pytest -m "not real_api"

  - name: Smoke Tests (Real API)
    run: pytest -m "smoke and real_api"
    env:
      OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

**Time**: ~3-5 minutes
**Cost**: ~$0.02 per run

## Performance Metrics

### Before Optimization

```
Backend test suite:
├─> Fast tests (no LLM): ~1-2 min
├─> Slow tests (auth): ~30-60s
└─> Real LLM calls: ~10-20s (gargalo!)
────────────────────────────────────
Total: ~2-4 minutos
```

### After Optimization (Current)

```
Backend test suite:
├─> Fast tests (no LLM): ~1-2 min
├─> Slow tests (auth): ~30-60s
├─> Mocked LLM tests: ~5s ✅
└─> 1 smoke test (optional): ~5s
────────────────────────────────────
Total: ~1.5-2.5 min (25-30% faster) ✅
```

## Best Practices

### 1. Default to Mocking

```python
# ✅ GOOD: Fast, deterministic, no cost
@pytest.mark.integration
def test_generate_guide(mock_llm_client):
    guide = service.generate_guide(...)
    mock_llm_client.complete_json.assert_called_once()

# ❌ BAD: Slow, costs money, flaky
def test_generate_guide():
    guide = service.generate_guide(...)  # Real API call!
```

### 2. One Smoke Test Per External Service

```python
# ✅ GOOD: Minimal smoke test
@pytest.mark.real_api
def test_openai_hello_world():
    """Verify OpenAI works with 'Hi' -> response."""
    # Just verify connectivity

# ❌ BAD: Extensive real API testing
@pytest.mark.real_api
def test_openai_complex_workflow():
    """Test complex multi-step LLM workflow with real API."""
    # Too expensive and slow for smoke test
```

### 3. Use Centralized Fixtures

```python
# ✅ GOOD: Reusable fixture
def test_avatar_gen(mock_openai_image, mock_s3_storage):
    result = generate_avatars(...)

# ❌ BAD: Inline mocking (duplicated)
def test_avatar_gen():
    with patch("openai.OpenAI") as mock:
        mock.return_value.images.generate.return_value = ...
        # Duplicated setup code
```

### 4. Skip Real API Tests Locally

```python
# ✅ GOOD: Auto-skip if no API key
def test_real_api():
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not configured")
    # Real API call

# ❌ BAD: Fail if no API key
def test_real_api():
    # Expects API key, fails loudly
```

## Troubleshooting

### "Tests are slow"

```bash
# Find slow tests
pytest --durations=10

# Exclude slow tests
pytest -m "not slow"

# Check if real API calls are being made
pytest -v | grep "SLOW TEST"
```

### "API costs are high"

```bash
# Verify no real API calls in default run
pytest -m "not real_api"

# Check which tests are marked as real_api
grep -r "@pytest.mark.real_api" tests/

# Should only be in tests/smoke/
```

### "Tests are flaky"

- Check for real API calls (network issues)
- Ensure mocks are properly configured
- Verify database isolation (use `isolated_db_session`)

## References

- Centralized mocks: `tests/fixtures/llm_mocks.py`
- Smoke tests: `tests/smoke/test_openai_integration.py`
- Analysis: `docs/test-performance-analysis.md`
- pytest markers: https://docs.pytest.org/en/stable/example/markers.html
