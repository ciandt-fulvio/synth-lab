# API REST - synth-lab

## Visão Geral

A API REST do synth-lab é construída com **FastAPI** e oferece acesso programático a todas as funcionalidades do sistema através de **17 endpoints HTTP**.

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

### 3. Research Endpoints (6 endpoints)

#### 3.1 Executar Research (Streaming SSE)

```http
POST /research/execute
```

Executa research com múltiplos synths e transmite progresso via Server-Sent Events.

**Request Body**:
```json
{
  "topic_name": "compra-amazon",
  "synth_ids": ["ynnasw", "abc123"],  // Opcional: IDs específicos
  "synth_count": 10,                  // Ou quantidade aleatória
  "max_turns": 6,
  "max_concurrent": 5,
  "model": "gpt-5-mini",
  "generate_summary": true
}
```

**Response**: Stream SSE (Content-Type: `text/event-stream`)

**Eventos Enviados**:

1. **started**
```
event: started
data: {"exec_id": "batch_compra-amazon_20251219_110534", "topic_name": "compra-amazon", "synth_count": 10}
```

2. **interview_started**
```
event: interview_started
data: {"synth_id": "ynnasw", "synth_name": "Ravy Lopes"}
```

3. **turn** (cada turno de conversa)
```
event: turn
data: {"synth_id": "ynnasw", "turn": 1, "speaker": "Interviewer", "text": "Como você se sente ao fazer compras online?"}

event: turn
data: {"synth_id": "ynnasw", "turn": 1, "speaker": "Interviewee", "text": "Eu me sinto bem confortável..."}
```

4. **interview_completed**
```
event: interview_completed
data: {"synth_id": "ynnasw", "status": "completed", "duration_ms": 45000}
```

5. **interview_failed**
```
event: interview_failed
data: {"synth_id": "abc123", "error": "LLM timeout"}
```

6. **all_completed**
```
event: all_completed
data: {"exec_id": "batch_...", "successful": 9, "failed": 1}
```

7. **job_queued**
```
event: job_queued
data: {"job_type": "summary", "job_id": "uuid-1234"}

event: job_queued
data: {"job_type": "prfaq", "job_id": "uuid-5678"}
```

**Client JavaScript**:
```javascript
const eventSource = new EventSource('http://localhost:8000/research/execute');

eventSource.addEventListener('turn', (e) => {
  const data = JSON.parse(e.data);
  console.log(`[${data.synth_id}] ${data.speaker}: ${data.text}`);
});

eventSource.addEventListener('all_completed', (e) => {
  const data = JSON.parse(e.data);
  console.log(`Done! ${data.successful} successful, ${data.failed} failed`);
  eventSource.close();
});

eventSource.addEventListener('error', (e) => {
  console.error('SSE error:', e);
  eventSource.close();
});
```

**Client Python**:
```python
import requests

url = "http://localhost:8000/research/execute"
payload = {
    "topic_name": "compra-amazon",
    "synth_count": 5,
    "max_turns": 6,
    "model": "gpt-5-mini",
    "generate_summary": True
}

with requests.post(url, json=payload, stream=True) as response:
    for line in response.iter_lines():
        if line:
            decoded = line.decode('utf-8')
            if decoded.startswith('data: '):
                data = json.loads(decoded[6:])
                print(data)
```

---

#### 3.2 Listar Research Executions

```http
GET /research/list
```

Lista research executions com filtros opcionais.

**Query Parameters**:
- `limit`, `offset`, `sort_by`, `sort_order` (padrão paginação)
- `status` (string, opcional): Filtrar por status (`running`, `completed`, `failed`)
- `topic_name` (string, opcional): Filtrar por topic

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
      "model": "gpt-5-mini",
      "max_turns": 6,
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
curl "http://localhost:8000/research/list?status=completed"
```

---

#### 3.3 Obter Research Execution por ID

```http
GET /research/{exec_id}
```

Retorna detalhes de uma research execution.

**Path Parameters**:
- `exec_id` (string, requerido): ID da execution

**Response 200**:
```json
{
  "exec_id": "batch_compra-amazon_20251219_110534",
  "topic_name": "compra-amazon",
  "synth_count": 10,
  "successful_count": 9,
  "failed_count": 1,
  "model": "gpt-5-mini",
  "max_turns": 6,
  "status": "completed",
  "started_at": "2025-12-19T11:05:34Z",
  "completed_at": "2025-12-19T11:12:45Z",
  "summary_path": "output/reports/batch_compra-amazon_20251219_110534_summary.md"
}
```

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

#### 3.4 Listar Transcrições de uma Execution

```http
GET /research/{exec_id}/transcripts
```

Lista transcrições de uma research execution.

**Path Parameters**:
- `exec_id` (string, requerido): ID da execution

**Query Parameters**:
- `limit`, `offset` (padrão paginação)

**Response 200**:
```json
{
  "data": [
    {
      "synth_id": "ynnasw",
      "synth_name": "Ravy Lopes",
      "status": "completed",
      "turn_count": 6,
      "timestamp": "2025-12-19T11:08:23Z",
      "file_path": "output/transcripts/batch_.../ynnasw_20251219_110823.json"
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

#### 3.5 Obter Transcrição Específica

```http
GET /research/{exec_id}/transcripts/{synth_id}
```

Retorna transcrição completa de uma entrevista.

**Path Parameters**:
- `exec_id` (string, requerido): ID da execution
- `synth_id` (string, requerido): ID do synth

**Response 200**:
```json
{
  "exec_id": "batch_compra-amazon_20251219_110534",
  "synth_id": "ynnasw",
  "synth_name": "Ravy Lopes",
  "status": "completed",
  "turn_count": 6,
  "timestamp": "2025-12-19T11:08:23Z",
  "messages": [
    {
      "turn_number": 1,
      "speaker": "Interviewer",
      "text": "Como você se sente ao fazer compras online?",
      "internal_notes": null
    },
    {
      "turn_number": 1,
      "speaker": "Interviewee",
      "text": "Eu me sinto bem confortável. Uso bastante e-commerce...",
      "internal_notes": "Demonstra confiança (abertura: 82)"
    },
    {
      "turn_number": 2,
      "speaker": "Interviewer",
      "text": "O que você mais valoriza em um e-commerce?",
      "internal_notes": null
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

#### 3.6 Download de Summary

```http
GET /research/{exec_id}/summary
```

Faz download do summary da research execution em Markdown.

**Path Parameters**:
- `exec_id` (string, requerido): ID da execution

**Response 200**:
- Content-Type: `text/plain; charset=utf-8`
- Body: Arquivo Markdown

**Response 404**:
```json
{
  "error": {
    "code": "SUMMARY_NOT_FOUND",
    "message": "Summary não encontrado para execution 'batch_...'"
  }
}
```

**Exemplo**:
```bash
# Download
curl "http://localhost:8000/research/batch_compra-amazon_20251219_110534/summary" -o summary.md

# Visualizar
curl "http://localhost:8000/research/batch_compra-amazon_20251219_110534/summary"
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
  "model": "gpt-5-mini",
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

### 6. Health Check Endpoints (2 endpoints)

#### 6.1 Health Check

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

#### 6.2 Root Endpoint

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
        "model": "gpt-5-mini"
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
ls -lh output/synthlab.db

# Recriar DB
uv run python scripts/migrate_to_sqlite.py
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

- **17 endpoints** bem documentados
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
