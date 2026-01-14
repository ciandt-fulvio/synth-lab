# Testes E2E (End-to-End) - synth-lab

Este documento descreve como rodar, debugar e manter os testes E2E do synth-lab usando Playwright em ambiente Docker isolado.

## Índice

- [Visão Geral](#visão-geral)
- [Quick Start](#quick-start)
- [Arquitetura](#arquitetura)
- [Comandos](#comandos)
- [Debugging](#debugging)
- [Git Hooks](#git-hooks)
- [Troubleshooting](#troubleshooting)
- [Adicionando Novos Testes](#adicionando-novos-testes)

---

## Visão Geral

Os testes E2E validam a aplicação completa (frontend + backend + banco de dados) executando cenários reais de uso no navegador.

**Características:**
- **Isolamento total**: Rodam em containers (Docker ou Podman) com portas dedicadas
- **Reproduzível**: Mesma configuração local e no CI
- **Sem interferência**: Dev servers (8000/8080) continuam rodando normalmente
- **Limpeza automática**: Containers são removidos após cada execução
- **Compatível**: Detecta automaticamente Docker ou Podman no sistema

**Ambiente de Teste:**
| Serviço | Porta Host | URL |
|---------|-----------|-----|
| Frontend | 8091 | http://localhost:8091 |
| Backend | 8001 | http://localhost:8001 |
| PostgreSQL | 5433 | localhost:5433 (DB: synthlab_e2e) |

---

## Quick Start

### 1. Rodar Todos os Testes (Recomendado)

```bash
make test-e2e-docker
```

Isso irá:
1. Buildar imagens Docker (cache após primeira vez)
2. Subir PostgreSQL, backend e frontend
3. Rodar migrations e seed do banco
4. Executar testes Playwright
5. Derrubar containers e limpar volumes

### 2. Modo Debug (Ambiente Persistente)

Para investigar falhas ou desenvolver novos testes:

```bash
# Subir ambiente e manter rodando
make test-e2e-docker-up

# Em outro terminal, rodar testes manualmente
cd frontend
TEST_ENV=docker npm run test:e2e

# Ou rodar em modo UI (visual)
TEST_ENV=docker npm run test:e2e:ui

# Quando terminar, derrubar ambiente
make test-e2e-docker-down
```

### 3. Visualizar Logs

```bash
# Logs em tempo real
make test-e2e-docker-logs

# Ou individualmente
docker-compose -f docker-compose.e2e.yml logs backend-e2e
docker-compose -f docker-compose.e2e.yml logs frontend-e2e
docker-compose -f docker-compose.e2e.yml logs postgres-e2e
```

---

## Arquitetura

### Mapeamento de Portas

```
┌─────────────────────────────────────────────────┐
│ Host Machine                                    │
│                                                 │
│  Dev:  Backend:8000  Frontend:8080  DB:5432    │
│  E2E:  Backend:8001  Frontend:8091  DB:5433    │
│         ↓              ↓              ↓         │
└─────────┼──────────────┼──────────────┼─────────┘
          │              │              │
    ┌─────┼──────────────┼──────────────┼─────┐
    │ Docker Network (e2e-network)            │
    │                                          │
    │  backend-e2e:8000 ←→ frontend-e2e:8080 │
    │            ↕                             │
    │     postgres-e2e:5432                   │
    └──────────────────────────────────────────┘
```

### Fluxo de Execução

```
1. docker-compose up --build
   ├─ postgres-e2e: Inicia e aguarda health check
   ├─ backend-e2e: Roda migrations → seed → uvicorn
   └─ frontend-e2e: Build assets → vite preview

2. Playwright (no host)
   └─ Testa contra http://localhost:8091

3. docker-compose down -v
   └─ Remove containers e volumes (estado limpo)
```

---

## Comandos

### Makefile

| Comando | Descrição |
|---------|-----------|
| `make test-e2e` | Roda E2E via Docker (alias de test-e2e-docker) |
| `make test-e2e-docker` | Roda E2E via Docker (limpa ao final) |
| `make test-e2e-docker-up` | Sobe ambiente (mantém rodando) |
| `make test-e2e-docker-down` | Derruba ambiente |
| `make test-e2e-docker-logs` | Visualiza logs em tempo real |
| `make test-e2e-local` | Roda E2E localmente (legacy, requer servers manuais) |
| `make test-e2e-ui` | Roda E2E em modo UI (visual) |

### npm (dentro de `frontend/`)

| Comando | Descrição |
|---------|-----------|
| `npm run test:e2e:docker` | Roda testes contra ambiente Docker |
| `npm run test:e2e:docker:up` | Sobe ambiente Docker |
| `npm run test:e2e:docker:down` | Derruba ambiente Docker |
| `npm run test:e2e:docker:logs` | Visualiza logs |
| `npm run test:e2e` | Roda testes localmente (porta 8080) |
| `npm run test:e2e:ui` | Modo UI (debugging visual) |
| `npm run test:e2e:debug` | Modo debug (step-by-step) |

### Docker Compose Direto

```bash
# Subir ambiente
docker-compose -f docker-compose.e2e.yml up --build -d

# Derrubar ambiente
docker-compose -f docker-compose.e2e.yml down -v

# Logs
docker-compose -f docker-compose.e2e.yml logs -f backend-e2e

# Rebuild forçado (se mudou dependências)
docker-compose -f docker-compose.e2e.yml build --no-cache
```

---

## Debugging

### 1. Testes Falhando

```bash
# 1. Subir ambiente e manter rodando
make test-e2e-docker-up

# 2. Acessar manualmente no navegador
open http://localhost:8091

# 3. Rodar testes em modo UI (visual)
cd frontend
TEST_ENV=docker npm run test:e2e:ui

# 4. Ver logs do backend
make test-e2e-docker-logs

# 5. Quando terminar
make test-e2e-docker-down
```

### 2. Inspecionar Banco de Dados

```bash
# Conectar ao PostgreSQL do container
docker exec -it synthlab-postgres-e2e psql -U synthlab_e2e -d synthlab_e2e

# Ou via host (porta 5433)
psql postgresql://synthlab_e2e:synthlab_e2e@localhost:5433/synthlab_e2e
```

### 3. Acessar Backend Diretamente

```bash
# Health check
curl http://localhost:8001/health

# Listar experimentos
curl http://localhost:8001/api/experiments
```

### 4. Screenshots e Vídeos

Playwright captura automaticamente em falhas:
```
frontend/
├── test-results/        # Screenshots de falhas
└── playwright-report/   # Relatório HTML com traces
```

Visualizar relatório:
```bash
cd frontend
npm run test:e2e:report
```

---

## Git Hooks

### Instalação

```bash
./scripts/install-hooks.sh
```

### O Que Faz

- **Hook pre-push**: Executa `make test-e2e-docker` antes de cada `git push`
- Se testes passam → push prossegue
- Se testes falham → push é bloqueado

### Bypass (Não Recomendado)

```bash
git push --no-verify
```

### Desinstalar

```bash
rm .git/hooks/pre-push
```

---

## Podman vs Docker

O projeto **detecta automaticamente** se você tem Docker ou Podman instalado.

### Usando Podman (macOS/Linux)

Se você usa Podman em vez de Docker:

1. **Instalar podman-compose:**
   ```bash
   # macOS
   brew install podman-compose

   # Linux
   pip install podman-compose
   ```

2. **O Makefile detecta automaticamente:**
   ```bash
   make test-e2e-docker
   # Output: 🐳 Using container runtime: podman
   ```

3. **Sem necessidade de alias manual** - tudo funciona automaticamente!

### CI/CD (GitHub Actions)

**Workflow:** `.github/workflows/tests-e2e.yml`

**Como funciona:**
1. **Checkout código** e setup Node.js 20
2. **Instalar dependências:** frontend + Playwright browsers
3. **Subir ambiente E2E:**
   ```bash
   docker-compose -f docker-compose.e2e.yml up --build -d
   ```
4. **Health checks:** Aguarda backend (8001/health) e frontend (8091) estarem prontos
5. **Executar testes:** `TEST_ENV=docker npm run test:e2e`
6. **Upload artifacts** (apenas se falhar):
   - Screenshots (`frontend/test-results/`)
   - Playwright report (`frontend/playwright-report/`)
   - Logs dos containers (backend, frontend, postgres)
7. **Cleanup:** Para containers e remove volumes

**Diferenças local vs CI:**
- **Local:** Pode usar Docker ou Podman (auto-detecta)
- **CI:** Usa Docker nativamente no GitHub Actions
- **Compatibilidade:** Mesmo `docker-compose.e2e.yml` funciona em ambos

**Ver resultados do CI:**
1. GitHub → Actions → E2E Tests
2. Clicar no run específico
3. Se falhou → Artifacts → Download logs/reports

## Troubleshooting

### Problema: Aliases docker/podman conflitantes

**Se você tem aliases no shell como:**
```bash
alias docker=podman
alias docker-compose=podman-compose
```

**Isso pode causar conflitos!** O projeto agora usa um **script wrapper** (`scripts/compose-e2e.sh`) que detecta automaticamente o comando real, ignorando aliases.

**✅ Solução:** Os comandos via Makefile já usam o wrapper automaticamente:
```bash
make test-e2e-docker  # Funciona com Docker ou Podman
```

**Recomendação:** Considere remover os aliases e deixar o projeto detectar automaticamente.

### Problema: podman-compose não encontrado

**Erro:**
```
/bin/sh: podman-compose: command not found
```

**Solução:**
```bash
# macOS
brew install podman-compose

# Linux (via pip)
pip install podman-compose

# Ou via pipx (recomendado)
pipx install podman-compose
```

Após instalar, rode novamente:
```bash
make test-e2e-docker
# Deve mostrar: 🐳 Using: podman
```

### Problema: Porta 8091 já em uso

```bash
# Ver quem está usando a porta
lsof -i :8091

# Matar processo (se seguro)
kill <PID>

# Ou usar portas diferentes (editar docker-compose.e2e.yml)
```

### Problema: Build lento na primeira vez

**Causa:** Docker precisa baixar imagens e buildar layers

**Solução:**
- Primeira vez: ~5-10 minutos
- Execuções seguintes: ~30s (usa cache)
- Força rebuild: `docker-compose -f docker-compose.e2e.yml build --no-cache`

### Problema: Containers órfãos

```bash
# Listar containers do projeto
docker ps -a | grep synthlab

# Remover tudo forçadamente
docker-compose -f docker-compose.e2e.yml down -v
docker system prune -f
```

### Problema: Seed data inconsistente

```bash
# Forçar recriação do banco
docker-compose -f docker-compose.e2e.yml down -v  # Remove volumes
docker-compose -f docker-compose.e2e.yml up --build
```

### Problema: Testes passam localmente, falham no CI

**Possíveis causas:**
1. **Timing**: CI pode ser mais lento
   - Solução: Aumentar timeouts no `playwright.config.ts`

2. **Variáveis de ambiente**: OPENAI_API_KEY ausente
   - Verificar GitHub Secrets

3. **Diferenças de plataforma**: Linux (CI) vs macOS/Windows (local)
   - Testar com `docker run --platform linux/amd64`

### Problema: "Cannot find package 'vite'" no frontend container

**Erro:**
```
Error [ERR_MODULE_NOT_FOUND]: Cannot find package 'vite'
```

**Causa:** Frontend Dockerfile estava instalando apenas prod dependencies (`npm ci --production`), mas Vite é necessário para preview mode.

**✅ Solução:** Já corrigido em `frontend/Dockerfile` linha 30:
```dockerfile
# Antes (ERRADO):
RUN npm ci --production

# Depois (CORRETO):
RUN npm ci
```

### Problema: "Foreign key constraint violation" no backend

**Erro:**
```
sqlalchemy.exc.IntegrityError: (psycopg2.errors.ForeignKeyViolation)
update or delete on table "synth_groups" violates foreign key constraint
```

**Causa:** Seed cleanup deletando `SynthGroup` antes de `Experiment`, mas experiments têm FK para synth_groups.

**✅ Solução:** Já corrigido em `tests/fixtures/seed_test.py`:
```python
# Ordem correta (filhos antes de pais):
session.query(Experiment).delete()  # Primeiro
session.query(SynthGroup).delete()  # Depois
```

### Problema: Proxy não funciona no frontend E2E

**Erro:** Requests `/api/*` retornam 404

**Causa:** Vite preview mode não tinha configuração de proxy (apenas dev mode tinha).

**✅ Solução:** Já corrigido em `frontend/vite.config.ts`:
```typescript
export default defineConfig(() => {
  const backendHost = process.env.VITE_BACKEND_HOST || 'localhost';
  const proxyConfig = { /* ... */ };

  return {
    server: { proxy: proxyConfig },    // Dev mode
    preview: { proxy: proxyConfig },   // Preview mode (E2E)
  };
});
```

### Problema: Verificar se testes estão usando ambiente correto

**Como validar isolamento:**

```bash
# Criar script de validação
bash /tmp/test-isolation.sh

# Deve mostrar:
# ✅ Porta 5432 (PostgreSQL Dev) está em uso
# ✅ Porta 5433 (PostgreSQL E2E) está em uso
# ✅ Porta 8000 (Backend Dev) está em uso
# ✅ Porta 8001 (Backend E2E) está em uso
# ✅ Porta 8080 (Frontend Dev) está em uso
# ✅ Porta 8091 (Frontend E2E) está em uso
```

**Conteúdo do script:**
```bash
#!/bin/bash
echo "🔍 Validando Isolamento E2E vs Dev"
echo "=================================="

check_port() {
    local port=$1
    local name=$2
    if lsof -i :$port > /dev/null 2>&1; then
        echo "✅ Porta $port ($name) está em uso"
    else
        echo "❌ Porta $port ($name) está livre"
    fi
}

check_port 5432 "PostgreSQL Dev"
check_port 5433 "PostgreSQL E2E"
check_port 8000 "Backend Dev"
check_port 8001 "Backend E2E"
check_port 8080 "Frontend Dev"
check_port 8091 "Frontend E2E"
```

---

## Adicionando Novos Testes

### 1. Estrutura de Pastas

```
frontend/tests/e2e/
├── smoke/                # Testes críticos rápidos
├── experiments/          # Testes de experimentos
├── interviews/           # Testes de entrevistas
└── navigation/           # Testes de navegação
```

### 2. Exemplo de Teste

```typescript
import { test, expect } from '@playwright/test';

test.describe('Nova Funcionalidade', () => {
  test('deve fazer X quando Y', async ({ page }) => {
    // Navegar
    await page.goto('/');

    // Interagir
    await page.click('button[aria-label="Nova Ação"]');

    // Verificar
    await expect(page.locator('.resultado')).toBeVisible();
    await expect(page.locator('.resultado')).toHaveText('Esperado');
  });
});
```

### 3. Executar Apenas Seus Testes

```bash
# Por arquivo
TEST_ENV=docker npx playwright test experiments/novo-teste.spec.ts

# Por tag
test.describe('Teste @minha-feature', () => { ... });
TEST_ENV=docker npx playwright test --grep @minha-feature

# Modo debug
TEST_ENV=docker npx playwright test --debug experiments/novo-teste.spec.ts
```

### 4. Dados de Teste

Use dados seeded do banco (veja `tests/fixtures/seed_test.py`):

- **Experimento padrão**: ID `exp_a1b2c3d4`
  - Nome: "App de Delivery - Feature de Agendamento de Pedidos"
  - 500 synths analisados
  - 6 entrevistas realizadas

```typescript
test('usa experimento seeded', async ({ page }) => {
  await page.goto('/experiments/exp_a1b2c3d4');
  await expect(page.locator('h1')).toContainText('App de Delivery');
});
```

---

## Checklist de Validação Pós-Implementação

- [ ] `make test-e2e-docker` roda sem erros
- [ ] Dev servers (8000/8080) continuam funcionando durante E2E
- [ ] Testes passam contra ambiente Docker (porta 8091)
- [ ] Falhas geram screenshots e logs capturados
- [ ] `docker-compose down -v` limpa tudo (sem containers órfãos)
- [ ] Segunda execução é mais rápida (usa cache de build)
- [ ] Hook pre-push instalado e funciona
- [ ] Hook bloqueia push quando testes falham
- [ ] `make test-e2e` agora usa versão Docker
- [ ] CI usa mesma estratégia e passa

---

## Referências

- [Playwright Documentation](https://playwright.dev/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Plano de Implementação](../.claude/plans/partitioned-sparking-cascade.md)

---

**Última atualização:** 2026-01-14
