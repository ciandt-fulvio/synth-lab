# Causal Simulation - Implementation Summary

## Overview

Feature 035 implementa um sistema de **Simulação Causal** completamente separado do sistema de **Simulação** existente (relacionado a experimentos).

## Conceitos Distintos

### 1. Simulation (Existente - Contexto de Experimentos)
- **Rota Frontend**: `/experiments/:id/simulations/:simId`
- **Componente**: `SimulationDetail.tsx`
- **Relacionado a**: Experimentos com synths

### 2. CausalSimulation (Novo - Feature 035)
- **Rotas Frontend**:
  - `/simulations` - Lista de simulações causais
  - `/simulations/:id` - Detalhes da simulação causal
- **Componentes**:
  - `Simulations.tsx` - Lista
  - `CausalSimulationDetail.tsx` - Detalhes
- **Relacionado a**: Previsões baseadas em perguntas de negócio

## Phase 3 - Implementação Completa

### Backend (12 tarefas completas)

#### Services (T021-T026)
- ✅ `question_parser_service.py` - Parse perguntas em estrutura
- ✅ `dag_constructor_service.py` - Gera DAG causal com LLM
- ✅ `hypothesis_parametrizer_service.py` - Quantifica hipóteses
- ✅ `simulation_engine_service.py` - Motor Monte Carlo (500 mundos)
- ✅ `evidence_calculator_service.py` - Agrega estatísticas
- ✅ `insight_generator_service.py` - Sintetiza insights com LLM

#### Repositories (T027-T029)
- ✅ `causal_dag_repository.py` - Persistência de DAG (JSONB)
- ✅ `hypothesis_repository.py` - Batch operations
- ✅ `simulation_insight_repository.py` - Insights causais (separado de chart insights)

#### API Layer (T030-T034)
- ✅ `routers/simulations.py` - 5 endpoints:
  - POST `/simulations` - Criar simulação
  - GET `/simulations/{id}` - Detalhes
  - GET `/simulations` - Listar
  - DELETE `/simulations/{id}` - Deletar
  - POST `/simulations/{id}/run` - Executar simulação
- ✅ `routers/simulation_insights.py` - 2 endpoints:
  - GET `/simulations/{id}/insights` - Listar insights
  - GET `/insights/{id}/trace` - Rastreabilidade
- ✅ `schemas/simulation.py` - Validação Pydantic
- ✅ Registrado em `api/main.py`

### Frontend (6 tarefas completas)

#### Services & Hooks (T038)
- ✅ `services/simulations-api.ts` - Typed API calls
- ✅ `hooks/use-simulations.ts` - React Query hooks
- ✅ `lib/query-keys.ts` - Cache keys adicionadas

#### Components (T035-T037)
- ✅ `QuestionInput.tsx` - Input de pergunta com exemplos
- ✅ `PercentileChart.tsx` - Box plot (p5/p25/p50/p75/p95)
- ✅ `SensitivityChart.tsx` - Variance explained (R²)

#### Pages
- ✅ `Simulations.tsx` - Lista de simulações causais
- ✅ `CausalSimulationDetail.tsx` - Detalhes e resultados
- ✅ Routes registradas em `App.tsx`

## Progresso Total

- **Phase 1**: ✅ 8/8 (100%) - Domain entities
- **Phase 2**: ✅ 12/12 (100%) - Database & migrations
- **Phase 3**: ✅ 18/18 (100%) - API & Frontend **COMPLETO**
- **Total MVP**: 38/38 (100%) ✅

## Próximos Passos (Fora do MVP)

Phase 4 (futuro):
- Persistir SimulatedWorld no banco
- Exportar resultados (PDF, CSV)
- Comparação de simulações
- Visualizações avançadas (sankey, network graph)

## Separação de Concerns

### Backend
```
Causal Simulation:
- /simulations/* (novo)
- simulation_insight_repository.py (novo)

Experiment Simulation:
- /experiments/{id}/simulations/{id} (existente)
- insight_repository.py (existente - para charts)
```

### Frontend
```
Causal Simulation:
- /simulations (novo)
- /simulations/:id (novo)
- CausalSimulationDetail.tsx (novo)

Experiment Simulation:
- /experiments/:id/simulations/:simId (existente)
- SimulationDetail.tsx (existente)
```

## Arquivos Criados/Modificados

### Backend
- 6 services em `services/simulation/`
- 3 repositories
- 2 routers
- 1 schemas file
- main.py (registrar routers)

### Frontend
- 1 API service
- 1 hook file
- 3 componentes
- 2 páginas
- query-keys.ts (adicionar keys)
- App.tsx (adicionar rotas)

## Status: ✅ PHASE 3 COMPLETO

Todos os componentes do MVP foram implementados e o build está passando sem erros.
