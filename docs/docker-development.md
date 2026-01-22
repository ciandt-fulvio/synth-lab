# Docker Development Guide

Este guia descreve como usar Docker para desenvolvimento e testes no SynthLab.

## Visao Geral

O SynthLab utiliza Docker Compose com profiles para gerenciar diferentes ambientes:

| Profile | Proposito | Portas |
|---------|-----------|--------|
| `dev` | Desenvolvimento com hot reload | frontend: 8080, backend: 8000, postgres: 5432 |
| `test` | Testes E2E isolados | frontend: 8091, backend: 8001, postgres: 5433 |

## Pre-requisitos

- Docker ou Podman instalado
- Docker Compose v2 ou podman-compose

```bash
# Verificar instalacao
docker --version
docker compose version

# Ou com Podman
podman --version
podman-compose --version
```

## Ambiente de Desenvolvimento

### Iniciar

```bash
# Iniciar todos os servicos
make dev-up

# Ou diretamente com docker compose
docker compose -f docker/docker-compose.yml --profile dev up -d
```

Apos iniciar, acesse:
- **Frontend**: http://localhost:8080 (com HMR)
- **Backend**: http://localhost:8000/docs (com hot reload)
- **PostgreSQL**: localhost:5432

### Desenvolvimento com Hot Reload

O ambiente de desenvolvimento monta volumes do codigo fonte, permitindo que alteracoes sejam refletidas automaticamente:

**Backend (Python)**:
- Codigo fonte em `src/` e montado em `/app/src`
- uvicorn monitora alteracoes com `WATCHFILES_FORCE_POLLING=true`
- Alteracoes em arquivos `.py` recarregam o servidor automaticamente

**Frontend (TypeScript/React)**:
- Codigo fonte em `frontend/` e montado em `/app`
- Vite HMR ativado com `CHOKIDAR_USEPOLLING=true`
- Alteracoes em arquivos `.tsx`, `.ts`, `.css` sao refletidas instantaneamente

### Ver Logs

```bash
# Logs de todos os servicos
make dev-logs

# Logs de um servico especifico
docker compose -f docker/docker-compose.yml logs -f backend-dev
docker compose -f docker/docker-compose.yml logs -f frontend-dev
docker compose -f docker/docker-compose.yml logs -f postgres-dev
```

### Parar

```bash
make dev-down

# Ou diretamente
docker compose -f docker/docker-compose.yml --profile dev down
```

### Dados Persistentes

O PostgreSQL de desenvolvimento usa um volume nomeado (`synthlab-postgres-dev-data`) para persistir dados entre reinicializacoes. Para resetar:

```bash
# Parar e remover volume
docker compose -f docker/docker-compose.yml --profile dev down -v
```

## Ambiente de Testes

### Caracteristicas

O ambiente de testes difere do desenvolvimento:

| Aspecto | Desenvolvimento | Testes |
|---------|-----------------|--------|
| Codigo | Volume mounts (hot reload) | Copiado na imagem (producao) |
| Banco de dados | Persistente | Efemero (limpo a cada execucao) |
| Portas | 8080, 8000, 5432 | 8091, 8001, 5433 |
| Rede | `synthlab-dev-network` | `synthlab-test-network` |

### Executar Testes E2E

```bash
# Workflow completo: build, start, test, cleanup
make test-e2e
```

### Iniciar Ambiente para Debug

```bash
# Iniciar e manter rodando
make test-e2e-docker-up

# Ver logs
make test-e2e-docker-logs

# Executar testes manualmente
cd frontend && TEST_ENV=docker npm run test:e2e

# Parar quando terminar
make test-e2e-docker-down
```

## Estrutura de Arquivos Docker

```
docker/
├── docker-compose.yml       # Compose unificado com profiles
├── .env.dev                 # Variaveis para desenvolvimento
├── .env.test                # Variaveis para testes
├── backend/
│   └── Dockerfile.dev       # Dockerfile de desenvolvimento (com volume mounts)
├── frontend/
│   └── Dockerfile.dev       # Dockerfile de desenvolvimento (com HMR)
└── postgres/
    └── init-scripts/
        └── seed-test-data.sql  # Seed para ambiente de testes

Dockerfile                   # Producao backend (raiz do projeto)
frontend/Dockerfile          # Producao frontend
```

## Troubleshooting

### Portas em uso

```bash
# Verificar o que esta usando a porta
lsof -i :8000
lsof -i :8080

# Matar processos nas portas
make kill
```

### Problemas com Podman

```bash
# Reiniciar podman machine (macOS)
podman machine stop && podman machine start
```

### Hot reload nao funciona

1. Verificar se volumes estao montados corretamente:
   ```bash
   docker compose -f docker/docker-compose.yml --profile dev exec backend-dev ls -la /app/src
   ```

2. Verificar variaveis de ambiente:
   ```bash
   docker compose -f docker/docker-compose.yml --profile dev exec backend-dev env | grep WATCHFILES
   ```

### Erro de build no backend

Se o backend falhar com erro de `uv pip install -e .`, verifique se o Dockerfile.dev cria o placeholder `src/` antes da instalacao.

### Banco de dados nao conecta

Verificar se o PostgreSQL esta healthy:
```bash
docker compose -f docker/docker-compose.yml --profile dev ps
```

## Comandos Uteis

```bash
# Rebuild de um servico especifico
docker compose -f docker/docker-compose.yml --profile dev up -d --build backend-dev

# Executar comando em container
docker compose -f docker/docker-compose.yml exec backend-dev python -c "print('hello')"

# Acessar shell do container
docker compose -f docker/docker-compose.yml exec backend-dev bash

# Ver status dos containers
docker compose -f docker/docker-compose.yml --profile dev ps

# Limpar tudo (imagens, volumes, networks)
docker compose -f docker/docker-compose.yml --profile dev down -v --rmi local
```

## Deploy para Railway

O ambiente de producao no Railway usa os mesmos Dockerfiles do ambiente de teste (sem volume mounts):

- `Dockerfile` (raiz) - Backend Python
- `frontend/Dockerfile` - Frontend React

O Railway injeta a variavel `PORT` automaticamente. Os Dockerfiles estao configurados para usar `${PORT:-8000}` como fallback.

Para mais detalhes sobre deploy, veja a documentacao do Railway e os arquivos `railway.toml` e `frontend/railway.toml`.
