# Proposta de APIs - synth-lab

## Contexto

O synth-lab possui três domínios principais:
1. **Synths**: Personas sintéticas brasileiras com dados demográficos, psicográficos e tecnológicos
2. **Research**: Entrevistas de UX research com synths sobre tópicos específicos
3. **PR-FAQ**: Documentos estratégicos gerados a partir de pesquisas (Amazon Working Backwards)

---

## APIs Propostas

### 1. **Synths APIs** (4 endpoints)

| API | Método | Descrição |
|-----|--------|-----------|
| `synths/list` | GET | Lista todos os synths com paginação e campos selecionáveis |
| `synths/{id}` | GET | Detalhes completos de um synth específico |
| `synths/search` | POST | Busca avançada com filtros (WHERE clause ou full query DuckDB) |
| `synths/{id}/avatar` | GET | Retorna a imagem de avatar do synth |
| `synths/{id}/research` | GET | Lista todas as pesquisas em que o synth participou |

### 2. **Topic Guides APIs** (2 endpoints)

| API | Método | Descrição |
|-----|--------|-----------|
| `topics/list` | GET | Lista todos os topic guides disponíveis com metadados |
| `topics/{name}` | GET | Detalhes de um topic guide (script, contexto, arquivos) |
| `topics/{name}/research` | GET | Lista todas as pesquisas executadas sobre este tópico |

### 3. **Research Executions APIs** (6 endpoints)

| API | Método | Descrição |
|-----|--------|-----------|
| `research/{exec_id}` | GET | Detalhes de uma execução específica (metadados + summary) |
| `research/{exec_id}/transcripts` | GET | Lista transcrições da pesquisa |
| `research/{exec_id}/transcripts/{synth_id}` | GET | Transcrição específica de um synth na pesquisa |
| `research/{exec_id}/summary` | GET | Retorna o relatório de síntese (Markdown) |
| `research/execute` | POST | Executa nova pesquisa (N synths, onde N≥1) |
| `research/{exec_id}/synths` | GET | Lista todos os synths que participaram da pesquisa |
| `research/{exec_id}/prfaq` | GET | Retorna o PR-FAQ gerado para esta pesquisa (se existir) |

### 4. **PR-FAQ APIs** (3 endpoints)

| API | Método | Descrição |
|-----|--------|-----------|
| `prfaq/list` | GET | Lista todos os PR-FAQs gerados |
| `prfaq/{exec_id}/markdown` | GET | Retorna PR-FAQ em formato Markdown |
| `prfaq/generate` | POST | Gera novo PR-FAQ a partir de um exec_id de pesquisa |


---

---

## Notas sobre Unificação Batch/Individual

**Decisão**: Pesquisa individual passa a ser uma execução com `synth_count=1`

- Identificador único: `{exec_id}` (não mais batch_id)
- Mesma estrutura de dados e endpoints
- Mesmo fluxo de geração de summary
- Transcrições acessíveis via `/{exec_id}/transcripts/{synth_id}`

---

## Modelo de Erros e Status Codes

### Estrutura Padrão de Erro

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Mensagem legível",
    "details": {
      "field": "nome_campo",
      "reason": "Motivo específico"
    }
  }
}
```

### Status Codes

| Código | Cenário |
|--------|---------|
| **200** | Sucesso (GET, POST com resposta) |
| **201** | Recurso criado (POST) |
| **204** | Sucesso sem conteúdo |
| **400** | Request inválido (body malformado, parâmetros inválidos) |
| **404** | Recurso não encontrado |
| **422** | Validação falhou (campos válidos mas valores incorretos) |
| **500** | Erro interno do servidor |
| **503** | Serviço indisponível (LLM timeout, database offline) |

### Códigos de Erro

| Código | Descrição |
|--------|-----------|
| `SYNTH_NOT_FOUND` | Synth ID não existe |
| `TOPIC_NOT_FOUND` | Topic guide não existe |
| `EXECUTION_NOT_FOUND` | Execution ID não existe |
| `PRFAQ_NOT_FOUND` | PR-FAQ não existe |
| `INVALID_QUERY` | Query SQL inválida ou insegura |
| `INVALID_FILTERS` | Filtros malformados |
| `TRANSCRIPT_NOT_FOUND` | Transcrição não existe |
| `GENERATION_FAILED` | Falha na geração (LLM, validação) |
| `DATABASE_ERROR` | Erro de acesso ao banco |

---

## Especificação de Request/Response

### 1. Synths APIs

#### `GET /synths/list`

**Query Parameters:**
```typescript
{
  limit?: number;          // Default: 50, Max: 200
  offset?: number;         // Default: 0
  fields?: string[];       // Campos a retornar (ex: ["id", "nome", "arquetipo"])
  sort_by?: string;        // Campo para ordenação (default: "created_at")
  sort_order?: "asc"|"desc"; // Default: "desc"
}
```

**Response 200:**
```json
{
  "data": [
    {
      "id": "ynnasw",
      "nome": "Ravy Lopes",
      "arquetipo": "Adulto Nordeste Social",
      "descricao": "Homem de 43 anos...",
      "link_photo": "https://...",
      "created_at": "2025-12-18T16:55:43.384958+00:00",
      "version": "2.0.0"
      // + campos adicionais se especificados em 'fields'
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

---

#### `GET /synths/{id}`

**Path Parameters:**
- `id`: string (6 caracteres alfanuméricos)

**Response 200:**
```json
{
  "id": "ynnasw",
  "nome": "Ravy Lopes",
  "arquetipo": "Adulto Nordeste Social",
  "descricao": "...",
  "link_photo": "https://...",
  "created_at": "2025-12-18T16:55:43.384958+00:00",
  "version": "2.0.0",
  "demografia": { /* objeto completo */ },
  "psicografia": { /* objeto completo */ },
  "deficiencias": { /* objeto completo */ },
  "capacidades_tecnologicas": { /* objeto completo */ }
}
```

**Response 404:**
```json
{
  "error": {
    "code": "SYNTH_NOT_FOUND",
    "message": "Synth com ID 'ynnasw' não encontrado"
  }
}
```

---

#### `POST /synths/search`

**Request Body:**
```json
{
  "where_clause": "idade > 30 AND regiao = 'Sudeste'",
  "limit": 50,
  "offset": 0,
  "fields": ["id", "nome", "idade"]
}
```

**Alternativa (full query):**
```json
{
  "query": "SELECT id, nome FROM synths WHERE idade BETWEEN 25 AND 40 LIMIT 10"
}
```

**Response 200:**
```json
{
  "data": [ /* lista de synths */ ],
  "pagination": {
    "total": 45,
    "limit": 50,
    "offset": 0
  }
}
```

**Response 422:**
```json
{
  "error": {
    "code": "INVALID_QUERY",
    "message": "Query contém operações não permitidas (INSERT, DELETE)",
    "details": {
      "detected": "DELETE"
    }
  }
}
```

---

#### `GET /synths/{id}/avatar`

**Path Parameters:**
- `id`: string

**Response 200:**
- Content-Type: `image/png`
- Body: Imagem binária

**Response 404:**
```json
{
  "error": {
    "code": "SYNTH_NOT_FOUND",
    "message": "Avatar não encontrado para synth 'ynnasw'"
  }
}
```

---

#### `GET /synths/{id}/research`

**Path Parameters:**
- `id`: string

**Query Parameters:**
```typescript
{
  limit?: number;
  offset?: number;
}
```

**Response 200:**
```json
{
  "synth_id": "ynnasw",
  "synth_name": "Ravy Lopes",
  "executions": [
    {
      "exec_id": "batch_compra-amazon_20251219_082053",
      "topic_name": "compra-amazon",
      "executed_at": "2025-12-19T08:20:53+00:00",
      "status": "completed",
      "has_transcript": true
    }
  ],
  "pagination": {
    "total": 3,
    "limit": 50,
    "offset": 0
  }
}
```

---

### 2. Topic Guides APIs

#### `GET /topics/list`

**Query Parameters:**
```typescript
{
  limit?: number;
  offset?: number;
}
```

**Response 200:**
```json
{
  "data": [
    {
      "name": "compra-amazon",
      "display_name": "Compra Amazon",
      "description": "Contexto sobre compra na Amazon",
      "question_count": 8,
      "file_count": 5,
      "created_at": "2025-12-01T10:00:00+00:00",
      "updated_at": "2025-12-15T14:30:00+00:00"
    }
  ],
  "pagination": {
    "total": 12,
    "limit": 50,
    "offset": 0
  }
}
```

---

#### `GET /topics/{name}`

**Path Parameters:**
- `name`: string (nome do diretório do topic guide)

**Response 200:**
```json
{
  "name": "compra-amazon",
  "display_name": "Compra Amazon",
  "summary": {
    "context_description": "Contexto sobre...",
    "files": [
      {
        "filename": "01_homepage.PNG",
        "content_hash": "a3f5d8...",
        "description": "Captura da homepage da Amazon"
      }
    ]
  },
  "script": [
    {
      "id": 1,
      "ask": "Como você se sente ao...",
      "context_examples": {
        "positive": "...",
        "negative": "...",
        "neutral": "..."
      }
    }
  ],
  "metadata": {
    "question_count": 8,
    "file_count": 5,
    "created_at": "2025-12-01T10:00:00+00:00"
  }
}
```

**Response 404:**
```json
{
  "error": {
    "code": "TOPIC_NOT_FOUND",
    "message": "Topic guide 'compra-amazon' não encontrado"
  }
}
```

---

#### `GET /topics/{name}/research`

**Path Parameters:**
- `name`: string

**Query Parameters:**
```typescript
{
  limit?: number;
  offset?: number;
}
```

**Response 200:**
```json
{
  "topic_name": "compra-amazon",
  "executions": [
    {
      "exec_id": "batch_compra-amazon_20251219_082053",
      "synth_count": 10,
      "executed_at": "2025-12-19T08:20:53+00:00",
      "status": "completed",
      "has_summary": true,
      "has_prfaq": true
    }
  ],
  "pagination": {
    "total": 5,
    "limit": 50,
    "offset": 0
  }
}
```

---

### 3. Research Executions APIs

#### `GET /research/{exec_id}`

**Path Parameters:**
- `exec_id`: string

**Response 200:**
```json
{
  "exec_id": "batch_compra-amazon_20251219_082053",
  "topic_name": "compra-amazon",
  "metadata": {
    "synth_count": 10,
    "successful_count": 9,
    "failed_count": 1,
    "executed_at": "2025-12-19T08:20:53+00:00",
    "completed_at": "2025-12-19T08:45:12+00:00",
    "model": "gpt-5-mini",
    "max_turns": 6,
    "status": "completed"
  },
  "summary_available": true,
  "prfaq_available": false
}
```

**Response 404:**
```json
{
  "error": {
    "code": "EXECUTION_NOT_FOUND",
    "message": "Execution 'batch_...' não encontrada"
  }
}
```

---

#### `GET /research/{exec_id}/transcripts`

**Path Parameters:**
- `exec_id`: string

**Response 200:**
```json
{
  "exec_id": "batch_compra-amazon_20251219_082053",
  "transcripts": [
    {
      "synth_id": "ynnasw",
      "synth_name": "Ravy Lopes",
      "turn_count": 6,
      "timestamp": "2025-12-19T08:25:34-03:00",
      "status": "completed"
    }
  ],
  "total": 9
}
```

---

#### `GET /research/{exec_id}/transcripts/{synth_id}`

**Path Parameters:**
- `exec_id`: string
- `synth_id`: string

**Response 200:**
```json
{
  "metadata": {
    "exec_id": "batch_compra-amazon_20251219_082053",
    "synth_id": "ynnasw",
    "synth_name": "Ravy Lopes",
    "topic_guide": "compra-amazon",
    "model": "gpt-5-mini",
    "max_turns": 6,
    "total_turns": 6,
    "timestamp": "2025-12-19T08:25:34-03:00"
  },
  "messages": [
    {
      "speaker": "Interviewer",
      "text": "Como você...",
      "internal_notes": "Notas estratégicas..."
    }
  ]
}
```

**Response 404:**
```json
{
  "error": {
    "code": "TRANSCRIPT_NOT_FOUND",
    "message": "Transcrição não encontrada para synth 'ynnasw' na execução 'batch_...'"
  }
}
```

---

#### `GET /research/{exec_id}/summary`

**Path Parameters:**
- `exec_id`: string

**Response 200:**
- Content-Type: `text/markdown`
- Body: Conteúdo Markdown do relatório

**Response 404:**
```json
{
  "error": {
    "code": "EXECUTION_NOT_FOUND",
    "message": "Summary não encontrado para execução 'batch_...'"
  }
}
```

---

#### `POST /research/execute`

**Request Body:**
```json
{
  "topic_name": "compra-amazon",
  "synth_ids": ["ynnasw", "abc123"],  // Opcional: se omitido, seleciona aleatório
  "synth_count": 10,                  // Obrigatório se synth_ids não fornecido
  "max_turns": 6,
  "max_concurrent": 10,
  "model": "gpt-5-mini",
  "generate_summary": true
}
```

**Response 201:**
```json
{
  "exec_id": "batch_compra-amazon_20251219_110534",
  "status": "running",
  "topic_name": "compra-amazon",
  "synth_count": 10,
  "started_at": "2025-12-19T11:05:34+00:00"
}
```

**Response 422:**
```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Deve fornecer 'synth_ids' ou 'synth_count'",
    "details": {
      "fields": ["synth_ids", "synth_count"]
    }
  }
}
```

---

#### `GET /research/{exec_id}/synths`

**Path Parameters:**
- `exec_id`: string

**Response 200:**
```json
{
  "exec_id": "batch_compra-amazon_20251219_082053",
  "synths": [
    {
      "id": "ynnasw",
      "nome": "Ravy Lopes",
      "arquetipo": "Adulto Nordeste Social",
      "has_transcript": true,
      "status": "completed"
    }
  ],
  "total": 9
}
```

---

#### `GET /research/{exec_id}/prfaq`

**Path Parameters:**
- `exec_id`: string

**Response 200:**
```json
{
  "exec_id": "batch_compra-amazon_20251219_082053",
  "prfaq_available": true,
  "generated_at": "2025-12-19T09:30:00+00:00"
}
```

**Response 404:**
```json
{
  "error": {
    "code": "PRFAQ_NOT_FOUND",
    "message": "PR-FAQ não foi gerado para execução 'batch_...'"
  }
}
```

---

### 4. PR-FAQ APIs

#### `GET /prfaq/list`

**Query Parameters:**
```typescript
{
  limit?: number;
  offset?: number;
}
```

**Response 200:**
```json
{
  "data": [
    {
      "exec_id": "batch_compra-amazon_20251219_082053",
      "topic_name": "compra-amazon",
      "press_release": {
        "headline": "Amazon's SmartShop...",
        "one_liner": "Enhance your shopping..."
      },
      "faq_count": 10,
      "generated_at": "2025-12-19T09:30:00+00:00",
      "validation_status": "valid",
      "confidence_score": 0.92
    }
  ],
  "pagination": {
    "total": 8,
    "limit": 50,
    "offset": 0
  }
}
```

---

#### `GET /prfaq/{exec_id}/markdown`

**Path Parameters:**
- `exec_id`: string

**Response 200:**
- Content-Type: `text/markdown`
- Body: Conteúdo Markdown do PR-FAQ

**Response 404:**
```json
{
  "error": {
    "code": "PRFAQ_NOT_FOUND",
    "message": "PR-FAQ não encontrado para execução 'batch_...'"
  }
}
```

---

#### `POST /prfaq/generate`

**Request Body:**
```json
{
  "exec_id": "batch_compra-amazon_20251219_082053",
  "model": "gpt-5-mini"
}
```

**Response 201:**
```json
{
  "exec_id": "batch_compra-amazon_20251219_082053",
  "status": "generated",
  "generated_at": "2025-12-19T10:15:22+00:00",
  "validation_status": "valid",
  "confidence_score": 0.92
}
```

**Response 422:**
```json
{
  "error": {
    "code": "GENERATION_FAILED",
    "message": "Falha ao gerar PR-FAQ: summary não encontrado",
    "details": {
      "reason": "missing_summary"
    }
  }
}
```

---

## Próximos Passos

1. ✅ Campos de request/response definidos
2. Definir estratégia de paginação (cursor-based vs offset?)
3. ✅ Modelo de erros e status codes definidos
4. Escolher framework (FastAPI recomendado)
5. Implementar camada de service entre API e módulos existentes
