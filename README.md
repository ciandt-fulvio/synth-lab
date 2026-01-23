# SynthLab - Gerador de Personas Sintéticas

> Gerador de personas sintéticas (Synths) com atributos demográficos, psicográficos, comportamentais e cognitivos realistas, baseados em dados do IBGE e pesquisas verificadas.

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Objetivo

Criar Synths representativos da população brasileira para:
- **Pesquisas de UX qualitativas** com entrevistas simuladas
- Testes de UX e design de interfaces
- Simulações Monte Carlo e modelagem estatística
- Validação de acessibilidade e inclusão
- Pesquisas de mercado e segmentação
- Desenvolvimento e validação de produtos

## ✨ Características

### 🚀 API REST Moderna (NOVO!)
- **FastAPI** standalone com documentação automática em `/docs`
- **Arquitetura em 3 camadas**: Interface → Service → Database
- **PostgreSQL** com SQLAlchemy ORM para persistência de dados
- **17 endpoints REST** para synths, research, topics e PR-FAQ
- **Streaming SSE** para execução de pesquisas em tempo real
- **Jobs assíncronos** para geração de relatórios
- **Paginação** e filtros avançados
- **CORS** configurado para desenvolvimento web

### Interface CLI Simplificada
- 🎨 **Saída colorida e formatada** com biblioteca Rich
- ⚡ **Comando principal**: `synthlab gensynth` para geração de personas sintéticas
- 🖼️ **Geração de avatares** via OpenAI API com controle de blocos (9 avatares por bloco)
- 📊 **Benchmark integrado** para análise de performance
- 🔇 **Modo silencioso** para integração em pipelines
- ✅ **Validação e análise** de distribuições demográficas

> 📝 **Nota**: Outras funcionalidades (pesquisas UX, topic guides, PR-FAQ) estão disponíveis via **REST API** - veja seção [API REST](#-api-rest-moderna-novo)

### Dados Realistas (Schema v2.3.0)
- **Atributos Demográficos**: Idade, gênero, localização, escolaridade, renda, ocupação (IBGE Censo 2022, PNAD 2022/2023)
- **Atributos Psicográficos**: Personalidade Big Five, interesses, inclinação política/religiosa
- **Atributos Comportamentais**: Hábitos de consumo, padrões de mídia social
- **Limitações Físicas/Cognitivas**: Deficiências visuais, auditivas, motoras, cognitivas (IBGE PNS 2019)
- **Capacidades Tecnológicas**: Alfabetização digital, dispositivos, familiaridade com plataformas (TIC Domicílios 2023)
- **Vieses Comportamentais**: 7 vieses cognitivos alinhados com traços de personalidade (literatura acadêmica)

## 🚀 Instalação

### Pré-requisitos

- Python 3.13 ou superior
- `uv` (gerenciador de pacotes)
- OpenAI API Key (para geração de avatares e entrevistas)

### Setup

```bash
# Clone o repositório
git clone <repo-url>
cd synth-lab

# Instalar dependências (uv cria automaticamente o .venv)
uv sync

# Configurar variável de ambiente
export OPENAI_API_KEY="sk-your-api-key-here"

# Pronto! Use uv run para executar comandos
uv run synthlab --help
```

> **Nota**: Não é necessário ativar o ambiente virtual ou instalar o pacote. O `uv run` gerencia tudo automaticamente, executando comandos diretamente no ambiente isolado.

### Iniciar API REST

```bash
# Iniciar servidor FastAPI
./scripts/start_api.sh

# Ou manualmente
uv run uvicorn src.synth_lab.api.main:app --reload --host 0.0.0.0 --port 8000

# Acessar documentação interativa
open http://localhost:8000/docs
```

### 🔐 Autenticação e Controle de Acesso

O SynthLab implementa autenticação via Google OAuth 2.0 com controle de acesso baseado em whitelist de emails/domínios.

#### Configuração do Google OAuth

1. **Criar Projeto no Google Cloud Console**:
   - Acesse [Google Cloud Console](https://console.cloud.google.com/)
   - Crie um novo projeto ou selecione um existente
   - Ative a API "Google+ API" ou "People API"

2. **Configurar OAuth Consent Screen**:
   - Navegue para "APIs & Services" → "OAuth consent screen"
   - Escolha "External" se for para uso público
   - Preencha informações básicas (nome do app, email de suporte)
   - Adicione escopos: `userinfo.email`, `userinfo.profile`, `openid`

3. **Criar OAuth 2.0 Client ID**:
   - Navegue para "APIs & Services" → "Credentials"
   - Clique em "Create Credentials" → "OAuth client ID"
   - Tipo: "Web application"
   - Authorized redirect URIs:
     - Desenvolvimento: `http://localhost:8000/auth/callback`
     - Produção: `https://seu-dominio.com/auth/callback`
   - Copie o **Client ID** e **Client Secret**

#### Variáveis de Ambiente para Autenticação

Adicione ao seu arquivo `.env`:

```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret_here
OAUTH_REDIRECT_URI=http://localhost:8000/auth/callback

# JWT Session Management
JWT_SECRET_KEY=your_secret_key_min_32_chars_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email/Domain Whitelist (comma-separated)
# Examples:
# - Specific emails: user1@example.com,user2@example.com
# - Entire domain: @company.com
# - Mixed: user@gmail.com,@yourcompany.com
WHITELIST=user@example.com,@yourcompany.com

# Session Secret (for OAuth state CSRF protection)
SESSION_SECRET_KEY=your_session_secret_key_min_32_chars_here

# Frontend URL (for OAuth callback redirect)
FRONTEND_URL=http://localhost:5173

# Environment (enables secure cookies in production)
ENVIRONMENT=development  # or 'production'
```

#### Gerar Secrets Seguros

```bash
# Gerar JWT_SECRET_KEY (32+ caracteres)
openssl rand -hex 32

# Gerar SESSION_SECRET_KEY (32+ caracteres)
openssl rand -hex 32
```

#### Configurar Whitelist

A whitelist controla quais usuários podem acessar o sistema:

```bash
# Permitir emails específicos
WHITELIST=alice@example.com,bob@example.com

# Permitir domínio inteiro
WHITELIST=@yourcompany.com

# Misto: emails específicos + domínio
WHITELIST=alice@gmail.com,bob@hotmail.com,@yourcompany.com
```

#### Primeiro Login

1. Inicie o servidor: `uv run uvicorn src.synth_lab.api.main:app --reload`
2. Acesse o frontend: `http://localhost:5173`
3. Clique em "Login with Google"
4. Autorize o aplicativo no Google
5. Se seu email estiver na whitelist, você será autenticado
6. Um token JWT será armazenado em cookie HTTP-only

#### Migração de Dados (Para Deployments Existentes)

Se você já tem experiments e synth_groups no banco de dados, execute o script de migração para atribuir ownership:

```bash
# Primeiro, obtenha o UUID do usuário que será o owner
# (faça login uma vez e consulte a tabela users no banco)

# Preview das mudanças (dry-run)
export MIGRATION_OWNER_ID="550e8400-e29b-41d4-a716-446655440000"
uv run python scripts/migrate_ownership.py --dry-run

# Aplicar migração (após confirmar preview)
uv run python scripts/migrate_ownership.py

# Ou especificar owner via argumento
uv run python scripts/migrate_ownership.py --owner-id "550e8400-e29b-41d4-a716-446655440000"
```

#### Endpoints de Autenticação

```bash
# Login (redireciona para Google OAuth)
GET http://localhost:8000/auth/login

# Callback (gerenciado automaticamente pelo Google)
GET http://localhost:8000/auth/callback?code=...&state=...

# Obter usuário atual
GET http://localhost:8000/auth/me

# Logout
POST http://localhost:8000/auth/logout
```

#### Compartilhamento de Recursos

Depois de autenticado, você pode compartilhar experiments e synth_groups com outros usuários:

```bash
# Compartilhar experiment (automaticamente compartilha synth_group associado)
POST http://localhost:8000/auth/experiments/{experiment_id}/shares
Body: {"user_id": "uuid-do-usuario", "permission_level": "viewer"}  # ou "editor"

# Listar compartilhamentos de um experiment
GET http://localhost:8000/auth/experiments/{experiment_id}/shares

# Revogar acesso
DELETE http://localhost:8000/auth/experiments/{experiment_id}/shares/{user_id}
```

Para documentação completa da API de autenticação e compartilhamento, veja:
- **Contrato OpenAPI**: `specs/034-user-login/contracts/auth-api.yaml`
- **Auditoria de Segurança**: `specs/034-user-login/SECURITY_AUDIT.md`

### 🐳 Docker Development (Recomendado)

O SynthLab oferece ambientes Docker pré-configurados para desenvolvimento e testes:

```bash
# Desenvolvimento com hot reload (recomendado)
make dev-up        # Inicia frontend (8080), backend (8000), postgres (5432)
make dev-logs      # Ver logs de todos os serviços
make dev-down      # Para o ambiente

# Testes Backend (ambiente isolado com PostgreSQL)
make test                  # Executa todos os testes backend (846+ testes)
make test-fast             # Testes rápidos (unit only, sem integração)

# Testes E2E (ambiente isolado)
make test-e2e              # Executa tudo: build + start + test + cleanup
make test-e2e-docker-up    # Inicia ambiente para debug (portas 8091, 8001, 5433)
make test-e2e-docker-down  # Para e limpa o ambiente
```

**Características do ambiente de desenvolvimento:**
- ✅ Hot reload para backend (uvicorn --reload com polling)
- ✅ HMR (Hot Module Replacement) para frontend (Vite)
- ✅ Volume mounts para código fonte
- ✅ PostgreSQL persistente para dados de desenvolvimento

**Características do ambiente de testes:**
- ✅ Imagens de produção (sem volume mounts)
- ✅ PostgreSQL efêmero (dados limpos a cada execução)
- ✅ Portas separadas (não conflita com ambiente de dev)
- ✅ Seed de dados de teste automático
- ✅ Migrações Alembic aplicadas automaticamente
- ✅ Isolamento de transações (SAVEPOINT) por teste

> 📖 Para documentação detalhada, veja [Docker Development Guide](docs/docker-development.md)

### 🚀 CI/CD Pipeline

O projeto usa GitHub Actions com pipeline automatizado:

```
push → lint → build → test → deploy
```

**Workflows:**
- **PR/Push**: Lint, build e testes (backend + E2E)
- **Staging**: Deploy automático para Railway (staging)
- **Production**: Deploy manual via workflow dispatch

**Ambientes:**
- **Staging**: `synth-lab-*-staging.up.railway.app`
- **Production**: `synth-lab-*.up.railway.app`

## 📖 Uso

### Interface de Linha de Comando

O SynthLab oferece uma CLI intuitiva com saída colorida para melhor experiência do usuário.

**Todos os comandos usam `uv run` para execução automática no ambiente virtual**:

```bash
# Ver ajuda geral
uv run synthlab --help

# Ver versão
uv run synthlab --version

# Ver ajuda do comando gensynth
uv run synthlab gensynth --help
```

> 💡 **Para outras funcionalidades** (consultas, pesquisas UX, topic guides, PR-FAQ), use a **REST API** - veja [documentação da API](#api-rest)

### Comandos Disponíveis

#### Gerar Synths

```bash
# Gerar um Synth individual
uv run synthlab gensynth -n 1

# Gerar batch de Synths
uv run synthlab gensynth -n 100
uv run synthlab gensynth -n 1000

# 🎨 NOVO: Gerar Synths com avatares visuais
uv run synthlab gensynth -n 9 --avatar

# Gerar com número customizado de blocos de avatares (1 bloco = 9 avatares)
uv run synthlab gensynth --avatar -b 3  # Gera 27 avatares (3 blocos)

# Combinar com outras opções
uv run synthlab gensynth -n 18 --avatar --benchmark

# Com benchmark de performance
uv run synthlab gensynth -n 100 --benchmark

# Modo silencioso (minimal output)
uv run synthlab gensynth -n 100 --quiet

# Output em diretório customizado
uv run synthlab gensynth -n 10 --output ./meus-synths/
```

#### 🎨 Geração de Avatares

Gere imagens de avatares visuais realistas para synths usando a OpenAI API (gpt-image-1-mini 2).

**Requisitos**:
```bash
# Configure sua chave API OpenAI
export OPENAI_API_KEY="sk-your-api-key-here"
```

**Uso**:
```bash
# Gerar 9 synths com avatares (1 bloco)
uv run synthlab gensynth -n 9 --avatar

# Gerar múltiplos blocos de avatares
uv run synthlab gensynth -n 18 --avatar  # 2 blocos automáticos
uv run synthlab gensynth --avatar -b 5   # 5 blocos explícitos (45 avatares)

# Gerar avatares para synths existentes (User Story 3)
uv run synthlab gensynth --avatar  # Auto-detecta synths sem avatar e gera para todos
uv run synthlab gensynth --avatar --synth-ids syn001,syn002,syn003  # IDs específicos
uv run synthlab gensynth --avatar --synth-ids syn010,syn011,syn012,syn013,syn014,syn015,syn016,syn017,syn018  # 9 IDs = 1 bloco

# Combinar com outras opções
uv run synthlab gensynth -n 27 --avatar --benchmark
```

**Características**:
- 🖼️ Avatares 341x341 pixels em formato PNG
- 🎭 Filtros visuais variados (B&W, sepia, warm, cool, 3D style)
- 👥 Diversidade demográfica precisa (idade, gênero, etnia)
- 💼 Backgrounds relacionados à profissão
- 💰 Custo: ~$0.02 por bloco (9 avatares) usando gpt-image-1-mini 2
- 📁 Salvos em: `data/synths/avatar/{synth-id}.png`

**Funcionalidades Avançadas**:
- ✅ **Auto-detecção**: Simplesmente rode `--avatar` para gerar avatares apenas para synths que não os possuem
- ✅ Retry automático com exponential backoff para rate limits
- ✅ Delay entre blocos para evitar throttling
- ✅ Progress indicators em tempo real
- ✅ Tratamento de erros robusto
- ✅ Validação de dados antes da geração
- ✅ Confirmação antes de sobrescrever avatares existentes
- ✅ Geração de avatares para synths específicos (via --synth-ids)

#### Validar Synths

```bash
# Validar todos os Synths no diretório
uv run synthlab gensynth --validate-all

# Validar um arquivo específico
uv run synthlab gensynth --validate-file data/synths/abc123.json

# Executar testes de validação internos
uv run synthlab gensynth --validar
```

#### Analisar Distribuições

```bash
# Analisar distribuição regional vs IBGE
uv run synthlab gensynth --analyze region

# Analisar distribuição etária vs IBGE
uv run synthlab gensynth --analyze age

# Analisar ambas as distribuições
uv run synthlab gensynth --analyze all
```

#### Consultar Synths (via REST API)

> 📝 **Nota**: A funcionalidade de consulta de synths está disponível via **REST API**. Veja a [documentação completa da API](#-api-rest-moderna-novo).

```bash
# Iniciar o servidor da API
uv run python -m synth_lab.api.main

# Listar todos os Synths gerados (com paginação)
curl http://localhost:8000/synths/list

# Obter detalhes de um synth específico
curl http://localhost:8000/synths/{synth_id}

# Obter avatar de um synth
curl http://localhost:8000/synths/{synth_id}/avatar
```

**Endpoints disponíveis**:
- `GET /synths/list` - Lista todos os synths com paginação
- `GET /synths/{synth_id}` - Retorna dados completos de um synth
- `GET /synths/{synth_id}/avatar` - Retorna caminho do avatar (se existir)

> **Nota**: Para consultas SQL personalizadas e filtros avançados, conecte-se diretamente ao PostgreSQL via `psql` ou use ferramentas como pgAdmin, DBeaver, etc.

#### Topic Guides (Materiais de Contexto) - via REST API

> 📝 **Nota**: A funcionalidade de topic guides está disponível via **REST API**. Veja a [documentação completa da API](#-api-rest-moderna-novo).

```bash
# Iniciar o servidor da API
uv run python -m synth_lab.api.main

# Listar todos os topic guides
curl http://localhost:8000/topics/list

# Obter detalhes de um topic guide específico
curl http://localhost:8000/topics/{topic_name}
```

**Endpoints disponíveis**:
- `GET /topics/list` - Lista todos os topic guides disponíveis
- `GET /topics/{topic_name}` - Retorna detalhes completos de um topic guide

**Gerenciamento manual de arquivos:**
Topic guides são criados manualmente no diretório `data/topic_guides/`. Para criar um novo:

1. Crie o diretório: `mkdir -p data/topic_guides/amazon-ecommerce`
2. Adicione arquivos: `cp screenshots/*.png data/topic_guides/amazon-ecommerce/`
3. A API detectará automaticamente o novo topic guide

**Tipos de arquivos suportados:**
- Imagens: PNG, JPEG (via OpenAI Vision API)
- Documentos: PDF, Markdown (.md), Text (.txt)

> **Nota**: As descrições dos arquivos são geradas com IA usando gpt-4o-mini e armazenadas em `summary.md` para uso nas entrevistas de pesquisa UX.

#### Entrevistas de Pesquisa UX - via REST API

> 📝 **Nota**: A funcionalidade de entrevistas de pesquisa UX está disponível via **REST API**. Veja a [documentação completa da API](#-api-rest-moderna-novo).

```bash
# Iniciar o servidor da API
uv run python -m synth_lab.api.main

# Listar todas as execuções de pesquisa
curl http://localhost:8000/research/list

# Obter detalhes de uma execução específica
curl http://localhost:8000/research/{execution_id}

# Obter resumo de uma pesquisa (se disponível)
curl http://localhost:8000/research/{execution_id}/summary
```

**Endpoints disponíveis**:
- `GET /research/list` - Lista todas as execuções de pesquisa com paginação
- `GET /research/{execution_id}` - Retorna detalhes completos de uma execução
- `GET /research/{execution_id}/summary` - Retorna resumo agregado (se existir)

**Características do Sistema de Pesquisa**:
- ⚡ **Paralelização automática**: Múltiplas entrevistas simultâneas (com rate limiting)
- 📊 **Sumarização automática**: Gera `batch_summary.json` com insights agregados
- 🔄 **Retry automático**: Trata rate limits e erros transitórios
- 📁 **Saída organizada**: Todas as transcrições em subdiretório com timestamp
- 🎯 **Filtros flexíveis**: Por IDs específicos, limite, ou auto-detecção
- 📈 **Progress reporting**: Barra de progresso em tempo real

> **Nota**: Requer `OPENAI_API_KEY` configurada. As entrevistas usam dois LLMs em conversa - um como entrevistador UX e outro como o synth (persona), com comportamento baseado no Big Five personality. Transcrições são salvas automaticamente em JSON.
>
> **Topic Guide Obrigatório**: Cada entrevista requer um topic guide que deve conter:
> - **script.json**: Roteiro de perguntas estruturado (array com `id` e `ask`)
> - **summary.md**: Contexto geral e descrições IA dos materiais
> - **Arquivos de contexto**: Imagens, PDFs, documentos referenciados
>
> **Function Calling Integrado**: O sistema automaticamente:
> - Carrega o **resumo contextual** e as **descrições IA** de todas as imagens/PDFs/documentos
> - Disponibiliza uma **ferramenta de function calling** para o LLM carregar imagens dinamicamente durante a entrevista
> - O entrevistador pode "ver" as imagens reais (via Vision API) quando necessário, não apenas as descrições de texto
> - Isso permite que o LLM faça perguntas mais específicas sobre elementos visuais durante a entrevista

### Estrutura de Saída

Os Synths são salvos como arquivos JSON em `data/synths/` com identificadores únicos. Cada Synth contém:

- **Identificação**: ID único (6 chars), nome completo, arquétipo, descrição, link para foto
- **Demografia**: Idade, gênero biológico/identidade, raça/etnia, localização, escolaridade, renda, ocupação, estado civil, composição familiar
- **Psicografia**: Big Five (abertura, conscienciosidade, extroversão, amabilidade, neuroticismo), interesses, inclinação política/religiosa
- **Comportamento**: Hábitos de consumo, padrões de mídia, fonte de notícias, lealdade a marca, engajamento em redes sociais
- **Deficiências**: Limitações visuais, auditivas, motoras (cadeira de rodas), cognitivas (se aplicável)
- **Capacidades Tecnológicas**: Alfabetização digital, dispositivos (principal, qualidade), preferências de acessibilidade (zoom, contraste), velocidade de digitação, frequência de internet, familiaridade com plataformas
- **Vieses Comportamentais**: Aversão à perda, desconto hiperbólico, suscetibilidade a chamariz, ancoragem, viés de confirmação, viés de status quo, sobrecarga de informação (alinhados com traços de personalidade)
- **Metadata**: Timestamp de criação (ISO 8601), versão do schema (2.3.0)

<details>
<summary>Exemplo de Synth gerado (clique para expandir)</summary>

```json
{
  "id": "abc123",
  "nome": "Maria Silva Santos",
  "arquetipo": "Jovem Adulto Sudeste Criativo",
  "descricao": "Mulher de 28 anos, designer gráfica, mora em São Paulo, SP. Possui traços marcantes de Abertura, Amabilidade.",
  "link_photo": "https://ui-avatars.com/api/?name=Maria+Silva+Santos&size=256&background=random",
  "created_at": "2025-12-14T15:30:00Z",
  "version": "2.3.0",
  "demografia": {
    "idade": 28,
    "genero_biologico": "feminino",
    "identidade_genero": "mulher cis",
    "raca_etnia": "parda",
    "localizacao": {
      "pais": "Brasil",
      "regiao": "Sudeste",
      "estado": "SP",
      "cidade": "São Paulo"
    },
    "escolaridade": "Superior completo",
    "renda_mensal": 4500.00,
    "ocupacao": "Designer gráfico",
    "estado_civil": "solteiro",
    "composicao_familiar": {
      "tipo": "unipessoal",
      "numero_pessoas": 1
    }
  },
  "psicografia": {
    "personalidade_big_five": {
      "abertura": 78,
      "conscienciosidade": 62,
      "extroversao": 55,
      "amabilidade": 71,
      "neuroticismo": 42
    },
    "valores": ["criatividade", "autonomia", "justiça social"],
    "interesses": ["design", "arte", "tecnologia", "música"],
    "hobbies": ["desenho", "fotografia", "videogames", "yoga"],
    "estilo_vida": "Criativo e explorador",
    "inclinacao_politica": -25,
    "inclinacao_religiosa": "católico"
  },
  "comportamento": {
    "habitos_consumo": {
      "frequencia_compras": "semanal",
      "preferencia_canal": "híbrido",
      "categorias_preferidas": ["tecnologia", "livros", "vestuário", "decoração"]
    },
    "uso_tecnologia": {
      "smartphone": true,
      "computador": true,
      "tablet": true,
      "smartwatch": false
    },
    "padroes_midia": {
      "tv_aberta": 2,
      "streaming": 15,
      "redes_sociais": 12
    },
    "fonte_noticias": ["jornais online", "redes sociais", "podcasts"],
    "comportamento_compra": {
      "impulsivo": 45,
      "pesquisa_antes_comprar": 75
    },
    "lealdade_marca": 55,
    "engajamento_redes_sociais": {
      "plataformas": ["Instagram", "LinkedIn", "Pinterest", "WhatsApp"],
      "frequencia_posts": "ocasional"
    }
  },
  "deficiencias": {
    "visual": {"tipo": "nenhuma"},
    "auditiva": {"tipo": "nenhuma"},
    "motora": {"tipo": "nenhuma", "usa_cadeira_rodas": false},
    "cognitiva": {"tipo": "nenhuma"}
  },
  "capacidades_tecnologicas": {
    "alfabetizacao_digital": 85,
    "dispositivos": {
      "principal": "computador",
      "qualidade": "novo"
    },
    "preferencias_acessibilidade": {
      "zoom_fonte": 100,
      "alto_contraste": false
    },
    "velocidade_digitacao": 70,
    "frequencia_internet": "diária",
    "familiaridade_plataformas": {
      "e_commerce": 90,
      "banco_digital": 85,
      "redes_sociais": 95
    }
  },
  "vieses": {
    "aversao_perda": 48,
    "desconto_hiperbolico": 55,
    "suscetibilidade_chamariz": 42,
    "ancoragem": 51,
    "vies_confirmacao": 60,
    "vies_status_quo": 38,
    "sobrecarga_informacao": 45
  }
}
```
</details>

## 📁 Estrutura do Projeto

```
synth-lab/
├── src/
│   └── synth_lab/                # Pacote principal
│       ├── __init__.py
│       ├── __main__.py           # Entry point CLI
│       ├── gen_synth/            # Módulo de geração
│       │   ├── __init__.py
│       │   ├── gen_synth.py      # Orquestrador principal
│       │   ├── config.py         # Configurações e paths
│       │   └── utils.py          # Funções utilitárias
│       ├── query/                # Módulo de consulta
│       │   ├── __init__.py       # Enums e exceções
│       │   ├── validator.py      # Validação de queries
│       │   ├── database.py       # Operações DuckDB
│       │   ├── formatter.py      # Formatação Rich tables
│       │   └── cli.py            # Comando listsynth
│       └── research/             # Módulo de pesquisa UX
│           ├── __init__.py       # Public API
│           ├── models.py         # Pydantic models
│           ├── prompts.py        # System prompts
│           ├── interview.py      # Interview logic
│           ├── transcript.py     # JSON persistence
│           └── cli.py            # Comando research
├── tests/
│   ├── unit/
│   │   └── synth_lab/
│   │       ├── gen_synth/        # Testes unitários de geração
│   │       ├── query/            # Testes unitários de query
│   │       └── research/         # Testes unitários de research
│   ├── integration/
│   │   └── synth_lab/
│   │       └── query/            # Testes de integração
│   ├── contract/
│   │   └── synth_lab/
│   │       └── research/         # Testes de contrato (LLM schemas)
│   └── fixtures/
│       └── query/                # Fixtures para testes
├── data/
│   ├── synths/                   # Synths gerados (JSON)
│   ├── transcripts/              # Transcrições de entrevistas (JSON)
│   ├── topic_guides/             # Guias de tópicos para entrevistas
│   ├── config/                   # Configurações demográficas
│   │   ├── ibge_distributions.json
│   │   ├── interests_hobbies.json
│   │   └── occupations_structured.json
│   └── schemas/                  # JSON Schema para validação
│       └── synth-schema.json
├── pyproject.toml                # Configuração do projeto
├── pytest.ini                    # Configuração pytest
└── README.md                     # Este arquivo
```

## 🎓 Documentação

### Documentação Principal

- **[Requisitos](docs/requisitos.md)**: Requisitos funcionais e não-funcionais do projeto
- **[Arquitetura](docs/arquitetura.md)**: Arquitetura em 3 camadas (Interface → Service → Database)
- **[Modelo de Dados](docs/database_model.md)**: Esquema completo do banco de dados PostgreSQL
- **[API REST](docs/api.md)**: Documentação completa dos 17 endpoints REST
- **[CLI](docs/cli.md)**: Guia completo da interface de linha de comando
- **[Camada de Serviços](docs/services.md)**: Documentação da lógica de negócio

### Especificações Técnicas

- **[spec.md](specs/001-generate-synths/spec.md)**: Requisitos completos, escopo e critérios de aceitação
- **[data-model.md](specs/001-generate-synths/data-model.md)**: Modelo de dados detalhado com todos os atributos
- **[research.md](specs/001-generate-synths/research.md)**: Fontes de dados, metodologia e referências
- **[quickstart.md](specs/001-generate-synths/quickstart.md)**: Guia rápido para começar
- **[plan.md](specs/001-generate-synths/plan.md)**: Plano de implementação e arquitetura
- **[tasks.md](specs/001-generate-synths/tasks.md)**: Tarefas e progresso do desenvolvimento

## 📊 Fontes de Dados

Todas as distribuições estatísticas são baseadas em fontes oficiais e pesquisas verificadas:

| Fonte | Dados | Ano |
|-------|-------|-----|
| **IBGE Censo** | População por região, religião, raça/etnia | 2022 |
| **IBGE PNAD** | Demografia, renda, escolaridade, ocupação | 2022/2023 |
| **IBGE PNS** | Deficiências físicas e cognitivas | 2019 |
| **TIC Domicílios (CETIC.br)** | Alfabetização digital, uso de tecnologia | 2023 |
| **DataSenado** | Inclinação política da população | 2024 |
| **Pesquisa TIM + USP** | Hobbies e interesses dos brasileiros | Recente |

## 🧪 Validação e Qualidade

- **JSON Schema**: Validação automática de todos os campos (Draft 2020-12)
- **Distribuições Realistas**: Conformidade com dados do IBGE (<10% erro)
- **Consistência Interna**: Validação de relações entre atributos (ex: ocupação vs. escolaridade)
- **Cobertura de Casos**: Inclusão de edge cases e perfis diversos
- **ID Únicos**: Garantia de IDs únicos com sistema de retry
- **Validação Automática**: 10 testes internos de coerência

### Métricas de Performance

```
✅ Geração individual: ~0.001s por synth
✅ Geração em lote: ~1800 synths/segundo
✅ Batch de 100: ~0.06s (bem abaixo do limite de 2 minutos)
✅ Distribuição regional: <7% erro vs IBGE
✅ Distribuição etária: <4% erro vs IBGE
✅ Validação schema: 100% dos synths gerados passam
✅ Cobertura de testes: 846+ testes automatizados
✅ E2E tests: 105+ testes Playwright
```

## 🛠️ Stack Tecnológica

- **Python 3.13+**: Linguagem base
- **Faker (pt_BR)**: Geração de dados sintéticos brasileiros
- **OpenAI Python SDK**: Structured outputs para entrevistas com LLMs
- **Pydantic v2**: Validação estrita de dados e schemas
- **jsonschema**: Validação de estrutura de dados
- **rich**: Interface CLI com saída colorida e formatada
- **PostgreSQL**: Banco de dados relacional para persistência
- **SQLAlchemy 2.0+**: ORM para acesso ao banco de dados
- **Typer**: Framework CLI moderno com type hints
- **Loguru**: Sistema de logging estruturado
- **pytest**: Framework de testes unitários e integração
- **uv**: Gerenciamento rápido de dependências

## 💡 Exemplos de Uso

### Análise Exploratória
Veja o notebook `first-lab.ipynb` para exemplos de análise exploratória dos Synths gerados.

### Casos de Uso

**1. Pesquisa UX Qualitativa com Topic Guides via REST API**
```bash
# Criar topic guide manualmente
mkdir -p data/topic_guides/mobile-banking
cp screens/*.png data/topic_guides/mobile-banking/
cp user-flows/*.pdf data/topic_guides/mobile-banking/

# Iniciar API server
uv run python -m synth_lab.api.main

# Verificar topic guide criado
curl http://localhost:8000/topics/mobile-banking

# Listar execuções de pesquisa disponíveis
curl http://localhost:8000/research/list

# Obter detalhes de uma execução específica
curl http://localhost:8000/research/{execution_id}

# Obter resumo agregado (se disponível)
curl http://localhost:8000/research/{execution_id}/summary

# Análise de transcrições (Python)
import json
from pathlib import Path

transcripts = [json.loads(p.read_text()) for p in Path("data/transcripts/mobile-banking_batch_20251216_143052").glob("*.json")]
# Análise qualitativa: temas recorrentes, pain points, insights
```

**2. 🖼️ NOVO: Geração de Avatares Realistas para Personas**
```bash
# Gerar synths com avatares (9 por bloco)
uv run synthlab gensynth -n 9 --avatar

# Gerar múltiplos blocos de avatares (45 avatares = 5 blocos)
uv run synthlab gensynth -n 45 --avatar

# Gerar avatares para synths existentes que ainda não possuem
uv run synthlab gensynth --avatar

# Gerar avatares para synths específicos
uv run synthlab gensynth --avatar --synth-ids abc123,xyz789,def456

# Combinar com análise de distribuição
uv run synthlab gensynth -n 18 --avatar --analyze all --benchmark
```

**Características dos Avatares**:
- 🎨 Imagens realistas de 341x341px em PNG
- 👥 Diversidade demográfica precisa (idade, gênero, etnia)
- 💼 Backgrounds relacionados à profissão
- 🎭 Múltiplos estilos visuais (B&W, sepia, warm, cool, 3D)
- 📁 Salvos em: `data/synths/avatar/{synth-id}.png`
- 💰 ~$0.02 por bloco de 9 avatares usando OpenAI API

**3. Análise Demográfica com PostgreSQL**
```bash
# Conectar ao banco
psql postgresql://synthlab:synthlab@localhost:5432/synthlab

# Distribuição por região (exemplo - schema pode variar)
SELECT regiao, COUNT(*) as total FROM synths GROUP BY regiao ORDER BY total DESC;

# Média de renda por escolaridade
SELECT escolaridade, AVG(renda_mensal) as media_renda FROM synths GROUP BY escolaridade;

# Perfis de alto poder aquisitivo
SELECT * FROM synths WHERE renda_mensal > 10000 AND escolaridade = 'Superior completo';
```

> **Nota**: Use `psql` ou ferramentas como pgAdmin, DBeaver para consultas SQL avançadas, ou use a REST API para acesso via HTTP.

**4. Testes de UX/UI**
```bash
# Conectar ao banco PostgreSQL
psql postgresql://synthlab:synthlab@localhost:5432/synthlab

# Selecionar Synths com baixa alfabetização digital (exemplo - schema pode variar)
SELECT * FROM synths WHERE alfabetizacao_digital < 40;

# Usuários com deficiências visuais
SELECT nome, idade, cidade FROM synths WHERE deficiencia_visual != 'nenhuma';
```

**5. Segmentação de Mercado**
```bash
# Conectar ao banco PostgreSQL
psql postgresql://synthlab:synthlab@localhost:5432/synthlab

# Jovens da região Sudeste (exemplo - schema pode variar)
SELECT * FROM synths WHERE idade BETWEEN 18 AND 35 AND regiao = 'Sudeste';

# Perfil tecnológico e renda média-alta
SELECT * FROM synths WHERE alfabetizacao_digital > 70 AND renda_mensal > 5000;
```

**6. Análise Comportamental**
```python
# Usar Python para análise mais complexa
import json
synths = json.load(open('data/synths/synths.json'))
high_openness = [s for s in synths if s['psicografia']['personalidade_big_five']['abertura'] > 70]
```

## 📝 Licença

MIT License - veja o arquivo LICENSE para detalhes.
