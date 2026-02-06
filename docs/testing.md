# Testing - synth-lab

## Estratégia

Multi-camadas: testes rápidos por padrão, testes com API real apenas quando explicitamente solicitados.

| Camada | Externos | Velocidade | Custo |
|--------|----------|------------|-------|
| **Unit tests** | Nenhum | Muito rápido | $0 |
| **Integration tests** | Mocked (OpenAI, S3, HTTP) + real DB | Rápido | $0 |
| **Contract tests** | Nenhum | Rápido | $0 |
| **Smoke tests** | REAL API calls | Lento (5-10s) | ~$0.02 |
| **E2E tests** | Playwright (full stack) | Moderado | $0 |

## Pytest Markers

| Marker | Propósito |
|--------|-----------|
| `integration` | Testes com APIs mockadas |
| `smoke` | Validação de caminho crítico |
| `real_api` | Testes com chamadas REAIS (custa dinheiro) |
| `slow` | Testes >5 segundos |
| `contract` | Validação de schema API |

## Comandos

```bash
# Default: testes rápidos (exclui real API)
make test

# Ou diretamente
pytest                        # Exclui real_api por padrão
pytest -m "not slow"          # Exclui lentos
pytest -m integration         # Apenas integration
pytest -m "real_api"          # Apenas smoke com API real (CI only)

# E2E
make test-e2e                 # Full: build + start + test + cleanup

# Smoke contra ambientes remotos
make test-smoke-staging
make test-smoke-production
```

## Mocking

### Fixtures centralizadas (`tests/fixtures/llm_mocks.py`)

| Fixture | Mocka |
|---------|-------|
| `mock_llm_client` | LLM client genérico |
| `mock_openai_client` | OpenAI chat completions |
| `mock_openai_image` | OpenAI DALL-E |
| `mock_s3_storage` | Operações S3 |
| `mock_http_image_download` | Downloads HTTP de imagens |

### Regras de Mock

| Componente | Dev | CI | Motivo |
|------------|-----|-----|--------|
| LLM calls | Mock | Mock | Rápido, grátis, determinístico |
| S3 | Mock | Mock | Sem custo, sem dependência |
| Database | Real (isolado) | Real (isolado) | Testa queries reais |
| Smoke tests | Skip (sem API key) | Real | Valida produção |

## Pre-Push Hook (Smart Mode)

O hook roda automaticamente em `git push origin main` com detecção inteligente de mudanças.

### Lógica de Skip

| Cenário | Build BE | Build FE | Unit Tests | E2E | Push Images |
|---------|----------|----------|------------|-----|-------------|
| Apenas docs | Skip | Skip | Skip | Skip | Skip |
| Apenas backend | Sim | Skip | Sim | Sim | BE only |
| Apenas frontend | Skip | Sim | Skip | Sim | FE only |
| Backend + Frontend | Sim | Sim | Sim | Sim | Ambos |
| Config mudou | Sim | Sim | Sim | Sim | Ambos |

### Performance

| Cenário | Antes | Agora | Economia |
|---------|-------|-------|----------|
| Apenas docs | 5-10 min | ~5 seg | 98% |
| Apenas backend | 5-10 min | 2-3 min | 60% |
| Apenas frontend | 5-10 min | 2-3 min | 60% |
| Config change | 5-10 min | 5-10 min | 0% |

### Cache Docker

O hook usa `--cache-from` com última imagem do GHCR para acelerar builds.

### Bypass (emergência)

```bash
git push origin main --no-verify
```

## Smoke Tests por Ambiente

**Staging** (`frontend/tests/e2e/smoke/critical-flows.spec.ts`):
- Com autenticação via `/auth/test-login`
- Testa navegação, criação de experimentos, etc.

**Production** (`frontend/tests/e2e/smoke/public-health.spec.ts`):
- Sem autenticação
- Health check backend, frontend carrega HTML, sem erros 5xx, tempos de resposta

## Troubleshooting

```bash
# Encontrar testes lentos
pytest --durations=10

# Verificar quais testes usam API real
grep -r "@pytest.mark.real_api" tests/

# Forçar full validation (commitar mudança em config)
touch docker/.env.dev && git add docker/.env.dev && git commit -m "chore: force validation"
```
