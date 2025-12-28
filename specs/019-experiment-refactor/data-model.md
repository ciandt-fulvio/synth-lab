# Data Model: 019-experiment-refactor

**Date**: 2025-12-27
**Status**: Nova estrutura do zero (sem migração)

## Visão Geral do Modelo

```
┌─────────────────────────────────────────────────────────────┐
│                        EXPERIMENT                            │
│  (Hub central com scorecard embutido)                        │
│  - id, name, hypothesis, description                         │
│  - scorecard_data (JSON)                                     │
│  - created_at, updated_at                                    │
└─────────────────────────────────────────────────────────────┘
              │                              │
              │ 1:1                          │ 1:N
              ▼                              ▼
┌──────────────────────────┐    ┌──────────────────────────────┐
│      ANALYSIS_RUNS       │    │    RESEARCH_EXECUTIONS       │
│  (Análise Quantitativa)  │    │       (Entrevistas)          │
│  - id, experiment_id     │    │  - exec_id, experiment_id    │
│  - config (JSON)         │    │  - topic_name, status        │
│  - status, results       │    │  - synth_count, model        │
└──────────────────────────┘    └──────────────────────────────┘
              │                              │
              │ 1:N                          │ 1:N
              ▼                              ▼
┌──────────────────────────┐    ┌──────────────────────────────┐
│     SYNTH_OUTCOMES       │    │        TRANSCRIPTS           │
│  (Resultados por synth)  │    │  (Transcrições por synth)    │
│  - id, analysis_id       │    │  - id, exec_id, synth_id     │
│  - synth_id, rates       │    │  - messages (JSON)           │
└──────────────────────────┘    └──────────────────────────────┘
```

## Entidades de Domínio

### 1. Experiment (Hub Central)

```python
# domain/entities/experiment.py

class ScorecardDimension(BaseModel):
    """Dimensão do scorecard com score e metadados."""
    score: float = Field(ge=0.0, le=1.0)
    rules_applied: list[str] = []
    lower_bound: float | None = None
    upper_bound: float | None = None

class ScorecardData(BaseModel):
    """Dados do scorecard embutidos no experimento."""
    feature_name: str
    scenario: str = "baseline"
    description_text: str
    description_media_urls: list[str] = []

    # Dimensões [0, 1]
    complexity: ScorecardDimension
    initial_effort: ScorecardDimension
    perceived_risk: ScorecardDimension
    time_to_value: ScorecardDimension

    # Gerados por LLM
    justification: str | None = None
    impact_hypotheses: list[str] = []

class Experiment(BaseModel):
    """Experimento com scorecard embutido."""
    id: str = Field(default_factory=lambda: f"exp_{secrets.token_hex(4)}")
    name: str = Field(max_length=100)
    hypothesis: str = Field(max_length=500)
    description: str | None = Field(default=None, max_length=2000)

    # Scorecard embutido (opcional até ser preenchido)
    scorecard_data: ScorecardData | None = None

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime | None = None

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()

    def has_scorecard(self) -> bool:
        """Verifica se experimento tem scorecard preenchido."""
        return self.scorecard_data is not None
```

### 2. AnalysisRun (Análise Quantitativa)

```python
# domain/entities/analysis_run.py

class AnalysisConfig(BaseModel):
    """Configuração da análise quantitativa."""
    n_synths: int = Field(default=500, ge=10, le=10000)
    n_executions: int = Field(default=100, ge=10, le=1000)
    sigma: float = Field(default=0.05, ge=0.0, le=0.5)
    seed: int | None = None

class AggregatedOutcomes(BaseModel):
    """Resultados agregados da análise."""
    did_not_try_rate: float = Field(ge=0.0, le=1.0)
    failed_rate: float = Field(ge=0.0, le=1.0)
    success_rate: float = Field(ge=0.0, le=1.0)

class AnalysisRun(BaseModel):
    """Execução de análise quantitativa (1:1 com Experiment)."""
    id: str = Field(default_factory=lambda: f"ana_{secrets.token_hex(4)}")
    experiment_id: str  # FK para Experiment (UNIQUE)

    config: AnalysisConfig
    status: Literal["pending", "running", "completed", "failed"] = "pending"

    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = None

    total_synths: int = 0
    aggregated_outcomes: AggregatedOutcomes | None = None
    execution_time_seconds: float | None = None
```

### 3. SynthOutcome (Resultado por Synth)

```python
# domain/entities/synth_outcome.py

class SynthOutcome(BaseModel):
    """Resultado de um synth na análise."""
    id: str = Field(default_factory=lambda: f"out_{secrets.token_hex(4)}")
    analysis_id: str  # FK para AnalysisRun
    synth_id: str

    did_not_try_rate: float = Field(ge=0.0, le=1.0)
    failed_rate: float = Field(ge=0.0, le=1.0)
    success_rate: float = Field(ge=0.0, le=1.0)

    synth_attributes: dict  # Atributos do synth usados na simulação
```

### 4. ResearchExecution (Entrevista)

```python
# domain/entities/research_execution.py

class ResearchExecution(BaseModel):
    """Execução de entrevistas (N:1 com Experiment)."""
    exec_id: str = Field(default_factory=lambda: f"res_{secrets.token_hex(4)}")
    experiment_id: str | None  # FK para Experiment (opcional)

    topic_name: str
    status: Literal["pending", "running", "generating_summary", "completed", "failed"] = "pending"

    synth_count: int = 0
    successful_count: int = 0
    failed_count: int = 0

    model: str = "gpt-4o-mini"
    max_turns: int = 6

    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = None

    summary_content: str | None = None
```

### 5. Transcript (Transcrição)

```python
# domain/entities/transcript.py

class Message(BaseModel):
    """Mensagem em uma transcrição."""
    speaker: Literal["Interviewer", "Interviewee"]
    text: str
    internal_notes: str | None = None

class Transcript(BaseModel):
    """Transcrição de uma entrevista com um synth."""
    id: str = Field(default_factory=lambda: f"trn_{secrets.token_hex(4)}")
    exec_id: str  # FK para ResearchExecution
    synth_id: str
    synth_name: str

    status: Literal["pending", "running", "completed", "failed"] = "pending"
    turn_count: int = 0
    messages: list[Message] = []

    timestamp: datetime = Field(default_factory=datetime.now)
```

## Schema SQL (SQLite)

```sql
-- Tabela principal: Experimentos com scorecard embutido
CREATE TABLE experiments (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL CHECK(length(name) <= 100),
    hypothesis TEXT NOT NULL CHECK(length(hypothesis) <= 500),
    description TEXT CHECK(length(description) <= 2000),

    -- Scorecard embutido como JSON
    scorecard_data TEXT CHECK(json_valid(scorecard_data) OR scorecard_data IS NULL),

    created_at TEXT NOT NULL,
    updated_at TEXT
);

CREATE INDEX idx_experiments_created_at ON experiments(created_at);
CREATE INDEX idx_experiments_name ON experiments(name);


-- Tabela: Análises Quantitativas (1:1 com experiment)
CREATE TABLE analysis_runs (
    id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL UNIQUE,  -- UNIQUE enforces 1:1

    config TEXT NOT NULL CHECK(json_valid(config)),
    status TEXT NOT NULL DEFAULT 'pending',

    started_at TEXT NOT NULL,
    completed_at TEXT,

    total_synths INTEGER DEFAULT 0,
    aggregated_outcomes TEXT CHECK(json_valid(aggregated_outcomes) OR aggregated_outcomes IS NULL),
    execution_time_seconds REAL,

    FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE
);

CREATE INDEX idx_analysis_runs_experiment_id ON analysis_runs(experiment_id);
CREATE INDEX idx_analysis_runs_status ON analysis_runs(status);


-- Tabela: Resultados por synth
CREATE TABLE synth_outcomes (
    id TEXT PRIMARY KEY,
    analysis_id TEXT NOT NULL,
    synth_id TEXT NOT NULL,

    did_not_try_rate REAL NOT NULL,
    failed_rate REAL NOT NULL,
    success_rate REAL NOT NULL,

    synth_attributes TEXT CHECK(json_valid(synth_attributes)),

    FOREIGN KEY (analysis_id) REFERENCES analysis_runs(id) ON DELETE CASCADE
);

CREATE INDEX idx_synth_outcomes_analysis_id ON synth_outcomes(analysis_id);


-- Tabela: Entrevistas (N:1 com experiment)
CREATE TABLE research_executions (
    exec_id TEXT PRIMARY KEY,
    experiment_id TEXT,  -- Nullable for standalone executions

    topic_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',

    synth_count INTEGER NOT NULL DEFAULT 0,
    successful_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,

    model TEXT DEFAULT 'gpt-4o-mini',
    max_turns INTEGER DEFAULT 6,

    started_at TEXT NOT NULL,
    completed_at TEXT,

    summary_content TEXT,

    FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE SET NULL
);

CREATE INDEX idx_research_executions_experiment_id ON research_executions(experiment_id);
CREATE INDEX idx_research_executions_status ON research_executions(status);
CREATE INDEX idx_research_executions_topic_name ON research_executions(topic_name);


-- Tabela: Transcrições
CREATE TABLE transcripts (
    id TEXT PRIMARY KEY,
    exec_id TEXT NOT NULL,
    synth_id TEXT NOT NULL,
    synth_name TEXT NOT NULL,

    status TEXT NOT NULL DEFAULT 'pending',
    turn_count INTEGER DEFAULT 0,
    messages TEXT CHECK(json_valid(messages)),

    timestamp TEXT NOT NULL,

    FOREIGN KEY (exec_id) REFERENCES research_executions(exec_id) ON DELETE CASCADE
);

CREATE INDEX idx_transcripts_exec_id ON transcripts(exec_id);
CREATE INDEX idx_transcripts_synth_id ON transcripts(synth_id);


-- Tabelas auxiliares (existentes, mantidas)
CREATE TABLE IF NOT EXISTS synths (
    id TEXT PRIMARY KEY,
    group_id TEXT,
    name TEXT NOT NULL,
    attributes TEXT CHECK(json_valid(attributes)),
    link_photo TEXT,
    local_photo_path TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS synth_groups (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    size INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS topic_guides (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    context_definition TEXT NOT NULL,
    questions TEXT NOT NULL CHECK(json_valid(questions)),
    created_at TEXT NOT NULL,
    updated_at TEXT
);
```

## Relacionamentos

| Tabela Origem | Tabela Destino | Cardinalidade | FK Column | ON DELETE |
|---------------|----------------|---------------|-----------|-----------|
| experiments | analysis_runs | 1:1 | experiment_id (UNIQUE) | CASCADE |
| experiments | research_executions | 1:N | experiment_id | SET NULL |
| analysis_runs | synth_outcomes | 1:N | analysis_id | CASCADE |
| research_executions | transcripts | 1:N | exec_id | CASCADE |

## Validações de Negócio

### Experiment
- `name`: Obrigatório, max 100 chars, não pode ser vazio ou só espaços
- `hypothesis`: Obrigatório, max 500 chars
- `description`: Opcional, max 2000 chars
- `scorecard_data`: Obrigatório antes de executar análise

### ScorecardData (dentro de Experiment)
- Todas dimensões: Score entre 0.0 e 1.0
- `feature_name`: Obrigatório
- `description_text`: Obrigatório

### AnalysisRun
- `experiment_id`: Obrigatório e UNIQUE (garante 1:1)
- `n_synths`: Entre 10 e 10000
- `n_executions`: Entre 10 e 1000
- `sigma`: Entre 0.0 e 0.5

### ResearchExecution
- `experiment_id`: Opcional (permite entrevistas standalone)
- `topic_name`: Obrigatório
- `max_turns`: Padrão 6

## Transições de Estado

### AnalysisRun.status
```
pending → running → completed
                 ↘ failed
```

### ResearchExecution.status
```
pending → running → generating_summary → completed
                 ↘ failed
```

### Transcript.status
```
pending → running → completed
                 ↘ failed
```
