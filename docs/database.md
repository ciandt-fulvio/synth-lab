# Banco de Dados - synth-lab

## Visão Geral

PostgreSQL 14+ com SQLAlchemy 2.0+ ORM. Migrações via Alembic. Connection pooling gerenciado pelo SQLAlchemy.

```bash
DATABASE_URL="postgresql://synthlab:synthlab@localhost:5432/synthlab"
```

## Diagrama de Relacionamento

```
synths (standalone)

experiments ──< research_executions ──< transcripts
    │
    ├──1 interview_guide
    ├──< experiment_documents
    ├──< experiment_materials
    ├──<> tags (via experiment_tags)
    ├──1 causal_models ──< causal_edges
    ├──< simulation_batches ──< simulation_runs
    ├──< analysis_interpretations
    └──< simulation_reports

synth_groups ──< synths (via group_id)
```

## Tabelas

### synths

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | TEXT PK | 6 caracteres (ex: "ynnasw") |
| nome | TEXT NOT NULL | Nome completo |
| arquetipo | TEXT | Ex: "Jovem Adulto Sudeste" |
| descricao | TEXT | Descrição resumida |
| avatar_path | TEXT | Path para avatar local (PNG) |
| created_at | TEXT NOT NULL | ISO 8601 |
| data | JSONB | Demografia, psicografia, deficiências, capacidades tecnológicas |

Índices: `arquetipo`, `created_at DESC`, `nome`

### experiments

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | VARCHAR(50) PK | UUID-style (ex: "exp_12345678") |
| name | VARCHAR(100) NOT NULL | Nome do experimento |
| hypothesis | VARCHAR(500) NOT NULL | Hipótese de pesquisa |
| description | TEXT | Descrição detalhada |
| scorecard_data | JSONB | Configuração do scorecard |
| status | VARCHAR(20) DEFAULT 'active' | 'active' ou 'deleted' (soft delete) |
| created_at | VARCHAR(50) NOT NULL | ISO 8601 |
| updated_at | VARCHAR(50) | ISO 8601 |

Índices: `created_at DESC`, `name`, `status`

Relacionamentos: `interview_guide` (1:1), `research_executions` (1:N), `experiment_documents` (1:N), `experiment_materials` (1:N), `tags` (M:N via experiment_tags)

### interview_guide

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| experiment_id | VARCHAR(50) PK/FK | → experiments(id) ON DELETE CASCADE |
| context_definition | TEXT | Contexto da entrevista |
| questions | TEXT | Perguntas |
| context_examples | TEXT | Exemplos |
| created_at | VARCHAR(50) NOT NULL | ISO 8601 |

### research_executions

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| exec_id | VARCHAR(100) PK | Ex: "batch_compra-amazon_20251219_110534" |
| experiment_id | VARCHAR(50) FK | → experiments(id) SET NULL on delete |
| topic_name | VARCHAR(200) NOT NULL | Nome do topic guide |
| status | VARCHAR(50) NOT NULL | pending/running/generating_summary/completed/failed |
| synth_count | INTEGER NOT NULL | Total de synths |
| successful_count | INTEGER | Entrevistas OK |
| failed_count | INTEGER | Entrevistas falhas |
| model | VARCHAR(50) | Modelo LLM usado |
| max_turns | INTEGER | Máximo de turnos por entrevista |
| additional_context | TEXT | Contexto adicional passado à entrevista |
| synth_selection_type | VARCHAR(50) | Estratégia de seleção: random/propensos/resistentes/indecisos/sensiveis |
| started_at | VARCHAR(50) NOT NULL | ISO 8601 |
| completed_at | VARCHAR(50) | ISO 8601 |

Índices: `topic_name`, `status`, `started_at`, `experiment_id`

### transcripts

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | SERIAL PK | Auto-increment |
| exec_id | TEXT FK | → research_executions |
| synth_id | TEXT FK | → synths |
| synth_name | TEXT | Cache do nome |
| messages | JSONB | Array de {turn_number, speaker, text} |
| turn_count | INTEGER | Turnos |
| UNIQUE | | (exec_id, synth_id) |

### tags + experiment_tags

**tags**: `id` (VARCHAR PK), `name` (VARCHAR UNIQUE), `created_at`

**experiment_tags** (junction M:N): `experiment_id` FK, `tag_id` FK, `created_at`. PK composta. ON DELETE CASCADE.

### experiment_materials

Materiais de experimentos (imagens, vídeos, documentos) com upload S3, thumbnails e descrições via IA.

### experiment_documents

Documentos gerados (summaries, PR-FAQs) vinculados a experimentos.

### causal_models + causal_edges

Modelo causal DAG de um experimento. `causal_models` armazena nós (fatores) com tipos enriquecidos; `causal_edges` armazena as arestas direcionadas com pesos/força.

### simulation_batches + simulation_runs

`simulation_batches`: batch de cenários gerados automaticamente para um experimento. `simulation_runs`: resultado individual de cada synth × cenário, com taxa de adoção e outcomes JSONB.

### analysis_interpretations

Interpretações geradas por LLM dos resultados de simulação (summary narrativo).

### simulation_reports

Relatório analítico gerado por LLM ao fim de cada batch, com drivers de adoção, incertezas críticas e agenda de entrevistas. 1 relatório por batch.

## ORM Models

```
models/orm/
├── base.py             # Base, JSONVariant, mixins
├── experiment.py       # Experiment, InterviewGuide
├── synth.py            # Synth, SynthGroup
├── research.py         # ResearchExecution, Transcript
├── document.py         # ExperimentDocument
├── material.py         # ExperimentMaterial
├── tag.py              # Tag, ExperimentTag
├── causal_model.py     # CausalModel, CausalEdge
├── simulation_run.py   # SimulationBatch, SimulationRun, AnalysisInterpretation, SimulationReport
├── user.py             # User
└── share.py            # ExperimentShare, SynthGroupShare
```

## Migrações

```bash
make db-migrate MSG="add column"  # Criar e aplicar nova migração
```

Migrações ficam em `src/synth_lab/infrastructure/migrations/versions/`.

Testes usam container isolado (`make test`) que aplica migrações automaticamente.

## Ambientes

| Ambiente | Porta | Volume | Persistência |
|----------|-------|--------|--------------|
| Dev | 5432 | `synthlab-postgres-dev-data` | Persistente (NÃO apagar) |
| Test | 5433 | Efêmero | Limpo a cada execução |
| Staging | Railway | Railway Volume | Persistente |
| Production | Railway | Railway Volume | Persistente |
