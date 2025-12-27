# Data Model: Experiment Hub

**Feature**: 018-experiment-hub
**Date**: 2025-12-27

## Diagrama de Entidades (ERD)

```
+------------------+
|   experiments    |
+------------------+
| id (PK)          |
| name             |
| hypothesis       |
| description      |
| created_at       |
| updated_at       |
+------------------+
        |
        | 1
        |
        +---------------------------+
        |                           |
        | N                         | N
        v                           v
+------------------+       +----------------------+
| feature_scorecards|       | research_executions  |
+------------------+       +----------------------+
| id (PK)          |       | exec_id (PK)         |
| experiment_id(FK)|       | experiment_id (FK)   |
| data (JSON)      |       | topic_name           |
| created_at       |       | status               |
| updated_at       |       | synth_count          |
+------------------+       | ...                  |
        |                  +----------------------+
        | 1                         |
        |                           | 1
        | N                         |
        v                           | N
+------------------+                v
| simulation_runs  |       +------------------+
+------------------+       |   transcripts    |
| id (PK)          |       +------------------+
| scorecard_id(FK) |       | id (PK)          |
| scenario_id      |       | exec_id (FK)     |
| config (JSON)    |       | synth_id (FK)    |
| status           |       | content (JSON)   |
| ...              |       | ...              |
+------------------+       +------------------+
        |
        | 1
        |
        +---------------------------+
        |                           |
        | N                         | N
        v                           v
+------------------+       +------------------+
|  synth_outcomes  |       | region_analyses  |
+------------------+       +------------------+
| simulation_id(FK)|       | simulation_id(FK)|
| synth_id (FK)    |       | rules (JSON)     |
| did_not_try_rate |       | synth_count      |
| failed_rate      |       | ...              |
| success_rate     |       +------------------+
+------------------+


+------------------+       +------------------+
|   synth_groups   |       |   scenarios      |
+------------------+       +------------------+
| id (PK)          |       | id (PK)          |
| name             |       | name             |
| description      |       | description      |
| created_at       |       | modifiers (JSON) |
+------------------+       +------------------+
        |                  (Carregados de JSON,
        | 1                 nao persistidos)
        |
        | N
        v
+------------------+
|      synths      |
+------------------+
| id (PK)          |
| synth_group_id   |
|   (FK, NOT NULL) |
| nome             |
| descricao        |
| data (JSON)      |
| avatar_path      |
| created_at       |
| ...              |
+------------------+
```

---

## Entidades

### Experiment

Representa uma feature ou hipótese a ser testada. É o container central que agrupa simulações e entrevistas relacionadas.

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| id | TEXT | PK, NOT NULL | ID único (ex: `exp_a1b2c3d4`) |
| name | TEXT | NOT NULL, max 100 chars | Nome curto da feature |
| hypothesis | TEXT | NOT NULL, max 500 chars | Descrição da hipótese a ser testada |
| description | TEXT | NULL, max 2000 chars | Contexto adicional, links, referências |
| created_at | TEXT | NOT NULL | ISO 8601 timestamp de criação |
| updated_at | TEXT | NULL | ISO 8601 timestamp de última atualização |

**Relacionamentos**:
- 1:N com `feature_scorecards` (um experimento tem N scorecards)
- 1:N com `research_executions` (um experimento tem N entrevistas)

**Índices**:
- `idx_experiments_created` em `created_at DESC`
- `idx_experiments_name` em `name`

---

### SynthGroup

Representa um agrupamento de synths gerados em conjunto. Permite rastrear "safras" de synths.

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| id | TEXT | PK, NOT NULL | ID único (ex: `grp_a1b2c3d4`) |
| name | TEXT | NOT NULL | Nome descritivo do grupo |
| description | TEXT | NULL | Descrição do propósito/contexto |
| created_at | TEXT | NOT NULL | ISO 8601 timestamp de criação |

**Relacionamentos**:
- 1:N com `synths` (um grupo contém N synths)

**Índices**:
- `idx_synth_groups_created` em `created_at DESC`

---

### FeatureScorecard (Extensão)

Adiciona vinculação obrigatória com experimento.

| Campo Novo | Tipo | Restrições | Descrição |
|------------|------|------------|-----------|
| experiment_id | TEXT | FK NOT NULL | Referência ao experimento pai |

**Índices Novos**:
- `idx_scorecards_experiment` em `experiment_id`

---

### ResearchExecution (Extensão)

Adiciona vinculação obrigatória com experimento.

| Campo Novo | Tipo | Restrições | Descrição |
|------------|------|------------|-----------|
| experiment_id | TEXT | FK NOT NULL | Referência ao experimento pai |

**Índices Novos**:
- `idx_executions_experiment` em `experiment_id`

---

### Synth (Extensão)

Adiciona vinculação obrigatória com grupo.

| Campo Novo | Tipo | Restrições | Descrição |
|------------|------|------------|-----------|
| synth_group_id | TEXT | FK NOT NULL | Referência ao grupo de synths |

**Índices Novos**:
- `idx_synths_group` em `synth_group_id`

---

## Schema SQL Completo

```sql
-- Experiments table (NEW)
CREATE TABLE IF NOT EXISTS experiments (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    hypothesis TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_experiments_created ON experiments(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_experiments_name ON experiments(name);

-- Synth Groups table (NEW)
CREATE TABLE IF NOT EXISTS synth_groups (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_synth_groups_created ON synth_groups(created_at DESC);

-- Synths table (MODIFIED - add synth_group_id)
CREATE TABLE IF NOT EXISTS synths (
    id TEXT PRIMARY KEY,
    synth_group_id TEXT NOT NULL,
    nome TEXT NOT NULL,
    descricao TEXT,
    link_photo TEXT,
    avatar_path TEXT,
    created_at TEXT NOT NULL,
    version TEXT DEFAULT '2.0.0',
    data TEXT CHECK(json_valid(data) OR data IS NULL),
    FOREIGN KEY (synth_group_id) REFERENCES synth_groups(id)
);

CREATE INDEX IF NOT EXISTS idx_synths_created_at ON synths(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_synths_nome ON synths(nome);
CREATE INDEX IF NOT EXISTS idx_synths_group ON synths(synth_group_id);

-- Research executions table (MODIFIED - add experiment_id)
CREATE TABLE IF NOT EXISTS research_executions (
    exec_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    topic_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'completed',
    synth_count INTEGER NOT NULL,
    successful_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    model TEXT DEFAULT 'gpt-5-mini',
    max_turns INTEGER DEFAULT 6,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    summary_content TEXT,
    CHECK(status IN ('pending', 'running', 'generating_summary', 'completed', 'failed')),
    FOREIGN KEY (experiment_id) REFERENCES experiments(id)
);

CREATE INDEX IF NOT EXISTS idx_executions_topic ON research_executions(topic_name);
CREATE INDEX IF NOT EXISTS idx_executions_status ON research_executions(status);
CREATE INDEX IF NOT EXISTS idx_executions_started ON research_executions(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_executions_experiment ON research_executions(experiment_id);

-- Feature Scorecards (MODIFIED - add experiment_id)
CREATE TABLE IF NOT EXISTS feature_scorecards (
    id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    data TEXT NOT NULL CHECK(json_valid(data)),
    created_at TEXT NOT NULL,
    updated_at TEXT,
    FOREIGN KEY (experiment_id) REFERENCES experiments(id)
);

CREATE INDEX IF NOT EXISTS idx_scorecards_created ON feature_scorecards(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scorecards_experiment ON feature_scorecards(experiment_id);
```

---

## Validações de Negócio

### Experiment
- `name`: obrigatório, máximo 100 caracteres
- `hypothesis`: obrigatório, máximo 500 caracteres
- `description`: opcional, máximo 2000 caracteres
- Nomes duplicados são permitidos

### SynthGroup
- `name`: obrigatório
- Grupos são imutáveis após criação
- Synths não podem mudar de grupo

### Vinculações
- Toda simulação (via scorecard) DEVE ter experiment_id
- Toda entrevista DEVE ter experiment_id
- Todo synth DEVE ter synth_group_id

---

## Queries Comuns

### Listar experimentos com contadores
```sql
SELECT
    e.id,
    e.name,
    e.hypothesis,
    e.description,
    e.created_at,
    e.updated_at,
    (SELECT COUNT(*) FROM feature_scorecards WHERE experiment_id = e.id) as simulation_count,
    (SELECT COUNT(*) FROM research_executions WHERE experiment_id = e.id) as interview_count
FROM experiments e
ORDER BY e.created_at DESC
LIMIT ? OFFSET ?;
```

### Detalhe do experimento com simulações e entrevistas
```sql
-- Experimento
SELECT * FROM experiments WHERE id = ?;

-- Simulações (via scorecards)
SELECT
    sr.id,
    sr.scenario_id,
    sr.status,
    sr.started_at,
    sr.completed_at,
    sr.aggregated_outcomes
FROM simulation_runs sr
JOIN feature_scorecards fs ON sr.scorecard_id = fs.id
WHERE fs.experiment_id = ?
ORDER BY sr.started_at DESC;

-- Entrevistas
SELECT
    exec_id,
    topic_name,
    status,
    synth_count,
    started_at,
    completed_at,
    summary_content IS NOT NULL as has_summary
FROM research_executions
WHERE experiment_id = ?
ORDER BY started_at DESC;
```

### Listar synths por grupo
```sql
SELECT s.*, sg.name as group_name
FROM synths s
JOIN synth_groups sg ON s.synth_group_id = sg.id
WHERE s.synth_group_id = ?
ORDER BY s.created_at DESC;
```

### Listar grupos com contagem de synths
```sql
SELECT
    sg.id,
    sg.name,
    sg.description,
    sg.created_at,
    COUNT(s.id) as synth_count
FROM synth_groups sg
LEFT JOIN synths s ON sg.id = s.synth_group_id
GROUP BY sg.id
ORDER BY sg.created_at DESC;
```
