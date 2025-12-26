# Data Model: Sistema de Análise para UX Research

**Feature Branch**: `017-analysis-ux-research`
**Created**: 2025-12-26

---

## Visão Geral

Este documento define todas as entidades Pydantic que serão criadas para suportar as funcionalidades de análise. As entidades estão organizadas por domínio funcional.

---

## 1. Chart Data Entities (`domain/entities/chart_data.py`)

### 1.1 Try vs Success Chart

```python
from pydantic import BaseModel
from typing import Literal

class TryVsSuccessPoint(BaseModel):
    """Ponto individual no gráfico Try vs Success."""
    synth_id: str
    attempt_rate: float      # X: 1 - did_not_try_rate
    success_rate: float      # Y: success_rate
    quadrant: Literal["low_value", "usability_issue", "discovery_issue", "ok"]

class TryVsSuccessChart(BaseModel):
    """Dados completos para o gráfico Try vs Success."""
    simulation_id: str
    points: list[TryVsSuccessPoint]
    quadrant_counts: dict[str, int]  # {"low_value": 50, "usability_issue": 210, ...}
    quadrant_thresholds: dict[str, float]  # {"x": 0.5, "y": 0.5}
    total_synths: int
```

### 1.2 Outcome Distribution Chart

```python
class SynthDistribution(BaseModel):
    """Distribuição de outcomes para um synth."""
    synth_id: str
    did_not_try_rate: float
    failed_rate: float
    success_rate: float
    sort_key: float  # valor usado para ordenação

class OutcomeDistributionChart(BaseModel):
    """Dados para o gráfico de distribuição de outcomes."""
    simulation_id: str
    distributions: list[SynthDistribution]
    summary: dict[str, float]  # {"avg_success": 0.42, "avg_failed": 0.35, ...}
    worst_performers: list[str]  # top 10 synth_ids com menor success
    best_performers: list[str]   # top 10 synth_ids com maior success
    total_synths: int
```

### 1.3 Sankey Chart

```python
class SankeyNode(BaseModel):
    """Nó do diagrama Sankey."""
    id: str           # "all", "attempted", "not_attempted", "success", "failed"
    label: str        # "Todos (500)", "Tentaram (375)", etc.
    value: int        # contagem absoluta

class SankeyLink(BaseModel):
    """Link entre nós do Sankey."""
    source: str       # id do nó origem
    target: str       # id do nó destino
    value: int        # contagem que flui
    percentage: float # % do total

class SankeyChart(BaseModel):
    """Dados para o diagrama Sankey."""
    simulation_id: str
    total_synths: int
    nodes: list[SankeyNode]
    links: list[SankeyLink]
```

### 1.4 Failure Heatmap Chart

```python
class HeatmapCell(BaseModel):
    """Célula do heatmap."""
    x_bin: str           # "0.0-0.2", "0.2-0.4", etc.
    y_bin: str
    x_range: tuple[float, float]  # (0.0, 0.2)
    y_range: tuple[float, float]
    metric_value: float  # média de failed_rate (ou outra métrica) nesta célula
    synth_count: int
    synth_ids: list[str]

class FailureHeatmapChart(BaseModel):
    """Dados para o heatmap de falhas."""
    simulation_id: str
    x_axis: str          # "capability_mean"
    y_axis: str          # "trust_mean"
    metric: str          # "failed_rate" | "success_rate" | "did_not_try_rate"
    bins: int
    cells: list[HeatmapCell]
    max_value: float
    min_value: float
    critical_cells: list[HeatmapCell]  # células com valor > threshold
    critical_threshold: float
```

### 1.5 Box Plot Chart

```python
class BoxPlotStats(BaseModel):
    """Estatísticas para um box plot."""
    min: float
    q1: float      # 25th percentile
    median: float  # 50th percentile
    q3: float      # 75th percentile
    max: float
    mean: float
    outliers: list[float]

class RegionBoxPlot(BaseModel):
    """Box plot para uma região."""
    region_id: str
    region_label: str  # rule_text simplificado
    synth_count: int
    stats: BoxPlotStats  # stats para a métrica selecionada

class BoxPlotChart(BaseModel):
    """Dados para o gráfico de box plot por região."""
    simulation_id: str
    metric: str  # "success_rate" | "failed_rate" | "did_not_try_rate"
    regions: list[RegionBoxPlot]
    baseline_stats: BoxPlotStats  # toda a população
```

### 1.6 Scatter Correlation Chart

```python
class CorrelationPoint(BaseModel):
    """Ponto no scatter de correlação."""
    synth_id: str
    x_value: float
    y_value: float

class CorrelationStats(BaseModel):
    """Estatísticas de correlação."""
    pearson_r: float
    p_value: float
    r_squared: float
    is_significant: bool  # p < 0.05
    trend_slope: float
    trend_intercept: float

class TrendlinePoint(BaseModel):
    """Ponto da linha de tendência."""
    x: float
    y: float

class ScatterCorrelationChart(BaseModel):
    """Dados para o scatter de correlação."""
    simulation_id: str
    x_axis: str
    y_axis: str
    points: list[CorrelationPoint]
    correlation: CorrelationStats
    trendline: list[TrendlinePoint]
```

### 1.7 Tornado Chart

```python
class TornadoBar(BaseModel):
    """Barra do diagrama tornado."""
    dimension: str
    rank: int
    sensitivity_index: float
    negative_impact: float  # impacto quando reduz a dimensão
    positive_impact: float  # impacto quando aumenta a dimensão
    baseline_value: float
    label_negative: str  # "-10% → +5% success"
    label_positive: str  # "+10% → -8% success"

class TornadoChart(BaseModel):
    """Dados para o diagrama tornado."""
    simulation_id: str
    baseline_success: float
    bars: list[TornadoBar]  # ordenados por sensitivity_index desc
    deltas_used: list[float]
    most_sensitive: str  # nome da dimensão mais sensível
```

---

## 2. Cluster Result Entities (`domain/entities/cluster_result.py`)

### 2.1 Cluster Profile

```python
class ClusterProfile(BaseModel):
    """Perfil de um cluster."""
    cluster_id: int
    size: int
    percentage: float  # % do total
    centroid: dict[str, float]  # média de cada feature
    avg_success_rate: float
    avg_failed_rate: float
    avg_did_not_try_rate: float
    high_traits: list[str]  # traits acima da média geral
    low_traits: list[str]   # traits abaixo da média geral
    suggested_label: str    # ex: "Power Users", "Strugglers"
    synth_ids: list[str]    # synths neste cluster
```

### 2.2 K-Means Result

```python
class ElbowDataPoint(BaseModel):
    """Ponto para o gráfico Elbow Method."""
    k: int
    inertia: float
    silhouette: float

class KMeansResult(BaseModel):
    """Resultado do clustering K-Means."""
    simulation_id: str
    n_clusters: int
    method: Literal["kmeans"] = "kmeans"
    features_used: list[str]
    silhouette_score: float
    inertia: float
    clusters: list[ClusterProfile]
    synth_assignments: dict[str, int]  # synth_id → cluster_id
    elbow_data: list[ElbowDataPoint]
    created_at: str  # ISO timestamp
```

### 2.3 Hierarchical Result

```python
class DendrogramNode(BaseModel):
    """Nó do dendrograma."""
    id: int
    synth_id: str | None  # se folha
    left_child: int | None  # se nó interno
    right_child: int | None
    distance: float
    count: int  # número de folhas abaixo

class SuggestedCut(BaseModel):
    """Sugestão de corte do dendrograma."""
    n_clusters: int
    distance: float
    silhouette_estimate: float

class HierarchicalResult(BaseModel):
    """Resultado do clustering hierárquico."""
    simulation_id: str
    method: Literal["hierarchical"] = "hierarchical"
    linkage_method: str  # "ward", "complete", "average", "single"
    features_used: list[str]
    nodes: list[DendrogramNode]
    linkage_matrix: list[list[float]]  # formato scipy
    suggested_cuts: list[SuggestedCut]
    cluster_assignments: dict[str, int] | None  # se já cortado
    n_clusters: int | None  # se já cortado
    created_at: str
```

### 2.4 Radar Chart

```python
class RadarAxis(BaseModel):
    """Eixo do radar chart."""
    name: str           # "capability_mean"
    label: str          # "Capability"
    value: float        # valor real (0.72)
    normalized: float   # valor normalizado 0-1

class ClusterRadar(BaseModel):
    """Radar para um cluster."""
    cluster_id: int
    label: str          # "Power Users"
    color: str          # "#FF6B6B"
    axes: list[RadarAxis]
    success_rate: float

class RadarChart(BaseModel):
    """Dados para radar chart de clusters."""
    simulation_id: str
    clusters: list[ClusterRadar]
    axis_labels: list[str]
    baseline: list[float]  # média geral para cada eixo
```

### 2.5 Dendrogram Chart

```python
class DendrogramBranch(BaseModel):
    """Branch para renderização."""
    x_start: float
    x_end: float
    y_start: float
    y_end: float
    is_leaf: bool
    synth_id: str | None
    cluster_id: int | None
    count: int

class DendrogramChart(BaseModel):
    """Dados para visualização do dendrograma."""
    simulation_id: str
    branches: list[DendrogramBranch]
    leaves: list[dict]  # [{x: 0, synth_id: "...", cluster_id: 1}, ...]
    cut_lines: list[dict]  # [{y: 2.5, n_clusters: 4}, ...]
    width: float
    height: float
```

---

## 3. Outlier Result Entities (`domain/entities/outlier_result.py`)

### 3.1 Extreme Synth

```python
class ExtremeSynth(BaseModel):
    """Synth extremo para tabela de casos especiais."""
    synth_id: str
    rank: int
    extreme_type: Literal["worst_failure", "best_success", "most_unstable", "unexpected"]
    success_rate: float
    failed_rate: float
    did_not_try_rate: float
    profile_summary: str  # "Idoso, 67 anos, alta capability"
    key_attributes: dict[str, float]
    reason: str  # "Alta capability mas 85% falha"
    interview_priority: int  # 1-10
    interview_questions: list[str]

class ExtremeCasesTable(BaseModel):
    """Tabela de casos extremos."""
    simulation_id: str
    worst_failures: list[ExtremeSynth]
    best_successes: list[ExtremeSynth]
    most_unstable: list[ExtremeSynth]
    unexpected: list[ExtremeSynth]
    total_analyzed: int
```

### 3.2 Outlier Synth

```python
class OutlierSynth(BaseModel):
    """Synth detectado como outlier."""
    synth_id: str
    anomaly_score: float  # mais negativo = mais anômalo
    is_outlier: bool
    outlier_type: Literal["unexpected_failure", "unexpected_success", "atypical_profile", "unstable_behavior"]
    deviation_from_mean: dict[str, float]  # quanto cada feature desvia
    nearest_normal: str | None  # synth_id do mais próximo "normal"

class OutlierResult(BaseModel):
    """Resultado da detecção de outliers."""
    simulation_id: str
    method: Literal["isolation_forest"]
    contamination: float
    outliers: list[OutlierSynth]
    total_outliers: int
    all_scores: dict[str, float]  # synth_id → anomaly_score
```

---

## 4. Explainability Entities (`domain/entities/explainability.py`)

### 4.1 SHAP Explanation

```python
class ShapContribution(BaseModel):
    """Contribuição de uma feature."""
    feature: str
    value: float       # valor da feature para este synth
    shap_value: float  # contribuição para predição
    direction: Literal["positive", "negative"]

class ShapExplanation(BaseModel):
    """Explicação SHAP para um synth."""
    simulation_id: str
    synth_id: str
    base_value: float     # predição média
    predicted_value: float
    actual_value: float
    contributions: list[ShapContribution]  # ordenadas por magnitude
    explanation_text: str

class ShapSummary(BaseModel):
    """Summary de feature importance global."""
    simulation_id: str
    feature_importance: dict[str, float]  # feature → importância média
    top_positive: list[str]  # features que mais aumentam success
    top_negative: list[str]  # features que mais reduzem success
    model_r2: float  # R² do modelo treinado
```

### 4.2 Partial Dependence Plot

```python
class PDPPoint(BaseModel):
    """Ponto do PDP."""
    feature_value: float
    predicted_outcome: float
    ci_lower: float | None
    ci_upper: float | None

class PDPResult(BaseModel):
    """Resultado do Partial Dependence Plot."""
    simulation_id: str
    feature: str
    points: list[PDPPoint]
    feature_range: tuple[float, float]
    baseline_prediction: float
    effect_type: Literal["monotonic_positive", "monotonic_negative", "non_linear", "flat"]
    effect_strength: float  # 0-1

class PDPComparison(BaseModel):
    """Comparação de PDP entre features."""
    simulation_id: str
    features: list[str]
    pdps: dict[str, PDPResult]
    effect_ranking: list[str]  # features ordenadas por efeito
```

---

## 5. Chart Insight Entities (`domain/entities/chart_insight.py`)

### 5.1 Chart Caption

```python
class ChartCaption(BaseModel):
    """Legenda curta gerada por LLM."""
    simulation_id: str
    chart_type: str
    caption: str  # ≤20 tokens
    key_metric: str
    key_value: float
    confidence: float  # 0-1
```

### 5.2 Chart Insight

```python
class ChartInsight(BaseModel):
    """Insight completo gerado por LLM."""
    simulation_id: str
    chart_type: str
    caption: str
    explanation: str  # ≤200 tokens
    evidence: list[str]
    recommendation: str | None
    confidence: float
```

### 5.3 Simulation Insights

```python
class SimulationInsights(BaseModel):
    """Todos os insights de uma simulação."""
    simulation_id: str
    insights: dict[str, ChartInsight]  # chart_type → insight
    executive_summary: str | None
    generated_at: str  # ISO timestamp
```

---

## 6. API Request/Response Schemas (`api/schemas/analysis.py`)

### 6.1 Clustering Requests

```python
class ClusterRequest(BaseModel):
    """Request para criar clustering."""
    method: Literal["kmeans", "hierarchical"] = "kmeans"
    n_clusters: int = 4
    features: list[str] | None = None
    include_outcomes: bool = False
    linkage: str = "ward"  # para hierarchical

class CutDendrogramRequest(BaseModel):
    """Request para cortar dendrograma."""
    n_clusters: int
```

### 6.2 Query Parameters

```python
# Try vs Success
class TryVsSuccessParams(BaseModel):
    x_threshold: float = 0.5
    y_threshold: float = 0.5

# Distribution
class DistributionParams(BaseModel):
    mode: Literal["by_synth", "by_percentile", "by_cluster"] = "by_synth"
    sort_by: Literal["success_rate", "failed_rate", "did_not_try_rate"] = "success_rate"
    order: Literal["asc", "desc"] = "desc"
    limit: int = 50

# Heatmap
class HeatmapParams(BaseModel):
    x_axis: str = "capability_mean"
    y_axis: str = "trust_mean"
    bins: int = 5
    metric: Literal["failed_rate", "success_rate", "did_not_try_rate"] = "failed_rate"

# Box Plot
class BoxPlotParams(BaseModel):
    metric: Literal["success_rate", "failed_rate", "did_not_try_rate"] = "success_rate"
    include_baseline: bool = True

# Scatter
class ScatterParams(BaseModel):
    x_axis: str = "trust_mean"
    y_axis: str = "success_rate"
    show_trendline: bool = True

# Extreme Cases
class ExtremeCasesParams(BaseModel):
    type: Literal["all", "failures", "successes", "unstable", "unexpected"] = "all"
    limit: int = 10
    include_interview_suggestions: bool = True

# Outliers
class OutliersParams(BaseModel):
    contamination: float = 0.1
    include_outcomes: bool = True
    type: Literal["all", "unexpected_failure", "unexpected_success", "atypical_profile"] = "all"

# SHAP
class ShapParams(BaseModel):
    synth_id: str | None = None  # None = summary

# PDP
class PDPParams(BaseModel):
    feature: str
    grid_resolution: int = 20

class PDPComparisonParams(BaseModel):
    features: str  # comma-separated

# Dendrogram
class DendrogramParams(BaseModel):
    max_depth: int = 5
    truncate_mode: Literal["level", "lastp", "none"] = "level"
    color_threshold: float | None = None
```

---

## 7. Relacionamentos

```
SimulationRun (existente)
    │
    ├── SynthOutcome (existente) ──► usado por todos os services
    │
    ├── RegionAnalysis (existente) ──► BoxPlotChart
    │
    ├── SensitivityResult (existente) ──► TornadoChart
    │
    └── [Novos resultados em memória/cache]
        ├── KMeansResult
        ├── HierarchicalResult
        ├── OutlierResult
        ├── ShapExplanation (cacheado por synth)
        └── ChartInsight (cacheado por chart_type)
```

**Nota**: Não criamos novas tabelas no banco. Resultados de clustering, SHAP e insights são cacheados em memória por sessão/simulação.
