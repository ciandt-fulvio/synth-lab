# Database Deployment Strategy

## Overview

O synth-lab usa uma estratégia de deployment que **separa** a gestão do database (migrations/seeding) da inicialização do container. Isso garante:

- ✅ Migrations rodam **antes** do deploy (não durante startup do container)
- ✅ Seeding é **condicional** e **seguro** (verifica se DB já tem dados)
- ✅ Containers iniciam **rápido** (sem esperar migrations/seed)
- ✅ Zero race conditions (migrations não rodam em paralelo em múltiplas réplicas)

## Responsabilidades

| Componente | Responsabilidade |
|------------|------------------|
| **GitHub Actions Workflow** | Migrations + Seeding (ANTES do deploy) |
| **Container Entrypoint** | Apenas iniciar a aplicação (uvicorn) |
| **E2E Local (docker-compose)** | Migrations + Seeding (via flags) |

## Deployment Modes

### 1. Normal Deploy (Staging - Automático)

**Trigger**: `git push origin main`

**Fluxo**:
```
1. Pre-push hook roda localmente:
   ├─> Build images
   ├─> Run tests
   ├─> Push images to GHCR
   └─> Allow push

2. GitHub Actions workflow:
   ├─> Migrate DB (apply new migrations only - ADDITIVE)
   ├─> Seed DB (conditional - only if synth_groups is empty)
   ├─> Deploy backend to Railway
   ├─> Deploy frontend to Railway
   └─> Run smoke tests
```

**Database**: Preserva dados existentes, aplica apenas novas migrations.

### 2. Fresh Start (Staging - Manual)

**Trigger**: `./scripts/fresh-start-staging.sh` ou `gh workflow run deploy-staging.yml -f fresh_start=true`

**Fluxo**:
```
1. GitHub Actions workflow:
   ├─> Reset DB (DROP SCHEMA CASCADE - DESTROYS ALL DATA)
   ├─> Migrate DB (recreate from scratch)
   ├─> Seed DB (always, since DB is empty)
   ├─> Deploy backend to Railway
   ├─> Deploy frontend to Railway
   └─> Run smoke tests
```

**Database**: Apaga tudo e recria do zero.

**Use quando**:
- Primeira vez deployando staging
- Database ficou em estado inconsistente
- Quer testar migrations do zero
- Quer dados de seed atualizados

### 3. Normal Deploy (Production - Manual)

**Trigger**: `gh workflow run deploy-production.yml`

**Fluxo**:
```
1. GitHub Actions workflow:
   ├─> Migrate DB (apply new migrations only - PRESERVES DATA)
   ├─> Deploy backend to Railway
   ├─> Deploy frontend to Railway
   └─> Run smoke tests
```

**Database**: Preserva **TODOS** os dados, aplica apenas novas migrations.

**Características**:
- ✅ Usa imagens `staging-verified` (já testadas em staging)
- ✅ NO SEEDING (production data é real)
- ✅ NO RESET (preserva dados)

### 4. Fresh Start (Production - Manual, DANGEROUS)

**Trigger**: `./scripts/fresh-start-production.sh` ou `gh workflow run deploy-production.yml -f fresh_start=true`

⚠️⚠️⚠️ **DANGER: DESTROYS ALL PRODUCTION DATA** ⚠️⚠️⚠️

**Fluxo**:
```
1. GitHub Actions workflow:
   ├─> Reset DB (DROP SCHEMA CASCADE - DESTROYS ALL DATA)
   ├─> Migrate DB (recreate from scratch)
   ├─> Deploy backend to Railway
   ├─> Deploy frontend to Railway
   └─> Run smoke tests
```

**Database**: Apaga **TODOS OS DADOS** e recria do zero.

**Use APENAS quando**:
- Primeira vez deployando production
- Reset completo do sistema (com backup e comunicação com usuários)

**ANTES de rodar**:
- ✅ Criar backup do database
- ✅ Comunicar downtime com usuários
- ✅ Verificar que staging está funcionando
- ✅ Ter plano de rollback

## Container Entrypoint Behavior

O entrypoint do container (`scripts/docker-entrypoint-backend.sh`) tem comportamento **condicional**:

| Environment | `RUN_MIGRATIONS` | `SEED_E2E_DATABASE` | Behavior |
|-------------|------------------|---------------------|----------|
| **E2E Local** | `true` | `true` | Run migrations + seed |
| **Railway Staging** | `false` (default) | `false` (default) | Just start uvicorn |
| **Railway Production** | `false` (default) | `false` (default) | Just start uvicorn |

**Isso garante**:
- ✅ E2E local funciona standalone (docker-compose up)
- ✅ Railway não roda migrations duplicadas
- ✅ Railway não tenta fazer seed em produção

## Alembic Migrations

### Criando Nova Migration

```bash
# 1. Modificar modelos em src/synth_lab/models/orm/
# 2. Gerar migration automática
cd src/synth_lab/alembic
alembic revision --autogenerate -m "add user preferences table"

# 3. Revisar migration gerada em alembic/versions/
# 4. Testar localmente
alembic upgrade head

# 5. Commit e push
git add .
git commit -m "feat(db): add user preferences table"
git push origin main
# ↑ Workflow vai aplicar a migration automaticamente
```

### Migrations são Aditivas

Alembic migrations são **aditivas** e **idempotentes**:
- ✅ Seguro rodar múltiplas vezes (não quebra)
- ✅ Só aplica migrations que ainda não foram aplicadas
- ✅ Preserva dados existentes (a menos que você explicitamente delete)

### Rollback (se necessário)

```bash
# Ver histórico de migrations
alembic history

# Rollback para revision anterior
alembic downgrade -1

# Rollback para revision específica
alembic downgrade <revision>

# Rollback completo (DANGER)
alembic downgrade base
```

⚠️ **Production**: Rollback em production é arriscado. Sempre teste em staging primeiro.

## Seeding Strategy

### Staging

**Script**: `scripts/seed_database.py`

**Comportamento**:
```python
# Verifica se synth_groups tem dados
if db has data:
    skip seed (preserva dados existentes)
else:
    run seed (cria dados de teste)
```

**Dados de seed**:
- Usuários de teste
- Synth groups pré-configurados
- Experiments de exemplo
- Dados para smoke tests

**Quando roda**:
- ✅ Fresh start (sempre, porque DB está vazio)
- ✅ Deploy normal (só se synth_groups vazio)

### Production

**NO SEEDING** - production data é real user data.

Se precisar popular production inicialmente, faça manualmente via SQL ou script separado.

## Railway Configuration

### Environment Variables (CRITICAL)

Railway **NÃO deve** ter estas variáveis:
- ❌ `RUN_MIGRATIONS` (default `false` - workflow cuida disso)
- ❌ `SEED_E2E_DATABASE` (default `false` - não seed em prod)

Railway **DEVE** ter:
- ✅ `DATABASE_URL` - connection string do PostgreSQL
- ✅ `OPENAI_API_KEY` - para LLM calls
- ✅ `PORT` - porta do container (Railway seta automaticamente)
- ✅ Outras env vars (JWT, S3, etc.)

### Service Configuration

Cada serviço no Railway deve estar configurado com:
- **Source**: Docker Image
- **Image URL**: `ghcr.io/<user>/synth-lab-api:latest` (atualizado pelo workflow)
- **Healthcheck**: `/health` endpoint
- **Auto Deploy**: Disabled (workflow controla deploys)

## Troubleshooting

### Migration Failed

**Sintoma**: Workflow falha no step "Migrate DB"

**Causa**: Migration tem erro ou conflito

**Solução**:
```bash
# 1. Testar migration localmente
cd src/synth_lab/alembic
alembic upgrade head

# 2. Se falhar, revisar migration em alembic/versions/
# 3. Corrigir e commitar
# 4. Push novamente
```

### Container Não Inicia (502)

**Sintoma**: Railway mostra 502, health check falha

**Possíveis causas**:
1. **Migrations não rodaram** → DB schema desatualizado
2. **Env vars faltando** → Container crasha no startup
3. **Imagem não existe no GHCR** → Railway não consegue pull

**Solução**:
```bash
# Verificar logs do workflow
gh run list --workflow=deploy-staging.yml --limit 1
gh run view <run-id> --log

# Verificar logs do Railway
railway logs --service synth-lab-api --environment staging

# Se migrations não rodaram, trigger fresh start
./scripts/fresh-start-staging.sh
```

### Seed Não Rodou

**Sintoma**: Database vazio após deploy

**Causa**: `synth_groups` já tinha dados (seed é condicional)

**Solução**:
```bash
# Opção 1: Fresh start (apaga tudo)
./scripts/fresh-start-staging.sh

# Opção 2: Seed manual (preserva dados)
DATABASE_URL="postgresql://..." python scripts/seed_database.py
```

## Commands Reference

### GitHub CLI

```bash
# Trigger normal staging deploy
git push origin main

# Trigger fresh start staging
gh workflow run deploy-staging.yml -f fresh_start=true

# Trigger normal production deploy
gh workflow run deploy-production.yml

# Trigger fresh start production (DANGER)
gh workflow run deploy-production.yml -f fresh_start=true

# Monitor workflow
gh run watch

# View workflow logs
gh run list --workflow=deploy-staging.yml --limit 5
gh run view <run-id> --log
```

### Scripts

```bash
# Fresh start staging (interactive with confirmation)
./scripts/fresh-start-staging.sh

# Fresh start production (triple confirmation required)
./scripts/fresh-start-production.sh

# Manual seed (local database)
DATABASE_URL="postgresql://..." python scripts/seed_database.py
```

### Railway CLI

```bash
# View logs
railway logs --service synth-lab-api --environment staging

# Redeploy (without code changes)
railway redeploy --service synth-lab-api --environment staging

# View service info
railway service
```

## Best Practices

### Development

1. **Test migrations locally** antes de commit
2. **Never bypass pre-push hook** (`--no-verify`)
3. **Always use feature branches** para mudanças grandes de schema
4. **Review generated migrations** (não confie cegamente no autogenerate)

### Staging

1. **Use fresh start** quando quiser resetar completamente
2. **Normal deploys preservam dados** - bom para testar migrations incrementais
3. **Smoke tests validam deployment** - não ignore falhas

### Production

1. **NEVER use fresh start** a menos que seja absolutamente necessário
2. **Test migrations in staging first** - sempre
3. **Have rollback plan** antes de deploy
4. **Communicate downtime** com usuários se necessário
5. **Monitor after deploy** - logs, health checks, user reports

## Migration Patterns

### Adding Column (Safe)

```python
def upgrade():
    op.add_column('users', sa.Column('preferences', sa.JSON(), nullable=True))

def downgrade():
    op.drop_column('users', 'preferences')
```

✅ **Safe**: Não afeta dados existentes

### Renaming Column (Careful)

```python
# Opção 1: Rename (breaks old code)
def upgrade():
    op.alter_column('users', 'name', new_column_name='full_name')

# Opção 2: Add + Copy + Drop (safe with dual-write)
def upgrade():
    # 1. Add new column
    op.add_column('users', sa.Column('full_name', sa.String(), nullable=True))
    # 2. Copy data
    op.execute("UPDATE users SET full_name = name")
    # 3. Deploy code that uses both columns (dual-write)
    # 4. Later migration: drop old column
```

⚠️ **Careful**: Renaming requires code coordination

### Dropping Column (Dangerous)

```python
def upgrade():
    op.drop_column('users', 'old_field')
```

⚠️ **Dangerous**: Se código ainda usa essa coluna, vai quebrar

**Safe approach**:
1. Deploy code que NÃO usa a coluna
2. Wait (garante que nenhum pod antigo está rodando)
3. Deploy migration que remove a coluna

## FAQ

### Q: Posso rodar migrations diretamente no Railway?

❌ **Não recomendado**. Railway pode ter múltiplas réplicas do container, causando race conditions. Sempre rode migrations via workflow.

### Q: E se eu precisar de uma migration urgente?

```bash
# 1. Criar e testar migration localmente
alembic revision -m "urgent fix"
# ... editar migration ...
alembic upgrade head  # testar

# 2. Commit e push
git add . && git commit -m "fix(db): urgent migration"
git push origin main  # Workflow roda automaticamente

# 3. Se MUITO urgente, pode rodar manualmente:
# (conectar ao DB via Railway CLI)
railway run alembic upgrade head
```

### Q: Como fazer backup antes de fresh start?

```bash
# Via Railway
railway db backup

# Via pg_dump (se tiver acesso direto)
pg_dump $DATABASE_URL > backup.sql

# Restore
psql $DATABASE_URL < backup.sql
```

### Q: Posso fazer seed parcial (só alguns dados)?

Sim! Edite `scripts/seed_database.py` para ter flags opcionais:

```python
def seed_database(engine, seed_users=True, seed_experiments=True):
    if seed_users:
        # seed users
    if seed_experiments:
        # seed experiments
```

### Q: Como testar migrations em produção sem afetar usuários?

1. **Create staging clone**: Clone production DB para staging
2. **Test migration**: Rode migration em staging clonado
3. **Verify**: Teste app com schema novo
4. **Deploy**: Se tudo OK, deploy em production

```bash
# Clonar production para staging (Railway)
railway db clone production staging
```
