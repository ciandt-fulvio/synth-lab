# Data Model: synth-lab REST API

**Feature**: 010-rest-api | **Date**: 2025-12-19

## Database Schema

### Overview

Database: `output/synthlab.db` (SQLite with JSON1 extension)

```sql
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
PRAGMA synchronous=NORMAL;
```

---

### Table: `synths`

Stores synthetic persona profiles with nested JSON data.

```sql
CREATE TABLE synths (
    id TEXT PRIMARY KEY,                    -- 6-character alphanumeric ID
    nome TEXT NOT NULL,                     -- Display name
    arquetipo TEXT,                         -- Archetype classification
    descricao TEXT,                         -- Brief description
    link_photo TEXT,                        -- External photo URL
    avatar_path TEXT,                       -- Local avatar file path
    created_at TEXT NOT NULL,               -- ISO 8601 timestamp
    version TEXT DEFAULT '2.0.0',           -- Schema version

    -- Nested JSON columns
    demografia TEXT CHECK(json_valid(demografia) OR demografia IS NULL),
    psicografia TEXT CHECK(json_valid(psicografia) OR psicografia IS NULL),
    deficiencias TEXT CHECK(json_valid(deficiencias) OR deficiencias IS NULL),
    capacidades_tecnologicas TEXT CHECK(json_valid(capacidades_tecnologicas) OR capacidades_tecnologicas IS NULL)
);

-- Indexes for common queries
CREATE INDEX idx_synths_arquetipo ON synths(arquetipo);
CREATE INDEX idx_synths_created_at ON synths(created_at DESC);
CREATE INDEX idx_synths_nome ON synths(nome);
```

**Example JSON Queries**:
```sql
-- Get synth age
SELECT json_extract(demografia, '$.idade') as idade FROM synths WHERE id = ?;

-- Filter by region
SELECT * FROM synths
WHERE json_extract(demografia, '$.localizacao.regiao') = 'Nordeste';

-- Search by technology level
SELECT * FROM synths
WHERE json_extract(capacidades_tecnologicas, '$.nivel_geral') = 'intermediario';
```

---

### Table: `research_executions`

Tracks research execution metadata.

```sql
CREATE TABLE research_executions (
    exec_id TEXT PRIMARY KEY,               -- Format: batch_{topic}_{timestamp}
    topic_name TEXT NOT NULL,               -- Reference to topic guide
    status TEXT NOT NULL DEFAULT 'pending', -- pending, running, completed, failed
    synth_count INTEGER NOT NULL,           -- Number of synths selected
    successful_count INTEGER DEFAULT 0,     -- Completed interviews
    failed_count INTEGER DEFAULT 0,         -- Failed interviews
    model TEXT DEFAULT 'gpt-5-mini',        -- LLM model used
    max_turns INTEGER DEFAULT 6,            -- Max interview turns
    started_at TEXT NOT NULL,               -- ISO 8601 timestamp
    completed_at TEXT,                      -- ISO 8601 timestamp (nullable)
    summary_path TEXT,                      -- Path to summary markdown

    CHECK(status IN ('pending', 'running', 'completed', 'failed'))
);

CREATE INDEX idx_executions_topic ON research_executions(topic_name);
CREATE INDEX idx_executions_status ON research_executions(status);
CREATE INDEX idx_executions_started ON research_executions(started_at DESC);
```

---

### Table: `transcripts`

Stores interview transcripts linked to executions.

```sql
CREATE TABLE transcripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exec_id TEXT NOT NULL REFERENCES research_executions(exec_id),
    synth_id TEXT NOT NULL REFERENCES synths(id),
    status TEXT NOT NULL DEFAULT 'pending', -- pending, completed, failed
    turn_count INTEGER DEFAULT 0,           -- Number of turns completed
    timestamp TEXT NOT NULL,                -- ISO 8601 timestamp
    file_path TEXT,                         -- Path to transcript JSON
    messages TEXT CHECK(json_valid(messages) OR messages IS NULL),  -- Interview messages

    UNIQUE(exec_id, synth_id),
    CHECK(status IN ('pending', 'completed', 'failed'))
);

CREATE INDEX idx_transcripts_exec ON transcripts(exec_id);
CREATE INDEX idx_transcripts_synth ON transcripts(synth_id);
```

**Messages JSON Structure**:
```json
[
  {
    "speaker": "Interviewer",
    "text": "Como você se sente ao...",
    "internal_notes": "Notas estratégicas..."
  },
  {
    "speaker": "Ravy Lopes",
    "text": "Eu me sinto..."
  }
]
```

---

### Table: `prfaq_metadata`

Stores PR-FAQ generation metadata and validation status.

```sql
CREATE TABLE prfaq_metadata (
    exec_id TEXT PRIMARY KEY REFERENCES research_executions(exec_id),
    generated_at TEXT NOT NULL,             -- ISO 8601 timestamp
    model TEXT DEFAULT 'gpt-5-mini',        -- LLM model used
    validation_status TEXT DEFAULT 'valid', -- valid, invalid, pending
    confidence_score REAL,                  -- 0.0 to 1.0
    headline TEXT,                          -- Press release headline
    one_liner TEXT,                         -- One-line summary
    faq_count INTEGER DEFAULT 0,            -- Number of FAQ items
    markdown_path TEXT,                     -- Path to markdown file
    json_path TEXT,                         -- Path to structured JSON

    CHECK(validation_status IN ('valid', 'invalid', 'pending'))
);

CREATE INDEX idx_prfaq_generated ON prfaq_metadata(generated_at DESC);
```

---

### Table: `topic_guides_cache`

Optional cache for topic guide metadata (filesystem is source of truth).

```sql
CREATE TABLE topic_guides_cache (
    name TEXT PRIMARY KEY,                  -- Directory name
    display_name TEXT,                      -- Human-readable name
    description TEXT,                       -- Context description
    question_count INTEGER DEFAULT 0,       -- Number of questions
    file_count INTEGER DEFAULT 0,           -- Number of associated files
    script_hash TEXT,                       -- Hash of script.json for cache invalidation
    created_at TEXT,                        -- First seen timestamp
    updated_at TEXT                         -- Last updated timestamp
);
```

---

### Table: `schema_migrations`

Tracks database schema versions.

```sql
CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL,
    description TEXT
);

-- Initial migration
INSERT INTO schema_migrations (version, applied_at, description)
VALUES (1, datetime('now'), 'Initial schema creation');
```

---

## Entity-Relationship Diagram

```
┌─────────────────┐       ┌──────────────────────┐
│     synths      │       │ research_executions  │
├─────────────────┤       ├──────────────────────┤
│ id (PK)         │◄──┐   │ exec_id (PK)         │
│ nome            │   │   │ topic_name           │
│ arquetipo       │   │   │ status               │
│ descricao       │   │   │ synth_count          │
│ link_photo      │   │   │ started_at           │
│ avatar_path     │   │   │ completed_at         │
│ created_at      │   │   │ summary_path         │
│ demografia (J)  │   │   └──────────┬───────────┘
│ psicografia (J) │   │              │
│ deficiencias (J)│   │              │ 1
│ capac_tec (J)   │   │              │
└─────────────────┘   │              ▼
                      │   ┌──────────────────────┐
                      │   │     transcripts      │
                      │   ├──────────────────────┤
                      └───┤ synth_id (FK)        │
                          │ exec_id (FK)         │
                          │ status               │
                          │ turn_count           │
                          │ timestamp            │
                          │ messages (J)         │
                          └──────────────────────┘
                                     │
                                     ▲ 1
                                     │
┌─────────────────┐       ┌──────────────────────┐
│ topic_guides_   │       │   prfaq_metadata     │
│     cache       │       ├──────────────────────┤
├─────────────────┤       │ exec_id (PK/FK)      │
│ name (PK)       │       │ generated_at         │
│ display_name    │       │ validation_status    │
│ question_count  │       │ confidence_score     │
│ file_count      │       │ headline             │
│ script_hash     │       │ faq_count            │
└─────────────────┘       │ markdown_path        │
                          └──────────────────────┘

(J) = JSON column
```

---

## Domain Models (Pydantic)

### Synth Models

```python
# models/synth.py
from pydantic import BaseModel, Field
from datetime import datetime

class Demographics(BaseModel):
    idade: int
    genero: str
    localizacao: dict  # {cidade, estado, regiao}
    educacao: str
    ocupacao: str
    renda_familiar: str

class Psychographics(BaseModel):
    valores: list[str]
    interesses: list[str]
    estilo_vida: str
    personalidade: str

class Disabilities(BaseModel):
    tipo: str | None = None
    descricao: str | None = None
    nivel: str | None = None

class TechCapabilities(BaseModel):
    nivel_geral: str
    dispositivos: list[str]
    apps_frequentes: list[str]
    comportamento_digital: str

class SynthBase(BaseModel):
    id: str = Field(..., min_length=6, max_length=6)
    nome: str
    arquetipo: str | None = None
    descricao: str | None = None
    link_photo: str | None = None
    avatar_path: str | None = None
    created_at: datetime
    version: str = "2.0.0"

class SynthSummary(SynthBase):
    """Used in list endpoints."""
    pass

class SynthDetail(SynthBase):
    """Used in detail endpoint."""
    demografia: Demographics | None = None
    psicografia: Psychographics | None = None
    deficiencias: Disabilities | None = None
    capacidades_tecnologicas: TechCapabilities | None = None
```

### Research Models

```python
# models/research.py
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ResearchExecutionBase(BaseModel):
    exec_id: str
    topic_name: str
    status: ExecutionStatus
    synth_count: int
    started_at: datetime
    completed_at: datetime | None = None

class ResearchExecutionDetail(ResearchExecutionBase):
    successful_count: int = 0
    failed_count: int = 0
    model: str = "gpt-xxxx"
    max_turns: int = 6
    summary_available: bool = False
    prfaq_available: bool = False

class TranscriptSummary(BaseModel):
    synth_id: str
    synth_name: str
    turn_count: int
    timestamp: datetime
    status: str

class TranscriptDetail(BaseModel):
    metadata: dict
    messages: list[dict]

class ResearchExecuteRequest(BaseModel):
    topic_name: str
    synth_ids: list[str] | None = None
    synth_count: int | None = None
    max_turns: int = Field(default=6, ge=1, le=20)
    max_concurrent: int = Field(default=10, ge=1, le=50)
    model: str = "gpt-xxxx"
    generate_summary: bool = True
```

### Topic Models

```python
# models/topic.py
from pydantic import BaseModel
from datetime import datetime

class TopicFile(BaseModel):
    filename: str
    content_hash: str | None = None
    description: str | None = None

class TopicQuestion(BaseModel):
    id: int
    ask: str
    context_examples: dict | None = None

class TopicSummary(BaseModel):
    name: str
    display_name: str | None = None
    description: str | None = None
    question_count: int = 0
    file_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

class TopicDetail(TopicSummary):
    summary: dict | None = None
    script: list[TopicQuestion] = []
    files: list[TopicFile] = []
```

### PR-FAQ Models

```python
# models/prfaq.py
from pydantic import BaseModel
from datetime import datetime

class PRFAQSummary(BaseModel):
    exec_id: str
    topic_name: str
    headline: str | None = None
    one_liner: str | None = None
    faq_count: int = 0
    generated_at: datetime
    validation_status: str = "valid"
    confidence_score: float | None = None

class PRFAQGenerateRequest(BaseModel):
    exec_id: str
    model: str = "gpt-xxxx"

class PRFAQGenerateResponse(BaseModel):
    exec_id: str
    status: str = "generated"
    generated_at: datetime
    validation_status: str
    confidence_score: float | None = None
```

### Pagination Models

```python
# models/pagination.py
from pydantic import BaseModel, Field
from typing import Generic, TypeVar

T = TypeVar("T")

class PaginationParams(BaseModel):
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
    sort_by: str | None = None
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")

class PaginationMeta(BaseModel):
    total: int
    limit: int
    offset: int
    has_next: bool

class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T]
    pagination: PaginationMeta
```

---

## Filesystem Structure

Files that remain on filesystem (not in SQLite):

```
output/
├── synthlab.db                     # SQLite database
├── synths/
│   ├── synths.json                 # Backup/migration source
│   └── avatar/
│       └── {synth_id}.png          # Avatar images
├── transcripts/
│   ├── {topic}_{synth_id}_{ts}.json    # Individual transcripts
│   └── batch_{topic}_{ts}/         # Batch directories
│       └── {synth_id}.json
├── traces/
│   └── {topic}_{synth_id}_{ts}.json    # Execution traces
└── reports/
    ├── batch_{topic}_{ts}_summary.md   # Research summaries
    └── batch_{topic}_{ts}_prfaq.md     # PR-FAQ documents

data/topic_guides/
└── {topic_name}/
    ├── script.json                 # Interview script
    ├── summary.md                  # Context summary
    └── *.png                       # Screenshot files
```

---

## Migration Script

```python
# scripts/migrate_to_sqlite.py
"""Migrate existing JSON data to SQLite database."""

import json
import sqlite3
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path("output")
DB_PATH = OUTPUT_DIR / "synthlab.db"
SYNTHS_JSON = OUTPUT_DIR / "synths" / "synths.json"

def create_schema(conn: sqlite3.Connection) -> None:
    """Create database schema."""
    conn.executescript("""
        PRAGMA journal_mode=WAL;
        PRAGMA foreign_keys=ON;

        CREATE TABLE IF NOT EXISTS synths (
            id TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            arquetipo TEXT,
            descricao TEXT,
            link_photo TEXT,
            avatar_path TEXT,
            created_at TEXT NOT NULL,
            version TEXT DEFAULT '2.0.0',
            demografia TEXT,
            psicografia TEXT,
            deficiencias TEXT,
            capacidades_tecnologicas TEXT
        );

        CREATE TABLE IF NOT EXISTS research_executions (
            exec_id TEXT PRIMARY KEY,
            topic_name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'completed',
            synth_count INTEGER NOT NULL,
            successful_count INTEGER DEFAULT 0,
            failed_count INTEGER DEFAULT 0,
            model TEXT DEFAULT 'gpt-5-mini',
            max_turns INTEGER DEFAULT 6,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            summary_path TEXT
        );

        CREATE TABLE IF NOT EXISTS transcripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exec_id TEXT NOT NULL,
            synth_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'completed',
            turn_count INTEGER DEFAULT 0,
            timestamp TEXT NOT NULL,
            file_path TEXT,
            messages TEXT,
            UNIQUE(exec_id, synth_id)
        );

        CREATE TABLE IF NOT EXISTS prfaq_metadata (
            exec_id TEXT PRIMARY KEY,
            generated_at TEXT NOT NULL,
            model TEXT DEFAULT 'gpt-5-mini',
            validation_status TEXT DEFAULT 'valid',
            confidence_score REAL,
            headline TEXT,
            one_liner TEXT,
            faq_count INTEGER DEFAULT 0,
            markdown_path TEXT,
            json_path TEXT
        );

        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL,
            description TEXT
        );

        INSERT OR IGNORE INTO schema_migrations (version, applied_at, description)
        VALUES (1, datetime('now'), 'Initial schema creation');
    """)

def migrate_synths(conn: sqlite3.Connection) -> int:
    """Migrate synths from JSON to SQLite."""
    if not SYNTHS_JSON.exists():
        return 0

    with open(SYNTHS_JSON) as f:
        synths = json.load(f)

    count = 0
    for synth in synths:
        avatar_path = f"output/synths/avatar/{synth['id']}.png"
        if not Path(avatar_path).exists():
            avatar_path = None

        conn.execute("""
            INSERT OR REPLACE INTO synths
            (id, nome, arquetipo, descricao, link_photo, avatar_path, created_at, version,
             demografia, psicografia, deficiencias, capacidades_tecnologicas)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            synth["id"],
            synth["nome"],
            synth.get("arquetipo"),
            synth.get("descricao"),
            synth.get("link_photo"),
            avatar_path,
            synth.get("created_at", datetime.now().isoformat()),
            synth.get("version", "2.0.0"),
            json.dumps(synth.get("demografia")) if synth.get("demografia") else None,
            json.dumps(synth.get("psicografia")) if synth.get("psicografia") else None,
            json.dumps(synth.get("deficiencias")) if synth.get("deficiencias") else None,
            json.dumps(synth.get("capacidades_tecnologicas")) if synth.get("capacidades_tecnologicas") else None,
        ))
        count += 1

    return count

def main():
    """Run migration."""
    conn = sqlite3.connect(DB_PATH)
    try:
        create_schema(conn)
        synth_count = migrate_synths(conn)
        conn.commit()
        print(f"Migration complete: {synth_count} synths migrated")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
```
