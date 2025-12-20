# synth-lab: API + Service Layer + Database Architecture

## Overview
Implementar arquitetura de 3 camadas para synth-lab:
1. **Database Layer** (SQLite): Persistência de dados
2. **Service Layer**: Lógica de negócio compartilhada
3. **Interface Layer**: CLI + REST API (ambos usam Service Layer)

## Decisões de Arquitetura

### ✅ Decisões Confirmadas
- **Database**: SQLite com JSON1 (zero dependências, built-in Python 3.13)
- **API Framework**: FastAPI standalone (`http://localhost:8000`)
- **Service Layer**: Camada compartilhada entre CLI e API
- **Streaming**: Research execution com Server-Sent Events (SSE)
- **Async Jobs**: Summary e PR-FAQ gerados de forma assíncrona após research
- **No Migration**: Dados atuais em `output/` são apenas desenvolvimento (descartáveis)

### ⚠️ Mudanças Importantes vs Plano Anterior
1. ❌ **Sem migração de dados** - começar do zero com database
2. ✅ **Geração de synths grava no DB** - `gen_synth` integrado com database
3. ✅ **Service layer compartilhada** - CLI e API usam mesma lógica
4. ✅ **Research streaming** - POST /research/execute retorna stream (SSE)
5. ✅ **Summary/PR-FAQ async** - dispara job ao fim da última research

---

## Arquitetura de 3 Camadas

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
│  │  • TopicGuideService (create, update, list)     │    │
│  │  • ResearchService (execute, stream, status)    │    │
│  │  • ReportService (summary, prfaq - async)       │    │
│  └──────────────────────┬──────────────────────────┘    │
└─────────────────────────┼───────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────┐
│                   DATABASE LAYER                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │  • Connection (context manager)                 │    │
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

---

## Database Schema (SQLite)

### Tabela: `synths`
```sql
CREATE TABLE synths (
    id TEXT PRIMARY KEY,  -- 6 caracteres (ex: "ynnasw")
    nome TEXT NOT NULL,
    arquetipo TEXT,
    descricao TEXT,
    link_photo TEXT,
    created_at TEXT NOT NULL,  -- ISO 8601
    version TEXT,
    -- JSON columns
    demografia TEXT CHECK(json_valid(demografia)),
    psicografia TEXT CHECK(json_valid(psicografia)),
    deficiencias TEXT CHECK(json_valid(deficiencias)),
    capacidades_tecnologicas TEXT CHECK(json_valid(capacidades_tecnologicas))
);

CREATE INDEX idx_synths_arquetipo ON synths(arquetipo);
CREATE INDEX idx_synths_created_at ON synths(created_at);
```

### Tabela: `synth_avatars`
```sql
CREATE TABLE synth_avatars (
    synth_id TEXT PRIMARY KEY REFERENCES synths(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,  -- ex: "output/synths/avatar/ynnasw.png"
    generated_at TEXT NOT NULL,
    model TEXT,  -- ex: "dall-e-3"
    prompt_hash TEXT  -- MD5 do prompt usado
);

CREATE INDEX idx_avatars_generated_at ON synth_avatars(generated_at);
```

### Tabela: `topic_guides`
```sql
CREATE TABLE topic_guides (
    name TEXT PRIMARY KEY,  -- ex: "compra-amazon"
    display_name TEXT,
    description TEXT,
    script_path TEXT,  -- ex: "data/topic_guides/compra-amazon/script.json"
    question_count INTEGER,
    file_count INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

### Tabela: `topic_guide_files`
```sql
CREATE TABLE topic_guide_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_name TEXT REFERENCES topic_guides(name) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT,  -- PNG, JPEG, PDF, etc.
    content_hash TEXT,
    description TEXT,
    size_bytes INTEGER,
    created_at TEXT NOT NULL
);

CREATE INDEX idx_topic_files_topic ON topic_guide_files(topic_name);
```

### Tabela: `research_executions`
```sql
CREATE TABLE research_executions (
    exec_id TEXT PRIMARY KEY,  -- ex: "batch_compra-amazon_20251219_082053"
    topic_name TEXT REFERENCES topic_guides(name),
    synth_count INTEGER NOT NULL,
    successful_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    model TEXT,  -- ex: "gpt-5-mini"
    max_turns INTEGER,
    status TEXT NOT NULL,  -- 'running', 'completed', 'failed'
    executed_at TEXT NOT NULL,
    completed_at TEXT,
    has_summary BOOLEAN DEFAULT 0,
    has_prfaq BOOLEAN DEFAULT 0
);

CREATE INDEX idx_executions_topic ON research_executions(topic_name);
CREATE INDEX idx_executions_status ON research_executions(status);
CREATE INDEX idx_executions_date ON research_executions(executed_at);
```

### Tabela: `research_transcripts`
```sql
CREATE TABLE research_transcripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exec_id TEXT REFERENCES research_executions(exec_id) ON DELETE CASCADE,
    synth_id TEXT REFERENCES synths(id),
    file_path TEXT NOT NULL,  -- ex: "output/transcripts/batch_.../ynnasw_20251219.json"
    turn_count INTEGER,
    model TEXT,
    timestamp TEXT NOT NULL,
    status TEXT  -- 'completed', 'failed'
);

CREATE INDEX idx_transcripts_exec ON research_transcripts(exec_id);
CREATE INDEX idx_transcripts_synth ON research_transcripts(synth_id);
```

### Tabela: `research_traces`
```sql
CREATE TABLE research_traces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exec_id TEXT REFERENCES research_executions(exec_id) ON DELETE CASCADE,
    synth_id TEXT REFERENCES synths(id),
    trace_id TEXT,
    file_path TEXT NOT NULL,
    duration_ms INTEGER,
    start_time TEXT,
    end_time TEXT
);

CREATE INDEX idx_traces_exec ON research_traces(exec_id);
```

### Tabela: `research_reports`
```sql
CREATE TABLE research_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exec_id TEXT REFERENCES research_executions(exec_id) ON DELETE CASCADE,
    report_type TEXT NOT NULL,  -- 'summary' ou 'prfaq'
    file_path_markdown TEXT,
    file_path_json TEXT,
    file_path_pdf TEXT,
    generated_at TEXT NOT NULL,
    validation_status TEXT,
    confidence_score REAL,
    version INTEGER DEFAULT 1
);

CREATE INDEX idx_reports_exec ON research_reports(exec_id);
CREATE INDEX idx_reports_type ON research_reports(report_type);
```

### Tabela: `prfaq_metadata` (para endpoint /prfaq/list)
```sql
CREATE TABLE prfaq_metadata (
    exec_id TEXT PRIMARY KEY REFERENCES research_executions(exec_id) ON DELETE CASCADE,
    headline TEXT,
    one_liner TEXT,
    faq_count INTEGER,
    confidence_score REAL,
    validation_status TEXT,
    generated_at TEXT NOT NULL
);
```

### Tabela: `async_jobs` (para tracking de jobs assíncronos)
```sql
CREATE TABLE async_jobs (
    job_id TEXT PRIMARY KEY,  -- UUID
    job_type TEXT NOT NULL,  -- 'generate_summary', 'generate_prfaq'
    exec_id TEXT REFERENCES research_executions(exec_id),
    status TEXT NOT NULL,  -- 'pending', 'running', 'completed', 'failed'
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    error_message TEXT,
    result_data TEXT  -- JSON com resultado
);

CREATE INDEX idx_jobs_status ON async_jobs(status);
CREATE INDEX idx_jobs_type ON async_jobs(job_type);
CREATE INDEX idx_jobs_exec ON async_jobs(exec_id);
```

### Configurações iniciais
```sql
PRAGMA journal_mode=WAL;  -- Concurrent reads
PRAGMA foreign_keys=ON;   -- Enforce referential integrity
```

---

## Estrutura de Diretórios

```
src/synth_lab/
├── database/               # DATABASE LAYER
│   ├── __init__.py
│   ├── connection.py       # SQLite connection manager
│   ├── schema.sql          # Full schema definition
│   ├── repositories/       # Data access
│   │   ├── __init__.py
│   │   ├── synth_repository.py
│   │   ├── topic_repository.py
│   │   ├── research_repository.py
│   │   └── job_repository.py
│   └── models.py           # Pydantic models for DB records
│
├── services/               # SERVICE LAYER (NEW)
│   ├── __init__.py
│   ├── synth_service.py    # Business logic: generate, list, get
│   ├── topic_service.py    # Business logic: create, update, list
│   ├── research_service.py # Business logic: execute (streaming), status
│   └── report_service.py   # Business logic: summary, prfaq (async)
│
├── api/                    # REST API (INTERFACE LAYER)
│   ├── __init__.py
│   ├── main.py             # FastAPI app
│   ├── dependencies.py     # DI: database, services
│   ├── errors.py           # Exception handlers
│   ├── streaming.py        # SSE helpers
│   ├── models/             # Request/response models
│   │   ├── synth.py
│   │   ├── topic.py
│   │   ├── research.py
│   │   └── prfaq.py
│   └── routers/
│       ├── synths.py       # 5 endpoints
│       ├── topics.py       # 3 endpoints
│       ├── research.py     # 6 endpoints (inclui SSE)
│       └── prfaq.py        # 3 endpoints
│
├── cli/                    # CLI (INTERFACE LAYER - refactor atual)
│   ├── __init__.py
│   ├── main.py             # Typer app (entry point)
│   ├── synth_commands.py   # Commands: synthlab synth generate/list
│   ├── topic_commands.py   # Commands: synthlab topic create/update
│   └── research_commands.py # Commands: synthlab research execute
│
├── gen_synth/              # Geração de synths (usa service layer)
├── research_agentic/       # Research engine (usa service layer)
├── topic_guide/            # Topic guides (usa service layer)
└── ...
```

---

## Service Layer Design

### `SynthService` (src/synth_lab/services/synth_service.py)

```python
from pathlib import Path
from datetime import datetime
from src.synth_lab.database.repositories.synth_repository import SynthRepository
from src.synth_lab.gen_synth.generator import generate_synth_profile
from src.synth_lab.gen_synth.avatar_generator import generate_avatar

class SynthService:
    def __init__(self, synth_repo: SynthRepository):
        self.synth_repo = synth_repo

    def generate_synth(self, arquetipo: str | None = None) -> dict:
        """
        Gera um novo synth e salva no database.

        1. Gera perfil com LLM
        2. Insere no database (tabela synths)
        3. Gera avatar
        4. Registra avatar no database (tabela synth_avatars)
        5. Retorna synth completo
        """
        # Gera perfil
        synth_data = generate_synth_profile(arquetipo=arquetipo)

        # Salva no database
        synth_id = self.synth_repo.create(synth_data)

        # Gera avatar
        avatar_path = generate_avatar(
            synth_id=synth_id,
            synth_profile=synth_data,
            output_dir=Path("output/synths/avatar")
        )

        # Registra avatar
        self.synth_repo.register_avatar(
            synth_id=synth_id,
            file_path=str(avatar_path),
            model="dall-e-3"
        )

        return self.synth_repo.get_by_id(synth_id)

    def list_synths(self, limit: int = 50, offset: int = 0,
                    filters: dict | None = None) -> tuple[list[dict], int]:
        """Lista synths com paginação."""
        return self.synth_repo.list(limit=limit, offset=offset, filters=filters)

    def get_synth(self, synth_id: str) -> dict | None:
        """Retorna synth por ID."""
        return self.synth_repo.get_by_id(synth_id)

    def search_synths(self, where_clause: str) -> list[dict]:
        """Busca avançada com WHERE clause SQL."""
        return self.synth_repo.search(where_clause)
```

### `ResearchService` (src/synth_lab/services/research_service.py)

```python
from typing import AsyncGenerator
import asyncio
from datetime import datetime
from src.synth_lab.database.repositories.research_repository import ResearchRepository
from src.synth_lab.research_agentic.batch_interview import run_interview

class ResearchService:
    def __init__(self, research_repo: ResearchRepository, report_service):
        self.research_repo = research_repo
        self.report_service = report_service

    async def execute_research_stream(
        self,
        topic_name: str,
        synth_ids: list[str] | None,
        synth_count: int | None,
        max_turns: int,
        max_concurrent: int,
        model: str,
        generate_summary: bool = True
    ) -> AsyncGenerator[dict, None]:
        """
        Executa research com streaming de progresso.

        Yields eventos SSE:
        - {"event": "started", "exec_id": "...", "synth_count": 10}
        - {"event": "interview_started", "synth_id": "ynnasw", "synth_name": "..."}
        - {"event": "turn", "synth_id": "ynnasw", "turn": 1, "speaker": "Interviewer", "text": "..."}
        - {"event": "interview_completed", "synth_id": "ynnasw", "duration_ms": 45000}
        - {"event": "interview_failed", "synth_id": "abc123", "error": "..."}
        - {"event": "all_completed", "successful": 9, "failed": 1}
        - {"event": "job_queued", "job_type": "summary", "job_id": "uuid-..."}
        """
        # Criar execution record
        exec_id = f"batch_{topic_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Selecionar synths
        if synth_ids:
            selected_synths = synth_ids
        else:
            # Buscar synths aleatórios
            selected_synths = self.research_repo.get_random_synth_ids(synth_count)

        # Criar registro de execução
        self.research_repo.create_execution(
            exec_id=exec_id,
            topic_name=topic_name,
            synth_count=len(selected_synths),
            model=model,
            max_turns=max_turns,
            status="running"
        )

        # Evento: started
        yield {
            "event": "started",
            "exec_id": exec_id,
            "topic_name": topic_name,
            "synth_count": len(selected_synths)
        }

        # Executar interviews em paralelo com semaphore
        semaphore = asyncio.Semaphore(max_concurrent)
        tasks = []

        async def run_single_interview(synth_id: str):
            async with semaphore:
                # Yield: interview_started
                synth = self.research_repo.get_synth(synth_id)
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

                    # Salvar transcript no DB
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

        # Rodar todas as interviews e fazer merge dos streams
        async for event in merge_async_generators(
            [run_single_interview(sid) for sid in selected_synths]
        ):
            yield event

        # Atualizar status da execução
        self.research_repo.complete_execution(exec_id)

        # Yield: all_completed
        stats = self.research_repo.get_execution_stats(exec_id)
        yield {
            "event": "all_completed",
            "exec_id": exec_id,
            "successful": stats["successful_count"],
            "failed": stats["failed_count"]
        }

        # Disparar jobs assíncronos (summary + prfaq)
        if generate_summary:
            summary_job_id = await self.report_service.queue_summary_generation(exec_id)
            yield {
                "event": "job_queued",
                "job_type": "summary",
                "job_id": summary_job_id
            }

            # PR-FAQ será gerado após summary
            prfaq_job_id = await self.report_service.queue_prfaq_generation(
                exec_id,
                depends_on=summary_job_id
            )
            yield {
                "event": "job_queued",
                "job_type": "prfaq",
                "job_id": prfaq_job_id
            }

    def get_execution_status(self, exec_id: str) -> dict | None:
        """Retorna status de uma execução."""
        return self.research_repo.get_execution(exec_id)

    def list_executions(self, topic_name: str | None = None) -> list[dict]:
        """Lista execuções com filtro opcional por tópico."""
        return self.research_repo.list_executions(topic_name=topic_name)
```

### `ReportService` (src/synth_lab/services/report_service.py)

```python
import asyncio
import uuid
from datetime import datetime
from src.synth_lab.database.repositories.research_repository import ResearchRepository
from src.synth_lab.database.repositories.job_repository import JobRepository

class ReportService:
    def __init__(self, research_repo: ResearchRepository, job_repo: JobRepository):
        self.research_repo = research_repo
        self.job_repo = job_repo
        self._job_worker_running = False

    async def queue_summary_generation(self, exec_id: str) -> str:
        """
        Enfileira job para gerar summary.
        Retorna job_id.
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

    async def queue_prfaq_generation(self, exec_id: str, depends_on: str | None = None) -> str:
        """
        Enfileira job para gerar PR-FAQ.
        Se depends_on fornecido, aguarda conclusão daquele job.
        """
        job_id = str(uuid.uuid4())

        self.job_repo.create_job(
            job_id=job_id,
            job_type="generate_prfaq",
            exec_id=exec_id,
            status="pending",
            depends_on=depends_on
        )

        return job_id

    async def _job_worker(self):
        """
        Worker assíncrono que processa jobs pendentes.
        Roda em background.
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

    async def _generate_summary(self, exec_id: str):
        """Gera summary de uma research execution."""
        # Chamar módulo existente de geração de summary
        from src.synth_lab.research_agentic.summary import generate_summary

        summary_md = await generate_summary(exec_id)

        # Salvar arquivo
        file_path = f"output/reports/{exec_id}_summary.md"
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        Path(file_path).write_text(summary_md, encoding="utf-8")

        # Registrar no database
        self.research_repo.register_report(
            exec_id=exec_id,
            report_type="summary",
            file_path_markdown=file_path
        )

        # Atualizar flag has_summary
        self.research_repo.update_execution(exec_id, has_summary=True)

    async def _generate_prfaq(self, exec_id: str):
        """Gera PR-FAQ de uma research execution."""
        from src.synth_lab.prfaq.generator import generate_prfaq

        prfaq_data = await generate_prfaq(exec_id)

        # Salvar arquivos (JSON + Markdown)
        json_path = f"output/reports/{exec_id}_prfaq.json"
        md_path = f"output/reports/{exec_id}_prfaq.md"

        Path(json_path).write_text(
            json.dumps(prfaq_data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        Path(md_path).write_text(prfaq_data["markdown"], encoding="utf-8")

        # Registrar no database
        self.research_repo.register_report(
            exec_id=exec_id,
            report_type="prfaq",
            file_path_json=json_path,
            file_path_markdown=md_path,
            confidence_score=prfaq_data.get("confidence_score")
        )

        # Salvar metadata
        self.research_repo.save_prfaq_metadata(
            exec_id=exec_id,
            headline=prfaq_data["press_release"]["headline"],
            one_liner=prfaq_data["press_release"]["one_liner"],
            faq_count=len(prfaq_data["faq"]),
            confidence_score=prfaq_data.get("confidence_score")
        )

        # Atualizar flag has_prfaq
        self.research_repo.update_execution(exec_id, has_prfaq=True)

    def get_job_status(self, job_id: str) -> dict | None:
        """Retorna status de um job assíncrono."""
        return self.job_repo.get_job(job_id)
```

---

## API Endpoints - Especificação Detalhada

### 1. Research Streaming Endpoint (NOVO)

#### `POST /research/execute` (Server-Sent Events)

**Request Body:**
```json
{
  "topic_name": "compra-amazon",
  "synth_ids": ["ynnasw", "abc123"],  // Opcional
  "synth_count": 10,                  // Se synth_ids não fornecido
  "max_turns": 6,
  "max_concurrent": 5,
  "model": "gpt-5-mini",
  "generate_summary": true
}
```

**Response**: Stream de eventos SSE (Content-Type: `text/event-stream`)

**Eventos:**

1. **started**
```
event: started
data: {"exec_id": "batch_compra-amazon_20251219_110534", "topic_name": "compra-amazon", "synth_count": 10}
```

2. **interview_started**
```
event: interview_started
data: {"synth_id": "ynnasw", "synth_name": "Ravy Lopes"}
```

3. **turn** (cada linha de diálogo)
```
event: turn
data: {"synth_id": "ynnasw", "turn": 1, "speaker": "Interviewer", "text": "Como você se sente..."}

event: turn
data: {"synth_id": "ynnasw", "turn": 1, "speaker": "Interviewee", "text": "Eu acho que..."}
```

4. **interview_completed**
```
event: interview_completed
data: {"synth_id": "ynnasw", "status": "completed", "duration_ms": 45000}
```

5. **interview_failed**
```
event: interview_failed
data: {"synth_id": "abc123", "error": "LLM timeout"}
```

6. **all_completed**
```
event: all_completed
data: {"exec_id": "batch_...", "successful": 9, "failed": 1}
```

7. **job_queued** (summary e prfaq)
```
event: job_queued
data: {"job_type": "summary", "job_id": "uuid-1234"}

event: job_queued
data: {"job_type": "prfaq", "job_id": "uuid-5678"}
```

**Client Example (JavaScript):**
```javascript
const eventSource = new EventSource('/research/execute');

eventSource.addEventListener('turn', (e) => {
  const data = JSON.parse(e.data);
  console.log(`[${data.synth_id}] ${data.speaker}: ${data.text}`);
});

eventSource.addEventListener('all_completed', (e) => {
  const data = JSON.parse(e.data);
  console.log(`Completed! ${data.successful} successful, ${data.failed} failed`);
  eventSource.close();
});
```

**FastAPI Implementation:**
```python
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from src.synth_lab.services.research_service import ResearchService

router = APIRouter()

@router.post("/research/execute")
async def execute_research_stream(request: ResearchExecuteRequest):
    async def event_generator():
        async for event in research_service.execute_research_stream(
            topic_name=request.topic_name,
            synth_ids=request.synth_ids,
            synth_count=request.synth_count,
            max_turns=request.max_turns,
            max_concurrent=request.max_concurrent,
            model=request.model,
            generate_summary=request.generate_summary
        ):
            yield f"event: {event['event']}\n"
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

---

### 2. Job Status Endpoint (NOVO)

#### `GET /jobs/{job_id}`

**Response 200:**
```json
{
  "job_id": "uuid-1234",
  "job_type": "generate_summary",
  "exec_id": "batch_compra-amazon_20251219_110534",
  "status": "completed",
  "created_at": "2025-12-19T11:05:34+00:00",
  "started_at": "2025-12-19T11:05:36+00:00",
  "completed_at": "2025-12-19T11:07:12+00:00",
  "result_data": {
    "file_path": "output/reports/batch_compra-amazon_20251219_110534_summary.md"
  }
}
```

**Response 404:**
```json
{
  "error": {
    "code": "JOB_NOT_FOUND",
    "message": "Job 'uuid-1234' não encontrado"
  }
}
```

---

### 3. Outros Endpoints (Mantidos da Spec Original)

Todos os endpoints da especificação original em `specs/api-pre-work.md` permanecem:
- **Synths APIs**: 5 endpoints (list, get, search, avatar, research)
- **Topic Guides APIs**: 3 endpoints (list, get, research)
- **Research APIs**: 6 endpoints (get, transcripts, summary, synths, prfaq)
- **PR-FAQ APIs**: 3 endpoints (list, markdown, generate)

**Mudança**: POST /research/execute agora é SSE streaming (descrito acima)

---

## Integração: Geração de Synths com Database

### Modificação: `gen_synth` Module

**Antes** (arquivo JSON):
```python
def save_synth(synth_data: dict):
    # Salva em output/synths/synths.json
    synths = load_json("output/synths/synths.json")
    synths.append(synth_data)
    save_json("output/synths/synths.json", synths)
```

**Depois** (usa SynthService):
```python
from src.synth_lab.services.synth_service import SynthService
from src.synth_lab.database.repositories.synth_repository import SynthRepository

def generate_and_save_synth(arquetipo: str | None = None) -> dict:
    """
    Gera synth e salva no database (não mais em JSON).
    """
    synth_service = SynthService(SynthRepository())

    # Service cuida de tudo: gerar perfil, salvar DB, gerar avatar, registrar avatar
    synth = synth_service.generate_synth(arquetipo=arquetipo)

    return synth
```

### CLI Integration

**Command**: `synthlab synth generate`

```python
# src/synth_lab/cli/synth_commands.py
import typer
from src.synth_lab.services.synth_service import SynthService
from src.synth_lab.database.repositories.synth_repository import SynthRepository

app = typer.Typer()

@app.command("generate")
def generate_synth(
    arquetipo: str = typer.Option(None, help="Arquétipo específico"),
    count: int = typer.Option(1, help="Quantidade de synths a gerar")
):
    """Gera novos synths e salva no database."""
    synth_service = SynthService(SynthRepository())

    for i in range(count):
        synth = synth_service.generate_synth(arquetipo=arquetipo)
        typer.echo(f"✓ Synth gerado: {synth['id']} - {synth['nome']}")
```

---

## Implementation Roadmap

### Phase 1: Database Layer (Fundação)
**Files to Create:**
- `src/synth_lab/database/connection.py`
- `src/synth_lab/database/schema.sql`
- `src/synth_lab/database/repositories/synth_repository.py`
- `src/synth_lab/database/repositories/topic_repository.py`
- `src/synth_lab/database/repositories/research_repository.py`
- `src/synth_lab/database/repositories/job_repository.py`
- `src/synth_lab/database/models.py`

**Script:**
- `scripts/init_database.py` - Cria `output/synthlab.db` com schema

**Tasks:**
1. Implementar connection manager com context manager
2. Criar schema SQL completo (10 tabelas)
3. Implementar repositories (CRUD operations)
4. Testar conexão e queries básicas

---

### Phase 2: Service Layer (Lógica de Negócio)
**Files to Create:**
- `src/synth_lab/services/synth_service.py`
- `src/synth_lab/services/topic_service.py`
- `src/synth_lab/services/research_service.py`
- `src/synth_lab/services/report_service.py`

**Tasks:**
1. Implementar SynthService (generate, list, get, search)
2. Implementar TopicService (create, update, list)
3. Implementar ResearchService (execute_stream, get_status)
4. Implementar ReportService (queue_summary, queue_prfaq, job_worker)
5. Integrar com módulos existentes (gen_synth, research_agentic)

---

### Phase 3: Integrar Geração de Synths com Database
**Files to Modify:**
- `src/synth_lab/gen_synth/storage.py`
- `src/synth_lab/gen_synth/cli.py`
- `src/synth_lab/gen_synth/avatar_generator.py`

**Tasks:**
1. Modificar `storage.py` para usar SynthService
2. Remover salvamento em JSON (ou manter como fallback)
3. Atualizar CLI para gerar e salvar no DB
4. Registrar avatars na tabela `synth_avatars`

---

### Phase 4: API Layer (REST Endpoints)
**Files to Create:**
- `src/synth_lab/api/main.py`
- `src/synth_lab/api/dependencies.py`
- `src/synth_lab/api/errors.py`
- `src/synth_lab/api/streaming.py`
- `src/synth_lab/api/models/` (synth.py, topic.py, research.py, prfaq.py)
- `src/synth_lab/api/routers/` (synths.py, topics.py, research.py, prfaq.py)

**Tasks:**
1. Setup FastAPI app com CORS
2. Implementar dependency injection (DB, services)
3. Implementar exception handlers (match spec error codes)
4. Implementar SSE streaming para /research/execute
5. Implementar todos os 17 endpoints (+1 para jobs)
6. Testar com Postman/curl

**Prioridade dos Endpoints:**
1. GET /synths/list, GET /synths/{id} (teste básico)
2. POST /research/execute (SSE streaming -核心功能)
3. GET /jobs/{job_id} (monitorar async jobs)
4. Demais endpoints de leitura
5. Endpoints de escrita restantes

---

### Phase 5: CLI Refactor (Usar Service Layer)
**Files to Modify:**
- `src/synth_lab/cli/main.py` (novo entry point)
- Mover comandos atuais para `cli/synth_commands.py`, etc.

**Tasks:**
1. Criar estrutura modular para CLI (synth_commands, topic_commands, research_commands)
2. Modificar comandos existentes para usar service layer
3. Remover acessos diretos a arquivos JSON
4. Testar comandos: `synthlab synth generate`, `synthlab research execute`

---

### Phase 6: Testing & Documentation
**Files to Create:**
- `tests/unit/services/` - Testes unitários dos services
- `tests/integration/api/` - Testes de integração da API
- `docs/API.md` - Documentação da API

**Tasks:**
1. Testes unitários para cada service
2. Testes de integração para endpoints
3. Testar SSE streaming (client JavaScript)
4. Documentar fluxos: geração de synth, research streaming, async jobs
5. Exemplos de uso da API

---

### Phase 7: Deployment & Tooling
**Files to Create:**
- `scripts/start_api.sh` - Launcher da API
- `scripts/reset_database.sh` - Resetar database (dev)
- `docker-compose.yml` (opcional) - Container para API

**Tasks:**
1. Script para iniciar API: `./scripts/start_api.sh`
2. Configurar uvicorn com reload (dev) e sem reload (prod)
3. Adicionar health check endpoint: GET /health
4. Documentar deploy local

---

## Dependencies to Add

```toml
[project]
dependencies = [
    # Existing
    "duckdb>=0.9.0",      # Manter para backward compatibility (opcional)
    "rich>=13.0.0",
    "typer>=0.9.0",

    # NEW: API
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.5.0",

    # NEW: SSE streaming
    "sse-starlette>=1.8.0",  # Helper para SSE no FastAPI
]

# SQLite: built-in (zero deps)
```

**Install:**
```bash
uv pip install -e .
# ou
uv pip install fastapi uvicorn[standard] pydantic sse-starlette
```

---

## Key Differences from Original Plan

| Aspecto | Plano Original | Plano Revisado ✅ |
|---------|----------------|-------------------|
| **Migração de dados** | Migrar `output/` para DB | ❌ Sem migração - dados atuais descartáveis |
| **Geração de synths** | Continua salvando em JSON | ✅ Salva direto no DB + registra avatar |
| **Arquitetura** | DB + API (2 camadas) | ✅ DB + Service + (API/CLI) (3 camadas) |
| **Research execute** | Síncrono (blocking) | ✅ SSE streaming (non-blocking UI) |
| **Summary/PR-FAQ** | Síncrono | ✅ Async jobs com worker em background |
| **CLI** | Separado da API | ✅ CLI e API usam mesmo service layer |
| **Paralelização** | Sequential | ✅ Parallel interviews com semaphore |

---

## Success Criteria

✅ **Database**
- SQLite database criado com todas as tabelas
- Indexes configurados para queries eficientes
- Foreign keys e constraints funcionando

✅ **Service Layer**
- Geração de synths salva no DB + registra avatar
- Research streaming funciona com SSE
- Async jobs processam summary/prfaq em background
- CLI e API usam mesmos services (zero duplicação)

✅ **API**
- 18 endpoints implementados (17 originais + 1 para jobs)
- POST /research/execute retorna stream SSE
- Client JavaScript consegue consumir eventos em tempo real
- Error handling match spec (códigos de erro corretos)

✅ **CLI**
- `synthlab synth generate` salva no DB
- `synthlab research execute` usa service layer
- Comandos existentes continuam funcionando

✅ **Testing**
- Testes unitários para services
- Testes de integração para API
- SSE streaming testado com client

✅ **Documentation**
- README atualizado com arquitetura de 3 camadas
- API documentation (OpenAPI auto-gerado)
- Exemplos de uso (curl, JavaScript client)

---

## Risk Mitigation

| Risco | Mitigação |
|-------|-----------|
| SSE streaming complexo | Usar `sse-starlette` lib (batalha-testada) |
| Async jobs travarem | Worker com timeout, retry logic, dead letter queue |
| Concurrent writes no SQLite | WAL mode + serialize writes via service layer |
| Breaking changes no CLI | Manter backward compat, deprecated warnings |
| Performance de streaming | Buffering estratégico, backpressure handling |

---

## Next Steps (Immediate)

1. ✅ **Aprovar este plano** - User review
2. 🔨 **Phase 1**: Implementar database layer (foundation)
3. 🔨 **Phase 2**: Implementar service layer
4. 🔨 **Phase 3**: Integrar geração de synths
5. 🔨 **Test**: Gerar synth via CLI e verificar no DB
6. 🔨 **Phase 4**: Implementar API + SSE streaming
7. 🔨 **Test**: Client JavaScript consumindo research stream
8. 🔨 **Phase 5-7**: CLI refactor, testing, deployment

---

**Autor**: Claude Code (synth-lab planning)
**Data**: 2025-12-19
**Versão**: 2.0 (com streaming + async jobs)
