# Quickstart: Análise Quantitativa

**Phase 1 Output** | **Date**: 2026-02-14 | **Branch**: `042-quantitative-analysis`

## Pré-requisitos

1. Ambiente de dev rodando: `make dev-up`
2. Banco de dados com seed: synths com dados demográficos e sensitivities
3. Pelo menos 1 experimento criado com `synth_group_id` associado a um grupo com synths

## Ordem de Implementação

```
1. Domain Entities (causal_model.py, simulation_run.py)
2. ORM Models (causal_model.py, simulation_run.py)
3. Alembic Migration
4. Repositories (causal_model_repository.py, simulation_run_repository.py)
5. Simulation Engine (simulation_engine.py — Monte Carlo puro)
6. userVar Extractors (dentro de simulation_engine.py)
7. Service (quantitative_analysis_service.py — orquestração)
8. API Router + Schemas
9. Adaptar InterviewGuideGeneratorService (novo prompt, remover auto-gen na criação)
10. Frontend Types
11. Frontend Service (quantitative-analysis-api.ts)
12. Frontend Hooks (use-quantitative-analysis.ts)
13. Frontend Components (DAGView, Likerts, Results)
14. Integrar na aba "Análise Quanti" do ExperimentDetail
15. E2E Tests
```

## Verificação Rápida (por camada)

### Backend — Testar Simulação Engine

```bash
# Após implementar simulation_engine.py
cd /Users/fulvio/Projects/synth-lab
uv run python -m synth_lab.services.simulation_engine
# Deve rodar simulação com dados fake e imprimir stats
```

### Backend — Testar Service

```bash
# Após implementar service + repository
uv run pytest tests/unit/test_simulation_engine.py -v
uv run pytest tests/integration/test_quantitative_analysis_service.py -v
```

### Backend — Testar API

```bash
# Com dev-up rodando
curl -X POST http://localhost:8000/experiments/{exp_id}/quantitative-analysis/generate \
  -H "Content-Type: application/json" | python -m json.tool

# Após gerar modelo e selecionar Likerts:
curl -X POST http://localhost:8000/experiments/{exp_id}/quantitative-analysis/simulate \
  -H "Content-Type: application/json" | python -m json.tool
```

### Frontend — Verificar aba

1. Acesse `http://localhost:8080/experiments/{id}?tab=quanti`
2. Clique "Gerar Modelo" → DAG deve aparecer
3. Selecione opções Likert → DAG deve reagir (espessura/cor)
4. Clique "Simular" → Resultados devem aparecer abaixo

## Pontos de Atenção

- **NumPy**: Precisa ser adicionado ao `pyproject.toml` antes de implementar simulation_engine
- **Phoenix Tracing**: Todas as chamadas LLM devem ter `_tracer.start_as_current_span()`
- **Alembic Migration**: Rodar `make db-migrate MSG='add causal model tables'` após criar ORM models
- **InterviewGuideGeneratorService**: Encontrar onde é chamado na criação do experimento e remover essa chamada
- **Timeouts**: LLM calls devem ter timeout de 30s. Simulação deve ter timeout de 30s
- **Seed para testes**: Usar `np.random.default_rng(42)` em testes para resultados determinísticos
