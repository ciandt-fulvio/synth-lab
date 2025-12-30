# API Contracts: AI-Generated Insights

**Feature**: 023-quantitative-ai-insights
**Date**: 2025-12-29

## Overview

REST API contracts for retrieving AI-generated chart insights and executive summaries. All endpoints follow existing synth-lab API patterns (FastAPI, JSON responses, error handling).

## Base URL

```
http://localhost:8000/api
```

## Authentication

None required (internal API).

## Endpoints

### 1. Get Chart Insight

**Endpoint**: `GET /experiments/{experiment_id}/insights/{chart_type}`

**Description**: Retrieve AI-generated insight for a specific chart type.

**Path Parameters**:
- `experiment_id` (string, required): Experiment ID (e.g., `exp_12345678`)
- `chart_type` (string, required): Chart type identifier

**Valid Chart Types**:
- `try_vs_success`
- `shap_summary`
- `pdp`
- `pca_scatter`
- `radar_comparison`
- `extreme_cases`
- `outliers`

**Request Example**:
```http
GET /api/experiments/exp_12345678/insights/try_vs_success HTTP/1.1
Host: localhost:8000
```

**Success Response** (200 OK):
```json
{
  "analysisId": "ana_12345678",
  "chartType": "try_vs_success",
  "problemUnderstanding": "O experimento testa a usabilidade de um novo fluxo de checkout com foco em reduzir fricção durante o pagamento.",
  "trendsObserved": "Alta taxa de tentativa (85%) indica boa descoberabilidade. Conversão moderada (62%) sugere barreiras na execução. Principal ponto de falha: etapa de pagamento (23% dos usuários).",
  "keyFindings": [
    "73% dos usuários que tentam completam o checkout (conversão razoável)",
    "Principal barreira identificada: etapa de pagamento (23% de falha)",
    "Synths com alta tolerância a fricção têm 2x mais probabilidade de sucesso"
  ],
  "summary": "O novo fluxo de checkout mostra boa descoberabilidade (85% tentam usar) mas enfrenta desafios de conversão na etapa de pagamento. Análise sugere simplificar formulário de pagamento e adicionar sinais visuais de segurança para aumentar confiança.",
  "generationTimestamp": "2025-12-29T10:30:00Z",
  "status": "completed",
  "model": "04-mini",
  "reasoningTrace": null
}
```

**Pending Response** (200 OK):
```json
{
  "analysisId": "ana_12345678",
  "chartType": "try_vs_success",
  "status": "pending",
  "generationTimestamp": "2025-12-29T10:28:00Z",
  "model": "04-mini"
}
```

**Not Found Response** (404 Not Found):
```json
{
  "detail": "Insight for chart type 'try_vs_success' not found for experiment 'exp_12345678'"
}
```

**Failed Generation Response** (200 OK):
```json
{
  "analysisId": "ana_12345678",
  "chartType": "try_vs_success",
  "status": "failed",
  "generationTimestamp": "2025-12-29T10:30:00Z",
  "model": "04-mini"
}
```

**Error Response** (400 Bad Request):
```json
{
  "detail": "Invalid chart type: 'invalid_type'. Must be one of: try_vs_success, shap_summary, pdp, pca_scatter, radar_comparison, extreme_cases, outliers"
}
```

---

### 2. Get All Chart Insights

**Endpoint**: `GET /experiments/{experiment_id}/insights`

**Description**: Retrieve all AI-generated insights for an experiment (across all chart types).

**Path Parameters**:
- `experiment_id` (string, required): Experiment ID

**Query Parameters**:
- `status` (string, optional): Filter by status (`pending`, `completed`, `failed`)

**Request Example**:
```http
GET /api/experiments/exp_12345678/insights?status=completed HTTP/1.1
Host: localhost:8000
```

**Success Response** (200 OK):
```json
{
  "experimentId": "exp_12345678",
  "insights": [
    {
      "analysisId": "ana_12345678",
      "chartType": "try_vs_success",
      "problemUnderstanding": "...",
      "trendsObserved": "...",
      "keyFindings": ["...", "...", "..."],
      "summary": "...",
      "generationTimestamp": "2025-12-29T10:30:00Z",
      "status": "completed",
      "model": "04-mini"
    },
    {
      "analysisId": "ana_12345678",
      "chartType": "shap_summary",
      "problemUnderstanding": "...",
      "trendsObserved": "...",
      "keyFindings": ["...", "..."],
      "summary": "...",
      "generationTimestamp": "2025-12-29T10:31:00Z",
      "status": "completed",
      "model": "04-mini"
    }
    // ... other insights
  ],
  "totalCount": 7,
  "completedCount": 5,
  "pendingCount": 1,
  "failedCount": 1
}
```

**Empty Response** (200 OK):
```json
{
  "experimentId": "exp_12345678",
  "insights": [],
  "totalCount": 0,
  "completedCount": 0,
  "pendingCount": 0,
  "failedCount": 0
}
```

---

### 3. Get Executive Summary

**Endpoint**: `GET /experiments/{experiment_id}/insights/summary`

**Description**: Retrieve executive summary synthesizing all chart insights.

**Path Parameters**:
- `experiment_id` (string, required): Experiment ID

**Request Example**:
```http
GET /api/experiments/exp_12345678/insights/summary HTTP/1.1
Host: localhost:8000
```

**Success Response** (200 OK):
```json
{
  "analysisId": "ana_12345678",
  "overview": "Experimento testou novo fluxo de checkout com 500 usuários sintéticos. Resultados mostram boa descoberabilidade (85% tentam) mas conversão limitada pela etapa de pagamento (62% sucesso final).",
  "explainability": "Análise SHAP identificou confiança (23.4% de importância) e tolerância a fricção (18.9%) como principais drivers de sucesso. Usuários com baixa confiança abandonam na etapa de pagamento mesmo com alta capacidade técnica.",
  "segmentation": "PCA revelou 3 segmentos: (1) usuários experientes (40%) com alta conversão, (2) novatos hesitantes (35%) com baixa taxa de tentativa, (3) usuários motivados (25%) com tentativa alta mas falha frequente no pagamento.",
  "edgeCases": "Identificados 10 casos de falha surpreendente: synths com alta capacidade técnica mas baixa confiança. Sugere problema de comunicação de segurança no formulário de pagamento.",
  "recommendations": [
    "Simplificar formulário de pagamento: reduzir campos obrigatórios de 8 para 4",
    "Adicionar sinais de confiança: certificados de segurança visíveis, ícone de cadeado, selos de pagamento",
    "Oferecer onboarding contextual para usuários novatos: tooltip explicativo na primeira tentativa"
  ],
  "includedChartTypes": [
    "try_vs_success",
    "shap_summary",
    "pdp",
    "pca_scatter",
    "radar_comparison",
    "extreme_cases",
    "outliers"
  ],
  "generationTimestamp": "2025-12-29T10:35:00Z",
  "status": "completed",
  "model": "04-mini"
}
```

**Pending Response** (200 OK):
```json
{
  "analysisId": "ana_12345678",
  "status": "pending",
  "generationTimestamp": "2025-12-29T10:33:00Z",
  "model": "04-mini",
  "includedChartTypes": []
}
```

**Partial Summary Response** (200 OK - less than 3 insights available):
```json
{
  "analysisId": "ana_12345678",
  "overview": "Síntese parcial baseada em insights disponíveis. Aguardando geração de insights adicionais para análise completa.",
  "explainability": "Dados disponíveis limitados. Análise completa requer insights de SHAP e PDP.",
  "segmentation": "Segmentação não disponível. Aguardando insights de PCA e Radar.",
  "edgeCases": "Análise de casos extremos pendente.",
  "recommendations": [
    "Aguardar conclusão de geração de insights para recomendações completas"
  ],
  "includedChartTypes": ["try_vs_success"],
  "generationTimestamp": "2025-12-29T10:35:00Z",
  "status": "partial",
  "model": "04-mini"
}
```

**Not Found Response** (404 Not Found):
```json
{
  "detail": "Executive summary not found for experiment 'exp_12345678'"
}
```

---

### 4. Trigger Insight Generation (Manual Override)

**Endpoint**: `POST /experiments/{experiment_id}/insights/generate`

**Description**: Manually trigger insight generation for all chart types (normally auto-triggered after analysis completes).

**Path Parameters**:
- `experiment_id` (string, required): Experiment ID

**Request Body** (optional):
```json
{
  "chartTypes": ["try_vs_success", "shap_summary"],  // Optional: specific chart types
  "force": true  // Optional: regenerate even if insights exist (default: false)
}
```

**Request Example**:
```http
POST /api/experiments/exp_12345678/insights/generate HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "chartTypes": ["try_vs_success"],
  "force": true
}
```

**Success Response** (202 Accepted):
```json
{
  "experimentId": "exp_12345678",
  "message": "Insight generation triggered for 1 chart type(s)",
  "chartTypes": ["try_vs_success"],
  "estimatedCompletionTime": "2025-12-29T10:32:00Z"
}
```

**Error Response** (400 Bad Request):
```json
{
  "detail": "Analysis not found for experiment 'exp_12345678'. Run analysis first."
}
```

---

## Error Codes

| Status Code | Meaning | When It Occurs |
|-------------|---------|----------------|
| 200 OK | Success | Insight/summary found and returned |
| 202 Accepted | Accepted | Manual generation triggered |
| 400 Bad Request | Invalid request | Invalid chart_type, missing analysis |
| 404 Not Found | Not found | Insight/summary doesn't exist (not yet generated) |
| 500 Internal Server Error | Server error | Unexpected error during processing |

## Response Headers

All responses include:
```
Content-Type: application/json
Access-Control-Allow-Origin: http://localhost:5173  # Frontend dev server
```

## Rate Limiting

None (internal API).

## Caching

- Frontend should cache insights using React Query with staleTime=5 minutes
- Insights are immutable once completed (status="completed")
- Executive summary is regenerated if any individual insight is regenerated

## Data Freshness

- Individual insights: Generated within 2 minutes of chart data caching
- Executive summary: Generated within 30 seconds of last insight completion
- Insights cached indefinitely until experiment is deleted

## Contract Testing

See `tests/contract/test_insights_contracts.py` for contract validation tests.

**Contract Guarantees**:
1. All chart types return consistent JSON structure
2. `status` field always present and valid
3. `completed` status guarantees all required fields populated
4. `pending` status may have partial data
5. `failed` status only includes minimal metadata

---

**Version**: 1.0.0
**Last Updated**: 2025-12-29
