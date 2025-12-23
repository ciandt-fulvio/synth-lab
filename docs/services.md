# Camada de Serviços - synth-lab

## Visão Geral

A **Service Layer** (Camada de Serviços) contém toda a lógica de negócio do synth-lab. É compartilhada entre CLI e API REST, garantindo comportamento consistente em todas as interfaces.

### Princípios de Design

- **Single Responsibility**: Cada service cuida de um domínio específico
- **Dependency Injection**: Services recebem dependencies via construtor
- **Stateless**: Não mantêm estado entre chamadas
- **Testável**: Facilmente testável com mock de repositories
- **Reutilizável**: Usado por CLI e API sem duplicação

### Localização

```
src/synth_lab/services/
├── __init__.py
├── errors.py              # Exceções de domínio
├── synth_service.py       # Lógica de synths
├── topic_service.py       # Lógica de topic guides
├── research_service.py    # Lógica de research executions
└── report_service.py      # Lógica de relatórios assíncronos
```

---

## Hierarquia de Exceções

### Arquivo: `services/errors.py`

```python
class SynthLabError(Exception):
    """Exceção base para erros de domínio."""
    def __init__(self, message: str, code: str, details: dict | None = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)

class NotFoundError(SynthLabError):
    """Recurso não encontrado."""
    pass

class SynthNotFoundError(NotFoundError):
    """Synth não encontrado."""
    def __init__(self, synth_id: str):
        super().__init__(
            message=f"Synth com ID '{synth_id}' não encontrado",
            code="SYNTH_NOT_FOUND",
            details={"synth_id": synth_id}
        )

class TopicNotFoundError(NotFoundError):
    """Topic guide não encontrado."""
    def __init__(self, topic_name: str):
        super().__init__(
            message=f"Topic guide '{topic_name}' não encontrado",
            code="TOPIC_NOT_FOUND",
            details={"topic_name": topic_name}
        )

class ExecutionNotFoundError(NotFoundError):
    """Research execution não encontrada."""
    pass

class TranscriptNotFoundError(NotFoundError):
    """Transcrição não encontrada."""
    pass

class PRFAQNotFoundError(NotFoundError):
    """PR-FAQ não encontrado."""
    pass

class ValidationError(SynthLabError):
    """Erro de validação."""
    pass

class InvalidQueryError(ValidationError):
    """Query SQL inválida."""
    def __init__(self, query: str, reason: str):
        super().__init__(
            message=f"Query SQL inválida: {reason}",
            code="INVALID_QUERY",
            details={"query": query, "reason": reason}
        )

class InvalidRequestError(ValidationError):
    """Request inválido."""
    pass

class GenerationFailedError(SynthLabError):
    """Falha na geração (LLM)."""
    def __init__(self, resource: str, reason: str):
        super().__init__(
            message=f"Falha ao gerar {resource}: {reason}",
            code="GENERATION_FAILED",
            details={"resource": resource, "reason": reason}
        )

class DatabaseError(SynthLabError):
    """Erro de banco de dados."""
    def __init__(self, operation: str, reason: str):
        super().__init__(
            message=f"Erro de banco de dados em '{operation}': {reason}",
            code="DATABASE_ERROR",
            details={"operation": operation, "reason": reason}
        )
```

---

## 1. SynthService

### Arquivo: `services/synth_service.py`

Gerencia toda a lógica de negócio relacionada a synths.

### Dependências

```python
from synth_lab.repositories.synth_repository import SynthRepository
from synth_lab.models.synth import (
    SynthSummary, SynthDetail, SynthSearchRequest, SynthFieldInfo
)
from synth_lab.models.pagination import PaginationParams, PaginatedResponse
from synth_lab.services.errors import SynthNotFoundError, InvalidQueryError
from synth_lab.gen_synth.generator import generate_synth_profile
from synth_lab.gen_synth.avatar_generator import generate_avatar
```

### Classe

```python
class SynthService:
    """Service para lógica de negócio de synths."""

    def __init__(self, synth_repo: SynthRepository):
        """
        Inicializa service com repository injetado.

        Args:
            synth_repo: Repository de synths
        """
        self.synth_repo = synth_repo
        self.logger = logger.bind(component="synth_service")
```

### Métodos Públicos

#### 1.1 generate_synth()

Gera um novo synth e salva no banco de dados.

```python
def generate_synth(
    self,
    arquetipo: str | None = None,
    generate_avatar: bool = True
) -> SynthDetail:
    """
    Gera novo synth e opcionalmente seu avatar.

    Args:
        arquetipo: Arquétipo específico (opcional)
        generate_avatar: Se deve gerar avatar (padrão: True)

    Returns:
        SynthDetail: Synth completo gerado

    Raises:
        GenerationFailedError: Se geração falhar
        DatabaseError: Se falhar ao salvar no DB

    Example:
        >>> service = SynthService(SynthRepository())
        >>> synth = service.generate_synth(arquetipo="Jovem Adulto Sudeste")
        >>> print(synth.id)
        'ynnasw'
    """
    self.logger.info("Gerando novo synth", arquetipo=arquetipo)

    try:
        # Gerar perfil com LLM
        synth_data = generate_synth_profile(arquetipo=arquetipo)

        # Salvar no DB
        synth_id = self.synth_repo.create(synth_data)
        self.logger.info("Synth criado no DB", synth_id=synth_id)

        # Gerar avatar se solicitado
        if generate_avatar:
            avatar_path = generate_avatar(
                synth_id=synth_id,
                synth_profile=synth_data,
                output_dir=Path("output/synths/avatar")
            )

            # Registrar avatar no DB
            self.synth_repo.register_avatar(
                synth_id=synth_id,
                file_path=str(avatar_path),
                model="dall-e-3"
            )
            self.logger.info("Avatar gerado", synth_id=synth_id, path=avatar_path)

        # Retornar synth completo
        return self.get_synth(synth_id)

    except Exception as e:
        self.logger.exception("Falha ao gerar synth", error=str(e))
        raise GenerationFailedError("synth", str(e))
```

#### 1.2 list_synths()

Lista synths com paginação e filtros.

```python
def list_synths(
    self,
    params: PaginationParams,
    fields: list[str] | None = None
) -> PaginatedResponse[SynthSummary]:
    """
    Lista synths com paginação.

    Args:
        params: Parâmetros de paginação
        fields: Campos a incluir (opcional)

    Returns:
        PaginatedResponse[SynthSummary]: Synths paginados

    Example:
        >>> params = PaginationParams(limit=10, offset=0, sort_by="created_at")
        >>> response = service.list_synths(params)
        >>> print(len(response.data))
        10
        >>> print(response.pagination.total)
        150
    """
    self.logger.info("Listando synths", params=params)

    try:
        rows, meta = self.synth_repo.list(params, fields)

        synths = [self._row_to_summary(row) for row in rows]

        return PaginatedResponse(data=synths, pagination=meta)

    except Exception as e:
        self.logger.exception("Falha ao listar synths", error=str(e))
        raise DatabaseError("list_synths", str(e))
```

#### 1.3 get_synth()

Obtém synth por ID.

```python
def get_synth(self, synth_id: str) -> SynthDetail:
    """
    Obtém synth por ID.

    Args:
        synth_id: ID do synth

    Returns:
        SynthDetail: Synth completo

    Raises:
        SynthNotFoundError: Se synth não existir

    Example:
        >>> synth = service.get_synth("ynnasw")
        >>> print(synth.nome)
        'Ravy Lopes'
    """
    self.logger.info("Buscando synth", synth_id=synth_id)

    row = self.synth_repo.get_by_id(synth_id)

    if not row:
        raise SynthNotFoundError(synth_id)

    return self._row_to_detail(row)
```

#### 1.4 search_synths()

Busca avançada com SQL WHERE clause.

```python
def search_synths(
    self,
    where_clause: str | None = None,
    query: str | None = None,
    params: PaginationParams | None = None
) -> PaginatedResponse[SynthSummary]:
    """
    Busca avançada com SQL.

    Args:
        where_clause: Cláusula WHERE (ex: "demografia.idade > 30")
        query: Query SQL completa (alternativa a where_clause)
        params: Parâmetros de paginação

    Returns:
        PaginatedResponse[SynthSummary]: Resultados paginados

    Raises:
        InvalidQueryError: Se query contiver comandos não permitidos

    Example:
        >>> response = service.search_synths(
        ...     where_clause="json_extract(demografia, '$.idade') > 30",
        ...     params=PaginationParams(limit=20)
        ... )
        >>> print(len(response.data))
        20
    """
    self.logger.info("Buscando synths", where_clause=where_clause, query=query)

    # Validar segurança da query
    self._validate_sql_safety(query or where_clause)

    try:
        rows, meta = self.synth_repo.search(
            where_clause=where_clause,
            query=query,
            params=params or PaginationParams()
        )

        synths = [self._row_to_summary(row) for row in rows]

        return PaginatedResponse(data=synths, pagination=meta)

    except Exception as e:
        self.logger.exception("Falha ao buscar synths", error=str(e))
        raise DatabaseError("search_synths", str(e))
```

#### 1.5 get_avatar()

Obtém path do avatar de um synth.

```python
def get_avatar(self, synth_id: str) -> Path:
    """
    Obtém path do avatar de um synth.

    Args:
        synth_id: ID do synth

    Returns:
        Path: Path para arquivo PNG

    Raises:
        SynthNotFoundError: Se synth não existir
        AvatarNotFoundError: Se avatar não existir

    Example:
        >>> path = service.get_avatar("ynnasw")
        >>> print(path)
        Path('output/synths/avatar/ynnasw.png')
    """
    self.logger.info("Buscando avatar", synth_id=synth_id)

    # Verificar se synth existe
    if not self.synth_repo.get_by_id(synth_id):
        raise SynthNotFoundError(synth_id)

    # Buscar avatar
    avatar_path = self.synth_repo.get_avatar_path(synth_id)

    if not avatar_path or not avatar_path.exists():
        raise AvatarNotFoundError(synth_id)

    return avatar_path
```

#### 1.6 get_fields()

Lista campos disponíveis para filtros.

```python
def get_fields(self) -> list[SynthFieldInfo]:
    """
    Lista campos disponíveis para filtros.

    Returns:
        list[SynthFieldInfo]: Lista de campos

    Example:
        >>> fields = service.get_fields()
        >>> print(fields[0].name)
        'id'
        >>> print(fields[0].type)
        'string'
    """
    return self.synth_repo.get_fields()
```

### Métodos Privados

```python
def _validate_sql_safety(self, sql: str | None):
    """Valida segurança da query SQL."""
    if not sql:
        return

    BLOCKED_KEYWORDS = [
        "INSERT", "UPDATE", "DELETE", "DROP", "CREATE",
        "ALTER", "TRUNCATE", "REPLACE", "EXEC", "EXECUTE"
    ]

    sql_upper = sql.upper()
    for keyword in BLOCKED_KEYWORDS:
        if keyword in sql_upper:
            raise InvalidQueryError(sql, f"Comando '{keyword}' não permitido")

def _row_to_summary(self, row: dict) -> SynthSummary:
    """Converte row do DB para SynthSummary."""
    return SynthSummary(
        id=row["id"],
        nome=row["nome"],
        arquetipo=row.get("arquetipo"),
        descricao=row.get("descricao"),
        created_at=row["created_at"],
        avatar_url=f"/synths/{row['id']}/avatar" if row.get("avatar_path") else None
    )

def _row_to_detail(self, row: dict) -> SynthDetail:
    """Converte row do DB para SynthDetail."""
    return SynthDetail(
        id=row["id"],
        nome=row["nome"],
        arquetipo=row.get("arquetipo"),
        descricao=row.get("descricao"),
        link_photo=row.get("link_photo"),
        avatar_path=row.get("avatar_path"),
        created_at=row["created_at"],
        version=row.get("version"),
        demografia=json.loads(row["demografia"]) if row.get("demografia") else None,
        psicografia=json.loads(row["psicografia"]) if row.get("psicografia") else None,
        deficiencias=json.loads(row["deficiencias"]) if row.get("deficiencias") else None,
        capacidades_tecnologicas=json.loads(row["capacidades_tecnologicas"]) if row.get("capacidades_tecnologicas") else None
    )
```

---

## 2. TopicService

### Arquivo: `services/topic_service.py`

Gerencia lógica de negócio de topic guides.

### Classe

```python
class TopicService:
    """Service para lógica de negócio de topic guides."""

    def __init__(
        self,
        topic_repo: TopicRepository,
        llm_client: LLMClient
    ):
        self.topic_repo = topic_repo
        self.llm_client = llm_client
        self.logger = logger.bind(component="topic_service")
```

### Métodos Principais

#### 2.1 create_topic()

```python
def create_topic(
    self,
    name: str,
    display_name: str | None = None,
    description: str | None = None
) -> TopicDetail:
    """
    Cria novo topic guide.

    Args:
        name: Nome do topic (slug)
        display_name: Nome formatado (opcional)
        description: Descrição (opcional)

    Returns:
        TopicDetail: Topic criado

    Raises:
        InvalidRequestError: Se topic já existir
    """
```

#### 2.2 update_topic()

```python
async def update_topic(
    self,
    topic_name: str,
    force: bool = False
) -> TopicDetail:
    """
    Atualiza descrições de arquivos do topic guide.

    Args:
        topic_name: Nome do topic
        force: Re-processar todos os arquivos (ignora cache)

    Returns:
        TopicDetail: Topic atualizado

    Process:
        1. Escaneia diretório do topic
        2. Para cada arquivo novo/modificado:
           - Imagens: gera descrição com Vision API
           - PDFs: extrai texto
           - Markdown/Text: carrega conteúdo
        3. Atualiza summary.md com descrições
        4. Salva cache (hashes) no DB
    """
```

#### 2.3 list_topics()

```python
def list_topics(
    self,
    params: PaginationParams
) -> PaginatedResponse[TopicSummary]:
    """Lista topic guides com paginação."""
```

#### 2.4 get_topic()

```python
def get_topic(self, topic_name: str) -> TopicDetail:
    """
    Obtém topic guide por nome.

    Raises:
        TopicNotFoundError: Se topic não existir
    """
```

---

## 3. ResearchService

### Arquivo: `services/research_service.py`

Gerencia lógica de research executions.

### Classe

```python
class ResearchService:
    """Service para lógica de negócio de research executions."""

    def __init__(
        self,
        research_repo: ResearchRepository,
        synth_repo: SynthRepository,
        topic_repo: TopicRepository,
        report_service: ReportService
    ):
        self.research_repo = research_repo
        self.synth_repo = synth_repo
        self.topic_repo = topic_repo
        self.report_service = report_service
        self.logger = logger.bind(component="research_service")
```

### Métodos Principais

#### 3.1 execute_research_stream()

```python
async def execute_research_stream(
    self,
    topic_name: str,
    synth_ids: list[str] | None,
    synth_count: int | None,
    max_turns: int,
    max_concurrent: int,
    model: str | None = None,
    generate_summary: bool = True
) -> AsyncGenerator[dict, None]:
    """
    Executa research com streaming de progresso.

    Args:
        topic_name: Nome do topic guide
        synth_ids: IDs específicos (opcional)
        synth_count: Quantidade aleatória (alternativa)
        max_turns: Máx. de turnos por entrevista
        max_concurrent: Entrevistas paralelas simultâneas
        model: Modelo LLM
        generate_summary: Gerar summary ao final

    Yields:
        dict: Eventos SSE de progresso

    Events:
        - {"event": "started", "exec_id": "...", "synth_count": 10}
        - {"event": "interview_started", "synth_id": "ynnasw", "synth_name": "..."}
        - {"event": "turn", "synth_id": "ynnasw", "turn": 1, "speaker": "...", "text": "..."}
        - {"event": "interview_completed", "synth_id": "ynnasw"}
        - {"event": "interview_failed", "synth_id": "abc123", "error": "..."}
        - {"event": "all_completed", "successful": 9, "failed": 1}
        - {"event": "job_queued", "job_type": "summary", "job_id": "uuid"}

    Example:
        >>> async for event in service.execute_research_stream(...):
        ...     print(event)
        {'event': 'started', 'exec_id': 'batch_...', 'synth_count': 10}
        {'event': 'turn', 'synth_id': 'ynnasw', 'speaker': 'Interviewer', ...}
        ...
    """
    # Criar execution record
    exec_id = f"batch_{topic_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Selecionar synths
    if synth_ids:
        selected_synths = synth_ids
    else:
        selected_synths = self.synth_repo.get_random_ids(synth_count)

    # Criar registro
    self.research_repo.create_execution(
        exec_id=exec_id,
        topic_name=topic_name,
        synth_count=len(selected_synths),
        model=model,
        max_turns=max_turns,
        status="running"
    )

    # Yield: started
    yield {
        "event": "started",
        "exec_id": exec_id,
        "topic_name": topic_name,
        "synth_count": len(selected_synths)
    }

    # Executar entrevistas em paralelo com semaphore
    semaphore = asyncio.Semaphore(max_concurrent)

    async def run_single_interview(synth_id: str):
        async with semaphore:
            # Yield: interview_started
            synth = self.synth_repo.get_by_id(synth_id)
            yield {
                "event": "interview_started",
                "synth_id": synth_id,
                "synth_name": synth["nome"]
            }

            try:
                # Executar interview (async generator)
                async for turn_event in run_interview_async(
                    synth_id=synth_id,
                    topic_name=topic_name,
                    max_turns=max_turns,
                    model=model
                ):
                    # Yield cada turn
                    yield {
                        "event": "turn",
                        "synth_id": synth_id,
                        "turn": turn_event["turn_number"],
                        "speaker": turn_event["speaker"],
                        "text": turn_event["text"]
                    }

                # Salvar transcript
                transcript_path = f"output/transcripts/{exec_id}/{synth_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                self.research_repo.save_transcript(
                    exec_id=exec_id,
                    synth_id=synth_id,
                    file_path=transcript_path,
                    turn_count=max_turns,
                    status="completed"
                )

                # Yield: completed
                yield {
                    "event": "interview_completed",
                    "synth_id": synth_id,
                    "status": "completed"
                }

            except Exception as e:
                # Yield: failed
                yield {
                    "event": "interview_failed",
                    "synth_id": synth_id,
                    "error": str(e)
                }

    # Merge de async generators
    async for event in merge_async_generators(
        [run_single_interview(sid) for sid in selected_synths]
    ):
        yield event

    # Atualizar status
    self.research_repo.complete_execution(exec_id)

    # Yield: all_completed
    stats = self.research_repo.get_execution_stats(exec_id)
    yield {
        "event": "all_completed",
        "exec_id": exec_id,
        "successful": stats["successful_count"],
        "failed": stats["failed_count"]
    }

    # Disparar jobs assíncronos
    if generate_summary:
        summary_job_id = await self.report_service.queue_summary_generation(exec_id)
        yield {
            "event": "job_queued",
            "job_type": "summary",
            "job_id": summary_job_id
        }

        prfaq_job_id = await self.report_service.queue_prfaq_generation(
            exec_id,
            depends_on=summary_job_id
        )
        yield {
            "event": "job_queued",
            "job_type": "prfaq",
            "job_id": prfaq_job_id
        }
```

#### 3.2 get_execution_status()

```python
def get_execution_status(self, exec_id: str) -> ResearchExecutionDetail:
    """
    Obtém status de uma execution.

    Raises:
        ExecutionNotFoundError: Se execution não existir
    """
```

#### 3.3 list_executions()

```python
def list_executions(
    self,
    params: PaginationParams,
    status: str | None = None,
    topic_name: str | None = None
) -> PaginatedResponse[ResearchExecutionSummary]:
    """Lista executions com filtros opcionais."""
```

#### 3.4 get_transcripts()

```python
def get_transcripts(
    self,
    exec_id: str,
    params: PaginationParams
) -> PaginatedResponse[TranscriptSummary]:
    """Lista transcrições de uma execution."""
```

#### 3.5 get_transcript()

```python
def get_transcript(
    self,
    exec_id: str,
    synth_id: str
) -> TranscriptDetail:
    """
    Obtém transcrição específica.

    Raises:
        TranscriptNotFoundError: Se transcrição não existir
    """
```

---

## 4. ReportService

### Arquivo: `services/report_service.py`

Gerencia geração assíncrona de relatórios.

### Classe

```python
class ReportService:
    """Service para geração assíncrona de relatórios."""

    def __init__(
        self,
        research_repo: ResearchRepository,
        job_repo: JobRepository,
        llm_client: LLMClient
    ):
        self.research_repo = research_repo
        self.job_repo = job_repo
        self.llm_client = llm_client
        self._job_worker_running = False
        self.logger = logger.bind(component="report_service")
```

### Métodos Públicos

#### 4.1 queue_summary_generation()

```python
async def queue_summary_generation(self, exec_id: str) -> str:
    """
    Enfileira job para gerar summary.

    Args:
        exec_id: ID da research execution

    Returns:
        str: Job ID (UUID)

    Example:
        >>> job_id = await service.queue_summary_generation("batch_...")
        >>> print(job_id)
        'f47ac10b-58cc-4372-a567-0e02b2c3d479'
    """
    job_id = str(uuid.uuid4())

    self.job_repo.create_job(
        job_id=job_id,
        job_type="generate_summary",
        exec_id=exec_id,
        status="pending"
    )

    # Garante que worker está rodando
    if not self._job_worker_running:
        asyncio.create_task(self._job_worker())

    return job_id
```

#### 4.2 queue_prfaq_generation()

```python
async def queue_prfaq_generation(
    self,
    exec_id: str,
    depends_on: str | None = None
) -> str:
    """
    Enfileira job para gerar PR-FAQ.

    Args:
        exec_id: ID da research execution
        depends_on: Job ID que deve completar antes (opcional)

    Returns:
        str: Job ID (UUID)
    """
```

#### 4.3 get_job_status()

```python
def get_job_status(self, job_id: str) -> dict:
    """
    Obtém status de um job.

    Raises:
        JobNotFoundError: Se job não existir
    """
```

### Métodos Privados

#### 4.4 _job_worker()

```python
async def _job_worker(self):
    """
    Worker assíncrono que processa jobs pendentes.

    Runs in background:
        - Poll DB a cada 2s para jobs pendentes
        - Processa job (summary ou prfaq)
        - Atualiza status (completed ou failed)
        - Continua loop até não haver mais jobs
    """
    self._job_worker_running = True

    while True:
        # Buscar próximo job pendente
        job = self.job_repo.get_next_pending_job()

        if not job:
            await asyncio.sleep(2)  # Poll a cada 2s
            continue

        # Marcar como running
        self.job_repo.update_job_status(job["job_id"], "running")

        try:
            if job["job_type"] == "generate_summary":
                await self._generate_summary(job["exec_id"])
            elif job["job_type"] == "generate_prfaq":
                await self._generate_prfaq(job["exec_id"])

            # Marcar como completed
            self.job_repo.update_job_status(job["job_id"], "completed")

        except Exception as e:
            # Marcar como failed
            self.job_repo.update_job_status(
                job["job_id"],
                "failed",
                error_message=str(e)
            )
```

#### 4.5 _generate_summary()

```python
async def _generate_summary(self, exec_id: str):
    """
    Gera summary de uma research execution.

    Process:
        1. Carrega todas as transcrições
        2. Chama LLM para gerar resumo
        3. Salva summary.md
        4. Atualiza DB
    """
    from synth_lab.research_agentic.summary import generate_summary

    summary_md = await generate_summary(exec_id)

    # Salvar arquivo
    file_path = f"output/reports/{exec_id}_summary.md"
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    Path(file_path).write_text(summary_md, encoding="utf-8")

    # Registrar no DB
    self.research_repo.register_report(
        exec_id=exec_id,
        report_type="summary",
        file_path_markdown=file_path
    )

    # Atualizar flag has_summary
    self.research_repo.update_execution(exec_id, summary_path=file_path)
```

#### 4.6 _generate_prfaq()

```python
async def _generate_prfaq(self, exec_id: str):
    """
    Gera PR-FAQ de uma research execution.

    Process:
        1. Carrega summary
        2. Chama LLM para gerar PR-FAQ
        3. Valida output
        4. Salva .json e .md
        5. Atualiza DB com metadata
    """
```

---

## Uso da Service Layer

### Em CLI

```python
# src/synth_lab/cli/synth_commands.py
from synth_lab.services.synth_service import SynthService
from synth_lab.repositories.synth_repository import SynthRepository

@app.command("generate")
def generate_synth(count: int = 1, avatar: bool = False):
    """Gera novos synths via CLI."""
    synth_service = SynthService(SynthRepository())

    for i in range(count):
        synth = synth_service.generate_synth(generate_avatar=avatar)
        typer.echo(f"✓ Synth gerado: {synth.id} - {synth.nome}")
```

### Em API REST

```python
# src/synth_lab/api/routers/synths.py
from fastapi import APIRouter, Depends
from synth_lab.services.synth_service import SynthService
from synth_lab.api.dependencies import get_synth_service

router = APIRouter()

@router.get("/synths/list")
async def list_synths(
    params: PaginationParams = Depends(),
    service: SynthService = Depends(get_synth_service)
):
    """Lista synths via API."""
    return service.list_synths(params)
```

### Dependency Injection

```python
# src/synth_lab/api/dependencies.py
from functools import lru_cache
from synth_lab.services.synth_service import SynthService
from synth_lab.repositories.synth_repository import SynthRepository
from synth_lab.infrastructure.database import get_database

@lru_cache
def get_synth_service() -> SynthService:
    """Retorna singleton de SynthService."""
    db = get_database()
    synth_repo = SynthRepository(db)
    return SynthService(synth_repo)
```

---

## Testes

### Unit Tests

```python
# tests/unit/services/test_synth_service.py
from unittest.mock import Mock
from synth_lab.services.synth_service import SynthService

def test_get_synth_success():
    # Mock repository
    mock_repo = Mock()
    mock_repo.get_by_id.return_value = {
        "id": "ynnasw",
        "nome": "Ravy Lopes",
        "created_at": "2025-12-19T10:00:00Z",
        ...
    }

    # Service com mock
    service = SynthService(mock_repo)

    # Executar
    synth = service.get_synth("ynnasw")

    # Assertions
    assert synth.id == "ynnasw"
    assert synth.nome == "Ravy Lopes"
    mock_repo.get_by_id.assert_called_once_with("ynnasw")

def test_get_synth_not_found():
    # Mock repository
    mock_repo = Mock()
    mock_repo.get_by_id.return_value = None

    # Service com mock
    service = SynthService(mock_repo)

    # Deve lançar exceção
    with pytest.raises(SynthNotFoundError):
        service.get_synth("invalid_id")
```

### Integration Tests

```python
# tests/integration/services/test_synth_service_integration.py
from synth_lab.services.synth_service import SynthService
from synth_lab.repositories.synth_repository import SynthRepository
from synth_lab.infrastructure.database import DatabaseManager

def test_generate_and_retrieve_synth():
    # Setup real database (test DB)
    db = DatabaseManager(db_path="test_synthlab.db")
    repo = SynthRepository(db)
    service = SynthService(repo)

    # Gerar synth
    synth = service.generate_synth(generate_avatar=False)

    # Recuperar
    retrieved = service.get_synth(synth.id)

    # Assertions
    assert retrieved.id == synth.id
    assert retrieved.nome == synth.nome

    # Cleanup
    db.execute("DELETE FROM synths WHERE id = ?", (synth.id,))
```

---

## Boas Práticas

### 1. Sempre Injetar Dependencies

```python
# Correto
class SynthService:
    def __init__(self, synth_repo: SynthRepository):
        self.synth_repo = synth_repo

# Evite
class SynthService:
    def __init__(self):
        self.synth_repo = SynthRepository()  # Acoplamento forte
```

### 2. Lançar Exceções de Domínio

```python
# Correto
if not synth:
    raise SynthNotFoundError(synth_id)

# Evite
if not synth:
    raise Exception(f"Synth {synth_id} not found")  # Genérico
```

### 3. Log com Contexto

```python
# Correto
self.logger.info("Synth gerado", synth_id=synth.id, arquetipo=arquetipo)

# Evite
print(f"Synth {synth.id} gerado")  # Não estruturado
```

### 4. Validar Entrada

```python
# Correto
def generate_synth(self, arquetipo: str | None = None):
    if arquetipo and len(arquetipo) > 100:
        raise InvalidRequestError("Arquétipo muito longo")
```

### 5. Não Misturar Responsabilidades

```python
# Correto - Service foca em lógica
class SynthService:
    def generate_synth(self):
        synth_data = generate_synth_profile()  # Chama gerador
        self.synth_repo.create(synth_data)     # Delega persistência

# Evite - Service fazendo SQL direto
class SynthService:
    def generate_synth(self):
        synth_data = ...
        self.db.execute("INSERT INTO synths ...")  # Responsabilidade do repo
```

---

## Conclusão

A Service Layer do synth-lab:

- **Centraliza lógica de negócio** em classes reutilizáveis
- **Compartilhada** entre CLI e API REST
- **Testável** via dependency injection
- **Escalável** para futuras features
- **Bem documentada** com type hints e docstrings

Para mais informações:
- [Arquitetura](arquitetura.md)
- [Repositórios](database_model.md)
- [API REST](api.md)
- [CLI](cli.md)
