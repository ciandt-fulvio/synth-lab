# Pre-Work: Sistema de Análise para UX Research

**Feature Branch**: `017-analysis-ux-research` (futuro)
**Created**: 2025-12-26
**Status**: Pre-Work / Research
**Dependency**: 016-feature-impact-simulation

---

## Visão Geral da Jornada

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        JORNADA DO UX RESEARCHER                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   "O que          "Onde           "Quem são       "Quem           "Por que │
│   aconteceu?"     quebra?"        eles?"          investigar?"    falhou?" │
│        │               │               │               │               │    │
│        ▼               ▼               ▼               ▼               ▼    │
│   ┌────────┐      ┌────────┐      ┌────────┐      ┌────────┐      ┌───────┐│
│   │ VISÃO  │ ───► │LOCALI- │ ───► │SEGMEN- │ ───► │ CASOS  │ ───► │EXPLI- ││
│   │ GERAL  │      │ ZAÇÃO  │      │ TAÇÃO  │      │ESPECIAIS│     │CAÇÃO  ││
│   └────────┘      └────────┘      └────────┘      └────────┘      └───────┘│
│   5 min           15 min          30 min          15 min          30 min   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Fases de Implementação

### FASE 1: Visão Geral
**Pergunta**: "O que aconteceu na simulação?"

| Componente | Tipo | Valor UX | Esforço |
|------------|------|----------|---------|
| **Try vs Success Scatter** | Gráfico | ⭐⭐⭐⭐⭐ | Trivial |
| **Outcome Distribution** | Gráfico | ⭐⭐⭐⭐⭐ | Trivial |

### FASE 2: Localização
**Pergunta**: "Onde exatamente a experiência quebra?"

| Componente | Tipo | Valor UX | Esforço |
|------------|------|----------|---------|
| **Failure Heatmap** | Gráfico | ⭐⭐⭐⭐⭐ | Médio |
| **Box Plot por Região** | Gráfico | ⭐⭐⭐⭐ | Baixo |
| **Scatter Trust vs Success** | Gráfico | ⭐⭐⭐⭐ | Baixo |
| **Tornado Diagram** | Gráfico | ⭐⭐⭐⭐ | Baixo |

### FASE 3: Segmentação
**Pergunta**: "Quem são esses usuários?"

| Componente | Tipo | Valor UX | Esforço |
|------------|------|----------|---------|
| **K-Means + Elbow** | ML | ⭐⭐⭐⭐ | Médio |
| **Persona Radar Chart** | Gráfico | ⭐⭐⭐⭐ | Baixo |
| **Hierarchical Clustering** | ML | ⭐⭐⭐⭐ | Médio |
| **Dendrograma** | Gráfico | ⭐⭐⭐⭐ | Baixo |

### FASE 4: Casos Especiais
**Pergunta**: "Quem devemos entrevistar primeiro?"

| Componente | Tipo | Valor UX | Esforço |
|------------|------|----------|---------|
| **Extreme Cases Table** | Tabela | ⭐⭐⭐⭐⭐ | Trivial |
| **Isolation Forest** | ML | ⭐⭐⭐⭐ | Médio |

### FASE 5: Explicação Profunda
**Pergunta**: "Por que esse synth específico falhou?"

| Componente | Tipo | Valor UX | Esforço |
|------------|------|----------|---------|
| **SHAP Values** | ML | ⭐⭐⭐⭐⭐ | Alto |
| **Partial Dependence Plots** | ML | ⭐⭐⭐⭐ | Alto |

### FASE 6: Insights LLM
**Pergunta**: "O que isso significa?"

| Componente | Tipo | Valor UX | Esforço |
|------------|------|----------|---------|
| **Caption Generator** | LLM | ⭐⭐⭐⭐ | Médio |
| **Insight Generator** | LLM | ⭐⭐⭐⭐⭐ | Médio |

---

## Arquitetura Proposta

```
src/synth_lab/
├── services/simulation/
│   ├── analyzer.py           # (existe) Decision Tree regions
│   ├── sensitivity.py        # (existe) OAT
│   ├── clustering.py         # (novo) K-Means, Hierarchical
│   ├── outliers.py           # (novo) Isolation Forest
│   ├── explainability.py     # (novo) SHAP, PDP
│   ├── chart_data.py         # (novo) dados para gráficos
│   └── insight_generator.py  # (novo) LLM captions/insights
│
├── domain/entities/
│   ├── cluster_result.py     # (novo)
│   ├── outlier_result.py     # (novo)
│   ├── chart_data.py         # (novo) tipos para gráficos
│   └── chart_insight.py      # (novo) LLM outputs
│
└── api/routers/
    └── simulation.py         # expandir com novos endpoints
```

---

## Endpoints Propostos

```python
# FASE 1 - Visão Geral
GET /simulation/simulations/{id}/charts/try-vs-success
GET /simulation/simulations/{id}/charts/distribution

# FASE 2 - Localização
GET /simulation/simulations/{id}/charts/failure-heatmap
GET /simulation/simulations/{id}/charts/box-plot
GET /simulation/simulations/{id}/charts/scatter
GET /simulation/simulations/{id}/charts/tornado

# FASE 3 - Segmentação
POST /simulation/simulations/{id}/clusters
GET /simulation/simulations/{id}/clusters
GET /simulation/simulations/{id}/clusters/elbow
GET /simulation/simulations/{id}/clusters/dendrogram
GET /simulation/simulations/{id}/clusters/{cluster_id}/radar
GET /simulation/simulations/{id}/clusters/radar-comparison

# FASE 4 - Casos Especiais
GET /simulation/simulations/{id}/extreme-cases
GET /simulation/simulations/{id}/outliers

# FASE 5 - Explicabilidade
GET /simulation/simulations/{id}/shap
GET /simulation/simulations/{id}/shap/summary
GET /simulation/simulations/{id}/pdp
GET /simulation/simulations/{id}/pdp/comparison

# FASE 6 - Insights LLM
GET /simulation/simulations/{id}/charts/{chart_type}/caption
GET /simulation/simulations/{id}/charts/{chart_type}/insight
GET /simulation/simulations/{id}/insights
```

---

# Apêndice: Requisitos Detalhados por Componente

---

## FASE 1: Visão Geral

### 1.1 Try vs Success Scatter

**O que é**: Scatter plot onde cada ponto é um synth, posicionado por taxa de tentativa (X) e taxa de sucesso (Y).

**Input necessário**:
```python
# De synth_outcomes (já existe)
{
    "synth_id": "synth_001",
    "did_not_try_rate": 0.25,  # → attempt_rate = 1 - 0.25 = 0.75
    "success_rate": 0.40
}
```

**Output esperado**:
```python
class TryVsSuccessPoint(BaseModel):
    synth_id: str
    attempt_rate: float      # X: 1 - did_not_try_rate
    success_rate: float      # Y: success_rate (dado tentativa)
    quadrant: Literal[
        "low_value",         # baixo X, baixo Y
        "usability_issue",   # alto X, baixo Y
        "discovery_issue",   # baixo X, alto Y
        "ok"                 # alto X, alto Y
    ]

class TryVsSuccessChart(BaseModel):
    simulation_id: str
    points: list[TryVsSuccessPoint]
    quadrant_counts: dict[str, int]
    quadrant_thresholds: dict[str, float]  # ex: {"x": 0.5, "y": 0.5}
```

**Lógica de quadrante**:
```python
def classify_quadrant(attempt_rate: float, success_rate: float) -> str:
    x_threshold = 0.5
    y_threshold = 0.5

    if attempt_rate < x_threshold and success_rate < y_threshold:
        return "low_value"       # Não tenta, não consegue → feature sem valor
    elif attempt_rate >= x_threshold and success_rate < y_threshold:
        return "usability_issue" # Tenta mas falha → problema de usabilidade
    elif attempt_rate < x_threshold and success_rate >= y_threshold:
        return "discovery_issue" # Não tenta mas conseguiria → problema de descoberta
    else:
        return "ok"              # Tenta e consegue → sucesso
```

**Endpoint**:
```
GET /simulation/simulations/{id}/charts/try-vs-success
    ?x_threshold=0.5
    &y_threshold=0.5
```

**Critérios de aceite**:
- [ ] Retorna todos os synths da simulação com coordenadas X, Y
- [ ] Classifica cada synth em um dos 4 quadrantes
- [ ] Retorna contagem agregada por quadrante
- [ ] Thresholds são configuráveis via query params

---

### 1.2 Outcome Distribution por Usuário

**O que é**: Stacked bar chart mostrando proporção de outcomes para cada synth (ou agregado por percentil).

**Input necessário**:
```python
# De synth_outcomes (já existe)
{
    "synth_id": "synth_001",
    "did_not_try_rate": 0.25,
    "failed_rate": 0.35,
    "success_rate": 0.40
}
```

**Output esperado**:
```python
class SynthDistribution(BaseModel):
    synth_id: str
    did_not_try_rate: float
    failed_rate: float
    success_rate: float
    # Ordenação para visualização
    sort_key: float  # ex: success_rate ou failed_rate

class OutcomeDistributionChart(BaseModel):
    simulation_id: str
    distributions: list[SynthDistribution]
    # Agregações úteis
    summary: dict[str, float]  # médias gerais
    worst_performers: list[str]  # top 10 synth_ids com menor success
    best_performers: list[str]   # top 10 synth_ids com maior success
```

**Modos de visualização**:
```python
class DistributionMode(str, Enum):
    BY_SYNTH = "by_synth"           # 1 barra por synth (pode ser muitos)
    BY_PERCENTILE = "by_percentile" # agrupa em P10, P25, P50, P75, P90
    BY_CLUSTER = "by_cluster"       # agrupa por cluster (se existir)
```

**Endpoint**:
```
GET /simulation/simulations/{id}/charts/distribution
    ?mode=by_synth|by_percentile|by_cluster
    &sort_by=success_rate|failed_rate|did_not_try_rate
    &order=asc|desc
    &limit=50
```

**Critérios de aceite**:
- [ ] Retorna distribuição de outcomes para todos os synths
- [ ] Suporta ordenação por qualquer outcome
- [ ] Suporta modo percentil para grandes volumes
- [ ] Identifica top/bottom performers

---


**O que é**: Diagrama de fluxo mostrando como synths "fluem" entre estados (all → attempted/not_attempted → success/failed).

**Input necessário**:
```python
# De aggregated_outcomes da simulação (já existe)
{
    "did_not_try": 0.25,
    "failed": 0.35,
    "success": 0.40
}
```

**Output esperado**:
```python
    id: str           # "all", "attempted", "not_attempted", "success", "failed"
    label: str        # "Todos (500)", "Tentaram (375)", etc.
    value: int        # contagem absoluta

    source: str       # id do nó origem
    target: str       # id do nó destino
    value: int        # contagem que flui
    percentage: float # % do total

    simulation_id: str
    total_synths: int
```

**Estrutura do fluxo**:
```
                    ┌─► Success (40%)
All Synths ─┬─► Attempted (75%) ─┤
            │                    └─► Failed (35%)
            │
            └─► Did Not Try (25%)
```

**Cálculos necessários**:
```python
    did_not_try_count = int(outcomes["did_not_try"] * total_synths)
    attempted_count = total_synths - did_not_try_count

    # Success e Failed são % dos que TENTARAM, não do total
    # Precisamos recalcular baseado nos que tentaram
    success_of_attempted = outcomes["success"] / (outcomes["success"] + outcomes["failed"])
    failed_of_attempted = outcomes["failed"] / (outcomes["success"] + outcomes["failed"])

    success_count = int(success_of_attempted * attempted_count)
    failed_count = attempted_count - success_count

    # ... build nodes and links
```

**Endpoint**:
```
```

**Critérios de aceite**:
- [ ] Retorna nós com contagens absolutas
- [ ] Retorna links com valores e percentuais
- [ ] Percentuais são calculados corretamente (success/failed são % dos que tentaram)
- [ ] Labels incluem contagem absoluta

---

## FASE 2: Localização

### 2.1 Failure Heatmap (2 variáveis)

**O que é**: Heatmap 2D onde cada célula mostra taxa de falha para combinação de dois atributos.

**Input necessário**:
```python
# De synth_outcomes + synth_attributes (já existe)
{
    "synth_id": "synth_001",
    "failed_rate": 0.35,
    "synth_attributes": {
        "latent_traits": {
            "capability_mean": 0.45,
            "trust_mean": 0.62,
            ...
        }
    }
}
```

**Output esperado**:
```python
class HeatmapCell(BaseModel):
    x_bin: str           # "0.0-0.2", "0.2-0.4", etc.
    y_bin: str
    x_range: tuple[float, float]  # (0.0, 0.2)
    y_range: tuple[float, float]
    failure_rate: float  # média de failed_rate nesta célula
    synth_count: int     # quantos synths nesta célula
    synth_ids: list[str] # para drill-down

class FailureHeatmapChart(BaseModel):
    simulation_id: str
    x_axis: str          # "capability_mean"
    y_axis: str          # "complexity" (do scorecard)
    bins: int            # 5
    cells: list[HeatmapCell]
    # Metadados
    max_failure_rate: float
    min_failure_rate: float
    critical_cells: list[HeatmapCell]  # células com failure > threshold
```

**Eixos disponíveis**:
```python
HEATMAP_AXES = {
    # Atributos do synth (latent_traits)
    "capability_mean",
    "trust_mean",
    "friction_tolerance_mean",
    "exploration_prob",
    # Atributos do scorecard (fixos por simulação, mas útil para comparar)
    # Nota: scorecard é fixo, então eixo Y seria synth attribute
}

# Combinações recomendadas:
RECOMMENDED_PAIRS = [
    ("capability_mean", "trust_mean"),           # capability vs trust
    ("friction_tolerance_mean", "capability_mean"), # tolerância vs capability
]
```

**Lógica de binning**:
```python
def create_bins(values: list[float], n_bins: int = 5) -> list[tuple[float, float]]:
    """Cria bins uniformes entre 0 e 1."""
    bin_size = 1.0 / n_bins
    return [(i * bin_size, (i + 1) * bin_size) for i in range(n_bins)]

def assign_bin(value: float, bins: list[tuple]) -> str:
    for low, high in bins:
        if low <= value < high:
            return f"{low:.1f}-{high:.1f}"
    return f"{bins[-1][0]:.1f}-{bins[-1][1]:.1f}"  # último bin inclui 1.0
```

**Endpoint**:
```
GET /simulation/simulations/{id}/charts/failure-heatmap
    ?x_axis=capability_mean
    &y_axis=trust_mean
    &bins=5
    &metric=failed_rate|did_not_try_rate|success_rate
```

**Critérios de aceite**:
- [ ] Suporta qualquer par de atributos latentes como eixos
- [ ] Número de bins é configurável
- [ ] Retorna contagem de synths por célula
- [ ] Identifica células críticas (failure > threshold)
- [ ] Permite drill-down para synth_ids específicos

---

### 2.2 Box Plot por Região

**O que é**: Box plot comparando distribuição de outcomes entre regiões identificadas pelo Decision Tree.

**Input necessário**:
```python
# De region_analyses (já existe)
{
    "id": "region_001",
    "rule_text": "capability_mean <= 0.48 AND trust_mean <= 0.4",
    "synth_count": 45,
    "failed_rate": 0.65,
    ...
}

# De synth_outcomes para cada synth na região
```

**Output esperado**:
```python
class BoxPlotStats(BaseModel):
    min: float
    q1: float      # 25th percentile
    median: float  # 50th percentile
    q3: float      # 75th percentile
    max: float
    mean: float
    outliers: list[float]

class RegionBoxPlot(BaseModel):
    region_id: str
    region_label: str  # rule_text simplificado
    synth_count: int
    success_rate_stats: BoxPlotStats
    failed_rate_stats: BoxPlotStats
    did_not_try_rate_stats: BoxPlotStats

class BoxPlotChart(BaseModel):
    simulation_id: str
    regions: list[RegionBoxPlot]
    baseline_stats: BoxPlotStats  # toda a população para comparação
```

**Lógica de cálculo**:
```python
def calculate_box_stats(values: list[float]) -> BoxPlotStats:
    arr = np.array(values)
    q1, median, q3 = np.percentile(arr, [25, 50, 75])
    iqr = q3 - q1
    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr

    outliers = arr[(arr < lower_fence) | (arr > upper_fence)].tolist()

    return BoxPlotStats(
        min=float(arr[arr >= lower_fence].min()) if any(arr >= lower_fence) else float(arr.min()),
        q1=q1,
        median=median,
        q3=q3,
        max=float(arr[arr <= upper_fence].max()) if any(arr <= upper_fence) else float(arr.max()),
        mean=float(arr.mean()),
        outliers=outliers
    )
```

**Endpoint**:
```
GET /simulation/simulations/{id}/charts/box-plot
    ?metric=success_rate|failed_rate|did_not_try_rate
    &include_baseline=true
```

**Critérios de aceite**:
- [ ] Usa regiões do region_analysis existente
- [ ] Calcula estatísticas corretas (quartis, outliers)
- [ ] Inclui baseline (toda população) para comparação
- [ ] Suporta seleção de métrica

---

### 2.3 Scatter Trust vs Success

**O que é**: Scatter plot mostrando correlação entre um atributo latente e taxa de sucesso.

**Input necessário**:
```python
# De synth_outcomes + synth_attributes
{
    "synth_id": "synth_001",
    "success_rate": 0.40,
    "synth_attributes": {
        "latent_traits": {
            "trust_mean": 0.62
        }
    }
}
```

**Output esperado**:
```python
class CorrelationPoint(BaseModel):
    synth_id: str
    x_value: float  # atributo (ex: trust_mean)
    y_value: float  # outcome (ex: success_rate)

class CorrelationStats(BaseModel):
    pearson_r: float      # coeficiente de correlação
    p_value: float        # significância estatística
    r_squared: float      # R²
    trend_slope: float    # inclinação da linha de tendência
    trend_intercept: float

class ScatterCorrelationChart(BaseModel):
    simulation_id: str
    x_axis: str           # "trust_mean"
    y_axis: str           # "success_rate"
    points: list[CorrelationPoint]
    correlation: CorrelationStats
    # Linha de tendência
    trendline: list[tuple[float, float]]  # pontos para plotar
```

**Atributos disponíveis para X**:
```python
X_AXIS_OPTIONS = [
    "capability_mean",
    "trust_mean",
    "friction_tolerance_mean",
    "exploration_prob",
    # Observáveis também
    "digital_literacy",
    "similar_tool_experience",
    "motor_ability",
    "time_availability",
    "domain_expertise",
]

Y_AXIS_OPTIONS = [
    "success_rate",
    "failed_rate",
    "did_not_try_rate",
    "attempt_rate",  # calculado: 1 - did_not_try_rate
]
```

**Endpoint**:
```
GET /simulation/simulations/{id}/charts/scatter
    ?x_axis=trust_mean
    &y_axis=success_rate
    &show_trendline=true
```

**Critérios de aceite**:
- [ ] Suporta qualquer atributo latente/observável como X
- [ ] Suporta qualquer outcome como Y
- [ ] Calcula correlação de Pearson
- [ ] Retorna pontos para linha de tendência
- [ ] Identifica correlação significativa (p < 0.05)

---

### 2.4 Tornado Diagram

**O que é**: Bar chart horizontal mostrando impacto de cada dimensão do scorecard nos outcomes.

**Input necessário**:
```python
# De sensitivity_result (já existe)
{
    "simulation_id": "sim_001",
    "dimensions": [
        {
            "dimension": "complexity",
            "sensitivity_index": 2.5,
            "rank": 1,
            "outcomes_by_delta": {
                "-0.1": {"success": 0.50},
                "+0.1": {"success": 0.30}
            }
        },
        ...
    ]
}
```

**Output esperado**:
```python
class TornadoBar(BaseModel):
    dimension: str
    rank: int
    sensitivity_index: float
    # Para o gráfico tornado, precisamos de impacto negativo e positivo
    negative_impact: float  # quando reduz a dimensão
    positive_impact: float  # quando aumenta a dimensão
    baseline_value: float
    # Labels
    label_negative: str  # "-10% → +5% success"
    label_positive: str  # "+10% → -8% success"

class TornadoChart(BaseModel):
    simulation_id: str
    baseline_success: float
    bars: list[TornadoBar]  # ordenados por sensitivity_index
    # Metadados
    deltas_used: list[float]
    most_sensitive: str
```

**Lógica de cálculo**:
```python
def build_tornado_bar(dim: DimensionSensitivity, baseline_success: float) -> TornadoBar:
    # Pega o maior delta testado
    max_delta = max(dim.deltas_tested)
    min_delta = min(dim.deltas_tested)

    # Impacto quando REDUZ a dimensão (delta negativo)
    neg_outcome = dim.outcomes_by_delta.get(str(min_delta), {})
    negative_impact = neg_outcome.get("success", baseline_success) - baseline_success

    # Impacto quando AUMENTA a dimensão (delta positivo)
    pos_outcome = dim.outcomes_by_delta.get(str(max_delta), {})
    positive_impact = pos_outcome.get("success", baseline_success) - baseline_success

    return TornadoBar(
        dimension=dim.dimension,
        rank=dim.rank,
        sensitivity_index=dim.sensitivity_index,
        negative_impact=negative_impact,
        positive_impact=positive_impact,
        baseline_value=dim.baseline_value,
        label_negative=f"{min_delta:+.0%} → {negative_impact:+.1%} success",
        label_positive=f"{max_delta:+.0%} → {positive_impact:+.1%} success"
    )
```

**Endpoint**:
```
GET /simulation/simulations/{id}/charts/tornado
```

**Pré-requisito**: Sensitivity analysis já executada para esta simulação.

**Critérios de aceite**:
- [ ] Usa dados de sensitivity_result existente
- [ ] Calcula impacto positivo e negativo separadamente
- [ ] Ordena por sensitivity_index
- [ ] Inclui labels legíveis para cada barra

---

## FASE 3: Segmentação

### 3.1 K-Means Clustering

**O que é**: Agrupa synths em K clusters baseado em atributos e/ou outcomes.

**Input necessário**:
```python
# Features para clustering (configurável)
features = [
    # Latent traits
    "capability_mean", "trust_mean", "friction_tolerance_mean", "exploration_prob",
    # Outcomes (opcional)
    "success_rate", "failed_rate"
]

# Dados de cada synth
synth_data = {
    "synth_001": {
        "capability_mean": 0.45,
        "trust_mean": 0.62,
        ...
        "success_rate": 0.40
    }
}
```

**Output esperado**:
```python
class ClusterProfile(BaseModel):
    cluster_id: int
    size: int
    percentage: float  # % do total
    # Centroid (média de cada feature)
    centroid: dict[str, float]
    # Outcomes médios
    avg_success_rate: float
    avg_failed_rate: float
    avg_did_not_try_rate: float
    # Características distintivas
    high_traits: list[str]  # traits acima da média geral
    low_traits: list[str]   # traits abaixo da média geral
    # Label sugerido
    suggested_label: str    # ex: "Tech Savvy", "Strugglers"

class KMeansResult(BaseModel):
    simulation_id: str
    n_clusters: int
    # Métricas de qualidade
    silhouette_score: float  # -1 a 1, maior é melhor
    inertia: float           # soma das distâncias ao centroid
    # Resultados
    clusters: list[ClusterProfile]
    synth_assignments: dict[str, int]  # synth_id → cluster_id
    # Para Elbow Method
    elbow_data: list[dict]  # [{k: 2, inertia: X, silhouette: Y}, ...]
```

**Lógica de implementação**:
```python
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

class ClusteringService:
    def cluster_kmeans(
        self,
        outcomes: list[dict],
        n_clusters: int = 4,
        features: list[str] | None = None
    ) -> KMeansResult:
        # 1. Extrair features
        if features is None:
            features = ["capability_mean", "trust_mean",
                       "friction_tolerance_mean", "exploration_prob"]

        X, synth_ids = self._extract_features(outcomes, features)

        # 2. Normalizar (importante para K-Means)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # 3. Fit K-Means
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X_scaled)

        # 4. Calcular métricas
        sil_score = silhouette_score(X_scaled, labels)

        # 5. Elbow data (para sugerir K ideal)
        elbow_data = self._calculate_elbow(X_scaled, max_k=10)

        # 6. Construir profiles
        clusters = self._build_cluster_profiles(
            X, synth_ids, labels, outcomes, features
        )

        return KMeansResult(
            simulation_id=simulation_id,
            n_clusters=n_clusters,
            silhouette_score=sil_score,
            inertia=kmeans.inertia_,
            clusters=clusters,
            synth_assignments={sid: int(lbl) for sid, lbl in zip(synth_ids, labels)},
            elbow_data=elbow_data
        )

    def _calculate_elbow(self, X: np.ndarray, max_k: int = 10) -> list[dict]:
        """Calcula inertia e silhouette para diferentes valores de K."""
        results = []
        for k in range(2, min(max_k + 1, len(X))):
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(X)
            results.append({
                "k": k,
                "inertia": kmeans.inertia_,
                "silhouette": silhouette_score(X, labels)
            })
        return results

    def _suggest_label(self, profile: dict) -> str:
        """Sugere label baseado em características dominantes."""
        labels = {
            ("high_capability", "high_trust"): "Power Users",
            ("high_capability", "low_trust"): "Skeptical Experts",
            ("low_capability", "high_trust"): "Eager Learners",
            ("low_capability", "low_trust"): "Strugglers",
            ("high_exploration",): "Explorers",
            ("low_exploration",): "Task-Focused",
        }
        # Match baseado em high_traits/low_traits
        ...
```

**Endpoint**:
```
POST /simulation/simulations/{id}/clusters
    body: {
        "method": "kmeans",
        "n_clusters": 4,
        "features": ["capability_mean", "trust_mean", ...],  # opcional
        "include_outcomes": false  # se true, inclui success_rate etc
    }

GET /simulation/simulations/{id}/clusters
    # Retorna último resultado de clustering

GET /simulation/simulations/{id}/clusters/elbow
    # Retorna dados para Elbow Method chart
```

**Critérios de aceite**:
- [ ] Implementa K-Means com normalização
- [ ] Calcula silhouette score
- [ ] Gera dados para Elbow Method
- [ ] Identifica características distintivas de cada cluster
- [ ] Sugere labels legíveis
- [ ] Persiste resultado para reutilização

---

### 3.2 Persona Radar Chart

**O que é**: Radar/Spider chart mostrando perfil de cada cluster em múltiplas dimensões.

**Input necessário**:
```python
# De KMeansResult ou HierarchicalResult
cluster_profile = {
    "cluster_id": 1,
    "centroid": {
        "capability_mean": 0.72,
        "trust_mean": 0.45,
        "friction_tolerance_mean": 0.68,
        "exploration_prob": 0.55
    },
    "avg_success_rate": 0.65
}
```

**Output esperado**:
```python
class RadarAxis(BaseModel):
    name: str           # "capability_mean"
    label: str          # "Capability"
    value: float        # 0.72
    normalized: float   # valor normalizado 0-1 para plotar

class ClusterRadar(BaseModel):
    cluster_id: int
    label: str          # "Power Users"
    color: str          # "#FF6B6B" para visualização
    axes: list[RadarAxis]
    # Outcome summary
    success_rate: float

class RadarChart(BaseModel):
    simulation_id: str
    clusters: list[ClusterRadar]
    # Eixos (mesmos para todos os clusters)
    axis_labels: list[str]
    # Baseline para comparação (média geral)
    baseline: list[float]
```

**Lógica de normalização**:
```python
def normalize_for_radar(value: float, min_val: float = 0, max_val: float = 1) -> float:
    """Normaliza valor para escala 0-1 do radar."""
    return (value - min_val) / (max_val - min_val)

# Para atributos que já são 0-1, normalização é identidade
# Mas podemos usar min/max da população para melhor contraste
```

**Endpoint**:
```
GET /simulation/simulations/{id}/clusters/{cluster_id}/radar

GET /simulation/simulations/{id}/clusters/radar-comparison
    # Retorna todos os clusters sobrepostos
```

**Critérios de aceite**:
- [ ] Gera radar para cada cluster
- [ ] Suporta sobreposição de múltiplos clusters
- [ ] Inclui baseline (média geral) para referência
- [ ] Normaliza valores para escala comparável

---

### 3.3 Hierarchical Clustering

**O que é**: Clustering hierárquico que mostra relações de similaridade em árvore.

**Input necessário**:
```python
# Mesmos features do K-Means
features = ["capability_mean", "trust_mean", ...]
```

**Output esperado**:
```python
class DendrogramNode(BaseModel):
    id: int
    # Se folha
    synth_id: str | None
    # Se nó interno
    left_child: int | None
    right_child: int | None
    # Distância de merge
    distance: float
    # Contagem de folhas abaixo
    count: int

class HierarchicalResult(BaseModel):
    simulation_id: str
    method: str  # "ward", "complete", "average"
    # Estrutura do dendrograma
    nodes: list[DendrogramNode]
    linkage_matrix: list[list[float]]  # formato scipy
    # Cortes sugeridos
    suggested_cuts: list[dict]  # [{n_clusters: 4, distance: 2.5}, ...]
    # Se cortado em N clusters
    cluster_assignments: dict[str, int] | None
```

**Lógica de implementação**:
```python
from scipy.cluster.hierarchy import linkage, fcluster, dendrogram
from scipy.spatial.distance import pdist

class ClusteringService:
    def cluster_hierarchical(
        self,
        outcomes: list[dict],
        method: str = "ward",
        features: list[str] | None = None
    ) -> HierarchicalResult:
        X, synth_ids = self._extract_features(outcomes, features)

        # Normalizar
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Calcular linkage
        Z = linkage(X_scaled, method=method)

        # Encontrar cortes sugeridos (gaps na distância)
        suggested_cuts = self._find_suggested_cuts(Z)

        # Construir nós do dendrograma
        nodes = self._build_dendrogram_nodes(Z, synth_ids)

        return HierarchicalResult(
            simulation_id=simulation_id,
            method=method,
            nodes=nodes,
            linkage_matrix=Z.tolist(),
            suggested_cuts=suggested_cuts
        )

    def cut_dendrogram(
        self,
        result: HierarchicalResult,
        n_clusters: int
    ) -> dict[str, int]:
        """Corta dendrograma em N clusters."""
        Z = np.array(result.linkage_matrix)
        labels = fcluster(Z, n_clusters, criterion='maxclust')
        # Mapear para synth_ids
        ...
```

**Endpoint**:
```
POST /simulation/simulations/{id}/clusters
    body: {
        "method": "hierarchical",
        "linkage": "ward"  # ward, complete, average, single
    }

POST /simulation/simulations/{id}/clusters/cut
    body: {
        "n_clusters": 4
    }
```

**Critérios de aceite**:
- [ ] Implementa hierarchical clustering com scipy
- [ ] Suporta diferentes métodos de linkage
- [ ] Sugere pontos de corte baseado em gaps
- [ ] Permite cortar em N clusters específico
- [ ] Retorna estrutura para renderizar dendrograma

---

### 3.4 Dendrograma

**O que é**: Visualização em árvore do hierarchical clustering.

**Input necessário**:
```python
# De HierarchicalResult
linkage_matrix = [...]  # formato scipy
```

**Output esperado**:
```python
class DendrogramBranch(BaseModel):
    """Representação para renderização do dendrograma."""
    x_start: float
    x_end: float
    y_start: float
    y_end: float
    # Metadados
    is_leaf: bool
    synth_id: str | None
    cluster_id: int | None
    count: int  # synths abaixo deste nó

class DendrogramChart(BaseModel):
    simulation_id: str
    branches: list[DendrogramBranch]
    leaves: list[dict]  # [{x: 0, synth_id: "...", cluster_id: 1}, ...]
    # Linhas de corte sugeridas
    cut_lines: list[dict]  # [{y: 2.5, n_clusters: 4}, ...]
    # Dimensões
    width: float
    height: float
```

**Nota**: A renderização real será no frontend. O backend retorna coordenadas.

**Endpoint**:
```
GET /simulation/simulations/{id}/clusters/dendrogram
    ?max_depth=5          # limita profundidade para grandes datasets
    &truncate_mode=level  # level, lastp, none
    &color_threshold=2.5  # colorir por cluster
```

**Critérios de aceite**:
- [ ] Retorna coordenadas para renderização
- [ ] Suporta truncamento para grandes datasets
- [ ] Inclui linhas de corte sugeridas
- [ ] Permite coloração por cluster

---

### 3.5 Relacionamento entre Clustering e Visualizações

**Fluxo recomendado**:
```
┌─────────────────────────────────────────────────────────────────────────┐
│                        FLUXO DE CLUSTERING                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Outcomes + Attributes                                                 │
│          │                                                              │
│          ▼                                                              │
│   ┌──────────────┐         ┌──────────────┐                            │
│   │   K-Means    │         │ Hierarchical │                            │
│   │  (n=4 fixo)  │         │  Clustering  │                            │
│   └──────┬───────┘         └──────┬───────┘                            │
│          │                        │                                     │
│          ▼                        ▼                                     │
│   ┌──────────────┐         ┌──────────────┐                            │
│   │ Radar Chart  │         │  Dendrograma │                            │
│   │ (1 por       │         │ (hierarquia) │                            │
│   │  cluster)    │         │              │                            │
│   └──────────────┘         └──────────────┘                            │
│                                                                         │
│   OPÇÃO LINKADA: Hierarchical gera clusters, Radar visualiza cada um  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## FASE 4: Casos Especiais

### 4.1 Extreme Cases Table

**O que é**: Tabela dos synths mais extremos (piores falhas, melhores sucessos, mais instáveis).

**Input necessário**:
```python
# De synth_outcomes + synth (dados completos)
{
    "synth_id": "synth_001",
    "success_rate": 0.05,  # muito baixo
    "failed_rate": 0.85,
    "synth_attributes": {...},
    # Dados do synth para contexto
    "synth_profile": {
        "idade": 67,
        "profissao": "Aposentado",
        ...
    }
}
```

**Output esperado**:
```python
class ExtremeSynth(BaseModel):
    synth_id: str
    rank: int
    extreme_type: Literal["worst_failure", "best_success", "most_unstable", "unexpected"]
    # Outcomes
    success_rate: float
    failed_rate: float
    did_not_try_rate: float
    # Perfil resumido
    profile_summary: str  # "Idoso, 67 anos, aposentado, alta capability"
    # Atributos chave
    key_attributes: dict[str, float]
    # Por que é extremo
    reason: str  # "Alta capability (0.8) mas 85% falha - frustração"
    # Para entrevista
    interview_priority: int  # 1-10
    interview_questions: list[str]  # sugestões de perguntas

class ExtremeCasesTable(BaseModel):
    simulation_id: str
    # Categorias
    worst_failures: list[ExtremeSynth]
    best_successes: list[ExtremeSynth]
    most_unstable: list[ExtremeSynth]  # alta variância entre execuções
    unexpected: list[ExtremeSynth]      # outliers do Isolation Forest
    # Totais
    total_analyzed: int
```

**Lógica de identificação**:
```python
def identify_extreme_cases(
    outcomes: list[dict],
    synths: list[dict],
    top_n: int = 10
) -> ExtremeCasesTable:
    # Worst failures: menor success_rate
    sorted_by_failure = sorted(outcomes, key=lambda x: x["success_rate"])
    worst_failures = sorted_by_failure[:top_n]

    # Best successes: maior success_rate
    best_successes = sorted_by_failure[-top_n:][::-1]

    # Most unstable: maior variância (se tivermos execuções individuais)
    # Nota: precisa de dados de execuções, não só agregados

    # Unexpected: onde outcome não bate com atributos
    # Ex: alta capability + alta trust mas baixo success
    unexpected = find_unexpected(outcomes)

    return ExtremeCasesTable(...)

def find_unexpected(outcomes: list[dict]) -> list[dict]:
    """Encontra synths cujo outcome não corresponde aos atributos."""
    unexpected = []
    for o in outcomes:
        attrs = o["synth_attributes"]["latent_traits"]

        # Alta capability + alta trust deveria ter alto success
        if attrs["capability_mean"] > 0.7 and attrs["trust_mean"] > 0.6:
            if o["success_rate"] < 0.4:
                o["unexpected_reason"] = "high_potential_low_success"
                unexpected.append(o)

        # Baixa capability deveria ter baixo success
        if attrs["capability_mean"] < 0.3:
            if o["success_rate"] > 0.7:
                o["unexpected_reason"] = "low_potential_high_success"
                unexpected.append(o)

    return unexpected
```

**Endpoint**:
```
GET /simulation/simulations/{id}/extreme-cases
    ?type=failures|successes|unstable|unexpected|all
    &limit=10
    &include_interview_suggestions=true
```

**Critérios de aceite**:
- [ ] Identifica top N piores e melhores
- [ ] Identifica casos inesperados (outliers comportamentais)
- [ ] Inclui perfil resumido do synth
- [ ] Sugere perguntas para entrevista
- [ ] Prioriza por relevância para pesquisa

---

### 4.2 Isolation Forest (Outliers)

**O que é**: Detecta synths anômalos cujo comportamento é estatisticamente incomum.

**Input necessário**:
```python
# Features: atributos + outcomes
X = [
    [capability, trust, friction_tol, exploration, success_rate, failed_rate],
    ...
]
```

**Output esperado**:
```python
class OutlierSynth(BaseModel):
    synth_id: str
    anomaly_score: float  # -1 a 0 (mais negativo = mais anômalo)
    is_outlier: bool
    outlier_type: Literal[
        "unexpected_failure",   # deveria ter sucesso mas falhou
        "unexpected_success",   # deveria falhar mas teve sucesso
        "atypical_profile",     # combinação rara de atributos
        "unstable_behavior"     # alta variância
    ]
    # Comparação com "normais"
    deviation_from_mean: dict[str, float]  # quanto cada feature desvia
    nearest_normal: str  # synth_id do synth "normal" mais próximo

class OutlierResult(BaseModel):
    simulation_id: str
    method: str  # "isolation_forest"
    contamination: float  # % esperado de outliers
    # Resultados
    outliers: list[OutlierSynth]
    total_outliers: int
    # Todos os scores (para visualização)
    all_scores: dict[str, float]  # synth_id → anomaly_score
```

**Lógica de implementação**:
```python
from sklearn.ensemble import IsolationForest

class OutlierService:
    def detect_outliers(
        self,
        outcomes: list[dict],
        contamination: float = 0.1,
        include_outcomes: bool = True
    ) -> OutlierResult:
        # 1. Preparar features
        features = ["capability_mean", "trust_mean",
                   "friction_tolerance_mean", "exploration_prob"]
        if include_outcomes:
            features += ["success_rate", "failed_rate"]

        X, synth_ids = self._extract_features(outcomes, features)

        # 2. Fit Isolation Forest
        iso = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        predictions = iso.fit_predict(X)  # 1 = normal, -1 = outlier
        scores = iso.score_samples(X)     # quanto menor, mais anômalo

        # 3. Classificar tipo de outlier
        outliers = []
        for i, (pred, score) in enumerate(zip(predictions, scores)):
            if pred == -1:
                synth_id = synth_ids[i]
                outlier_type = self._classify_outlier_type(
                    outcomes[i],
                    X[i],
                    np.mean(X, axis=0)
                )
                outliers.append(OutlierSynth(
                    synth_id=synth_id,
                    anomaly_score=float(score),
                    is_outlier=True,
                    outlier_type=outlier_type,
                    ...
                ))

        return OutlierResult(
            simulation_id=simulation_id,
            method="isolation_forest",
            contamination=contamination,
            outliers=outliers,
            total_outliers=len(outliers),
            all_scores={sid: float(s) for sid, s in zip(synth_ids, scores)}
        )

    def _classify_outlier_type(
        self,
        outcome: dict,
        features: np.ndarray,
        mean_features: np.ndarray
    ) -> str:
        """Classifica o tipo de anomalia."""
        attrs = outcome["synth_attributes"]["latent_traits"]
        success = outcome["success_rate"]

        # Calcular "expected success" baseado em atributos
        expected = 0.3 * attrs["capability_mean"] + 0.3 * attrs["trust_mean"] + 0.4 * 0.5

        if success < expected - 0.3:
            return "unexpected_failure"
        elif success > expected + 0.3:
            return "unexpected_success"
        else:
            return "atypical_profile"
```

**Endpoint**:
```
GET /simulation/simulations/{id}/outliers
    ?contamination=0.1
    &include_outcomes=true
    &type=all|unexpected_failure|unexpected_success
```

**Critérios de aceite**:
- [ ] Implementa Isolation Forest
- [ ] Contamination é configurável
- [ ] Classifica tipo de anomalia
- [ ] Retorna scores para todos os synths (para visualização)
- [ ] Identifica synth "normal" mais próximo (para comparação)

---

## FASE 5: Explicação Profunda

### 5.1 SHAP Values

**O que é**: Explica contribuição de cada feature para o outcome de um synth específico.

**Input necessário**:
```python
# Precisa treinar modelo preditivo primeiro
X = features de todos os synths
y = success_rate de todos os synths
```

**Output esperado**:
```python
class ShapContribution(BaseModel):
    feature: str
    value: float       # valor do feature para este synth
    shap_value: float  # contribuição para predição
    direction: Literal["positive", "negative"]

class ShapExplanation(BaseModel):
    synth_id: str | None  # None = summary de todos
    # Base
    base_value: float     # predição média
    predicted_value: float  # predição para este synth
    actual_value: float     # valor real
    # Contribuições
    contributions: list[ShapContribution]
    # Texto explicativo
    explanation_text: str  # "Trust baixa (-0.15) e complexity alta (-0.12) explicam..."

class ShapSummary(BaseModel):
    simulation_id: str
    # Feature importance global
    feature_importance: dict[str, float]
    # Top positive/negative contributors
    top_positive: list[str]
    top_negative: list[str]
```

**Lógica de implementação**:
```python
import shap
from sklearn.ensemble import GradientBoostingRegressor

class ExplainabilityService:
    def __init__(self, db: DatabaseManager):
        self.db = db
        self._model = None
        self._explainer = None

    def _train_model(self, outcomes: list[dict]) -> None:
        """Treina modelo para usar com SHAP."""
        X, y, feature_names = self._prepare_data(outcomes)

        self._model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=4,
            random_state=42
        )
        self._model.fit(X, y)
        self._feature_names = feature_names

        # Criar explainer
        self._explainer = shap.TreeExplainer(self._model)
        self._X = X

    def explain_synth(
        self,
        simulation_id: str,
        synth_id: str
    ) -> ShapExplanation:
        """Explica predição para um synth específico."""
        outcomes = self._load_outcomes(simulation_id)

        if self._model is None:
            self._train_model(outcomes)

        # Encontrar synth
        synth_idx = self._find_synth_index(synth_id, outcomes)
        synth_features = self._X[synth_idx:synth_idx+1]

        # Calcular SHAP values
        shap_values = self._explainer.shap_values(synth_features)

        # Construir explicação
        contributions = []
        for i, (fname, fval, sval) in enumerate(zip(
            self._feature_names,
            synth_features[0],
            shap_values[0]
        )):
            contributions.append(ShapContribution(
                feature=fname,
                value=float(fval),
                shap_value=float(sval),
                direction="positive" if sval > 0 else "negative"
            ))

        # Ordenar por magnitude
        contributions.sort(key=lambda x: abs(x.shap_value), reverse=True)

        return ShapExplanation(
            synth_id=synth_id,
            base_value=float(self._explainer.expected_value),
            predicted_value=float(self._model.predict(synth_features)[0]),
            actual_value=outcomes[synth_idx]["success_rate"],
            contributions=contributions,
            explanation_text=self._generate_explanation_text(contributions)
        )

    def _generate_explanation_text(self, contributions: list[ShapContribution]) -> str:
        """Gera texto explicativo."""
        top_3 = contributions[:3]
        parts = []
        for c in top_3:
            direction = "aumentou" if c.direction == "positive" else "reduziu"
            parts.append(f"{c.feature} ({c.value:.2f}) {direction} em {abs(c.shap_value):.2f}")

        return " | ".join(parts)
```

**Endpoint**:
```
GET /simulation/simulations/{id}/shap
    ?synth_id=xxx  # se omitido, retorna summary

GET /simulation/simulations/{id}/shap/summary
    # Feature importance global
```

**Critérios de aceite**:
- [ ] Treina modelo internamente (GradientBoosting ou similar)
- [ ] Calcula SHAP values para synth específico
- [ ] Gera summary de feature importance
- [ ] Produz texto explicativo legível
- [ ] Cacheia modelo treinado

---

### 5.2 Partial Dependence Plots (PDP)

**O que é**: Mostra efeito marginal de uma feature na predição, mantendo outras constantes.

**Input necessário**:
```python
# Modelo treinado (mesmo do SHAP)
# Feature para analisar
feature = "capability_mean"
```

**Output esperado**:
```python
class PDPPoint(BaseModel):
    feature_value: float
    predicted_outcome: float
    ci_lower: float | None  # intervalo de confiança
    ci_upper: float | None

class PDPResult(BaseModel):
    simulation_id: str
    feature: str
    # Pontos para plotar
    points: list[PDPPoint]
    # Metadados
    feature_range: tuple[float, float]
    baseline_prediction: float
    # Interpretação
    effect_type: Literal["monotonic_positive", "monotonic_negative", "non_linear", "flat"]
    effect_strength: float  # 0-1

class PDPComparison(BaseModel):
    """Compara PDP de múltiplas features."""
    simulation_id: str
    features: list[str]
    pdps: dict[str, PDPResult]
    # Ranking por efeito
    effect_ranking: list[str]
```

**Lógica de implementação**:
```python
from sklearn.inspection import partial_dependence

class ExplainabilityService:
    def calculate_pdp(
        self,
        simulation_id: str,
        feature: str,
        grid_resolution: int = 20
    ) -> PDPResult:
        outcomes = self._load_outcomes(simulation_id)

        if self._model is None:
            self._train_model(outcomes)

        # Encontrar índice da feature
        feature_idx = self._feature_names.index(feature)

        # Calcular PDP
        pdp_results = partial_dependence(
            self._model,
            self._X,
            features=[feature_idx],
            grid_resolution=grid_resolution,
            kind="average"
        )

        # Construir pontos
        points = []
        for fval, pred in zip(
            pdp_results["grid_values"][0],
            pdp_results["average"][0]
        ):
            points.append(PDPPoint(
                feature_value=float(fval),
                predicted_outcome=float(pred),
                ci_lower=None,
                ci_upper=None
            ))

        # Classificar tipo de efeito
        effect_type = self._classify_effect(points)

        return PDPResult(
            simulation_id=simulation_id,
            feature=feature,
            points=points,
            feature_range=(float(self._X[:, feature_idx].min()),
                          float(self._X[:, feature_idx].max())),
            baseline_prediction=float(np.mean(self._model.predict(self._X))),
            effect_type=effect_type,
            effect_strength=self._calculate_effect_strength(points)
        )

    def _classify_effect(self, points: list[PDPPoint]) -> str:
        """Classifica o tipo de efeito observado."""
        values = [p.predicted_outcome for p in points]
        diffs = np.diff(values)

        if all(d >= 0 for d in diffs):
            return "monotonic_positive"
        elif all(d <= 0 for d in diffs):
            return "monotonic_negative"
        elif max(values) - min(values) < 0.05:
            return "flat"
        else:
            return "non_linear"
```

**Endpoint**:
```
GET /simulation/simulations/{id}/pdp
    ?feature=capability_mean
    &grid_resolution=20

GET /simulation/simulations/{id}/pdp/comparison
    ?features=capability_mean,trust_mean,friction_tolerance_mean
```

**Critérios de aceite**:
- [ ] Calcula PDP para qualquer feature
- [ ] Classifica tipo de efeito (monotônico, não-linear, flat)
- [ ] Permite comparar múltiplas features
- [ ] Retorna dados para plotar curva

---

## FASE 6: Insights LLM

### 6.1 Caption Generator

**O que é**: Gera legenda curta (≤20 tokens) para qualquer gráfico.

**Input necessário**:
```python
chart_type = "try_vs_success"
chart_data = {
    "quadrant_counts": {
        "low_value": 50,
        "usability_issue": 210,
        "discovery_issue": 40,
        "ok": 200
    },
    "total_synths": 500
}
```

**Output esperado**:
```python
class ChartCaption(BaseModel):
    chart_type: str
    caption: str  # ≤20 tokens
    key_metric: str
    key_value: float
    confidence: float  # 0-1, confiança do LLM
```

**Prompt template**:
```python
CAPTION_PROMPTS = {
    "try_vs_success": """
Dados do gráfico Try vs Success:
- Baixo valor: {low_value} synths ({low_value_pct}%)
- Problema usabilidade: {usability_issue} synths ({usability_pct}%)
- Problema descoberta: {discovery_issue} synths ({discovery_pct}%)
- OK: {ok} synths ({ok_pct}%)

Gere uma legenda de no máximo 20 tokens focando no insight mais importante.
Seja factual, use números.

Legenda:""",

    "failure_heatmap": """
Heatmap de falha: {x_axis} × {y_axis}
Célula mais crítica: {worst_cell} com {worst_rate}% falha
Célula mais segura: {best_cell} com {best_rate}% falha

Gere uma legenda de no máximo 20 tokens identificando a zona de risco.

Legenda:""",

    # ... outros tipos
}
```

**Endpoint**:
```
GET /simulation/simulations/{id}/charts/{chart_type}/caption
```

**Critérios de aceite**:
- [ ] Gera caption ≤20 tokens
- [ ] Caption é factual e usa números
- [ ] Foca no insight mais importante
- [ ] Funciona para todos os tipos de gráfico

---

### 6.2 Insight Generator

**O que é**: Gera parágrafo explicativo (≤200 tokens) com evidências.

**Input necessário**:
```python
chart_type = "try_vs_success"
chart_data = {...}  # dados completos
caption = "42% dos synths têm problema de usabilidade"  # do Layer 1
```

**Output esperado**:
```python
class ChartInsight(BaseModel):
    chart_type: str
    caption: str
    explanation: str  # ≤200 tokens
    evidence: list[str]
    recommendation: str | None
    confidence: float
```

**Prompt template**:
```python
INSIGHT_PROMPT = """
Você é um assistente de UX Research usando dados para gerar um resumo executivo para um Product Manager

Gráfico: {chart_type}
Legenda: {caption}

Dados completos:
{chart_data_formatted}

Regras:
1. Máximo 200 tokens
2. Inclua 2-3 evidências numéricas
3. Explique o "porquê" se possível
4. Sugira uma ação se relevante
5. Use linguagem simples

Explicação:"""
```

**Endpoint**:
```
GET /simulation/simulations/{id}/charts/{chart_type}/insight

GET /simulation/simulations/{id}/insights
    # Todos os gráficos de uma vez
```

**Critérios de aceite**:
- [ ] Gera explicação ≤100 tokens
- [ ] Inclui evidências numéricas
- [ ] Sugere ação quando relevante
- [ ] Cacheia para evitar re-chamadas ao LLM

---

## Resumo de Entidades Novas

```python
# domain/entities/

# Clustering
cluster_result.py
├── ClusterProfile
├── KMeansResult
└── HierarchicalResult

# Outliers
outlier_result.py
├── OutlierSynth
└── OutlierResult

# Explicabilidade
explainability_result.py
├── ShapContribution
├── ShapExplanation
├── PDPPoint
└── PDPResult

# Dados de Gráficos
chart_data.py
├── TryVsSuccessChart
├── FailureHeatmapChart
├── BoxPlotChart
├── ScatterCorrelationChart
├── TornadoChart
├── RadarChart
├── DendrogramChart
└── ExtremeCasesTable

# Insights LLM
chart_insight.py
├── ChartCaption
└── ChartInsight
```

---

## Resumo de Serviços Novos

```python
# services/simulation/

clustering.py
├── ClusteringService
│   ├── cluster_kmeans()
│   ├── cluster_hierarchical()
│   └── cut_dendrogram()

outliers.py
├── OutlierService
│   └── detect_outliers()

explainability.py
├── ExplainabilityService
│   ├── explain_synth()  # SHAP
│   ├── explain_summary()
│   └── calculate_pdp()

chart_data.py
├── ChartDataService
│   ├── get_try_vs_success()
│   ├── get_failure_heatmap()
│   ├── get_box_plot()
│   ├── get_scatter()
│   ├── get_tornado()
│   ├── get_radar()
│   ├── get_dendrogram()
│   └── get_extreme_cases()

insight_generator.py
├── InsightGenerator
│   ├── generate_caption()
│   └── generate_insight()
```

