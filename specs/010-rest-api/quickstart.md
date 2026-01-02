# Quickstart: synth-lab REST API

**Feature**: 010-rest-api | **Date**: 2025-12-19

## Pré-requisitos

- Python 3.13+
- uv (gerenciador de pacotes)
- OpenAI API key configurada em `OPENAI_API_KEY`

## Instalação

```bash
# Clone o repositório (se ainda não tiver)
git clone https://github.com/seu-usuario/synth-lab.git
cd synth-lab

# Checkout da branch da feature
git checkout 010-rest-api

# Instale as dependências
uv pip install -e .
```

## Migração de Dados

Execute o script de migração para criar o banco PostgreSQL:

```bash
uv run python scripts/migrate_to_postgresql.py
```

Isso cria `output/synthlab.db` com os dados existentes.

## Iniciando o Servidor

```bash
# Iniciar o servidor API
uv run uvicorn synth_lab.api.main:app --host 0.0.0.0 --port 8000 --reload

# Ou usando o script de conveniência
./scripts/start_api.sh
```

A API estará disponível em:
- **Base URL**: http://localhost:8000
- **Documentação Interativa (Swagger)**: http://localhost:8000/docs
- **Documentação Alternativa (ReDoc)**: http://localhost:8000/redoc

## Exemplos de Uso

### Listar Synths

```bash
# Lista todos os synths
curl http://localhost:8000/synths/list

# Com paginação
curl "http://localhost:8000/synths/list?limit=10&offset=0"

# Selecionando campos específicos
curl "http://localhost:8000/synths/list?fields=id,nome,arquetipo"
```

### Buscar Synth por ID

```bash
curl http://localhost:8000/synths/ynnasw
```

### Busca Avançada

```bash
# Busca com WHERE clause
curl -X POST http://localhost:8000/synths/search \
  -H "Content-Type: application/json" \
  -d '{"where_clause": "idade > 30"}'

# Busca com query completa
curl -X POST http://localhost:8000/synths/search \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT id, nome FROM synths WHERE arquetipo LIKE '\''%Nordeste%'\'' LIMIT 5"}'
```

### Avatar do Synth

```bash
# Baixar avatar como PNG
curl http://localhost:8000/synths/ynnasw/avatar -o avatar.png
```

### Listar Topic Guides

```bash
curl http://localhost:8000/topics/list
```

### Detalhes do Topic Guide

```bash
curl http://localhost:8000/topics/compra-amazon
```

### Executar Pesquisa

```bash
# Executar pesquisa com 5 synths aleatórios
curl -X POST http://localhost:8000/research/execute \
  -H "Content-Type: application/json" \
  -d '{
    "topic_name": "compra-amazon",
    "synth_count": 5,
    "max_turns": 6,
    "generate_summary": true
  }'

# Executar com synths específicos
curl -X POST http://localhost:8000/research/execute \
  -H "Content-Type: application/json" \
  -d '{
    "topic_name": "compra-amazon",
    "synth_ids": ["ynnasw", "abc123"],
    "max_turns": 6
  }'
```

### Consultar Execução

```bash
# Metadados da execução
curl http://localhost:8000/research/batch_compra-amazon_20251219_082053

# Lista de transcrições
curl http://localhost:8000/research/batch_compra-amazon_20251219_082053/transcripts

# Transcrição específica
curl http://localhost:8000/research/batch_compra-amazon_20251219_082053/transcripts/ynnasw

# Resumo da pesquisa (Markdown)
curl http://localhost:8000/research/batch_compra-amazon_20251219_082053/summary
```

### Gerar PR-FAQ

```bash
# Gerar PR-FAQ de uma execução
curl -X POST http://localhost:8000/prfaq/generate \
  -H "Content-Type: application/json" \
  -d '{"exec_id": "batch_compra-amazon_20251219_082053"}'

# Obter PR-FAQ em Markdown
curl http://localhost:8000/prfaq/batch_compra-amazon_20251219_082053/markdown
```

### Listar PR-FAQs

```bash
curl http://localhost:8000/prfaq/list
```

## Usando com Python

```python
import httpx

BASE_URL = "http://localhost:8000"

# Listar synths
response = httpx.get(f"{BASE_URL}/synths/list")
synths = response.json()
print(f"Total de synths: {synths['pagination']['total']}")

# Buscar synth específico
synth = httpx.get(f"{BASE_URL}/synths/ynnasw").json()
print(f"Nome: {synth['nome']}")
print(f"Idade: {synth['demografia']['idade']}")

# Executar pesquisa
result = httpx.post(
    f"{BASE_URL}/research/execute",
    json={
        "topic_name": "compra-amazon",
        "synth_count": 3,
        "generate_summary": True
    }
).json()
print(f"Execução iniciada: {result['exec_id']}")
```

## Tratamento de Erros

Todos os erros seguem o formato:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Mensagem descritiva",
    "details": {}
  }
}
```

### Códigos de Erro Comuns

| Código | HTTP Status | Descrição |
|--------|-------------|-----------|
| `SYNTH_NOT_FOUND` | 404 | Synth não existe |
| `TOPIC_NOT_FOUND` | 404 | Topic guide não existe |
| `EXECUTION_NOT_FOUND` | 404 | Execução não existe |
| `PRFAQ_NOT_FOUND` | 404 | PR-FAQ não existe |
| `INVALID_QUERY` | 422 | Query SQL inválida ou insegura |
| `GENERATION_FAILED` | 422 | Falha na geração (LLM, validação) |
| `DATABASE_ERROR` | 503 | Erro de acesso ao banco |

## CLI (Comandos Existentes)

Os comandos CLI continuam funcionando:

```bash
# Pesquisa via CLI
uv run python -m synth_lab research batch \
  --topic compra-amazon \
  --synth-count 5 \
  --max-turns 6

# Gerar PR-FAQ via CLI
uv run python -m synth_lab research-prfaq generate \
  --exec-id batch_compra-amazon_20251219_082053

# Listar synths via CLI
uv run python -m synth_lab listsynth
```

## Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `OPENAI_API_KEY` | API key do OpenAI | (obrigatório) |
| `SYNTHLAB_DB_PATH` | Caminho do banco PostgreSQL | `output/synthlab.db` |
| `SYNTHLAB_LOG_LEVEL` | Nível de log | `INFO` |
| `SYNTHLAB_DEFAULT_MODEL` | Modelo LLM padrão | `gpt-5-mini` |

## Estrutura de Diretórios

```
output/
├── synthlab.db           # Banco de dados PostgreSQL
├── synths/
│   ├── synths.json       # Backup JSON (source of truth original)
│   └── avatar/           # Imagens de avatar
├── transcripts/          # Transcrições de entrevistas
├── traces/               # Traces de execução
└── reports/              # Resumos e PR-FAQs

data/topic_guides/
└── {topic_name}/         # Diretórios de topic guides
    ├── script.json       # Script de entrevista
    ├── summary.md        # Contexto
    └── *.png             # Screenshots
```

## Próximos Passos

1. Explore a documentação interativa em http://localhost:8000/docs
2. Teste os endpoints com os exemplos acima
3. Integre com seu sistema usando as APIs REST
4. Para contribuir, veja o guia de desenvolvimento em `CONTRIBUTING.md`
