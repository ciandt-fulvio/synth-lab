# Legacy Components - To Be Deprecated

Este documento lista componentes legados do sistema de simulação original (feature #016) que serão removidos em futuras versões. O novo sistema de análise baseado em experimentos (features #019/#020/#021) substitui essas funcionalidades.

> **Data de análise**: 2025-12-29
> **Status**: Mantido para backward compatibility, planejado para remoção

---

## Resumo da Migração

| Sistema Legado | Sistema Novo |
|---------------|--------------|
| `/api/simulations/*` | `/api/experiments/{id}/analysis/*` |
| `simulation_runs` table | `analysis_runs` table |
| `feature_scorecards` table | Embedded em `experiments.scorecard_data` |
| Scorecard separado | Scorecard integrado ao experimento |

---

## Backend - Arquivos Python

### API Router

| Arquivo | Descrição | Substituído Por |
|---------|-----------|-----------------|
| `src/synth_lab/api/routers/simulation.py` | Router principal da API de simulação legada (~600 linhas). Endpoints: scorecards, simulations, clustering, explainability, insights | `routers/experiments.py` + `routers/analysis.py` |

### Repositories

| Arquivo | Descrição | Substituído Por |
|---------|-----------|-----------------|
| `src/synth_lab/repositories/simulation_repository.py` | Acesso a dados para `simulation_runs` e `synth_outcomes` (via simulation) | `analysis_repository.py` + `analysis_outcome_repository.py` |
| `src/synth_lab/repositories/scorecard_repository.py` | CRUD para `feature_scorecards` standalone | Scorecard embedded em `experiment_repository.py` |
| `src/synth_lab/repositories/sensitivity_repository.py` | Resultados de análise de sensibilidade | Migrar para analysis context |
| `src/synth_lab/repositories/region_repository.py` | Resultados de análise de regiões | Migrar para analysis context |

### Services

| Arquivo | Descrição | Substituído Por |
|---------|-----------|-----------------|
| `src/synth_lab/services/simulation/simulation_service.py` | Orquestração do workflow de simulação | `analysis_execution_service.py` |
| `src/synth_lab/services/simulation/scorecard_service.py` | Lógica de negócio para scorecards | Embedded no experimento |
| `src/synth_lab/services/simulation/scorecard_llm.py` | Geração de insights via LLM para scorecard | Manter (compartilhado) |

**Nota**: Os seguintes services são compartilhados entre sistemas legado e novo:
- `engine.py` - Motor Monte Carlo (usado por ambos)
- `analyzer.py` - Análise de regiões
- `clustering_service.py` - K-Means e clustering hierárquico
- `explainability_service.py` - SHAP e PDP
- `insight_service.py` - Insights LLM
- `chart_data_service.py` - Dados para gráficos

### Domain Entities

| Arquivo | Descrição | Status |
|---------|-----------|--------|
| `src/synth_lab/domain/entities/simulation_run.py` | Entidade `SimulationRun` | Substituído por `AnalysisRun` |
| `src/synth_lab/domain/entities/feature_scorecard.py` | Entidade `FeatureScorecard` | Manter (usado pelo novo sistema) |

---

## Frontend - Arquivos TypeScript/React

### Services

| Arquivo | Descrição | Substituído Por |
|---------|-----------|-----------------|
| `frontend/src/services/simulation-api.ts` | Cliente para `/simulation/*` endpoints | `experiments-api.ts` (funções `getAnalysis*`) |

### Hooks

| Arquivo | Descrição | Substituído Por |
|---------|-----------|-----------------|
| `frontend/src/hooks/use-simulation-charts.ts` | Hooks React Query para charts de simulação | `use-analysis-charts.ts` |
| `frontend/src/hooks/use-outliers.ts` | Duplicado de `use-edge-cases.ts` | Consolidar em `use-edge-cases.ts` |

### Pages

| Arquivo | Descrição | Status |
|---------|-----------|--------|
| `frontend/src/pages/SimulationDetail.tsx` | Página de detalhes de simulação (incompleta) | Remover - nunca foi finalizada |

### Components

| Arquivo | Descrição | Status |
|---------|-----------|--------|
| `frontend/src/components/experiments/NewSimulationDialog.tsx` | Dialog para criar simulação (dead code) | Remover - nunca foi utilizado |

---

## Banco de Dados - Tabelas SQLite

### Tabelas Removidas (já executado)

| Tabela | Registros | Status | Notas |
|--------|-----------|--------|-------|
| `assumption_log` | 0 | **REMOVIDA** | Nunca foi implementada |

### Tabelas a Deprecar

| Tabela | Registros | Substituída Por | Notas |
|--------|-----------|-----------------|-------|
| `feature_scorecards` | 0 | `experiments.scorecard_data` | Scorecard agora embedded no experimento |
| `simulation_runs` | 0 | `analysis_runs` | Análise 1:1 com experimento |
| `region_analyses` | 0 | - | Depende de `simulation_runs` |
| `sensitivity_results` | 0 | - | Depende de `simulation_runs` |

### Tabelas Ativas (NÃO deprecar)

| Tabela | Registros | Uso |
|--------|-----------|-----|
| `experiments` | 8+ | Core - experimentos |
| `analysis_runs` | 4+ | Novo sistema de análise |
| `synth_outcomes` | 200+ | Outcomes por synth |
| `synths` | 50+ | Core - personas sintéticas |
| `synth_groups` | 1+ | Agrupamento de synths |
| `research_executions` | 0+ | Sistema de entrevistas |
| `transcripts` | 0+ | Transcrições de entrevistas |
| `prfaq_metadata` | 0+ | Metadados PRFAQ |
| `interview_guide` | 7+ | Guias de entrevista |
| `chart_insights` | 18+ | Cache de insights LLM |

---

## Plano de Deprecação

### Fase 1: Documentação (ATUAL)
- [x] Documentar todos os componentes legados
- [x] Remover tabela `assumption_log` (nunca usada)

### Fase 2: Frontend Cleanup
- [ ] Remover `NewSimulationDialog.tsx` (dead code)
- [ ] Remover `SimulationDetail.tsx` (página incompleta)
- [ ] Consolidar `use-outliers.ts` em `use-edge-cases.ts`
- [ ] Mover funções usadas de `simulation-api.ts` para `experiments-api.ts`

### Fase 3: Backend Cleanup
- [ ] Migrar sensitivity/region analysis para contexto de analysis
- [ ] Remover `simulation.py` router
- [ ] Remover repositories legados
- [ ] Atualizar rotas no frontend

### Fase 4: Database Cleanup
- [ ] Remover tabelas legadas do schema
- [ ] Criar migration para dropar tabelas

---

## Notas Importantes

1. **Não quebrar produção**: O sistema legado ainda pode ter dados em ambientes de produção. Sempre verificar antes de remover.

2. **Engine compartilhado**: O `MonteCarloEngine` (`engine.py`) é usado por ambos os sistemas. Não remover.

3. **Insights e Charts**: Os services de insights e charts são compartilhados. Funcionam com `simulation_id` ou `analysis_id`.

4. **Frontend já migrado**: A maioria do frontend já usa o novo sistema via `ExperimentDetail.tsx` e `use-analysis-charts.ts`.
