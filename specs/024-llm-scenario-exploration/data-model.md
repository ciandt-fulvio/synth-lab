# Data Model: Simulation-Driven Scenario Exploration

**Feature**: 024-llm-scenario-exploration
**Date**: 2025-12-31

## Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────────┐
│   Experiment    │       │     AnalysisRun     │
│  (existing)     │       │     (existing)      │
├─────────────────┤       ├─────────────────────┤
│ id              │       │ id                  │
│ name            │       │ experiment_id       │
│ hypothesis      │       │ scenario_id         │
│ scorecard_data  │───┐   │ aggregated_outcomes │
└─────────────────┘   │   └─────────────────────┘
                      │              │
                      │              │
                      ▼              ▼
              ┌───────────────────────────────┐
              │         Exploration           │
              ├───────────────────────────────┤
              │ id (PK)                       │
              │ experiment_id (FK)            │
              │ baseline_analysis_id (FK)     │
              │ goal (JSON)                   │
              │ config (JSON)                 │
              │ status                        │
              │ current_depth                 │
              │ total_nodes                   │
              │ total_llm_calls               │
              │ best_success_rate             │
              │ started_at                    │
              │ completed_at                  │
              └───────────────────────────────┘
                           │
                           │ 1:N
                           ▼
              ┌───────────────────────────────┐
              │       ScenarioNode            │
              ├───────────────────────────────┤
              │ id (PK)                       │
              │ exploration_id (FK)           │
              │ parent_id (FK, self-ref)      │
              │ depth                         │
              │ action_applied                │
              │ action_category               │
              │ rationale                     │
              │ scorecard_params (JSON)       │
              │ simulation_results (JSON)     │
              │ execution_time_seconds        │
              │ node_status                   │
              │ created_at                    │
              └───────────────────────────────┘
```

---

## Entities

### Exploration

Representa uma sessao de exploracao de cenarios.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | TEXT | PK, pattern: `expl_[a-f0-9]{8}` | Identificador unico |
| experiment_id | TEXT | FK → experiments.id, NOT NULL | Experimento de origem |
| baseline_analysis_id | TEXT | FK → analysis_runs.id, NOT NULL | Analise baseline |
| goal | TEXT (JSON) | NOT NULL | Meta de performance |
| config | TEXT (JSON) | NOT NULL | Configuracao de busca |
| status | TEXT | NOT NULL, enum | Status atual |
| current_depth | INTEGER | NOT NULL, DEFAULT 0, >= 0 | Profundidade atual |
| total_nodes | INTEGER | NOT NULL, DEFAULT 0, >= 0 | Total de nos criados |
| total_llm_calls | INTEGER | NOT NULL, DEFAULT 0, >= 0 | Chamadas LLM feitas |
| best_success_rate | REAL | NULL, [0,1] | Melhor success_rate encontrado |
| started_at | TEXT | NOT NULL, ISO 8601 | Inicio da exploracao |
| completed_at | TEXT | NULL, ISO 8601 | Fim da exploracao |

**Status Enum**:
- `running` - Exploracao em andamento
- `goal_achieved` - Meta atingida
- `depth_limit_reached` - Limite de profundidade atingido
- `cost_limit_reached` - Limite de custo (LLM calls) atingido
- `no_viable_paths` - Nenhum caminho viavel restante

**Goal JSON Schema**:
```json
{
  "metric": "success_rate",
  "operator": ">=",
  "value": 0.40
}
```

**Config JSON Schema**:
```json
{
  "beam_width": 3,
  "max_depth": 5,
  "max_llm_calls": 20,
  "n_executions": 100,
  "sigma": 0.1,
  "seed": null
}
```

---

### ScenarioNode

Representa um no na arvore de exploracao.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | TEXT | PK, pattern: `node_[a-f0-9]{8}` | Identificador unico |
| exploration_id | TEXT | FK → explorations.id, NOT NULL | Exploracao pai |
| parent_id | TEXT | FK → scenario_nodes.id, NULL | No pai (null para raiz) |
| depth | INTEGER | NOT NULL, >= 0 | Nivel na arvore (0 = raiz) |
| action_applied | TEXT | NULL | Acao que gerou este no |
| action_category | TEXT | NULL | Categoria da acao |
| rationale | TEXT | NULL | Justificativa da acao |
| scorecard_params | TEXT (JSON) | NOT NULL | Parametros do scorecard |
| simulation_results | TEXT (JSON) | NULL | Resultados da simulacao |
| execution_time_seconds | REAL | NULL, >= 0 | Tempo de simulacao |
| node_status | TEXT | NOT NULL, enum | Status do no |
| created_at | TEXT | NOT NULL, ISO 8601 | Criacao do no |

**Node Status Enum**:
- `active` - No ativo na fronteira
- `dominated` - Dominado por outro no
- `winner` - Atingiu a meta
- `expansion_failed` - Falha ao expandir (LLM timeout, etc)

**Scorecard Params JSON Schema**:
```json
{
  "complexity": 0.45,
  "initial_effort": 0.30,
  "perceived_risk": 0.25,
  "time_to_value": 0.40
}
```

**Simulation Results JSON Schema**:
```json
{
  "success_rate": 0.35,
  "fail_rate": 0.40,
  "did_not_try_rate": 0.25
}
```

---

### ActionProposal (Value Object - nao persistido)

Representa uma proposta de acao gerada pelo LLM.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| action | str | NOT NULL, max 500 chars | Descricao da acao |
| category | str | NOT NULL, enum | Categoria do catalogo |
| rationale | str | NOT NULL, max 200 chars | Justificativa |
| impacts | dict[str, float] | NOT NULL | Impactos estimados |

**Category Enum**:
- `ux_interface` - UX / Interface
- `onboarding` - Onboarding / Educacao
- `flow` - Fluxo / Processo
- `communication` - Comunicacao / Feedback
- `operational` - Operacional / Feature Control

**Impacts Schema**:
```json
{
  "complexity": -0.02,
  "initial_effort": 0.00,
  "perceived_risk": 0.01,
  "time_to_value": -0.01
}
```

**Validation Rules**:
- Cada impact value deve estar em [-0.10, +0.10]
- Pelo menos um impact deve ser diferente de zero
- Category deve existir no catalogo

---

### ActionCatalog (Static Configuration)

Catalogo de categorias de acoes carregado de arquivo JSON.

**Location**: `data/action_catalog.json`

**Schema**:
```json
{
  "version": "1.0.0",
  "categories": [
    {
      "id": "ux_interface",
      "name": "UX / Interface",
      "description": "Melhorias na interface de usuario",
      "examples": [
        {
          "action": "Tooltip contextual",
          "typical_impacts": {
            "complexity": {"min": -0.04, "max": -0.01},
            "time_to_value": {"min": -0.03, "max": -0.01},
            "perceived_risk": {"min": 0.00, "max": 0.00}
          }
        }
      ]
    }
  ]
}
```

---

## State Transitions

### Exploration Status

```
                    ┌─────────────┐
                    │   running   │
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │goal_achieved│ │depth_limit_ │ │cost_limit_  │
    │             │ │  reached    │ │  reached    │
    └─────────────┘ └─────────────┘ └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │no_viable_   │
                    │   paths     │
                    └─────────────┘
```

### ScenarioNode Status

```
    ┌─────────────┐
    │   active    │◄─────────── Criacao do no
    └──────┬──────┘
           │
     ┌─────┼─────┐
     │     │     │
     ▼     ▼     ▼
┌────────┐┌────────┐┌──────────────┐
│dominated││ winner ││expansion_failed│
└────────┘└────────┘└──────────────┘
```

---

## SQL DDL

```sql
-- Explorations table
CREATE TABLE IF NOT EXISTS explorations (
    id TEXT PRIMARY KEY CHECK (id GLOB 'expl_[a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9]'),
    experiment_id TEXT NOT NULL,
    baseline_analysis_id TEXT NOT NULL,
    goal TEXT NOT NULL,
    config TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'goal_achieved', 'depth_limit_reached', 'cost_limit_reached', 'no_viable_paths')),
    current_depth INTEGER NOT NULL DEFAULT 0 CHECK (current_depth >= 0),
    total_nodes INTEGER NOT NULL DEFAULT 0 CHECK (total_nodes >= 0),
    total_llm_calls INTEGER NOT NULL DEFAULT 0 CHECK (total_llm_calls >= 0),
    best_success_rate REAL CHECK (best_success_rate IS NULL OR (best_success_rate >= 0 AND best_success_rate <= 1)),
    started_at TEXT NOT NULL,
    completed_at TEXT,
    FOREIGN KEY (experiment_id) REFERENCES experiments(id),
    FOREIGN KEY (baseline_analysis_id) REFERENCES analysis_runs(id)
);

-- Scenario nodes table
CREATE TABLE IF NOT EXISTS scenario_nodes (
    id TEXT PRIMARY KEY CHECK (id GLOB 'node_[a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9]'),
    exploration_id TEXT NOT NULL,
    parent_id TEXT,
    depth INTEGER NOT NULL CHECK (depth >= 0),
    action_applied TEXT,
    action_category TEXT,
    rationale TEXT,
    scorecard_params TEXT NOT NULL,
    simulation_results TEXT,
    execution_time_seconds REAL CHECK (execution_time_seconds IS NULL OR execution_time_seconds >= 0),
    node_status TEXT NOT NULL DEFAULT 'active' CHECK (node_status IN ('active', 'dominated', 'winner', 'expansion_failed')),
    created_at TEXT NOT NULL,
    FOREIGN KEY (exploration_id) REFERENCES explorations(id),
    FOREIGN KEY (parent_id) REFERENCES scenario_nodes(id)
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_explorations_experiment ON explorations(experiment_id);
CREATE INDEX IF NOT EXISTS idx_explorations_status ON explorations(status);
CREATE INDEX IF NOT EXISTS idx_scenario_nodes_exploration ON scenario_nodes(exploration_id);
CREATE INDEX IF NOT EXISTS idx_scenario_nodes_parent ON scenario_nodes(parent_id);
CREATE INDEX IF NOT EXISTS idx_scenario_nodes_status ON scenario_nodes(exploration_id, node_status);
CREATE INDEX IF NOT EXISTS idx_scenario_nodes_depth ON scenario_nodes(exploration_id, depth);
```

---

## Queries Comuns

### Buscar fronteira ativa
```sql
SELECT * FROM scenario_nodes
WHERE exploration_id = ?
AND node_status = 'active'
ORDER BY depth DESC;
```

### Buscar caminho ate um no
```sql
WITH RECURSIVE path AS (
    SELECT * FROM scenario_nodes WHERE id = ?
    UNION ALL
    SELECT sn.* FROM scenario_nodes sn
    INNER JOIN path p ON sn.id = p.parent_id
)
SELECT * FROM path ORDER BY depth ASC;
```

### Contar nos por status
```sql
SELECT node_status, COUNT(*) as count
FROM scenario_nodes
WHERE exploration_id = ?
GROUP BY node_status;
```

### Buscar melhor no por success_rate
```sql
SELECT * FROM scenario_nodes
WHERE exploration_id = ?
AND simulation_results IS NOT NULL
ORDER BY json_extract(simulation_results, '$.success_rate') DESC
LIMIT 1;
```
