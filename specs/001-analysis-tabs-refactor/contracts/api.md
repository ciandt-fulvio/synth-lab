# API Contracts: Analysis Tabs Refactor

**Feature**: 001-analysis-tabs-refactor
**Date**: 2025-12-29

## New Endpoint

### Create Auto Interview

**Endpoint**: `POST /api/experiments/{experiment_id}/interviews/auto`

**Description**: Creates an automatic interview with extreme case synths (top 5 + bottom 5 performers)

**Request**:
```json
{
  "num_turns": 4
}
```

**Response** (201 Created):
```json
{
  "interview_id": "int_abc123",
  "experiment_id": "exp_xyz789",
  "synth_ids": ["synth_1", "synth_2", ..., "synth_10"],
  "num_turns": 4,
  "status": "pending",
  "created_at": "2025-12-29T14:00:00Z"
}
```

**Errors**:
- `404 Not Found` - Experiment não encontrado
- `400 Bad Request` - Não há synths suficientes (precisa pelo menos 10)
- `409 Conflict` - Já existe entrevista automática em andamento
- `500 Internal Server Error` - Erro ao criar entrevista

**Business Logic**:
1. Busca todos os synths do experimento
2. Ordena por success_rate (desc)
3. Seleciona top 5 e bottom 5
4. Cria interview com esses 10 synths e num_turns=4
5. Retorna interview criada com link para acompanhamento

---

## Endpoints to Remove (Backend Cleanup)

**ONLY if not used elsewhere in the codebase**:

### Get Attribute Importance

`GET /api/experiments/{experiment_id}/analysis/charts/attribute-importance`

**Decision**: Verificar se usado em outra parte do código antes de remover. Se usado APENAS na aba Influência antiga, pode ser removido.

### Get Attribute Correlation

`GET /api/experiments/{experiment_id}/analysis/charts/attribute-correlation`

**Decision**: Verificar se usado em outra parte do código antes de remover. Se usado APENAS na aba Influência antiga, pode ser removido.

---

## Modified Endpoints (No Changes, Just Usage Update)

### Get SHAP Summary

`GET /api/experiments/{experiment_id}/analysis/charts/shap-summary`

**Change**: Will be called from PhaseInfluence instead of PhaseDeepDive (or wherever it was before)

### Get PDP

`GET /api/experiments/{experiment_id}/analysis/charts/pdp`

**Change**: Will be called from PhaseInfluence instead of PhaseDeepDive (or wherever it was before)

### Get SHAP Waterfall

`GET /api/experiments/{experiment_id}/analysis/charts/shap-waterfall?synth_id={synth_id}`

**Change**:
- Will be called from PhaseSpecial (below ExtremeCasesSection and OutliersSection)
- `synth_id` will come from card click instead of dropdown selection

### Get Extreme Cases

`GET /api/experiments/{experiment_id}/analysis/charts/extreme-cases`

**Change**: Response will be used to populate click handlers (no schema change)

### Get Outliers

`GET /api/experiments/{experiment_id}/analysis/charts/outliers?threshold={threshold}`

**Change**: Response will be used to populate click handlers (no schema change)

---

## Frontend Types (TypeScript)

### AutoInterviewRequest
```typescript
interface AutoInterviewRequest {
  num_turns: number;  // Always 4
}
```

### AutoInterviewResponse
```typescript
interface AutoInterviewResponse {
  interview_id: string;
  experiment_id: string;
  synth_ids: string[];
  num_turns: number;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  created_at: string;
}
```

### ExtremeCaseWithHandler
```typescript
interface ExtremeCaseWithHandler extends ExtremeCase {
  onClick: () => void;  // Click handler to trigger SHAP Waterfall
}
```

### OutlierWithHandler
```typescript
interface OutlierWithHandler extends Outlier {
  onClick: () => void;  // Click handler to trigger SHAP Waterfall
}
```
