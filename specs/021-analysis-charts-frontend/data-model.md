# Data Model: Analysis Charts Frontend

**Feature**: 021-analysis-charts-frontend
**Date**: 2025-12-28

## Overview

Este documento descreve os tipos TypeScript usados nos gráficos de análise quantitativa. Todos os tipos já existem em `frontend/src/types/simulation.ts` e estão documentados aqui para referência.

---

## Phase 4: Edge Cases & Outliers

### ExtremeSynth

Representa um synth identificado como caso extremo.

```typescript
interface ExtremeSynth {
  synth_id: string;           // ID do synth
  success_rate: number;       // Taxa de sucesso (0-1)
  failed_rate: number;        // Taxa de falha (0-1)
  did_not_try_rate: number;   // Taxa de não tentativa (0-1)
  attributes: Record<string, number>;  // Atributos do synth
  category: 'worst_failure' | 'best_success' | 'unexpected';
  suggested_questions: string[];  // Perguntas sugeridas para entrevista
}
```

### ExtremeCasesTable

Tabela consolidada de casos extremos.

```typescript
interface ExtremeCasesTable {
  simulation_id: string;
  worst_failures: ExtremeSynth[];    // Piores falhas
  best_successes: ExtremeSynth[];    // Melhores sucessos
  unexpected_cases: ExtremeSynth[];  // Casos inesperados
}
```

### OutlierSynth

Representa um synth identificado como outlier estatístico.

```typescript
interface OutlierSynth {
  synth_id: string;
  anomaly_score: number;        // Score de anomalia (maior = mais anômalo)
  success_rate: number;
  failed_rate: number;
  did_not_try_rate: number;
  attributes: Record<string, number>;
  outlier_type: 'attribute_outlier' | 'outcome_outlier' | 'both';
  explanation: string;          // Explicação do porquê é outlier
}
```

### OutlierResult

Resultado da detecção de outliers.

```typescript
interface OutlierResult {
  simulation_id: string;
  method: 'isolation_forest';   // Método de detecção
  contamination: number;        // Parâmetro de sensibilidade (0.01-0.3)
  outliers: OutlierSynth[];
  total_synths: number;
  outlier_percentage: number;   // % de synths identificados como outliers
}
```

---

## Phase 5: Explainability (SHAP & PDP)

### ShapContribution

Contribuição individual de uma feature para a predição.

```typescript
interface ShapContribution {
  feature: string;      // Nome da feature
  value: number;        // Valor da feature para este synth
  shap_value: number;   // Contribuição SHAP (positivo = aumenta sucesso)
}
```

### ShapExplanation

Explicação SHAP para um synth individual.

```typescript
interface ShapExplanation {
  simulation_id: string;
  synth_id: string;
  base_value: number;          // Valor base (média)
  predicted_value: number;     // Predição final
  contributions: ShapContribution[];
  explanation_text?: string;   // Explicação em texto (LLM)
}
```

### FeatureImportance

Importância de uma feature no modelo.

```typescript
interface FeatureImportance {
  feature: string;
  mean_abs_shap: number;  // Média do valor absoluto SHAP
  direction: 'positive' | 'negative' | 'mixed';  // Direção do impacto
}
```

### ShapSummary

Resumo global de importância de features.

```typescript
interface ShapSummary {
  simulation_id: string;
  feature_importance: FeatureImportance[];
  top_features: string[];       // Top N features mais importantes
  explanation_text?: string;    // Explicação em texto (LLM)
}
```

### PDPPoint

Ponto na curva de dependência parcial.

```typescript
interface PDPPoint {
  feature_value: number;    // Valor da feature
  avg_prediction: number;   // Predição média neste ponto
  std_prediction?: number;  // Desvio padrão (opcional)
}
```

### PDPResult

Resultado de um gráfico PDP para uma feature.

```typescript
interface PDPResult {
  simulation_id: string;
  feature: string;
  points: PDPPoint[];
  feature_range: [number, number];  // Min/max da feature
  effect_type: 'linear' | 'monotonic' | 'nonlinear' | 'threshold';
  effect_strength: number;  // Força do efeito (0-1)
}
```

### PDPComparison

Comparação de PDPs entre features.

```typescript
interface PDPComparison {
  simulation_id: string;
  pdps: PDPResult[];
  feature_ranking: string[];  // Features ordenadas por impacto
}
```

---

## Phase 6: LLM Insights

### ChartCaption

Legenda para um gráfico.

```typescript
interface ChartCaption {
  short: string;   // Legenda curta (1 linha)
  medium: string;  // Legenda média (2-3 linhas)
}
```

### InsightEvidence

Evidência que suporta um insight.

```typescript
interface InsightEvidence {
  metric: string;           // Nome da métrica
  value: string | number;   // Valor observado
  interpretation: string;   // Interpretação do valor
}
```

### ChartInsight

Insight gerado por LLM para um gráfico.

```typescript
interface ChartInsight {
  simulation_id: string;
  chart_type: ChartType;        // Tipo do gráfico
  caption: ChartCaption;
  explanation: string;          // Explicação detalhada
  evidence: InsightEvidence[];  // Evidências
  recommendation: string;       // Recomendação acionável
  generated_at: string;         // Timestamp ISO
}
```

### SimulationInsights

Todos os insights de uma simulação.

```typescript
interface SimulationInsights {
  simulation_id: string;
  insights: ChartInsight[];
  executive_summary?: string;   // Resumo executivo (markdown)
  updated_at: string;
}
```

### ChartType

Tipos de gráficos que podem ter insights.

```typescript
type ChartType =
  | 'try_vs_success'
  | 'distribution'
  | 'failure_heatmap'
  | 'box_plot'
  | 'scatter'
  | 'tornado'
  | 'elbow'
  | 'radar'
  | 'dendrogram'
  | 'extreme_cases'
  | 'outliers'
  | 'shap_summary'
  | 'shap_explanation'
  | 'pdp'
  | 'pdp_comparison';
```

---

## Request Types

### ClusterRequest

Request para criar clusters.

```typescript
interface ClusterRequest {
  method: 'kmeans' | 'hierarchical';
  n_clusters?: number;               // Para K-Means
  features?: string[];               // Features a usar
  linkage?: 'ward' | 'complete' | 'average' | 'single';  // Para hierarchical
}
```

### CutDendrogramRequest

Request para cortar dendrograma.

```typescript
interface CutDendrogramRequest {
  n_clusters: number;  // Número de clusters desejado
}
```

### GenerateInsightRequest

Request para gerar insight.

```typescript
interface GenerateInsightRequest {
  chart_data: Record<string, unknown>;  // Dados do gráfico
  force_regenerate?: boolean;            // Forçar regeneração
}
```

---

## Component Props Interfaces

### Recommended Props Patterns

```typescript
// Section component props
interface ChartSectionProps {
  simulationId: string;
  height?: number;
  showExplanation?: boolean;
}

// Chart component props
interface ChartComponentProps<T> {
  data: T;
  height?: number;
  onPointClick?: (point: T['points'][0]) => void;
}

// Table component props
interface TableSectionProps {
  simulationId: string;
  nPerCategory?: number;
}
```

---

## State Types

### Filter/Control States

```typescript
// Axis selection state
type AxisOption =
  | 'capability_mean'
  | 'trust_mean'
  | 'complexity'
  | 'initial_effort'
  | 'perceived_risk'
  | 'time_to_value'
  | 'success_rate'
  | 'failed_rate';

// Clustering method state
type ClusteringMethod = 'kmeans' | 'hierarchical';

// Slider threshold state (0-1)
type ThresholdValue = number;
```

---

## API Response Types Reference

Todas as funções de API em `simulation-api.ts` retornam os tipos acima:

```typescript
// Phase 4
getExtremeCases(simId, nPerCategory): Promise<ExtremeCasesTable>
getOutliers(simId, contamination): Promise<OutlierResult>

// Phase 5
getShapSummary(simId): Promise<ShapSummary>
getShapExplanation(simId, synthId): Promise<ShapExplanation>
getPDP(simId, feature, gridResolution): Promise<PDPResult>
getPDPComparison(simId, features, gridResolution): Promise<PDPComparison>

// Phase 6
getSimulationInsights(simId): Promise<SimulationInsights>
generateChartInsight(simId, chartType, chartData): Promise<ChartInsight>
generateExecutiveSummary(simId): Promise<ExecutiveSummaryResponse>
```
