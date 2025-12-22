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
│   synths    │
└─────────────┘

┌────────────────────────┐
│ research_executions    │◄──────┐
└────────────────────────┘       │
       ▲                         │
       │                         │
       ├─────────────────────────┤
       │                         │
┌──────┴────┐          ┌─────────┴────────┐
│transcripts│          │ prfaq_metadata   │
└───────────┘          └──────────────────┘

┌───────────────────┐
│ topic_guides_cache│
└───────────────────┘
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

### 2. research_executions

Registra execuções de pesquisas (batch de entrevistas).

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

### 3. transcripts

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

### 4. prfaq_metadata

Metadados de PR-FAQ gerados.

```sql
CREATE TABLE prfaq_metadata (
    exec_id TEXT PRIMARY KEY,          -- FK para research_executions
    generated_at TEXT,                 -- ISO 8601 timestamp
    model TEXT DEFAULT 'gpt-5-mini',   -- Modelo LLM usado
    validation_status TEXT DEFAULT 'valid',
    confidence_score REAL,             -- 0.0 - 1.0
    headline TEXT,                     -- Manchete do Press Release
    one_liner TEXT,                    -- Resumo de uma linha
    faq_count INTEGER DEFAULT 0,       -- Número de perguntas no FAQ
    markdown_content TEXT,             -- Conteúdo em markdown
    json_content TEXT CHECK(json_valid(json_content) OR json_content IS NULL),
    status TEXT DEFAULT 'completed',
    error_message TEXT,
    started_at TEXT,
    CHECK(validation_status IN ('valid', 'invalid', 'pending')),
    CHECK(status IN ('generating', 'completed', 'failed'))
);

CREATE INDEX idx_prfaq_generated ON prfaq_metadata(generated_at DESC);
CREATE INDEX idx_prfaq_status ON prfaq_metadata(status);
```

---

### 5. topic_guides_cache

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

## Inicialização do Banco

### Criar Novo Banco

```python
from synth_lab.infrastructure.database import init_database

init_database()  # Cria em output/synthlab.db
```

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

Total: **7 índices** em 4 tabelas principais

**Synths**:
- `idx_synths_arquetipo` - Filtragem por arquétipo
- `idx_synths_created_at` - Ordenação por data
- `idx_synths_nome` - Busca por nome

**Executions**:
- `idx_executions_topic` - Filtragem por topic
- `idx_executions_status` - Filtragem por status
- `idx_executions_started` - Ordenação por data

**Transcripts**:
- `idx_transcripts_exec` - JOIN com executions
- `idx_transcripts_synth` - JOIN com synths

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
-- Vacuum para recuperar espaço
VACUUM;

-- Atualizar estatísticas para query planner
ANALYZE;
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
- **Validação**: `json_valid()` valida sintaxe, não schema
