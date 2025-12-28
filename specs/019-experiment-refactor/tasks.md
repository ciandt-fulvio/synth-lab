# Tasks: Refatoração do Modelo Experimento-Análise-Entrevista

**Input**: Design documents from `/specs/019-experiment-refactor/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/

**Tests**: Não solicitados explicitamente. Tarefas focam na implementação.

**Organization**: Tasks são agrupadas por user story para permitir implementação e teste independente de cada história.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos diferentes, sem dependências)
- **[Story]**: A qual user story pertence (US1, US2, US3, US4, US5)
- Inclui caminhos exatos de arquivos nas descrições

## Path Conventions

- **Backend**: `src/synth_lab/`
- **Frontend**: `frontend/src/`

---

## Phase 1: Setup (Infraestrutura Compartilhada)

**Purpose**: Criar nova estrutura de banco de dados e entidades base

- [ ] T001 Criar novo schema SQL em src/synth_lab/infrastructure/database.py conforme data-model.md
- [ ] T002 [P] Criar entidade Experiment com scorecard embutido em src/synth_lab/domain/entities/experiment.py
- [ ] T003 [P] Criar entidade AnalysisRun em src/synth_lab/domain/entities/analysis_run.py
- [ ] T004 [P] Criar entidade SynthOutcome em src/synth_lab/domain/entities/synth_outcome.py

---

## Phase 2: Foundational (Pré-requisitos Bloqueantes)

**Purpose**: Repositórios e services base que DEVEM estar completos antes das user stories

**⚠️ CRITICAL**: Nenhuma user story pode começar até esta fase estar completa

- [ ] T005 Criar ExperimentRepository com CRUD e scorecard em src/synth_lab/repositories/experiment_repository.py
- [ ] T006 [P] Criar AnalysisRepository com operações 1:1 em src/synth_lab/repositories/analysis_repository.py
- [ ] T007 [P] Atualizar ResearchRepository para suportar experiment_id em src/synth_lab/repositories/research_repository.py
- [ ] T008 Criar ExperimentService base em src/synth_lab/services/experiment_service.py
- [ ] T009 [P] Criar AnalysisService base em src/synth_lab/services/analysis/analysis_service.py
- [ ] T010 [P] Criar schemas Pydantic para Experiment em src/synth_lab/api/schemas/experiments.py
- [ ] T011 [P] Criar schemas Pydantic para Analysis em src/synth_lab/api/schemas/analysis.py

**Checkpoint**: Fundação pronta - implementação de user stories pode começar

---

## Phase 3: User Story 1 - Criar Experimento com Scorecard (Priority: P1) 🎯 MVP

**Goal**: Usuário cria experimento com scorecard embutido, incluindo estimativa via IA

**Independent Test**: Criar experimento, estimar scorecard via IA, salvar e verificar que scorecard está embutido

### Backend - User Story 1

- [ ] T012 [US1] Implementar endpoint POST /experiments em src/synth_lab/api/routers/experiments.py
- [ ] T013 [US1] Implementar endpoint GET /experiments/list em src/synth_lab/api/routers/experiments.py
- [ ] T014 [US1] Implementar endpoint GET /experiments/{id} em src/synth_lab/api/routers/experiments.py
- [ ] T015 [US1] Implementar endpoint PUT /experiments/{id} em src/synth_lab/api/routers/experiments.py
- [ ] T016 [US1] Implementar endpoint PUT /experiments/{id}/scorecard em src/synth_lab/api/routers/experiments.py
- [ ] T017 [US1] Implementar ScorecardEstimator com LLM em src/synth_lab/services/experiment_service.py
- [ ] T018 [US1] Implementar endpoint POST /experiments/{id}/estimate-scorecard em src/synth_lab/api/routers/experiments.py
- [ ] T019 [US1] Adicionar Phoenix tracing às chamadas LLM do ScorecardEstimator

### Frontend - User Story 1

- [ ] T020 [P] [US1] Atualizar types Experiment com scorecard em frontend/src/types/experiment.ts
- [ ] T021 [P] [US1] Adicionar query keys para scorecard em frontend/src/lib/query-keys.ts
- [ ] T022 [US1] Atualizar experiments-api.ts com endpoints de scorecard em frontend/src/services/experiments-api.ts
- [ ] T023 [US1] Criar hooks useExperiments, useExperiment, useEstimateScorecard em frontend/src/hooks/use-experiments.ts
- [ ] T024 [US1] Criar componente ScorecardForm em frontend/src/components/experiments/ScorecardForm.tsx
- [ ] T025 [US1] Atualizar NewExperimentDialog com scorecard form em frontend/src/components/experiments/NewExperimentDialog.tsx
- [ ] T026 [US1] Atualizar ExperimentDetail para mostrar scorecard em frontend/src/pages/ExperimentDetail.tsx
- [ ] T027 [US1] Atualizar ExperimentCard com resumo do scorecard em frontend/src/components/experiments/ExperimentCard.tsx

**Checkpoint**: User Story 1 completa - experimentos podem ser criados com scorecard

---

## Phase 4: User Story 2 - Executar Análise Quantitativa Única (Priority: P2)

**Goal**: Usuário executa análise quantitativa única (1:1) para o experimento

**Independent Test**: Executar análise, verificar resultados, re-executar e confirmar substituição

### Backend - User Story 2

- [ ] T028 [US2] Implementar endpoint GET /experiments/{id}/analysis em src/synth_lab/api/routers/experiments.py
- [ ] T029 [US2] Implementar endpoint POST /experiments/{id}/analysis em src/synth_lab/api/routers/experiments.py
- [ ] T030 [US2] Implementar endpoint DELETE /experiments/{id}/analysis em src/synth_lab/api/routers/experiments.py
- [ ] T031 [US2] Implementar lógica de análise 1:1 no AnalysisService em src/synth_lab/services/analysis/analysis_service.py
- [ ] T032 [US2] Implementar endpoint GET /experiments/{id}/analysis/outcomes em src/synth_lab/api/routers/experiments.py
- [ ] T033 [US2] Adicionar validação de scorecard antes de executar análise

### Frontend - User Story 2

- [ ] T034 [P] [US2] Atualizar types para Analysis em frontend/src/types/experiment.ts
- [ ] T035 [US2] Criar analysis-api.ts com endpoints de análise em frontend/src/services/analysis-api.ts
- [ ] T036 [US2] Criar hooks useAnalysis, useRunAnalysis em frontend/src/hooks/use-analysis.ts
- [ ] T037 [US2] Criar componente AnalysisCard em frontend/src/components/experiments/AnalysisCard.tsx
- [ ] T038 [US2] Integrar AnalysisCard no ExperimentDetail em frontend/src/pages/ExperimentDetail.tsx
- [ ] T039 [US2] Renomear labels "Simulação" → "Análise Quantitativa" no ExperimentDetail

**Checkpoint**: User Story 2 completa - análise quantitativa funcional

---

## Phase 5: User Story 3 - Sugestões de Entrevista (Priority: P2)

**Goal**: Sistema sugere synths para entrevista baseado em regiões de alto risco

**Independent Test**: Completar análise, verificar sugestões, aceitar e criar entrevista

### Backend - User Story 3

- [ ] T040 [US3] Implementar endpoint GET /experiments/{id}/analysis/regions em src/synth_lab/api/routers/experiments.py
- [ ] T041 [US3] Implementar endpoint GET /experiments/{id}/analysis/interview-suggestions em src/synth_lab/api/routers/experiments.py
- [ ] T042 [US3] Implementar lógica de clustering e sugestões no AnalysisService

### Frontend - User Story 3

- [ ] T043 [P] [US3] Atualizar types para InterviewSuggestion em frontend/src/types/experiment.ts
- [ ] T044 [US3] Adicionar endpoints de sugestão em frontend/src/services/analysis-api.ts
- [ ] T045 [US3] Criar hook useInterviewSuggestions em frontend/src/hooks/use-analysis.ts
- [ ] T046 [US3] Criar componente InterviewSuggestions em frontend/src/components/experiments/InterviewSuggestions.tsx
- [ ] T047 [US3] Integrar InterviewSuggestions no ExperimentDetail após análise completa

**Checkpoint**: User Story 3 completa - sugestões de entrevista funcionais

---

## Phase 6: User Story 4 - Múltiplas Rodadas de Entrevistas (Priority: P2)

**Goal**: Usuário pode criar N rodadas de entrevistas por experimento

**Independent Test**: Criar 3 rodadas de entrevista e verificar que todas aparecem listadas

### Backend - User Story 4

- [ ] T048 [US4] Implementar endpoint GET /experiments/{id}/interviews em src/synth_lab/api/routers/experiments.py
- [ ] T049 [US4] Implementar endpoint POST /experiments/{id}/interviews em src/synth_lab/api/routers/experiments.py
- [ ] T050 [US4] Atualizar ExperimentDetailResponse para incluir lista de interviews

### Frontend - User Story 4

- [ ] T051 [P] [US4] Atualizar types para Interview em frontend/src/types/experiment.ts
- [ ] T052 [US4] Criar interviews-api.ts para endpoints de entrevista em frontend/src/services/interviews-api.ts
- [ ] T053 [US4] Criar hooks useExperimentInterviews, useCreateInterview em frontend/src/hooks/use-interviews.ts
- [ ] T054 [US4] Criar componente InterviewList em frontend/src/components/experiments/InterviewList.tsx
- [ ] T055 [US4] Atualizar NewInterviewDialog para aceitar synth_ids sugeridos em frontend/src/components/experiments/NewInterviewDialog.tsx
- [ ] T056 [US4] Integrar InterviewList no ExperimentDetail

**Checkpoint**: User Story 4 completa - múltiplas entrevistas por experimento

---

## Phase 7: User Story 5 - SSE Streaming de Entrevistas (Priority: P3)

**Goal**: Mensagens de entrevista aparecem em tempo real via SSE

**Independent Test**: Iniciar entrevista, verificar que mensagens aparecem sem refresh

### Backend - User Story 5

- [ ] T057 [US5] Verificar endpoint GET /research/{exec_id}/stream funciona corretamente em src/synth_lab/api/routers/research.py
- [ ] T058 [US5] Adicionar replay de mensagens históricas no stream SSE
- [ ] T059 [US5] Verificar eventos interview_completed, transcription_completed, execution_completed

### Frontend - User Story 5

- [ ] T060 [P] [US5] Verificar types SSE em frontend/src/types/sse-events.ts
- [ ] T061 [US5] Verificar hook use-sse.ts conecta corretamente ao backend em frontend/src/hooks/use-sse.ts
- [ ] T062 [US5] Verificar hook use-live-interviews.ts gerencia estado corretamente em frontend/src/hooks/use-live-interviews.ts
- [ ] T063 [US5] Verificar LiveInterviewGrid funciona com SSE em frontend/src/components/interviews/LiveInterviewGrid.tsx
- [ ] T064 [US5] Atualizar InterviewDetail para usar LiveInterviewGrid quando status=running em frontend/src/pages/InterviewDetail.tsx
- [ ] T065 [US5] Implementar reconexão automática em caso de perda de conexão SSE

**Checkpoint**: User Story 5 completa - streaming SSE funcional

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Melhorias que afetam múltiplas user stories

- [ ] T066 [P] Atualizar documentação em docs/ com novo modelo
- [ ] T067 Remover código legado de feature_scorecards e simulation_runs
- [ ] T068 [P] Adicionar logging adequado em todos os services
- [ ] T069 Validar quickstart.md com fluxo completo
- [ ] T070 [P] Atualizar CLAUDE.md com nova estrutura se necessário

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sem dependências - pode começar imediatamente
- **Foundational (Phase 2)**: Depende de Setup - BLOQUEIA todas user stories
- **User Stories (Phase 3-7)**: Todas dependem de Foundational
  - US1 (P1): Pode começar após Foundational
  - US2 (P2): Pode começar após Foundational (não depende de US1 para backend)
  - US3 (P2): Depende de US2 (precisa de análise para sugestões)
  - US4 (P2): Pode começar após Foundational
  - US5 (P3): Pode começar após Foundational (verificação de SSE existente)
- **Polish (Phase 8)**: Depende de todas user stories desejadas

### User Story Dependencies

```
Foundational
     │
     ├──► US1 (Experimento + Scorecard) ──► MVP
     │
     ├──► US2 (Análise Quantitativa) ──► US3 (Sugestões)
     │
     ├──► US4 (Múltiplas Entrevistas)
     │
     └──► US5 (SSE Streaming)
```

### Within Each User Story

- Backend antes de Frontend
- Repository antes de Service
- Service antes de Router
- Types antes de Hooks
- Hooks antes de Components

### Parallel Opportunities

**Setup (Phase 1)**:
```bash
# Entidades podem ser criadas em paralelo:
Task: T002 [P] Criar entidade Experiment
Task: T003 [P] Criar entidade AnalysisRun
Task: T004 [P] Criar entidade SynthOutcome
```

**Foundational (Phase 2)**:
```bash
# Repositories e schemas podem ser criados em paralelo:
Task: T006 [P] Criar AnalysisRepository
Task: T007 [P] Atualizar ResearchRepository
Task: T010 [P] Criar schemas Experiment
Task: T011 [P] Criar schemas Analysis
```

**User Stories em Paralelo** (com desenvolvedores diferentes):
```bash
# Developer A: US1 (MVP)
# Developer B: US2 + US3
# Developer C: US4 + US5
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: User Story 1
4. Testar criação de experimento com scorecard
5. Deploy/demo se pronto

### Incremental Delivery
1. Setup + Foundational → Fundação pronta
2. Add US1 → Teste → Deploy (MVP!)
3. Add US2 → Teste → Deploy (Análise)
4. Add US3 → Teste → Deploy (Sugestões)
5. Add US4 → Teste → Deploy (Múltiplas Entrevistas)
6. Add US5 → Teste → Deploy (SSE)

---

## Notes

- [P] tasks = arquivos diferentes, sem dependências
- [Story] label mapeia task para user story específica
- Cada user story deve ser independentemente completável e testável
- Commit após cada task ou grupo lógico
- Stop em qualquer checkpoint para validar story independentemente
- Evitar: tasks vagas, conflitos no mesmo arquivo, dependências cross-story que quebram independência
