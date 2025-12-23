# Data Model: Chat com Synth Entrevistado

**Feature**: 015-synth-chat
**Date**: 2025-12-23

## Overview

O modelo de dados para o chat é minimalista, focado em estado de sessão do frontend.
Não há persistência de chat no banco de dados conforme definido na spec.

## Entities

### ChatMessage

Representa uma mensagem individual na conversa de chat.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| role | string | Remetente da mensagem | enum: "user", "synth" |
| content | string | Texto da mensagem | required, non-empty |
| timestamp | datetime | Momento do envio | ISO 8601 format |

**Validation Rules**:
- `role` deve ser "user" ou "synth"
- `content` não pode ser vazio
- `timestamp` é gerado automaticamente

### ChatRequest

Representa uma requisição de chat enviada ao backend.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| exec_id | string | ID da execução/entrevista de origem | required, format: batch_xxx |
| message | string | Mensagem do usuário | required, non-empty, max 2000 chars |
| chat_history | ChatMessage[] | Histórico de mensagens anteriores | optional, max 50 messages |

**Validation Rules**:
- `exec_id` deve corresponder a uma execução existente
- `message` não pode exceder 2000 caracteres
- `chat_history` limitado a 50 mensagens para controle de contexto

### ChatResponse

Representa a resposta do synth ao chat.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| message | string | Resposta do synth | required |
| timestamp | datetime | Momento da geração | ISO 8601 format |

### ChatSession (Frontend Only)

Estado da sessão de chat mantido no frontend.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| synth_id | string | ID do synth | required |
| exec_id | string | ID da execução de origem | required |
| synth_name | string | Nome do synth | required |
| synth_age | number | Idade do synth | optional |
| messages | ChatMessage[] | Histórico de mensagens | initially empty |
| is_loading | boolean | Indica se está aguardando resposta | default: false |

**State Transitions**:
```
IDLE -> LOADING (user sends message)
LOADING -> IDLE (response received)
LOADING -> ERROR (request failed)
ERROR -> IDLE (user retries or dismisses)
```

## Relationships

```
┌─────────────────┐     references     ┌─────────────────┐
│   ChatSession   │ ─────────────────► │   Execution     │
│   (frontend)    │                    │   (existing)    │
└─────────────────┘                    └─────────────────┘
         │                                      │
         │ contains                             │ has
         ▼                                      ▼
┌─────────────────┐                    ┌─────────────────┐
│  ChatMessage[]  │                    │   Transcript    │
│   (in memory)   │                    │   (existing)    │
└─────────────────┘                    └─────────────────┘
```

## Context Composition

O contexto enviado ao LLM é composto de três partes:

1. **Synth Profile** (existente no sistema)
   - Dados demográficos, psicográficos, comportamentais
   - Formatado via `format_synth_profile()`

2. **Interview Transcript** (carregado do backend)
   - Mensagens da entrevista original
   - Serve como "memória" do synth

3. **Chat History** (estado do frontend)
   - Mensagens trocadas no chat atual
   - Enviado em cada requisição

```
┌───────────────────────────────────────────────────────────────┐
│                    LLM Context                                │
├───────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐                                          │
│  │  Synth Profile  │  ← Persona completa do synth             │
│  └─────────────────┘                                          │
│  ┌─────────────────┐                                          │
│  │   Interview     │  ← Memória da entrevista                 │
│  │   Transcript    │                                          │
│  └─────────────────┘                                          │
│  ┌─────────────────┐                                          │
│  │  Chat History   │  ← Conversa atual com usuário            │
│  └─────────────────┘                                          │
│  ┌─────────────────┐                                          │
│  │  User Message   │  ← Mensagem mais recente                 │
│  └─────────────────┘                                          │
└───────────────────────────────────────────────────────────────┘
```

## No Database Changes

Esta feature não requer alterações no schema do banco de dados:
- Chat history é mantido apenas em memória (frontend state)
- Executions e Transcripts já existem e são apenas lidos
- Synth data já existe e é apenas lido

## Pydantic Models (Backend)

```python
# src/synth_lab/models/chat.py

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal

class ChatMessageModel(BaseModel):
    role: Literal["user", "synth"]
    content: str = Field(..., min_length=1)
    timestamp: datetime

class ChatRequest(BaseModel):
    exec_id: str = Field(..., pattern=r"^batch_")
    message: str = Field(..., min_length=1, max_length=2000)
    chat_history: list[ChatMessageModel] = Field(default_factory=list, max_length=50)

class ChatResponse(BaseModel):
    message: str
    timestamp: datetime
```

## TypeScript Types (Frontend)

```typescript
// frontend/src/types/chat.ts

export interface ChatMessage {
  role: 'user' | 'synth';
  content: string;
  timestamp: string; // ISO 8601
}

export interface ChatRequest {
  exec_id: string;
  message: string;
  chat_history: ChatMessage[];
}

export interface ChatResponse {
  message: string;
  timestamp: string;
}

export interface ChatSession {
  synthId: string;
  execId: string;
  synthName: string;
  synthAge?: number;
  messages: ChatMessage[];
  isLoading: boolean;
  error?: string;
}
```
