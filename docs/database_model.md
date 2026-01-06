# Modelo de Banco de Dados - synth-lab

## Visão Geral

O synth-lab utiliza **PostgreSQL 14+** com **SQLAlchemy 2.0+** ORM para armazenar dados estruturados e semi-estruturados. A conexão com o banco de dados é configurada via variável de ambiente `DATABASE_URL`.

### Configurações do Banco

```python
# Connection pooling
pool_size = WORKERS * 2  # Número de conexões persistentes
max_overflow = 10        # Conexões adicionais temporárias

# SQLAlchemy settings
echo = SQL_ECHO          # Log SQL queries (debug only)
```

### Características

- **Connection Pooling**: Pool de conexões gerenciado pelo SQLAlchemy
- **Foreign Keys**: Garantem integridade referencial entre tabelas
- **JSONB Type**: Suporta queries eficientes em campos JSON aninhados
- **ORM Models**: Modelos Pydantic + SQLAlchemy para validação e persistência
- **Thread-safe**: Pool gerencia conexões de forma thread-safe
- **Alembic Migrations**: Versionamento e migração de schema

## Esquema Completo

### Diagrama de Relacionamento

```
┌─────────────┐
│   synths    │
└─────────────┘

┌─────────────────┐       ┌────────────────────────┐
│   experiments   │◄──────│ research_executions    │
└─────────────────┘       └────────────────────────┘
       │                           ▲
       │                           │
       ├──────────────────┐        │
       │                  │  ┌─────┴─────┐
       │                  │  │transcripts│
       ▼                  │  └───────────┘
┌─────────────────┐       │
│ interview_guide │       │
└─────────────────┘       │
                          │
       ├──────────────────┤
       ▼                  ▼
┌─────────────────────┐  ┌──────────────────────┐
│ experiment_documents│  │ experiment_materials │
└─────────────────────┘  └──────────────────────┘

┌───────────────────┐    ┌──────────────────────┐
│ topic_guides_cache│    │    experiment_tags   │ (M:N junction)
└───────────────────┘    └──────────────────────┘
                                  │
                                  ▼
                         ┌───────────────┐
                         │     tags      │
                         └───────────────┘
```

## Tabelas

### 1. synths

Armazena personas sintéticas com atributos demográficos, psicográficos e comportamentais.

```sql
CREATE TABLE synths (
    id TEXT PRIMARY KEY,                -- 6 caracteres (ex: "ynnasw")
    nome TEXT NOT NULL,                 -- Nome completo
    arquetipo TEXT,                     -- Arquétipo (ex: "Jovem Adulto Sudeste")
    descricao TEXT,                     -- Descrição resumida
    link_photo TEXT,                    -- URL do avatar online
    avatar_path TEXT,                   -- Path para avatar local (PNG)
    created_at TEXT NOT NULL,           -- ISO 8601 timestamp
    version TEXT DEFAULT '2.0.0',       -- Versão do schema
    data TEXT CHECK(json_valid(data) OR data IS NULL)  -- Todos os dados aninhados
);

CREATE INDEX idx_synths_arquetipo ON synths(arquetipo);
CREATE INDEX idx_synths_created_at ON synths(created_at DESC);
CREATE INDEX idx_synths_nome ON synths(nome);
```

#### Campo `data` (JSON)

O campo `data` contém todos os dados aninhados do synth em um único JSON:

```json
{
  "demografia": {
    "idade": 28,
    "genero_biologico": "feminino",
    "identidade_genero": "mulher cis",
    "raca_etnia": "parda",
    "localizacao": {
      "pais": "Brasil",
      "regiao": "Sudeste",
      "estado": "SP",
      "cidade": "São Paulo"
    },
    "escolaridade": "Superior completo",
    "renda_mensal": 4500.00,
    "ocupacao": "Designer gráfico",
    "estado_civil": "solteiro",
    "composicao_familiar": {
      "tipo": "unipessoal",
      "numero_pessoas": 1
    }
  },
  "psicografia": {
    "personalidade_big_five": {
      "abertura": 78,
      "conscienciosidade": 62,
      "extroversao": 55,
      "amabilidade": 71,
      "neuroticismo": 42
    },
    "interesses": ["design", "arte", "tecnologia"],
    "inclinacao_politica": -25,
    "inclinacao_religiosa": "católico"
  },
  "deficiencias": {
    "visual": {"tipo": "nenhuma"},
    "auditiva": {"tipo": "nenhuma"},
    "motora": {"tipo": "nenhuma", "usa_cadeira_rodas": false},
    "cognitiva": {"tipo": "nenhuma"}
  },
  "capacidades_tecnologicas": {
    "alfabetizacao_digital": 85,
    "dispositivos": {
      "principal": "computador",
      "qualidade": "novo"
    },
    "preferencias_acessibilidade": {
      "zoom_fonte": 100,
      "alto_contraste": false
    },
    "velocidade_digitacao": 70,
    "frequencia_internet": "diária",
    "familiaridade_plataformas": {
      "e_commerce": 90,
      "banco_digital": 85,
      "redes_sociais": 95
    }
  }
}
```

#### Queries com JSON

```sql
-- Buscar synths por idade
SELECT * FROM synths WHERE json_extract(data, '$.demografia.idade') > 30;

-- Buscar por cidade
SELECT * FROM synths WHERE json_extract(data, '$.demografia.localizacao.cidade') = 'São Paulo';

-- Buscar por alfabetização digital baixa
SELECT * FROM synths
WHERE json_extract(data, '$.capacidades_tecnologicas.alfabetizacao_digital') < 40;

-- Buscar por personalidade (abertura alta)
SELECT * FROM synths
WHERE json_extract(data, '$.psicografia.personalidade_big_five.abertura') > 70;

-- Buscar por região
SELECT * FROM synths
WHERE json_extract(data, '$.demografia.localizacao.regiao') = 'Nordeste';
```

---

### 2. experiments

Armazena experimentos de pesquisa com hipóteses e configuração de scorecard.

```sql
CREATE TABLE experiments (
    id VARCHAR(50) PRIMARY KEY,           -- UUID-style identifier (ex: "exp_12345678")
    name VARCHAR(100) NOT NULL,           -- Nome do experimento (max 100 chars)
    hypothesis VARCHAR(500) NOT NULL,     -- Hipótese de pesquisa (max 500 chars)
    description TEXT,                     -- Descrição detalhada opcional (max 2000 chars)
    scorecard_data JSONB,                 -- Configuração do scorecard como JSON
    status VARCHAR(20) NOT NULL DEFAULT 'active',  -- 'active' ou 'deleted' (soft delete)
    created_at VARCHAR(50) NOT NULL,      -- ISO 8601 timestamp
    updated_at VARCHAR(50)                -- ISO 8601 timestamp (nullable)
);

-- Índices
CREATE INDEX idx_experiments_created ON experiments(created_at DESC);
CREATE INDEX idx_experiments_name ON experiments(name);
CREATE INDEX idx_experiments_status ON experiments(status);
```

| Coluna | Tipo Python | Tipo PostgreSQL | NOT NULL | Default | Descrição |
|--------|-------------|-----------------|----------|---------|-----------|
| id | str | VARCHAR(50) | ✅ | - | Chave primária UUID-style |
| name | str | VARCHAR(100) | ✅ | - | Nome do experimento |
| hypothesis | str | VARCHAR(500) | ✅ | - | Hipótese de pesquisa |
| description | str \| None | TEXT | ❌ | NULL | Descrição detalhada |
| scorecard_data | dict[str, Any] \| None | JSONB | ❌ | NULL | Configuração do scorecard |
| status | str | VARCHAR(20) | ✅ | 'active' | Status: 'active' ou 'deleted' |
| created_at | str | VARCHAR(50) | ✅ | - | Timestamp ISO 8601 |
| updated_at | str \| None | VARCHAR(50) | ❌ | NULL | Timestamp ISO 8601 |

#### Relacionamentos

| Relação | Tipo | Tabela Relacionada | FK | Descrição |
|---------|------|-------------------|-----|-----------|
| analysis_run | 1:1 | analysis_runs | experiment_id | Run de análise associada |
| interview_guide | 1:1 | interview_guide | experiment_id | Guia de entrevista opcional |
| research_executions | 1:N | research_executions | experiment_id | Execuções de pesquisa |
| explorations | 1:N | explorations | experiment_id | Explorações de cenários |
| documents | 1:N | experiment_documents | experiment_id | Documentos (PRFAQ, Summary, etc.) |
| materials | 1:N | experiment_materials | experiment_id | Materiais (imagens, vídeos, docs) |
| experiment_tags | M:N | experiment_tags | experiment_id | Tags via tabela junction |

#### Campo scorecard_data (JSONB)

```json
{
  "dimensions": [
    {
      "name": "Relevância",
      "weight": 0.3,
      "criteria": ["Alinhamento com objetivo", "Clareza da proposta"]
    },
    {
      "name": "Viabilidade",
      "weight": 0.7,
      "criteria": ["Recursos necessários", "Complexidade técnica"]
    }
  ]
}
```

---

### 3. interview_guide

Armazena guias de entrevista para experimentos (relacionamento 1:1 com experiments).

```sql
CREATE TABLE interview_guide (
    experiment_id VARCHAR(50) PRIMARY KEY REFERENCES experiments(id) ON DELETE CASCADE,
    context_definition TEXT,              -- Definição do contexto da entrevista
    questions TEXT,                       -- Perguntas da entrevista
    context_examples TEXT,                -- Exemplos de contexto para referência
    created_at VARCHAR(50) NOT NULL,      -- ISO 8601 timestamp
    updated_at VARCHAR(50)                -- ISO 8601 timestamp (nullable)
);
```

| Coluna | Tipo Python | Tipo PostgreSQL | NOT NULL | Default | Descrição |
|--------|-------------|-----------------|----------|---------|-----------|
| experiment_id | str | VARCHAR(50) | ✅ | - | PK e FK para experiments |
| context_definition | str \| None | TEXT | ❌ | NULL | Definição do contexto |
| questions | str \| None | TEXT | ❌ | NULL | Perguntas da entrevista |
| context_examples | str \| None | TEXT | ❌ | NULL | Exemplos de contexto |
| created_at | str | VARCHAR(50) | ✅ | - | Timestamp ISO 8601 |
| updated_at | str \| None | VARCHAR(50) | ❌ | NULL | Timestamp ISO 8601 |

#### Relacionamentos

| Relação | Tipo | Tabela Relacionada | FK | Descrição |
|---------|------|-------------------|-----|-----------|
| experiment | N:1 | experiments | experiment_id | Experimento pai |

---

### 4. research_executions

Registra execuções de pesquisas (batch de entrevistas). Relaciona-se com `experiments` via `experiment_id` (FK opcional).

```sql
CREATE TABLE research_executions (
    exec_id TEXT PRIMARY KEY,          -- ex: "batch_compra-amazon_20251219_110534"
    topic_name TEXT NOT NULL,          -- Nome do topic guide
    status TEXT NOT NULL DEFAULT 'completed',
    synth_count INTEGER NOT NULL,      -- Total de synths
    successful_count INTEGER DEFAULT 0,-- Entrevistas bem-sucedidas
    failed_count INTEGER DEFAULT 0,    -- Entrevistas falhadas
    model TEXT DEFAULT 'gpt-5-mini',   -- Modelo LLM usado
    max_turns INTEGER DEFAULT 6,       -- Máx. de turnos por entrevista
    started_at TEXT NOT NULL,          -- ISO 8601 timestamp
    completed_at TEXT,                 -- ISO 8601 timestamp (nullable)
    summary_content TEXT,              -- Conteúdo do summary em markdown
    CHECK(status IN ('pending', 'running', 'generating_summary', 'completed', 'failed'))
);

CREATE INDEX idx_executions_topic ON research_executions(topic_name);
CREATE INDEX idx_executions_status ON research_executions(status);
CREATE INDEX idx_executions_started ON research_executions(started_at DESC);
```

#### Status Possíveis

- `pending` - Aguardando execução
- `running` - Em execução
- `generating_summary` - Gerando resumo
- `completed` - Completado com sucesso
- `failed` - Falhou

---

### 5. transcripts

Armazena transcrições individuais de entrevistas.

```sql
CREATE TABLE transcripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exec_id TEXT NOT NULL,             -- FK para research_executions
    synth_id TEXT NOT NULL,            -- FK para synths
    synth_name TEXT,                   -- Nome do synth (cache)
    status TEXT NOT NULL DEFAULT 'completed',
    turn_count INTEGER DEFAULT 0,      -- Número de turnos
    timestamp TEXT NOT NULL,           -- ISO 8601 timestamp
    messages TEXT CHECK(json_valid(messages) OR messages IS NULL),
    UNIQUE(exec_id, synth_id)
);

CREATE INDEX idx_transcripts_exec ON transcripts(exec_id);
CREATE INDEX idx_transcripts_synth ON transcripts(synth_id);
```

#### Campo messages (JSON)

```json
[
  {
    "turn_number": 1,
    "speaker": "Interviewer",
    "text": "Como você se sente ao fazer compras online?"
  },
  {
    "turn_number": 1,
    "speaker": "Interviewee",
    "text": "Eu me sinto bem confortável, uso bastante..."
  },
  {
    "turn_number": 2,
    "speaker": "Interviewer",
    "text": "O que você mais valoriza em um e-commerce?"
  }
]
```

---

### 6. topic_guides_cache

Cache de metadados de topic guides.

```sql
CREATE TABLE topic_guides_cache (
    name TEXT PRIMARY KEY,             -- ex: "compra-amazon"
    display_name TEXT,                 -- Nome formatado
    description TEXT,                  -- Descrição do topic
    question_count INTEGER DEFAULT 0,  -- Número de perguntas
    file_count INTEGER DEFAULT 0,      -- Número de arquivos
    script_hash TEXT,                  -- Hash do script.json
    created_at TEXT,                   -- ISO 8601 timestamp
    updated_at TEXT                    -- ISO 8601 timestamp
);
```

---

### 7. tags

Armazena tags para categorização de experimentos.

```sql
CREATE TABLE tags (
    id VARCHAR(50) PRIMARY KEY,        -- UUID-style identifier (ex: "tag_12345678")
    name VARCHAR(50) NOT NULL UNIQUE,  -- Nome da tag (max 50 chars, único)
    created_at VARCHAR(50) NOT NULL,   -- ISO 8601 timestamp
    updated_at VARCHAR(50)             -- ISO 8601 timestamp (nullable)
);

-- Índices
CREATE INDEX idx_tags_name ON tags(name);
```

| Coluna | Tipo Python | Tipo PostgreSQL | NOT NULL | Default | Descrição |
|--------|-------------|-----------------|----------|---------|-----------|
| id | str | VARCHAR(50) | ✅ | - | Chave primária UUID-style |
| name | str | VARCHAR(50) | ✅ | - | Nome da tag (único) |
| created_at | str | VARCHAR(50) | ✅ | - | Timestamp ISO 8601 |
| updated_at | str \| None | VARCHAR(50) | ❌ | NULL | Timestamp ISO 8601 |

#### Relacionamentos

| Relação | Tipo | Tabela Relacionada | FK | Descrição |
|---------|------|-------------------|-----|-----------|
| experiment_tags | 1:N | experiment_tags | tag_id | Links para experimentos via junction table |

---

### 8. experiment_tags

Tabela junction para relacionamento many-to-many entre experiments e tags.

```sql
CREATE TABLE experiment_tags (
    experiment_id VARCHAR(50) NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    tag_id VARCHAR(50) NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    created_at VARCHAR(50) NOT NULL,   -- ISO 8601 timestamp quando tag foi adicionada
    PRIMARY KEY (experiment_id, tag_id)
);

-- Índices
CREATE INDEX idx_experiment_tags_experiment ON experiment_tags(experiment_id);
CREATE INDEX idx_experiment_tags_tag ON experiment_tags(tag_id);
```

| Coluna | Tipo Python | Tipo PostgreSQL | NOT NULL | Default | Descrição |
|--------|-------------|-----------------|----------|---------|-----------|
| experiment_id | str | VARCHAR(50) | ✅ | - | FK para experiments (PK composta) |
| tag_id | str | VARCHAR(50) | ✅ | - | FK para tags (PK composta) |
| created_at | str | VARCHAR(50) | ✅ | - | Timestamp ISO 8601 |

#### Relacionamentos

| Relação | Tipo | Tabela Relacionada | FK | Descrição |
|---------|------|-------------------|-----|-----------|
| experiment | N:1 | experiments | experiment_id | Experimento pai |
| tag | N:1 | tags | tag_id | Tag associada |

#### Constraints

- **ON DELETE CASCADE**: Quando um experimento ou tag é deletado, os registros relacionados são removidos automaticamente
- **Chave primária composta**: (experiment_id, tag_id) garante unicidade do relacionamento

---

## Inicialização do Banco

### Criar Novo Banco

```python
from synth_lab.infrastructure.database import init_database

init_database()  # Cria em output/synthlab.db
```

### Validação

```sql
-- Verificar tabelas criadas
SELECT tablename FROM pg_tables WHERE schemaname = 'public';

-- Verificar índices
SELECT indexname, tablename FROM pg_indexes WHERE schemaname = 'public';

-- Verificar versão do PostgreSQL
SELECT version();

-- Verificar conexões ativas
SELECT count(*) FROM pg_stat_activity;
```

---

## Queries Úteis

### Estatísticas de Synths

```sql
-- Total de synths por arquétipo
SELECT arquetipo, COUNT(*) as total
FROM synths
GROUP BY arquetipo
ORDER BY total DESC;

-- Distribuição por faixa etária
SELECT
    CASE
        WHEN json_extract(data, '$.demografia.idade') BETWEEN 18 AND 30 THEN '18-30'
        WHEN json_extract(data, '$.demografia.idade') BETWEEN 31 AND 45 THEN '31-45'
        WHEN json_extract(data, '$.demografia.idade') BETWEEN 46 AND 60 THEN '46-60'
        ELSE '60+'
    END as faixa_etaria,
    COUNT(*) as total
FROM synths
GROUP BY faixa_etaria;

-- Distribuição por região
SELECT
    json_extract(data, '$.demografia.localizacao.regiao') as regiao,
    COUNT(*) as total
FROM synths
GROUP BY regiao
ORDER BY total DESC;
```

### Estatísticas de Research

```sql
-- Research executions por status
SELECT status, COUNT(*) as total
FROM research_executions
GROUP BY status;

-- Taxa de sucesso de entrevistas
SELECT
    exec_id,
    synth_count,
    successful_count,
    failed_count,
    ROUND(CAST(successful_count AS REAL) / synth_count * 100, 2) as taxa_sucesso
FROM research_executions
WHERE status = 'completed';

-- Topics mais pesquisados
SELECT
    topic_name,
    COUNT(*) as num_executions,
    SUM(synth_count) as total_entrevistas
FROM research_executions
GROUP BY topic_name
ORDER BY num_executions DESC;
```

---

## Performance

### Índices

Total: **13 índices** em 7 tabelas principais

**Synths**:
- `idx_synths_arquetipo` - Filtragem por arquétipo
- `idx_synths_created_at` - Ordenação por data
- `idx_synths_nome` - Busca por nome

**Experiments**:
- `idx_experiments_created` - Ordenação por data (DESC)
- `idx_experiments_name` - Busca por nome
- `idx_experiments_status` - Filtragem por status (soft delete)

**Executions**:
- `idx_executions_topic` - Filtragem por topic
- `idx_executions_status` - Filtragem por status
- `idx_executions_started` - Ordenação por data

**Transcripts**:
- `idx_transcripts_exec` - JOIN com executions
- `idx_transcripts_synth` - JOIN com synths

**Tags**:
- `idx_tags_name` - Busca por nome de tag

**Experiment Tags**:
- `idx_experiment_tags_experiment` - JOIN com experiments
- `idx_experiment_tags_tag` - JOIN com tags

### Otimizações JSON

Para queries frequentes em campos JSON, criar índices:

```sql
-- Criar índice em idade (JSON)
CREATE INDEX idx_synths_idade
ON synths(json_extract(data, '$.demografia.idade'));

-- Criar índice em região (JSON)
CREATE INDEX idx_synths_regiao
ON synths(json_extract(data, '$.demografia.localizacao.regiao'));
```

---

## Backup e Manutenção

### Backup Manual

```bash
# Backup completo do PostgreSQL
pg_dump -U synthlab -d synthlab > backup_$(date +%Y%m%d).sql

# Backup comprimido
pg_dump -U synthlab -d synthlab | gzip > backup_$(date +%Y%m%d).sql.gz

# Backup usando Docker Compose (se aplicável)
docker compose exec postgres pg_dump -U synthlab synthlab > backup.sql
```

### Verificação de Integridade

```sql
-- Verificar integridade de tabelas
SELECT pg_relation_check();

-- Verificar replicação (se aplicável)
SELECT * FROM pg_stat_replication;

-- Verificar locks
SELECT * FROM pg_locks WHERE NOT granted;
```

### Limpeza

```sql
-- Vacuum para recuperar espaço e atualizar estatísticas
VACUUM ANALYZE;

-- Vacuum completo (requer lock exclusivo)
VACUUM FULL;

-- Atualizar apenas estatísticas para query planner
ANALYZE;
```

---

## Considerações PostgreSQL

### Características

- **Writes concorrentes**: MVCC permite múltiplos writers simultâneos
- **Tamanho máximo**: ~32 TB por tabela (praticamente ilimitado para nosso uso)
- **Concorrência**: Suporta milhares de conexões simultâneas com connection pooling
- **Escalabilidade**: Suporta replicação e sharding para alta disponibilidade

### JSONB

- **Performance**: Queries em JSON são mais lentas que colunas nativas
- **Índices**: Criar índices explícitos em campos JSON frequentes
- **Validação**: `json_valid()` valida sintaxe, não schema
