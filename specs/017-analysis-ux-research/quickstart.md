# Quickstart: Sistema de Análise para UX Research

**Feature Branch**: `017-analysis-ux-research`
**Created**: 2025-12-26

---

## Pré-requisitos

1. Simulação executada e finalizada (`status: completed`)
2. Synth outcomes populados (`/simulation/simulations/{id}/run`)
3. Para Tornado Diagram: sensitivity analysis executada
4. Para Box Plot por Região: region analysis existente

---

## Jornada Típica de Análise

### Fase 1: Visão Geral (5 min)

**Objetivo**: Entender "o que aconteceu" na simulação.

#### 1.1 Try vs Success

```bash
# Ver distribuição de synths nos 4 quadrantes
curl "http://localhost:8000/simulation/simulations/{id}/charts/try-vs-success"

# Com thresholds customizados
curl "http://localhost:8000/simulation/simulations/{id}/charts/try-vs-success?x_threshold=0.6&y_threshold=0.4"
```

**Resposta**:
```json
{
  "simulation_id": "sim_001",
  "points": [
    {"synth_id": "synth_001", "attempt_rate": 0.75, "success_rate": 0.40, "quadrant": "ok"},
    {"synth_id": "synth_002", "attempt_rate": 0.80, "success_rate": 0.25, "quadrant": "usability_issue"}
  ],
  "quadrant_counts": {
    "low_value": 50,
    "usability_issue": 210,
    "discovery_issue": 40,
    "ok": 200
  },
  "quadrant_thresholds": {"x": 0.5, "y": 0.5},
  "total_synths": 500
}
```

**Interpretação**:
- `usability_issue` alto → usuários tentam mas falham → melhorar usabilidade
- `discovery_issue` alto → usuários não descobrem → melhorar onboarding/marketing

#### 1.2 Sankey Diagram

```bash
curl "http://localhost:8000/simulation/simulations/{id}/charts/sankey"
```

**Resposta**:
```json
{
  "simulation_id": "sim_001",
  "total_synths": 500,
  "nodes": [
    {"id": "all", "label": "Todos (500)", "value": 500},
    {"id": "attempted", "label": "Tentaram (375)", "value": 375},
    {"id": "not_attempted", "label": "Não tentaram (125)", "value": 125},
    {"id": "success", "label": "Sucesso (200)", "value": 200},
    {"id": "failed", "label": "Falharam (175)", "value": 175}
  ],
  "links": [
    {"source": "all", "target": "attempted", "value": 375, "percentage": 75.0},
    {"source": "all", "target": "not_attempted", "value": 125, "percentage": 25.0},
    {"source": "attempted", "target": "success", "value": 200, "percentage": 53.3},
    {"source": "attempted", "target": "failed", "value": 175, "percentage": 46.7}
  ]
}
```

#### 1.3 Outcome Distribution

```bash
# Top 20 piores performers
curl "http://localhost:8000/simulation/simulations/{id}/charts/distribution?sort_by=success_rate&order=asc&limit=20"

# Agregado por percentil
curl "http://localhost:8000/simulation/simulations/{id}/charts/distribution?mode=by_percentile"
```

---

### Fase 2: Localização (15 min)

**Objetivo**: Identificar "onde exatamente a experiência quebra".

#### 2.1 Failure Heatmap

```bash
# Heatmap de capability x trust
curl "http://localhost:8000/simulation/simulations/{id}/charts/failure-heatmap?x_axis=capability_mean&y_axis=trust_mean"

# Com 7 bins e métrica de success
curl "http://localhost:8000/simulation/simulations/{id}/charts/failure-heatmap?x_axis=capability_mean&y_axis=trust_mean&bins=7&metric=success_rate"
```

**Resposta**:
```json
{
  "simulation_id": "sim_001",
  "x_axis": "capability_mean",
  "y_axis": "trust_mean",
  "metric": "failed_rate",
  "bins": 5,
  "cells": [
    {
      "x_bin": "0.0-0.2",
      "y_bin": "0.0-0.2",
      "x_range": [0.0, 0.2],
      "y_range": [0.0, 0.2],
      "metric_value": 0.85,
      "synth_count": 45,
      "synth_ids": ["synth_001", "synth_005", ...]
    }
  ],
  "critical_cells": [
    {"x_bin": "0.0-0.2", "y_bin": "0.0-0.2", "metric_value": 0.85}
  ],
  "critical_threshold": 0.7
}
```

**Interpretação**: Células com alta falha indicam combinações de atributos problemáticas.

#### 2.2 Scatter Correlation

```bash
# Trust vs Success com linha de tendência
curl "http://localhost:8000/simulation/simulations/{id}/charts/scatter?x_axis=trust_mean&y_axis=success_rate&show_trendline=true"
```

**Resposta**:
```json
{
  "simulation_id": "sim_001",
  "x_axis": "trust_mean",
  "y_axis": "success_rate",
  "points": [...],
  "correlation": {
    "pearson_r": 0.72,
    "p_value": 0.0001,
    "r_squared": 0.52,
    "is_significant": true,
    "trend_slope": 0.65,
    "trend_intercept": 0.12
  },
  "trendline": [{"x": 0.0, "y": 0.12}, {"x": 1.0, "y": 0.77}]
}
```

#### 2.3 Tornado Diagram

```bash
# Requer sensitivity analysis prévia
curl "http://localhost:8000/simulation/simulations/{id}/charts/tornado"
```

---

### Fase 3: Segmentação (30 min)

**Objetivo**: Identificar "quem são esses usuários" via clustering.

#### 3.1 Criar Clustering K-Means

```bash
# Clustering com 4 grupos
curl -X POST "http://localhost:8000/simulation/simulations/{id}/clusters" \
  -H "Content-Type: application/json" \
  -d '{"method": "kmeans", "n_clusters": 4}'

# Com features customizadas
curl -X POST "http://localhost:8000/simulation/simulations/{id}/clusters" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "kmeans",
    "n_clusters": 4,
    "features": ["capability_mean", "trust_mean", "friction_tolerance_mean"],
    "include_outcomes": true
  }'
```

**Resposta**:
```json
{
  "simulation_id": "sim_001",
  "n_clusters": 4,
  "method": "kmeans",
  "silhouette_score": 0.42,
  "inertia": 1234.5,
  "clusters": [
    {
      "cluster_id": 0,
      "size": 120,
      "percentage": 24.0,
      "centroid": {"capability_mean": 0.72, "trust_mean": 0.68, ...},
      "avg_success_rate": 0.75,
      "high_traits": ["capability_mean", "trust_mean"],
      "low_traits": [],
      "suggested_label": "Power Users"
    },
    {
      "cluster_id": 1,
      "size": 150,
      "percentage": 30.0,
      "suggested_label": "Strugglers",
      ...
    }
  ],
  "elbow_data": [
    {"k": 2, "inertia": 2500, "silhouette": 0.35},
    {"k": 3, "inertia": 1800, "silhouette": 0.40},
    {"k": 4, "inertia": 1234, "silhouette": 0.42}
  ]
}
```

#### 3.2 Ver Elbow Method

```bash
curl "http://localhost:8000/simulation/simulations/{id}/clusters/elbow"
```

#### 3.3 Radar Chart de Comparação

```bash
# Comparar todos os clusters
curl "http://localhost:8000/simulation/simulations/{id}/clusters/radar-comparison"

# Radar de um cluster específico
curl "http://localhost:8000/simulation/simulations/{id}/clusters/0/radar"
```

#### 3.4 Hierarchical Clustering

```bash
# Criar clustering hierárquico
curl -X POST "http://localhost:8000/simulation/simulations/{id}/clusters" \
  -H "Content-Type: application/json" \
  -d '{"method": "hierarchical", "linkage": "ward"}'

# Ver dendrograma
curl "http://localhost:8000/simulation/simulations/{id}/clusters/dendrogram"

# Cortar em N clusters
curl -X POST "http://localhost:8000/simulation/simulations/{id}/clusters/cut" \
  -H "Content-Type: application/json" \
  -d '{"n_clusters": 3}'
```

---

### Fase 4: Casos Especiais (15 min)

**Objetivo**: Identificar "quem devemos entrevistar primeiro".

#### 4.1 Extreme Cases

```bash
# Todos os tipos
curl "http://localhost:8000/simulation/simulations/{id}/extreme-cases?type=all&limit=10"

# Apenas falhas inesperadas
curl "http://localhost:8000/simulation/simulations/{id}/extreme-cases?type=unexpected&limit=5"
```

**Resposta**:
```json
{
  "simulation_id": "sim_001",
  "worst_failures": [
    {
      "synth_id": "synth_042",
      "rank": 1,
      "extreme_type": "worst_failure",
      "success_rate": 0.05,
      "profile_summary": "Idoso, 67 anos, aposentado, alta capability (0.8)",
      "reason": "Alta capability mas apenas 5% sucesso - possível frustração",
      "interview_priority": 10,
      "interview_questions": [
        "O que te impediu de completar a tarefa?",
        "Em que momento você sentiu mais dificuldade?"
      ]
    }
  ],
  "unexpected": [
    {
      "synth_id": "synth_123",
      "extreme_type": "unexpected",
      "reason": "Alta capability + alta trust mas baixo success"
    }
  ]
}
```

#### 4.2 Outliers (Isolation Forest)

```bash
# Detectar 10% de outliers
curl "http://localhost:8000/simulation/simulations/{id}/outliers?contamination=0.1"

# Apenas unexpected failures
curl "http://localhost:8000/simulation/simulations/{id}/outliers?type=unexpected_failure"
```

---

### Fase 5: Explicação Profunda (30 min)

**Objetivo**: Entender "por que esse synth específico falhou".

#### 5.1 SHAP para Synth Específico

```bash
# Explicação para um synth
curl "http://localhost:8000/simulation/simulations/{id}/shap?synth_id=synth_042"
```

**Resposta**:
```json
{
  "simulation_id": "sim_001",
  "synth_id": "synth_042",
  "base_value": 0.42,
  "predicted_value": 0.15,
  "actual_value": 0.05,
  "contributions": [
    {"feature": "trust_mean", "value": 0.25, "shap_value": -0.18, "direction": "negative"},
    {"feature": "complexity", "value": 0.9, "shap_value": -0.12, "direction": "negative"},
    {"feature": "capability_mean", "value": 0.8, "shap_value": 0.05, "direction": "positive"}
  ],
  "explanation_text": "trust_mean (0.25) reduziu em 0.18 | complexity (0.90) reduziu em 0.12 | capability_mean (0.80) aumentou em 0.05"
}
```

#### 5.2 SHAP Summary

```bash
curl "http://localhost:8000/simulation/simulations/{id}/shap/summary"
```

**Resposta**:
```json
{
  "simulation_id": "sim_001",
  "feature_importance": {
    "trust_mean": 0.25,
    "capability_mean": 0.22,
    "complexity": 0.18,
    "friction_tolerance_mean": 0.15
  },
  "top_positive": ["capability_mean", "trust_mean"],
  "top_negative": ["complexity", "friction"],
  "model_r2": 0.78
}
```

#### 5.3 Partial Dependence Plot

```bash
# PDP para capability
curl "http://localhost:8000/simulation/simulations/{id}/pdp?feature=capability_mean"

# Comparar múltiplas features
curl "http://localhost:8000/simulation/simulations/{id}/pdp/comparison?features=capability_mean,trust_mean"
```

---

### Fase 6: Insights LLM

**Objetivo**: Gerar legendas e insights automáticos.

#### 6.1 Caption de Gráfico

```bash
curl "http://localhost:8000/simulation/simulations/{id}/charts/try-vs-success/caption"
```

**Resposta**:
```json
{
  "simulation_id": "sim_001",
  "chart_type": "try_vs_success",
  "caption": "42% dos synths apresentam problema de usabilidade - tentam mas falham",
  "key_metric": "usability_issue_percentage",
  "key_value": 42.0,
  "confidence": 0.92
}
```

#### 6.2 Insight Completo

```bash
curl "http://localhost:8000/simulation/simulations/{id}/charts/try-vs-success/insight"
```

**Resposta**:
```json
{
  "simulation_id": "sim_001",
  "chart_type": "try_vs_success",
  "caption": "42% dos synths apresentam problema de usabilidade",
  "explanation": "A maioria dos usuários (75%) tenta usar a feature, indicando interesse. No entanto, quase metade dos que tentam (42%) falha, sugerindo barreiras de usabilidade. Apenas 40% atinge sucesso completo. Os usuários no quadrante 'usability_issue' têm capability média de 0.6, indicando que não é falta de habilidade.",
  "evidence": [
    "210 de 500 synths (42%) no quadrante usability_issue",
    "Taxa de tentativa alta (75%) indica interesse",
    "Capability média do grupo problemático: 0.6"
  ],
  "recommendation": "Focar em simplificar o fluxo para usuários que já tentam usar a feature",
  "confidence": 0.88
}
```

#### 6.3 Todos os Insights

```bash
curl "http://localhost:8000/simulation/simulations/{id}/insights"
```

---

## Dicas de Uso

### Performance

1. **Clustering**: Para simulações grandes (>5000 synths), considere usar `limit` nos endpoints ou amostrar dados
2. **SHAP**: A primeira requisição treina o modelo (pode levar alguns segundos). Requisições subsequentes são cacheadas
3. **LLM Insights**: Resultados são cacheados por simulação+chart_type

### Fluxo Recomendado

1. Começar com **Try vs Success** para visão geral rápida
2. Se muitos `usability_issue`: explorar **Heatmap** para localizar problema
3. Criar **Clustering** para segmentar usuários
4. Identificar **Extreme Cases** para candidatos a entrevista
5. Usar **SHAP** para explicar casos específicos
6. Gerar **Insights LLM** para comunicar stakeholders

### Erros Comuns

| Erro | Causa | Solução |
|------|-------|---------|
| 404 Simulation not found | ID inválido | Verificar ID da simulação |
| 400 Simulation not completed | Simulação não executada | Executar `/run` primeiro |
| 400 No sensitivity result | Tornado sem sensitivity | Executar sensitivity analysis |
| 400 Too few synths for clustering | N < 10 | Usar análise individual |
