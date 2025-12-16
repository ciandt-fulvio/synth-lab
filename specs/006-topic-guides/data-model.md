# Data Model: Topic Guides with Multi-Modal Context

**Feature**: `006-topic-guides`
**Date**: 2025-12-16
**Status**: Phase 1 Design

## Overview

This document defines the data structures for organizing and documenting multi-modal contextual materials (images, PDFs, documents) that synths reference during UX research interviews.

## Core Entities

### 1. TopicGuide

**Description**: A named collection of contextual materials organized in a dedicated file system directory.

**Attributes**:
- `name`: str - Unique identifier for the topic guide (directory name)
- `path`: Path - Full file system path to the topic guide directory
- `summary_file`: SummaryFile - The summary.md file containing context and file catalog
- `files`: list[ContextFile] - All context files in the directory (excluding summary.md)
- `created_at`: datetime - When the topic guide was first created
- `updated_at`: datetime - Last time files were documented/updated

**Validation Rules**:
- `name` must be a valid directory name (no special characters: `/\:*?"<>|`)
- `name` must not be empty
- `path` must exist on file system after creation
- `summary_file` must exist and be valid markdown

**Lifecycle**:
1. **Created**: Directory created with initial summary.md
2. **Updated**: Files added/modified, summary.md updated with new descriptions
3. **Accessed**: Loaded by synth interview system for context

**Example**:
```python
TopicGuide(
    name="amazon-ecommerce",
    path=Path("data/topic_guides/amazon-ecommerce"),
    summary_file=SummaryFile(...),
    files=[ContextFile(...), ContextFile(...)],
    created_at=datetime(2025, 12, 16, 10, 30),
    updated_at=datetime(2025, 12, 16, 15, 45)
)
```

---

### 2. SummaryFile

**Description**: A markdown file containing general context about the topic and a catalog of all documented files.

**Attributes**:
- `path`: Path - Full path to summary.md file
- `context_description`: str - General description of the topic guide ("contexto para o guide: {name}")
- `file_descriptions`: list[FileDescription] - Catalog of all documented files with hashes and descriptions

**File Structure**:
```markdown
# contexto para o guide: {topic_name}

[General context about this topic guide]

## FILE DESCRIPTION

- **{filename}** (hash: {content_hash})
  {AI-generated description}

- **{filename}** (hash: {content_hash})
  {AI-generated description}
```

**Validation Rules**:
- Must be valid markdown format
- Must contain `## FILE DESCRIPTION` section
- Each file entry must include filename, hash, and description

**Operations**:
- `parse()`: Read and parse summary.md into structured data
- `add_description(file_desc: FileDescription)`: Append new file description
- `has_file(filename: str, content_hash: str)`: Check if file with hash exists
- `write()`: Serialize and write to disk

**Example**:
```python
SummaryFile(
    path=Path("data/topic_guides/amazon-ecommerce/summary.md"),
    context_description="contexto para o guide: amazon-ecommerce",
    file_descriptions=[
        FileDescription(
            filename="product-page.png",
            content_hash="a3b5c7d9e1f3...",
            description="Screenshot da página de produto da Amazon mostrando detalhes do item, preço e botão de compra"
        )
    ]
)
```

---

### 3. ContextFile

**Description**: Any document or image stored in a topic guide directory that provides background information for synth interviews.

**Attributes**:
- `filename`: str - Name of the file (including extension)
- `path`: Path - Full file system path
- `file_type`: FileType - Enum of supported types (PNG, JPEG, PDF, MD, TXT)
- `size_bytes`: int - File size in bytes
- `content_hash`: str - MD5 or SHA hash of file contents
- `is_documented`: bool - Whether file has description in summary.md

**Validation Rules**:
- File must exist on file system
- `file_type` must be one of the supported types (PNG, JPEG, PDF, MD, TXT)
- `filename` must not be "summary.md" (excluded from documentation)
- `content_hash` must be computed from actual file contents

**Operations**:
- `compute_hash()`: Calculate MD5/SHA hash of file contents
- `detect_type()`: Determine FileType from extension
- `is_supported()`: Check if file type is in supported list
- `can_read()`: Attempt to read file to check for corruption/permissions

**Example**:
```python
ContextFile(
    filename="checkout-flow.pdf",
    path=Path("data/topic_guides/amazon-ecommerce/checkout-flow.pdf"),
    file_type=FileType.PDF,
    size_bytes=245760,
    content_hash="d4e6f8a0b2c4...",
    is_documented=False
)
```

---

### 4. FileDescription

**Description**: An AI-generated 10-50 word description of a context file's content, stored in summary.md.

**Attributes**:
- `filename`: str - Name of the file being described
- `content_hash`: str - Hash of file contents when description was generated
- `description`: str - AI-generated description (10-50 words)
- `generated_at`: datetime - When the description was created
- `is_placeholder`: bool - True if description is a placeholder (e.g., for LLM API failures)

**Validation Rules**:
- `description` must be 10-50 words (validated during generation)
- `description` must not be empty
- If `is_placeholder` is True, description should indicate the issue (e.g., "API failure - manual documentation needed")

**Operations**:
- `word_count()`: Count words in description
- `validate()`: Ensure description meets length requirements
- `to_markdown()`: Format as markdown entry for summary.md

**Example**:
```python
FileDescription(
    filename="product-page.png",
    content_hash="a3b5c7d9e1f3...",
    description="Screenshot da página de produto da Amazon mostrando detalhes do item, preço, avaliações de clientes e botão de adicionar ao carrinho. Interface desktop com navegação superior visível.",
    generated_at=datetime(2025, 12, 16, 15, 45),
    is_placeholder=False
)
```

---

## Enumerations

### FileType

**Description**: Supported file types for context files.

**Values**:
- `PNG` - PNG image format
- `JPEG` - JPEG/JPG image format
- `PDF` - PDF document format
- `MD` - Markdown text format
- `TXT` - Plain text format

**Detection Logic**:
```python
def detect_file_type(filename: str) -> FileType | None:
    ext = filename.lower().split('.')[-1]
    mapping = {
        'png': FileType.PNG,
        'jpg': FileType.JPEG,
        'jpeg': FileType.JPEG,
        'pdf': FileType.PDF,
        'md': FileType.MD,
        'txt': FileType.TXT
    }
    return mapping.get(ext)
```

---

## Relationships

```
TopicGuide (1) ─── (1) SummaryFile
    │
    └─── (0..*) ContextFile
              │
              └─── (0..1) FileDescription
```

**Cardinality Rules**:
- One TopicGuide has exactly one SummaryFile
- One TopicGuide has zero or more ContextFiles
- One ContextFile has zero or one FileDescription (zero if not yet documented)
- FileDescriptions are stored in SummaryFile, not ContextFile objects

---

## Data Persistence

### File System Structure

```
data/topic_guides/{topic_name}/
├── summary.md              # SummaryFile (managed by system)
├── {context_file_1}        # ContextFile (user-provided)
├── {context_file_2}        # ContextFile (user-provided)
└── ...
```

### Summary.md Format

**Header Section**:
```markdown
# contexto para o guide: {topic_name}

[Optional user-written context about the topic]
```

**File Descriptions Section**:
```markdown
## FILE DESCRIPTION

- **{filename}** (hash: {content_hash})
  {description}
```

**Example**:
```markdown
# contexto para o guide: amazon-ecommerce

Este guia contém materiais de contexto para entrevistas sobre a experiência de compra na Amazon.

## FILE DESCRIPTION

- **product-page.png** (hash: a3b5c7d9e1f3a5b7c9d1e3f5a7b9c1d3)
  Screenshot da página de produto da Amazon mostrando detalhes do item, preço, avaliações de clientes e botão de adicionar ao carrinho. Interface desktop com navegação superior visível.

- **checkout-flow.pdf** (hash: d4e6f8a0b2c4d6e8f0a2b4c6d8e0f2a4)
  Documento descrevendo o fluxo de checkout da Amazon com diagramas de cada etapa do processo de finalização de compra.

- **api-error.log** (hash: ERROR)
  API failure - manual documentation needed
```

---

## State Transitions

### ContextFile States

```
┌─────────────┐
│   Created   │ (file added to directory)
└──────┬──────┘
       │
       ├─→ Supported type? ──No──→ [Skipped - logged warning]
       │
       ├─→ Can read? ──No──→ [Skipped - silent]
       │
       └─→ Yes
           │
           ▼
    ┌──────────────┐
    │ Compute Hash │
    └──────┬───────┘
           │
           ├─→ Hash exists in summary.md? ──Yes──→ [Skipped - unchanged]
           │
           └─→ No
               │
               ▼
        ┌─────────────┐
        │  Send to    │
        │  LLM API    │
        └──────┬──────┘
               │
               ├─→ Success ──→ [Documented - description added]
               │
               └─→ Failure ──→ [Placeholder - manual doc needed]
```

---

## Data Validation Examples

### Valid TopicGuide Name
```python
# Valid
"amazon-ecommerce"
"ux-study-2024"
"mobile-app-v2"

# Invalid
"amazon/ecommerce"  # Contains '/'
"study:2024"        # Contains ':'
""                  # Empty
```

### Valid FileDescription
```python
# Valid (42 words)
FileDescription(
    filename="test.png",
    content_hash="abc123",
    description="Screenshot mostrando a tela principal do aplicativo com menu de navegação, cards de conteúdo e barra de pesquisa no topo. Interface mobile em português com tema claro ativado.",
    generated_at=datetime.now(),
    is_placeholder=False
)

# Invalid - too short (8 words)
FileDescription(
    filename="test.png",
    content_hash="abc123",
    description="Screenshot da tela principal do app.",  # < 10 words
    ...
)

# Valid placeholder
FileDescription(
    filename="error.pdf",
    content_hash="ERROR",
    description="API failure - manual documentation needed",
    generated_at=datetime.now(),
    is_placeholder=True
)
```

---

## Performance Considerations

### Hash Computation
- **MD5**: ~100-200 MB/s for typical files
- **Expected Time**: <0.1s for files up to 10MB
- **Caching**: Hashes stored in summary.md, not recomputed on every run

### File Scanning
- **Expected**: 10-100 files per topic guide
- **Performance**: O(n) scan of directory + O(m) parse of summary.md where m = documented files
- **Optimization**: Skip files already in summary.md with matching hash

### LLM API Calls
- **Bottleneck**: Network latency + API processing (~3-5s per file)
- **Batch Processing**: Process files sequentially to avoid rate limits
- **Error Recovery**: Exponential backoff on failures

---

## Integration with Synth Interviews

### Context Loading

When a synth interview specifies a topic guide:

1. **Load TopicGuide**: Parse summary.md to get all FileDescriptions
2. **Include in Prompt**: Add file descriptions to LLM context
3. **Reference Format**:
   ```
   Context Materials:
   - product-page.png: Screenshot da página de produto...
   - checkout-flow.pdf: Documento descrevendo o fluxo...
   ```

### Example Integration

```python
# In research/interview.py
def conduct_interview(synth_id: str, topic_guide: str | None = None):
    context_materials = []

    if topic_guide:
        guide = load_topic_guide(topic_guide)
        context_materials = guide.summary_file.file_descriptions

    prompt = build_prompt(
        synth=load_synth(synth_id),
        context=context_materials
    )

    # ... continue with interview
```

---

## Summary

This data model provides:
- **Clear entity definitions** with validation rules and lifecycles
- **File system persistence** with structured markdown format
- **Content-based change detection** using file hashes
- **Robust error handling** with placeholder support
- **Integration pattern** for synth interviews

All entities follow the principle of simplicity (no unnecessary abstractions) while maintaining clear separation of concerns between file management, description generation, and synth integration.
