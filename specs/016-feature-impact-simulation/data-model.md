# Data Model: Sistema de Simulacao de Impacto de Features

**Date**: 2025-12-23
**Feature**: 016-feature-impact-simulation

## Entidades

### 1. SimulationAttributes (extensão do Synth)

Nova seção no schema de Synth para atributos de simulação.

```python
class SimulationObservables(BaseModel):
    """Atributos observáveis gerados durante gensynth."""

    digital_literacy: float = Field(ge=0.0, le=1.0)
    # Gerado: Beta(2, 4) → maioria baixa-média
    # Mapeado para: capacidades_tecnologicas.alfabetizacao_digital (0-100)

    similar_tool_experience: float = Field(ge=0.0, le=1.0)
    # Gerado: Beta(3, 3) → distribuição simétrica

    motor_ability: float = Field(ge=0.0, le=1.0)
    # Derivado de: deficiencias.motora.tipo
    # nenhuma=1.0, leve=0.8, moderada=0.5, severa=0.2

    time_availability: float = Field(ge=0.0, le=1.0)
    # Gerado: Beta(2, 3) → maioria com pouco tempo

    domain_expertise: float = Field(ge=0.0, le=1.0)
    # Gerado: Beta(3, 3) → simétrica


class SimulationLatentTraits(BaseModel):
    """Variáveis latentes derivadas dos observáveis."""

    capability_mean: float = Field(ge=0.0, le=1.0)
    # 0.40*digital_literacy + 0.35*similar_tool_experience +
    # 0.15*motor_ability + 0.10*domain_expertise

    trust_mean: float = Field(ge=0.0, le=1.0)
    # 0.60*similar_tool_experience + 0.40*digital_literacy

    friction_tolerance_mean: float = Field(ge=0.0, le=1.0)
    # 0.40*time_availability + 0.35*digital_literacy +
    # 0.25*similar_tool_experience

    exploration_prob: float = Field(ge=0.0, le=1.0)
    # 0.50*digital_literacy + 0.30*(1-similar_tool_experience) +
    # 0.20*time_availability


class SimulationAttributes(BaseModel):
    """Atributos completos de simulação para um synth."""

    observables: SimulationObservables
    latent_traits: SimulationLatentTraits
```

### 2. FeatureScorecard

Cadastro de uma feature para avaliação de impacto.

```python
class ScorecardDimension(BaseModel):
    """Uma dimensão do scorecard com score, regras e incerteza."""

    score: float = Field(ge=0.0, le=1.0)
    rules_applied: list[str] = Field(default_factory=list)
    # Ex: ["2 conceitos novos", "estados invisíveis"]

    min_uncertainty: float = Field(ge=0.0, le=1.0)
    max_uncertainty: float = Field(ge=0.0, le=1.0)

    @model_validator(mode='after')
    def validate_uncertainty_range(self) -> Self:
        if self.min_uncertainty > self.max_uncertainty:
            raise ValueError("min_uncertainty must be <= max_uncertainty")
        return self


class ScorecardIdentification(BaseModel):
    """Identificação do scorecard."""

    feature_name: str
    use_scenario: str
    created_at: datetime
    evaluators: list[str] = Field(default_factory=list)
    # Ex: ["Produto: João", "UX: Maria", "Eng: Pedro"]


class FeatureScorecard(BaseModel):
    """Cadastro completo de feature para simulação."""

    id: str = Field(pattern=r"^[a-zA-Z0-9]{8}$")
    identification: ScorecardIdentification

    # Descrição rica
    description_text: str
    description_media_urls: list[str] = Field(default_factory=list)

    # Dimensões
    complexity: ScorecardDimension
    initial_effort: ScorecardDimension
    perceived_risk: ScorecardDimension
    time_to_value: ScorecardDimension

    # LLM-generated
    justification: str | None = None
    impact_hypotheses: list[str] = Field(default_factory=list)

    # Metadata
    version: str = "1.0.0"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime | None = None
```

### 3. Scenario

Cenário contextual pré-definido.

```python
class Scenario(BaseModel):
    """Contexto de uso que modifica estado dos synths."""

    id: str  # "baseline", "crisis", "first-use"
    name: str
    description: str

    # Modificadores [-0.3, +0.3]
    motivation_modifier: float = Field(ge=-0.3, le=0.3)
    trust_modifier: float = Field(ge=-0.3, le=0.3)
    friction_modifier: float = Field(ge=-0.3, le=0.3)

    # Criticidade da tarefa [0, 1]
    task_criticality: float = Field(ge=0.0, le=1.0)


# Cenários pré-definidos
PREDEFINED_SCENARIOS = {
    "baseline": Scenario(
        id="baseline",
        name="Baseline",
        description="Condições típicas de uso",
        motivation_modifier=0.0,
        trust_modifier=0.0,
        friction_modifier=0.0,
        task_criticality=0.5
    ),
    "crisis": Scenario(
        id="crisis",
        name="Crise",
        description="Urgência, precisa resolver rápido",
        motivation_modifier=0.2,
        trust_modifier=-0.1,
        friction_modifier=-0.15,
        task_criticality=0.85
    ),
    "first-use": Scenario(
        id="first-use",
        name="Primeiro Uso",
        description="Exploração inicial do produto",
        motivation_modifier=0.1,
        trust_modifier=-0.2,
        friction_modifier=0.0,
        task_criticality=0.2
    )
}
```

### 4. SimulationRun

Execução de uma simulação.

```python
class SimulationConfig(BaseModel):
    """Configuração de uma simulação."""

    n_synths: int = Field(default=500, ge=1)
    n_executions: int = Field(default=100, ge=1)
    sigma: float = Field(default=0.05, ge=0.0, le=0.5)
    # Ruído sobre variáveis latentes

    seed: int | None = None
    # Para reprodutibilidade


class SimulationRun(BaseModel):
    """Registro de uma execução de simulação."""

    id: str = Field(pattern=r"^sim_[a-zA-Z0-9]{8}$")
    scorecard_id: str
    scenario_id: str
    config: SimulationConfig

    # Status
    status: Literal["pending", "running", "completed", "failed"]
    started_at: datetime
    completed_at: datetime | None = None

    # Métricas agregadas
    total_synths: int = 0
    aggregated_outcomes: dict[str, float] | None = None
    # {"did_not_try": 0.25, "failed": 0.35, "success": 0.40}

    # Performance
    execution_time_seconds: float | None = None
```

### 5. SynthOutcome

Resultado por synth em uma simulação.

```python
class SynthOutcome(BaseModel):
    """Resultado de simulação para um synth específico."""

    simulation_id: str
    synth_id: str

    # Proporções de outcomes [0, 1]
    did_not_try_rate: float = Field(ge=0.0, le=1.0)
    failed_rate: float = Field(ge=0.0, le=1.0)
    success_rate: float = Field(ge=0.0, le=1.0)

    # Atributos do synth (snapshot no momento da simulação)
    synth_attributes: SimulationAttributes

    @model_validator(mode='after')
    def validate_rates_sum(self) -> Self:
        total = self.did_not_try_rate + self.failed_rate + self.success_rate
        if not (0.99 <= total <= 1.01):  # Tolerância de arredondamento
            raise ValueError(f"Rates must sum to 1.0, got {total}")
        return self
```

### 6. RegionAnalysis

Análise de uma região do espaço de synths.

```python
class RegionRule(BaseModel):
    """Uma regra que define uma região."""

    attribute: str  # Ex: "capability_mean"
    operator: Literal["<", "<=", ">", ">="]
    threshold: float


class RegionAnalysis(BaseModel):
    """Grupo emergente identificado na análise."""

    id: str
    simulation_id: str

    # Regras que definem a região
    rules: list[RegionRule]
    # Ex: [{"attribute": "capability_mean", "operator": "<", "threshold": 0.48}]

    # Representação textual
    rule_text: str
    # Ex: "capability_mean < 0.48 AND trust_mean < 0.4"

    # Métricas
    synth_count: int
    synth_percentage: float  # % da população total

    # Outcomes desta região
    did_not_try_rate: float
    failed_rate: float
    success_rate: float

    # Comparação com população geral
    failure_delta: float
    # Diferença entre taxa de falha desta região vs. população geral
```

### 7. SensitivityResult

Resultado de análise de sensibilidade.

```python
class DimensionSensitivity(BaseModel):
    """Sensibilidade de uma dimensão do scorecard."""

    dimension: str  # complexity, initial_effort, perceived_risk, time_to_value

    # Valores testados
    baseline_value: float
    deltas_tested: list[float]  # [-0.10, -0.05, +0.05, +0.10]

    # Resultados por delta
    outcomes_by_delta: dict[str, dict[str, float]]
    # {"-0.10": {"did_not_try": 0.20, "failed": 0.30, "success": 0.50}, ...}

    # Índices de sensibilidade
    sensitivity_index: float
    # (% mudança output) / (% mudança input)

    # Ranking
    rank: int  # 1 = mais sensível


class SensitivityResult(BaseModel):
    """Resultado completo de análise de sensibilidade."""

    simulation_id: str
    analyzed_at: datetime

    # Configuração
    deltas_used: list[float]  # [0.05, 0.10]

    # Resultados por dimensão
    dimensions: list[DimensionSensitivity]

    # Dimensão mais impactante
    most_sensitive_dimension: str
```

### 8. AssumptionLog

Log de auditoria.

```python
class LogEntry(BaseModel):
    """Uma entrada no log de premissas."""

    id: str
    timestamp: datetime
    action: str  # "create_scorecard", "run_simulation", "analyze_region", etc.

    # Referências
    scorecard_id: str | None = None
    simulation_id: str | None = None

    # Dados
    data: dict[str, Any] = Field(default_factory=dict)
    # Ex: {"scorecard_version": "1.0.0", "scores": {...}}

    # Usuário (se aplicável)
    user: str | None = None


class AssumptionLog(BaseModel):
    """Registro histórico de decisões."""

    entries: list[LogEntry] = Field(default_factory=list)

    def add_entry(self, action: str, **kwargs) -> LogEntry:
        entry = LogEntry(
            id=generate_log_id(),
            timestamp=datetime.now(timezone.utc),
            action=action,
            **kwargs
        )
        self.entries.append(entry)
        return entry
```

---

## Relacionamentos

```
┌─────────────────┐
│     Synth       │
│  (existente)    │
├─────────────────┤
│ + simulation_   │◄────────────────────────────────────┐
│   attributes    │                                     │
└────────┬────────┘                                     │
         │                                              │
         │ 1:N                                          │
         ▼                                              │
┌─────────────────┐     N:1     ┌─────────────────┐     │
│  SynthOutcome   │────────────►│  SimulationRun  │     │
└─────────────────┘             ├─────────────────┤     │
                                │ scorecard_id    │─────┼──┐
                                │ scenario_id     │──┐  │  │
                                └────────┬────────┘  │  │  │
                                         │           │  │  │
                                         │ 1:N       │  │  │
                                         ▼           │  │  │
                                ┌─────────────────┐  │  │  │
                                │ RegionAnalysis  │  │  │  │
                                └─────────────────┘  │  │  │
                                                     │  │  │
                                ┌─────────────────┐  │  │  │
                                │    Scenario     │◄─┘  │  │
                                │ (pré-definido)  │     │  │
                                └─────────────────┘     │  │
                                                        │  │
                                ┌─────────────────┐     │  │
                                │ FeatureScorecard│◄────┘  │
                                └─────────────────┘        │
                                                           │
                                ┌─────────────────┐        │
                                │ AssumptionLog   │◄───────┘
                                │ (audit trail)   │
                                └─────────────────┘
```

---

## Persistência

### SQLite Tables

```sql
-- Nova coluna em synths (JSON)
-- Já existe: data TEXT CHECK(json_valid(data) OR data IS NULL)
-- simulation_attributes será armazenado dentro de data

-- Feature Scorecards
CREATE TABLE IF NOT EXISTS feature_scorecards (
    id TEXT PRIMARY KEY,
    data TEXT NOT NULL CHECK(json_valid(data)),
    created_at TEXT NOT NULL,
    updated_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_scorecards_created ON feature_scorecards(created_at DESC);

-- Simulation Runs
CREATE TABLE IF NOT EXISTS simulation_runs (
    id TEXT PRIMARY KEY,
    scorecard_id TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    config TEXT NOT NULL CHECK(json_valid(config)),
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    aggregated_outcomes TEXT CHECK(json_valid(aggregated_outcomes) OR aggregated_outcomes IS NULL),
    execution_time_seconds REAL,
    FOREIGN KEY (scorecard_id) REFERENCES feature_scorecards(id)
);

CREATE INDEX IF NOT EXISTS idx_simulations_scorecard ON simulation_runs(scorecard_id);
CREATE INDEX IF NOT EXISTS idx_simulations_status ON simulation_runs(status);

-- Synth Outcomes
CREATE TABLE IF NOT EXISTS synth_outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    simulation_id TEXT NOT NULL,
    synth_id TEXT NOT NULL,
    did_not_try_rate REAL NOT NULL,
    failed_rate REAL NOT NULL,
    success_rate REAL NOT NULL,
    synth_attributes TEXT CHECK(json_valid(synth_attributes)),
    UNIQUE(simulation_id, synth_id),
    FOREIGN KEY (simulation_id) REFERENCES simulation_runs(id)
);

CREATE INDEX IF NOT EXISTS idx_outcomes_simulation ON synth_outcomes(simulation_id);

-- Region Analysis
CREATE TABLE IF NOT EXISTS region_analyses (
    id TEXT PRIMARY KEY,
    simulation_id TEXT NOT NULL,
    rules TEXT NOT NULL CHECK(json_valid(rules)),
    rule_text TEXT NOT NULL,
    synth_count INTEGER NOT NULL,
    synth_percentage REAL NOT NULL,
    did_not_try_rate REAL NOT NULL,
    failed_rate REAL NOT NULL,
    success_rate REAL NOT NULL,
    failure_delta REAL NOT NULL,
    FOREIGN KEY (simulation_id) REFERENCES simulation_runs(id)
);

-- Assumption Log
CREATE TABLE IF NOT EXISTS assumption_log (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    action TEXT NOT NULL,
    scorecard_id TEXT,
    simulation_id TEXT,
    data TEXT CHECK(json_valid(data) OR data IS NULL),
    user TEXT
);

CREATE INDEX IF NOT EXISTS idx_log_timestamp ON assumption_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_log_action ON assumption_log(action);
```

---

## Validações

### Regras de Negócio

1. **SimulationAttributes**: Todos os valores devem estar em [0, 1]
2. **SynthOutcome**: `did_not_try_rate + failed_rate + success_rate = 1.0` (±0.01 tolerância)
3. **ScorecardDimension**: `min_uncertainty <= max_uncertainty`
4. **Scenario modifiers**: Devem estar em [-0.3, +0.3]
5. **Scenario task_criticality**: Deve estar em [0, 1]
6. **FeatureScorecard**: Todos os scores e uncertainties em [0, 1]

### State Transitions

```
SimulationRun.status:
  pending → running → completed
                   └→ failed
```
