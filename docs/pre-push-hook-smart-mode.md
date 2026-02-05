# Pre-Push Hook Smart Mode

## Visão Geral

O pre-push hook agora usa **detecção inteligente de mudanças** para otimizar builds e testes, economizando tempo sem comprometer segurança.

## Como Funciona

### 1. Detecção de Mudanças

O hook compara os arquivos alterados desde `origin/main` e classifica em categorias:

```bash
# Mudanças no Backend
src/
tests/
pyproject.toml
uv.lock
Dockerfile.backend
alembic/
scripts/seed_database.py

# Mudanças no Frontend
frontend/src/
frontend/tests/
frontend/package.json
frontend/package-lock.json
frontend/Dockerfile

# Mudanças em Config (roda tudo)
docker/
.env.*
Makefile
.github/

# Apenas Docs (pula testes)
docs/
README.md
*.md
```

### 2. Skip Inteligente

| Cenário | Build Backend | Build Frontend | Testes Unitários | E2E Tests | Push Images |
|---------|--------------|----------------|------------------|-----------|-------------|
| **Apenas docs** | ❌ Skip | ❌ Skip | ❌ Skip | ❌ Skip | ❌ Skip |
| **Apenas backend** | ✅ Sim | ❌ Skip | ✅ Sim | ✅ Sim | ✅ Backend only |
| **Apenas frontend** | ❌ Skip | ✅ Sim | ❌ Skip | ✅ Sim | ✅ Frontend only |
| **Backend + Frontend** | ✅ Sim | ✅ Sim | ✅ Sim | ✅ Sim | ✅ Ambos |
| **Config mudou** | ✅ Sim | ✅ Sim | ✅ Sim | ✅ Sim | ✅ Ambos |

### 3. Cache do Docker

O hook agora usa `--cache-from` para acelerar builds:

```bash
# Pull da última imagem do GHCR (se existir)
podman pull ghcr.io/user/synth-lab-api:latest

# Usa como cache no build
podman build --cache-from ghcr.io/user/synth-lab-api:latest ...
```

**Benefícios:**
- ✅ Layers reutilizadas automaticamente
- ✅ Builds muito mais rápidos se apenas pequenas mudanças
- ✅ Funciona mesmo em máquinas diferentes (cache compartilhado via GHCR)

## Cenários de Uso

### Exemplo 1: Atualizar README

```bash
# Você edita: README.md
git add README.md
git commit -m "docs: update README"
git push origin main

# Hook detecta:
📊 Change Summary:
  Backend changed:  NO
  Frontend changed: NO
  Docs only:        YES

# Resultado:
⏭️  Skipping backend build (no changes)
⏭️  Skipping frontend build (no changes)
⏭️  Skipping unit tests (docs only)
⏭️  Skipping E2E tests (docs only)
⏭️  Skipping image push (no changes)

✅ Push completo em ~5 segundos!
```

### Exemplo 2: Fix no Backend

```bash
# Você edita: src/synth_lab/services/experiment_service.py
git add src/
git commit -m "fix: correct experiment validation"
git push origin main

# Hook detecta:
📊 Change Summary:
  Backend changed:  YES
  Frontend changed: NO
  Docs only:        NO

# Resultado:
✅ Building backend image (com cache do GHCR)
⏭️  Skipping frontend build (no changes)
✅ Running unit tests
✅ Running E2E tests (backend afeta integração)
✅ Pushing backend image to GHCR
⏭️  Skipping frontend push (no changes)

✅ Push completo em ~2-3 minutos (vs 5-10 min antes)
```

### Exemplo 3: Mudança no Frontend

```bash
# Você edita: frontend/src/pages/ExperimentDetail.tsx
git add frontend/
git commit -m "feat: add new button to experiment detail"
git push origin main

# Hook detecta:
📊 Change Summary:
  Backend changed:  NO
  Frontend changed: YES
  Docs only:        NO

# Resultado:
⏭️  Skipping backend build (no changes)
✅ Building frontend image (com cache do GHCR)
⏭️  Skipping unit tests (backend unchanged)
✅ Running E2E tests (frontend afeta integração)
⏭️  Skipping backend push (no changes)
✅ Pushing frontend image to GHCR

✅ Push completo em ~2-3 minutos (vs 5-10 min antes)
```

### Exemplo 4: Mudança em Config

```bash
# Você edita: docker/.env.dev
git add docker/
git commit -m "chore: update env vars"
git push origin main

# Hook detecta:
📊 Change Summary:
  Config changed:   YES
  → Running full validation

# Resultado:
✅ Building backend image
✅ Building frontend image
✅ Running unit tests
✅ Running E2E tests
✅ Pushing both images

✅ Push completo em ~5-10 minutos (full validation)
```

## Por Que É Seguro?

### 1. Docs Only: Pode Pular Tudo?

✅ **SIM** - Se apenas documentação mudou, não há risco de quebrar código. Build é skipado porque:
- Imagens Docker não incluem arquivos `.md`
- Nenhum código executável foi alterado
- Nada pode quebrar em produção

### 2. Frontend Mudou: Pode Pular Testes Unitários Backend?

✅ **SIM** - Testes unitários do backend testam lógica isolada (sem frontend). Mas:
- ❌ **E2E NÃO pode ser pulado** - testa integração frontend+backend
- Frontend pode ter bugs que só aparecem na integração

### 3. Backend Mudou: Pode Pular Build do Frontend?

✅ **SIM** - Frontend não precisa rebuild se seu código não mudou. Mas:
- ❌ **E2E NÃO pode ser pulado** - mudanças no backend podem quebrar integração
- Backend pode mudar contratos de API

### 4. Config Mudou: Por Que Rodar Tudo?

✅ **SEGURO** - Mudanças em:
- `.env.*` → podem afetar comportamento de ambos (backend/frontend)
- `docker/` → podem afetar ambientes de teste
- `Makefile` → podem afetar comandos de build/teste
- `.github/` → podem afetar CI/CD

Por isso, **sempre roda validação completa** para evitar surpresas.

## Performance

### Comparação de Tempo (Estimativa)

| Cenário | Antes (Full) | Agora (Smart) | Economia |
|---------|--------------|---------------|----------|
| Apenas docs | 5-10 min | ~5 seg | 98% |
| Apenas backend | 5-10 min | 2-3 min | 60% |
| Apenas frontend | 5-10 min | 2-3 min | 60% |
| Backend + Frontend | 5-10 min | 5-10 min* | 0-30%** |
| Config change | 5-10 min | 5-10 min | 0% |

\* Com cache do Docker, pode ser mais rápido
\** Economia vem do cache do Docker (`--cache-from`)

### Cache do Docker

**Antes:**
```bash
# Build sempre do zero (exceto cache local de layers)
podman build -t synth-lab-api:SHA .
# Tempo: ~5 min para build completo
```

**Agora:**
```bash
# Pull última imagem do GHCR
podman pull ghcr.io/user/synth-lab-api:latest

# Usa como cache
podman build --cache-from ghcr.io/user/synth-lab-api:latest -t synth-lab-api:SHA .
# Tempo: ~1-2 min se apenas pequenas mudanças
```

**Benefícios:**
- ✅ Cache compartilhado entre máquinas (via GHCR)
- ✅ CI/CD também se beneficia (não precisa rebuild completo)
- ✅ Funciona mesmo depois de `podman system prune`

## Comandos Úteis

### Ver Mudanças Detectadas (Manual)

```bash
# Ver arquivos mudados desde origin/main
git fetch origin main
git diff --name-only origin/main...HEAD

# Testar classificação
git diff --name-only origin/main...HEAD | grep -E '^src/|^tests/|pyproject.toml'
# ↑ Backend mudou?

git diff --name-only origin/main...HEAD | grep -E '^frontend/(src/|tests/|package)'
# ↑ Frontend mudou?
```

### Forçar Full Validation

```bash
# Commitar mudança em config para forçar full validation
touch docker/.env.dev
git add docker/.env.dev
git commit -m "chore: force full validation"
```

### Bypass do Hook

```bash
# Se precisar fazer push sem validação (emergência)
git push origin main --no-verify

# ⚠️  NÃO RECOMENDADO - use apenas se CI estiver quebrado
```

## Troubleshooting

### "Skipped tests but they should run"

**Causa:** Arquivo mudado não está na lista de detecção

**Solução:** Adicione o padrão no hook (linha ~70-95)

```bash
# Exemplo: adicionar novo diretório
if [[ "$file" =~ ^(src/|NEW_DIR/|tests/|...) ]]; then
    BACKEND_CHANGED=true
    DOCS_ONLY=false
fi
```

### "Build failed with cache error"

**Causa:** Imagem de cache no GHCR não existe ou está corrompida

**Solução:** O hook ignora erros de pull (linha ~149):
```bash
podman pull "$GHCR_BACKEND_IMAGE:latest" 2>/dev/null || true
# ↑ Se falhar, continua sem cache (build do zero)
```

### "Hook says no changes but I changed files"

**Causa:** Comparação com `origin/main` pode estar desatualizada

**Solução:** Faça fetch antes de push:
```bash
git fetch origin main
git push origin main
```

O hook já faz isso automaticamente (linha ~59), mas pode falhar se sem conexão.

## Limitações

1. **Não detecta mudanças indiretas:**
   - Se você mudou uma lib interna que afeta ambos (backend/frontend)
   - Hook vai rodar testes do que mudou, mas pode não capturar acoplamento
   - **Mitigação:** CI roda full validation em PRs

2. **Cache pode ter false positives:**
   - Se Dockerfile mudou mas arquivo não foi commitado
   - **Mitigação:** Sempre commite Dockerfiles junto com código

3. **Depende de GHCR estar acessível:**
   - Se GHCR estiver down, cache não funciona
   - **Mitigação:** Hook continua sem cache (mais lento mas funciona)

## Conclusão

O smart mode do pre-push hook:
- ✅ **Economiza tempo** (60-98% em mudanças isoladas)
- ✅ **Mantém segurança** (sempre roda testes relevantes)
- ✅ **Aproveita cache** (GHCR compartilhado)
- ✅ **É conservador** (na dúvida, roda tudo)
- ✅ **É transparente** (mostra o que foi skipado e por quê)

**Recomendação:** Deixe habilitado (é o padrão agora). Use `--no-verify` apenas em emergências.
