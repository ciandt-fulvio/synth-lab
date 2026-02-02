# Quickstart Guide: Unified DAG & Hypothesis Generation

**Feature**: 037-unified-dag-hypotheses
**Audience**: Developers integrating with the unified generation and drawer editing APIs
**Last Updated**: 2026-02-02

## Overview

Feature 037 unifies DAG and hypothesis generation into a single LLM call. After generation, users interact with variables through a right-side sheet (drawer) to adjust relevance and value ranges. The DAG visualization shows relevance-driven color saturation.

## Prerequisites

- Simulation must exist (`POST /api/simulations`)
- Simulation question must be validated (`POST /api/simulations/{id}/confirm-question`)

## Step 1: Generate DAG + Hypotheses (Unified)

**Endpoint**: `POST /api/simulations/{simulation_id}/confirm-question` (existing, now generates both)

```bash
curl -X POST http://localhost:8000/api/simulations/sim_12345678/confirm-question \
  -H "Content-Type: application/json"
```

**Response** (200 OK):
```json
{
  "id": "sim_12345678",
  "status": "AWAITING_DAG_VALIDATION",
  "dag": {
    "id": "dag_abcd1234",
    "nodes": [
      {
        "name": "conversion_rate",
        "type": "rate",
        "scope": "internal",
        "label": "Taxa de Conversão",
        "description": "Percentual de visitantes que compram",
        "controllability": "medium"
      }
    ],
    "edges": [
      { "from": "marketing_spend", "to": "conversion_rate", "strength_estimated": "moderate" }
    ]
  },
  "hypotheses": [
    {
      "id": "hyp_a1b2c3d4",
      "variable_name": "conversion_rate",
      "distribution_type": "beta",
      "distribution_params": { "alpha": 15.0, "beta": 85.0 },
      "relevance": "high",
      "range_min": 0.0,
      "range_max": 1.0
    },
    {
      "id": "hyp_b2c3d4e5",
      "variable_name": "marketing_spend",
      "distribution_type": "lognormal",
      "distribution_params": { "mu": 9.2, "sigma": 0.5 },
      "relevance": "medium",
      "range_min": 1000,
      "range_max": 100000
    }
  ]
}
```

**What Happens**:
1. Single `gpt-4o-mini` call generates DAG structure AND distribution hypotheses
2. Each hypothesis includes relevance (low/medium/high) and optional range (min/max)
3. Missing hypotheses default to uniform distribution, medium relevance
4. Both DAG and hypotheses persisted to database

## Step 2: View DAG with Relevance Saturation

After generation, the DAG visualization renders nodes with color saturation based on relevance:

- **High relevance** → Full color (100% saturation) — violet/cyan
- **Medium relevance** → 70% saturation — slightly desaturated
- **Low relevance** → 40% saturation — noticeably desaturated

No API call needed — frontend reads relevance from hypothesis data.

## Step 3: Edit Variable via Drawer

Click a node to open the right-side sheet. Edit relevance and range.

**Endpoint**: `PATCH /api/simulations/{simulation_id}/hypotheses/{hypothesis_id}`

### Change Relevance

```bash
curl -X PATCH http://localhost:8000/api/simulations/sim_12345678/hypotheses/hyp_a1b2c3d4 \
  -H "Content-Type: application/json" \
  -d '{
    "relevance": "low"
  }'
```

### Set Range Bounds

```bash
curl -X PATCH http://localhost:8000/api/simulations/sim_12345678/hypotheses/hyp_b2c3d4e5 \
  -H "Content-Type: application/json" \
  -d '{
    "range_min": 5000,
    "range_max": 50000
  }'
```

### Clear Range (Remove Clamping)

```bash
curl -X PATCH http://localhost:8000/api/simulations/sim_12345678/hypotheses/hyp_b2c3d4e5 \
  -H "Content-Type: application/json" \
  -d '{
    "range_min": null,
    "range_max": null
  }'
```

**Response** (200 OK):
```json
{
  "id": "hyp_b2c3d4e5",
  "variable_name": "marketing_spend",
  "distribution_type": "lognormal",
  "distribution_params": { "mu": 9.2, "sigma": 0.5 },
  "relevance": "low",
  "range_min": 5000,
  "range_max": 50000
}
```

**Validation Errors** (422):
```json
{ "detail": "range_min must be less than or equal to range_max" }
```

## Step 4: Run Simulation

Range clamping is applied automatically during simulation.

```bash
curl -X POST http://localhost:8000/api/simulations/sim_12345678/run
```

During sampling:
- If `range_min=5000` and `range_max=50000`, any sampled value outside this range is clamped
- If no range set (null), samples are used as-is

## Frontend Integration

```typescript
// Node click handler in DAGVisualization
const handleNodeClick = (variable: Variable) => {
  setSelectedVariable(variable);
  setSheetOpen(true);
};

// Sheet content
<Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
  <SheetContent side="right" className="w-full sm:w-[400px]">
    <SheetHeader>
      <SheetTitle>{selectedVariable.label}</SheetTitle>
      <SheetDescription>{selectedVariable.description}</SheetDescription>
    </SheetHeader>
    <NodeDetailForm
      hypothesis={hypothesisForVariable}
      onSave={handleSave}
    />
  </SheetContent>
</Sheet>

// Relevance-driven node color
function getNodeColor(scope: string, relevance: string): string {
  const base = scope === 'user'
    ? { h: 263, s: 84, l: 58 }
    : { h: 189, s: 95, l: 42 };
  const mult = { high: 1.0, medium: 0.7, low: 0.4 }[relevance] ?? 1.0;
  return `hsl(${base.h}, ${base.s * mult}%, ${base.l}%)`;
}
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `404` Simulation not found | Invalid simulation ID | Check ID with `GET /api/simulations/{id}` |
| `422` range_min > range_max | Invalid range | Ensure min ≤ max |
| `422` Invalid relevance | Not low/medium/high | Use valid enum value |
| `500` LLM failure | gpt-4o-mini timeout | Retry request |

## API Reference

Full OpenAPI specification: [contracts/openapi.yaml](contracts/openapi.yaml)
