# Quickstart: Exploracao de Cenarios via LLM

Este guia mostra como usar a feature de exploracao de cenarios para encontrar melhorias em um produto.

## Pre-requisitos

1. Experimento criado com scorecard preenchido
2. Analise baseline executada (pelo menos uma simulacao completa)

## 1. Iniciar Exploracao

### Via API

```bash
curl -X POST http://localhost:8000/api/explorations \
  -H "Content-Type: application/json" \
  -d '{
    "experiment_id": "exp_12345678",
    "goal_value": 0.40,
    "beam_width": 3,
    "max_depth": 5
  }'
```

### Resposta

```json
{
  "id": "expl_abcd1234",
  "experiment_id": "exp_12345678",
  "baseline_analysis_id": "ana_87654321",
  "goal": {
    "metric": "success_rate",
    "operator": ">=",
    "value": 0.40
  },
  "status": "running",
  "current_depth": 0,
  "total_nodes": 1,
  "best_success_rate": 0.25
}
```

## 2. Executar Iteracoes

A exploracao pode ser executada de duas formas:

### Automatica (recomendado)

A API executa iteracoes automaticamente ate atingir a meta ou limite de recursos.

### Manual (para debug)

```bash
curl -X POST http://localhost:8000/api/explorations/expl_abcd1234/iterate
```

### Resposta de Iteracao

```json
{
  "exploration_id": "expl_abcd1234",
  "iteration_number": 1,
  "status": "running",
  "nodes_expanded": 1,
  "nodes_created": 2,
  "nodes_dominated": 0,
  "llm_calls_made": 1,
  "best_success_rate": 0.32,
  "frontier_size": 2
}
```

## 3. Verificar Status

```bash
curl http://localhost:8000/api/explorations/expl_abcd1234
```

### Status Possiveis

| Status | Significado |
|--------|-------------|
| `running` | Exploracao em andamento |
| `goal_achieved` | Meta atingida! |
| `depth_limit_reached` | Limite de profundidade atingido |
| `cost_limit_reached` | Limite de chamadas LLM atingido |
| `no_viable_paths` | Nenhum caminho viavel restante |

## 4. Obter Arvore Completa

```bash
curl http://localhost:8000/api/explorations/expl_abcd1234/tree
```

### Resposta

```json
{
  "exploration": { ... },
  "nodes": [
    {
      "id": "node_11111111",
      "parent_id": null,
      "depth": 0,
      "action_applied": null,
      "scorecard_params": {
        "complexity": 0.45,
        "initial_effort": 0.30,
        "perceived_risk": 0.25,
        "time_to_value": 0.40
      },
      "simulation_results": {
        "success_rate": 0.25,
        "fail_rate": 0.45,
        "did_not_try_rate": 0.30
      },
      "node_status": "dominated"
    },
    {
      "id": "node_22222222",
      "parent_id": "node_11111111",
      "depth": 1,
      "action_applied": "Adicionar tooltip contextual no fluxo",
      "action_category": "ux_interface",
      "rationale": "Reduz friccao cognitiva no momento de duvida",
      "scorecard_params": {
        "complexity": 0.43,
        "initial_effort": 0.30,
        "perceived_risk": 0.25,
        "time_to_value": 0.38
      },
      "simulation_results": {
        "success_rate": 0.32,
        "fail_rate": 0.40,
        "did_not_try_rate": 0.28
      },
      "node_status": "active"
    }
  ],
  "node_count_by_status": {
    "active": 2,
    "dominated": 3,
    "winner": 1,
    "expansion_failed": 0
  }
}
```

## 5. Obter Caminho Vencedor

Quando a exploracao atinge a meta:

```bash
curl http://localhost:8000/api/explorations/expl_abcd1234/winning-path
```

### Resposta

```json
{
  "exploration_id": "expl_abcd1234",
  "winner_node_id": "node_99999999",
  "path": [
    {
      "depth": 0,
      "action": null,
      "success_rate": 0.25,
      "delta_success_rate": 0.0
    },
    {
      "depth": 1,
      "action": "Adicionar tooltip contextual",
      "category": "ux_interface",
      "rationale": "Reduz friccao cognitiva",
      "success_rate": 0.32,
      "delta_success_rate": 0.07
    },
    {
      "depth": 2,
      "action": "Implementar default inteligente",
      "category": "flow",
      "rationale": "Reduz etapas manuais",
      "success_rate": 0.41,
      "delta_success_rate": 0.09
    }
  ],
  "total_improvement": 0.16
}
```

## 6. Consultar Catalogo de Acoes

```bash
curl http://localhost:8000/api/action-catalog
```

### Categorias Disponiveis

| Categoria | Descricao |
|-----------|-----------|
| `ux_interface` | Melhorias de interface (tooltips, feedback visual) |
| `onboarding` | Educacao do usuario (tutoriais, checklists) |
| `flow` | Otimizacao de fluxo (remover etapas, defaults) |
| `communication` | Feedback e mensagens (erros claros, confirmacoes) |
| `operational` | Controle de feature (rollout gradual, feature flags) |

## Exemplo Completo: Fluxo de Exploracao

```python
import httpx

BASE_URL = "http://localhost:8000"

# 1. Iniciar exploracao
response = httpx.post(f"{BASE_URL}/api/explorations", json={
    "experiment_id": "exp_12345678",
    "goal_value": 0.40,
    "beam_width": 3,
    "max_depth": 5
})
exploration = response.json()
exploration_id = exploration["id"]
print(f"Exploracao iniciada: {exploration_id}")

# 2. Aguardar conclusao (polling simples)
import time
while True:
    response = httpx.get(f"{BASE_URL}/api/explorations/{exploration_id}")
    status = response.json()["status"]
    print(f"Status: {status}, Best: {response.json()['best_success_rate']}")

    if status != "running":
        break
    time.sleep(5)

# 3. Se atingiu meta, obter caminho vencedor
if status == "goal_achieved":
    response = httpx.get(f"{BASE_URL}/api/explorations/{exploration_id}/winning-path")
    path = response.json()

    print("\n=== Caminho Vencedor ===")
    for step in path["path"]:
        if step["action"]:
            print(f"  → {step['action']}")
            print(f"    Categoria: {step['category']}")
            print(f"    Success rate: {step['success_rate']:.1%} (+{step['delta_success_rate']:.1%})")

    print(f"\nMelhoria total: +{path['total_improvement']:.1%}")
else:
    print(f"Exploracao encerrou sem atingir meta: {status}")
```

## Parametros de Configuracao

| Parametro | Default | Descricao |
|-----------|---------|-----------|
| `goal_value` | (obrigatorio) | Meta de success_rate (0-1) |
| `beam_width` | 3 | Cenarios mantidos por iteracao |
| `max_depth` | 5 | Profundidade maxima da arvore |
| `max_llm_calls` | 20 | Limite de chamadas LLM |
| `n_executions` | 100 | Execucoes Monte Carlo por simulacao |
| `seed` | null | Seed para reproducibilidade |

## Dicas

1. **Comece com defaults**: beam_width=3, max_depth=5 funciona bem para a maioria dos casos
2. **Use seed**: Para reproduzir resultados, sempre passe um seed
3. **Monitore custos**: max_llm_calls controla o custo total de LLM
4. **Analise nos dominados**: Eles mostram caminhos que nao funcionaram - insights valiosos
