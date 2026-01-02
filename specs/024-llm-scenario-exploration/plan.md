# Implementation Plan: Simulation-Driven Scenario Exploration (LLM-Assisted)

**Branch**: `024-llm-scenario-exploration` | **Date**: 2025-12-31 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/024-llm-scenario-exploration/spec.md`

## Summary

Implementar um sistema de exploracao de cenarios de produto via simulacoes iterativas em arvore, onde o LLM (gpt-4.1-mini) propoe acoes concretas de melhoria, cada acao e traduzida em impactos parametricos no scorecard, simulada via MonteCarloEngine existente, e avaliada por dominancia de Pareto com beam search para manter apenas os K melhores cenarios por iteracao. Execucao paralela/assincrona de nos irmaos para otimizacao de tempo.

## Technical Context

**Language/Version**: Python 3.13+ (backend)
**Primary Dependencies**: FastAPI 0.109+, Pydantic 2.5+, OpenAI SDK, asyncio
**Storage**: PostgreSQL 3 com JSON1 extension (`output/synthlab.db`)
**Testing**: pytest, pytest-asyncio
**Target Platform**: Linux/macOS server
**Project Type**: Web application (backend API)
**Performance Goals**: Exploracao depth=3, beam_width=3 em menos de 5 minutos
**Constraints**: LLM timeout 30s, max_llm_calls default 20
**Scale/Scope**: Arvores com 15-25 nos tipicamente, exploracao interativa

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Test-First (TDD/BDD) | PASS | User stories tem acceptance scenarios em Given-When-Then |
| II. Fast Test Battery | PASS | Unit tests para Pareto filter, beam search serao < 0.5s cada |
| III. Complete Tests Before PR | PASS | All scenarios require tests |
| IV. Frequent Commits | PASS | Workflow permite commits por entidade/service |
| V. Simplicity | PASS | Reutiliza MonteCarloEngine existente, classes focadas |
| VI. Language | PASS | Codigo em ingles, documentacao em portugues |
| VII. Architecture | PASS | Router→Service→Repository, LLM em service com tracing Phoenix |
| VIII. Other Principles | PASS | Phoenix tracing, DRY (reutiliza simulation service), SOLID |

**Architecture Compliance:**
- [x] Router so faz request → service → response
- [x] Logica de negocio em ExplorationService (nao no router)
- [x] LLM calls em ActionProposalService com tracing Phoenix
- [x] Dados persistidos via ExplorationRepository
- [x] Queries SQL parametrizadas

## Project Structure

### Documentation (this feature)

```text
specs/024-llm-scenario-exploration/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (API schemas)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/synth_lab/
├── api/
│   ├── routers/
│   │   └── exploration.py          # NEW: Endpoints de exploracao
│   └── schemas/
│       └── exploration.py          # NEW: Request/Response schemas
│
├── domain/
│   └── entities/
│       ├── exploration.py          # NEW: Exploration, ExplorationConfig
│       ├── scenario_node.py        # NEW: ScenarioNode
│       └── action_catalog.py       # NEW: ActionCatalog, ActionCategory
│
├── repositories/
│   └── exploration_repository.py   # NEW: Persistencia de Exploration/Nodes
│
├── services/
│   └── exploration/                # NEW: Subdominio exploration
│       ├── __init__.py
│       ├── exploration_service.py  # Orquestracao principal
│       ├── action_proposal_service.py # LLM proposals com tracing
│       ├── pareto_filter.py        # Dominancia Pareto + beam search
│       ├── tree_manager.py         # Gestao da arvore de cenarios
│       └── action_catalog.py       # Catalogo estatico de acoes
│
└── infrastructure/
    └── (existing: llm_client.py, phoenix_tracing.py)

tests/
├── unit/
│   └── services/
│       └── exploration/
│           ├── test_pareto_filter.py
│           ├── test_tree_manager.py
│           └── test_action_proposal_service.py
├── integration/
│   └── test_exploration_service.py
└── contract/
    └── test_exploration_api.py
```

**Structure Decision**: Web application backend (Option 2 do template). Novo subdominio `exploration` em services seguindo padrao existente (ex: `simulation/`, `research_agentic/`).

## Complexity Tracking

> Nenhuma violacao de constituicao identificada.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |

## Component Design

### 1. Domain Entities

**Exploration** - Sessao de exploracao:
- `id`: `expl_{hex(4)}`
- `experiment_id`: FK para Experiment
- `baseline_analysis_id`: FK para AnalysisRun (baseline)
- `goal`: Meta (ex: `{"metric": "success_rate", "operator": ">=", "value": 0.40}`)
- `config`: ExplorationConfig (beam_width, max_depth, max_llm_calls, n_executions)
- `status`: running | goal_achieved | depth_limit_reached | cost_limit_reached | no_viable_paths
- `current_depth`: int
- `total_nodes`: int
- `total_llm_calls`: int
- `best_success_rate`: float
- `started_at`, `completed_at`: datetime

**ScenarioNode** - No na arvore:
- `id`: `node_{hex(4)}`
- `exploration_id`: FK para Exploration
- `parent_id`: FK para ScenarioNode (null para raiz)
- `depth`: int
- `action_applied`: str (null para raiz)
- `action_category`: str
- `rationale`: str
- `scorecard_params`: JSON {complexity, initial_effort, perceived_risk, time_to_value}
- `simulation_results`: JSON {success_rate, fail_rate, did_not_try_rate}
- `execution_time_seconds`: float
- `node_status`: active | dominated | winner | expansion_failed

**ActionCatalog** - Catalogo estatico em JSON:
- Categorias: UX/Interface, Onboarding, Fluxo, Comunicacao, Operacional
- Por categoria: exemplos de acoes, faixas de impacto tipicas

### 2. Service Layer

**ExplorationService** - Orquestracao principal:
- `start_exploration(experiment_id, goal, config)` → Exploration
- `run_iteration()` → atualiza arvore
- `get_exploration_tree(exploration_id)` → arvore completa
- `get_winning_path(exploration_id)` → sequencia de acoes

**ActionProposalService** - LLM com tracing:
- `generate_proposals(scenario_node, experiment)` → list[ActionProposal]
- Usa `_tracer.start_as_current_span("generate_proposals")`
- Timeout 30s por chamada
- Modelo: gpt-4.1-mini

**ParetoFilter** - Filtragem e selecao:
- `filter_dominated(nodes)` → nodes nao-dominados
- `beam_select(nodes, k)` → top K por criterio
- Criterio: Δsuccess_rate (maior melhor), risk acumulado (menor melhor)

**TreeManager** - Gestao da arvore:
- `create_root_node(exploration, analysis_run)` → ScenarioNode
- `expand_node(parent, proposals)` → list[ScenarioNode]
- `get_frontier(exploration_id)` → nodes ativos na fronteira

### 3. Repository Layer

**ExplorationRepository**:
- `create_exploration(exploration)` → Exploration
- `update_exploration(exploration)` → Exploration
- `get_by_id(exploration_id)` → Exploration | None
- `create_node(node)` → ScenarioNode
- `update_node_status(node_id, status)` → None
- `get_nodes_by_exploration(exploration_id)` → list[ScenarioNode]
- `get_frontier_nodes(exploration_id)` → list[ScenarioNode]

### 4. API Layer

**Endpoints**:
- `POST /api/explorations` - Inicia exploracao
- `GET /api/explorations/{id}` - Status da exploracao
- `GET /api/explorations/{id}/tree` - Arvore completa
- `GET /api/explorations/{id}/winning-path` - Caminho vencedor
- `POST /api/explorations/{id}/iterate` - Executa uma iteracao (opcional)

### 5. Async/Parallel Execution

**Estrategia para nos irmaos**:
```python
async def expand_frontier(self, frontier_nodes: list[ScenarioNode]):
    """Expande todos os nos da fronteira em paralelo."""
    tasks = [
        self._expand_single_node(node)
        for node in frontier_nodes
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    # Process results, handle exceptions
```

**Pontos de paralelismo**:
1. Chamadas LLM para nos diferentes (nao bloqueiam umas as outras)
2. Simulacoes de nos irmaos (mesmo pai) executam em paralelo
3. Timeout individual de 30s por chamada LLM

## Integration Points

### Existing Components (Reuse)

| Component | Location | Usage |
|-----------|----------|-------|
| MonteCarloEngine | `services/simulation/engine.py` | Executa simulacao de cenarios filhos |
| SimulationService | `services/simulation/simulation_service.py` | Wrapper para engine |
| Experiment | `domain/entities/experiment.py` | Fonte do scorecard_data |
| AnalysisRun | `domain/entities/analysis_run.py` | Baseline analysis |
| LLMClient | `infrastructure/llm_client.py` | Chamadas OpenAI |
| Phoenix Tracing | `infrastructure/phoenix_tracing.py` | Tracing de LLM calls |
| ExperimentRepository | `repositories/experiment_repository.py` | Busca experimento |
| AnalysisRepository | `repositories/analysis_repository.py` | Busca baseline |

### New Tables (PostgreSQL)

```sql
CREATE TABLE explorations (
    id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL REFERENCES experiments(id),
    baseline_analysis_id TEXT NOT NULL REFERENCES analysis_runs(id),
    goal TEXT NOT NULL,  -- JSON
    config TEXT NOT NULL,  -- JSON
    status TEXT NOT NULL DEFAULT 'running',
    current_depth INTEGER NOT NULL DEFAULT 0,
    total_nodes INTEGER NOT NULL DEFAULT 0,
    total_llm_calls INTEGER NOT NULL DEFAULT 0,
    best_success_rate REAL,
    started_at TEXT NOT NULL,
    completed_at TEXT
);

CREATE TABLE scenario_nodes (
    id TEXT PRIMARY KEY,
    exploration_id TEXT NOT NULL REFERENCES explorations(id),
    parent_id TEXT REFERENCES scenario_nodes(id),
    depth INTEGER NOT NULL,
    action_applied TEXT,
    action_category TEXT,
    rationale TEXT,
    scorecard_params TEXT NOT NULL,  -- JSON
    simulation_results TEXT,  -- JSON
    execution_time_seconds REAL,
    node_status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL
);

CREATE INDEX idx_scenario_nodes_exploration ON scenario_nodes(exploration_id);
CREATE INDEX idx_scenario_nodes_status ON scenario_nodes(exploration_id, node_status);
```

## Risk Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM retorna formato invalido | Medio | Validacao rigorosa, descarta proposta invalida |
| Timeout LLM frequente | Medio | Retry com backoff, marca node como expansion_failed |
| Explosao de nos | Alto | Beam search K=3-5, Pareto filter rigoroso |
| Baseline nao existe | Alto | Validacao upfront, rejeita exploracao |
| Simulacao lenta | Medio | Execucao paralela de nos irmaos |
