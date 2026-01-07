# Data Model: Synth Material Integration

**Date**: 2026-01-06
**Feature**: 029-synth-material-integration

## Overview

This feature reuses the existing `ExperimentMaterial` entity (already implemented in feature 001-experiment-materials). No new database tables or migrations are required. This document defines the data structures and transformations needed for materials integration into LLM contexts.

---

## Existing Entities (Reused)

### ExperimentMaterial

**Description**: Metadata for files attached to experiments (images, PDFs, videos)

**Source**: `src/synth_lab/models/orm/material.py`

**Fields**:
- `id`: String (PK) - UUID-style ID (format: `mat_XXXXXX`)
- `experiment_id`: String (FK) - References `experiments.id`
- `file_type`: String - Category: 'image', 'video', 'document'
- `file_url`: String - S3 URL of the file
- `thumbnail_url`: String (nullable) - S3 URL of thumbnail
- `file_name`: String - Original filename
- `file_size`: Integer - File size in bytes
- `mime_type`: String - MIME type (e.g., "image/png")
- `material_type`: String - Purpose: 'design', 'prototype', 'competitor', 'spec', 'other'
- `description`: String (nullable) - AI-generated description (max 30 words)
- `description_status`: String - Status: 'pending', 'generating', 'completed', 'failed'
- `display_order`: Integer - Display order (0-indexed)
- `created_at`: String - ISO timestamp

**Relationships**:
- `experiment`: Many-to-one with `Experiment`

**Indexes**:
- `idx_experiment_materials_experiment` - On `experiment_id`
- `idx_experiment_materials_type` - On `material_type`
- `idx_experiment_materials_order` - On `experiment_id, display_order`
- `idx_experiment_materials_status` - On `description_status`

---

## New Data Structures (In-Memory)

These structures are used at runtime for LLM integration. They are NOT persisted to the database.

### MaterialContext

**Description**: In-memory representation of materials formatted for LLM prompts

**Purpose**: Intermediate structure between ORM model and prompt string

**Python Definition**:
```python
from pydantic import BaseModel

class MaterialContext(BaseModel):
    """Materials context for LLM prompts."""

    material_id: str  # mat_XXXXXX
    material_type: str  # design, prototype, competitor, spec, other
    file_name: str
    mime_type: str
    description: str | None
    file_size_mb: float  # Converted from bytes for readability

    @property
    def display_label(self) -> str:
        """Human-readable label for prompt."""
        return f"[{self.material_type}] {self.file_name} ({self.mime_type})"
```

**Transformation**:
```python
def to_material_context(material: ExperimentMaterial) -> MaterialContext:
    """Convert ORM model to context structure."""
    return MaterialContext(
        material_id=material.id,
        material_type=material.material_type,
        file_name=material.file_name,
        mime_type=material.mime_type,
        description=material.description,
        file_size_mb=round(material.file_size / 1_000_000, 2)
    )
```

---

### MaterialReference

**Description**: Citation of a material in generated content (PR-FAQs, summaries)

**Purpose**: Structured format for material references that appear in LLM outputs

**Python Definition**:
```python
from pydantic import BaseModel
import re

class MaterialReference(BaseModel):
    """Reference to a material in generated content."""

    material_id: str  # mat_XXXXXX or filename
    reference_type: Literal["material_id", "filename_timestamp", "filename"]
    timestamp: str | None = None  # For videos: "00:12" or "1:23"
    context: str  # The insight or observation tied to this reference

    @classmethod
    def from_markdown_link(cls, link: str) -> "MaterialReference":
        """
        Parse material reference from markdown link.

        Formats:
        - [text](mat_abc123)
        - [text](video.mp4@00:12)
        - [text](image.png)
        """
        pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        match = re.match(pattern, link)
        if not match:
            raise ValueError(f"Invalid reference format: {link}")

        context, ref = match.groups()

        # Video with timestamp: filename@HH:MM or filename@MM:SS
        if '@' in ref:
            filename, timestamp = ref.split('@', 1)
            return cls(
                material_id=filename,
                reference_type="filename_timestamp",
                timestamp=timestamp,
                context=context
            )
        # Material ID: mat_XXXXXX
        elif ref.startswith('mat_'):
            return cls(
                material_id=ref,
                reference_type="material_id",
                context=context
            )
        # Filename only
        else:
            return cls(
                material_id=ref,
                reference_type="filename",
                context=context
            )
```

---

### MaterialToolResponse

**Description**: Response format from material retrieval tool

**Purpose**: Standardized return value for LLM function calling

**Python Definition**:
```python
from pydantic import BaseModel
from typing import Literal

class MaterialToolResponse(BaseModel):
    """Response from ver_material() tool."""

    status: Literal["success", "error"]
    material_id: str
    data_uri: str | None  # "data:image/png;base64,..." or None if error
    error_message: str | None
    mime_type: str | None
    file_name: str | None

    @classmethod
    def success(cls, material_id: str, data_uri: str, mime_type: str, file_name: str):
        """Create success response."""
        return cls(
            status="success",
            material_id=material_id,
            data_uri=data_uri,
            error_message=None,
            mime_type=mime_type,
            file_name=file_name
        )

    @classmethod
    def error(cls, material_id: str, error_message: str):
        """Create error response."""
        return cls(
            status="error",
            material_id=material_id,
            data_uri=None,
            error_message=error_message,
            mime_type=None,
            file_name=None
        )
```

---

## Data Flows

### Flow 1: Materials → Interview System

```
1. Fetch Materials (DB)
   ExperimentMaterialRepository.get_by_experiment(experiment_id)
   → List[ExperimentMaterial]

2. Transform to Context (In-Memory)
   [to_material_context(m) for m in materials]
   → List[MaterialContext]

3. Format for Prompt (String)
   format_materials_for_prompt(contexts, context="interview")
   → str (markdown section)

4. Inject into System Prompt
   interviewer_instructions.format(materials_section=prompt_section)
   → Complete system prompt with materials

5. Agent Runtime (Tool Call)
   LLM calls: ver_material(material_id="mat_abc123")
   → MaterialToolResponse.success(...) with base64 data
```

---

### Flow 2: Interview → PR-FAQ with Material References

```
1. Interview Completion
   Synth responses mention materials
   → Raw interview transcript with material mentions

2. PR-FAQ Generation (LLM)
   System prompt includes materials list
   → Generated PR-FAQ with markdown references

3. Parse References (Post-Processing)
   Extract all [text](ref) patterns
   → List[MaterialReference]

4. Validate References
   Check material_ids exist in experiment
   → Valid references only

5. Store PR-FAQ
   Save with embedded material references
   → Frontend renders with clickable links
```

---

### Flow 3: Exploration → Summary with Materials

```
1. Fetch Materials (DB)
   Same as Flow 1
   → List[ExperimentMaterial]

2. Preload Material Content (if <10 items)
   Download all from S3, encode base64
   → Dict[material_id, data_uri]

3. Build Exploration Prompt
   Include materials metadata + preloaded content
   → Complete prompt for exploration

4. Generate Summary
   LLM has all materials in context
   → Summary with material references

5. Parse and Validate
   Same as Flow 2
   → Summary with validated references
```

---

## Validation Rules

### Material Context Validation

1. **Token Budget**:
   - Materials section must not exceed 2000 tokens
   - Estimation: ~100 tokens per material
   - Limit: 20 materials per prompt (soft limit)
   - Action if exceeded: Log warning, truncate list, add note in prompt

2. **File Size Validation**:
   - Images/PDFs: Max 50MB per file
   - Videos: Max 50MB for full video, else keyframe extraction
   - Total request size: <200MB (OpenAI limit)

3. **MIME Type Validation**:
   - Supported: image/png, image/jpeg, image/gif, image/webp, application/pdf, video/mp4, video/webm
   - Unsupported types: Skip with warning, don't fail entire process

### Material Reference Validation

1. **Format Validation**:
   - Must match regex: `\[.*?\]\((mat_\w+|[\w.-]+(@[\d:]+)?)\)`
   - Timestamp format: `HH:MM` or `MM:SS` or `H:MM:SS`

2. **Existence Validation**:
   - If reference uses `mat_XXXXXX`, verify ID exists in experiment's materials
   - If reference uses filename, fuzzy match to experiment's materials
   - Invalid references: Keep as-is, log warning

3. **Completeness Validation**:
   - PR-FAQ must have "Materiais de Referência" section if materials exist
   - At least 1 material reference per 3 materials attached (coverage metric)

---

## State Transitions

### Material Description Status

```
pending → generating → completed
pending → generating → failed
```

**Note**: This feature doesn't modify description status. It only reads the `description` field when available. Description generation is handled by feature 001-experiment-materials.

---

## Performance Considerations

### Query Optimization

- Use existing indexes on `experiment_id`
- Fetch materials with single query: `get_by_experiment(experiment_id)`
- No N+1 queries (materials loaded once per interview/generation)

### Caching Strategy

- **Interview Session**: Cache materials in memory for duration
- **PR-FAQ Generation**: No caching (one-time operation)
- **Exploration**: Cache during prompt building, discard after

### S3 Download Optimization

- Async downloads using `asyncio.gather()`
- Parallel limit: 5 concurrent downloads
- Timeout per download: 10 seconds
- Retry logic: 3 attempts with exponential backoff (already in material_service)

---

## Error Handling

### Missing Materials

**Scenario**: Material ID in database but file not in S3

**Handling**:
```python
try:
    data = download_from_s3(material.file_url)
except S3Error:
    logger.warning(f"Material {material.id} not found in S3")
    return MaterialToolResponse.error(
        material.id,
        "Material não encontrado. Arquivo pode ter sido removido."
    )
```

### Corrupted Files

**Scenario**: File exists but is corrupted/unreadable

**Handling**:
- Try to download
- If base64 encoding fails, return error response
- LLM continues without this material

### Token Limit Exceeded

**Scenario**: Too many materials (>20)

**Handling**:
```python
if len(materials) > 20:
    logger.warning(f"Experiment has {len(materials)} materials, truncating to 20")
    materials = materials[:20]
    prompt_note = "\n\n⚠️ Nota: Apenas os primeiros 20 materiais são mostrados."
```

---

## Summary

- **No database changes**: Reuses existing `experiment_materials` table
- **3 new in-memory structures**: MaterialContext, MaterialReference, MaterialToolResponse
- **3 data flows**: Interview, PR-FAQ, Exploration
- **Validation rules**: Token budget, file size, MIME types, reference format
- **Performance**: Async downloads, caching, query optimization
- **Error handling**: Graceful degradation, no failures on missing/corrupted materials
