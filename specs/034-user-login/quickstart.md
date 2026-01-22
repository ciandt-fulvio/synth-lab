# Quickstart: Autenticação Google OAuth 2.0

**Feature**: 034-user-login
**Data**: 2026-01-22
**Status**: Guia de configuração e desenvolvimento

## Índice

1. [Pré-requisitos](#pré-requisitos)
2. [Configuração do Google Cloud](#configuração-do-google-cloud)
3. [Configuração do Ambiente Local](#configuração-do-ambiente-local)
4. [Configuração do Railway (Produção)](#configuração-do-railway-produção)
5. [Executando Localmente](#executando-localmente)
6. [Testando a Autenticação](#testando-a-autenticação)
7. [Troubleshooting](#troubleshooting)

---

## Pré-requisitos

- Python 3.13+
- Node.js 20+
- PostgreSQL 14+
- Conta no Google Cloud Platform
- Conta no Railway (para produção)

---

## Configuração do Google Cloud

### 1. Criar Projeto no Google Cloud Console

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto ou selecione um existente
3. Nome sugerido: "Synth-Lab OAuth"

### 2. Ativar Google+ API

1. No menu lateral, vá em **APIs & Services** > **Library**
2. Busque por "Google+ API"
3. Clique em **Enable**

### 3. Configurar Tela de Consentimento OAuth

1. Vá em **APIs & Services** > **OAuth consent screen**
2. Escolha **External** (para permitir qualquer conta Google)
3. Preencha os campos obrigatórios:
   - **App name**: Synth-Lab
   - **User support email**: seu email
   - **Developer contact**: seu email
4. Em **Scopes**, adicione:
   - `openid`
   - `email`
   - `profile`
5. Salve e continue

### 4. Criar Credenciais OAuth 2.0

1. Vá em **APIs & Services** > **Credentials**
2. Clique em **+ CREATE CREDENTIALS** > **OAuth client ID**
3. Escolha **Web application**
4. Configure:
   - **Name**: Synth-Lab Web Client
   - **Authorized JavaScript origins**:
     - `http://localhost:5173` (frontend local)
     - `http://localhost:8000` (backend local)
     - `https://synth-lab.up.railway.app` (produção)
   - **Authorized redirect URIs**:
     - `http://localhost:8000/auth/callback` (local)
     - `https://synth-lab.up.railway.app/auth/callback` (produção)
5. Clique em **CREATE**
6. **IMPORTANTE**: Copie o **Client ID** e **Client Secret** - você vai precisar deles

---

## Configuração do Ambiente Local

### 1. Clonar e Configurar Repositório

```bash
# Já deve estar no diretório do projeto
cd synth-lab
git checkout 034-user-login
```

### 2. Configurar Variáveis de Ambiente

Crie ou edite `.env.local`:

```bash
# Google OAuth
GOOGLE_CLIENT_ID=SEU_CLIENT_ID_AQUI.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=SEU_CLIENT_SECRET_AQUI

# JWT
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# Whitelist (comma-separated emails and domains)
# Adicione seu email e/ou domínio aqui
WHITELIST=seu-email@gmail.com,@seu-dominio.com

# Database
DATABASE_URL=postgresql://synthlab:synthlab_dev@localhost:5432/synthlab

# CORS
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:8000

# Server
HOST=0.0.0.0
PORT=8000
```

**IMPORTANTE**: Substitua `seu-email@gmail.com` pelo email que você vai usar para testar.

### 3. Gerar JWT Secret

```bash
# Linux/Mac
openssl rand -hex 32

# Copie o resultado e cole no .env.local como JWT_SECRET_KEY
```

### 4. Instalar Dependências Backend

```bash
# Adicionar novas dependências
uv add authlib python-jose slowapi

# Instalar todas as dependências
uv sync
```

### 5. Instalar Dependências Frontend

```bash
cd frontend
npm install @react-oauth/google
cd ..
```

### 6. Executar Migrations

```bash
# Criar a migration (depois que as entities forem implementadas)
uv run alembic revision --autogenerate -m "Add user authentication tables"

# Aplicar a migration
uv run alembic upgrade head
```

---

## Configuração do Railway (Produção)

### 1. Configurar Variáveis de Ambiente no Railway

No dashboard do Railway, vá em **Variables** e adicione:

```
GOOGLE_CLIENT_ID=SEU_CLIENT_ID_PRODUCAO
GOOGLE_CLIENT_SECRET=SEU_CLIENT_SECRET_PRODUCAO
JWT_SECRET_KEY=GERE_UM_NOVO_SECRET_PARA_PRODUCAO
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30
WHITELIST=usuario@empresa.com,@empresa.com
FRONTEND_URL=https://seu-dominio-frontend.app
BACKEND_URL=https://synth-lab.up.railway.app
```

**IMPORTANTE**:
- Use Client ID/Secret de PRODUÇÃO (diferentes do local)
- Gere um JWT_SECRET_KEY DIFERENTE para produção
- Configure a WHITELIST com emails/domínios autorizados

### 2. Atualizar URIs no Google Cloud

No Google Cloud Console, adicione as URIs de produção:
- **Authorized JavaScript origins**: `https://synth-lab.up.railway.app`
- **Authorized redirect URIs**: `https://synth-lab.up.railway.app/auth/callback`

---

## Executando Localmente

### 1. Iniciar PostgreSQL

```bash
# Via Docker
make dev-up

# OU manualmente
podman start synthlab-postgres-dev
```

### 2. Iniciar Backend

```bash
# Terminal 1
uv run uvicorn synth_lab.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Iniciar Frontend

```bash
# Terminal 2
cd frontend
npm run dev
```

### 4. Verificar

- Backend: http://localhost:8000/docs (Swagger UI)
- Frontend: http://localhost:5173

---

## Testando a Autenticação

### 1. Teste de Login Completo

1. Acesse http://localhost:5173
2. Clique em "Sign in with Google"
3. Escolha sua conta Google (deve estar na WHITELIST)
4. Autorize o aplicativo
5. Você deve ser redirecionado de volta para o app, autenticado

### 2. Verificar Token no DevTools

Abra DevTools (F12) > Application > Cookies:
- Deve haver um cookie `session` com valor JWT
- Flags: `HttpOnly`, `Secure` (em produção), `SameSite=Lax`

### 3. Testar Endpoint /auth/me

```bash
# Com cookie (use o browser ou ferramentas que preservam cookies)
curl -X GET http://localhost:8000/auth/me \
  --cookie "session=SEU_TOKEN_JWT_AQUI" \
  -H "Content-Type: application/json"

# Resposta esperada:
# {
#   "id": "uuid",
#   "email": "seu-email@gmail.com",
#   "display_name": "Seu Nome",
#   "google_user_id": "..."
# }
```

### 4. Testar Whitelist

Tente fazer login com um email NÃO listado na WHITELIST:
- Deve receber erro 403: "Email not authorized"

### 5. Testar Compartilhamento

```bash
# Compartilhar um experimento
curl -X POST http://localhost:8000/experiments/{experiment_id}/shares \
  --cookie "session=SEU_TOKEN_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "user_email": "colega@example.com",
    "permission_level": "editor"
  }'

# Listar compartilhamentos
curl -X GET http://localhost:8000/experiments/{experiment_id}/shares \
  --cookie "session=SEU_TOKEN_JWT"
```

---

## Troubleshooting

### Erro: "redirect_uri_mismatch"

**Causa**: A URI de callback não está configurada no Google Cloud.

**Solução**:
1. Verifique a URI exata no erro
2. Adicione essa URI em **Authorized redirect URIs** no Google Cloud Console
3. Aguarde alguns segundos para propagar

### Erro: "Email not authorized"

**Causa**: O email não está na WHITELIST.

**Solução**:
1. Adicione o email ou domínio na variável `WHITELIST` no `.env.local`
2. Reinicie o backend para recarregar a whitelist

### Erro: "CORS policy"

**Causa**: Frontend e backend em portas diferentes.

**Solução**:
1. Verifique se `FRONTEND_URL` no `.env.local` está correta
2. Verifique se o middleware CORS está configurado no FastAPI

### Token JWT inválido

**Causa**: Secret key mudou ou token expirou.

**Solução**:
1. Limpe os cookies no browser (DevTools > Application > Clear site data)
2. Faça login novamente

### "User not found" ao compartilhar

**Causa**: O usuário com quem você está tentando compartilhar nunca fez login.

**Solução**:
1. Peça para o usuário fazer login primeiro (isso cria o registro na tabela `users`)
2. Depois compartilhe usando o email dele

### Database migration error

**Causa**: Migrations não foram aplicadas.

**Solução**:
```bash
# Verificar status
uv run alembic current

# Aplicar pendentes
uv run alembic upgrade head

# Se necessário, resetar
uv run alembic downgrade base
uv run alembic upgrade head
```

---

## Próximos Passos

Após configurar a autenticação:

1. **Implementar testes** (`/speckit.tasks`)
2. **Adicionar owner_id aos experimentos existentes** (data migration)
3. **Implementar UI de compartilhamento** no frontend
4. **Configurar rate limiting** para produção
5. **Configurar logging e monitoring** (Phoenix traces)

---

## Referências

- [Google OAuth 2.0 Docs](https://developers.google.com/identity/protocols/oauth2)
- [Authlib Documentation](https://docs.authlib.org/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Railway Environment Variables](https://docs.railway.app/develop/variables)
- [JWT Best Practices](https://datatracker.ietf.org/doc/html/rfc8725)

---

## Checklist de Configuração

- [ ] Projeto criado no Google Cloud
- [ ] OAuth consent screen configurado
- [ ] Credenciais OAuth criadas (Client ID + Secret)
- [ ] Redirect URIs configuradas (local + produção)
- [ ] `.env.local` criado com todas as variáveis
- [ ] JWT_SECRET_KEY gerado
- [ ] WHITELIST configurada com seu email
- [ ] Dependências instaladas (backend + frontend)
- [ ] Database migrations aplicadas
- [ ] Backend rodando (http://localhost:8000/docs)
- [ ] Frontend rodando (http://localhost:5173)
- [ ] Login testado com sucesso
- [ ] Railway configurado (somente produção)
- [ ] Variáveis de ambiente Railway configuradas

---

**Última atualização**: 2026-01-22
**Mantenedores**: Synth-Lab Team
