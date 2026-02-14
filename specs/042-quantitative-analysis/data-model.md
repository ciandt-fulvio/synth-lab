# Data Model: Análise Quantitativa

**Phase 1 Output** | **Date**: 2026-02-14 | **Branch**: `042-quantitative-analysis`

## Entity Relationship Diagram

```
Experiment (existing)
  │ 1:1 (unique FK)
  ├── CausalModel
  │     │ 1:N
  │     └── CausalEdge (7-10 per model)
  │ 1:N
  ├── SimulationRun
  │     │ 1:N
  │     └── AnalysisInterpretation (3 per run)
  │ 1:1 (existing)
  └── InterviewGuide (updated by quanti, existing table)
```

## New Entities

### CausalModel

Modelo causal gerado pelo LLM. Relação 1:1 com experimento (apenas 1 modelo ativo por experimento).

| Campo | Tipo | Constraints | Descrição |
|-------|------|-------------|-----------|
| `id` | `str` | PK, `cm_[a-f0-9]{8}` | ID único |
| `experiment_id` | `str` | FK → experiments.id, UNIQUE | Experimento associado |
| `label` | `str` | max 200 chars | Título do modelo (gerado pelo LLM) |
| `intercept_mu` | `float` | [-1.0, 1.0] | Intercepto médio da simulação |
| `intercept_sigma` | `float` | [0.1, 1.0] | Desvio padrão do intercepto |
| `nodes` | `list[str]` | JSON, 7-10 items | Nomes dos nós do DAG |
| `raw_llm_response` | `dict` | JSON, nullable | Response completa do LLM (debug) |
| `created_at` | `datetime` | UTC, auto | Timestamp de criação |

**Validações**:
- `experiment_id` deve referenciar experimento existente
- `nodes` deve ter entre 7 e 10 items
- `intercept_mu` entre -1.0 e 1.0
- `intercept_sigma` entre 0.1 e 1.0

**ID Generation**: `cm_{secrets.token_hex(4)}`

---

### CausalEdge

Aresta do DAG causal. Cada aresta é uma afirmação com 5 opções Likert.

| Campo | Tipo | Constraints | Descrição |
|-------|------|-------------|-----------|
| `id` | `str` | PK, gerado pelo LLM | ID da aresta (ex: "e1", "e2") |
| `causal_model_id` | `str` | FK → causal_models.id | Modelo pai |
| `from_node` | `str` | max 50 chars | Nó de origem |
| `to_node` | `str` | max 50 chars | Nó de destino |
| `user_var` | `str` | enum 10 valores | userVar mapeada |
| `direction` | `int` | 1 ou -1 | Direção da relação |
| `header` | `str` | max 300 chars | Header contextual da afirmação |
| `options` | `list[dict]` | JSON, exatamente 5 | Opções Likert: [{text, mu, sigma}] |
| `default_option` | `int` | [0, 4] | Opção default sugerida pelo LLM |
| `selected_option` | `int \| None` | [0, 4] ou null | Seleção do PM (null = não respondida) |

**Validações**:
- `user_var` deve ser um dos 10 valores válidos: `ageNorm`, `incomeNorm`, `eduNorm`, `familySizeNorm`, `hasVisualDisab`, `hasMotorDisab`, `digitalCapability`, `riskAversion`, `institutionalTrust`, `frictionTolerance`
- `options` deve ter exatamente 5 items, cada um com `text` (str), `mu` (float), `sigma` (float)
- `from_node` e `to_node` devem existir em `causal_model.nodes`
- `direction` deve ser 1 ou -1
- `selected_option` é nullable (PM pode não ter respondido)

**Opções Likert Fixas** (mu/sigma):
| Index | mu | sigma | Semântica |
|-------|-----|-------|-----------|
| 0 | 0.80 | 0.15 | Concordância forte |
| 1 | 0.65 | 0.25 | Concordância significativa |
| 2 | 0.50 | 0.50 | Incerteza ("Não sei dizer...") |
| 3 | 0.30 | 0.25 | Concordância fraca |
| 4 | 0.15 | 0.15 | Discordância |

---

### SimulationRun

Resultado de uma execução de simulação Monte Carlo. Imutável após criação.

| Campo | Tipo | Constraints | Descrição |
|-------|------|-------------|-----------|
| `id` | `str` | PK, `sr_[a-f0-9]{8}` | ID único |
| `experiment_id` | `str` | FK → experiments.id | Experimento |
| `causal_model_id` | `str` | FK → causal_models.id | Modelo usado |
| `n_iterations` | `int` | default 3000 | Iterações Monte Carlo |
| `n_synths` | `int` | > 0 | Número de synths usados |
| `selections` | `dict` | JSON | Mapa edge_id → selected_option no momento da simulação |
| `stats` | `dict` | JSON | {mean, median, std, p10, p90} |
| `distribution` | `list[float]` | JSON | Array de taxas por iteração (3000 floats) |
| `segments` | `dict` | JSON | {age: {...}, income: {...}, education: {...}} |
| `sensitivity` | `list[dict]` | JSON | [{edge_id, header, impact, mean_low, mean_high}] |
| `created_at` | `datetime` | UTC, auto | Timestamp |

**Validações**:
- `selections` deve ter entrada para cada edge do `causal_model`
- `stats` deve conter: mean, median, std, p10, p90 (todos floats)
- `segments` deve conter chaves: age, income, education

**ID Generation**: `sr_{secrets.token_hex(4)}`

---

### AnalysisInterpretation

Interpretação AI de uma seção dos resultados.

| Campo | Tipo | Constraints | Descrição |
|-------|------|-------------|-----------|
| `id` | `str` | PK, `ai_[a-f0-9]{8}` | ID único |
| `simulation_run_id` | `str` | FK → simulation_runs.id | Run associado |
| `section` | `str` | enum: distribution, segments, sensitivity | Seção interpretada |
| `raw_text` | `str` | text | Estatísticas raw (sem LLM) |
| `ai_text` | `str` | text | Interpretação do LLM |
| `model` | `str` | max 50 | Modelo usado (ex: "gpt-4o-mini") |
| `created_at` | `datetime` | UTC, auto | Timestamp |

**Validações**:
- `section` deve ser um dos 3 valores: `distribution`, `segments`, `sensitivity`
- Constraint UNIQUE em (`simulation_run_id`, `section`)

**ID Generation**: `ai_{secrets.token_hex(4)}`

---

## Existing Entity Impact

### InterviewGuide (existing — modified behavior)

Nenhuma alteração na tabela. Mudança apenas no comportamento:
- **Antes**: Gerado automaticamente na criação do experimento
- **Depois**: Gerado automaticamente após simulação Monte Carlo (sobrescreve anterior)
- Campos preenchidos pela análise quantitativa: `context_definition`, `questions`, `context_examples`

### Experiment (existing — no schema change)

Nenhuma alteração no schema. Relacionamento com `CausalModel` e `SimulationRun` via FK nessas novas tabelas.

---

## Database Tables (DDL Summary)

### causal_models

```sql
CREATE TABLE causal_models (
    id VARCHAR(50) PRIMARY KEY,
    experiment_id VARCHAR(50) NOT NULL UNIQUE REFERENCES experiments(id) ON DELETE CASCADE,
    label VARCHAR(200) NOT NULL,
    intercept_mu FLOAT NOT NULL,
    intercept_sigma FLOAT NOT NULL,
    nodes JSONB NOT NULL,
    raw_llm_response JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_causal_models_experiment ON causal_models(experiment_id);
```

### causal_edges

```sql
CREATE TABLE causal_edges (
    id VARCHAR(50) NOT NULL,
    causal_model_id VARCHAR(50) NOT NULL REFERENCES causal_models(id) ON DELETE CASCADE,
    from_node VARCHAR(50) NOT NULL,
    to_node VARCHAR(50) NOT NULL,
    user_var VARCHAR(30) NOT NULL,
    direction SMALLINT NOT NULL CHECK (direction IN (1, -1)),
    header VARCHAR(300) NOT NULL,
    options JSONB NOT NULL,
    default_option SMALLINT NOT NULL CHECK (default_option BETWEEN 0 AND 4),
    selected_option SMALLINT CHECK (selected_option BETWEEN 0 AND 4),
    PRIMARY KEY (id, causal_model_id)
);

CREATE INDEX idx_causal_edges_model ON causal_edges(causal_model_id);
```

### simulation_runs

```sql
CREATE TABLE simulation_runs (
    id VARCHAR(50) PRIMARY KEY,
    experiment_id VARCHAR(50) NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    causal_model_id VARCHAR(50) NOT NULL REFERENCES causal_models(id) ON DELETE CASCADE,
    n_iterations INTEGER NOT NULL DEFAULT 3000,
    n_synths INTEGER NOT NULL,
    selections JSONB NOT NULL,
    stats JSONB NOT NULL,
    distribution JSONB NOT NULL,
    segments JSONB NOT NULL,
    sensitivity JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_simulation_runs_experiment ON simulation_runs(experiment_id);
CREATE INDEX idx_simulation_runs_created ON simulation_runs(created_at DESC);
```

### analysis_interpretations

```sql
CREATE TABLE analysis_interpretations (
    id VARCHAR(50) PRIMARY KEY,
    simulation_run_id VARCHAR(50) NOT NULL REFERENCES simulation_runs(id) ON DELETE CASCADE,
    section VARCHAR(20) NOT NULL CHECK (section IN ('distribution', 'segments', 'sensitivity')),
    raw_text TEXT NOT NULL,
    ai_text TEXT NOT NULL,
    model VARCHAR(50) NOT NULL DEFAULT 'gpt-4o-mini',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE (simulation_run_id, section)
);

CREATE INDEX idx_interpretations_run ON analysis_interpretations(simulation_run_id);
```

---

## State Transitions

### CausalModel Lifecycle

```
[não existe] → generate_causal_model() → [modelo gerado, edges com selected_option=null]
→ PM seleciona Likerts → [modelo calibrado, edges com selected_option preenchido]
→ re-generate (se PM clicar "Gerar Modelo" de novo) → [modelo anterior deletado, novo criado]
```

### SimulationRun Lifecycle

```
[não existe] → run_simulation() → [run criado com stats + distribution + segments + sensitivity]
→ (imutável — nova simulação cria novo run)
```

### AnalysisInterpretation Lifecycle

```
[não existe] → generate_interpretations() → [3 interpretações criadas (1 por section)]
→ (imutáveis — vinculadas ao run)
```
