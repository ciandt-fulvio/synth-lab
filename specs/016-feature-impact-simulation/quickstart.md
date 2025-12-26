# Quickstart: Sistema de Simulação de Impacto de Features

Guia rápido para usar o sistema de simulação de impacto de features no synth-lab.

## Pré-requisitos

```bash
# Certifique-se de ter synths no banco de dados
uv run python -m synth_lab.gen_synth.gen_synth -n 500
```

## 1. Gerar Synths com Atributos de Simulação

Os synths gerados após esta feature incluem automaticamente atributos de simulação:

```python
from synth_lab.gen_synth.gen_synth import main as generate_synths

# Gera 500 synths com simulation_attributes
synths = generate_synths(quantidade=500)

# Cada synth agora tem:
print(synths[0]["simulation_attributes"])
# {
#   "observables": {
#     "digital_literacy": 0.35,
#     "similar_tool_experience": 0.42,
#     "motor_ability": 0.85,
#     "time_availability": 0.28,
#     "domain_expertise": 0.55
#   },
#   "latent_traits": {
#     "capability_mean": 0.42,
#     "trust_mean": 0.39,
#     "friction_tolerance_mean": 0.35,
#     "exploration_prob": 0.38
#   }
# }
```

## 2. Criar um Feature Scorecard

### Via API REST

```bash
curl -X POST http://localhost:8000/api/v1/scorecards \
  -H "Content-Type: application/json" \
  -d '{
    "feature_name": "Novo Fluxo de Onboarding",
    "use_scenario": "Primeiro acesso ao produto",
    "evaluators": ["PM: João", "UX: Maria"],
    "description_text": "Fluxo de onboarding simplificado com 3 passos",
    "complexity": {
      "score": 0.4,
      "rules_applied": ["2 conceitos novos"],
      "min_uncertainty": 0.3,
      "max_uncertainty": 0.5
    },
    "initial_effort": {
      "score": 0.3,
      "rules_applied": ["uso imediato sem configuração"],
      "min_uncertainty": 0.2,
      "max_uncertainty": 0.4
    },
    "perceived_risk": {
      "score": 0.2,
      "rules_applied": ["não afeta dados"],
      "min_uncertainty": 0.1,
      "max_uncertainty": 0.3
    },
    "time_to_value": {
      "score": 0.5,
      "rules_applied": ["valor percebido em 2 minutos"],
      "min_uncertainty": 0.4,
      "max_uncertainty": 0.6
    }
  }'
```

### Via Python

```python
from synth_lab.services.simulation.scorecard_service import create_scorecard

scorecard = create_scorecard(
    feature_name="Novo Fluxo de Onboarding",
    use_scenario="Primeiro acesso ao produto",
    complexity={"score": 0.4, "rules_applied": ["2 conceitos novos"]},
    initial_effort={"score": 0.3, "rules_applied": ["uso imediato"]},
    perceived_risk={"score": 0.2, "rules_applied": ["não afeta dados"]},
    time_to_value={"score": 0.5, "rules_applied": ["valor em 2 min"]}
)
print(f"Scorecard criado: {scorecard.id}")
```

## 3. Gerar Insights via LLM

```bash
curl -X POST http://localhost:8000/api/v1/scorecards/{scorecard_id}/generate-insights
```

Resposta:
```json
{
  "justification": "O fluxo tem complexidade moderada (2 conceitos novos) mas baixo esforço inicial...",
  "impact_hypotheses": [
    "Synths com baixa digital_literacy terão dificuldade nos conceitos novos",
    "Tempo até valor de 2 min pode frustrar synths com pouco time_availability"
  ],
  "suggested_adjustments": [
    "Reduzir para 1 conceito novo no primeiro contato",
    "Adicionar indicador de progresso para synths impacientes"
  ]
}
```

## 4. Executar Simulação

### Cenários Disponíveis

| Cenário | Descrição |
|---------|-----------|
| `baseline` | Condições típicas de uso |
| `crisis` | Urgência, precisa resolver rápido |
| `first-use` | Exploração inicial do produto |

### Executar

```bash
curl -X POST http://localhost:8000/api/v1/simulations \
  -H "Content-Type: application/json" \
  -d '{
    "scorecard_id": "abc12345",
    "scenario_id": "baseline",
    "config": {
      "n_synths": 500,
      "n_executions": 100,
      "sigma": 0.05,
      "seed": 42
    }
  }'
```

Resposta (simulação iniciada):
```json
{
  "id": "sim_xyz78901",
  "status": "running",
  "started_at": "2025-12-23T10:30:00Z"
}
```

### Verificar Status

```bash
curl http://localhost:8000/api/v1/simulations/sim_xyz78901
```

Resposta (completa):
```json
{
  "id": "sim_xyz78901",
  "status": "completed",
  "completed_at": "2025-12-23T10:30:25Z",
  "execution_time_seconds": 25.3,
  "total_synths": 500,
  "aggregated_outcomes": {
    "did_not_try": 0.22,
    "failed": 0.38,
    "success": 0.40
  }
}
```

## 5. Analisar Resultados

### Ver Outcomes por Synth

```bash
curl "http://localhost:8000/api/v1/simulations/sim_xyz78901/outcomes?limit=10"
```

### Identificar Regiões de Falha

```bash
curl "http://localhost:8000/api/v1/simulations/sim_xyz78901/regions?min_failure_rate=0.5"
```

Resposta:
```json
[
  {
    "rule_text": "capability_mean < 0.35 AND trust_mean < 0.40",
    "synth_count": 87,
    "synth_percentage": 17.4,
    "failed_rate": 0.68,
    "failure_delta": 0.30
  },
  {
    "rule_text": "digital_literacy < 0.30",
    "synth_count": 112,
    "synth_percentage": 22.4,
    "failed_rate": 0.55,
    "failure_delta": 0.17
  }
]
```

### Análise de Sensibilidade

```bash
curl "http://localhost:8000/api/v1/simulations/sim_xyz78901/sensitivity?deltas=0.05,0.10"
```

Resposta:
```json
{
  "most_sensitive_dimension": "complexity",
  "dimensions": [
    {
      "dimension": "complexity",
      "sensitivity_index": 1.45,
      "rank": 1,
      "outcomes_by_delta": {
        "-0.10": {"success": 0.52},
        "+0.10": {"success": 0.28}
      }
    },
    {
      "dimension": "time_to_value",
      "sensitivity_index": 0.82,
      "rank": 2
    }
  ]
}
```

## 6. Comparar Cenários

Execute simulações em múltiplos cenários e compare:

```bash
# Execute para cada cenário
curl -X POST http://localhost:8000/api/v1/simulations \
  -d '{"scorecard_id": "abc12345", "scenario_id": "baseline"}'
curl -X POST http://localhost:8000/api/v1/simulations \
  -d '{"scorecard_id": "abc12345", "scenario_id": "crisis"}'
curl -X POST http://localhost:8000/api/v1/simulations \
  -d '{"scorecard_id": "abc12345", "scenario_id": "first-use"}'

# Compare resultados
curl -X POST http://localhost:8000/api/v1/simulations/compare \
  -d '{"simulation_ids": ["sim_baseline", "sim_crisis", "sim_firstuse"]}'
```

## 7. Consultar Histórico

```bash
curl "http://localhost:8000/api/v1/audit/log?scorecard_id=abc12345&limit=20"
```

---

## Fluxo Típico de Uso

```
1. Gerar synths com atributos de simulação
   └── uv run python -m synth_lab.gen_synth.gen_synth -n 500

2. Criar scorecard da feature
   └── POST /api/v1/scorecards

3. Gerar insights via LLM (opcional)
   └── POST /api/v1/scorecards/{id}/generate-insights

4. Executar simulação em baseline
   └── POST /api/v1/simulations

5. Analisar regiões de falha
   └── GET /api/v1/simulations/{id}/regions

6. Identificar variável mais sensível
   └── GET /api/v1/simulations/{id}/sensitivity

7. Comparar com outros cenários
   └── POST /api/v1/simulations/compare

8. Ajustar feature e re-simular
   └── Repetir ciclo
```

## Dicas

- **Performance**: Simulação de 500 synths × 100 execuções leva ~25 segundos
- **Reprodutibilidade**: Use `seed` fixo para resultados idênticos
- **Interpretação**: Foque em regiões com `failure_delta > 0.2` (20% pior que média)
- **Sensibilidade**: Comece ajustando a dimensão com maior `sensitivity_index`
