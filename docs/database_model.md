# Modelo de Banco de Dados - synth-lab

## Visão Geral

O synth-lab utiliza **SQLite 3.38+** com a extensão **JSON1** para armazenar dados estruturados e semi-estruturados. O banco de dados está localizado em `output/synthlab.db`.

### Configurações do Banco

```sql
PRAGMA journal_mode=WAL;        -- Permite leituras concorrentes
PRAGMA foreign_keys=ON;         -- Enforça integridade referencial
PRAGMA synchronous=NORMAL;      -- Balanceia segurança e performance
PRAGMA temp_store=MEMORY;       -- Usa memória para tabelas temporárias
```

### Características

- **WAL Mode**: Permite múltiplas leituras simultâneas
- **Foreign Keys**: Garantem integridade referencial entre tabelas
- **JSON1 Extension**: Suporta queries em campos JSON aninhados
- **Row Factory**: Retorna rows como objetos dict-like
- **Thread-safe**: Conexões thread-local via `threading.local()`

## Esquema Completo

### Diagrama de Relacionamento

```
┌─────────────┐
│   synths    │◄──────┐
└─────────────┘       │
       ▲              │
       │              │
       │              │
┌──────┴──────────┐   │
│ synth_avatars   │   │
└─────────────────┘   │
                      │
┌─────────────────┐   │
│ topic_guides    │   │
└─────────────────┘   │
       ▲              │
       │              │
┌──────┴──────────────┐
│topic_guide_files    │
└─────────────────────┘

┌────────────────────────┐
│ research_executions    │◄──────┐
└────────────────────────┘       │
       ▲                         │
       │                         │
       ├───────┐                 │
       │       │                 │
┌──────┴────┐  │  ┌──────────────┴───┐
│transcripts│  │  │ research_traces  │
└───────────┘  │  └──────────────────┘
               │
        ┌──────┴──────────┐
        │ research_reports│
        └─────────────────┘
               │
        ┌──────┴──────────┐
        │ prfaq_metadata  │
        └─────────────────┘

┌─────────────┐
│ async_jobs  │
└─────────────┘
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
    version TEXT DEFAULT '2.0.0',      -- Versão do schema

    -- Campos JSON
    demografia TEXT CHECK(json_valid(demografia)),
    psicografia TEXT CHECK(json_valid(psicografia)),
    deficiencias TEXT CHECK(json_valid(deficiencias)),
    capacidades_tecnologicas TEXT CHECK(json_valid(capacidades_tecnologicas))
);

CREATE INDEX idx_synths_arquetipo ON synths(arquetipo);
CREATE INDEX idx_synths_created_at ON synths(created_at DESC);
CREATE INDEX idx_synths_nome ON synths(nome);
```

#### Campos JSON

**demografia** (JSON):
```json
{
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
}
```

**psicografia** (JSON):
```json
{
  "personalidade_big_five": {
    "abertura": 78,
    "conscienciosidade": 62,
    "extroversao": 55,
    "amabilidade": 71,
    "neuroticismo": 42
  },
  "valores": ["criatividade", "autonomia", "justiça social"],
  "interesses": ["design", "arte", "tecnologia"],
  "hobbies": ["desenho", "fotografia", "videogames"],
  "estilo_vida": "Criativo e explorador",
  "inclinacao_politica": -25,
  "inclinacao_religiosa": "católico"
}
```

**deficiencias** (JSON):
```json
{
  "visual": {"tipo": "nenhuma"},
  "auditiva": {"tipo": "nenhuma"},
  "motora": {"tipo": "nenhuma", "usa_cadeira_rodas": false},
  "cognitiva": {"tipo": "nenhuma"}
}
```

**capacidades_tecnologicas** (JSON):
```json
{
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
```

#### Queries com JSON

```sql
-- Buscar synths por idade
SELECT * FROM synths WHERE json_extract(demografia, '$.idade') > 30;

-- Buscar por cidade
SELECT * FROM synths WHERE json_extract(demografia, '$.localizacao.cidade') = 'São Paulo';

-- Buscar por alfabetização digital
SELECT * FROM synths
WHERE json_extract(capacidades_tecnologicas, '$.alfabetizacao_digital') < 40;

-- Buscar por personalidade (abertura alta)
SELECT * FROM synths
WHERE json_extract(psicografia, '$.personalidade_big_five.abertura') > 70;
```

---

### 2. synth_avatars

Registra avatares gerados para synths (opcional).

```sql
CREATE TABLE synth_avatars (
    synth_id TEXT PRIMARY KEY REFERENCES synths(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,           -- ex: "output/synths/avatar/ynnasw.png"
    generated_at TEXT NOT NULL,        -- ISO 8601 timestamp
    model TEXT DEFAULT 'dall-e-3',     -- Modelo usado (OpenAI)
    prompt_hash TEXT                   -- MD5 do prompt usado
);

CREATE INDEX idx_avatars_generated_at ON synth_avatars(generated_at DESC);
```

#### Exemplo de Registro

```sql
INSERT INTO synth_avatars (synth_id, file_path, generated_at, model, prompt_hash)
VALUES (
    'ynnasw',
    'output/synths/avatar/ynnasw.png',
    '2025-12-19T10:30:00Z',
    'dall-e-3',
    'a3f7b9c2d1e4f5a6b7c8d9e0f1a2b3c4'
);
```

---

### 3. topic_guides

Metadados de topic guides (materiais de contexto para entrevistas).

```sql
CREATE TABLE topic_guides (
    name TEXT PRIMARY KEY,             -- ex: "compra-amazon"
    display_name TEXT,                 -- Nome formatado
    description TEXT,                  -- Descrição do topic
    script_path TEXT,                  -- Path para script.json
    question_count INTEGER DEFAULT 0,  -- Número de perguntas
    file_count INTEGER DEFAULT 0,      -- Número de arquivos
    created_at TEXT NOT NULL,          -- ISO 8601 timestamp
    updated_at TEXT NOT NULL           -- ISO 8601 timestamp
);

CREATE INDEX idx_topics_updated_at ON topic_guides(updated_at DESC);
```

#### Exemplo de Registro

```sql
INSERT INTO topic_guides (
    name, display_name, description, script_path, question_count, file_count,
    created_at, updated_at
)
VALUES (
    'compra-amazon',
    'Compra na Amazon',
    'Entrevista sobre experiência de compra no e-commerce Amazon',
    'data/topic_guides/compra-amazon/script.json',
    12,
    8,
    '2025-12-15T10:00:00Z',
    '2025-12-19T14:30:00Z'
);
```

---

### 4. topic_guide_files

Arquivos associados a topic guides (imagens, PDFs, documentos).

```sql
CREATE TABLE topic_guide_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_name TEXT NOT NULL REFERENCES topic_guides(name) ON DELETE CASCADE,
    filename TEXT NOT NULL,            -- Nome do arquivo
    file_path TEXT NOT NULL,           -- Path completo
    file_type TEXT,                    -- PNG, JPEG, PDF, MD, TXT
    content_hash TEXT,                 -- MD5 do conteúdo (cache)
    description TEXT,                  -- Descrição IA do arquivo
    size_bytes INTEGER,                -- Tamanho em bytes
    created_at TEXT NOT NULL           -- ISO 8601 timestamp
);

CREATE INDEX idx_topic_files_topic ON topic_guide_files(topic_name);
CREATE INDEX idx_topic_files_hash ON topic_guide_files(content_hash);
```

#### Exemplo de Registro

```sql
INSERT INTO topic_guide_files (
    topic_name, filename, file_path, file_type, content_hash,
    description, size_bytes, created_at
)
VALUES (
    'compra-amazon',
    'home-page.png',
    'data/topic_guides/compra-amazon/home-page.png',
    'PNG',
    'e4d909c290d0fb1ca068ffaddf22cbd0',
    'Página inicial da Amazon mostrando categorias de produtos...',
    245680,
    '2025-12-15T10:30:00Z'
);
```

---

### 5. research_executions

Registra execuções de pesquisas (batch de entrevistas).

```sql
CREATE TABLE research_executions (
    exec_id TEXT PRIMARY KEY,          -- ex: "batch_compra-amazon_20251219_110534"
    topic_name TEXT REFERENCES topic_guides(name),
    synth_count INTEGER NOT NULL,      -- Total de synths
    successful_count INTEGER DEFAULT 0,-- Entrevistas bem-sucedidas
    failed_count INTEGER DEFAULT 0,    -- Entrevistas falhadas
    model TEXT,                        -- ex: "gpt-5-mini"
    max_turns INTEGER,                 -- Máx. de turnos por entrevista
    status TEXT NOT NULL,              -- 'pending', 'running', 'completed', 'failed'
    started_at TEXT NOT NULL,          -- ISO 8601 timestamp
    completed_at TEXT,                 -- ISO 8601 timestamp (nullable)
    summary_path TEXT                  -- Path para summary.md (nullable)
);

CREATE INDEX idx_executions_topic ON research_executions(topic_name);
CREATE INDEX idx_executions_status ON research_executions(status);
CREATE INDEX idx_executions_started_at ON research_executions(started_at DESC);
```

#### Status Possíveis

- `pending` - Aguardando execução
- `running` - Em execução
- `completed` - Completado com sucesso
- `failed` - Falhou

#### Exemplo de Registro

```sql
INSERT INTO research_executions (
    exec_id, topic_name, synth_count, successful_count, failed_count,
    model, max_turns, status, started_at, completed_at, summary_path
)
VALUES (
    'batch_compra-amazon_20251219_110534',
    'compra-amazon',
    10,
    9,
    1,
    'gpt-5-mini',
    6,
    'completed',
    '2025-12-19T11:05:34Z',
    '2025-12-19T11:12:45Z',
    'output/reports/batch_compra-amazon_20251219_110534_summary.md'
);
```

---

### 6. transcripts

Armazena transcrições individuais de entrevistas.

```sql
CREATE TABLE transcripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exec_id TEXT NOT NULL REFERENCES research_executions(exec_id) ON DELETE CASCADE,
    synth_id TEXT NOT NULL REFERENCES synths(id),
    status TEXT NOT NULL,              -- 'completed', 'failed'
    turn_count INTEGER,                -- Número de turnos
    timestamp TEXT NOT NULL,           -- ISO 8601 timestamp
    file_path TEXT NOT NULL,           -- Path para arquivo JSON
    messages TEXT CHECK(json_valid(messages)), -- JSON array de mensagens

    UNIQUE(exec_id, synth_id)          -- Única transcrição por synth em cada exec
);

CREATE INDEX idx_transcripts_exec ON transcripts(exec_id);
CREATE INDEX idx_transcripts_synth ON transcripts(synth_id);
CREATE INDEX idx_transcripts_timestamp ON transcripts(timestamp DESC);
```

#### Campo messages (JSON)

```json
[
  {
    "turn_number": 1,
    "speaker": "Interviewer",
    "text": "Como você se sente ao fazer compras online?",
    "internal_notes": null
  },
  {
    "turn_number": 1,
    "speaker": "Interviewee",
    "text": "Eu me sinto bem confortável, uso bastante...",
    "internal_notes": "Demonstra confiança (abertura alta)"
  },
  {
    "turn_number": 2,
    "speaker": "Interviewer",
    "text": "O que você mais valoriza em um e-commerce?",
    "internal_notes": null
  }
]
```

#### Exemplo de Registro

```sql
INSERT INTO transcripts (
    exec_id, synth_id, status, turn_count, timestamp, file_path, messages
)
VALUES (
    'batch_compra-amazon_20251219_110534',
    'ynnasw',
    'completed',
    6,
    '2025-12-19T11:08:23Z',
    'output/transcripts/batch_compra-amazon_20251219_110534/ynnasw_20251219_110823.json',
    '[{"turn_number": 1, "speaker": "Interviewer", "text": "..."}, ...]'
);
```

---

### 7. research_traces

Rastreamento de execuções para debugging e análise de performance.

```sql
CREATE TABLE research_traces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exec_id TEXT NOT NULL REFERENCES research_executions(exec_id) ON DELETE CASCADE,
    synth_id TEXT REFERENCES synths(id),
    trace_id TEXT,                     -- ID de trace (opcional)
    file_path TEXT NOT NULL,           -- Path para arquivo de trace
    duration_ms INTEGER,               -- Duração em milissegundos
    start_time TEXT,                   -- ISO 8601 timestamp
    end_time TEXT                      -- ISO 8601 timestamp
);

CREATE INDEX idx_traces_exec ON research_traces(exec_id);
CREATE INDEX idx_traces_synth ON research_traces(synth_id);
```

---

### 8. research_reports

Relatórios gerados a partir de research executions (summary, PR-FAQ).

```sql
CREATE TABLE research_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exec_id TEXT NOT NULL REFERENCES research_executions(exec_id) ON DELETE CASCADE,
    report_type TEXT NOT NULL,         -- 'summary' ou 'prfaq'
    file_path_markdown TEXT,           -- Path para .md
    file_path_json TEXT,               -- Path para .json (PR-FAQ)
    file_path_pdf TEXT,                -- Path para .pdf (futuro)
    generated_at TEXT NOT NULL,        -- ISO 8601 timestamp
    validation_status TEXT,            -- 'validated', 'pending', 'failed'
    confidence_score REAL,             -- 0.0 - 1.0
    version INTEGER DEFAULT 1          -- Versão do relatório
);

CREATE INDEX idx_reports_exec ON research_reports(exec_id);
CREATE INDEX idx_reports_type ON research_reports(report_type);
CREATE INDEX idx_reports_generated_at ON research_reports(generated_at DESC);
```

#### Report Types

- `summary` - Resumo executivo da research execution
- `prfaq` - Press Release + FAQ gerado por IA

---

### 9. prfaq_metadata

Metadados específicos de PR-FAQ para listagem rápida.

```sql
CREATE TABLE prfaq_metadata (
    exec_id TEXT PRIMARY KEY REFERENCES research_executions(exec_id) ON DELETE CASCADE,
    headline TEXT,                     -- Manchete do Press Release
    one_liner TEXT,                    -- Resumo de uma linha
    faq_count INTEGER,                 -- Número de perguntas no FAQ
    confidence_score REAL,             -- 0.0 - 1.0
    validation_status TEXT,            -- 'validated', 'pending', 'failed'
    model TEXT,                        -- Modelo LLM usado
    generated_at TEXT NOT NULL,        -- ISO 8601 timestamp
    markdown_path TEXT,                -- Path para .md
    json_path TEXT                     -- Path para .json
);

CREATE INDEX idx_prfaq_generated_at ON prfaq_metadata(generated_at DESC);
CREATE INDEX idx_prfaq_validation ON prfaq_metadata(validation_status);
```

#### Exemplo de Registro

```sql
INSERT INTO prfaq_metadata (
    exec_id, headline, one_liner, faq_count, confidence_score,
    validation_status, model, generated_at, markdown_path, json_path
)
VALUES (
    'batch_compra-amazon_20251219_110534',
    'Amazon lança novo sistema de recomendações personalizadas',
    'Usuários agora recebem sugestões baseadas em preferências individuais',
    12,
    0.87,
    'validated',
    'gpt-5-mini',
    '2025-12-19T11:20:00Z',
    'output/reports/batch_compra-amazon_20251219_110534_prfaq.md',
    'output/reports/batch_compra-amazon_20251219_110534_prfaq.json'
);
```

---

### 10. async_jobs

Rastreamento de jobs assíncronos (summary, PR-FAQ).

```sql
CREATE TABLE async_jobs (
    job_id TEXT PRIMARY KEY,           -- UUID v4
    job_type TEXT NOT NULL,            -- 'generate_summary', 'generate_prfaq'
    exec_id TEXT REFERENCES research_executions(exec_id),
    status TEXT NOT NULL,              -- 'pending', 'running', 'completed', 'failed'
    created_at TEXT NOT NULL,          -- ISO 8601 timestamp
    started_at TEXT,                   -- ISO 8601 timestamp (nullable)
    completed_at TEXT,                 -- ISO 8601 timestamp (nullable)
    error_message TEXT,                -- Mensagem de erro (nullable)
    result_data TEXT                   -- JSON com resultado (nullable)
);

CREATE INDEX idx_jobs_status ON async_jobs(status);
CREATE INDEX idx_jobs_type ON async_jobs(job_type);
CREATE INDEX idx_jobs_exec ON async_jobs(exec_id);
CREATE INDEX idx_jobs_created_at ON async_jobs(created_at DESC);
```

#### Job Types

- `generate_summary` - Gerar resumo executivo
- `generate_prfaq` - Gerar PR-FAQ

#### Status Possíveis

- `pending` - Aguardando processamento
- `running` - Em processamento
- `completed` - Completado com sucesso
- `failed` - Falhou

#### Exemplo de Registro

```sql
INSERT INTO async_jobs (
    job_id, job_type, exec_id, status, created_at, started_at, completed_at, result_data
)
VALUES (
    'f47ac10b-58cc-4372-a567-0e02b2c3d479',
    'generate_summary',
    'batch_compra-amazon_20251219_110534',
    'completed',
    '2025-12-19T11:12:50Z',
    '2025-12-19T11:12:51Z',
    '2025-12-19T11:15:23Z',
    '{"file_path": "output/reports/batch_compra-amazon_20251219_110534_summary.md"}'
);
```

---

## Relacionamentos

### Chaves Estrangeiras

```
synths
  └─> synth_avatars (synth_id)
  └─> transcripts (synth_id)
  └─> research_traces (synth_id)

topic_guides
  └─> topic_guide_files (topic_name)
  └─> research_executions (topic_name)

research_executions
  └─> transcripts (exec_id)
  └─> research_traces (exec_id)
  └─> research_reports (exec_id)
  └─> prfaq_metadata (exec_id)
  └─> async_jobs (exec_id)
```

### Cascading Deletes

- Deletar `synth` → deleta `synth_avatar` associado
- Deletar `topic_guide` → deleta `topic_guide_files` associados
- Deletar `research_execution` → deleta:
  - Todos os `transcripts`
  - Todos os `research_traces`
  - Todos os `research_reports`
  - Metadata `prfaq_metadata`
  - Jobs `async_jobs` associados

---

## Inicialização do Banco

### Script de Migração

```bash
# Executar script de migração
uv run python scripts/migrate_to_sqlite.py
```

O script:
1. Cria arquivo `output/synthlab.db`
2. Aplica schema SQL completo
3. Configura WAL mode e foreign keys
4. Cria todos os índices

### Validação

```sql
-- Verificar tabelas criadas
SELECT name FROM sqlite_master WHERE type='table';

-- Verificar índices
SELECT name, tbl_name FROM sqlite_master WHERE type='index';

-- Verificar foreign keys habilitadas
PRAGMA foreign_keys;  -- Deve retornar 1

-- Verificar modo WAL
PRAGMA journal_mode;  -- Deve retornar 'wal'
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
        WHEN json_extract(demografia, '$.idade') BETWEEN 18 AND 30 THEN '18-30'
        WHEN json_extract(demografia, '$.idade') BETWEEN 31 AND 45 THEN '31-45'
        WHEN json_extract(demografia, '$.idade') BETWEEN 46 AND 60 THEN '46-60'
        ELSE '60+'
    END as faixa_etaria,
    COUNT(*) as total
FROM synths
GROUP BY faixa_etaria;

-- Synths com avatares gerados
SELECT COUNT(*) as synths_com_avatar
FROM synths s
INNER JOIN synth_avatars a ON s.id = a.synth_id;
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

### Estatísticas de Jobs

```sql
-- Jobs por status
SELECT status, COUNT(*) as total
FROM async_jobs
GROUP BY status;

-- Tempo médio de processamento de jobs completados
SELECT
    job_type,
    AVG(
        (julianday(completed_at) - julianday(started_at)) * 86400
    ) as avg_duration_seconds
FROM async_jobs
WHERE status = 'completed'
GROUP BY job_type;
```

---

## Performance

### Índices Criados

Total: **17 índices** em 10 tabelas

**Synths**:
- `idx_synths_arquetipo` - Filtragem por arquétipo
- `idx_synths_created_at` - Ordenação por data
- `idx_synths_nome` - Busca por nome

**Executions**:
- `idx_executions_topic` - Filtragem por topic
- `idx_executions_status` - Filtragem por status
- `idx_executions_started_at` - Ordenação por data

**Transcripts**:
- `idx_transcripts_exec` - JOIN com executions
- `idx_transcripts_synth` - JOIN com synths
- `idx_transcripts_timestamp` - Ordenação por data

**Jobs**:
- `idx_jobs_status` - Filtragem por status
- `idx_jobs_type` - Filtragem por tipo
- `idx_jobs_exec` - JOIN com executions
- `idx_jobs_created_at` - Ordenação por data

### Otimizações

1. **WAL Mode**: Permite leituras concorrentes
2. **Row Factory**: Acesso dict-like a colunas
3. **JSON Indexes**: Criar índices em campos JSON frequentes:

```sql
-- Criar índice em idade (JSON)
CREATE INDEX idx_synths_idade
ON synths(json_extract(demografia, '$.idade'));

-- Criar índice em cidade (JSON)
CREATE INDEX idx_synths_cidade
ON synths(json_extract(demografia, '$.localizacao.cidade'));
```

4. **ANALYZE**: Atualizar estatísticas para query planner

```sql
ANALYZE;
```

---

## Backup e Manutenção

### Backup Manual

```bash
# Backup completo
cp output/synthlab.db output/synthlab_backup_$(date +%Y%m%d).db

# Backup com checkpoint WAL
sqlite3 output/synthlab.db "PRAGMA wal_checkpoint(FULL);"
cp output/synthlab.db output/synthlab_backup.db
```

### Verificação de Integridade

```sql
-- Verificar integridade
PRAGMA integrity_check;

-- Verificar foreign keys
PRAGMA foreign_key_check;
```

### Limpeza

```sql
-- Remover jobs completados antigos (> 30 dias)
DELETE FROM async_jobs
WHERE status IN ('completed', 'failed')
AND datetime(completed_at) < datetime('now', '-30 days');

-- Vacuum para recuperar espaço
VACUUM;
```

---

## Limitações

### SQLite

- **Writes concorrentes**: WAL mode permite apenas 1 writer por vez
- **Tamanho máximo**: ~281 TB (praticamente ilimitado para nosso uso)
- **Concorrência**: Ideal para até ~100k writes/segundo

### JSON1

- **Performance**: Queries em JSON são mais lentas que colunas nativas
- **Índices**: Criar índices explícitos em campos JSON frequentes
- **Validação**: JSON_CHECK valida sintaxe, não schema

### Escalabilidade

- **Atual**: ~10k synths, ~1k executions
- **Futuro**: Migrar para PostgreSQL quando:
  - Synths > 100k
  - Executions > 10k
  - Writes concorrentes > 10/s

---

## Migração Futura

### Para PostgreSQL

```sql
-- Schema equivalente em PostgreSQL
CREATE TABLE synths (
    id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    ...
    demografia JSONB,  -- JSONB para queries rápidas
    psicografia JSONB,
    ...
);

-- Índices em campos JSON (GIN)
CREATE INDEX idx_synths_demografia_gin ON synths USING GIN (demografia);
```

**Benefícios**:
- Writes concorrentes ilimitados
- JSONB indexes (GIN) muito rápidos
- Replicação e high availability
- Full-text search nativo

**Compatibilidade**: Repositories abstraem DB, migração transparente para services.
