# Arquitetura do synth-lab

## Visão Geral

O **synth-lab** implementa uma arquitetura em **3 camadas** (Interface → Service → Database) que promove separação de responsabilidades, reutilização de código e facilidade de manutenção.

```
┌─────────────────────────────────────────────────────────┐
│                   INTERFACE LAYER                        │
│  ┌──────────────┐              ┌──────────────┐         │
│  │     CLI      │              │   REST API   │         │
│  │   (Typer)    │              │  (FastAPI)   │         │
│  └──────┬───────┘              └──────┬───────┘         │
│         │                             │                 │
│         └─────────────┬───────────────┘                 │
└───────────────────────┼─────────────────────────────────┘
                        │
┌───────────────────────┼─────────────────────────────────┐
│                   SERVICE LAYER                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │  • SynthService (generate, list, get)           │    │
│  │  • TopicService (create, update, list)          │    │
│  │  • ResearchService (execute, stream, status)    │    │
│  │  • ReportService (summary, prfaq - async)       │    │
│  └──────────────────────┬──────────────────────────┘    │
└─────────────────────────┼───────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────┐
│                   DATABASE LAYER                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │  • DatabaseManager (context manager)            │    │
│  │  • Repositories (synths, topics, executions)    │    │
│  │  • Models (Pydantic)                            │    │
│  └──────────────────────┬──────────────────────────┘    │
└─────────────────────────┼───────────────────────────────┘
                          │
                   ┌──────┴──────┐
                   │   SQLite    │
                   │ synthlab.db │
                   └─────────────┘
```

## Camadas da Arquitetura

### 1. Interface Layer (Camada de Interface)

Responsável por interagir com o usuário, seja através de linha de comando (CLI) ou requisições HTTP (API REST).

#### 1.1 CLI (Command Line Interface)

**Tecnologia**: Typer + Rich

**Localização**: `src/synth_lab/` (comandos integrados)

**Responsabilidades**:
- Capturar comandos do usuário
- Validar argumentos de entrada
- Chamar serviços da camada de negócio
- Formatar saída com cores e tabelas (Rich)
- Mostrar progress bars para operações longas

**Comandos Principais**:
```bash
# Geração
synthlab gensynth -n 10 --avatar

# Consulta
synthlab listsynth --where "demografia.idade > 30"

# Topic Guides
synthlab topic-guide create --name amazon-ecommerce
synthlab topic-guide update --name amazon-ecommerce

# Research
synthlab research interview <synth_id> <topic_name>
synthlab research batch <topic_name> --limit 10
```

#### 1.2 API REST (FastAPI)

**Tecnologia**: FastAPI + Pydantic + Uvicorn

**Localização**: `src/synth_lab/api/`

**Responsabilidades**:
- Expor endpoints HTTP RESTful
- Validar requests com Pydantic models
- Serializar responses em JSON
- Tratar exceções e retornar erros padronizados
- Servir documentação interativa (Swagger UI em `/docs`)
- Streaming via Server-Sent Events (SSE)

**Estrutura de Diretórios**:
```
src/synth_lab/api/
├── main.py              # FastAPI app principal
├── dependencies.py      # Dependency injection (DB, services)
├── errors.py            # Exception handlers
├── models/              # Request/response models
│   ├── synth.py
│   ├── topic.py
│   ├── research.py
│   └── prfaq.py
└── routers/             # Endpoints agrupados
    ├── synths.py        # 5 endpoints
    ├── topics.py        # 3 endpoints
    ├── research.py      # 6 endpoints
    └── prfaq.py         # 3 endpoints
```

**Endpoints**:
- **17 endpoints REST** divididos em 4 routers
- Paginação padrão: limit (1-200), offset (>=0)
- Sorting: sort_by + sort_order (asc/desc)
- Filtros: WHERE clause SQL ou campos específicos

### 2. Service Layer (Camada de Negócio)

Contém toda a lógica de negócio do sistema. É **compartilhada** entre CLI e API, garantindo comportamento consistente.

**Localização**: `src/synth_lab/services/`

**Princípios**:
- **Single Responsibility**: Cada service cuida de um domínio específico
- **Dependency Injection**: Services recebem repositories via construtor
- **Stateless**: Services não mantêm estado entre chamadas
- **Testável**: Facilmente testável com mock de repositories

#### 2.1 SynthService

**Arquivo**: `src/synth_lab/services/synth_service.py`

**Responsabilidades**:
- Gerar novos synths (com LLM)
- Listar synths com paginação e filtros
- Buscar synth por ID
- Busca avançada com SQL WHERE clause
- Gerar e registrar avatares

**Métodos Principais**:
```python
class SynthService:
    def generate_synth(arquetipo: str | None) -> dict
    def list_synths(params: PaginationParams, fields: list[str]) -> PaginatedResponse[SynthSummary]
    def get_synth(synth_id: str) -> SynthDetail
    def search_synths(where_clause: str, query: str, params: PaginationParams) -> PaginatedResponse[SynthSummary]
    def get_avatar(synth_id: str) -> Path
    def get_fields() -> list[SynthFieldInfo]
```

**Integrações**:
- `gen_synth.generator` - Geração de perfil com LLM
- `gen_synth.avatar_generator` - Geração de avatar com DALL-E
- `SynthRepository` - Persistência no banco

#### 2.2 TopicService

**Arquivo**: `src/synth_lab/services/topic_service.py`

**Responsabilidades**:
- Criar topic guides
- Atualizar descrições de arquivos (Vision API)
- Listar topic guides
- Obter detalhes de um topic
- Listar research executions de um topic

**Métodos Principais**:
```python
class TopicService:
    def create_topic(name: str, display_name: str, description: str) -> TopicDetail
    def update_topic(name: str, force: bool) -> TopicDetail
    def list_topics(params: PaginationParams) -> PaginatedResponse[TopicSummary]
    def get_topic(topic_name: str) -> TopicDetail
    def get_topic_executions(topic_name: str, params: PaginationParams) -> PaginatedResponse[ResearchExecutionSummary]
```

**Integrações**:
- `topic_guides.manager` - Processamento de arquivos
- `infrastructure.llm_client` - Geração de descrições
- `TopicRepository` - Persistência e cache

#### 2.3 ResearchService

**Arquivo**: `src/synth_lab/services/research_service.py`

**Responsabilidades**:
- Executar research com streaming de progresso
- Gerenciar paralelização de entrevistas
- Controlar concorrência (semaphore)
- Salvar transcrições
- Disparar jobs assíncronos (summary, PR-FAQ)

**Métodos Principais**:
```python
class ResearchService:
    async def execute_research_stream(
        topic_name: str,
        synth_ids: list[str] | None,
        synth_count: int | None,
        max_turns: int,
        max_concurrent: int,
        model: str | None = None,
        generate_summary: bool
    ) -> AsyncGenerator[dict, None]

    def get_execution_status(exec_id: str) -> dict
    def list_executions(params: PaginationParams) -> PaginatedResponse[ResearchExecutionSummary]
    def get_transcripts(exec_id: str, params: PaginationParams) -> PaginatedResponse[TranscriptSummary]
    def get_transcript(exec_id: str, synth_id: str) -> TranscriptDetail
    def get_summary(exec_id: str) -> str
```

**Eventos SSE Emitidos**:
- `started` - Início da execução
- `interview_started` - Início de entrevista individual
- `turn` - Cada turno de conversa
- `interview_completed` - Fim de entrevista bem-sucedida
- `interview_failed` - Falha em entrevista
- `all_completed` - Fim de toda a execução
- `job_queued` - Job assíncrono enfileirado

**Integrações**:
- `research_agentic.batch_interview` - Engine de entrevistas
- `ResearchRepository` - Persistência
- `ReportService` - Geração de relatórios

#### 2.4 ReportService

**Arquivo**: `src/synth_lab/services/report_service.py`

**Responsabilidades**:
- Enfileirar jobs assíncronos (summary, PR-FAQ)
- Processar jobs em background (worker)
- Gerar resumos executivos
- Gerar documentos PR-FAQ
- Atualizar metadata de reports

**Métodos Principais**:
```python
class ReportService:
    async def queue_summary_generation(exec_id: str) -> str  # retorna job_id
    async def queue_prfaq_generation(exec_id: str, depends_on: str | None) -> str
    def get_job_status(job_id: str) -> dict

    # Privados
    async def _job_worker()
    async def _generate_summary(exec_id: str)
    async def _generate_prfaq(exec_id: str)
```

**Integrações**:
- `research_agentic.summary` - Geração de summary
- `research_prfaq.generator` - Geração de PR-FAQ
- `JobRepository` - Persistência de jobs

### 3. Database Layer (Camada de Dados)

Responsável por toda a interação com o banco de dados SQLite.

**Localização**: `src/synth_lab/infrastructure/` e `src/synth_lab/repositories/`

#### 3.1 DatabaseManager

**Arquivo**: `src/synth_lab/infrastructure/database.py`

**Responsabilidades**:
- Gerenciar conexões SQLite
- Fornecer context managers para queries
- Gerenciar transações com rollback automático
- Configurar WAL mode e foreign keys

**Características**:
- **Thread-safe**: Usa `threading.local()` para conexões por thread
- **WAL mode**: Permite leituras concorrentes
- **Foreign keys**: Habilitadas para integridade referencial
- **Transações**: Rollback automático em caso de erro

**Métodos Principais**:
```python
class DatabaseManager:
    def connection() -> ContextManager[sqlite3.Connection]
    def transaction() -> ContextManager[sqlite3.Connection]
    def execute(sql: str, params: tuple) -> sqlite3.Cursor
    def fetchone(sql: str, params: tuple) -> sqlite3.Row | None
    def fetchall(sql: str, params: tuple) -> list[sqlite3.Row]
    def executemany(sql: str, params_list: list[tuple])
```

#### 3.2 Repositories

Cada repository encapsula acesso a dados de um domínio específico.

**BaseRepository** (`src/synth_lab/repositories/base.py`):
- Métodos comuns de paginação
- Conversão de rows para dicts
- Validação de campos de ordenação

**SynthRepository** (`src/synth_lab/repositories/synth_repository.py`):
```python
class SynthRepository:
    def create(synth_data: dict) -> str
    def get_by_id(synth_id: str) -> dict | None
    def list(params: PaginationParams, fields: list[str]) -> tuple[list[dict], PaginationMeta]
    def search(where_clause: str, query: str, params: PaginationParams) -> tuple[list[dict], PaginationMeta]
    def register_avatar(synth_id: str, file_path: str, model: str)
    def get_avatar_path(synth_id: str) -> Path | None
    def get_fields() -> list[SynthFieldInfo]
```

**TopicRepository** (`src/synth_lab/repositories/topic_repository.py`):
```python
class TopicRepository:
    def create(topic_data: dict) -> str
    def get_by_name(topic_name: str) -> dict | None
    def list(params: PaginationParams) -> tuple[list[dict], PaginationMeta]
    def update_cache(topic_name: str, metadata: dict)
    def add_file(topic_name: str, file_data: dict)
    def get_files(topic_name: str) -> list[dict]
```

**ResearchRepository** (`src/synth_lab/repositories/research_repository.py`):
```python
class ResearchRepository:
    def create_execution(exec_data: dict) -> str
    def get_execution(exec_id: str) -> dict | None
    def list_executions(params: PaginationParams) -> tuple[list[dict], PaginationMeta]
    def update_execution(exec_id: str, **fields)
    def complete_execution(exec_id: str)

    def save_transcript(exec_id: str, synth_id: str, transcript_data: dict)
    def get_transcripts(exec_id: str, params: PaginationParams) -> tuple[list[dict], PaginationMeta]
    def get_transcript(exec_id: str, synth_id: str) -> dict | None

    def register_report(exec_id: str, report_data: dict)
    def save_prfaq_metadata(exec_id: str, metadata: dict)
```

**PRFAQRepository** (`src/synth_lab/repositories/prfaq_repository.py`):
```python
class PRFAQRepository:
    def list(params: PaginationParams) -> tuple[list[dict], PaginationMeta]
    def get_by_exec_id(exec_id: str) -> dict | None
    def get_markdown(exec_id: str) -> str
```

**JobRepository** (`src/synth_lab/repositories/job_repository.py`):
```python
class JobRepository:
    def create_job(job_data: dict) -> str
    def get_job(job_id: str) -> dict | None
    def get_next_pending_job() -> dict | None
    def update_job_status(job_id: str, status: str, error_message: str | None)
```

#### 3.3 Models (Pydantic)

**Localização**: `src/synth_lab/models/`

**Responsabilidades**:
- Validação automática de dados
- Serialização/deserialização JSON
- Type safety em tempo de compilação
- Documentação automática de schemas

**Hierarquia de Models**:

```
models/
├── synth.py
│   ├── SynthBase (campos obrigatórios)
│   ├── SynthSummary (para listagens)
│   ├── SynthDetail (com dados aninhados)
│   ├── Demographics, Psychographics, TechCapabilities, etc.
│   └── SynthSearchRequest, SynthFieldInfo
│
├── topic.py
│   ├── TopicSummary
│   ├── TopicDetail
│   ├── TopicQuestion
│   └── TopicFile
│
├── research.py
│   ├── ResearchExecutionBase
│   ├── ResearchExecutionSummary
│   ├── ResearchExecutionDetail
│   ├── TranscriptSummary
│   ├── TranscriptDetail
│   ├── Message
│   ├── ExecutionStatus (enum)
│   └── ResearchExecuteRequest, ResearchExecuteResponse
│
├── prfaq.py
│   ├── PRFAQSummary
│   ├── PRFAQGenerateRequest
│   └── PRFAQGenerateResponse
│
└── pagination.py
    ├── PaginationParams
    ├── PaginationMeta
    └── PaginatedResponse[T]
```

## Fluxo de Dados

### Exemplo 1: Listar Synths via API

```
1. Request HTTP
   GET /synths/list?limit=10&offset=0

2. Router Handler (api/routers/synths.py)
   └─> Cria PaginationParams(limit=10, offset=0)
   └─> Chama SynthService.list_synths(params)

3. Service Layer (services/synth_service.py)
   └─> SynthService.list_synths()
       └─> Chama SynthRepository.list(params)

4. Repository Layer (repositories/synth_repository.py)
   └─> SynthRepository.list()
       └─> Chama BaseRepository._paginate_query()
       └─> DatabaseManager.fetchone() [COUNT query]
       └─> DatabaseManager.fetchall() [SELECT com LIMIT/OFFSET]
       └─> Converte rows para SynthSummary

5. Database Layer (infrastructure/database.py)
   └─> SQLite Connection (thread-local)
   └─> Executa queries no banco synthlab.db
   └─> Retorna sqlite3.Row objects

6. Response
   └─> Repository retorna (list[dict], PaginationMeta)
   └─> Service retorna PaginatedResponse[SynthSummary]
   └─> Router valida com Pydantic
   └─> FastAPI serializa para JSON
   └─> HTTP 200 OK com body JSON
```

### Exemplo 2: Executar Research via CLI

```
1. Comando CLI
   $ synthlab research batch compra-amazon --limit 10

2. CLI Handler
   └─> Parseia argumentos (topic_name="compra-amazon", limit=10)
   └─> Chama ResearchService.execute_research_stream()

3. Service Layer (services/research_service.py)
   └─> ResearchService.execute_research_stream()
       ├─> Cria execution record no DB
       ├─> Seleciona synths aleatórios (via repository)
       ├─> Para cada synth:
       │   ├─> Executa interview (async, com semaphore)
       │   ├─> Salva transcript no DB
       │   └─> Yield eventos de progresso
       ├─> Atualiza status da execution
       └─> Enfileira jobs assíncronos (summary, PR-FAQ)

4. Research Engine (research_agentic/batch_interview.py)
   └─> Carrega synth do DB
   └─> Carrega topic guide do DB
   └─> Executa conversa LLM (interviewer + synth)
   └─> Retorna transcript completo

5. Repository Layer
   └─> ResearchRepository.save_transcript()
       └─> INSERT na tabela research_transcripts

6. Job Service (services/report_service.py)
   └─> Enfileira job de summary
   └─> Worker em background processa job
   └─> Gera summary.md usando LLM
   └─> Salva arquivo e atualiza DB
```

## Padrões de Design

### 1. Dependency Injection

**Problema**: Acoplamento forte entre camadas

**Solução**: Services recebem repositories via construtor

```python
# API dependencies (api/dependencies.py)
@lru_cache
def get_db() -> DatabaseManager:
    return get_database()

@lru_cache
def get_synth_service() -> SynthService:
    return SynthService(SynthRepository())

# Router handler
@router.get("/synths/list")
async def list_synths(
    service: SynthService = Depends(get_synth_service)
):
    return service.list_synths(...)
```

**Benefícios**:
- Testável (mock de dependencies)
- Reutilizável (mesma service em CLI e API)
- Flexível (fácil trocar implementações)

### 2. Repository Pattern

**Problema**: Lógica de negócio misturada com acesso a dados

**Solução**: Repositories encapsulam toda a lógica SQL

```python
# Service não sabe como dados são armazenados
class SynthService:
    def __init__(self, repo: SynthRepository):
        self.repo = repo

    def get_synth(self, synth_id: str):
        return self.repo.get_by_id(synth_id)

# Repository cuida de SQL
class SynthRepository:
    def get_by_id(self, synth_id: str):
        sql = "SELECT * FROM synths WHERE id = ?"
        return self.db.fetchone(sql, (synth_id,))
```

**Benefícios**:
- Separação de responsabilidades
- Fácil trocar banco de dados
- Queries SQL centralizadas

### 3. Pydantic Models para Validação

**Problema**: Validação manual propensa a erros

**Solução**: Pydantic valida automaticamente

```python
class PaginationParams(BaseModel):
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
    sort_by: str | None = None
    sort_order: Literal["asc", "desc"] = "asc"

# FastAPI valida automaticamente
@router.get("/synths/list")
async def list_synths(params: PaginationParams = Depends()):
    # params já validado!
    pass
```

**Benefícios**:
- Validação automática
- Erros claros e detalhados
- Documentação automática (OpenAPI)
- Type hints integrados

### 4. Context Managers para Recursos

**Problema**: Conexões não fechadas, transações não rollback

**Solução**: Context managers garantem cleanup

```python
class DatabaseManager:
    @contextmanager
    def connection(self):
        conn = self._get_connection()
        try:
            yield conn
        finally:
            # Cleanup sempre executado
            pass

    @contextmanager
    def transaction(self):
        with self.connection() as conn:
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise

# Uso
with db.transaction() as conn:
    conn.execute("INSERT INTO ...")
    # Commit automático ou rollback em erro
```

**Benefícios**:
- Segurança (rollback garantido)
- Legibilidade (with statement)
- Menos bugs (não esquece de fechar)

### 5. Async Generators para Streaming

**Problema**: API bloqueante durante research longa

**Solução**: Async generator com SSE

```python
class ResearchService:
    async def execute_research_stream(self, ...) -> AsyncGenerator[dict, None]:
        # Yield eventos conforme ocorrem
        yield {"event": "started", "exec_id": exec_id}

        async for turn in run_interview_async(...):
            yield {"event": "turn", "text": turn.text}

        yield {"event": "completed"}

# FastAPI converte para SSE
@router.post("/research/execute")
async def execute_research(request: ResearchExecuteRequest):
    async def event_generator():
        async for event in service.execute_research_stream(...):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

**Benefícios**:
- UX melhor (progresso em tempo real)
- Escalável (não bloqueia servidor)
- Interruptível (cliente pode cancelar)

## Decisões Arquiteturais

### 1. Por que SQLite?

**Alternativas Consideradas**: PostgreSQL, MongoDB, DuckDB

**Decisão**: SQLite com JSON1

**Razões**:
- ✅ Zero dependências (built-in Python 3.13)
- ✅ Deploy simples (single file)
- ✅ JSON1 suporta queries em campos aninhados
- ✅ WAL mode permite leituras concorrentes
- ✅ Suficiente para até 10k synths
- ❌ Não escala para milhões de records (futuro: migrar para PostgreSQL)

### 2. Por que FastAPI?

**Alternativas Consideradas**: Flask, Django REST Framework

**Decisão**: FastAPI

**Razões**:
- ✅ Async nativo (melhor para I/O bound)
- ✅ Pydantic integrado (validação automática)
- ✅ OpenAPI docs automático
- ✅ Performance superior
- ✅ Type hints modernos
- ✅ SSE suportado nativamente

### 3. Por que Service Layer?

**Alternativas Consideradas**: Lógica direto no router, lógica direto no repository

**Decisão**: Service layer separada

**Razões**:
- ✅ CLI e API compartilham lógica
- ✅ Testável (mock de repositories)
- ✅ Reutilizável (composição de serviços)
- ✅ Single Responsibility (cada service um domínio)
- ❌ Mais boilerplate (tradeoff aceitável)

### 4. Por que Streaming SSE?

**Alternativas Consideradas**: Polling, WebSockets, GraphQL subscriptions

**Decisão**: Server-Sent Events (SSE)

**Razões**:
- ✅ Simples (HTTP unidirecional)
- ✅ Auto-reconnect do navegador
- ✅ Suportado por `EventSource` nativo
- ✅ Menos overhead que WebSockets
- ✅ Ideal para updates unidirecionais (server → client)
- ❌ Não bidirecional (mas não precisamos)

### 5. Por que Jobs Assíncronos?

**Alternativas Consideradas**: Síncrono (bloqueante), Celery, RQ

**Decisão**: Worker em background (asyncio)

**Razões**:
- ✅ Simples (sem dependências extras)
- ✅ Suficiente para volume atual
- ✅ Integrado com FastAPI (mesmo processo)
- ❌ Não persistente (jobs perdidos se processo cair)
- **Futuro**: Migrar para Celery quando escalar

## Segurança

### Validação de Entrada
- Pydantic valida todos os requests
- SQL injection prevenido por:
  - Parametrized queries (`?` placeholders)
  - Whitelist de keywords em WHERE clauses
  - Validação de campos de ordenação

### Autenticação/Autorização
- **Atual**: Nenhuma (API pública)
- **Futuro**: OAuth2 + JWT para produção

### Secrets Management
- OpenAI API Key em variável de ambiente (`OPENAI_API_KEY`)
- Nunca logados ou commitados
- `.env` em `.gitignore`

### CORS
- Configurado em `api/main.py`
- **Dev**: `allow_origins=["*"]`
- **Prod**: Restringir a domínios específicos

## Performance

### Database Otimizações
- **Índices** em colunas frequentemente consultadas
- **WAL mode** para leituras concorrentes
- **Foreign keys** para integridade (overhead aceitável)
- **JSON1** para queries em campos aninhados

### API Otimizações
- **Paginação** padrão (limit 50, max 200)
- **Lazy loading** de campos pesados (apenas quando solicitado)
- **Caching** de metadata (topic guides cache)
- **Connection pooling** (thread-local connections)

### Async Otimizações
- **Paralelização** de entrevistas (semaphore)
- **Streaming** de eventos (não bloqueia)
- **Background jobs** para tarefas longas

## Observabilidade

### Logging
- **Loguru** com níveis configuráveis
- Logs estruturados por componente
- Contexto de erro detalhado

### Métricas (Futuro)
- Tempo de resposta de endpoints
- Contadores de requests por endpoint
- Taxa de erro por operação
- Uso de tokens OpenAI

### Tracing (Futuro)
- OpenTelemetry para distributed tracing
- Rastreamento de research executions

## Escalabilidade

### Limites Atuais
- SQLite: ~10k synths, ~1k executions
- FastAPI: ~100 req/s
- Research concurrent: 10 interviews paralelas

### Plano de Escala
1. **Horizontal**: Load balancer + múltiplas instâncias FastAPI
2. **Database**: Migrar para PostgreSQL (compatível com repositories)
3. **Jobs**: Migrar para Celery + Redis
4. **Storage**: Separar avatares em S3 ou similar

## Manutenibilidade

### Convenções de Código
- Máximo 500 linhas por arquivo
- Google-style docstrings
- Type hints completos
- Ruff linting (PEP 8)

### Testes
- Unit tests para services (mock repositories)
- Integration tests para API (test database)
- Contract tests para LLM responses

### Documentação
- README atualizado
- Docs técnicos em `docs/`
- OpenAPI auto-gerado em `/docs`
- Inline comments para lógica complexa

## Evolução da Arquitetura

### Versão 1.0 (Atual)
- CLI com JSON files
- DuckDB para queries

### Versão 2.0 (API + Database)
- SQLite database
- Service layer compartilhada
- FastAPI REST API
- Streaming SSE

### Versão 3.0 (Futuro)
- PostgreSQL para escala
- Autenticação OAuth2
- Celery para jobs
- Dashboard web
- Métricas e tracing
- Deploy em cloud (AWS/GCP)

## Conclusão

A arquitetura em 3 camadas do synth-lab promove:
- **Separação de responsabilidades**: Cada camada tem um papel claro
- **Reutilização**: Service layer compartilhada entre CLI e API
- **Testabilidade**: Dependency injection facilita mocks
- **Escalabilidade**: Preparado para crescimento futuro
- **Manutenibilidade**: Código organizado e bem documentado

A escolha de tecnologias (FastAPI, SQLite, Pydantic) equilibra simplicidade, performance e capacidade de evolução.
