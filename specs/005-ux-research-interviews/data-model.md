# Data Model: UX Research Interviews with Synths

**Feature Branch**: `005-ux-research-interviews`
**Created**: 2025-12-16

## Entity Relationship Diagram

```text
┌─────────────────────┐
│   InterviewSession  │
├─────────────────────┤
│ id: str (UUID)      │
│ synth_id: str       │──────┐
│ topic_guide_path    │      │
│ max_rounds: int     │      │
│ start_time: datetime│      │
│ end_time: datetime  │      │
│ status: Status      │      │
│ model_used: str     │      │
└─────────────────────┘      │
         │                    │
         │ 1:N                │ N:1
         ▼                    ▼
┌─────────────────────┐  ┌─────────────────────┐
│      Message        │  │       Synth         │
├─────────────────────┤  ├─────────────────────┤
│ speaker: Speaker    │  │ (existing entity)   │
│ content: str        │  │ id: str             │
│ timestamp: datetime │  │ nome: str           │
│ internal_notes: str?│  │ arquetipo: str      │
│ round_number: int   │  │ demografia: dict    │
└─────────────────────┘  │ psicografia: dict   │
                         │ comportamento: dict │
┌─────────────────────┐  │ vieses: dict        │
│    Transcript       │  │ ...                 │
├─────────────────────┤  └─────────────────────┘
│ session: Session    │
│ synth_snapshot: dict│
│ messages: Message[] │
└─────────────────────┘

┌─────────────────────┐
│ InterviewResponse   │
├─────────────────────┤
│ message: str        │
│ should_end: bool    │
│ internal_notes: str?│
└─────────────────────┘
```

## Entities

### InterviewSession

Representa uma sessão completa de entrevista de pesquisa UX.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| id | str | UUID único da sessão | UUID v4 format |
| synth_id | str | ID do synth entrevistado | 6 chars alphanumeric |
| topic_guide_path | str \| None | Caminho do guia de tópicos | Valid file path or None |
| max_rounds | int | Limite máximo de turnos | 1-100, default 10 |
| start_time | datetime | Início da entrevista | ISO 8601 with timezone |
| end_time | datetime \| None | Fim da entrevista | ISO 8601 with timezone |
| status | SessionStatus | Estado da sessão | Enum value |
| model_used | str | Modelo LLM utilizado | Non-empty string |

**State Transitions**:
```
[created] → [in_progress] → [completed]
                         → [interrupted]
                         → [error]
```

### SessionStatus (Enum)

| Value | Description |
|-------|-------------|
| created | Sessão criada, ainda não iniciada |
| in_progress | Entrevista em andamento |
| completed | Entrevista concluída normalmente |
| interrupted | Entrevista interrompida pelo usuário |
| error | Entrevista terminada por erro |

### Message

Representa um turno de conversação na entrevista.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| speaker | Speaker | Quem falou | Enum value |
| content | str | Texto da mensagem | Non-empty string |
| timestamp | datetime | Momento da mensagem | ISO 8601 with timezone |
| internal_notes | str \| None | Notas internas (não exibidas) | Optional string |
| round_number | int | Número do turno | 1-based, >= 1 |

### Speaker (Enum)

| Value | Description |
|-------|-------------|
| interviewer | Entrevistador LLM |
| synth | Synth sendo entrevistado |

### InterviewResponse

Formato de resposta estruturada retornada por ambos os LLMs.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| message | str | Texto falado na entrevista | Non-empty string |
| should_end | bool | Sinaliza fim da entrevista | Only interviewer sets True |
| internal_notes | str \| None | Anotações internas opcionais | Optional string |

### Transcript

Documento completo da entrevista para persistência.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| session | InterviewSession | Metadados da sessão | Valid session object |
| synth_snapshot | dict | Cópia completa do synth | Valid synth schema v2.0.0 |
| messages | list[Message] | Lista de mensagens | Ordered by timestamp |

## Pydantic Models

```python
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from typing import Any


class SessionStatus(str, Enum):
    """Status da sessão de entrevista."""
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    INTERRUPTED = "interrupted"
    ERROR = "error"


class Speaker(str, Enum):
    """Identificador do participante da conversa."""
    INTERVIEWER = "interviewer"
    SYNTH = "synth"


class InterviewResponse(BaseModel):
    """Formato de resposta estruturada do LLM."""
    message: str = Field(..., min_length=1, description="Texto da fala")
    should_end: bool = Field(default=False, description="Sinaliza fim da entrevista")
    internal_notes: str | None = Field(default=None, description="Notas internas opcionais")


class Message(BaseModel):
    """Uma mensagem na conversa da entrevista."""
    speaker: Speaker
    content: str = Field(..., min_length=1)
    timestamp: datetime
    internal_notes: str | None = None
    round_number: int = Field(..., ge=1)


class InterviewSession(BaseModel):
    """Metadados de uma sessão de entrevista."""
    id: str = Field(..., pattern=r"^[a-f0-9-]{36}$")
    synth_id: str = Field(..., pattern=r"^[a-zA-Z0-9]{6}$")
    topic_guide_path: str | None = None
    max_rounds: int = Field(default=10, ge=1, le=100)
    start_time: datetime
    end_time: datetime | None = None
    status: SessionStatus = SessionStatus.CREATED
    model_used: str = Field(..., min_length=1)


class Transcript(BaseModel):
    """Transcrição completa da entrevista."""
    session: InterviewSession
    synth_snapshot: dict[str, Any]  # Full synth data at interview time
    messages: list[Message] = Field(default_factory=list)
```

## Relationships

1. **InterviewSession → Synth**: Many-to-One
   - Uma sessão referencia um synth pelo `synth_id`
   - Um synth pode ter múltiplas sessões de entrevista

2. **InterviewSession → Messages**: One-to-Many
   - Uma sessão contém múltiplas mensagens
   - Mensagens são ordenadas por `timestamp`

3. **Transcript → InterviewSession**: One-to-One
   - Cada transcript contém exatamente uma sessão

4. **Transcript → Synth Snapshot**: Embedded
   - Cópia completa do synth no momento da entrevista
   - Preserva estado mesmo se synth for modificado depois

## File Storage Format

### Transcript JSON Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "session": {
      "type": "object",
      "properties": {
        "id": { "type": "string", "format": "uuid" },
        "synth_id": { "type": "string", "pattern": "^[a-zA-Z0-9]{6}$" },
        "topic_guide_path": { "type": ["string", "null"] },
        "max_rounds": { "type": "integer", "minimum": 1, "maximum": 100 },
        "start_time": { "type": "string", "format": "date-time" },
        "end_time": { "type": ["string", "null"], "format": "date-time" },
        "status": { "enum": ["created", "in_progress", "completed", "interrupted", "error"] },
        "model_used": { "type": "string" }
      },
      "required": ["id", "synth_id", "max_rounds", "start_time", "status", "model_used"]
    },
    "synth_snapshot": { "type": "object" },
    "messages": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "speaker": { "enum": ["interviewer", "synth"] },
          "content": { "type": "string", "minLength": 1 },
          "timestamp": { "type": "string", "format": "date-time" },
          "internal_notes": { "type": ["string", "null"] },
          "round_number": { "type": "integer", "minimum": 1 }
        },
        "required": ["speaker", "content", "timestamp", "round_number"]
      }
    }
  },
  "required": ["session", "synth_snapshot", "messages"]
}
```

### Filename Convention

```
data/transcripts/{synth_id}_{YYYYMMDD}_{HHMMSS}.json
```

Example: `fhynws_20251216_143052.json`
