# Frontend API Contracts

**Feature**: 021-analysis-charts-frontend
**Date**: 2025-12-28

## Overview

Este documento descreve os contratos de API que o frontend consome para os gráficos de análise. Os endpoints já existem no backend e as funções de API já estão implementadas em `frontend/src/services/simulation-api.ts`.

---

## Phase 4: Edge Cases & Outliers

### GET /simulation/simulations/{id}/extreme-cases

Retorna casos extremos para seleção de entrevistas.

**Query Parameters:**
- `n_per_category` (int, default: 10): Número de casos por categoria

**Response:**
```json
{
  "simulation_id": "uuid",
  "worst_failures": [
    {
      "synth_id": "string",
      "success_rate": 0.1,
      "failed_rate": 0.8,
      "did_not_try_rate": 0.1,
      "attributes": { "trust_mean": 0.3, "capability_mean": 0.7 },
      "category": "worst_failure",
      "suggested_questions": [
        "O que dificultou o uso da feature?",
        "Qual era sua expectativa inicial?"
      ]
    }
  ],
  "best_successes": [...],
  "unexpected_cases": [...]
}
```

### GET /simulation/simulations/{id}/outliers

Detecta outliers estatísticos usando Isolation Forest.

**Query Parameters:**
- `contamination` (float, default: 0.1): Sensibilidade (0.01-0.3)

**Response:**
```json
{
  "simulation_id": "uuid",
  "method": "isolation_forest",
  "contamination": 0.1,
  "outliers": [
    {
      "synth_id": "string",
      "anomaly_score": 0.85,
      "success_rate": 0.2,
      "failed_rate": 0.7,
      "did_not_try_rate": 0.1,
      "attributes": { "trust_mean": 0.9, "capability_mean": 0.1 },
      "outlier_type": "attribute_outlier",
      "explanation": "Alta confiança mas baixa capacidade - combinação rara"
    }
  ],
  "total_synths": 500,
  "outlier_percentage": 10.0
}
```

---

## Phase 5: Explainability

### GET /simulation/simulations/{id}/shap/summary

Retorna importância global de features via SHAP.

**Response:**
```json
{
  "simulation_id": "uuid",
  "feature_importance": [
    {
      "feature": "trust_mean",
      "mean_abs_shap": 0.15,
      "direction": "positive"
    },
    {
      "feature": "capability_mean",
      "mean_abs_shap": 0.12,
      "direction": "positive"
    }
  ],
  "top_features": ["trust_mean", "capability_mean", "complexity"],
  "explanation_text": "A confiança é o fator mais determinante para o sucesso..."
}
```

### GET /simulation/simulations/{id}/shap/{synth_id}

Retorna explicação SHAP individual para um synth.

**Response:**
```json
{
  "simulation_id": "uuid",
  "synth_id": "synth_123",
  "base_value": 0.5,
  "predicted_value": 0.3,
  "contributions": [
    {
      "feature": "trust_mean",
      "value": 0.2,
      "shap_value": -0.15
    },
    {
      "feature": "complexity",
      "value": 0.8,
      "shap_value": -0.08
    }
  ],
  "explanation_text": "Este synth tem baixa probabilidade de sucesso principalmente devido à baixa confiança..."
}
```

### GET /simulation/simulations/{id}/pdp

Retorna gráfico de dependência parcial para uma feature.

**Query Parameters:**
- `feature` (string, required): Nome da feature
- `grid_resolution` (int, default: 20): Pontos no grid

**Response:**
```json
{
  "simulation_id": "uuid",
  "feature": "trust_mean",
  "points": [
    { "feature_value": 0.0, "avg_prediction": 0.2, "std_prediction": 0.05 },
    { "feature_value": 0.2, "avg_prediction": 0.35, "std_prediction": 0.06 },
    { "feature_value": 0.4, "avg_prediction": 0.5, "std_prediction": 0.07 }
  ],
  "feature_range": [0.0, 1.0],
  "effect_type": "monotonic",
  "effect_strength": 0.8
}
```

### GET /simulation/simulations/{id}/pdp/comparison

Compara PDPs de múltiplas features.

**Query Parameters:**
- `features` (string, required): Lista separada por vírgula
- `grid_resolution` (int, default: 20)

**Response:**
```json
{
  "simulation_id": "uuid",
  "pdps": [
    { "feature": "trust_mean", "points": [...], ... },
    { "feature": "capability_mean", "points": [...], ... }
  ],
  "feature_ranking": ["trust_mean", "capability_mean", "complexity"]
}
```

---

## Phase 6: LLM Insights

### GET /simulation/simulations/{id}/insights

Retorna insights previamente gerados.

**Response:**
```json
{
  "simulation_id": "uuid",
  "insights": [
    {
      "simulation_id": "uuid",
      "chart_type": "try_vs_success",
      "caption": {
        "short": "Alta taxa de não-tentativa",
        "medium": "65% dos synths não tentam usar a feature, indicando problema de descoberta"
      },
      "explanation": "A análise mostra que a maioria...",
      "evidence": [
        {
          "metric": "did_not_try_rate",
          "value": 0.65,
          "interpretation": "Acima do esperado (40%)"
        }
      ],
      "recommendation": "Melhorar onboarding e visibilidade da feature",
      "generated_at": "2025-12-28T10:00:00Z"
    }
  ],
  "executive_summary": "# Resumo Executivo\n\n...",
  "updated_at": "2025-12-28T10:00:00Z"
}
```

### POST /simulation/simulations/{id}/insights/{chart_type}

Gera insight para um gráfico específico.

**Request Body:**
```json
{
  "chart_data": { ... },
  "force_regenerate": false
}
```

**Response:** `ChartInsight` object

### POST /simulation/simulations/{id}/insights/executive-summary

Gera resumo executivo consolidando todos os insights.

**Response:**
```json
{
  "simulation_id": "uuid",
  "summary": "# Resumo Executivo\n\n## Principais Descobertas\n\n...",
  "total_insights": 5
}
```

---

## Frontend Service Functions

Todas as funções já implementadas em `simulation-api.ts`:

```typescript
// Phase 4
export async function getExtremeCases(simulationId: string, nPerCategory = 10): Promise<ExtremeCasesTable>
export async function getOutliers(simulationId: string, contamination = 0.1): Promise<OutlierResult>

// Phase 5
export async function getShapSummary(simulationId: string): Promise<ShapSummary>
export async function getShapExplanation(simulationId: string, synthId: string): Promise<ShapExplanation>
export async function getPDP(simulationId: string, feature: string, gridResolution = 20): Promise<PDPResult>
export async function getPDPComparison(simulationId: string, features: string[], gridResolution = 20): Promise<PDPComparison>

// Phase 6
export async function getSimulationInsights(simulationId: string): Promise<SimulationInsights>
export async function generateChartInsight(simulationId: string, chartType: ChartType, chartData: Record<string, unknown>, forceRegenerate = false): Promise<ChartInsight>
export async function generateExecutiveSummary(simulationId: string): Promise<ExecutiveSummaryResponse>
```

---

## Query Keys

Todas as keys já definidas em `lib/query-keys.ts`:

```typescript
simulation: {
  // Phase 4
  extremeCases: (simId: string) => ['simulation', 'extreme-cases', simId] as const,
  outliers: (simId: string) => ['simulation', 'outliers', simId] as const,

  // Phase 5
  shapSummary: (simId: string) => ['simulation', 'shap', 'summary', simId] as const,
  shapExplanation: (simId: string, synthId: string) => ['simulation', 'shap', 'explanation', simId, synthId] as const,
  pdp: (simId: string, feature: string) => ['simulation', 'pdp', simId, feature] as const,
  pdpComparison: (simId: string) => ['simulation', 'pdp', 'comparison', simId] as const,

  // Phase 6
  insights: (simId: string) => ['simulation', 'insights', simId] as const,
}
```
