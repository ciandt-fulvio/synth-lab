# Deprecated Elements Analysis - Document Unification

## Summary

After unifying document storage into the `experiment_documents` table, the following legacy elements are now deprecated. All document types (summary, prfaq, executive_summary) are now stored in `experiment_documents`.

## 1. Database Tables/Columns to Remove

### 1.1 `prfaq_metadata` Table (ENTIRE TABLE)
**Location:** `src/synth_lab/infrastructure/database.py` lines 166-185

**Status:** Deprecated - Replaced by `experiment_documents` with `document_type='prfaq'`

**Current State:**
- Still being written to via dual-write pattern (`prfaq_service.py` line 170)
- Still being read by legacy endpoints (`/prfaq/{exec_id}`, `/prfaq/{exec_id}/markdown`)
- Frontend NO LONGER reads from this table (now uses `/documents` API)

**Schema:**
```sql
CREATE TABLE prfaq_metadata (
    exec_id TEXT PRIMARY KEY,
    generated_at TEXT,
    model TEXT DEFAULT 'gpt-4o-mini',
    validation_status TEXT DEFAULT 'valid',
    confidence_score REAL,
    headline TEXT,
    one_liner TEXT,
    faq_count INTEGER DEFAULT 0,
    markdown_content TEXT,              -- Replaced by experiment_documents.markdown_content
    json_content TEXT CHECK(json_valid(json_content) OR json_content IS NULL),
    status TEXT DEFAULT 'completed',
    error_message TEXT,
    started_at TEXT,
    CHECK(validation_status IN ('valid', 'invalid', 'pending')),
    CHECK(status IN ('generating', 'completed', 'failed'))
);
```

**Note:** Only `markdown_content` is used in current code. Other metadata fields (validation_status, confidence_score, etc.) are populated but never read.

---

### 1.2 `research_executions.summary_content` Column
**Location:** `src/synth_lab/infrastructure/database.py` line 137

**Status:** Deprecated - Replaced by `experiment_documents` with `document_type='summary'`

**Current State:**
- Still being written to via dual-write pattern (`research_service.py` line 308)
- Still being read by:
  - `research_service.get_summary()` (line 155)
  - `research_service.get_artifact_states()` (line 192)
  - `prfaq_service.generate_prfaq()` (line 145) - reads summary to generate PR-FAQ
- Frontend NO LONGER reads from this column (now uses `/documents` API)

**Column:**
```sql
summary_content TEXT,  -- In research_executions table
```

---

### 1.3 Analysis Cache - Executive Summary Entries
**Location:** `analysis_cache` table with `cache_key='executive_summary'`

**Status:** Deprecated - Replaced by `experiment_documents` with `document_type='executive_summary'`

**Current State:**
- Legacy method `executive_summary_service.generate_summary()` still writes to this cache
- Only used in unit tests (`tests/unit/services/test_executive_summary_service.py`)
- Production code now uses `generate_markdown_summary()` which writes to `experiment_documents`
- Frontend NO LONGER reads from analysis_cache (now uses `/documents` API)

**Important:** The `analysis_cache` table itself CANNOT be removed - it's actively used for caching chart data (try_vs_success, distribution, heatmap, scatter, etc.)

---

## 2. Backend API Endpoints to Remove

### 2.1 Research API - Legacy Endpoints
**File:** `src/synth_lab/api/routers/research.py`

```python
# Line 101 - Artifact States (DEPRECATED)
@router.get("/{exec_id}/artifacts", response_model=ArtifactStatesResponse)
async def get_artifact_states(exec_id: str, service: ResearchService = Depends()) -> ArtifactStatesResponse:
    # Frontend now uses /documents/availability instead

# Line 118 - Summary Markdown (DEPRECATED)
@router.get("/{exec_id}/summary")
async def get_summary(exec_id: str, service: ResearchService = Depends()) -> PlainTextResponse:
    # Frontend now uses /documents/{experiment_id}/summary/markdown instead
```

**Note:** Keep `/summary/generate` endpoint (line 130) as it triggers background generation and may still be useful.

---

### 2.2 PR-FAQ API - Legacy Endpoints
**File:** `src/synth_lab/api/routers/prfaq.py`

```python
# Line 62 - PR-FAQ Markdown (DEPRECATED)
@router.get("/{exec_id}/markdown")
async def get_prfaq_markdown(exec_id: str, service: PRFAQService = Depends()) -> PlainTextResponse:
    # Frontend now uses /documents/{experiment_id}/prfaq/markdown instead
```

**Note:**
- `/prfaq/{exec_id}` (line 51) - Still used to display PR-FAQ metadata
- `/prfaq/generate` (line 80) - Still used to trigger generation

---

### 2.3 Insights API - Executive Summary (DEPRECATED)
**File:** `src/synth_lab/api/routers/insights.py`

Already removed from frontend in this refactor. Backend endpoint may still exist - need to verify.

---

## 3. Service Methods to Remove

### 3.1 ExecutiveSummaryService
**File:** `src/synth_lab/services/executive_summary_service.py`

```python
# Line 98 - Legacy JSON generation (DEPRECATED)
def generate_summary(self, analysis_id: str) -> ExecutiveSummary:
    # Only used in unit tests
    # Production code uses generate_markdown_summary() instead
```

---

### 3.2 ResearchService
**File:** `src/synth_lab/services/research_service.py`

```python
# Line 141 - Get Summary Content (STILL NEEDED)
def get_summary(self, exec_id: str) -> str:
    # Still used by legacy /summary endpoint
    # Can be removed when endpoint is removed

# Line 162 - Get Artifact States (DEPRECATED)
def get_artifact_states(self, exec_id: str) -> tuple[ArtifactStateModel, ArtifactStateModel]:
    # Frontend no longer uses this
    # Can be removed when /artifacts endpoint is removed
```

---

### 3.3 PRFAQService
**File:** `src/synth_lab/services/prfaq_service.py`

```python
# Line 84 - Get Markdown (STILL NEEDED)
def get_markdown(self, exec_id: str) -> str:
    # Still used by legacy /markdown endpoint
    # Can be removed when endpoint is removed
```

---

## 4. Repository Methods to Remove

### 4.1 AnalysisCacheRepository
**File:** `src/synth_lab/repositories/analysis_cache_repository.py`

```python
# Method to remove: store_executive_summary()
# Only used by legacy generate_summary() method
```

---

### 4.2 ResearchRepository
**File:** `src/synth_lab/repositories/research_repository.py`

```python
# Line 133 - Get Summary Content
def get_summary_content(self, exec_id: str) -> str | None:
    # Still used by:
    # 1. research_service.get_summary() (legacy endpoint)
    # 2. research_service.get_artifact_states() (deprecated)
    # 3. prfaq_service.generate_prfaq() - reads summary to generate PR-FAQ

# Line 411 - Get PR-FAQ Metadata
def get_prfaq_metadata(self, exec_id: str) -> dict | None:
    # Only used by get_artifact_states (deprecated)
```

---

### 4.3 PRFAQRepository
**File:** `src/synth_lab/repositories/prfaq_repository.py`

```python
# Line 102 - Get Markdown Content
def get_markdown_content(self, exec_id: str) -> str | None:
    # Still used by prfaq_service.get_markdown() (legacy endpoint)
```

---

## 5. Domain Entities to Remove

**File:** `src/synth_lab/domain/entities/artifact_state.py`

```python
# Entire file can be removed - artifact states are deprecated
# Only imported by research_service.get_artifact_states()
```

---

## 6. Critical Dependencies to Address

### 6.1 PR-FAQ Generation Depends on Summary
**File:** `prfaq_service.py` line 145

```python
# PR-FAQ generation reads from research_executions.summary_content
summary_content = research_repo.get_summary_content(request.exec_id)
```

**Solution:** Before removing `summary_content` column, update PR-FAQ generation to read from `experiment_documents` instead.

---

## 7. Removal Strategy

### Phase 1: Update Backend Dependencies
1. **Update PR-FAQ generation** to read summary from `experiment_documents` instead of `research_executions.summary_content`
2. **Remove dual-write** from services (stop writing to legacy tables)

### Phase 2: Remove Legacy Endpoints
1. Remove `GET /research/{exec_id}/artifacts`
2. Remove `GET /research/{exec_id}/summary`
3. Remove `GET /prfaq/{exec_id}/markdown`

### Phase 3: Remove Service Methods
1. Remove `executive_summary_service.generate_summary()`
2. Remove `research_service.get_artifact_states()`
3. Remove `research_service.get_summary()`
4. Remove `prfaq_service.get_markdown()`

### Phase 4: Remove Repository Methods
1. Remove `research_repo.get_summary_content()`
2. Remove `research_repo.get_prfaq_metadata()`
3. Remove `prfaq_repo.get_markdown_content()`
4. Remove `analysis_cache_repo.store_executive_summary()`

### Phase 5: Remove Database Schema
1. Drop `prfaq_metadata` table
2. Drop `research_executions.summary_content` column
3. Clean up executive_summary entries from `analysis_cache` (keep other cache entries)

### Phase 6: Update Tests
1. Update unit tests that use legacy methods
2. Ensure integration tests use new document API

---

## 8. Risk Assessment

### Low Risk (Can Remove Immediately)
- ✅ `research_service.get_artifact_states()` - Frontend no longer uses
- ✅ `GET /research/{exec_id}/artifacts` - Frontend no longer uses
- ✅ `executive_summary_service.generate_summary()` - Only used in tests
- ✅ `artifact_state.py` domain entity

### Medium Risk (Update Dependencies First)
- ⚠️ `research_executions.summary_content` column - PR-FAQ generation still reads from this
- ⚠️ `prfaq_metadata` table - Legacy endpoints still read from this
- ⚠️ Dual-write code in services - Safe to remove after confirming all data is in experiment_documents

### No Risk (Keep)
- ✅ `analysis_cache` table - Actively used for chart caching
- ✅ `/summary/generate` endpoint - Useful for triggering background generation
- ✅ `/prfaq/generate` endpoint - Useful for triggering background generation

---

## 9. Data Migration Considerations

**Important:** Before removing database tables/columns, ensure existing data is migrated to `experiment_documents`.

### Check for Unmigrated Data
```sql
-- Find summaries not in experiment_documents
SELECT exec_id, experiment_id
FROM research_executions
WHERE summary_content IS NOT NULL
  AND experiment_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM experiment_documents
    WHERE experiment_id = research_executions.experiment_id
      AND document_type = 'summary'
  );

-- Find PR-FAQs not in experiment_documents
SELECT pm.exec_id, re.experiment_id
FROM prfaq_metadata pm
JOIN research_executions re ON pm.exec_id = re.exec_id
WHERE pm.markdown_content IS NOT NULL
  AND re.experiment_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM experiment_documents
    WHERE experiment_id = re.experiment_id
      AND document_type = 'prfaq'
  );

-- Find executive summaries not in experiment_documents
SELECT ac.analysis_id, ar.experiment_id
FROM analysis_cache ac
JOIN analysis_runs ar ON ac.analysis_id = ar.id
WHERE ac.cache_key = 'executive_summary'
  AND NOT EXISTS (
    SELECT 1 FROM experiment_documents
    WHERE experiment_id = ar.experiment_id
      AND document_type = 'executive_summary'
  );
```

### Migration Script (if needed)
If unmigrated data exists, create a migration script to copy data from legacy tables to `experiment_documents` before removal.

---

## 10. Recommended Action Plan

Given the user's request to remove deprecated code and unnecessary tables:

1. **Immediate (Safe to Remove Now):**
   - ✅ Remove `GET /research/{exec_id}/artifacts` endpoint
   - ✅ Remove `research_service.get_artifact_states()` method
   - ✅ Remove `src/synth_lab/domain/entities/artifact_state.py`
   - ✅ Remove `research_repo.get_prfaq_metadata()` method

2. **After Dependency Update (Medium Priority):**
   - ⚠️ Update `prfaq_service.generate_prfaq()` to read from experiment_documents
   - ⚠️ Then remove `research_executions.summary_content` column
   - ⚠️ Then remove `prfaq_metadata` table

3. **Low Priority (Cleanup):**
   - Remove legacy endpoints (`GET /summary`, `GET /markdown`)
   - Remove dual-write code from services
   - Update unit tests to use new methods
