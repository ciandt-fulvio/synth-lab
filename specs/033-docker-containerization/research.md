# Research: Docker Containerization

**Feature**: 033-docker-containerization
**Date**: 2026-01-20
**Status**: Complete

## Overview

Esta pesquisa consolida as melhores práticas para containerização do synth-lab em três ambientes: desenvolvimento (hot reload), teste (imagens de produção), e produção (Railway).

---

## 1. Docker Compose Profiles

### Decision: Usar profiles em único docker-compose.yml

**Rationale**: Profiles permitem gerenciar múltiplos ambientes (dev, test) em um único arquivo, eliminando duplicação e drift de configuração.

**Alternatives Considered**:
- Múltiplos arquivos (docker-compose.dev.yml, docker-compose.test.yml) - Rejeitado por duplicação
- Docker Compose override files - Menos explícito que profiles

### Pattern Definido

```yaml
services:
  # Core services (sempre iniciam - SEM profile)
  postgres:
    image: postgres:14-alpine

  # Dev-only services
  backend-dev:
    profiles: ["dev"]

  frontend-dev:
    profiles: ["dev"]

  # Test services
  backend-test:
    profiles: ["test"]

  frontend-test:
    profiles: ["test"]
```

### Comandos

```bash
# Desenvolvimento
docker compose --profile dev up

# Testes (E2E)
docker compose --profile test up

# Ambos (para debugging)
docker compose --profile dev --profile test up
```

---

## 2. Vite Hot Reload (HMR) em Docker

### Decision: Polling com CHOKIDAR_USEPOLLING

**Rationale**: Docker volumes não propagam eventos inotify do host, especialmente em macOS/WSL. Polling é a solução confiável.

**Alternatives Considered**:
- inotify nativo - Não funciona com volumes Docker
- watchman - Complexidade adicional sem benefício

### Configuração vite.config.ts

```typescript
export default defineConfig({
  server: {
    host: "0.0.0.0",  // Bind para acesso externo
    port: 8080,
    hmr: {
      clientPort: 8080,  // Porta exposta pelo Docker
      host: "localhost",
    },
    watch: {
      usePolling: true,
      interval: 100,
    },
  },
});
```

### Volume Mounts Necessários

```yaml
volumes:
  - ./frontend:/app
  - /app/node_modules  # Previne sobrescrita
environment:
  - CHOKIDAR_USEPOLLING=true
```

**Nota**: O volume anônimo `/app/node_modules` é crítico para preservar dependências compiladas para Linux.

---

## 3. Uvicorn Reload em Docker

### Decision: WATCHFILES_FORCE_POLLING=true

**Rationale**: Uvicorn usa watchfiles para detecção de mudanças, que também requer polling em Docker.

**Alternatives Considered**:
- watchgod (deprecated)
- inotify nativo - Mesmo problema que Vite

### Configuração

```yaml
services:
  backend-dev:
    command: >
      uvicorn synth_lab.api.main:app
      --host 0.0.0.0
      --port 8000
      --reload
      --reload-dir /app/src
      --reload-delay 0.25
    volumes:
      - ./src:/app/src:cached
    environment:
      - WATCHFILES_FORCE_POLLING=true
```

### Flags Importantes

| Flag | Propósito |
|------|-----------|
| `--reload` | Habilita auto-reload |
| `--reload-dir /app/src` | Limita diretório observado |
| `--reload-delay 0.25` | Delay entre detecção e reload |
| `--host 0.0.0.0` | Bind para acesso externo |

**Importante**: `--reload` e `--workers` são mutuamente exclusivos. Use `--workers` apenas em produção.

---

## 4. PostgreSQL Health Checks

### Decision: pg_isready com depends_on condition

**Rationale**: Garante que backend só inicia após PostgreSQL estar pronto para aceitar conexões.

### Configuração

```yaml
services:
  postgres:
    image: postgres:14-alpine
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-synthlab}"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s

  backend:
    depends_on:
      postgres:
        condition: service_healthy
```

### Variáveis de Ambiente

```yaml
environment:
  POSTGRES_USER: synthlab
  POSTGRES_PASSWORD: synthlab
  POSTGRES_DB: synthlab
```

---

## 5. Railway Docker Deployment

### Decision: Dockerfile builds (não pre-built images)

**Rationale**: O projeto já usa Dockerfile builds via railway.toml. Manter consistência e simplicidade.

**Alternatives Considered**:
- Pre-built images via GHCR - Mais complexo, benefício marginal para nosso caso
- Railpack (novo builder) - Menos controle que Dockerfile

### railway.toml Backend

```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "./Dockerfile"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

### railway.toml Frontend

```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "./Dockerfile"

[build.buildArgs]
VITE_API_URL = "${{VITE_API_URL}}"

[deploy]
healthcheckPath = "/"
healthcheckTimeout = 100
```

### Variáveis Cross-Service

Railway permite referenciar variáveis de outros serviços:

```
# No frontend
VITE_API_URL=https://${{Backend.RAILWAY_PUBLIC_DOMAIN}}

# No backend
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

### Porta Obrigatória

Railway injeta `PORT` automaticamente. Apps **devem** escutar nesta porta:

```python
import os
port = int(os.getenv("PORT", 8000))
uvicorn.run(app, host="0.0.0.0", port=port)
```

---

## 6. Estrutura de Arquivos Recomendada

### Docker Compose Unificado

```
docker/
├── docker-compose.yml          # Compose principal com profiles
├── .env.dev                    # Variáveis desenvolvimento
├── .env.test                   # Variáveis teste
├── backend/
│   ├── Dockerfile              # Multi-stage para dev/prod
│   └── entrypoint.sh           # Script de inicialização
├── frontend/
│   └── Dockerfile.dev          # Dev-only com hot reload
└── postgres/
    └── init-scripts/
        └── seed-test-data.sql  # Dados para ambiente test
```

### Decisão: Manter Dockerfiles na raiz para Railway

```
# Raiz do projeto (para Railway)
Dockerfile                      # Backend - Railway usa este
frontend/Dockerfile             # Frontend - Railway usa este

# docker/ directory (para desenvolvimento local)
docker/docker-compose.yml       # Compose com profiles
```

**Rationale**: Railway espera Dockerfiles na raiz do serviço. Evita configuração extra de `dockerfilePath`.

---

## 7. Resumo de Decisões

| Aspecto | Decisão | Justificativa |
|---------|---------|---------------|
| Compose strategy | Single file + profiles | Evita duplicação |
| Vite HMR | Polling (CHOKIDAR_USEPOLLING) | Único método confiável em Docker |
| Uvicorn reload | Polling (WATCHFILES_FORCE_POLLING) | Consistente com Vite |
| PostgreSQL wait | depends_on + healthcheck | Garante ordem de startup |
| Railway builds | Dockerfile builds | Já existente, mantém consistência |
| Dockerfile location | Raiz para Railway, docker/ para local | Compatibilidade Railway |

---

## 8. Issues Conhecidos e Mitigações

### CPU Alto com Polling

**Problema**: Polling consome mais CPU que inotify
**Mitigação**: Aumentar `interval` e limitar diretórios observados

### Container Não Para

**Problema**: `docker compose down` pode travar com Vite
**Mitigação**: `stop_grace_period: 1s` no service config

### node_modules Sobrescrito

**Problema**: Volume mount sobrescreve node_modules do container
**Mitigação**: Volume anônimo `/app/node_modules`

### HMR WebSocket Falha

**Problema**: Browser não conecta ao WebSocket
**Mitigação**: `hmr.clientPort` deve igualar porta exposta do Docker

---

## Sources

- [Docker Compose Profiles | Docker Docs](https://docs.docker.com/compose/profiles/)
- [Vite Server Options | Vite Docs](https://vite.dev/config/server-options)
- [Uvicorn Settings | Uvicorn Docs](https://www.uvicorn.org/settings/)
- [Railway Dockerfiles Guide](https://docs.railway.com/guides/dockerfiles)
- [Railway Config as Code](https://docs.railway.com/reference/config-as-code)
- [Railway PostgreSQL Guide](https://docs.railway.com/guides/postgresql)
- [Watchfiles Polling Issue #181](https://github.com/samuelcolvin/watchfiles/issues/181)
- [Vite Docker HMR Discussion #14007](https://github.com/vitejs/vite/discussions/14007)
