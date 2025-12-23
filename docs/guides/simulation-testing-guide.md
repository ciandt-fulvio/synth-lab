# Manual de Testes - Feature Impact Simulation

Este guia explica como testar o sistema de simulação de impacto de features.

## Pré-requisitos

1. **Iniciar o servidor API:**
```bash
uv run uvicorn synth_lab.api.main:app --reload
```

2. **Verificar se há synths no banco:**
```bash
sqlite3 output/synthlab.db "SELECT COUNT(*) FROM synths;"
```

Se não houver synths, gere alguns primeiro:
```bash
uv run python -m synth_lab gensynth -n 20
```

---

## 1. Testar Cenários (Scenarios)

Os cenários estão definidos no arquivo `data/config/scenarios.json` na raiz do projeto.

### 1.1 Listar cenários disponíveis

```bash
curl -X GET http://localhost:8000/simulation/scenarios | jq
```

**Resposta esperada:**
```json
[
  {
    "id": "baseline",
    "name": "Baseline",
    "description": "Condicoes tipicas de uso",
    "motivation_modifier": 0.0,
    "trust_modifier": 0.0,
    "friction_modifier": 0.0,
    "task_criticality": 0.5
  },
  {
    "id": "crisis",
    "name": "Crise",
    "description": "Urgencia, precisa resolver rapido",
    ...
  },
  {
    "id": "first-use",
    "name": "Primeiro Uso",
    ...
  }
]
```

### 1.2 Obter cenário específico

```bash
curl -X GET http://localhost:8000/simulation/scenarios/baseline | jq
```

---

## 2. Testar Scorecards

### 2.1 Criar um scorecard

```bash
curl -X POST http://localhost:8000/simulation/scorecards \
  -H "Content-Type: application/json" \
  -d '{
    "feature_name": "Dark Mode",
    "use_scenario": "Usuário quer reduzir cansaço visual",
    "description_text": "Alternância entre tema claro e escuro na interface",
    "complexity": {"score": 0.3},
    "initial_effort": {"score": 0.2},
    "perceived_risk": {"score": 0.1},
    "time_to_value": {"score": 0.4}
  }' | jq
```

**Resposta esperada:**
```json
{
  "id": "abcd1234",
  "feature_name": "Dark Mode",
  "use_scenario": "Usuário quer reduzir cansaço visual",
  "description_text": "Alternância entre tema claro e escuro na interface",
  "complexity_score": 0.3,
  "initial_effort_score": 0.2,
  "perceived_risk_score": 0.1,
  "time_to_value_score": 0.4,
  "justification": null,
  "impact_hypotheses": [],
  "created_at": "2025-12-23T...",
  "updated_at": null
}
```

**Guarde o `id` retornado para os próximos testes!**

### 2.2 Listar scorecards

```bash
curl -X GET "http://localhost:8000/simulation/scorecards?limit=10" | jq
```

### 2.3 Obter scorecard por ID

```bash
# Substitua SCORECARD_ID pelo ID obtido na criação
curl -X GET http://localhost:8000/simulation/scorecards/SCORECARD_ID | jq
```

### 2.4 Gerar insights com LLM (opcional - requer OPENAI_API_KEY)

```bash
curl -X POST http://localhost:8000/simulation/scorecards/SCORECARD_ID/generate-insights \
  -H "Content-Type: application/json" \
  -d '{
    "generate_justification": true,
    "generate_hypotheses": true,
    "num_hypotheses": 3
  }' | jq
```

---

## 3. Testar Simulação Monte Carlo

### 3.1 Executar uma simulação

```bash
# Substitua SCORECARD_ID pelo ID do scorecard criado
curl -X POST http://localhost:8000/simulation/simulations \
  -H "Content-Type: application/json" \
  -d '{
    "scorecard_id": "SCORECARD_ID",
    "scenario_id": "baseline",
    "n_executions": 100,
    "sigma": 0.1,
    "seed": 42
  }' | jq
```

**Resposta esperada:**
```json
{
  "id": "sim_xyz12345",
  "scorecard_id": "SCORECARD_ID",
  "scenario_id": "baseline",
  "config": {
    "n_synths": 20,
    "n_executions": 100,
    "sigma": 0.1,
    "seed": 42
  },
  "status": "completed",
  "started_at": "2025-12-23T...",
  "completed_at": "2025-12-23T...",
  "total_synths": 20,
  "aggregated_outcomes": {
    "did_not_try": 0.35,
    "failed": 0.25,
    "success": 0.40
  },
  "execution_time_seconds": 0.05
}
```

### 3.2 Executar simulação com synths específicos

```bash
# Primeiro, obtenha IDs de synths do banco
sqlite3 output/synthlab.db "SELECT id FROM synths LIMIT 5;"

# Execute a simulação com synths específicos
curl -X POST http://localhost:8000/simulation/simulations \
  -H "Content-Type: application/json" \
  -d '{
    "scorecard_id": "SCORECARD_ID",
    "scenario_id": "crisis",
    "synth_ids": ["synth_id_1", "synth_id_2", "synth_id_3"],
    "n_executions": 50,
    "seed": 123
  }' | jq
```

### 3.3 Listar simulações

```bash
curl -X GET "http://localhost:8000/simulation/simulations?limit=10" | jq
```

### 3.4 Filtrar simulações por scorecard

```bash
curl -X GET "http://localhost:8000/simulation/simulations?scorecard_id=SCORECARD_ID" | jq
```

### 3.5 Obter simulação por ID

```bash
curl -X GET http://localhost:8000/simulation/simulations/SIMULATION_ID | jq
```

### 3.6 Obter outcomes por synth

```bash
curl -X GET "http://localhost:8000/simulation/simulations/SIMULATION_ID/outcomes?limit=50" | jq
```

**Resposta esperada:**
```json
{
  "outcomes": [
    {
      "synth_id": "synth_001",
      "did_not_try_rate": 0.32,
      "failed_rate": 0.28,
      "success_rate": 0.40,
      "synth_attributes": {
        "observables": {
          "digital_literacy": 0.45,
          "similar_tool_experience": 0.52,
          ...
        },
        "latent_traits": {
          "capability_mean": 0.48,
          "trust_mean": 0.51,
          ...
        }
      }
    },
    ...
  ],
  "total": 20,
  "limit": 50,
  "offset": 0
}
```

---

## 4. Comparar Cenários

Execute simulações com diferentes cenários para comparar:

```bash
# Cenário baseline
curl -X POST http://localhost:8000/simulation/simulations \
  -H "Content-Type: application/json" \
  -d '{"scorecard_id": "SCORECARD_ID", "scenario_id": "baseline", "n_executions": 100, "seed": 42}' | jq '.aggregated_outcomes'

# Cenário crise
curl -X POST http://localhost:8000/simulation/simulations \
  -H "Content-Type: application/json" \
  -d '{"scorecard_id": "SCORECARD_ID", "scenario_id": "crisis", "n_executions": 100, "seed": 42}' | jq '.aggregated_outcomes'

# Cenário primeiro uso
curl -X POST http://localhost:8000/simulation/simulations \
  -H "Content-Type: application/json" \
  -d '{"scorecard_id": "SCORECARD_ID", "scenario_id": "first-use", "n_executions": 100, "seed": 42}' | jq '.aggregated_outcomes'
```

**Interpretação esperada:**
- **Crisis**: Maior motivação, mas menor confiança → pode ter mais tentativas mas com mais falhas
- **First-use**: Menor criticidade, menor confiança → pode ter menos tentativas
- **Baseline**: Valores neutros → resultados intermediários

---

## 5. Analisar Regiões de Alto Risco

A análise de regiões identifica grupos de synths com características semelhantes que têm alta taxa de falha.

### 5.1 Executar análise de regiões

```bash
# Substitua SIMULATION_ID pelo ID de uma simulação completa
curl -X GET "http://localhost:8000/simulation/simulations/SIMULATION_ID/regions?min_failure_rate=0.5" | jq
```

**Parâmetros:**
- `min_failure_rate`: Taxa mínima de falha para identificar região problemática (default: 0.5)

**Resposta esperada:**
```json
{
  "regions": [
    {
      "id": "region_abc123",
      "simulation_id": "sim_xyz12345",
      "rules": [
        {
          "attribute": "capability_mean",
          "operator": "<=",
          "threshold": 0.48
        },
        {
          "attribute": "trust_mean",
          "operator": "<=",
          "threshold": 0.4
        }
      ],
      "rule_text": "capability_mean <= 0.48 AND trust_mean <= 0.4",
      "synth_count": 45,
      "synth_percentage": 22.5,
      "did_not_try_rate": 0.1,
      "failed_rate": 0.65,
      "success_rate": 0.25,
      "failure_delta": 0.15
    }
  ],
  "total": 3
}
```

**Interpretação:**
- `rule_text`: Regra interpretável que define o grupo
- `synth_count`: Quantidade de synths neste grupo
- `synth_percentage`: Percentual do total de synths
- `failed_rate`: Taxa de falha neste grupo (0.65 = 65%)
- `failure_delta`: Diferença em relação à média geral

### 5.2 Análise com diferentes thresholds

```bash
# Regiões com taxa de falha >= 60%
curl -X GET "http://localhost:8000/simulation/simulations/SIMULATION_ID/regions?min_failure_rate=0.6" | jq

# Regiões com taxa de falha >= 40%
curl -X GET "http://localhost:8000/simulation/simulations/SIMULATION_ID/regions?min_failure_rate=0.4" | jq
```

---

## 6. Comparar Simulações entre Cenários

Compare múltiplas simulações para identificar quais grupos de synths são mais sensíveis ao contexto.

### 6.1 Preparar simulações para comparação

Primeiro, execute simulações com o mesmo scorecard em diferentes cenários:

```bash
# Guardar os IDs das simulações retornadas
SIM_BASELINE=$(curl -s -X POST http://localhost:8000/simulation/simulations \
  -H "Content-Type: application/json" \
  -d '{"scorecard_id": "SCORECARD_ID", "scenario_id": "baseline", "n_executions": 100, "seed": 42}' | jq -r '.id')

SIM_CRISIS=$(curl -s -X POST http://localhost:8000/simulation/simulations \
  -H "Content-Type: application/json" \
  -d '{"scorecard_id": "SCORECARD_ID", "scenario_id": "crisis", "n_executions": 100, "seed": 42}' | jq -r '.id')

SIM_FIRST_USE=$(curl -s -X POST http://localhost:8000/simulation/simulations \
  -H "Content-Type: application/json" \
  -d '{"scorecard_id": "SCORECARD_ID", "scenario_id": "first-use", "n_executions": 100, "seed": 42}' | jq -r '.id')

echo "Baseline: $SIM_BASELINE"
echo "Crisis: $SIM_CRISIS"
echo "First-use: $SIM_FIRST_USE"
```

### 6.2 Comparar as simulações

```bash
curl -X POST http://localhost:8000/simulation/simulations/compare \
  -H "Content-Type: application/json" \
  -d "{\"simulation_ids\": [\"$SIM_BASELINE\", \"$SIM_CRISIS\", \"$SIM_FIRST_USE\"]}" | jq
```

**Resposta esperada:**
```json
{
  "simulations": [
    {
      "id": "sim_baseline",
      "scenario_id": "baseline",
      "aggregated_outcomes": {
        "did_not_try": 0.35,
        "failed": 0.25,
        "success": 0.40
      }
    },
    {
      "id": "sim_crisis",
      "scenario_id": "crisis",
      "aggregated_outcomes": {
        "did_not_try": 0.20,
        "failed": 0.35,
        "success": 0.45
      }
    },
    {
      "id": "sim_first_use",
      "scenario_id": "first-use",
      "aggregated_outcomes": {
        "did_not_try": 0.45,
        "failed": 0.30,
        "success": 0.25
      }
    }
  ],
  "most_affected_regions": [
    {
      "rule_text": "capability_mean <= 0.48 AND trust_mean <= 0.4",
      "outcomes_by_scenario": {
        "baseline": 0.65,
        "crisis": 0.75,
        "first-use": 0.80
      }
    }
  ]
}
```

**Interpretação:**
- `simulations`: Resultados agregados de cada simulação
- `most_affected_regions`: Grupos de synths com maior variação entre cenários
- `outcomes_by_scenario`: Taxa de falha de cada região por cenário

### 6.3 Comparação com 2 simulações (mínimo)

```bash
curl -X POST http://localhost:8000/simulation/simulations/compare \
  -H "Content-Type: application/json" \
  -d "{\"simulation_ids\": [\"$SIM_BASELINE\", \"$SIM_CRISIS\"]}" | jq
```

**Validação:**
- Mínimo: 2 simulações
- Máximo: 5 simulações
- Todas devem existir no banco de dados

---

## 7. Análise de Sensibilidade (OAT)

Identifica qual dimensão do scorecard tem maior impacto nos resultados.

### 7.1 Executar análise de sensibilidade

```bash
# Análise com deltas padrão (±0.05, ±0.10)
curl -X GET "http://localhost:8000/simulation/simulations/SIMULATION_ID/sensitivity" | jq
```

**Resposta esperada:**
```json
{
  "simulation_id": "sim_xyz12345",
  "analyzed_at": "2025-12-23T20:30:00Z",
  "deltas_used": [0.05, 0.10],
  "dimensions": [
    {
      "dimension": "complexity",
      "baseline_value": 0.4,
      "deltas_tested": [-0.1, -0.05, 0.05, 0.1],
      "outcomes_by_delta": {
        "-0.1": {"did_not_try": 0.30, "failed": 0.20, "success": 0.50},
        "-0.05": {"did_not_try": 0.32, "failed": 0.23, "success": 0.45},
        "0.05": {"did_not_try": 0.38, "failed": 0.28, "success": 0.34},
        "0.1": {"did_not_try": 0.42, "failed": 0.33, "success": 0.25}
      },
      "sensitivity_index": 2.5,
      "rank": 1
    },
    {
      "dimension": "perceived_risk",
      "baseline_value": 0.2,
      "sensitivity_index": 1.8,
      "rank": 2
    },
    {
      "dimension": "initial_effort",
      "sensitivity_index": 1.2,
      "rank": 3
    },
    {
      "dimension": "time_to_value",
      "sensitivity_index": 0.9,
      "rank": 4
    }
  ]
}
```

**Interpretação:**
- `rank`: 1 = dimensão mais sensível, 4 = menos sensível
- `sensitivity_index`: (% mudança no output) / (% mudança no input)
- `outcomes_by_delta`: Resultados para cada variação testada
- Dimensão com rank 1 tem maior impacto → priorizar ajustes nela

### 7.2 Análise com deltas customizados

```bash
# Testar apenas variações pequenas (±0.05)
curl -X GET "http://localhost:8000/simulation/simulations/SIMULATION_ID/sensitivity?deltas=0.05" | jq

# Testar variações maiores (±0.05, ±0.15)
curl -X GET "http://localhost:8000/simulation/simulations/SIMULATION_ID/sensitivity?deltas=0.05,0.15" | jq
```

**Observações:**
- Análise cria simulações adicionais para cada variação
- Para 4 dimensões com 2 deltas: 16 simulações adicionais (4 × 2 × 2 direções)
- Pode levar alguns segundos para completar

---

## 8. Validar Componentes Individualmente

### 8.1 Validar sample_state

```bash
uv run python src/synth_lab/services/simulation/sample_state.py
```

### 8.2 Validar probability

```bash
uv run python src/synth_lab/services/simulation/probability.py
```

### 8.3 Validar Monte Carlo engine

```bash
uv run python src/synth_lab/services/simulation/engine.py
```

### 8.4 Validar simulation repository

```bash
uv run python src/synth_lab/repositories/simulation_repository.py
```

### 8.5 Validar simulation service

```bash
uv run python src/synth_lab/services/simulation/simulation_service.py
```

### 8.6 Validar scenario loader

```bash
uv run python src/synth_lab/services/simulation/scenario_loader.py
```

### 8.7 Validar region analyzer

```bash
uv run python src/synth_lab/services/simulation/analyzer.py
```

### 8.8 Validar comparison service

```bash
uv run python src/synth_lab/services/simulation/comparison_service.py
```

### 8.9 Validar sensitivity analyzer

```bash
uv run python src/synth_lab/services/simulation/sensitivity.py
```

### 8.10 Validar API router

```bash
uv run python src/synth_lab/api/routers/simulation.py
```

---

## 9. Testes via Python

### 9.1 Script de teste completo

```python
"""
Teste completo do sistema de simulação.
Execute com: uv run python docs/guides/test_simulation.py
"""
import requests

BASE_URL = "http://localhost:8000/simulation"

# 1. Criar scorecard
print("1. Criando scorecard...")
scorecard_response = requests.post(f"{BASE_URL}/scorecards", json={
    "feature_name": "Teste Automático",
    "use_scenario": "Validação do sistema",
    "description_text": "Feature criada para teste automatizado",
    "complexity": {"score": 0.4},
    "initial_effort": {"score": 0.3},
    "perceived_risk": {"score": 0.2},
    "time_to_value": {"score": 0.5}
})
scorecard = scorecard_response.json()
scorecard_id = scorecard["id"]
print(f"   Scorecard criado: {scorecard_id}")

# 2. Listar cenários
print("\n2. Listando cenários...")
scenarios = requests.get(f"{BASE_URL}/scenarios").json()
print(f"   Cenários disponíveis: {[s['id'] for s in scenarios]}")

# 3. Executar simulação baseline
print("\n3. Executando simulação baseline...")
sim_response = requests.post(f"{BASE_URL}/simulations", json={
    "scorecard_id": scorecard_id,
    "scenario_id": "baseline",
    "n_executions": 100,
    "seed": 42
})
simulation = sim_response.json()
print(f"   Status: {simulation['status']}")
print(f"   Synths: {simulation['total_synths']}")
print(f"   Tempo: {simulation['execution_time_seconds']:.3f}s")
print(f"   Resultados: {simulation['aggregated_outcomes']}")

# 4. Obter outcomes detalhados
print("\n4. Obtendo outcomes por synth...")
sim_id = simulation["id"]
outcomes = requests.get(f"{BASE_URL}/simulations/{sim_id}/outcomes?limit=5").json()
print(f"   Total outcomes: {outcomes['total']}")
for o in outcomes["outcomes"][:3]:
    print(f"   - {o['synth_id']}: success={o['success_rate']:.2f}")

# 5. Comparar cenários
print("\n5. Comparando cenários...")
for scenario_id in ["baseline", "crisis", "first-use"]:
    sim = requests.post(f"{BASE_URL}/simulations", json={
        "scorecard_id": scorecard_id,
        "scenario_id": scenario_id,
        "n_executions": 100,
        "seed": 42
    }).json()
    agg = sim["aggregated_outcomes"]
    print(f"   {scenario_id:12} → success={agg['success']:.3f}, did_not_try={agg['did_not_try']:.3f}")

print("\n✅ Todos os testes completados com sucesso!")
```

### 9.2 Script de teste avançado (com análises)

```python
"""
Teste completo incluindo análises avançadas.
Execute com: uv run python docs/guides/test_advanced_simulation.py
"""
import requests
import time

BASE_URL = "http://localhost:8000/simulation"

# 1. Criar scorecard
print("1. Criando scorecard...")
scorecard_response = requests.post(f"{BASE_URL}/scorecards", json={
    "feature_name": "Teste Completo",
    "use_scenario": "Validação com análises",
    "description_text": "Feature para teste de análises avançadas",
    "complexity": {"score": 0.6},
    "initial_effort": {"score": 0.4},
    "perceived_risk": {"score": 0.3},
    "time_to_value": {"score": 0.5}
})
scorecard_id = scorecard_response.json()["id"]
print(f"   Scorecard: {scorecard_id}")

# 2. Executar simulações em diferentes cenários
print("\n2. Executando simulações...")
sim_ids = {}
for scenario in ["baseline", "crisis", "first-use"]:
    sim = requests.post(f"{BASE_URL}/simulations", json={
        "scorecard_id": scorecard_id,
        "scenario_id": scenario,
        "n_executions": 100,
        "seed": 42
    }).json()
    sim_ids[scenario] = sim["id"]
    print(f"   {scenario}: {sim['id']} (success={sim['aggregated_outcomes']['success']:.3f})")

# 3. Análise de regiões
print("\n3. Analisando regiões de risco...")
regions = requests.get(
    f"{BASE_URL}/simulations/{sim_ids['baseline']}/regions?min_failure_rate=0.5"
).json()
print(f"   Regiões encontradas: {regions['total']}")
if regions['total'] > 0:
    top_region = regions['regions'][0]
    print(f"   Região crítica: {top_region['rule_text']}")
    print(f"   Taxa de falha: {top_region['failed_rate']:.3f}")

# 4. Comparação de cenários
print("\n4. Comparando cenários...")
comparison = requests.post(f"{BASE_URL}/simulations/compare", json={
    "simulation_ids": list(sim_ids.values())
}).json()
print(f"   Simulações comparadas: {len(comparison['simulations'])}")
print(f"   Regiões afetadas: {len(comparison['most_affected_regions'])}")

# 5. Análise de sensibilidade
print("\n5. Analisando sensibilidade...")
print("   (Aguarde - criando 16 simulações adicionais...)")
start = time.time()
sensitivity = requests.get(
    f"{BASE_URL}/simulations/{sim_ids['baseline']}/sensitivity?deltas=0.05"
).json()
elapsed = time.time() - start
print(f"   Tempo: {elapsed:.1f}s")

# Mostrar ranking
print("\n   Ranking de dimensões por impacto:")
for dim in sensitivity['dimensions']:
    print(f"   {dim['rank']}. {dim['dimension']:20} (índice: {dim['sensitivity_index']:.2f})")

print("\n✅ Teste avançado completo!")
```

Salve e execute:
```bash
uv run python docs/guides/test_advanced_simulation.py
```

---

## 10. Verificar Dados no Banco

```bash
# Ver scorecards
sqlite3 output/synthlab.db "SELECT id, json_extract(data, '$.identification.feature_name') as name FROM scorecards LIMIT 5;"

# Ver simulações
sqlite3 output/synthlab.db "SELECT id, scorecard_id, scenario_id, status, total_synths FROM simulation_runs ORDER BY started_at DESC LIMIT 5;"

# Ver outcomes de uma simulação
sqlite3 output/synthlab.db "SELECT synth_id, success_rate FROM synth_outcomes WHERE simulation_id='SIMULATION_ID' LIMIT 10;"

# Ver análises de região
sqlite3 output/synthlab.db "SELECT id, simulation_id, rule_text, failed_rate FROM region_analyses ORDER BY failed_rate DESC LIMIT 5;"

# Contar registros
sqlite3 output/synthlab.db "SELECT 'scorecards' as table_name, COUNT(*) as count FROM scorecards UNION ALL SELECT 'simulation_runs', COUNT(*) FROM simulation_runs UNION ALL SELECT 'synth_outcomes', COUNT(*) FROM synth_outcomes UNION ALL SELECT 'region_analyses', COUNT(*) FROM region_analyses;"
```

---

## 11. Troubleshooting

### Erro: "Scorecard not found"
- Verifique se o ID do scorecard está correto
- Liste os scorecards existentes: `curl http://localhost:8000/simulation/scorecards | jq`

### Erro: "Scenario not found"
- Use apenas: `baseline`, `crisis`, ou `first-use`
- Verifique cenários disponíveis: `curl http://localhost:8000/simulation/scenarios | jq`

### Erro: "No synths found"
- Gere synths primeiro: `uv run python -m synth_lab gensynth -n 20`

### Simulação muito lenta
- Reduza `n_executions` (mínimo: 10)
- Use menos synths via `synth_ids`

### Análise de sensibilidade demorando muito
- Use menos deltas: `?deltas=0.05` em vez de `?deltas=0.05,0.10`
- Para 2 deltas: cria 16 simulações (4 dims × 2 deltas × 2 direções)
- Para 1 delta: cria 8 simulações (4 dims × 1 delta × 2 direções)
- Considere usar simulações com menos executions no baseline

### Erro: "Not enough outcomes for region analysis"
- A análise de regiões precisa de pelo menos 40 synths
- Execute simulação com mais synths (min 50 recomendado)
- Ou use `synth_ids` específicos para garantir quantidade mínima

### Verificar logs
```bash
# Os logs aparecem no terminal onde o servidor está rodando
# Ou verifique o arquivo de log se configurado
```
