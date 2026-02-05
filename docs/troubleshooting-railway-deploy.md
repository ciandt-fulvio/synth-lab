# Troubleshooting Railway Deployment Issues

## Problema: Railway procura por imagem antiga que não existe

### Sintomas

- Railway mostra erro: `This image does not have a "<commit-sha>" tag`
- Health check retorna 502
- Backend não consegue iniciar
- Frontend funciona normalmente

### Causa Raiz

O Railway pode ficar "preso" tentando baixar uma imagem antiga que:
1. Nunca foi criada (pre-push hook falhou)
2. Foi deletada do GHCR
3. Está com tag incorreta

### Diagnóstico

#### 1. Verificar se a imagem existe no GHCR

```bash
# Ver commit SHA atual
git rev-parse HEAD

# Ver últimas imagens no GHCR
podman search ghcr.io/<seu-usuario>/synth-lab-api --list-tags | head -20

# Tentar baixar a imagem específica
podman pull ghcr.io/<seu-usuario>/synth-lab-api:<commit-sha>
```

#### 2. Verificar logs do GitHub Actions

```bash
# Ver últimos workflows
gh run list --workflow=deploy-staging.yml --limit 5

# Ver logs de um workflow específico
gh run view <run-id> --log | grep -E "(Deploy backend|Image:|ghcr\.io)"
```

#### 3. Verificar o que o Railway está tentando usar

No painel do Railway:
1. Acesse o serviço `synth-lab-api`
2. Vá em "Deployments"
3. Veja qual imagem está sendo usada no deployment que falhou

### Soluções

#### Solução 1: Forçar redeploy com imagem correta

Se a imagem correta existe no GHCR, mas o Railway está tentando usar a errada:

```bash
# 1. Verificar qual imagem existe
podman search ghcr.io/<seu-usuario>/synth-lab-api --list-tags | grep -E "(latest|7c3b3ff)"

# 2. Se a imagem existe, forçar redeploy via GitHub Actions
gh workflow run deploy-staging.yml
```

#### Solução 2: Reconstruir e fazer push da imagem

Se a imagem não existe no GHCR:

```bash
# 1. Verificar qual commit precisa
git log -1 --oneline

# 2. Reconstruir e fazer push manualmente
COMMIT_SHA=$(git rev-parse HEAD)
podman build -t synth-lab-api:$COMMIT_SHA -f Dockerfile.backend .
podman tag synth-lab-api:$COMMIT_SHA ghcr.io/<seu-usuario>/synth-lab-api:$COMMIT_SHA
podman push ghcr.io/<seu-usuario>/synth-lab-api:$COMMIT_SHA
podman push ghcr.io/<seu-usuario>/synth-lab-api:latest

# 3. Forçar redeploy
gh workflow run deploy-staging.yml
```

#### Solução 3: Usar tag `:latest`

Se houver problemas persistentes com tags específicas:

**Opção A: Modificar temporariamente o workflow**

No arquivo `.github/workflows/deploy-staging.yml`, altere:
```yaml
# De:
IMAGE_TAG: ${{ github.sha }}

# Para:
IMAGE_TAG: latest
```

**Opção B: Configurar Railway para usar `:latest`**

1. Acesse o Railway
2. Service Settings → Source
3. Mude a imagem para: `ghcr.io/<seu-usuario>/synth-lab-api:latest`

> ⚠️ **Nota**: Usar `:latest` é menos seguro porque não garante qual versão está rodando.

#### Solução 4: Limpar deployments antigos do Railway

Se o Railway está com cache de configuração antiga:

1. Acesse o Railway
2. Vá no serviço `synth-lab-api`
3. Settings → Delete Service
4. Recrie o serviço:
   - Service Name: `synth-lab-api`
   - Source: Docker Image
   - Image: `ghcr.io/<seu-usuario>/synth-lab-api:latest`
5. Configure variáveis de ambiente novamente
6. Deploy

### Prevenção

#### 1. Garantir que pre-push hook sempre rode

```bash
# Verificar se hook está configurado
git config core.hooksPath
# Deve retornar: .githooks

# Se não estiver configurado
git config core.hooksPath .githooks

# Testar hook manualmente
./.githooks/pre-push
```

#### 2. Verificar imagens antes de fazer push

```bash
# Antes de fazer push, verificar se imagens foram criadas
COMMIT_SHA=$(git rev-parse HEAD)
podman images | grep $COMMIT_SHA

# Deve mostrar:
# synth-lab-api:7c3b3ff...
# synth-lab-frontend:7c3b3ff...
```

#### 3. Nunca usar `--no-verify`

```bash
# ❌ NÃO FAZER:
git push --no-verify

# ✅ SEMPRE:
git push
# (deixa o pre-push hook rodar)
```

### Melhorias Implementadas (v2)

As seguintes melhorias foram adicionadas ao workflow para prevenir esses problemas:

1. **Verificação de Imagem Antes do Deploy**
   - Workflow agora verifica se a imagem existe no GHCR antes de tentar deployar
   - Falha rápido se a imagem não existir, com mensagem clara

2. **Timeout Reduzido**
   - Health check agora espera 5 minutos (antes: 10 minutos)
   - Fail-fast para iteração mais rápida

3. **Espera Inicial Aumentada**
   - Espera 3 minutos antes do primeiro health check (antes: 2 minutos)
   - Dá tempo para o Railway baixar imagens grandes

4. **Verificação no Script de Deploy**
   - `railway-deploy-image.sh` agora verifica se a imagem existe antes de atualizar o Railway
   - Usa `skopeo`, `podman`, ou `docker` para verificar

### Logs Úteis

#### Ver logs do backend no Railway

Via Railway CLI:
```bash
railway logs --service synth-lab-api --environment staging
```

Via Railway UI:
1. Acesse o projeto
2. Selecione `synth-lab-api`
3. Aba "Deployments"
4. Clique no deployment ativo
5. "View Logs"

#### Ver logs do GitHub Actions

```bash
# Workflow atual
gh run list --workflow=deploy-staging.yml --limit 1

# Ver logs
gh run view <run-id> --log

# Filtrar por job específico
gh run view <run-id> --log | grep -A 20 "Deploy Backend"
```

### Contato de Suporte

Se o problema persistir após seguir este guia:

1. **Coletar informações**:
   - Commit SHA: `git rev-parse HEAD`
   - Imagens disponíveis: `podman search ghcr.io/<usuario>/synth-lab-api --list-tags`
   - Logs do workflow: `gh run view <run-id> --log > workflow.log`
   - Screenshot do erro no Railway

2. **Criar issue no GitHub**:
   ```bash
   gh issue create \
     --title "Railway deployment failing: image not found" \
     --body "$(cat <<EOF
   **Commit SHA**: $(git rev-parse HEAD)
   **Error**: Railway cannot find image
   **Workflow run**: $(gh run list --workflow=deploy-staging.yml --limit 1 --json url --jq '.[0].url')

   See attached logs and screenshots.
   EOF
   )"
   ```

## Verificações Rápidas

### Checklist de Diagnóstico

```bash
# ✅ 1. Pre-push hook configurado?
git config core.hooksPath
# Esperado: .githooks

# ✅ 2. Imagem local existe?
COMMIT_SHA=$(git rev-parse HEAD | cut -c1-12)
podman images | grep $COMMIT_SHA
# Deve mostrar imagens synth-lab-api e synth-lab-frontend

# ✅ 3. Imagem no GHCR existe?
podman pull ghcr.io/<usuario>/synth-lab-api:$COMMIT_SHA
# Deve baixar com sucesso

# ✅ 4. Workflow rodou?
gh run list --workflow=deploy-staging.yml --limit 1
# Deve mostrar status "completed" ou "in_progress"

# ✅ 5. Railway está acessível?
curl https://synth-lab-api-staging.up.railway.app/health
# Deve retornar 200 OK (se backend estiver rodando)
```

Se TODAS as verificações passarem mas o Railway ainda falha:
→ **Problema está no Railway, não no código/CI/CD**
→ Verificar logs do Railway e configuração do serviço
