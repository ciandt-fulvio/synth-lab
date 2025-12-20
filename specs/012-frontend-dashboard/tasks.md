# Tasks: Frontend Dashboard

**Input**: Design documents from `/specs/012-frontend-dashboard/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Não solicitados explicitamente na especificação. Tarefas de teste não incluídas.

**Organization**: Tasks são agrupadas por user story para permitir implementação e teste independente de cada história.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos diferentes, sem dependências)
- **[Story]**: Qual user story esta tarefa pertence (e.g., US1, US2, US3)
- Caminhos exatos incluídos nas descrições

## Path Conventions

- **Frontend**: `frontend/src/` para código fonte
- Paths relativos ao diretório `frontend/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inicialização do projeto e estrutura básica

- [ ] T001 [P] Install runtime dependencies (react-markdown, remark-gfm) via `pnpm add react-markdown remark-gfm` in frontend/
- [ ] T002 [P] Configure Vite proxy for API in frontend/vite.config.ts (target: http://localhost:8000, rewrite /api to /)
- [ ] T003 [P] Create directory structure: frontend/src/types/, frontend/src/services/, frontend/src/components/interviews/, frontend/src/components/synths/, frontend/src/components/shared/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infraestrutura core que DEVE estar completa antes de qualquer user story

**⚠️ CRITICAL**: Nenhum trabalho de user story pode começar até esta fase estar completa

### Types (from data-model.md)

- [ ] T004 [P] Create common types (PaginatedResponse, PaginationParams) in frontend/src/types/common.ts
- [ ] T005 [P] Create research types (ExecutionStatus, ResearchExecutionSummary, ResearchExecutionDetail, Message, TranscriptSummary, TranscriptDetail, ResearchExecuteRequest, ResearchExecuteResponse) in frontend/src/types/research.ts
- [ ] T006 [P] Create synth types (all interfaces from data-model.md including Demographics, Psychographics, Behavior, SynthSummary, SynthDetail) in frontend/src/types/synth.ts
- [ ] T007 [P] Create topic types (TopicSummary, TopicDetail) in frontend/src/types/topic.ts
- [ ] T008 [P] Create prfaq types (PRFAQSummary, PRFAQGenerateRequest, PRFAQGenerateResponse) in frontend/src/types/prfaq.ts
- [ ] T009 [P] Create SSE event types (InterviewMessageEvent, TranscriptionCompletedEvent, ExecutionCompletedEvent, SSEEvent) in frontend/src/types/events.ts
- [ ] T010 Create types barrel export in frontend/src/types/index.ts (re-export all types)

### API Services

- [ ] T011 Create base API configuration with fetch wrapper and error handling in frontend/src/services/api.ts
- [ ] T012 [P] Create synths API service (listSynths, getSynth, getSynthAvatar, searchSynths) in frontend/src/services/synths-api.ts
- [ ] T013 [P] Create research API service (listExecutions, getExecution, getTranscripts, getTranscript, getSummary, executeResearch) in frontend/src/services/research-api.ts
- [ ] T014 [P] Create topics API service (listTopics, getTopic) in frontend/src/services/topics-api.ts
- [ ] T015 [P] Create prfaq API service (getPrfaq, getPrfaqMarkdown, generatePrfaq) in frontend/src/services/prfaq-api.ts

### Library Utilities

- [ ] T016 [P] Create React Query keys configuration in frontend/src/lib/query-keys.ts
- [ ] T017 [P] Create Zod validation schemas (newInterviewSchema) in frontend/src/lib/schemas.ts

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Visualizar Lista de Entrevistas (Priority: P1) 🎯 MVP

**Goal**: Usuário visualiza lista de todas as pesquisas realizadas com cards informativos

**Independent Test**: Acessar aba "Interviews" e verificar se lista é carregada corretamente com dados da API

### Implementation for User Story 1

- [ ] T018 [US1] Create use-research hook with useResearchList, useResearchDetail queries in frontend/src/hooks/use-research.ts
- [ ] T019 [P] [US1] Create StatusBadge component for execution status display (pending/running/completed/failed) in frontend/src/components/shared/StatusBadge.tsx
- [ ] T020 [US1] Create InterviewCard component with topic, date, status badge, synth count in frontend/src/components/interviews/InterviewCard.tsx
- [ ] T021 [US1] Create InterviewList component with paginated grid of InterviewCards and empty state in frontend/src/components/interviews/InterviewList.tsx

**Checkpoint**: User Story 1 should be fully functional - lista de entrevistas visível

---

## Phase 4: User Story 2 - Visualizar Detalhes da Entrevista (Priority: P1)

**Goal**: Usuário clica em card e vê página de detalhes com informações completas

**Independent Test**: Clicar em card de entrevista e verificar se detalhes são exibidos corretamente

### Implementation for User Story 2

- [ ] T022 [US2] Update MarkdownPopup component to use react-markdown with remark-gfm in frontend/src/components/shared/MarkdownPopup.tsx
- [ ] T023 [US2] Create InterviewDetail page with execution info, synth list, summary button, prfaq button in frontend/src/pages/InterviewDetail.tsx
- [ ] T024 [US2] Add route /interviews/:execId to App.tsx in frontend/src/App.tsx
- [ ] T025 [US2] Add navigation from InterviewCard to InterviewDetail page in frontend/src/components/interviews/InterviewCard.tsx

**Checkpoint**: User Story 2 should be fully functional - detalhes de entrevista visíveis

---

## Phase 5: User Story 3 - Visualizar Lista de Synths (Priority: P1)

**Goal**: Usuário visualiza galeria de todos os synths disponíveis

**Independent Test**: Acessar aba "Synths" e verificar se grade de cards é exibida com avatares

### Implementation for User Story 3

- [ ] T026 [US3] Create use-synths hook with useSynthsList, useSynthDetail queries in frontend/src/hooks/use-synths.ts
- [ ] T027 [P] [US3] Create SynthCard component with avatar image, name, archetype, location in frontend/src/components/synths/SynthCard.tsx
- [ ] T028 [US3] Create SynthList component with responsive grid of SynthCards and pagination in frontend/src/components/synths/SynthList.tsx

**Checkpoint**: User Story 3 should be fully functional - lista de synths visível

---

## Phase 6: User Story 4 - Visualizar Detalhes do Synth (Priority: P2)

**Goal**: Usuário clica em synth e vê modal com todos os dados detalhados

**Independent Test**: Clicar em card de synth e verificar se popup mostra todas as informações

### Implementation for User Story 4

- [ ] T029 [P] [US4] Create BigFiveChart component with horizontal bars for personality traits using recharts in frontend/src/components/synths/BigFiveChart.tsx
- [ ] T030 [US4] Create SynthDetailDialog modal with avatar, demographics, psychographics (BigFiveChart), behavior, tech capabilities sections in frontend/src/components/synths/SynthDetailDialog.tsx
- [ ] T031 [US4] Integrate SynthDetailDialog with SynthList (open on card click) in frontend/src/components/synths/SynthList.tsx

**Checkpoint**: User Story 4 should be fully functional - detalhes do synth em modal

---

## Phase 7: User Story 5 - Disparar Nova Entrevista (Priority: P2)

**Goal**: Usuário cria nova pesquisa via formulário

**Independent Test**: Clicar em "Nova Entrevista", preencher formulário e verificar se execução é iniciada

### Implementation for User Story 5

- [ ] T032 [US5] Create use-topics hook with useTopicsList query in frontend/src/hooks/use-topics.ts
- [ ] T033 [US5] Create NewInterviewDialog component with form (topic select, synth selection/count, max_turns, model) using react-hook-form and zod in frontend/src/components/interviews/NewInterviewDialog.tsx
- [ ] T034 [US5] Add "Nova Entrevista" button to InterviewList that opens NewInterviewDialog in frontend/src/components/interviews/InterviewList.tsx
- [ ] T035 [US5] Implement form submission with mutation and redirect to InterviewDetail on success in frontend/src/components/interviews/NewInterviewDialog.tsx

**Checkpoint**: User Story 5 should be fully functional - nova entrevista pode ser criada

---

## Phase 8: User Story 6 - Acompanhar Entrevista em Tempo Real (Priority: P3)

**Goal**: Usuário vê mensagens chegando em tempo real via SSE

**Independent Test**: Iniciar entrevista e verificar se mensagens aparecem em tempo real

### Implementation for User Story 6

- [ ] T036 [US6] DEFER to next FEATUTE Create use-sse hook with EventSource connection, reconnection logic, and message state in frontend/src/hooks/use-sse.ts
- [ ] T037 [US6] DEFER to next FEATUTE Create InterviewMessages component with message list, auto-scroll, and status updates in frontend/src/components/interviews/InterviewMessages.tsx
- [ ] T038 [US6] DEFER to next FEATUTE Integrate InterviewMessages with InterviewDetail page (show when status is running) in frontend/src/pages/InterviewDetail.tsx

**Checkpoint**: User Story 6 should be fully functional - streaming em tempo real funcionando

---

## Phase 9: User Story 7 - Gerar PR/FAQ (Priority: P3)

**Goal**: Usuário gera PR/FAQ a partir do summary

**Independent Test**: Em entrevista completa, clicar em "Gerar PR/FAQ" e verificar se documento é gerado

### Implementation for User Story 7

- [ ] T039 [US7] Add generatePrfaq mutation to InterviewDetail with loading state in frontend/src/pages/InterviewDetail.tsx
- [ ] T040 [US7] Add "Gerar PR/FAQ" button that appears when summary_available=true and prfaq_available=false in frontend/src/pages/InterviewDetail.tsx
- [ ] T041 [US7] Add "Ver PR/FAQ" button with MarkdownPopup when prfaq_available=true in frontend/src/pages/InterviewDetail.tsx

**Checkpoint**: User Story 7 should be fully functional - PR/FAQ pode ser gerado

---

## Phase 10: Integration

**Purpose**: Integrar todos os componentes na página principal

- [ ] T042 Update Index.tsx with Interviews and Synths tabs using InterviewList and SynthList in frontend/src/pages/Index.tsx
- [ ] T043 Update App.tsx to include all routes (/interviews/:execId) in frontend/src/App.tsx
- [ ] T044 Add header with application title "Synth Lab" and description in frontend/src/pages/Index.tsx
- [ ] T045 Ensure SynthDetailDialog can be opened from InterviewDetail synth list in frontend/src/pages/InterviewDetail.tsx

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Melhorias que afetam múltiplas user stories

- [ ] T046 [P] Add error handling with user-friendly messages and retry buttons across all components
- [ ] T047 [P] Add loading skeletons/spinners for all async operations
- [ ] T048 [P] Add empty states for lists (no interviews, no synths)
- [ ] T049 [P] Ensure responsive design works on mobile and desktop
- [ ] T050 Run quickstart.md validation - verify all flows work end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-9)**: All depend on Foundational phase completion
  - User stories can proceed in priority order (P1 → P2 → P3)
  - Or in parallel if team capacity allows
- **Integration (Phase 10)**: Depends on US1, US3 minimum (core tabs)
- **Polish (Phase 11)**: Depends on Integration phase

### User Story Dependencies

| User Story | Priority | Dependencies | Notes |
|------------|----------|--------------|-------|
| US1 - Lista Entrevistas | P1 | Foundational | MVP core |
| US2 - Detalhes Entrevista | P1 | US1 (uses same hooks) | Extends US1 |
| US3 - Lista Synths | P1 | Foundational | MVP core |
| US4 - Detalhes Synth | P2 | US3 (uses same hooks) | Extends US3 |
| US5 - Nova Entrevista | P2 | US1, US2 | Redirects to detail |
| US6 - Real-time | P3 | US2 | Enhances detail page |
| US7 - Gerar PR/FAQ | P3 | US2 | Enhances detail page |

### Within Each User Story

- Hooks before components
- Shared components before feature components
- Core implementation before integration

### Parallel Opportunities

**Phase 1 (all parallel)**:
```
T001 + T002 + T003
```

**Phase 2 Types (all parallel)**:
```
T004 + T005 + T006 + T007 + T008 + T009
```

**Phase 2 Services (after T011)**:
```
T012 + T013 + T014 + T015
T016 + T017
```

**User Stories (after Foundational)**:
```
US1 + US3 can run in parallel (different domains)
US2 depends on US1
US4 depends on US3
US5 depends on US1, US2
US6, US7 depend on US2
```

---

## Parallel Example: Phase 2 Types

```bash
# Launch all type definitions together:
Task: "Create common types in frontend/src/types/common.ts"
Task: "Create research types in frontend/src/types/research.ts"
Task: "Create synth types in frontend/src/types/synth.ts"
Task: "Create topic types in frontend/src/types/topic.ts"
Task: "Create prfaq types in frontend/src/types/prfaq.ts"
Task: "Create SSE event types in frontend/src/types/events.ts"
```

---

## Implementation Strategy

### MVP First (US1 + US3)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Lista Entrevistas)
4. Complete Phase 5: User Story 3 (Lista Synths)
5. Complete Phase 10: Integration (tabs funcionando)
6. **STOP and VALIDATE**: Test MVP independently
7. Deploy/demo if ready

### Incremental Delivery

1. **MVP**: Setup + Foundational + US1 + US3 + Integration → Tabs com listas
2. **+Details**: US2 + US4 → Detalhes de entrevistas e synths
3. **+Creation**: US5 → Criar novas entrevistas
4. **+Real-time**: US6 → Streaming SSE
5. **+PR/FAQ**: US7 → Geração de documentos
6. **+Polish**: Phase 11 → Error handling, loading states

---

## Summary

| Phase | Tasks | Focus |
|-------|-------|-------|
| Setup | 3 | Dependencies, config, directories |
| Foundational | 14 | Types, services, hooks base |
| US1 | 4 | Lista de entrevistas |
| US2 | 4 | Detalhes da entrevista |
| US3 | 3 | Lista de synths |
| US4 | 3 | Detalhes do synth |
| US5 | 4 | Nova entrevista |
| US6 | 3 | Real-time SSE |
| US7 | 3 | Gerar PR/FAQ |
| Integration | 4 | Página principal |
| Polish | 5 | Cross-cutting concerns |
| **Total** | **50** | |

---

## Notes

- [P] tasks = arquivos diferentes, sem dependências
- [Story] label mapeia tarefa para user story específica
- Cada user story deve ser independentemente completável e testável
- Commit após cada tarefa ou grupo lógico
- Pare em qualquer checkpoint para validar story independentemente
