# API Contracts: Docker Containerization

Este feature não introduz novas APIs ou modifica contratos existentes.

## Reason

A containerização Docker é uma mudança puramente de infraestrutura que empacota o sistema existente sem modificar:

- Endpoints da API REST
- Schemas de request/response
- Protocolos de comunicação

## Existing APIs Preserved

Todas as APIs existentes continuam funcionando identicamente:

| API | Endpoint | Status |
|-----|----------|--------|
| Health Check | `GET /health` | Preservado |
| Experiments | `/experiments/*` | Preservado |
| Synths | `/synths/*` | Preservado |
| Explorations | `/explorations/*` | Preservado |
| Materials | `/materials/*` | Preservado |
| (todos os outros) | ... | Preservado |

## Container-Specific Endpoints

O health check existente (`/health`) será usado pelo Docker Compose e Railway para verificar disponibilidade:

```yaml
# docker-compose.yml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]

# railway.toml
healthcheckPath = "/health"
```

Nenhuma modificação necessária no endpoint - já retorna status adequado.
