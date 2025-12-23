# Implementation Plan: Chat com Synth Entrevistado

**Branch**: `015-synth-chat` | **Date**: 2025-12-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/015-synth-chat/spec.md`

## Summary

Implementar funcionalidade de chat direto com synths após visualização de entrevista. O usuário poderá conversar com o synth que mantém memória da entrevista e responde consistente com sua persona. Interface estilo ChatGPT com histórico de sessão.

## Technical Context

**Language/Version**: Python 3.13+ (backend), TypeScript 5.5+ (frontend)
**Primary Dependencies**: FastAPI, OpenAI SDK, React 18, TanStack Query, shadcn/ui
**Storage**: SQLite (leitura apenas - sem persistência de chat)
**Testing**: pytest (backend), vitest (frontend)
**Target Platform**: Web application (desktop/mobile browsers)
**Project Type**: Web (frontend + backend)
**Performance Goals**: Resposta do synth < 10 segundos
**Constraints**: Histórico de chat apenas em memória (sessão do navegador)
**Scale/Scope**: Single user sessions, ~50 mensagens por conversa

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First Development (TDD/BDD) | ✅ PASS | Tests serão escritos antes da implementação |
| II. Fast Test Battery | ✅ PASS | Unit tests < 5s total |
| III. Complete Test Battery | ✅ PASS | Todos os testes passarão antes do PR |
| IV. Frequent Commits | ✅ PASS | Commits atômicos a cada fase |
| V. Simplicity | ✅ PASS | Solução minimalista sem persistência |
| VI. Language | ✅ PASS | Código em inglês, docs em português |
| VII. Architecture | ✅ PASS | Segue estrutura existente do projeto |
| IX. Other Principles | ✅ PASS | Reutiliza LLMClient com tracing Phoenix |

## Project Structure

### Documentation (this feature)

```text
specs/015-synth-chat/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 - Research decisions
├── data-model.md        # Phase 1 - Data model
├── quickstart.md        # Phase 1 - Usage guide
├── contracts/           # Phase 1 - API contracts
│   └── chat-api.yaml    # OpenAPI specification
└── tasks.md             # Phase 2 - Implementation tasks (created by /speckit.tasks)
```

### Source Code (repository root)

```text
# Backend
src/synth_lab/
├── api/
│   └── routers/
│       └── chat.py           # NEW - Chat endpoint
├── models/
│   └── chat.py               # NEW - Pydantic models
└── services/
    └── chat/
        ├── __init__.py       # NEW
        └── service.py        # NEW - Chat logic

# Frontend
frontend/src/
├── components/
│   ├── chat/
│   │   ├── SynthChatDialog.tsx   # NEW - Main chat dialog
│   │   ├── ChatMessage.tsx       # NEW - Message component
│   │   └── ChatInput.tsx         # NEW - Input component
│   └── shared/
│       └── TranscriptDialog.tsx  # MODIFY - Add chat button
├── hooks/
│   └── use-synth-chat.ts         # NEW - Chat state hook
├── services/
│   └── chat-api.ts               # NEW - API client
└── types/
    └── chat.ts                   # NEW - TypeScript types

# Tests
tests/
├── unit/
│   └── synth_lab/
│       └── services/
│           └── chat/
│               └── test_service.py  # NEW
└── integration/
    └── test_chat_api.py             # NEW

frontend/src/__tests__/
└── components/
    └── chat/
        └── SynthChatDialog.test.tsx  # NEW
```

**Structure Decision**: Web application structure (Option 2) - extends existing backend/ and frontend/ separation.

## Complexity Tracking

> No violations identified. Feature follows existing patterns.

## Phase Outputs

### Phase 0: Research
- ✅ [research.md](./research.md) - Decisões técnicas documentadas

### Phase 1: Design
- ✅ [data-model.md](./data-model.md) - Modelo de dados
- ✅ [contracts/chat-api.yaml](./contracts/chat-api.yaml) - OpenAPI spec
- ✅ [quickstart.md](./quickstart.md) - Guia de uso

### Phase 2: Tasks
- ⏳ Será gerado pelo comando `/speckit.tasks`

## Key Design Decisions

1. **REST síncrono** para chat (não SSE) - simplicidade para interação 1:1
2. **Stateless backend** - contexto enviado em cada requisição
3. **Histórico em memória** - sem persistência de chat no banco
4. **Reutilização de LLMClient** - infraestrutura existente com retry e tracing
5. **Dialog sobre dialog** - SynthChatDialog abre sobre TranscriptDialog

## Dependencies

### Existing (no changes needed)
- OpenAI SDK via LLMClient
- React Query para data fetching
- shadcn/ui para componentes de UI
- Tailwind CSS para estilos

### New Files Required
- Backend: 3 novos arquivos (router, models, service)
- Frontend: 6 novos arquivos (components, hook, api, types)
- Tests: 3 novos arquivos

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Resposta lenta do LLM | Medium | Timeout de 30s, loading indicator |
| Contexto muito grande | Low | Limite de 50 mensagens no histórico |
| Persona inconsistente | Medium | Reutilizar format_synth_profile() existente |

## Next Steps

Execute `/speckit.tasks` para gerar as tarefas de implementação detalhadas.
