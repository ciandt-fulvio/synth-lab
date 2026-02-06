# CI/CD Pipeline v2 - Build Once, Deploy Everywhere

## Overview

Pipeline reorganizado para buildar imagens nativas AMD64 no GitHub Actions (sem QEMU), com deploy automático para staging e production.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ LOCAL (Mac ARM/Intel)                                           │
├─────────────────────────────────────────────────────────────────┤
│ Pre-Push Hook (.githooks/pre-push)                             │
│   ├─> Build local (para testes isolados)                       │
│   ├─> make test (unit tests)                                   │
│   ├─> make test-e2e (E2E tests)                                │
│   └─> Allow push if tests pass                                 │
│                                                                 │
│ Não faz push de imagens (GitHub Actions fará)                  │
└─────────────────────────────────────────────────────────────────┘
                            ↓ git push origin main
┌─────────────────────────────────────────────────────────────────┐
│ GITHUB ACTIONS (AMD64 native runners)                          │
├─────────────────────────────────────────────────────────────────┤
│ 1. Build Images (build-images.yml) - 5 min                     │
│    ├─> Build backend (AMD64 nativo, sem QEMU)                  │
│    ├─> Build frontend (paralelo)                               │
│    ├─> Cache layers do GHCR                                    │
│    └─> Push: :staging, :commit-sha, :latest                    │
│                                                                 │
│ Sem testes (já rodaram localmente)                             │
└─────────────────────────────────────────────────────────────────┘
                            ↓ workflow_run (auto)
┌─────────────────────────────────────────────────────────────────┐
│ 2. Deploy Staging (deploy-staging.yml) - 10 min                │
│    ├─> Check: build-images passou? (gate)                      │
│    ├─> Migrate DB (alembic upgrade head)                       │
│    ├─> Seed DB (condicional, se vazio)                         │
│    ├─> Deploy backend → Railway                                │
│    ├─> Deploy frontend → Railway                               │
│    ├─> Smoke tests                                             │
│    └─> Tag :staging-verified (se smoke tests passaram)         │
└─────────────────────────────────────────────────────────────────┘
                            ↓ workflow_run (auto)
┌─────────────────────────────────────────────────────────────────┐
│ 3. Deploy Production (deploy-production.yml) - 5 min           │
│    ├─> Check: smoke tests staging passaram? (gate)             │
│    ├─> Migrate DB (SAFE, não dropa)                            │
│    ├─> Deploy backend → Railway                                │
│    ├─> Deploy frontend → Railway                               │
│    └─> Smoke tests production                                  │
│                                                                 │
│ 🔒 GATE: Só roda se smoke tests staging passaram               │
└─────────────────────────────────────────────────────────────────┘
```

## Key Changes from v1

| Aspecto | v1 (old) | v2 (new) |
|---------|----------|----------|
| **Local build** | Build + push para GHCR | Build apenas (para testes) |
| **GHCR push** | Pre-push hook (local) | GitHub Actions (AMD64 nativo) |
| **Build speed** | Lento (QEMU no Mac ARM) | Rápido (AMD64 nativo) |
| **Build reliability** | Crashes com QEMU | Confiável (sem QEMU) |
| **Staging deploy** | Trigger: push to main | Trigger: workflow_run (build-images) |
| **Production deploy** | Manual only | Auto (se smoke tests passaram) |
| **Image cleanup** | Keep latest + 3 SHAs | Keep latest + 1 SHA |

## Workflows

### 1. build-images.yml (NEW)

**Trigger**: Push to main

**Jobs**:
- `build-backend`: Build e push backend image
- `build-frontend`: Build e push frontend image (paralelo)
- `notify`: Summary

**Tags criadas**:
- `:staging` - usado para deploy
- `:commit-sha` - referência imutável
- `:latest` - alias para última build

**Duration**: ~5 min (paralelo)

### 2. deploy-staging.yml (MODIFIED)

**Trigger**: workflow_run (build-images completes)

**Changes**:
- Added `check-build-status` job (gate)
- Runs only if build-images succeeded
- Mantém todos os outros jobs

**Duration**: ~10 min

### 3. deploy-production.yml (MODIFIED)

**Trigger**: workflow_run (deploy-staging completes) + workflow_dispatch (manual)

**Changes**:
- Added `check-staging-status` job (gate)
- Runs only if staging smoke tests passed
- Auto-deploy habilitado (pode ser desabilitado)

**Duration**: ~5 min

## Image Tags Strategy

| Tag | Purpose | Created By | Lifetime |
|-----|---------|------------|----------|
| `:staging` | Deploy staging/production | build-images.yml | Overwritten on each build |
| `:commit-sha` | Immutable reference | build-images.yml | Permanent |
| `:latest` | Latest successful build | build-images.yml | Overwritten on each build |
| `:staging-verified` | Smoke tests passed | deploy-staging.yml | Overwritten on each staging deploy |

## Local Development

### Pre-Push Hook

```bash
# Automatically runs on: git push origin main
# 1. Builds images locally (ARM → AMD64 via QEMU, for tests only)
# 2. Runs unit tests (make test)
# 3. Runs E2E tests (make test-e2e)
# 4. Allows push if all tests pass

# NO GHCR push (GitHub Actions will build natively)
```

### Image Cleanup

Local images são mantidas apenas para testes. Cleanup automático:

```bash
# Runs automatically at end of pre-push hook
./scripts/clean-old-images.sh

# Keeps: latest + 1 most recent commit SHA
# Removes: old commit SHAs, orphaned images, dangling images
```

## Railway Configuration

Railway services devem estar configurados como:

**Source**: Dockerfile (not "Docker Image")

**Files**:
- Backend: `railway.toml` → `dockerfilePath = "Dockerfile.backend"`
- Frontend: `frontend/railway.toml` → `dockerfilePath = "Dockerfile"`

**Deployment**:
- Railway puxa código do GitHub
- Builda usando Dockerfile especificado
- **NÃO** usa imagens do GHCR diretamente

## Security & Gates

### Gate 1: Local Tests (Pre-Push)
- Unit tests must pass
- E2E tests must pass
- Blocks git push if fails

### Gate 2: Build Success (Deploy Staging)
- deploy-staging.yml only runs if build-images.yml succeeded
- Prevents deploying broken builds

### Gate 3: Smoke Tests (Deploy Production)
- deploy-production.yml only runs if staging smoke tests passed
- Prevents deploying to production if staging is broken

## Disable Auto-Deploy (Emergency)

Para desabilitar auto-deploy para production:

1. Edit `.github/workflows/deploy-production.yml`
2. Remove `workflow_run` trigger:
   ```yaml
   on:
     # workflow_run:  # COMMENTED OUT
     #   workflows: ["Deploy Staging"]
     #   types: [completed]
     #   branches: [main]
     workflow_dispatch:  # Keep manual trigger
       inputs:
         # ...
   ```
3. Commit and push

Production agora só deploya via `gh workflow run deploy-production.yml`

## Troubleshooting

### Build fails in GitHub Actions

```bash
# View logs
gh run view <run-id> --log

# Check build step
gh run view <run-id> --log | grep -A 50 "Build and push backend"

# Common issues:
# - Docker layer cache miss (first build is slower)
# - Build context too large (check .dockerignore)
# - Dependency resolution (check pyproject.toml, package.json)
```

### Staging deploy fails

```bash
# Check if build-images succeeded
gh run list --workflow=build-images.yml --limit 5

# Check deploy logs
gh run view <run-id> --log

# Common issues:
# - Railway service not found (check service names)
# - Database migration failed (check alembic logs)
# - Health check timeout (check Railway logs)
```

### Production auto-deploy not triggering

```bash
# Check if staging smoke tests passed
gh run list --workflow=deploy-staging.yml --limit 5
gh run view <run-id> --log | grep -A 20 "Smoke Tests"

# Check workflow_run conclusion
# (must be "success" for all jobs, including smoke tests)
```

### Smoke tests fail

```bash
# Download Playwright artifacts
gh run download <run-id>

# View test results
# staging-playwright-report/index.html
# staging-smoke-test-results/

# Common issues:
# - Backend not healthy (Railway container not started)
# - Frontend can't reach backend (CORS, network)
# - Test data missing (check seed_database.py)
```

## Benefits

1. **Faster local iteration**: Não precisa esperar push de imagens
2. **Reliable builds**: AMD64 nativo no CI, sem QEMU crashes
3. **Parallel builds**: Backend + frontend em paralelo (~5 min)
4. **Auto-deploy**: Staging → Production automático se smoke tests passarem
5. **Quality gates**: Múltiplas validações antes de chegar em produção
6. **Easy rollback**: Imagens tagadas no GHCR, Railway rollback CLI
7. **Auditability**: workflow_run tracking, commit SHAs imutáveis

## Metrics

| Stage | Duration | Trigger | Manual? |
|-------|----------|---------|---------|
| Pre-push hook | 2-5 min | git push | No |
| Build images | ~5 min | push to main | No |
| Deploy staging | ~10 min | build completes | No |
| Deploy production | ~5 min | smoke tests pass | Optional (auto by default) |
| **Total** | **~20-25 min** | Single push | Auto end-to-end |

## Future Improvements

1. **Conditional builds**: Skip rebuild se código não mudou (change detection)
2. **Build matrix**: Test múltiplas versões Python/Node em paralelo
3. **Canary deploys**: Deploy gradual em production (Railway Pro)
4. **Rollback automation**: Auto-rollback se smoke tests prod falharem
5. **Slack notifications**: Notificar em cada stage do pipeline
