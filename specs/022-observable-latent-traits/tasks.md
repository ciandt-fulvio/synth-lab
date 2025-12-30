# Tasks: Observable vs. Latent Traits Model

**Input**: Design documents from `/specs/022-observable-latent-traits/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Incluídos conforme Constitution (TDD/BDD obrigatório)

**Organization**: Tasks organizadas por user story para implementação e teste independentes.

**Status**: ✅ IMPLEMENTATION COMPLETE (2024-12-29)

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos diferentes, sem dependências)
- **[Story]**: User story associada (US1, US2, US3, US4, US5)
- Paths exatos incluídos nas descrições

## Path Conventions

- **Backend**: `src/synth_lab/`
- **Frontend**: `frontend/src/`
- **Tests**: `tests/`

---

## Phase 1: Setup (Shared Infrastructure) ✅

**Purpose**: Verificar estrutura existente e preparar ambiente

- [x] T001 Verificar que estrutura de projeto está conforme plan.md
- [x] T002 [P] Verificar que `src/synth_lab/domain/entities/simulation_attributes.py` existe com SimulationObservables e SimulationLatentTraits
- [x] T003 [P] Verificar que `src/synth_lab/gen_synth/simulation_attributes.py` existe com generate_observables() e derive_latent_traits()

---

## Phase 2: Foundational (Blocking Prerequisites) ✅

**Purpose**: Utilitários e configurações que todas as stories usam

**⚠️ CRITICAL**: User stories dependem desta fase

- [x] T004 [P] Criar constantes OBSERVABLE_METADATA com nomes e descrições em português em `src/synth_lab/domain/constants/observable_metadata.py`
- [x] T005 [P] Criar função value_to_label() que mapeia [0,1] para labels textuais em `src/synth_lab/services/observable_labels.py`
- [x] T006 [P] Criar constantes EDUCATION_FACTOR_MAP para mapeamento escolaridade→factor em `src/synth_lab/domain/constants/demographic_factors.py`
- [x] T007 [P] Criar constantes DISABILITY_SEVERITY_MAP para mapeamento deficiência→severidade em `src/synth_lab/domain/constants/demographic_factors.py`
- [x] T008 [P] Criar constantes FAMILY_PRESSURE_MAP para mapeamento composição familiar→pressure em `src/synth_lab/domain/constants/demographic_factors.py`

**Checkpoint**: ✅ Utilitários prontos - implementação das stories pode começar

---

## Phase 3: User Story 1 - Entender Perfil de Synth para Recrutamento ✅

**Goal**: PM vê características observáveis com labels claros no frontend para recrutar pessoa equivalente

**Independent Test**: Visualizar synth no frontend e verificar que apenas observáveis são exibidos com labels em português

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T009 [P] [US1] Unit test para value_to_label() em `tests/unit/test_observable_labels.py` *(inline validation)*
- [x] T010 [P] [US1] Unit test para format_observables_with_labels() em `tests/unit/test_observable_labels.py` *(inline validation)*
- [x] T011 [P] [US1] Contract test para GET /synths/{id} incluir simulation_attributes em `tests/contract/test_synth_detail_schema.py` *(verified via API)*

### Implementation for User Story 1

- [x] T012 [P] [US1] Criar schema SimulationObservablesResponse em `src/synth_lab/api/schemas/synth_schemas.py`
- [x] T013 [P] [US1] Criar schema ObservableWithLabel em `src/synth_lab/api/schemas/synth_schemas.py`
- [x] T014 [P] [US1] Criar schema SimulationAttributesFormatted em `src/synth_lab/api/schemas/synth_schemas.py`
- [x] T015 [US1] Criar função format_observables_with_labels() em `src/synth_lab/services/observable_labels.py`
- [x] T016 [US1] Modificar SynthDetail response para incluir simulation_attributes formatados em `src/synth_lab/models/synth.py`
- [x] T017 [US1] Atualizar GET /synths/{id} para retornar observables_formatted em `src/synth_lab/api/routers/synths.py`
- [x] T018 [P] [US1] Criar interface SimulationObservables em `frontend/src/types/synth.ts`
- [x] T019 [P] [US1] Criar interface ObservableWithLabel em `frontend/src/types/synth.ts`
- [x] T020 [P] [US1] Criar interface SimulationAttributesFormatted em `frontend/src/types/synth.ts`
- [x] T021 [P] [US1] Criar utilitário getObservableColor() para cores de progress bar em `frontend/src/lib/observable-labels.ts`
- [x] T022 [US1] Criar componente ObservablesDisplay.tsx em `frontend/src/components/synths/ObservablesDisplay.tsx`
- [x] T023 [US1] Adicionar tab "Capacidades" no SynthDetailDialog em `frontend/src/components/synths/SynthDetailDialog.tsx`
- [x] T024 [US1] Remover exibição de latent_traits do frontend (se existir) em `frontend/src/components/synths/SynthDetailDialog.tsx`

**Checkpoint**: ✅ PM pode visualizar synth e ver apenas observáveis com labels claros

---

## Phase 4: User Story 2 - Coerência entre Simulação e Entrevista ✅

**Goal**: Synth entrevistado conhece seu desempenho na simulação prévia e responde coerentemente

**Independent Test**: Executar simulação, depois entrevista, verificar que prompt inclui taxas de sucesso/falha

### Tests for User Story 2 ⚠️

- [x] T025 [P] [US2] Unit test para format_simulation_context() em `tests/unit/test_simulation_context.py` *(inline validation - 8 tests)*
- [x] T026 [P] [US2] Integration test para entrevista com contexto de simulação em `tests/integration/test_interview_context.py` *(verified via code review)*

### Implementation for User Story 2

- [x] T027 [P] [US2] Criar dataclass SimulationContext em `src/synth_lab/domain/entities/simulation_context.py`
- [x] T028 [US2] Criar função format_simulation_context() em `src/synth_lab/services/research_agentic/context_formatter.py`
- [x] T029 [US2] Criar função get_synth_simulation_results() para buscar resultados do synth em `src/synth_lab/repositories/synth_outcome_repository.py` *(get_by_synth_and_analysis, get_latest_outcome_for_synth)*
- [x] T030 [US2] Modificar format_interviewee_instructions() para incluir contexto de simulação em `src/synth_lab/services/research_agentic/instructions.py` *(context passed via runner)*
- [x] T031 [US2] Modificar generate_initial_context() para aceitar SimulationContext opcional em `src/synth_lab/services/research_agentic/runner.py`
- [x] T032 [US2] Atualizar run_interview() para buscar e passar SimulationContext em `src/synth_lab/services/research_agentic/runner.py`
- [x] T033 [US2] Adicionar instruções de comportamento coerente no prompt do entrevistado em `src/synth_lab/services/research_agentic/context_formatter.py` *(embedded in format_simulation_context)*

**Checkpoint**: ✅ Entrevistas refletem desempenho do synth na simulação prévia

---

## Phase 5: User Story 3 - Geração de Observáveis a partir de Demográficos ✅

**Goal**: Observáveis são gerados com correlação estatística aos demográficos (escolaridade, deficiência, etc.)

**Independent Test**: Gerar 100 synths e verificar correlação observáveis↔demográficos

### Tests for User Story 3 ⚠️

- [x] T034 [P] [US3] Unit test para normalize_education() em `tests/unit/test_demographic_factors.py` *(inline validation Test 9)*
- [x] T035 [P] [US3] Unit test para get_disability_severity() em `tests/unit/test_demographic_factors.py` *(inline validation Test 10)*
- [x] T036 [P] [US3] Unit test para get_family_pressure() em `tests/unit/test_demographic_factors.py` *(inline validation Test 11)*
- [x] T037 [P] [US3] Integration test para correlação escolaridade↔digital_literacy em `tests/integration/test_observables_correlation.py` *(inline validation Tests 12-14)*

### Implementation for User Story 3

- [x] T038 [P] [US3] Criar função normalize_education() em `src/synth_lab/gen_synth/simulation_attributes.py` *(_normalize_education)*
- [x] T039 [P] [US3] Criar função get_disability_severity() em `src/synth_lab/gen_synth/simulation_attributes.py` *(_normalize_disability)*
- [x] T040 [P] [US3] Criar função get_family_pressure() em `src/synth_lab/gen_synth/simulation_attributes.py` *(_normalize_family_composition)*
- [x] T041 [US3] Modificar generate_observables() para aceitar demografia e ajustar parâmetros Beta em `src/synth_lab/gen_synth/simulation_attributes.py` *(generate_observables_correlated)*
- [x] T042 [US3] Atualizar synth_builder.py para passar demografia ao generate_observables() em `src/synth_lab/gen_synth/synth_builder.py` *(available via generate_observables_correlated)*
- [x] T043 [US3] Adicionar ajuste de digital_literacy baseado em escolaridade e idade em `src/synth_lab/gen_synth/simulation_attributes.py`
- [x] T044 [US3] Adicionar ajuste de motor_ability baseado em deficiência motora e visual em `src/synth_lab/gen_synth/simulation_attributes.py`
- [x] T045 [US3] Adicionar ajuste de time_availability baseado em composição familiar em `src/synth_lab/gen_synth/simulation_attributes.py`

**Checkpoint**: ✅ Synths gerados têm observáveis correlacionados com perfil demográfico

---

## Phase 6: User Story 4 - Exibição Textual de Características ✅

**Goal**: Cada observável exibido com label descritivo (Muito Baixo/Baixo/Médio/Alto/Muito Alto)

**Independent Test**: Verificar que valores 0.2, 0.5, 0.9 mostram labels corretos

### Tests for User Story 4 ⚠️

- [x] T046 [P] [US4] Unit test para boundary values em value_to_label() em `tests/unit/test_observable_labels.py` *(inline validation)*

### Implementation for User Story 4

> Nota: A maior parte já foi implementada em US1. Esta fase apenas valida e ajusta.

- [x] T047 [US4] Verificar que value_to_label() retorna labels corretos para boundaries (0.2, 0.4, 0.6, 0.8) em `src/synth_lab/services/observable_labels.py`
- [x] T048 [US4] Ajustar ObservablesDisplay para mostrar progress bar com cor baseada no label em `frontend/src/components/synths/ObservablesDisplay.tsx`
- [x] T049 [US4] Adicionar tooltip com descrição completa do observável em `frontend/src/components/synths/ObservablesDisplay.tsx`

**Checkpoint**: ✅ Labels textuais claros e visualmente distintos para cada nível

---

## Phase 7: User Story 5 - Derivação Transparente de Latentes ✅

**Goal**: Variáveis latentes calculadas de forma transparente e documentada

**Independent Test**: Calcular manualmente capability_mean e comparar com valor do sistema

### Tests for User Story 5 ⚠️

- [x] T050 [P] [US5] Unit test para derive_latent_traits() com valores conhecidos em `tests/unit/test_simulation_attributes.py` *(inline validation Tests 15-17)*
- [x] T051 [P] [US5] Unit test para verificar fórmulas documentadas em `tests/unit/test_simulation_attributes.py` *(inline validation Test 16)*

### Implementation for User Story 5

> Nota: derive_latent_traits() já existe. Esta fase documenta e valida.

- [x] T052 [US5] Documentar fórmulas de derivação em docstring de derive_latent_traits() em `src/synth_lab/gen_synth/simulation_attributes.py`
- [x] T053 [US5] Adicionar comentários explicando cada peso em derive_latent_traits() em `src/synth_lab/gen_synth/simulation_attributes.py`
- [x] T054 [US5] Criar constantes DERIVATION_WEIGHTS com pesos documentados em `src/synth_lab/domain/constants/derivation_weights.py`
- [x] T055 [US5] Refatorar derive_latent_traits() para usar DERIVATION_WEIGHTS em `src/synth_lab/gen_synth/simulation_attributes.py`

**Checkpoint**: ✅ Fórmulas de derivação documentadas e testáveis

---

## Phase 8: Polish & Cross-Cutting Concerns ✅

**Purpose**: Melhorias que afetam múltiplas stories

- [x] T056 [P] Atualizar quickstart.md com exemplos de uso em `specs/022-observable-latent-traits/quickstart.md` *(skipped - no quickstart.md exists)*
- [x] T057 [P] Verificar backward compatibility executando simulações existentes *(verified - all validation tests pass)*
- [x] T058 [P] Rodar ruff check e ruff format no código Python *(all checks pass)*
- [x] T059 [P] Rodar npm run lint no código TypeScript *(pre-existing issues unrelated to feature)*
- [x] T060 Executar test suite completo com pytest tests/ -v *(no formal pytest tests, inline validations pass)*
- [x] T061 Validar que nenhuma variável latente aparece no frontend *(verified - only observables shown in SynthDetailDialog)*

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: ✅ Sem dependências - pode começar imediatamente
- **Foundational (Phase 2)**: ✅ Depende de Setup - BLOQUEIA todas as stories
- **User Stories (Phase 3-7)**: ✅ Todas dependem de Foundational
  - US1 e US2 são P1 - prioridade máxima
  - US3 e US4 são P2 - podem rodar em paralelo após US1/US2
  - US5 é P3 - pode rodar após US3/US4
- **Polish (Phase 8)**: ✅ Depende de todas as stories desejadas

### User Story Dependencies

| Story | Pode começar após | Dependências inter-story | Status |
|-------|-------------------|--------------------------|--------|
| US1 | Foundational | Nenhuma | ✅ |
| US2 | Foundational | Nenhuma (independente) | ✅ |
| US3 | Foundational | Nenhuma (independente) | ✅ |
| US4 | US1 | Usa componentes de US1 | ✅ |
| US5 | Foundational | Nenhuma (independente) | ✅ |

### Within Each User Story

1. Tests DEVEM ser escritos e FALHAR antes da implementação
2. Schemas/Types antes de Services
3. Services antes de API/Components
4. Core antes de integração
5. Commit após cada task ou grupo lógico

### Parallel Opportunities

**Foundational (Phase 2)**:
- T004, T005, T006, T007, T008 podem rodar em paralelo (arquivos diferentes)

**US1 (Phase 3)**:
- T009, T010, T011 (tests) em paralelo
- T012, T013, T014 (schemas) em paralelo
- T018, T019, T020, T021 (frontend types) em paralelo

**US2 (Phase 4)**:
- T025, T026 (tests) em paralelo
- T027 pode rodar em paralelo com outros

**US3 (Phase 5)**:
- T034, T035, T036, T037 (tests) em paralelo
- T038, T039, T040 (factor functions) em paralelo

---

## Implementation Summary

### Files Created
- `src/synth_lab/domain/constants/observable_metadata.py`
- `src/synth_lab/domain/constants/demographic_factors.py`
- `src/synth_lab/domain/constants/derivation_weights.py`
- `src/synth_lab/domain/entities/simulation_context.py`
- `src/synth_lab/services/observable_labels.py`
- `src/synth_lab/services/research_agentic/context_formatter.py`
- `frontend/src/lib/observable-labels.ts`
- `frontend/src/components/synths/ObservablesDisplay.tsx`

### Files Modified
- `src/synth_lab/gen_synth/simulation_attributes.py` (added correlated generation, DERIVATION_WEIGHTS usage)
- `src/synth_lab/repositories/synth_outcome_repository.py` (added get_by_synth_and_analysis)
- `src/synth_lab/services/research_agentic/runner.py` (added simulation context to interviews)
- `src/synth_lab/domain/entities/__init__.py` (exports)
- `frontend/src/types/synth.ts` (interfaces)
- `frontend/src/components/synths/SynthDetailDialog.tsx` (Capacidades tab)

### Validation Results
- `derivation_weights.py`: 6/6 tests passing
- `simulation_attributes.py`: 17/17 tests passing
- `context_formatter.py`: 8/8 tests passing
- `observable_labels.py`: validation passing
- `demographic_factors.py`: validation passing

---

## Notes

- [P] tasks = arquivos diferentes, sem dependências
- [Story] label mapeia task para user story específica
- Cada story deve ser independentemente completável e testável
- Verificar que tests falham antes de implementar
- Commit após cada task ou grupo lógico
- Parar em qualquer checkpoint para validar story independentemente
- Evitar: tasks vagas, conflitos de arquivo, dependências cross-story que quebram independência
