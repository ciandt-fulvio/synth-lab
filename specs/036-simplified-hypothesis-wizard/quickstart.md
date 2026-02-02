# Quickstart Guide: Simplified Hypothesis Wizard

**Feature**: 036-simplified-hypothesis-wizard
**Audience**: Developers integrating with the hypothesis wizard API
**Last Updated**: 2026-01-28

## Overview

The Simplified Hypothesis Wizard guides users through hypothesis generation in 3 simple steps:

1. **Select Scenario Profile** (Conservative/Realistic/Optimistic)
2. **Answer Clarification Questions** (3-5 qualitative questions)
3. **Review & Run Simulation**

This guide shows how to use the wizard API endpoints.

## Prerequisites

- Simulation must exist (`POST /api/simulations`)
- CausalDAG must be validated (`POST /api/simulations/{id}/dag/validate`)

## Step 1: Initialize Wizard with Scenario Profile

**Endpoint**: `POST /api/simulations/{simulation_id}/hypotheses/wizard/init`

**Request**:
```bash
curl -X POST http://localhost:8000/api/simulations/sim_12345678/hypotheses/wizard/init \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_profile": "realistic"
  }'
```

**Scenario Profile Options**:
- `conservative` - Worse-than-average outcomes, higher uncertainty
- `realistic` - Market-average parameters (recommended default)
- `optimistic` - Better-than-average outcomes, lower uncertainty

**Response** (200 OK):
```json
{
  "hypotheses": [
    {
      "id": "hyp_a1b2c3d4",
      "simulation_id": "sim_12345678",
      "variable_name": "conversion_rate",
      "distribution_type": "beta",
      "distrib_params": {
        "alpha": 15.0,
        "beta": 85.0
      },
      "range_min": 0.0,
      "range_max": 1.0,
      "correlations": null,
      "scenario_options": null,
      "selected_scenario": null,
      "created_at": "2026-01-28T10:00:00Z",
      "updated_at": "2026-01-28T10:00:00Z"
    },
    {
      "id": "hyp_b2c3d4e5",
      "simulation_id": "sim_12345678",
      "variable_name": "churn_rate",
      "distribution_type": "beta",
      "distrib_params": {
        "alpha": 20.0,
        "beta": 80.0
      },
      "range_min": 0.0,
      "range_max": 1.0,
      "correlations": null,
      "scenario_options": null,
      "selected_scenario": null,
      "created_at": "2026-01-28T10:00:00Z",
      "updated_at": "2026-01-28T10:00:00Z"
    }
  ],
  "clarification_questions": [
    {
      "variable_name": "conversion_rate",
      "question_text": "Conversion rate is more common or more rare in your context?",
      "criticality_score": 8.5
    },
    {
      "variable_name": "churn_rate",
      "question_text": "Churn rate is more common or more rare in your context?",
      "criticality_score": 7.2
    },
    {
      "variable_name": "acquisition_cost",
      "question_text": "Acquisition cost tends to be higher or lower than average?",
      "criticality_score": 6.8
    }
  ]
}
```

**What Happens**:
1. Wizard loads CausalDAG for the simulation
2. LLM generates baseline hypotheses with scenario profile hints
3. Profile adjustments applied to all distributions (Conservative = lower means/higher variance, etc.)
4. Wizard identifies 3-5 critical variables (high impact × high uncertainty)
5. Clarification questions generated from variable metadata
6. Hypotheses persisted to database (ready for simulation if user skips clarifications)

**Error Responses**:
- `404` - Simulation or CausalDAG not found
- `422` - DAG not validated or invalid scenario profile
- `500` - LLM failure or internal error

## Step 2: Apply Clarification Responses (Optional)

**Endpoint**: `POST /api/simulations/{simulation_id}/hypotheses/wizard/clarify`

Users can answer some, all, or none of the clarification questions.

### Example 1: Answer All Questions

**Request**:
```bash
curl -X POST http://localhost:8000/api/simulations/sim_12345678/hypotheses/wizard/clarify \
  -H "Content-Type: application/json" \
  -d '{
    "responses": [
      {
        "variable_name": "conversion_rate",
        "response": "more"
      },
      {
        "variable_name": "churn_rate",
        "response": "less"
      },
      {
        "variable_name": "acquisition_cost",
        "response": "equal"
      }
    ]
  }'
```

**Response Options**:
- `more` - Higher frequency/magnitude than expected (shifts mean up, reduces variance)
- `less` - Lower frequency/magnitude than expected (shifts mean down, reduces variance)
- `equal` - Matches expectation (keeps profile defaults)
- `dont_know` - High uncertainty (keeps mean, increases variance)

**Response** (200 OK):
```json
{
  "hypotheses": [
    {
      "id": "hyp_a1b2c3d4",
      "simulation_id": "sim_12345678",
      "variable_name": "conversion_rate",
      "distribution_type": "beta",
      "distrib_params": {
        "alpha": 19.5,
        "beta": 68.0
      },
      "range_min": 0.0,
      "range_max": 1.0,
      "correlations": null,
      "scenario_options": null,
      "selected_scenario": null,
      "created_at": "2026-01-28T10:00:00Z",
      "updated_at": "2026-01-28T10:05:00Z"
    },
    {
      "id": "hyp_b2c3d4e5",
      "simulation_id": "sim_12345678",
      "variable_name": "churn_rate",
      "distribution_type": "beta",
      "distrib_params": {
        "alpha": 26.0,
        "beta": 64.0
      },
      "range_min": 0.0,
      "range_max": 1.0,
      "correlations": null,
      "scenario_options": null,
      "selected_scenario": null,
      "created_at": "2026-01-28T10:00:00Z",
      "updated_at": "2026-01-28T10:05:00Z"
    }
  ]
}
```

### Example 2: Skip All Questions

**Request**:
```bash
curl -X POST http://localhost:8000/api/simulations/sim_12345678/hypotheses/wizard/clarify \
  -H "Content-Type: application/json" \
  -d '{
    "responses": []
  }'
```

**Response** (200 OK):
```json
{
  "hypotheses": [
    // Same as from /wizard/init (no adjustments)
  ]
}
```

### Example 3: Answer Some Questions

**Request**:
```bash
curl -X POST http://localhost:8000/api/simulations/sim_12345678/hypotheses/wizard/clarify \
  -H "Content-Type: application/json" \
  -d '{
    "responses": [
      {
        "variable_name": "conversion_rate",
        "response": "more"
      }
    ]
  }'
```

**Response** (200 OK):
```json
{
  "hypotheses": [
    // conversion_rate adjusted, other variables unchanged
  ]
}
```

**What Happens**:
1. Wizard loads existing hypotheses for the simulation
2. For each response, applies distribution adjustments based on response type
3. Updates hypotheses in database
4. Returns updated hypotheses (ready for simulation)

**Error Responses**:
- `404` - Simulation or hypotheses not found
- `422` - Invalid response type or variable not found in DAG
- `500` - Internal error

## Step 3: Run Simulation

After wizard completion, hypotheses are ready for simulation.

**Endpoint**: `POST /api/simulations/{simulation_id}/run` (existing endpoint)

```bash
curl -X POST http://localhost:8000/api/simulations/sim_12345678/run \
  -H "Content-Type: application/json"
```

**Response** (200 OK):
```json
{
  "simulation_id": "sim_12345678",
  "status": "running",
  "started_at": "2026-01-28T10:10:00Z"
}
```

## Complete Example Flow

```bash
# 1. Create simulation (existing endpoint)
SIM_ID=$(curl -X POST http://localhost:8000/api/simulations \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How will new pricing affect churn and revenue?",
    "problem_decomposition": { ... }
  }' | jq -r '.id')

# 2. Generate and validate DAG (existing endpoints)
curl -X POST http://localhost:8000/api/simulations/$SIM_ID/dag/generate
curl -X POST http://localhost:8000/api/simulations/$SIM_ID/dag/validate

# 3. Initialize wizard with realistic scenario
curl -X POST http://localhost:8000/api/simulations/$SIM_ID/hypotheses/wizard/init \
  -H "Content-Type: application/json" \
  -d '{ "scenario_profile": "realistic" }'

# 4. Apply clarifications
curl -X POST http://localhost:8000/api/simulations/$SIM_ID/hypotheses/wizard/clarify \
  -H "Content-Type: application/json" \
  -d '{
    "responses": [
      { "variable_name": "conversion_rate", "response": "more" },
      { "variable_name": "churn_rate", "response": "less" }
    ]
  }'

# 5. Run simulation (existing endpoint)
curl -X POST http://localhost:8000/api/simulations/$SIM_ID/run
```

## Integration with Existing Hypothesis Endpoints

Wizard-generated hypotheses are compatible with all existing hypothesis endpoints:

### Get Hypotheses
```bash
GET /api/simulations/{simulation_id}/hypotheses
```

Returns wizard-generated hypotheses (same schema as manually-edited).

### Update Single Hypothesis
```bash
PUT /api/simulations/{simulation_id}/hypotheses/{hypothesis_id}
```

Allows manual override of wizard-generated parameters (power user feature).

### Save Hypothesis Version
```bash
POST /api/simulations/{simulation_id}/hypotheses/versions
```

Saves snapshot of wizard-generated hypotheses for comparison (e.g., Conservative vs Optimistic).

## Frontend Integration Example

```typescript
// 1. Initialize wizard
const initWizard = async (simulationId: string, profile: ScenarioProfile) => {
  const response = await fetch(
    `/api/simulations/${simulationId}/hypotheses/wizard/init`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario_profile: profile }),
    }
  );
  return response.json(); // { hypotheses, clarification_questions }
};

// 2. Apply clarifications
const applyClarifications = async (
  simulationId: string,
  responses: ClarificationResponse[]
) => {
  const response = await fetch(
    `/api/simulations/${simulationId}/hypotheses/wizard/clarify`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ responses }),
    }
  );
  return response.json(); // { hypotheses }
};

// 3. Use in React component
const HypothesisWizard = ({ simulationId }: Props) => {
  const [profile, setProfile] = useState<ScenarioProfile>('realistic');
  const [questions, setQuestions] = useState<ClarificationQuestion[]>([]);
  const [responses, setResponses] = useState<ClarificationResponse[]>([]);

  const handleInit = async () => {
    const result = await initWizard(simulationId, profile);
    setQuestions(result.clarification_questions);
  };

  const handleClarify = async () => {
    await applyClarifications(simulationId, responses);
    // Navigate to simulation results or hypothesis review
  };

  // ... UI rendering
};
```

## Testing

### Test Scenario Profile Selection

```bash
# Conservative profile (worse outcomes, higher uncertainty)
curl -X POST http://localhost:8000/api/simulations/sim_test/hypotheses/wizard/init \
  -d '{ "scenario_profile": "conservative" }'

# Optimistic profile (better outcomes, lower uncertainty)
curl -X POST http://localhost:8000/api/simulations/sim_test/hypotheses/wizard/init \
  -d '{ "scenario_profile": "optimistic" }'
```

Compare `distrib_params` between profiles:
- Conservative: lower means (for positive variables), higher variance
- Optimistic: higher means, lower variance

### Test Clarification Mapping

```bash
# Generate baseline
curl -X POST http://localhost:8000/api/simulations/sim_test/hypotheses/wizard/init \
  -d '{ "scenario_profile": "realistic" }'

# Apply "more" response
curl -X POST http://localhost:8000/api/simulations/sim_test/hypotheses/wizard/clarify \
  -d '{
    "responses": [
      { "variable_name": "conversion_rate", "response": "more" }
    ]
  }'
```

Verify Beta distribution adjusted (α increased, β decreased for higher success rate).

## Troubleshooting

**Problem**: `422 Validation Error - DAG not validated`
- **Solution**: Run `POST /api/simulations/{id}/dag/validate` before wizard

**Problem**: `404 Simulation not found`
- **Solution**: Verify simulation ID exists with `GET /api/simulations/{id}`

**Problem**: `422 Variable not found in DAG`
- **Solution**: Ensure `variable_name` in clarification response matches DAG node name

**Problem**: No clarification questions returned
- **Cause**: All variables have low uncertainty (no critical uncertainties detected)
- **Action**: Proceed to simulation - no clarifications needed

**Problem**: LLM timeout (500 error)
- **Cause**: OpenAI API slow or unavailable
- **Solution**: Retry request or check OpenAI service status

## Next Steps

- **Review hypotheses**: Use `GET /api/simulations/{id}/hypotheses` to inspect generated distributions
- **Manual override**: Use `PUT /api/simulations/{id}/hypotheses/{hyp_id}` to adjust specific parameters
- **Save version**: Use `POST /api/simulations/{id}/hypotheses/versions` to snapshot for comparison
- **Run simulation**: Use `POST /api/simulations/{id}/run` to execute simulation

## API Reference

Full OpenAPI specification: [contracts/openapi.yaml](contracts/openapi.yaml)

Interactive API docs (when server running):
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
