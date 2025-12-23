# Tasks: Chat com Synth Entrevistado

**Input**: Design documents from `/specs/015-synth-chat/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/chat-api.yaml

**Tests**: Included per Constitution requirement (TDD/BDD mandatory)

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `src/synth_lab/`
- **Frontend**: `frontend/src/`
- **Tests**: `tests/` (backend), `frontend/src/__tests__/` (frontend)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create base files and types needed by all stories

- [x] T001 [P] Create chat types in frontend/src/types/chat.ts
- [x] T002 [P] Create chat Pydantic models in src/synth_lab/models/chat.py
- [x] T003 [P] Create chat service directory structure src/synth_lab/services/chat/__init__.py
- [x] T004 [P] Create chat API client in frontend/src/services/chat-api.ts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend service and endpoint that ALL user stories depend on

**WARNING**: No user story work can begin until this phase is complete

- [x] T005 Write unit test for chat service in tests/unit/synth_lab/services/chat/test_service.py
- [x] T006 Implement ChatService in src/synth_lab/services/chat/service.py
- [x] T007 Write integration test for chat API in tests/integration/test_chat_api.py
- [x] T008 Implement chat router in src/synth_lab/api/routers/chat.py
- [x] T009 Register chat router in src/synth_lab/api/main.py

**Checkpoint**: Backend chat endpoint functional - frontend work can begin

---

## Phase 3: User Story 1 - Iniciar Chat com Synth (Priority: P1)

**Goal**: Botão "Conversar com {nome}" aparece ao final do popup de transcrição e abre tela de chat

**Independent Test**: Abrir popup de entrevista concluída, rolar até o final, verificar botão e clicar para abrir chat

**Acceptance Criteria**:
- FR-001: Botão aparece ao final do popup de transcrição
- FR-002: Clique abre tela de chat
- FR-003: Título "Conversando com {nome}, {idade} anos"
- FR-012: Botão não aparece em entrevistas não concluídas

### Implementation for User Story 1

- [x] T010 [P] [US1] Create SynthChatDialog component shell in frontend/src/components/chat/SynthChatDialog.tsx
- [x] T011 [US1] Modify TranscriptDialog to add "Conversar com {nome}" button at bottom in frontend/src/components/shared/TranscriptDialog.tsx
- [x] T012 [US1] Implement chat dialog header with title "Conversando com {nome}, {idade} anos" in SynthChatDialog.tsx
- [x] T013 [US1] Add state management for opening/closing chat dialog in TranscriptDialog.tsx
- [x] T014 [US1] Implement condition to hide button when interview not completed in TranscriptDialog.tsx

**Checkpoint**: User Story 1 complete - button visible and chat dialog opens with correct title

---

## Phase 4: User Story 2 - Enviar e Receber Mensagens (Priority: P1)

**Goal**: Usuário pode enviar mensagens e receber respostas do synth no chat

**Independent Test**: Abrir chat, enviar mensagem, verificar resposta aparece no histórico

**Acceptance Criteria**:
- FR-004: Campo de texto com botão enviar e atalho Enter
- FR-005: Respostas do synth aparecem no histórico
- FR-006: Indicador de loading enquanto processa

### Implementation for User Story 2

- [x] T015 [P] [US2] Create ChatInput component in frontend/src/components/chat/ChatInput.tsx
- [x] T016 [P] [US2] Create ChatMessage component in frontend/src/components/chat/ChatMessage.tsx
- [x] T017 [US2] Create useSynthChat hook in frontend/src/hooks/use-synth-chat.ts
- [x] T018 [US2] Integrate ChatInput into SynthChatDialog.tsx with Enter key support
- [x] T019 [US2] Implement message list rendering with ChatMessage in SynthChatDialog.tsx
- [x] T020 [US2] Add loading indicator (typing animation) in SynthChatDialog.tsx
- [x] T021 [US2] Connect useSynthChat hook to chat-api.ts for sending messages

**Checkpoint**: User Story 2 complete - can send messages and receive synth responses

---

## Phase 5: User Story 3 - Synth Mantém Contexto da Entrevista (Priority: P1)

**Goal**: Synth responde de forma contextualizada, lembrando da entrevista e mantendo persona

**Independent Test**: Perguntar sobre algo mencionado na entrevista, verificar resposta contextualizada

**Acceptance Criteria**:
- FR-007: Synth mantém contexto da entrevista original
- FR-008: Synth responde em primeira pessoa consistente com persona

### Implementation for User Story 3

- [x] T022 [US3] Create chat prompt instructions template in src/synth_lab/services/chat/instructions.py
- [x] T023 [US3] Implement interview transcript loading in ChatService.generate_response()
- [x] T024 [US3] Implement synth profile loading in ChatService.generate_response()
- [x] T025 [US3] Format context composition (profile + transcript + chat history) in ChatService
- [x] T026 [US3] Add test for context-aware response in tests/unit/synth_lab/services/chat/test_service.py

**Checkpoint**: User Story 3 complete - synth responses are contextual and persona-consistent

---

## Phase 6: User Story 4 - Histórico de Chat Separado (Priority: P1)

**Goal**: Histórico do chat é independente da entrevista, mantido apenas na sessão

**Independent Test**: Abrir chat, trocar mensagens, verificar entrevista não foi alterada

**Acceptance Criteria**:
- FR-009: Histórico do chat independente do histórico da entrevista
- FR-010: Sistema preserva histórico do chat durante a sessão

### Implementation for User Story 4

- [x] T027 [US4] Implement chat session state in useSynthChat hook (messages array)
- [x] T028 [US4] Ensure chat history is sent with each request in chat-api.ts
- [x] T029 [US4] Verify TranscriptDialog messages remain unchanged when chat is open
- [x] T030 [US4] Implement session persistence (state preserved when dialog reopens) in useSynthChat

**Checkpoint**: User Story 4 complete - chat history separate from interview, preserved in session

---

## Phase 7: User Story 5 - Fechar e Voltar do Chat (Priority: P1)

**Goal**: Usuário pode fechar chat e retornar ao popup da entrevista

**Independent Test**: Abrir chat, enviar mensagem, fechar, reabrir, verificar histórico preservado

**Acceptance Criteria**:
- FR-011: Sistema permite fechar o chat e retornar ao popup

### Implementation for User Story 5

- [x] T031 [US5] Implement close button (X) in SynthChatDialog header
- [x] T032 [US5] Implement onClose callback to return to TranscriptDialog
- [x] T033 [US5] Verify chat state is preserved when reopening (test via useSynthChat)

**Checkpoint**: User Story 5 complete - full navigation flow works

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Error handling, edge cases, and final validation

- [x] T034 [P] Implement error handling for API failures in useSynthChat hook
- [x] T035 [P] Add error state display in SynthChatDialog (retry button)
- [x] T036 [P] Handle empty persona data gracefully in ChatService
- [x] T037 [P] Add auto-scroll to latest message in SynthChatDialog
- [ ] T038 Run quickstart.md validation - test full flow manually
- [x] T039 Run all tests and verify they pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - US1 → US2 → US3 → US4 → US5 (sequential for single developer)
  - Or parallel if multiple developers (each story independently testable)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

| Story | Depends On | Can Start After |
|-------|------------|-----------------|
| US1 (Iniciar Chat) | Phase 2 | Phase 2 complete |
| US2 (Enviar/Receber) | US1 | US1 complete (needs dialog) |
| US3 (Contexto) | Phase 2 | Phase 2 complete (backend only) |
| US4 (Histórico Separado) | US2 | US2 complete (needs messages) |
| US5 (Fechar/Voltar) | US1 | US1 complete (needs dialog) |

### Within Each User Story

- Tests MUST be written and FAIL before implementation (TDD)
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

**Phase 1 (all parallel)**:
```
T001, T002, T003, T004 can all run in parallel
```

**Phase 2 (sequential for TDD)**:
```
T005 → T006 (test then implement service)
T007 → T008 (test then implement router)
T009 after T008
```

**User Story 2 (partial parallel)**:
```
T015 || T016 (both components in parallel)
T017 after components
T018-T021 sequential (integration)
```

---

## Parallel Example: Phase 1

```bash
# Launch all setup tasks together:
Task: "Create chat types in frontend/src/types/chat.ts"
Task: "Create chat Pydantic models in src/synth_lab/models/chat.py"
Task: "Create chat service directory structure src/synth_lab/services/chat/__init__.py"
Task: "Create chat API client in frontend/src/services/chat-api.ts"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (backend ready)
3. Complete Phase 3: User Story 1 (button + dialog opens)
4. Complete Phase 4: User Story 2 (send/receive messages)
5. **STOP and VALIDATE**: Test basic chat flow
6. Deploy/demo if ready

### Full Feature

1. Complete MVP (US1 + US2)
2. Add User Story 3 (context/persona) → Test
3. Add User Story 4 (separate history) → Test
4. Add User Story 5 (navigation) → Test
5. Complete Phase 8 (polish)
6. Full validation with quickstart.md

### Estimated Task Count

| Phase | Tasks | Parallel |
|-------|-------|----------|
| Setup | 4 | 4 |
| Foundational | 5 | 2 |
| US1 | 5 | 1 |
| US2 | 7 | 2 |
| US3 | 5 | 0 |
| US4 | 4 | 0 |
| US5 | 3 | 0 |
| Polish | 6 | 4 |
| **Total** | **39** | **13** |

---

## Notes

- All user stories are P1 priority (critical path)
- Backend tests use pytest, frontend tests optional (not explicitly requested)
- TDD: Write tests first, verify they fail, then implement
- Commit after each task or logical group
- Stop at any checkpoint to validate independently
