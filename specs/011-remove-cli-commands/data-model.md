# Phase 1: Data Model - Model Consolidation Mapping

**Feature**: Remove CLI Commands & Fix Architecture
**Date**: 2025-12-20
**Purpose**: Document model reorganization and import path changes

## Overview

This document maps the current scattered model files to their target locations after refactoring. No data structures change - only file locations and import paths.

**Key Changes**:
1. Rename conflicting model files to avoid name collisions
2. Move feature-specific models under `services/`
3. Keep API/DB models in `models/` (top-level, shared)
4. Update all imports to reflect new paths

---

## Model Categories

### Category 1: API/DB Models (Shared Across Layers)
**Location**: `src/synth_lab/models/` (NO CHANGES)

These models define API contracts and database schemas. Used by:
- API routers (request/response models)
- Services (domain models)
- Repositories (DB query results)

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| `models/synth.py` | 257 | Synth domain models (SynthDetail, SynthSummary) | ✅ Keep as-is |
| `models/research.py` | 278 | Research execution models (ResearchExecution, InterviewSummary) | ✅ Keep as-is |
| `models/prfaq.py` | 156 | PR-FAQ API models (PRFAQGenerateRequest, PRFAQSummary) | ✅ Keep as-is |
| `models/topic.py` | 178 | Topic guide models (TopicSummary, TopicDetail) | ✅ Keep as-is |
| `models/pagination.py` | 167 | Pagination helpers (PaginationParams, PaginatedResponse) | ✅ Keep as-is |

**Import Path**: `from synth_lab.models.<module> import <Model>`

**Example**:
```python
from synth_lab.models.synth import SynthDetail
from synth_lab.models.prfaq import PRFAQGenerateRequest
from synth_lab.models.pagination import PaginatedResponse
```

---

### Category 2: Feature-Specific Models (Generation/Pipeline)
**Location**: `src/synth_lab/services/<feature>/` (MOVED + RENAMED)

These models are used internally by feature logic (generation workflows, internal processing). NOT used by API contracts.

#### research_prfaq: Generation Pipeline Models

| Current Path | Target Path | Lines | Purpose |
|--------------|-------------|-------|---------|
| `research_prfaq/models.py` | `services/research_prfaq/generation_models.py` | 488 | PR-FAQ generation workflow models |

**Models in this file**:
```python
# services/research_prfaq/generation_models.py (formerly research_prfaq/models.py)

@dataclass
class PRFAQDocument:
    """Internal model for PR-FAQ document during generation."""
    headline: str
    press_release: str
    external_faqs: List[FAQItem]
    internal_faqs: List[FAQItem]
    metadata: Dict[str, Any]

@dataclass
class PRFAQSection:
    """Internal model for PR-FAQ sections."""
    title: str
    content: str
    section_type: str

@dataclass
class FAQItem:
    """Internal model for FAQ items."""
    question: str
    answer: str
    category: str
```

**Import Path Change**:
```python
# Before:
from synth_lab.research_prfaq.models import PRFAQDocument, PRFAQSection

# After:
from synth_lab.services.research_prfaq.generation_models import PRFAQDocument, PRFAQSection
```

**Files Importing This Model**:
- `services/prfaq_service.py` → Update import
- `services/research_prfaq/generator.py` → Update import
- `services/research_prfaq/validator.py` → Update import

---

#### topic_guides: Internal Processing Models

| Current Path | Target Path | Lines | Purpose |
|--------------|-------------|-------|---------|
| `topic_guides/models.py` | `services/topic_guides/internal_models.py` | 337 | Topic guide internal dataclasses |

**Models in this file**:
```python
# services/topic_guides/internal_models.py (formerly topic_guides/models.py)

@dataclass
class TopicGuideSummary:
    """Internal model for topic guide summaries."""
    topic_name: str
    total_files: int
    total_sections: int
    summary_text: str
    created_at: datetime

@dataclass
class FileSection:
    """Internal model for file sections during processing."""
    file_path: str
    section_number: int
    heading: str
    content: str
    metadata: Dict[str, str]

@dataclass
class ProcessingResult:
    """Internal model for processing results."""
    success: bool
    files_processed: int
    sections_extracted: int
    errors: List[str]
```

**Import Path Change**:
```python
# Before:
from synth_lab.topic_guides.models import TopicGuideSummary, FileSection

# After:
from synth_lab.services.topic_guides.internal_models import TopicGuideSummary, FileSection
```

**Files Importing This Model**:
- `services/topic_service.py` → Update import
- `services/topic_guides/file_processor.py` → Update import
- `services/topic_guides/summary_manager.py` → Update import

---

### Category 3: Specialized Models (Domain-Specific)
**Location**: Kept in specialized modules (NO CHANGES)

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| `trace_visualizer/models.py` | 194 | OpenTelemetry-inspired trace models | ✅ Keep as-is (no conflicts) |
| `gen_synth/*.py` | Various | Avatar generation, synth builder models | ✅ Keep as-is (self-contained) |

**Rationale**: These models are highly specialized and don't conflict with shared API models. They remain with their feature code.

---

## Import Migration Matrix

### All Files Requiring Import Updates

#### services/prfaq_service.py
```python
# Before:
from synth_lab.research_prfaq.generator import generate_prfaq_markdown, save_prfaq_markdown
from synth_lab.research_prfaq.models import PRFAQDocument

# After:
from synth_lab.services.research_prfaq.generator import generate_prfaq_markdown, save_prfaq_markdown
from synth_lab.services.research_prfaq.generation_models import PRFAQDocument
```

#### services/research_service.py
```python
# Before:
from synth_lab.research_agentic.batch_runner import run_batch_interviews
from synth_lab.research_agentic.runner import interview_synth

# After:
from synth_lab.services.research_agentic.batch_runner import run_batch_interviews
from synth_lab.services.research_agentic.runner import interview_synth
```

#### services/topic_service.py
```python
# Before:
from synth_lab.topic_guides.file_processor import process_files
from synth_lab.topic_guides.summary_manager import create_summary
from synth_lab.topic_guides.models import TopicGuideSummary

# After:
from synth_lab.services.topic_guides.file_processor import process_files
from synth_lab.services.topic_guides.summary_manager import create_summary
from synth_lab.services.topic_guides.internal_models import TopicGuideSummary
```

#### services/research_prfaq/generator.py
```python
# Before:
from synth_lab.research_prfaq.models import PRFAQDocument, PRFAQSection

# After:
from .generation_models import PRFAQDocument, PRFAQSection  # Relative import
```

#### services/research_prfaq/validator.py
```python
# Before:
from synth_lab.research_prfaq.models import PRFAQDocument

# After:
from .generation_models import PRFAQDocument  # Relative import
```

#### services/topic_guides/file_processor.py
```python
# Before:
from synth_lab.topic_guides.models import FileSection, ProcessingResult

# After:
from .internal_models import FileSection, ProcessingResult  # Relative import
```

#### services/topic_guides/summary_manager.py
```python
# Before:
from synth_lab.topic_guides.models import TopicGuideSummary

# After:
from .internal_models import TopicGuideSummary  # Relative import
```

#### services/research_agentic/__init__.py
```python
# New file to mark as package
# Empty or with explicit exports
```

---

## Directory Structure Changes

### Before Refactoring
```
src/synth_lab/
├── models/                        # API/DB models
│   ├── synth.py
│   ├── research.py
│   ├── prfaq.py                  # API models
│   ├── topic.py                  # API models
│   └── pagination.py
│
├── services/
│   ├── synth_service.py
│   ├── research_service.py        # ❌ Imports from research_agentic/
│   ├── prfaq_service.py           # ❌ Imports from research_prfaq/
│   └── topic_service.py
│
├── research_prfaq/                # ❌ Peer to services (wrong level)
│   ├── cli.py
│   ├── models.py                  # ❌ Conflicts with models/prfaq.py
│   ├── generator.py
│   ├── prompts.py
│   └── validator.py
│
├── topic_guides/                  # ❌ Peer to services (wrong level)
│   ├── cli.py
│   ├── models.py                  # ❌ Conflicts with models/topic.py
│   ├── file_processor.py
│   └── summary_manager.py
│
└── research_agentic/              # ❌ Peer to services (wrong level)
    ├── cli.py
    ├── runner.py
    ├── batch_runner.py
    ├── agent_definitions.py
    ├── instructions.py
    ├── tools.py
    └── summarizer.py
```

### After Refactoring
```
src/synth_lab/
├── models/                        # ✅ API/DB models (unchanged)
│   ├── synth.py
│   ├── research.py
│   ├── prfaq.py
│   ├── topic.py
│   └── pagination.py
│
└── services/                      # ✅ Clean layering
    ├── synth_service.py
    ├── research_service.py        # ✅ Imports from .research_agentic/
    ├── prfaq_service.py           # ✅ Imports from .research_prfaq/
    ├── topic_service.py           # ✅ Imports from .topic_guides/
    ├── errors.py
    │
    ├── research_agentic/          # ✅ Under services/
    │   ├── __init__.py            # 🆕 Package marker
    │   ├── runner.py
    │   ├── batch_runner.py
    │   ├── agent_definitions.py
    │   ├── instructions.py
    │   ├── tools.py
    │   └── summarizer.py
    │
    ├── research_prfaq/            # ✅ Under services/
    │   ├── __init__.py            # 🆕 Package marker
    │   ├── generation_models.py   # 🆕 Renamed (was models.py)
    │   ├── generator.py
    │   ├── prompts.py
    │   └── validator.py
    │
    └── topic_guides/              # ✅ Under services/
        ├── __init__.py            # 🆕 Package marker
        ├── internal_models.py     # 🆕 Renamed (was models.py)
        ├── file_processor.py
        └── summary_manager.py
```

---

## Migration Checklist

### Step 1: Rename Model Files
- [ ] `research_prfaq/models.py` → `research_prfaq/generation_models.py`
- [ ] `topic_guides/models.py` → `topic_guides/internal_models.py`
- [ ] Update imports in same directory (use relative imports)

### Step 2: Move Directories
- [ ] Move `research_agentic/` → `services/research_agentic/`
- [ ] Move `research_prfaq/` → `services/research_prfaq/`
- [ ] Move `topic_guides/` → `services/topic_guides/`
- [ ] Add `__init__.py` to each moved directory

### Step 3: Update Service Imports
- [ ] Update `services/prfaq_service.py` imports
- [ ] Update `services/research_service.py` imports
- [ ] Update `services/topic_service.py` imports

### Step 4: Update Internal Imports
- [ ] Update imports in `services/research_prfaq/*.py`
- [ ] Update imports in `services/topic_guides/*.py`
- [ ] Update imports in `services/research_agentic/*.py`

### Step 5: Verify No Broken Imports
- [ ] Run `pytest tests/` to catch import errors
- [ ] Run `ruff check .` to find unused imports
- [ ] Search codebase for old import paths

---

## Validation

### Import Path Verification
```bash
# Search for old import paths (should find ZERO after migration):
grep -r "from synth_lab.research_prfaq.models import" src/
grep -r "from synth_lab.topic_guides.models import" src/
grep -r "from synth_lab.research_agentic" src/ | grep -v "services.research_agentic"
grep -r "from synth_lab.research_prfaq" src/ | grep -v "services.research_prfaq"
grep -r "from synth_lab.topic_guides" src/ | grep -v "services.topic_guides"
```

### Test Verification
```bash
# All tests should pass after import updates:
pytest tests/ -v
```

### API Verification
```bash
# API should start without import errors:
uvicorn synth_lab.api.main:app --reload
# Check API docs still load:
curl http://localhost:8000/docs
```

---

## Summary

**Total Files Affected**: 15 files
- 2 model files renamed
- 3 directories moved
- 10 files with import updates

**No Data Changes**: Models structures remain identical, only locations change.

**Zero Breaking Changes**: API contracts (models/) unchanged, services maintain same interfaces.

**Validation**: Test suite ensures no regression, import verification confirms clean migration.
