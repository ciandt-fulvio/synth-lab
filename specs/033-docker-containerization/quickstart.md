# Quickstart: Docker Containerization

**Feature**: 033-docker-containerization
**Date**: 2026-01-20

## Pré-requisitos

- Docker Desktop 4.x+ ou Docker Engine 24.x+
- Docker Compose V2+
- Git

## Ambientes Disponíveis

| Ambiente | Comando | Uso |
|----------|---------|-----|
| Desenvolvimento | `docker compose --profile dev up` | Coding com hot reload |
| Testes | `docker compose --profile test up` | E2E e testes manuais |

## Desenvolvimento Local

### 1. Iniciar Ambiente

```bash
# Copiar variáveis de ambiente
cp .env.example .env.docker.dev

# Iniciar todos os serviços
docker compose --profile dev up
```

### 2. Acessar Aplicação

| Serviço | URL |
|---------|-----|
| Frontend | http://localhost:8080 |
| Backend API | http://localhost:8000 |
| PostgreSQL | localhost:5432 |
| Phoenix Tracing | http://localhost:6006 |

### 3. Hot Reload

- **Frontend**: Edite arquivos em `frontend/src/` - mudanças aparecem automaticamente
- **Backend**: Edite arquivos em `src/synth_lab/` - uvicorn reinicia automaticamente

### 4. Database Migrations

```bash
# Criar nova migration
docker compose --profile dev exec backend alembic revision --autogenerate -m "description"

# Aplicar migrations
docker compose --profile dev exec backend alembic upgrade head
```

### 5. Parar Ambiente

```bash
docker compose --profile dev down
```

## Ambiente de Testes

### 1. Iniciar Ambiente

```bash
# Copiar variáveis de teste
cp .env.e2e .env.docker.test

# Build das imagens de produção
docker compose --profile test build

# Iniciar ambiente de teste
docker compose --profile test up -d
```

### 2. Executar Testes E2E

```bash
# Via Playwright local
cd frontend && npm run test:e2e:docker

# Ou via container
docker compose --profile test exec frontend npm run test
```

### 3. Reset do Banco de Teste

```bash
docker compose --profile test down -v
docker compose --profile test up -d
```

### 4. Acessar Logs

```bash
# Todos os serviços
docker compose --profile test logs -f

# Apenas backend
docker compose --profile test logs -f backend-test
```

## Deploy para Railway

O deploy usa as mesmas imagens Docker validadas no ambiente de teste:

### 1. Via GitHub Actions (Automático)

```bash
# Criar tag para trigger de deploy
git tag v0.3.0
git push origin v0.3.0
```

### 2. Via Railway CLI (Manual)

```bash
# Backend
cd / && railway up --service synth-lab-api

# Frontend
cd frontend && railway up --service synth-lab-frontend
```

## Comandos Úteis

```bash
# Ver status dos containers
docker compose --profile dev ps

# Rebuild após mudança em Dockerfile
docker compose --profile dev build --no-cache

# Acessar shell do container
docker compose --profile dev exec backend bash
docker compose --profile dev exec frontend sh

# Ver logs em tempo real
docker compose --profile dev logs -f backend

# Limpar tudo (volumes inclusos)
docker compose --profile dev down -v --rmi local
```

## Troubleshooting

### Hot reload não funciona

```bash
# Verificar se WATCHFILES_FORCE_POLLING está definido
docker compose --profile dev exec backend env | grep WATCH

# Verificar se CHOKIDAR_USEPOLLING está definido
docker compose --profile dev exec frontend env | grep CHOKIDAR
```

### Porta em uso

```bash
# Verificar processos usando a porta
lsof -i :8000
lsof -i :8080

# Ou usar portas alternativas
BACKEND_PORT=8001 FRONTEND_PORT=8081 docker compose --profile dev up
```

### Database connection refused

```bash
# Verificar se postgres está healthy
docker compose --profile dev ps postgres

# Ver logs do postgres
docker compose --profile dev logs postgres
```

### Permissão negada em volumes

```bash
# Linux: adicionar usuário ao grupo docker
sudo usermod -aG docker $USER

# Ou executar com sudo (não recomendado)
sudo docker compose --profile dev up
```

## Arquivos de Configuração

| Arquivo | Propósito |
|---------|-----------|
| `docker/docker-compose.yml` | Compose principal |
| `.env.docker.dev` | Variáveis desenvolvimento |
| `.env.docker.test` | Variáveis teste |
| `Dockerfile` | Backend para Railway |
| `frontend/Dockerfile` | Frontend para Railway |
| `docker/backend/Dockerfile` | Backend para dev local |
| `docker/frontend/Dockerfile.dev` | Frontend com HMR |
