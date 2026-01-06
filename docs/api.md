# API REST - synth-lab

## Visão Geral

A API REST do synth-lab é construída com **FastAPI** e oferece acesso programático a todas as funcionalidades do sistema através de **37 endpoints HTTP**.

### Características

- **Framework**: FastAPI 0.109+
- **Documentação**: Swagger UI automático em `/docs`
- **Validação**: Pydantic models para request/response
- **Streaming**: Server-Sent Events (SSE) para research executions
- **Paginação**: Suporte a limit/offset em todos os endpoints de listagem
- **CORS**: Configurado para desenvolvimento web
- **Formato**: JSON para todas as respostas (exceto arquivos)

### URL Base

```
http://localhost:8000
```

### Documentação Interativa

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## Iniciar o Servidor

### Desenvolvimento

```bash
# Via script
./scripts/start_api.sh

# Ou manualmente
uv run uvicorn src.synth_lab.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Produção

```bash
uv run uvicorn src.synth_lab.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## Estrutura de Resposta

### Respostas de Sucesso

```json
{
  "data": [...],
  "pagination": {
    "total": 100,
    "limit": 50,
    "offset": 0,
    "has_next": true
  }
}
```

### Respostas de Erro

```json
{
  "error": {
    "code": "SYNTH_NOT_FOUND",
    "message": "Synth com ID 'abc123' não encontrado",
    "details": {
      "synth_id": "abc123"
    }
  }
}
```

---

## Paginação Padrão

Todos os endpoints de listagem suportam paginação:

```
GET /endpoint?limit=50&offset=0&sort_by=created_at&sort_order=desc
```

### Parâmetros

| Parâmetro | Tipo | Padrão | Min | Max | Descrição |
|-----------|------|--------|-----|-----|-----------|
| `limit` | int | 50 | 1 | 200 | Itens por página |
| `offset` | int | 0 | 0 | - | Número de itens a pular |
| `sort_by` | string | - | - | - | Campo para ordenação |
| `sort_order` | string | asc | - | - | Ordem: `asc` ou `desc` |

### Resposta de Paginação

```json
{
  "pagination": {
    "total": 150,        // Total de itens disponíveis
    "limit": 50,         // Itens por página
    "offset": 0,         // Offset atual
    "has_next": true     // Indica se há próxima página
  }
}
```

---

## Endpoints

### 1. Synths Endpoints (5 endpoints)

#### 1.1 Listar Synths

```http
GET /synths/list
```

Lista synths com paginação e filtros opcionais.

**Query Parameters**:
- `limit` (int, opcional): Padrão 50, máx 200
- `offset` (int, opcional): Padrão 0
- `sort_by` (string, opcional): Campo para ordenação (`created_at`, `nome`, `arquetipo`)
- `sort_order` (string, opcional): `asc` ou `desc`
- `fields` (string, opcional): Campos a incluir separados por vírgula

**Response 200**:
```json
{
  "data": [
    {
      "id": "ynnasw",
      "nome": "Ravy Lopes",
      "arquetipo": "Jovem Adulto Sudeste",
      "descricao": "Homem de 32 anos, desenvolvedor...",
      "created_at": "2025-12-19T10:30:00Z",
      "avatar_url": "/synths/ynnasw/avatar"
    }
  ],
  "pagination": {
    "total": 150,
    "limit": 50,
    "offset": 0,
    "has_next": true
  }
}
```

**Exemplo**:
```bash
curl "http://localhost:8000/synths/list?limit=10&sort_by=created_at&sort_order=desc"
```

---

#### 1.2 Obter Synth por ID

```http
GET /synths/{synth_id}
```

Retorna detalhes completos de um synth específico.

**Path Parameters**:
- `synth_id` (string, requerido): ID do synth (6 caracteres)

**Response 200**:
```json
{
  "id": "ynnasw",
  "nome": "Ravy Lopes",
  "arquetipo": "Jovem Adulto Sudeste",
  "descricao": "Homem de 32 anos, desenvolvedor de software...",
  "link_photo": "https://ui-avatars.com/api/?name=Ravy+Lopes",
  "avatar_path": "output/synths/avatar/ynnasw.png",
  "created_at": "2025-12-19T10:30:00Z",
  "version": "2.0.0",
  "demografia": {
    "idade": 32,
    "genero_biologico": "masculino",
    "identidade_genero": "homem cis",
    "raca_etnia": "branco",
    "localizacao": {
      "pais": "Brasil",
      "regiao": "Sudeste",
      "estado": "SP",
      "cidade": "São Paulo"
    },
    "escolaridade": "Superior completo",
    "renda_mensal": 8500.00,
    "ocupacao": "Desenvolvedor de software",
    "estado_civil": "casado",
    "composicao_familiar": {
      "tipo": "casal sem filhos",
      "numero_pessoas": 2
    }
  },
  "psicografia": {
    "personalidade_big_five": {
      "abertura": 82,
      "conscienciosidade": 75,
      "extroversao": 48,
      "amabilidade": 65,
      "neuroticismo": 35
    },
    "valores": ["autonomia", "inovação", "crescimento pessoal"],
    "interesses": ["tecnologia", "ciência", "games", "música"],
    "hobbies": ["programação", "videogames", "violão"],
    "estilo_vida": "Analítico e introvertido",
    "inclinacao_politica": -15,
    "inclinacao_religiosa": "agnóstico"
  },
  "deficiencias": {
    "visual": {"tipo": "nenhuma"},
    "auditiva": {"tipo": "nenhuma"},
    "motora": {"tipo": "nenhuma", "usa_cadeira_rodas": false},
    "cognitiva": {"tipo": "nenhuma"}
  },
  "capacidades_tecnologicas": {
    "alfabetizacao_digital": 95,
    "dispositivos": {
      "principal": "computador",
      "qualidade": "novo"
    },
    "preferencias_acessibilidade": {
      "zoom_fonte": 100,
      "alto_contraste": false
    },
    "velocidade_digitacao": 85,
    "frequencia_internet": "diária",
    "familiaridade_plataformas": {
      "e_commerce": 95,
      "banco_digital": 98,
      "redes_sociais": 70
    }
  }
}
```

**Response 404**:
```json
{
  "error": {
    "code": "SYNTH_NOT_FOUND",
    "message": "Synth com ID 'abc123' não encontrado"
  }
}
```

**Exemplo**:
```bash
curl "http://localhost:8000/synths/ynnasw"
```

---

#### 1.3 Buscar Synths (Avançado)

```http
POST /synths/search
```

Busca avançada com SQL WHERE clause ou query completa.

**Request Body**:
```json
{
  "where_clause": "json_extract(demografia, '$.idade') > 30 AND json_extract(demografia, '$.localizacao.regiao') = 'Sudeste'",
  "limit": 50,
  "offset": 0
}
```

Ou com query SQL completa:

```json
{
  "query": "SELECT id, nome, json_extract(demografia, '$.idade') as idade FROM synths WHERE idade > 30 ORDER BY idade DESC",
  "limit": 50,
  "offset": 0
}
```

**Response 200**:
```json
{
  "data": [
    {
      "id": "ynnasw",
      "nome": "Ravy Lopes",
      "arquetipo": "Jovem Adulto Sudeste",
      ...
    }
  ],
  "pagination": {
    "total": 42,
    "limit": 50,
    "offset": 0,
    "has_next": false
  }
}
```

**Response 422** (Query inválida):
```json
{
  "error": {
    "code": "INVALID_QUERY",
    "message": "Query SQL contém comandos não permitidos: UPDATE",
    "details": {
      "blocked_keywords": ["UPDATE", "DELETE", "DROP"]
    }
  }
}
```

**Segurança**:
- Apenas comandos SELECT permitidos
- Keywords bloqueadas: INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, etc.
- Timeout de 5 segundos para queries

**Exemplo**:
```bash
curl -X POST "http://localhost:8000/synths/search" \
  -H "Content-Type: application/json" \
  -d '{
    "where_clause": "json_extract(demografia, '\''$.idade'\'') BETWEEN 25 AND 35",
    "limit": 20
  }'
```

---

#### 1.4 Download de Avatar

```http
GET /synths/{synth_id}/avatar
```

Faz download do avatar do synth em formato PNG.

**Path Parameters**:
- `synth_id` (string, requerido): ID do synth

**Response 200**:
- Content-Type: `image/png`
- Body: Arquivo PNG (341x341 pixels)

**Response 404**:
```json
{
  "error": {
    "code": "AVATAR_NOT_FOUND",
    "message": "Avatar não encontrado para synth 'ynnasw'"
  }
}
```

**Exemplo**:
```bash
# Download direto
curl "http://localhost:8000/synths/ynnasw/avatar" -o avatar.png

# Exibir em navegador
open "http://localhost:8000/synths/ynnasw/avatar"
```

---

#### 1.5 Listar Campos Disponíveis

```http
GET /synths/fields
```

Retorna lista de campos disponíveis para filtros e ordenação.

**Response 200**:
```json
{
  "fields": [
    {
      "name": "id",
      "type": "string",
      "description": "ID único do synth",
      "sortable": true,
      "filterable": true
    },
    {
      "name": "nome",
      "type": "string",
      "description": "Nome completo",
      "sortable": true,
      "filterable": true
    },
    {
      "name": "demografia.idade",
      "type": "integer",
      "description": "Idade do synth",
      "sortable": true,
      "filterable": true,
      "json_path": "$.idade"
    },
    {
      "name": "demografia.localizacao.cidade",
      "type": "string",
      "description": "Cidade de residência",
      "sortable": false,
      "filterable": true,
      "json_path": "$.localizacao.cidade"
    }
  ]
}
```

**Exemplo**:
```bash
curl "http://localhost:8000/synths/fields"
```

---

### 2. Topics Endpoints (3 endpoints)

#### 2.1 Listar Topic Guides

```http
GET /topics/list
```

Lista topic guides com paginação.

**Query Parameters**:
- `limit` (int, opcional): Padrão 50
- `offset` (int, opcional): Padrão 0
- `sort_by` (string, opcional): `updated_at`, `created_at`, `name`
- `sort_order` (string, opcional): `asc` ou `desc`

**Response 200**:
```json
{
  "data": [
    {
      "name": "compra-amazon",
      "display_name": "Compra na Amazon",
      "description": "Entrevista sobre experiência de compra...",
      "question_count": 12,
      "file_count": 8,
      "created_at": "2025-12-15T10:00:00Z",
      "updated_at": "2025-12-19T14:30:00Z"
    }
  ],
  "pagination": {
    "total": 5,
    "limit": 50,
    "offset": 0,
    "has_next": false
  }
}
```

**Exemplo**:
```bash
curl "http://localhost:8000/topics/list"
```

---

#### 2.2 Obter Topic Guide por Nome

```http
GET /topics/{topic_name}
```

Retorna detalhes completos de um topic guide.

**Path Parameters**:
- `topic_name` (string, requerido): Nome do topic guide

**Response 200**:
```json
{
  "name": "compra-amazon",
  "display_name": "Compra na Amazon",
  "description": "Entrevista sobre experiência de compra no e-commerce Amazon",
  "script": [
    {
      "id": "q1",
      "ask": "Como você se sente ao fazer compras online?",
      "context_examples": ["Explore sentimentos, medos, preferências"]
    },
    {
      "id": "q2",
      "ask": "O que você mais valoriza em um e-commerce?",
      "context_examples": ["Facilidade, preço, confiabilidade"]
    }
  ],
  "files": [
    {
      "filename": "home-page.png",
      "file_path": "data/topic_guides/compra-amazon/home-page.png",
      "file_type": "PNG",
      "description": "Página inicial da Amazon mostrando categorias de produtos...",
      "size_bytes": 245680,
      "created_at": "2025-12-15T10:30:00Z"
    }
  ],
  "summary": "Topic guide para entrevistas sobre experiência de compra online...",
  "question_count": 12,
  "file_count": 8,
  "created_at": "2025-12-15T10:00:00Z",
  "updated_at": "2025-12-19T14:30:00Z"
}
```

**Response 404**:
```json
{
  "error": {
    "code": "TOPIC_NOT_FOUND",
    "message": "Topic guide 'compra-amazon' não encontrado"
  }
}
```

**Exemplo**:
```bash
curl "http://localhost:8000/topics/compra-amazon"
```

---

#### 2.3 Listar Research Executions de um Topic

```http
GET /topics/{topic_name}/research
```

Lista research executions de um topic específico.

**Path Parameters**:
- `topic_name` (string, requerido): Nome do topic guide

**Query Parameters**:
- `limit`, `offset`, `sort_by`, `sort_order` (padrão paginação)

**Response 200**:
```json
{
  "data": [
    {
      "exec_id": "batch_compra-amazon_20251219_110534",
      "topic_name": "compra-amazon",
      "synth_count": 10,
      "successful_count": 9,
      "failed_count": 1,
      "status": "completed",
      "started_at": "2025-12-19T11:05:34Z",
      "completed_at": "2025-12-19T11:12:45Z"
    }
  ],
  "pagination": {
    "total": 3,
    "limit": 50,
    "offset": 0,
    "has_next": false
  }
}
```

**Exemplo**:
```bash
curl "http://localhost:8000/topics/compra-amazon/research"
```

---

### 3. Research Endpoints (7 endpoints)

#### 3.1 Listar Research Executions

```http
GET /research/list
```

Lista research executions com paginação e filtros opcionais.

**Query Parameters**:
- `limit` (int, opcional): Padrão 50, máx 200
- `offset` (int, opcional): Padrão 0
- `sort_by` (string, opcional): Campo para ordenação (padrão: `started_at`)
- `sort_order` (string, opcional): `asc` ou `desc` (padrão: `desc`)

**Response 200**:
```json
{
  "data": [
    {
      "exec_id": "batch_compra-amazon_20251219_110534",
      "experiment_id": "exp_12345",
      "topic_name": "compra-amazon",
      "synth_count": 10,
      "status": "completed",
      "started_at": "2025-12-19T11:05:34Z",
      "completed_at": "2025-12-19T11:12:45Z"
    }
  ],
  "pagination": {
    "total": 15,
    "limit": 50,
    "offset": 0,
    "has_next": false
  }
}
```

**Exemplo**:
```bash
curl "http://localhost:8000/research/list?sort_by=started_at&sort_order=desc"
```

---

#### 3.2 Obter Research Execution por ID

```http
GET /research/{exec_id}
```

Retorna detalhes completos de uma research execution, incluindo contadores e flags de disponibilidade.

**Path Parameters**:
- `exec_id` (string, requerido): ID da execution (ex: `batch_compra-amazon_20251219_110534`)

**Response 200**:
```json
{
  "exec_id": "batch_compra-amazon_20251219_110534",
  "experiment_id": "exp_12345",
  "topic_name": "compra-amazon",
  "synth_count": 10,
  "successful_count": 9,
  "failed_count": 1,
  "model": "gpt-4o-mini",
  "max_turns": 6,
  "status": "completed",
  "started_at": "2025-12-19T11:05:34Z",
  "completed_at": "2025-12-19T11:12:45Z",
  "summary_available": true,
  "prfaq_available": false
}
```

**Status Possíveis**:
- `pending` - Aguardando processamento
- `running` - Em execução
- `generating_summary` - Gerando sumário
- `completed` - Completado com sucesso
- `failed` - Falhou

**Response 404**:
```json
{
  "error": {
    "code": "EXECUTION_NOT_FOUND",
    "message": "Research execution 'batch_...' não encontrada"
  }
}
```

**Exemplo**:
```bash
curl "http://localhost:8000/research/batch_compra-amazon_20251219_110534"
```

---

#### 3.3 Listar Transcrições de uma Execution

```http
GET /research/{exec_id}/transcripts
```

Lista transcrições (resumos) de todas as entrevistas em uma research execution.

**Path Parameters**:
- `exec_id` (string, requerido): ID da execution

**Query Parameters**:
- `limit` (int, opcional): Padrão 50, máx 200
- `offset` (int, opcional): Padrão 0

**Response 200**:
```json
{
  "data": [
    {
      "synth_id": "ynnasw",
      "synth_name": "Ravy Lopes",
      "turn_count": 6,
      "timestamp": "2025-12-19T11:08:23Z",
      "status": "completed"
    },
    {
      "synth_id": "abc123",
      "synth_name": "Maria Silva",
      "turn_count": 5,
      "timestamp": "2025-12-19T11:09:15Z",
      "status": "completed"
    }
  ],
  "pagination": {
    "total": 10,
    "limit": 50,
    "offset": 0,
    "has_next": false
  }
}
```

**Exemplo**:
```bash
curl "http://localhost:8000/research/batch_compra-amazon_20251219_110534/transcripts"
```

---

#### 3.4 Obter Transcrição Específica

```http
GET /research/{exec_id}/transcripts/{synth_id}
```

Retorna transcrição completa de uma entrevista, incluindo todas as mensagens (perguntas e respostas).

**Path Parameters**:
- `exec_id` (string, requerido): ID da execution
- `synth_id` (string, requerido): ID do synth entrevistado

**Response 200**:
```json
{
  "exec_id": "batch_compra-amazon_20251219_110534",
  "synth_id": "ynnasw",
  "synth_name": "Ravy Lopes",
  "turn_count": 6,
  "timestamp": "2025-12-19T11:08:23Z",
  "status": "completed",
  "messages": [
    {
      "speaker": "Interviewer",
      "text": "Como você se sente ao fazer compras online?",
      "internal_notes": null
    },
    {
      "speaker": "Ravy Lopes",
      "text": "Eu me sinto bem confortável. Uso bastante e-commerce para comprar eletrônicos e livros.",
      "internal_notes": "Demonstra confiança (abertura: 82)"
    },
    {
      "speaker": "Interviewer",
      "text": "O que você mais valoriza em um e-commerce?",
      "internal_notes": "Explorar valores principais"
    }
  ]
}
```

**Response 404**:
```json
{
  "error": {
    "code": "TRANSCRIPT_NOT_FOUND",
    "message": "Transcrição não encontrada para exec 'batch_...' e synth 'ynnasw'"
  }
}
```

**Exemplo**:
```bash
curl "http://localhost:8000/research/batch_compra-amazon_20251219_110534/transcripts/ynnasw"
```

---

#### 3.5 Gerar Summary

```http
POST /research/{exec_id}/summary/generate
```

Inicia a geração de um summary para uma research execution completada. A geração acontece em background, e o endpoint retorna imediatamente.

**Path Parameters**:
- `exec_id` (string, requerido): ID da execution

**Request Body** (opcional):
```json
{
  "model": "gpt-5-mini"
}
```

**Body Parameters**:
- `model` (string, opcional): Modelo LLM para geração (padrão: `gpt-5-mini`)

**Response 200**:
```json
{
  "exec_id": "batch_compra-amazon_20251219_110534",
  "status": "generating",
  "message": "Started summary generation",
  "generated_at": "2025-12-19T11:15:00Z"
}
```

**Status Possíveis**:
- `generating` - Geração em andamento
- `completed` - Geração completada
- `failed` - Geração falhou

**Response 404**:
```json
{
  "error": {
    "code": "EXECUTION_NOT_FOUND",
    "message": "Execution not found"
  }
}
```

**Response 400**:
```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Execution batch_... is not completed (status: running)"
  }
}
```

**Exemplo**:
```bash
# Com modelo padrão
curl -X POST "http://localhost:8000/research/batch_compra-amazon_20251219_110534/summary/generate"

# Com modelo específico
curl -X POST "http://localhost:8000/research/batch_compra-amazon_20251219_110534/summary/generate" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4o"}'
```

---

#### 3.6 Executar Research

```http
POST /research/execute
```

Inicia uma nova research execution (batch de entrevistas). A execução roda de forma assíncrona - use `GET /research/{exec_id}` para verificar o status.

**Request Body**:
```json
{
  "topic_name": "compra-amazon",
  "experiment_id": "exp_12345",
  "additional_context": "Foco em experiência mobile",
  "synth_ids": ["ynnasw", "abc123"],
  "synth_count": null,
  "max_turns": 6,
  "max_concurrent": 12,
  "model": "gpt-4o-mini",
  "skip_interviewee_review": true
}
```

**Body Parameters**:
- `topic_name` (string, requerido): Nome do topic guide
- `experiment_id` (string, opcional): ID do experimento pai (para linkagem)
- `additional_context` (string, opcional): Contexto adicional para complementar o cenário
- `synth_ids` (list[string], opcional): IDs específicos de synths para entrevistar
- `synth_count` (int, opcional): Número de synths aleatórios (se `synth_ids` não fornecido)
- `max_turns` (int, opcional): Máximo de turnos por entrevista (padrão: 6, min: 1, max: 20)
- `max_concurrent` (int, opcional): Máximo de entrevistas simultâneas (padrão: 12, min: 1, max: 50)
- `model` (string, opcional): Modelo LLM para usar (padrão: `gpt-4o-mini`)
- `skip_interviewee_review` (bool, opcional): Pular revisão de respostas para execução mais rápida (padrão: true)

**Response 200**:
```json
{
  "exec_id": "batch_compra-amazon_20251219_110534",
  "status": "running",
  "topic_name": "compra-amazon",
  "synth_count": 2,
  "started_at": "2025-12-19T11:05:34Z"
}
```

**Exemplo**:
```bash
# Executar com synth_ids específicos
curl -X POST "http://localhost:8000/research/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "topic_name": "compra-amazon",
    "synth_ids": ["ynnasw", "abc123"],
    "max_turns": 8,
    "model": "gpt-4o-mini"
  }'

# Executar com synth_count aleatório
curl -X POST "http://localhost:8000/research/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "topic_name": "compra-amazon",
    "synth_count": 5,
    "max_turns": 6
  }'
```

---

#### 3.7 Stream de Mensagens (SSE)

```http
GET /research/{exec_id}/stream
```

Conecta via Server-Sent Events (SSE) para receber atualizações em tempo real de todas as entrevistas em uma execution. Primeiro envia mensagens históricas (replay), depois transmite mensagens ao vivo.

**Path Parameters**:
- `exec_id` (string, requerido): ID da execution

**Response 200**:
- Content-Type: `text/event-stream`
- Headers:
  - `Cache-Control: no-cache`
  - `Connection: keep-alive`
  - `X-Accel-Buffering: no`

**Eventos SSE**:

1. **message** - Mensagem de entrevista (pergunta ou resposta)
```
event: message
data: {
  "event_type": "message",
  "exec_id": "batch_compra-amazon_20251219_110534",
  "synth_id": "ynnasw",
  "turn_number": 1,
  "speaker": "Interviewer",
  "text": "Como você se sente ao fazer compras online?",
  "timestamp": "2025-12-19T11:08:23Z",
  "is_replay": false
}
```

2. **interview_completed** - Uma entrevista individual foi concluída
```
event: interview_completed
data: {
  "synth_id": "ynnasw",
  "total_turns": 6
}
```

3. **transcription_completed** - Todas as entrevistas finalizadas, geração de summary iniciando
```
event: transcription_completed
data: {
  "successful_count": 9,
  "failed_count": 1
}
```

4. **execution_completed** - Todo o processamento finalizado (incluindo summary)
```
event: execution_completed
data: {}
```

**Response 404**:
```json
{
  "error": {
    "code": "EXECUTION_NOT_FOUND",
    "message": "Execution not found"
  }
}
```

**Exemplo (JavaScript)**:
```javascript
const eventSource = new EventSource(
  'http://localhost:8000/research/batch_compra-amazon_20251219_110534/stream'
);

// Mensagem de entrevista
eventSource.addEventListener('message', (e) => {
  const event = JSON.parse(e.data);
  console.log(`[${event.synth_id}] ${event.speaker}: ${event.text}`);
});

// Entrevista individual concluída
eventSource.addEventListener('interview_completed', (e) => {
  const data = JSON.parse(e.data);
  console.log(`Interview ${data.synth_id} completed: ${data.total_turns} turns`);
});

// Todas as transcrições concluídas
eventSource.addEventListener('transcription_completed', (e) => {
  const data = JSON.parse(e.data);
  console.log(`All done! ${data.successful_count} success, ${data.failed_count} failed`);
});

// Execution completada
eventSource.addEventListener('execution_completed', () => {
  console.log('Execution fully completed!');
  eventSource.close();
});
```

**Exemplo (cURL)**:
```bash
# Streaming via cURL
curl -N "http://localhost:8000/research/batch_compra-amazon_20251219_110534/stream"
```

---

### 4. PR-FAQ Endpoints (3 endpoints)

#### 4.1 Listar PR-FAQs

```http
GET /prfaq/list
```

Lista PR-FAQs gerados com metadata.

**Query Parameters**:
- `limit`, `offset`, `sort_by`, `sort_order` (padrão paginação)

**Response 200**:
```json
{
  "data": [
    {
      "exec_id": "batch_compra-amazon_20251219_110534",
      "topic_name": "compra-amazon",
      "headline": "Amazon lança novo sistema de recomendações personalizadas",
      "one_liner": "Usuários agora recebem sugestões baseadas em preferências individuais",
      "faq_count": 12,
      "confidence_score": 0.87,
      "validation_status": "validated",
      "generated_at": "2025-12-19T11:20:00Z"
    }
  ],
  "pagination": {
    "total": 8,
    "limit": 50,
    "offset": 0,
    "has_next": false
  }
}
```

**Exemplo**:
```bash
curl "http://localhost:8000/prfaq/list"
```

---

#### 4.2 Obter PR-FAQ por Execution ID

```http
GET /prfaq/{exec_id}
```

Retorna metadata de um PR-FAQ.

**Path Parameters**:
- `exec_id` (string, requerido): ID da execution

**Response 200**:
```json
{
  "exec_id": "batch_compra-amazon_20251219_110534",
  "topic_name": "compra-amazon",
  "headline": "Amazon lança novo sistema de recomendações personalizadas",
  "one_liner": "Usuários agora recebem sugestões baseadas em preferências individuais",
  "faq_count": 12,
  "confidence_score": 0.87,
  "validation_status": "validated",
  "model": "gpt-xxxx",
  "generated_at": "2025-12-19T11:20:00Z",
  "markdown_path": "output/reports/batch_compra-amazon_20251219_110534_prfaq.md",
  "json_path": "output/reports/batch_compra-amazon_20251219_110534_prfaq.json"
}
```

**Response 404**:
```json
{
  "error": {
    "code": "PRFAQ_NOT_FOUND",
    "message": "PR-FAQ não encontrado para execution 'batch_...'"
  }
}
```

**Exemplo**:
```bash
curl "http://localhost:8000/prfaq/batch_compra-amazon_20251219_110534"
```

---

#### 4.3 Download de PR-FAQ (Markdown)

```http
GET /prfaq/{exec_id}/markdown
```

Faz download do PR-FAQ em Markdown.

**Path Parameters**:
- `exec_id` (string, requerido): ID da execution

**Response 200**:
- Content-Type: `text/plain; charset=utf-8`
- Body: Arquivo Markdown com Press Release + FAQ

**Response 404**:
```json
{
  "error": {
    "code": "PRFAQ_NOT_FOUND",
    "message": "PR-FAQ não encontrado para execution 'batch_...'"
  }
}
```

**Exemplo**:
```bash
# Download
curl "http://localhost:8000/prfaq/batch_compra-amazon_20251219_110534/markdown" -o prfaq.md

# Visualizar
curl "http://localhost:8000/prfaq/batch_compra-amazon_20251219_110534/markdown"
```

---

### 5. Jobs Endpoint (1 endpoint)

#### 5.1 Consultar Status de Job Assíncrono

```http
GET /jobs/{job_id}
```

Retorna status de um job assíncrono (summary, PR-FAQ).

**Path Parameters**:
- `job_id` (string, requerido): UUID do job

**Response 200**:
```json
{
  "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "job_type": "generate_summary",
  "exec_id": "batch_compra-amazon_20251219_110534",
  "status": "completed",
  "created_at": "2025-12-19T11:12:50Z",
  "started_at": "2025-12-19T11:12:51Z",
  "completed_at": "2025-12-19T11:15:23Z",
  "error_message": null,
  "result_data": {
    "file_path": "output/reports/batch_compra-amazon_20251219_110534_summary.md"
  }
}
```

**Status Possíveis**:
- `pending` - Aguardando processamento
- `running` - Em processamento
- `completed` - Completado com sucesso
- `failed` - Falhou

**Response 404**:
```json
{
  "error": {
    "code": "JOB_NOT_FOUND",
    "message": "Job 'f47ac10b-...' não encontrado"
  }
}
```

**Exemplo**:
```bash
curl "http://localhost:8000/jobs/f47ac10b-58cc-4372-a567-0e02b2c3d479"
```

---

### 6. Experiments Endpoints (12 endpoints)

#### 6.1 Criar Experimento

```http
POST /experiments
```

Cria um novo experimento, opcionalmente com scorecard embutido.

**Request Body**:
```json
{
  "name": "Novo Fluxo de Checkout",
  "hypothesis": "Reduzir etapas do checkout aumentará conversão em 15%",
  "description": "Baseado em feedback de usuários e análise de abandono",
  "scorecard_data": null
}
```

**Body Parameters**:
- `name` (string, requerido): Nome curto da feature (máx 100 caracteres)
- `hypothesis` (string, requerido): Descrição da hipótese a testar (máx 500 caracteres)
- `description` (string, opcional): Contexto adicional (máx 2000 caracteres)
- `scorecard_data` (object, opcional): Dados do scorecard embutido

**Response 201**:
```json
{
  "id": "exp_a1b2c3d4",
  "name": "Novo Fluxo de Checkout",
  "hypothesis": "Reduzir etapas do checkout aumentará conversão em 15%",
  "description": "Baseado em feedback de usuários e análise de abandono",
  "scorecard_data": null,
  "has_scorecard": false,
  "has_interview_guide": false,
  "tags": [],
  "created_at": "2025-12-19T10:30:00Z",
  "updated_at": null
}
```

**Response 422** (Validação falhou):
```json
{
  "detail": "Name must not exceed 100 characters"
}
```

**Exemplo**:
```bash
curl -X POST "http://localhost:8000/experiments" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Novo Fluxo de Checkout",
    "hypothesis": "Reduzir etapas do checkout aumentará conversão em 15%"
  }'
```

---

#### 6.2 Estimar Scorecard via IA (sem experimento)

```http
POST /experiments/estimate-scorecard
```

Usa IA para estimar dimensões do scorecard a partir de texto, antes de criar o experimento.

**Request Body**:
```json
{
  "name": "Novo Fluxo de Checkout",
  "hypothesis": "Reduzir etapas do checkout aumentará conversão em 15%",
  "description": "Sistema de checkout simplificado com menos etapas"
}
```

**Body Parameters**:
- `name` (string, requerido): Nome curto da feature (máx 100 caracteres)
- `hypothesis` (string, requerido): Descrição da hipótese (máx 500 caracteres)
- `description` (string, opcional): Contexto adicional (máx 2000 caracteres)

**Response 200**:
```json
{
  "complexity": {
    "score": 0.4,
    "rules_applied": [],
    "lower_bound": 0.3,
    "upper_bound": 0.5
  },
  "initial_effort": {
    "score": 0.3,
    "rules_applied": [],
    "lower_bound": 0.2,
    "upper_bound": 0.4
  },
  "perceived_risk": {
    "score": 0.2,
    "rules_applied": [],
    "lower_bound": 0.1,
    "upper_bound": 0.3
  },
  "time_to_value": {
    "score": 0.6,
    "rules_applied": [],
    "lower_bound": 0.5,
    "upper_bound": 0.7
  },
  "justification": "Based on feature complexity and similar implementations...",
  "impact_hypotheses": ["Users may struggle initially with the new flow"]
}
```

**Response 500** (Erro na estimativa):
```json
{
  "detail": "Scorecard estimation failed: LLM error"
}
```

**Exemplo**:
```bash
curl -X POST "http://localhost:8000/experiments/estimate-scorecard" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Novo Fluxo de Checkout",
    "hypothesis": "Reduzir etapas do checkout aumentará conversão em 15%"
  }'
```

---

#### 6.3 Listar Experimentos

```http
GET /experiments/list
```

Lista experimentos com paginação, busca, ordenação e filtro por tags.

**Query Parameters**:
- `limit` (int, opcional): Padrão 50, máx 200
- `offset` (int, opcional): Padrão 0
- `search` (string, opcional): Filtra por nome OU hipótese (case-insensitive, máx 200 caracteres)
- `tag` (string, opcional): Filtra por nome de tag (exact match, máx 50 caracteres)
- `sort_by` (string, opcional): `created_at` (padrão) ou `name`
- `sort_order` (string, opcional): `desc` (padrão) ou `asc`

**Response 200**:
```json
{
  "data": [
    {
      "id": "exp_a1b2c3d4",
      "name": "Novo Fluxo de Checkout",
      "hypothesis": "Reduzir etapas do checkout aumentará conversão em 15%",
      "description": "Baseado em feedback de usuários",
      "has_scorecard": true,
      "has_analysis": true,
      "has_interview_guide": true,
      "interview_count": 3,
      "tags": ["ux-research", "checkout"],
      "created_at": "2025-12-19T10:30:00Z",
      "updated_at": "2025-12-20T14:00:00Z"
    }
  ],
  "pagination": {
    "total": 25,
    "limit": 50,
    "offset": 0,
    "has_next": false
  }
}
```

**Exemplo**:
```bash
# Listar com paginação
curl "http://localhost:8000/experiments/list?limit=10&offset=0"

# Buscar por termo
curl "http://localhost:8000/experiments/list?search=checkout"

# Filtrar por tag
curl "http://localhost:8000/experiments/list?tag=ux-research"

# Ordenar por nome
curl "http://localhost:8000/experiments/list?sort_by=name&sort_order=asc"
```

---

#### 6.4 Obter Experimento por ID

```http
GET /experiments/{experiment_id}
```

Retorna detalhes completos de um experimento, incluindo análise e entrevistas vinculadas.

**Path Parameters**:
- `experiment_id` (string, requerido): ID do experimento

**Response 200**:
```json
{
  "id": "exp_a1b2c3d4",
  "name": "Novo Fluxo de Checkout",
  "hypothesis": "Reduzir etapas do checkout aumentará conversão em 15%",
  "description": "Baseado em feedback de usuários",
  "scorecard_data": {
    "feature_name": "Novo Fluxo de Checkout",
    "scenario": "baseline",
    "description_text": "Sistema de checkout simplificado",
    "description_media_urls": [],
    "complexity": {"score": 0.4, "rules_applied": [], "lower_bound": 0.3, "upper_bound": 0.5},
    "initial_effort": {"score": 0.3, "rules_applied": [], "lower_bound": null, "upper_bound": null},
    "perceived_risk": {"score": 0.2, "rules_applied": [], "lower_bound": null, "upper_bound": null},
    "time_to_value": {"score": 0.6, "rules_applied": [], "lower_bound": null, "upper_bound": null},
    "justification": "Based on feature complexity...",
    "impact_hypotheses": []
  },
  "has_scorecard": true,
  "has_interview_guide": true,
  "tags": ["ux-research", "checkout"],
  "created_at": "2025-12-19T10:30:00Z",
  "updated_at": "2025-12-20T14:00:00Z",
  "analysis": {
    "id": "ana_12345678",
    "simulation_id": "ana_12345678",
    "status": "completed",
    "started_at": "2025-12-19T11:00:00Z",
    "completed_at": "2025-12-19T11:05:00Z",
    "total_synths": 100,
    "n_executions": 100,
    "execution_time_seconds": 300.5,
    "aggregated_outcomes": {
      "did_not_try_rate": 0.2,
      "failed_rate": 0.3,
      "success_rate": 0.5
    }
  },
  "interviews": [
    {
      "exec_id": "batch_exp_a1b2c3d4_20251219_120000",
      "topic_name": "exp_a1b2c3d4",
      "status": "completed",
      "synth_count": 10,
      "total_turns": 60,
      "has_summary": true,
      "has_prfaq": false,
      "additional_context": "Foco em usuários mobile",
      "started_at": "2025-12-19T12:00:00Z",
      "completed_at": "2025-12-19T12:15:00Z"
    }
  ],
  "interview_count": 1
}
```

**Response 404**:
```json
{
  "detail": "Experiment exp_invalid not found"
}
```

**Exemplo**:
```bash
curl "http://localhost:8000/experiments/exp_a1b2c3d4"
```

---

#### 6.5 Atualizar Experimento

```http
PUT /experiments/{experiment_id}
```

Atualiza nome, hipótese ou descrição de um experimento. Para atualizar o scorecard, use `PUT /experiments/{id}/scorecard`.

**Path Parameters**:
- `experiment_id` (string, requerido): ID do experimento

**Request Body**:
```json
{
  "name": "Novo Fluxo de Checkout v2",
  "hypothesis": "Reduzir etapas do checkout aumentará conversão em 20%",
  "description": "Baseado em nova análise de dados"
}
```

**Body Parameters** (todos opcionais):
- `name` (string): Nome curto da feature (máx 100 caracteres)
- `hypothesis` (string): Descrição da hipótese (máx 500 caracteres)
- `description` (string): Contexto adicional (máx 2000 caracteres)

**Response 200**:
```json
{
  "id": "exp_a1b2c3d4",
  "name": "Novo Fluxo de Checkout v2",
  "hypothesis": "Reduzir etapas do checkout aumentará conversão em 20%",
  "description": "Baseado em nova análise de dados",
  "scorecard_data": null,
  "has_scorecard": false,
  "has_interview_guide": true,
  "tags": ["ux-research"],
  "created_at": "2025-12-19T10:30:00Z",
  "updated_at": "2025-12-20T15:00:00Z"
}
```

**Response 404**:
```json
{
  "detail": "Experiment exp_invalid not found"
}
```

**Exemplo**:
```bash
curl -X PUT "http://localhost:8000/experiments/exp_a1b2c3d4" \
  -H "Content-Type: application/json" \
  -d '{"name": "Novo Fluxo de Checkout v2"}'
```

---

#### 6.6 Deletar Experimento

```http
DELETE /experiments/{experiment_id}
```

Deleta um experimento.

**Path Parameters**:
- `experiment_id` (string, requerido): ID do experimento

**Response 204**: Sem conteúdo (sucesso)

**Response 404**:
```json
{
  "detail": "Experiment exp_invalid not found"
}
```

**Exemplo**:
```bash
curl -X DELETE "http://localhost:8000/experiments/exp_a1b2c3d4"
```

---

#### 6.7 Atualizar Scorecard do Experimento

```http
PUT /experiments/{experiment_id}/scorecard
```

Atualiza ou cria o scorecard embutido de um experimento.

**Path Parameters**:
- `experiment_id` (string, requerido): ID do experimento

**Request Body**:
```json
{
  "feature_name": "Novo Fluxo de Checkout",
  "scenario": "baseline",
  "description_text": "Sistema de checkout simplificado com menos etapas",
  "description_media_urls": [],
  "complexity": {
    "score": 0.4,
    "rules_applied": ["Menos etapas", "Interface familiar"],
    "lower_bound": 0.3,
    "upper_bound": 0.5
  },
  "initial_effort": {
    "score": 0.3,
    "rules_applied": [],
    "lower_bound": null,
    "upper_bound": null
  },
  "perceived_risk": {
    "score": 0.2,
    "rules_applied": [],
    "lower_bound": null,
    "upper_bound": null
  },
  "time_to_value": {
    "score": 0.6,
    "rules_applied": [],
    "lower_bound": null,
    "upper_bound": null
  },
  "justification": "Based on feature complexity and similar implementations",
  "impact_hypotheses": ["Users may struggle initially with the new flow"]
}
```

**Response 200**:
```json
{
  "id": "exp_a1b2c3d4",
  "name": "Novo Fluxo de Checkout",
  "hypothesis": "Reduzir etapas do checkout aumentará conversão em 15%",
  "description": "Baseado em feedback de usuários",
  "scorecard_data": {
    "feature_name": "Novo Fluxo de Checkout",
    "scenario": "baseline",
    "description_text": "Sistema de checkout simplificado com menos etapas",
    "description_media_urls": [],
    "complexity": {"score": 0.4, "rules_applied": ["Menos etapas", "Interface familiar"], "lower_bound": 0.3, "upper_bound": 0.5},
    "initial_effort": {"score": 0.3, "rules_applied": [], "lower_bound": null, "upper_bound": null},
    "perceived_risk": {"score": 0.2, "rules_applied": [], "lower_bound": null, "upper_bound": null},
    "time_to_value": {"score": 0.6, "rules_applied": [], "lower_bound": null, "upper_bound": null},
    "justification": "Based on feature complexity and similar implementations",
    "impact_hypotheses": ["Users may struggle initially with the new flow"]
  },
  "has_scorecard": true,
  "has_interview_guide": true,
  "tags": [],
  "created_at": "2025-12-19T10:30:00Z",
  "updated_at": "2025-12-20T16:00:00Z"
}
```

**Response 404**:
```json
{
  "detail": "Experiment exp_invalid not found"
}
```

**Exemplo**:
```bash
curl -X PUT "http://localhost:8000/experiments/exp_a1b2c3d4/scorecard" \
  -H "Content-Type: application/json" \
  -d '{
    "feature_name": "Novo Fluxo de Checkout",
    "scenario": "baseline",
    "description_text": "Sistema simplificado",
    "complexity": {"score": 0.4, "rules_applied": []},
    "initial_effort": {"score": 0.3, "rules_applied": []},
    "perceived_risk": {"score": 0.2, "rules_applied": []},
    "time_to_value": {"score": 0.6, "rules_applied": []}
  }'
```

---

#### 6.8 Criar Entrevista para Experimento

```http
POST /experiments/{experiment_id}/interviews
```

Cria uma nova entrevista vinculada ao experimento. Usa o interview guide do experimento.

**Path Parameters**:
- `experiment_id` (string, requerido): ID do experimento

**Request Body**:
```json
{
  "additional_context": "Foco em experiência mobile",
  "synth_ids": ["synth_001", "synth_002"],
  "synth_count": null,
  "max_turns": 6,
  "generate_summary": true
}
```

**Body Parameters**:
- `additional_context` (string, opcional): Contexto adicional para complementar o cenário
- `synth_ids` (list[string], opcional): IDs específicos de synths para entrevistar
- `synth_count` (int, opcional): Número de synths aleatórios se `synth_ids` não fornecido (padrão: 5, min: 1, max: 50)
- `max_turns` (int, opcional): Máximo de turnos por entrevista (padrão: 6, min: 1, max: 20)
- `generate_summary` (bool, opcional): Gerar summary após conclusão (padrão: true)

**Response 201**:
```json
{
  "exec_id": "batch_exp_a1b2c3d4_20251219_120000",
  "status": "running",
  "topic_name": "exp_a1b2c3d4",
  "synth_count": 2,
  "started_at": "2025-12-19T12:00:00Z"
}
```

**Response 404**:
```json
{
  "detail": "Experiment exp_invalid not found"
}
```

**Response 422**:
```json
{
  "detail": "Experiment does not have an interview guide configured"
}
```

**Exemplo**:
```bash
curl -X POST "http://localhost:8000/experiments/exp_a1b2c3d4/interviews" \
  -H "Content-Type: application/json" \
  -d '{
    "synth_count": 5,
    "max_turns": 8,
    "additional_context": "Foco em usuários mobile"
  }'
```

---

#### 6.9 Obter Auto-Entrevista do Experimento

```http
GET /experiments/{experiment_id}/interviews/auto
```

Retorna a auto-entrevista (casos extremos) do experimento, se existir.

**Path Parameters**:
- `experiment_id` (string, requerido): ID do experimento

**Response 200** (se existir):
```json
{
  "exec_id": "batch_exp_a1b2c3d4_auto_20251219_130000",
  "status": "completed",
  "topic_name": "exp_a1b2c3d4_auto",
  "synth_count": 10,
  "started_at": "2025-12-19T13:00:00Z"
}
```

**Response 200** (se não existir):
```json
null
```

**Exemplo**:
```bash
curl "http://localhost:8000/experiments/exp_a1b2c3d4/interviews/auto"
```

---

#### 6.10 Criar Auto-Entrevista para Experimento

```http
POST /experiments/{experiment_id}/interviews/auto
```

Cria uma entrevista automática com casos extremos (5 melhores + 5 piores) dos resultados da simulação.

**Path Parameters**:
- `experiment_id` (string, requerido): ID do experimento

**Requisitos**:
- Experimento deve existir
- Experimento deve ter interview guide configurado
- Simulação deve ter pelo menos 10 synths

**Response 201**:
```json
{
  "exec_id": "batch_exp_a1b2c3d4_auto_20251219_130000",
  "status": "running",
  "topic_name": "exp_a1b2c3d4_auto",
  "synth_count": 10,
  "started_at": "2025-12-19T13:00:00Z"
}
```

**Response 404**:
```json
{
  "detail": "Experiment exp_invalid not found"
}
```

**Response 400**:
```json
{
  "detail": "Not enough synths for auto-interview. Found 8, need 10 (5 best + 5 worst)."
}
```

**Response 422**:
```json
{
  "detail": "Experiment does not have an interview guide configured"
}
```

**Exemplo**:
```bash
curl -X POST "http://localhost:8000/experiments/exp_a1b2c3d4/interviews/auto"
```

---

#### 6.11 Listar Explorações do Experimento

```http
GET /experiments/{experiment_id}/explorations
```

Lista todas as explorações de um experimento, ordenadas por data (mais recente primeiro).

**Path Parameters**:
- `experiment_id` (string, requerido): ID do experimento

**Response 200**:
```json
[
  {
    "id": "expl_12345678",
    "status": "completed",
    "goal_value": "maximize_success",
    "best_success_rate": 0.75,
    "total_nodes": 15,
    "started_at": "2025-12-19T14:00:00Z",
    "completed_at": "2025-12-19T14:30:00Z"
  }
]
```

**Response 404**:
```json
{
  "detail": "Experiment exp_invalid not found"
}
```

**Exemplo**:
```bash
curl "http://localhost:8000/experiments/exp_a1b2c3d4/explorations"
```

---

#### 6.12 Estimar Scorecard para Experimento

```http
POST /experiments/{experiment_id}/estimate-scorecard
```

Usa IA para estimar dimensões do scorecard baseado nos dados do experimento existente.

**Path Parameters**:
- `experiment_id` (string, requerido): ID do experimento

**Response 200**:
```json
{
  "complexity": {
    "score": 0.4,
    "rules_applied": [],
    "lower_bound": 0.3,
    "upper_bound": 0.5
  },
  "initial_effort": {
    "score": 0.3,
    "rules_applied": [],
    "lower_bound": 0.2,
    "upper_bound": 0.4
  },
  "perceived_risk": {
    "score": 0.2,
    "rules_applied": [],
    "lower_bound": 0.1,
    "upper_bound": 0.3
  },
  "time_to_value": {
    "score": 0.6,
    "rules_applied": [],
    "lower_bound": 0.5,
    "upper_bound": 0.7
  },
  "justification": "Based on experiment details and similar implementations...",
  "impact_hypotheses": ["Users may need time to adapt to the new workflow"]
}
```

**Response 404**:
```json
{
  "detail": "Experiment exp_invalid not found"
}
```

**Response 500**:
```json
{
  "detail": "Scorecard estimation failed: LLM error"
}
```

**Exemplo**:
```bash
curl -X POST "http://localhost:8000/experiments/exp_a1b2c3d4/estimate-scorecard"
```

---

### 7. Tags Endpoints (4 endpoints)

#### 7.1 Listar Tags

```http
GET /tags
```

Lista todas as tags disponíveis no sistema, ordenadas por nome.

**Response 200**:
```json
[
  {
    "id": "tag_abc123",
    "name": "pesquisa-mercado"
  },
  {
    "id": "tag_def456",
    "name": "ux-research"
  }
]
```

**Exemplo**:
```bash
curl "http://localhost:8000/tags"
```

---

#### 7.2 Criar Tag

```http
POST /tags
```

Cria uma nova tag. Se uma tag com o mesmo nome já existir, retorna a tag existente.

**Request Body**:
```json
{
  "name": "nova-tag"
}
```

**Body Parameters**:
- `name` (string, requerido): Nome da tag (máx 50 caracteres)

**Response 201**:
```json
{
  "id": "tag_xyz789",
  "name": "nova-tag"
}
```

**Response 200** (tag já existe):
```json
{
  "id": "tag_abc123",
  "name": "nova-tag"
}
```

**Exemplo**:
```bash
curl -X POST "http://localhost:8000/tags" \
  -H "Content-Type: application/json" \
  -d '{"name": "pesquisa-qualitativa"}'
```

---

#### 7.3 Adicionar Tag a Experimento

```http
POST /tags/experiments/{experiment_id}/tags
```

Adiciona uma tag a um experimento. Cria a tag se não existir. Operação idempotente (adicionar tag já associada não causa erro).

**Path Parameters**:
- `experiment_id` (string, requerido): ID do experimento

**Request Body**:
```json
{
  "tag_name": "ux-research"
}
```

**Body Parameters**:
- `tag_name` (string, requerido): Nome da tag a adicionar

**Response 204**: Sem conteúdo (sucesso)

**Response 404**:
```json
{
  "detail": "Experiment exp_12345 not found"
}
```

**Exemplo**:
```bash
curl -X POST "http://localhost:8000/tags/experiments/exp_12345/tags" \
  -H "Content-Type: application/json" \
  -d '{"tag_name": "ux-research"}'
```

---

#### 7.4 Remover Tag de Experimento

```http
DELETE /tags/experiments/{experiment_id}/tags/{tag_name}
```

Remove a associação de uma tag com um experimento. A tag em si não é deletada do sistema.

**Path Parameters**:
- `experiment_id` (string, requerido): ID do experimento
- `tag_name` (string, requerido): Nome da tag a remover

**Response 204**: Sem conteúdo (sucesso)

**Response 404**:
```json
{
  "detail": "Experiment exp_12345 not found"
}
```

Ou:
```json
{
  "detail": "Tag 'ux-research' not found"
}
```

Ou:
```json
{
  "detail": "Tag 'ux-research' not associated with experiment exp_12345"
}
```

**Exemplo**:
```bash
curl -X DELETE "http://localhost:8000/tags/experiments/exp_12345/tags/ux-research"
```

---

### 8. Health Check Endpoints (2 endpoints)

#### 8.1 Health Check

```http
GET /health
```

Verifica se o servidor está ativo.

**Response 200**:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-19T15:30:00Z",
  "version": "2.0.0"
}
```

**Exemplo**:
```bash
curl "http://localhost:8000/health"
```

---

#### 8.2 Root Endpoint

```http
GET /
```

Informações básicas da API.

**Response 200**:
```json
{
  "name": "synth-lab API",
  "version": "2.0.0",
  "description": "API REST para geração e pesquisa com personas sintéticas",
  "docs": "/docs",
  "redoc": "/redoc"
}
```

**Exemplo**:
```bash
curl "http://localhost:8000/"
```

---

## Códigos de Erro

### Códigos HTTP

| Código | Significado | Quando Usar |
|--------|-------------|-------------|
| 200 | OK | Sucesso |
| 201 | Created | Recurso criado com sucesso |
| 204 | No Content | Sucesso sem conteúdo (ex: DELETE) |
| 400 | Bad Request | Requisição inválida (ex: dados insuficientes) |
| 404 | Not Found | Recurso não encontrado |
| 422 | Unprocessable Entity | Validação de entrada falhou |
| 500 | Internal Server Error | Erro interno do servidor |
| 503 | Service Unavailable | Banco de dados indisponível |

### Códigos de Erro Customizados

| Código | Descrição | HTTP Status |
|--------|-----------|-------------|
| `SYNTH_NOT_FOUND` | Synth não encontrado | 404 |
| `TOPIC_NOT_FOUND` | Topic guide não encontrado | 404 |
| `EXECUTION_NOT_FOUND` | Research execution não encontrada | 404 |
| `TRANSCRIPT_NOT_FOUND` | Transcrição não encontrada | 404 |
| `PRFAQ_NOT_FOUND` | PR-FAQ não encontrado | 404 |
| `AVATAR_NOT_FOUND` | Avatar não encontrado | 404 |
| `SUMMARY_NOT_FOUND` | Summary não encontrado | 404 |
| `JOB_NOT_FOUND` | Job não encontrado | 404 |
| `TAG_NOT_FOUND` | Tag não encontrada | 404 |
| `EXPERIMENT_NOT_FOUND` | Experimento não encontrado | 404 |
| `INTERVIEW_GUIDE_NOT_FOUND` | Interview guide não configurado | 422 |
| `SCORECARD_ESTIMATION_FAILED` | Estimativa de scorecard falhou | 500 |
| `NOT_ENOUGH_SYNTHS` | Synths insuficientes para auto-entrevista | 400 |
| `INVALID_QUERY` | Query SQL inválida | 422 |
| `INVALID_REQUEST` | Request inválido | 422 |
| `GENERATION_FAILED` | Geração falhou | 422 |
| `DATABASE_ERROR` | Erro de banco de dados | 503 |

---

## CORS

### Configuração

A API está configurada para aceitar requisições de qualquer origem em **desenvolvimento**:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Dev: all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Produção

Em produção, restringir a origens específicas:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

---

## Rate Limiting (Futuro)

Atualmente não há rate limiting implementado. Para produção, considerar:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.get("/synths/list")
@limiter.limit("100/minute")
async def list_synths():
    ...
```

---

## Exemplos de Uso

### JavaScript (Fetch API)

```javascript
// Listar synths
const response = await fetch('http://localhost:8000/synths/list?limit=10');
const data = await response.json();
console.log(data.data);

// Obter synth específico
const synth = await fetch('http://localhost:8000/synths/ynnasw');
const synthData = await synth.json();
console.log(synthData);

// Busca avançada
const searchResponse = await fetch('http://localhost:8000/synths/search', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    where_clause: "json_extract(demografia, '$.idade') > 30",
    limit: 20
  })
});
const searchData = await searchResponse.json();
console.log(searchData.data);

// Streaming SSE
const eventSource = new EventSource('http://localhost:8000/research/execute');
eventSource.addEventListener('turn', (e) => {
  const event = JSON.parse(e.data);
  console.log(`[${event.synth_id}] ${event.speaker}: ${event.text}`);
});
```

### Python (requests)

```python
import requests
import json

base_url = "http://localhost:8000"

# Listar synths
response = requests.get(f"{base_url}/synths/list", params={"limit": 10})
data = response.json()
print(data["data"])

# Obter synth específico
synth = requests.get(f"{base_url}/synths/ynnasw")
print(synth.json())

# Busca avançada
search_response = requests.post(
    f"{base_url}/synths/search",
    json={
        "where_clause": "json_extract(demografia, '$.idade') > 30",
        "limit": 20
    }
)
print(search_response.json()["data"])

# Download de avatar
avatar_response = requests.get(f"{base_url}/synths/ynnasw/avatar")
with open("avatar.png", "wb") as f:
    f.write(avatar_response.content)

# Streaming SSE
with requests.post(
    f"{base_url}/research/execute",
    json={
        "topic_name": "compra-amazon",
        "synth_count": 5,
        "max_turns": 6,
        "model": "gpt-xxxx"
    },
    stream=True
) as response:
    for line in response.iter_lines():
        if line:
            decoded = line.decode('utf-8')
            if decoded.startswith('data: '):
                event_data = json.loads(decoded[6:])
                print(event_data)
```

### cURL

```bash
# Listar synths
curl "http://localhost:8000/synths/list?limit=10"

# Obter synth específico
curl "http://localhost:8000/synths/ynnasw"

# Busca avançada
curl -X POST "http://localhost:8000/synths/search" \
  -H "Content-Type: application/json" \
  -d '{"where_clause": "json_extract(demografia, '\''$.idade'\'') > 30", "limit": 20}'

# Download de avatar
curl "http://localhost:8000/synths/ynnasw/avatar" -o avatar.png

# Download de summary
curl "http://localhost:8000/research/batch_compra-amazon_20251219_110534/summary" -o summary.md

# Listar topics
curl "http://localhost:8000/topics/list"

# Obter topic
curl "http://localhost:8000/topics/compra-amazon"

# Listar executions
curl "http://localhost:8000/research/list?status=completed"

# Listar PR-FAQs
curl "http://localhost:8000/prfaq/list"

# Health check
curl "http://localhost:8000/health"
```

---

## Deployment

### Desenvolvimento Local

```bash
# Iniciar com reload
./scripts/start_api.sh

# Ou
uv run uvicorn src.synth_lab.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Produção

```bash
# Múltiplos workers
uv run uvicorn src.synth_lab.api.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info

# Com Gunicorn (recomendado)
gunicorn src.synth_lab.api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Docker (Futuro)

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY . .
RUN pip install -e .
CMD ["uvicorn", "src.synth_lab.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Performance

### Benchmarks

| Endpoint | Latência p50 | Latência p95 | Throughput |
|----------|--------------|--------------|------------|
| GET /synths/list | 25ms | 50ms | 500 req/s |
| GET /synths/{id} | 15ms | 30ms | 800 req/s |
| POST /synths/search | 35ms | 80ms | 300 req/s |
| GET /synths/{id}/avatar | 20ms | 40ms | 600 req/s |
| POST /research/execute | N/A (streaming) | N/A | 10 concurrent |

### Otimizações

- **Paginação**: Limitar queries com LIMIT/OFFSET
- **Índices**: Campos frequentemente consultados indexados
- **Connection Pooling**: Thread-local connections
- **Streaming**: Não bloqueia servidor durante research longa
- **Async Jobs**: Background worker para tarefas pesadas

---

## Segurança

### Validação de Entrada

- Pydantic valida automaticamente todos os requests
- SQL injection prevenido por parametrized queries
- Whitelist de keywords em WHERE clauses

### Headers de Segurança (Futuro)

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["app.example.com"])
app.add_middleware(HTTPSRedirectMiddleware)
```

### Autenticação (Futuro)

```python
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.get("/synths/list")
async def list_synths(token: str = Depends(oauth2_scheme)):
    # Validate token
    ...
```

---

## Troubleshooting

### Servidor não inicia

```bash
# Verificar porta ocupada
lsof -i :8000

# Matar processo
kill -9 <PID>
```

### Banco de dados não encontrado

```bash
# Verificar se DB existe
# Conectar ao PostgreSQL
psql postgresql://synthlab:synthlab_dev@localhost:5432/synthlab

# Verificar tamanho do banco
SELECT pg_size_pretty(pg_database_size('synthlab'));

# Rodar migrações
alembic upgrade head
```

### CORS errors no navegador

Verificar configuração de CORS em `api/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Dev: all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### SSE não funciona

- Verificar que Content-Type é `text/event-stream`
- Cliente deve suportar SSE (`EventSource` em navegadores)
- Timeout de proxy/load balancer pode interromper conexão

---

## Próximos Passos

### Futuras Features

1. **Autenticação & Autorização**: OAuth2 + JWT
2. **Rate Limiting**: Proteção contra abuso
3. **Webhooks**: Notificações de eventos
4. **GraphQL**: API alternativa para queries complexas
5. **Métricas**: Prometheus + Grafana
6. **Caching**: Redis para queries frequentes
7. **CDN**: Servir avatares de CDN

### Melhorias de Performance

1. **Database Indexes**: Adicionar índices em campos JSON
2. **Query Optimization**: ANALYZE e otimizações de queries
3. **Connection Pooling**: Pool de conexões dedicado
4. **Load Balancing**: Múltiplas instâncias
5. **Horizontal Scaling**: Migrar para PostgreSQL

---

## Conclusão

A API REST do synth-lab oferece acesso completo e eficiente a todas as funcionalidades do sistema, com:

- **37 endpoints** bem documentados
- **Streaming SSE** para operações longas
- **Paginação** consistente
- **Validação automática** com Pydantic
- **Documentação interativa** em `/docs`
- **Pronto para produção** com otimizações

Para mais informações, consulte:
- [Documentação Swagger UI](http://localhost:8000/docs)
- [Arquitetura](arquitetura.md)
- [Modelo de Dados](database_model.md)
- [Camada de Serviços](services.md)
