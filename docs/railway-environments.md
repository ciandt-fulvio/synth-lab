# Railway Environments - synth-lab

## Visão Geral

O projeto **synth-lab** está hospedado no Railway.com sob o nome **sunny-caring**. Possui 2 ambientes configurados:

- **Production**: Ambiente de produção ativo
- **Staging**: Ambiente de testes/homologação

## Serviços

O projeto possui 3 serviços em cada ambiente:

| Serviço | Descrição | Tecnologia |
|---------|-----------|------------|
| **synth-lab-frontend** | Interface web do usuário | React 18 + TypeScript 5.5 + Vite |
| **synth-lab-api** | API backend | Python 3.13 + FastAPI |
| **Postgres** | Banco de dados | PostgreSQL 17 |

## URLs dos Ambientes

### Production

- **Frontend**: https://synth-lab-frontend-production.up.railway.app
- **API**: https://synth-lab-api-production.up.railway.app
- **Status**: ✅ Ativo (últimos deploys bem-sucedidos)

### Staging

- **Frontend**: https://synth-lab-frontend-staging.up.railway.app
- **API**: https://synth-lab-api-staging.up.railway.app
- **Status**: ⚠️ Sem deploys ativos (configurado mas não deployado)

## Como Acessar

### Via Railway CLI

```bash
# Verificar autenticação
railway whoami

# Ver status do projeto atual
railway status

# Ver status completo em JSON
railway status --json

# Listar variáveis de ambiente (production)
railway variables --json

# Listar variáveis de ambiente de outro serviço
railway variables --service synth-lab-api --json
railway variables --service synth-lab-frontend --json

# Ver logs do serviço atual
railway logs

# Ver logs de um serviço específico
railway logs --service synth-lab-api
railway logs --service synth-lab-frontend

# Ver logs de um ambiente específico
railway logs --environment production
railway logs --environment staging
```

## Como Fazer Deploy

### Deploy Automático (Git Push)

⚠️ **Nota**: Atualmente os serviços não estão conectados a um repositório Git. Os deploys são manuais.

### Deploy Manual via CLI

#### Deploy do Backend (synth-lab-api)

```bash
# Na raiz do projeto
railway up --service synth-lab-api --environment production

# Para staging
railway up --service synth-lab-api --environment staging
```

#### Deploy do Frontend (synth-lab-frontend)

```bash
# Na raiz do projeto (ou dentro de /frontend)
railway up --service synth-lab-frontend --environment production

# Para staging
railway up --service synth-lab-frontend --environment staging
```

### Configuração dos Deploys

#### Backend (railway.toml na raiz)

```toml
[build]
builder = "dockerfile"
dockerfilePath = "Dockerfile"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 100
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3
```

#### Frontend (frontend/railway.toml)

```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "npx serve dist -s -l $PORT"
healthcheckPath = "/"
healthcheckTimeout = 100
```

## Variáveis de Ambiente

### Backend (synth-lab-api)

Principais variáveis configuradas em production:

```bash
DATABASE_URL=postgresql://postgres:***@postgres.railway.internal:5432/railway
OPENAI_API_KEY=sk-proj-***
RAILWAY_ENVIRONMENT=production
RAILWAY_PUBLIC_DOMAIN=synth-lab-api-production.up.railway.app
RAILWAY_PRIVATE_DOMAIN=synth-lab-api.railway.internal
```

### Frontend (synth-lab-frontend)

Principais variáveis configuradas em production:

```bash
VITE_API_URL=https://synth-lab-api-production.up.railway.app
RAILWAY_ENVIRONMENT=production
RAILWAY_PUBLIC_DOMAIN=synth-lab-frontend-production.up.railway.app
RAILWAY_PRIVATE_DOMAIN=synth-lab-frontend.railway.internal
```

### Como Gerenciar Variáveis

```bash
# Listar variáveis
railway variables --json

# Adicionar/modificar variável (via web ou CLI)
# Recomendado: Use o dashboard web para variáveis sensíveis
# URL: https://railway.app/project/39623a84-29a1-456a-bb93-c842bc6ae7d8
```

## Domínios Customizados

### Sobre RAILWAY_PUBLIC_DOMAIN

A variável `RAILWAY_PUBLIC_DOMAIN` é **gerenciada automaticamente** pelo Railway e **não pode ser modificada diretamente**. Porém, quando você adiciona um domínio customizado ao serviço, essa variável **se atualiza automaticamente** para refletir o novo domínio.

### Como Adicionar um Domínio Customizado

#### Via CLI

```bash
# Adicionar domínio customizado
railway domain seu-dominio.com --service synth-lab-api --environment production

# Ou gerar domínio Railway (default)
railway domain --service synth-lab-api --environment production

# Ver configuração em JSON
railway domain --json
```

#### Via Web Dashboard

1. Acesse o projeto: https://railway.app/project/39623a84-29a1-456a-bb93-c842bc6ae7d8
2. Selecione o serviço (ex: synth-lab-api)
3. Vá para a aba "Settings"
4. Na seção "Domains", clique em "Add Domain"
5. Digite seu domínio customizado (ex: `api.synth-lab.com`)
6. Railway fornecerá um CNAME (ex: `g05ns7.up.railway.app`)

#### Configurar DNS

No seu provedor de DNS (Cloudflare, Namecheap, GoDaddy, etc):

1. Crie um registro CNAME:
   - **Nome**: `api` (ou `@` para domínio raiz)
   - **Tipo**: CNAME
   - **Valor**: O CNAME fornecido pelo Railway (ex: `g05ns7.up.railway.app`)
   - **TTL**: Automático ou 3600

2. Aguarde a verificação (pode levar alguns minutos)

3. Quando verificado, você verá um ✅ ao lado do domínio no Railway

4. Railway automaticamente emitirá um certificado SSL

### Após Adicionar Domínio Customizado

**A variável `RAILWAY_PUBLIC_DOMAIN` será atualizada automaticamente:**

Antes:
```bash
RAILWAY_PUBLIC_DOMAIN=synth-lab-api-production.up.railway.app
```

Depois:
```bash
RAILWAY_PUBLIC_DOMAIN=api.synth-lab.com
```

### Domínios Wildcard

Railway suporta domínios wildcard:

```bash
railway domain "*.synth-lab.com" --service synth-lab-api
```

Isso permite subdomínios como:
- `api.synth-lab.com`
- `staging-api.synth-lab.com`
- `dev-api.synth-lab.com`

### Referências entre Serviços

Para referenciar o domínio de outro serviço em variáveis de ambiente:

```bash
# No frontend, referenciar o backend
VITE_API_URL=https://${{synth-lab-api.RAILWAY_PUBLIC_DOMAIN}}

# Para comunicação interna (mais rápido), use RAILWAY_PRIVATE_DOMAIN
INTERNAL_API_URL=http://${{synth-lab-api.RAILWAY_PRIVATE_DOMAIN}}
```

### Verificar Domínios Atuais

```bash
# Ver domínios do serviço atual
railway domain

# Ver todos os domínios em JSON
railway status --json | grep -A 10 '"domains"'
```

**Domínios atuais:**
- `serviceDomains`: Domínios gerados pelo Railway (*.up.railway.app)
- `customDomains`: Domínios customizados configurados

### Troubleshooting

**Problema**: `RAILWAY_PUBLIC_DOMAIN` está vazio após deploy

**Solução**:
1. Remova o public networking no dashboard
2. Re-adicione o public networking
3. Faça redeploy: `railway redeploy`

**Problema**: Domínio customizado não verifica

**Solução**:
1. Verifique se o CNAME está correto no DNS
2. Use ferramentas como `dig` ou `nslookup`:
   ```bash
   dig api.synth-lab.com CNAME
   nslookup api.synth-lab.com
   ```
3. Aguarde propagação DNS (pode levar até 24h, mas geralmente 5-10 minutos)

## Comandos Úteis

### Verificar Status dos Deploys

```bash
# Status completo em JSON (inclui deploys, domínios, etc)
railway status --json

# Ver logs em tempo real
railway logs --service synth-lab-api --environment production

# Ver últimas N linhas de log
railway logs --service synth-lab-api --lines 100
```

### Redeployar uma Aplicação

```bash
# Fazer redeploy do último deployment bem-sucedido
railway redeploy --service synth-lab-api --environment production
```

### Filtrar Logs

```bash
# Ver apenas erros
railway logs --filter "@level:error"

# Ver warns relacionados a rate limiting
railway logs --filter "@level:warn AND rate limit"

# Últimos 10 erros
railway logs --lines 10 --filter "@level:error"
```

## Configuração do Banco de Dados

### Production

- **Engine**: PostgreSQL 17
- **Volume**: 500 MB (atual: ~98 MB usado)
- **Mount Path**: `/var/lib/postgresql/data`
- **Conexão Interna**: `postgres.railway.internal:5432`

### Staging

- **Engine**: PostgreSQL 17
- **Volume**: 500 MB (atual: ~97 MB usado)
- **Mount Path**: `/var/lib/postgresql/data`
- **Conexão Interna**: `postgres.railway.internal:5432`

## Healthchecks

### Backend

- **Path**: `/health`
- **Timeout**: 100s
- **Restart Policy**: On failure (max 3 retries)

### Frontend

- **Path**: `/`
- **Timeout**: 100s
- **Restart Policy**: On failure (max 10 retries)

## Workflow Recomendado

1. **Desenvolvimento Local**
   - Desenvolva e teste localmente
   - Use `uv run uvicorn synth_lab.api.main:app --reload` para backend
   - Use `npm run dev` para frontend

2. **Deploy para Staging**
   ```bash
   # Backend
   railway up --service synth-lab-api --environment staging

   # Frontend
   railway up --service synth-lab-frontend --environment staging
   ```

3. **Teste em Staging**
   - Acesse https://synth-lab-frontend-staging.up.railway.app
   - Valide funcionalidades
   - Verifique logs: `railway logs --environment staging`

4. **Deploy para Production**
   ```bash
   # Backend
   railway up --service synth-lab-api --environment production

   # Frontend
   railway up --service synth-lab-frontend --environment production
   ```

5. **Monitorar Production**
   ```bash
   # Logs em tempo real
   railway logs --service synth-lab-api --environment production

   # Verificar status
   railway status
   ```

## Troubleshooting

### Serviço não inicia

1. Verifique logs: `railway logs --service <service-name> --lines 100`
2. Verifique variáveis de ambiente: `railway variables --service <service-name> --json`
3. Verifique healthcheck path está respondendo

### Deploy falhou

1. Veja logs de build: `railway logs --build`
2. Verifique se o Dockerfile/railway.toml está correto
3. Verifique se as dependências estão corretas

### Banco de dados não conecta

1. Verifique se a variável `DATABASE_URL` está correta
2. Verifique se o serviço Postgres está rodando: `railway status`
3. Verifique logs do Postgres: `railway logs --service Postgres`

## Referências

- **Railway CLI Docs**: https://docs.railway.com/guides/cli
- **Railway Project Dashboard**: https://railway.app/project/39623a84-29a1-456a-bb93-c842bc6ae7d8
- **CLI Version**: 4.16.1
