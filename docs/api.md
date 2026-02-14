# API REST - synth-lab

## Visão Geral

API REST construída com FastAPI. Documentação interativa disponível em `/docs` (Swagger UI) e `/redoc`.

- **Formato**: JSON
- **Streaming**: SSE para research executions
- **Paginação**: `?limit=50&offset=0&sort_by=created_at&sort_order=desc` em todos os endpoints de listagem

### Resposta de Paginação

```json
{
  "data": [...],
  "pagination": { "total": 100, "limit": 50, "offset": 0, "has_next": true }
}
```

### Resposta de Erro

```json
{
  "error": { "code": "SYNTH_NOT_FOUND", "message": "Synth com ID 'abc123' não encontrado" }
}
```

---

## Endpoints

### Health (2)

| Método | Path | Descrição |
|--------|------|-----------|
| GET | `/health` | Health check (status, version, environment) |
| GET | `/` | Info da API |

### Synths (5)

| Método | Path | Descrição |
|--------|------|-----------|
| GET | `/synths/list` | Listar synths (paginado, filtros) |
| GET | `/synths/{synth_id}` | Detalhes de um synth |
| POST | `/synths/search` | Busca avançada (WHERE clause ou SQL) |
| GET | `/synths/{synth_id}/avatar` | Download avatar PNG |
| GET | `/synths/fields` | Campos disponíveis para filtros |

### Experiments (11)

| Método | Path | Descrição |
|--------|------|-----------|
| POST | `/experiments` | Criar experimento |
| GET | `/experiments/list` | Listar (paginado, search, tag, sort) |
| GET | `/experiments/{id}` | Detalhes (inclui interviews) |
| PUT | `/experiments/{id}` | Atualizar nome/hipótese/descrição |
| DELETE | `/experiments/{id}` | Deletar experimento |
| PUT | `/experiments/{id}/scorecard` | Atualizar scorecard |
| POST | `/experiments/estimate-scorecard` | Estimar scorecard via IA (sem experimento) |
| POST | `/experiments/{id}/estimate-scorecard` | Estimar scorecard via IA (com experimento) |
| POST | `/experiments/{id}/interviews` | Criar entrevista |
| GET | `/experiments/{id}/interviews/auto` | Obter auto-entrevista |
| POST | `/experiments/{id}/interviews/auto` | Criar auto-entrevista (5 melhores + 5 piores) |

### Topics (3)

| Método | Path | Descrição |
|--------|------|-----------|
| GET | `/topics/list` | Listar topic guides |
| GET | `/topics/{topic_name}` | Detalhes do topic (script, files) |
| GET | `/topics/{topic_name}/research` | Research executions do topic |

### Research (7)

| Método | Path | Descrição |
|--------|------|-----------|
| GET | `/research/list` | Listar research executions |
| GET | `/research/{exec_id}` | Detalhes da execution |
| GET | `/research/{exec_id}/transcripts` | Listar transcrições |
| GET | `/research/{exec_id}/transcripts/{synth_id}` | Transcrição específica |
| POST | `/research/{exec_id}/summary/generate` | Gerar summary |
| POST | `/research/execute` | Executar research (batch de entrevistas) |
| GET | `/research/{exec_id}/stream` | Stream SSE de mensagens |

### PR-FAQ (3)

| Método | Path | Descrição |
|--------|------|-----------|
| GET | `/prfaq/list` | Listar PR-FAQs |
| GET | `/prfaq/{exec_id}` | Detalhes do PR-FAQ |
| GET | `/prfaq/{exec_id}/markdown` | Download PR-FAQ em Markdown |

### Tags (4)

| Método | Path | Descrição |
|--------|------|-----------|
| GET | `/tags` | Listar tags |
| POST | `/tags` | Criar tag |
| POST | `/tags/experiments/{id}/tags` | Adicionar tag a experimento |
| DELETE | `/tags/experiments/{id}/tags/{tag_name}` | Remover tag de experimento |

### Jobs (1)

| Método | Path | Descrição |
|--------|------|-----------|
| GET | `/jobs/{job_id}` | Status de job assíncrono |

---

## Códigos de Erro

| Código HTTP | Significado |
|-------------|-------------|
| 200 | OK |
| 201 | Created |
| 204 | No Content (DELETE) |
| 400 | Bad Request |
| 404 | Not Found |
| 422 | Validação falhou |
| 500 | Erro interno |
| 503 | Banco indisponível |

### Códigos Customizados

`SYNTH_NOT_FOUND`, `EXPERIMENT_NOT_FOUND`, `EXECUTION_NOT_FOUND`, `TRANSCRIPT_NOT_FOUND`, `PRFAQ_NOT_FOUND`, `TAG_NOT_FOUND`, `AVATAR_NOT_FOUND`, `JOB_NOT_FOUND`, `INVALID_QUERY`, `INVALID_REQUEST`, `GENERATION_FAILED`, `DATABASE_ERROR`, `NOT_ENOUGH_SYNTHS`, `SCORECARD_ESTIMATION_FAILED`

---

## Notas

- **Swagger UI**: `http://localhost:8000/docs` (documentação interativa completa com exemplos)
- **SSE**: Research execution stream via `EventSource` no frontend
- **Status de executions**: `pending` → `running` → `generating_summary` → `completed` | `failed`
