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
    └──<> tags (via experiment_tags)

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
| exec_id | TEXT PK | Ex: "batch_compra-amazon_20251219_110534" |
| experiment_id | VARCHAR(50) FK | → experiments(id) (opcional) |
| topic_name | TEXT NOT NULL | Nome do topic guide |
| status | TEXT NOT NULL | pending/running/generating_summary/completed/failed |
| synth_count | INTEGER NOT NULL | Total de synths |
| successful_count | INTEGER | Entrevistas OK |
| failed_count | INTEGER | Entrevistas falhas |
| model | TEXT | Modelo LLM usado |
| summary_content | TEXT | Summary em markdown |
| started_at | TEXT NOT NULL | ISO 8601 |
| completed_at | TEXT | ISO 8601 |

Índices: `topic_name`, `status`, `started_at DESC`

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

## ORM Models

```
models/orm/
├── base.py          # Base, JSONVariant, mixins
├── experiment.py    # Experiment, InterviewGuide
├── synth.py         # Synth, SynthGroup
├── research.py      # ResearchExecution, Transcript
├── document.py      # ExperimentDocument
└── share.py         # ExperimentShare, SynthGroupShare
```

## Migrações

```bash
make alembic-upgrade                    # Aplicar migrações
make alembic-downgrade                  # Rollback
make alembic-revision MSG="add column"  # Nova migração
```

Testes usam container isolado (`make test`) que aplica migrações automaticamente.

## Ambientes

| Ambiente | Porta | Volume | Persistência |
|----------|-------|--------|--------------|
| Dev | 5432 | `synthlab-postgres-dev-data` | Persistente (NÃO apagar) |
| Test | 5433 | Efêmero | Limpo a cada execução |
| Staging | Railway | Railway Volume | Persistente |
| Production | Railway | Railway Volume | Persistente |
