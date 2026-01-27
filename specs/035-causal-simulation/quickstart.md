# Quickstart: Causal Simulation System

## Setup

```bash
# Install dependencies
cd /Users/fulvio/Projects/synth-lab
uv sync

# Run database migrations
uv run alembic upgrade head

# Start backend
uv run uvicorn synth_lab.api.main:app --reload

# Start frontend (new terminal)
cd frontend && npm run dev
```

## Example Workflow

### 1. Create Simulation from Natural Language Question

```bash
curl -X POST http://localhost:8000/api/simulations \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What will be the adoption rate for a weekly meal subscription service?"
  }'
```

**Response**:
```json
{
  "simulation_id": "sim_abc123",
  "status": "dag_generated",
  "problem_decomposition": {
    "intervention": "weekly_meal_subscription",
    "primary_outcome": "adoption_rate",
    "secondary_outcomes": ["retention_3m", "usage_frequency"],
    "time_horizon": "monthly",
    "unit_of_analysis": "user"
  },
  "dag": {
    "nodes": [
      {"id": "age", "type": "observable"},
      {"id": "income", "type": "observable"},
      {"id": "routine_predictability", "type": "latent"},
      {"id": "delivery_friction", "type": "friction"},
      {"id": "adoption", "type": "outcome"}
    ],
    "edges": [
      {"source": "age", "target": "income"},
      {"source": "income", "target": "adoption"},
      {"source": "routine_predictability", "target": "adoption"},
      {"source": "delivery_friction", "target": "adoption"}
    ]
  }
}
```

### 2. Review and Edit DAG (Optional)

```bash
# Add a new variable
curl -X PUT http://localhost:8000/api/simulations/sim_abc123/dag \
  -H "Content-Type: application/json" \
  -d '{
    "add_nodes": [
      {"id": "price_sensitivity", "type": "latent"}
    ],
    "add_edges": [
      {"source": "price_sensitivity", "target": "adoption"}
    ]
  }'
```

### 3. Review Generated Hypotheses

```bash
curl http://localhost:8000/api/simulations/sim_abc123/hypotheses
```

**Response**:
```json
{
  "hypotheses": [
    {
      "variable_id": "age",
      "distribution": "normal",
      "params": {"mean": 35, "std": 12},
      "scope": "user",
      "range": [18, 65]
    },
    {
      "variable_id": "delivery_friction",
      "distribution": "categorical",
      "params": {"categories": ["low", "medium", "high"], "probs": [0.3, 0.5, 0.2]},
      "scope": "world"
    }
  ]
}
```

### 4. Adjust Hypotheses (Optional)

```bash
# Update delivery_friction based on domain knowledge
curl -X PUT http://localhost:8000/api/simulations/sim_abc123/hypotheses \
  -H "Content-Type: application/json" \
  -d '{
    "updates": [
      {
        "variable_id": "delivery_friction",
        "params": {"categories": ["low", "medium", "high"], "probs": [0.2, 0.3, 0.5]}
      }
    ]
  }'
```

### 5. Run Simulation

```bash
curl -X POST http://localhost:8000/api/simulations/sim_abc123/run \
  -H "Content-Type: application/json" \
  -d '{
    "n_worlds": 500,
    "random_seed": 42
  }'
```

**Response** (async, poll for completion):
```json
{
  "simulation_id": "sim_abc123",
  "status": "running",
  "progress": "120/500 worlds completed"
}
```

### 6. View Results and Insights

```bash
# Get evidence (percentiles, sensitivity, clusters)
curl http://localhost:8000/api/simulations/sim_abc123/evidence

# Get generated insights
curl http://localhost:8000/api/simulations/sim_abc123/insights
```

**Evidence Response**:
```json
{
  "outcome_distribution": {
    "p5": 0.06,
    "p50": 0.14,
    "p95": 0.28
  },
  "sensitivity_analysis": {
    "delivery_friction": 0.42,
    "routine_predictability": 0.31,
    "income": 0.18,
    "age": 0.09
  },
  "failure_modes": [
    {
      "pattern": "adoption < 0.05",
      "condition": "delivery_friction == 'high' AND routine_predictability < 0.3",
      "affected_worlds": 87
    }
  ],
  "behavioral_clusters": [
    {
      "cluster_id": 1,
      "size": 210,
      "centroid": {"delivery_friction": "low", "routine_predictability": 0.7},
      "outcome_mean": 0.25
    }
  ]
}
```

**Insights Response**:
```json
{
  "insights": [
    {
      "insight_id": "ins_001",
      "type": "primary_forecast",
      "message": "Expected adoption: 12-16% (median 14%). Main driver: delivery friction explains 42% of variance.",
      "evidence": {
        "variables": ["delivery_friction", "routine_predictability"],
        "simulation_worlds": [23, 45, 67, ...],
        "statistical_basis": "Variance decomposition via correlation²"
      },
      "recommendations": [
        "Launch pilot with low-friction segment (20% of base)",
        "Invest in logistics reliability before broad rollout"
      ]
    }
  ]
}
```

### 7. Trace Insight to Evidence (Auditability)

```bash
curl http://localhost:8000/api/simulations/sim_abc123/insights/ins_001/trace
```

**Response**:
```json
{
  "insight": "Expected adoption: 12-16%",
  "trace": {
    "statistical_result": "p50 = 0.14, IQR = [0.12, 0.16]",
    "derived_from_variables": ["delivery_friction", "routine_predictability", "income"],
    "hypothesis_version": "v1_initial",
    "affected_worlds": [1, 2, 3, ..., 500],
    "random_seed": 42,
    "dag_structure": {
      "nodes": [...],
      "edges": [...]
    }
  }
}
```

### 8. Save Hypothesis Version for Scenario Planning

```bash
# Save current hypotheses as "optimistic" scenario
curl -X POST http://localhost:8000/api/simulations/sim_abc123/hypotheses/versions \
  -H "Content-Type: application/json" \
  -d '{
    "version_name": "optimistic",
    "description": "Low friction, high routine predictability assumptions"
  }'

# Later: compare with "pessimistic" scenario
curl "http://localhost:8000/api/simulations/sim_abc123/hypotheses/compare?v1=optimistic&v2=pessimistic"
```

## Frontend Integration (React)

```typescript
import { useSimulation, useDAG, useHypotheses, useInsights } from '@/hooks';

function SimulationPage() {
  const { createSimulation } = useSimulation();
  const [simulationId, setSimulationId] = useState<string | null>(null);
  
  const handleSubmit = async (question: string) => {
    const result = await createSimulation({ question });
    setSimulationId(result.simulation_id);
  };
  
  return (
    <div>
      <QuestionInput onSubmit={handleSubmit} />
      {simulationId && <SimulationResults simulationId={simulationId} />}
    </div>
  );
}

function SimulationResults({ simulationId }: { simulationId: string }) {
  const { data: dag } = useDAG(simulationId);
  const { data: hypotheses } = useHypotheses(simulationId);
  const { data: insights } = useInsights(simulationId);
  
  return (
    <>
      <DAGVisualization dag={dag} />
      <HypothesisTable hypotheses={hypotheses} />
      <InsightsList insights={insights} />
    </>
  );
}
```

## Next Steps

- See [data-model.md](./data-model.md) for complete database schema
- See [contracts/](./contracts/) for full API specifications
- Run `/speckit.tasks` to generate implementation task breakdown
