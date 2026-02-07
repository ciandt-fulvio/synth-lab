# Research: Mechanism & Sensitivity Update

**Feature**: 040-mechanism-sensitivity-update
**Date**: 2026-02-06

## RQ-001: Arquitetura do Novo Motor de Simulação (Substituindo Scorecard)

### Decisão

Substituir o motor de simulação baseado em scorecard (`engine.py` / `probability.py` / `sample_state.py`) por um motor baseado exclusivamente em mecanismos × sensibilidades com distribuições Beta.

### Racional

O motor atual (`MonteCarloEngine`) depende de:
1. **Scorecard dimensions** (complexity, initial_effort, perceived_risk, time_to_value) — estimadas via LLM
2. **Latent traits** (capability_mean, trust_mean, friction_tolerance_mean, exploration_prob) — derivadas de observáveis
3. **Observables** (digital_literacy, similar_tool_experience, motor_ability, time_availability, domain_expertise) — geradas no synth builder

O novo motor substitui toda essa cadeia por:
1. **9 mecanismos** (cada um com distribuição Beta parametrizada pelo mean selecionado pelo usuário)
2. **7 sensibilidades** (derivadas da demografia via YAML rules, persistidas no synth)
3. **9 estados emergentes** (mecanismo × sensibilidade → barriers e appeals)
4. **Probabilidade ajustada** = base − barrier_penalty + appeal_boost, clamped [0,1]

### Alternativas Consideradas

1. **Manter scorecard + adicionar emergent states como overlay**: Rejeitado porque adiciona complexidade sem justificativa — o scorecard é redundante quando mecanismos capturam a mesma informação de forma mais granular.
2. **Manter observáveis/latent traits no synth**: Rejeitado porque as 7 sensibilidades substituem completamente a função dos latent traits, com derivação mais rica baseada em YAML rules.

### O Que Será Removido

**Do synth (não gerar mais):**
- `observables.digital_literacy`
- `observables.similar_tool_experience`
- `observables.motor_ability`
- `observables.time_availability`
- `observables.domain_expertise`

**Do motor de simulação (não usar mais):**
- `capability_mean`, `trust_mean`, `friction_tolerance_mean`, `exploration_prob`
- Scorecard dimensions (complexity, initial_effort, perceived_risk, time_to_value)
- `UserState` (capability, trust, friction_tolerance, explores, motivation)
- `sample_user_state()` de `sample_state.py`

**Nota**: Os arquivos antigos (`engine.py`, `probability.py`, `sample_state.py`) serão mantidos no repositório mas marcados como deprecated. O novo motor viverá em arquivos separados.

---

## RQ-002: Distribuição Beta para Mecanismos

### Decisão

Cada mecanismo usará **Beta(α, β)** em vez de valor fixo, onde:
- `α = mean × strength`
- `β = (1 − mean) × strength`
- `strength = 15` (fixo, padrão inicial)

### Racional

A distribuição Beta é ideal para variáveis [0,1]:
- `Beta(2,2)` = incerto em torno de 0.5
- `Beta(8,2)` = tende para 0.8
- `Beta(20,3)` = tende para 0.87 com pouca variância

O `strength=15` produz distribuições com variância moderada (σ ≈ 0.1 para mean=0.5), adequadas para simulação exploratória.

### Exemplo

Para mean=0.6 (selecionado pelo usuário via dropdown):
- `α = 0.6 × 15 = 9`
- `β = 0.4 × 15 = 6`
- Resultado: Beta(9,6) — pico em ~0.6, σ ≈ 0.12

### Alternativas Consideradas

1. **Valor fixo**: Rejeitado — sem variação entre execuções, simulação trivial.
2. **Normal truncada**: Rejeitado — Beta é naturalmente [0,1], sem necessidade de truncamento.
3. **Strength variável por mecanismo**: Rejeitado por agora — complexidade adicional sem evidência de necessidade. Pode ser adicionado futuramente.

---

## RQ-003: Derivação de Sensibilidades via YAML

### Decisão

Sensibilidades são derivadas de dados demográficos do synth usando um arquivo YAML com regras condicionais, avaliadas em ordem com ajustes cumulativos sobre um valor base.

### Racional

- YAML permite ajuste sem mudança de código
- Regras são transparentes e auditáveis
- Suporta operadores numéricos (`>=`, `<=`, `>`, `<`, `==`) e string (`contains`, `contains_any`, `in`)
- Derivação é **determinística** — mesmos dados sempre produzem mesmas sensibilidades
- Versão da config é rastreada nos metadados de cada synth

### Estrutura do YAML

```yaml
version: "1.0"
description: "Calibração default para população brasileira"

sensitivities:
  risk_aversion:
    description: "Aversão a ações irreversíveis"
    base: 0.60
    rules:
      - condition: {field: "demografia.idade", operator: ">=", value: 60}
        adjustment: 0.10
        reason: "Idosos são mais conservadores"
      - condition: {field: "demografia.idade", operator: "<=", value: 25}
        adjustment: -0.05
        reason: "Jovens são mais aventureiros"
```

### Alternativas Consideradas

1. **Fórmulas hardcoded em Python**: Rejeitado — difícil de ajustar e auditar.
2. **LLM-based derivation**: Rejeitado — não determinístico, caro, lento.
3. **JSON em vez de YAML**: Rejeitado — YAML é mais legível para regras com comentários.

---

## RQ-004: Renomeação de Sensibilidades Existentes

### Decisão

A entidade `UserSensitivities` atual (6 campos) será **substituída** por uma nova versão com 7 campos alinhados ao spec 040.

### Mapeamento

| Antigo (038) | Novo (040) | Notas |
|---|---|---|
| `risk_aversion` | `risk_aversion` | Mantido |
| `social_dependency` | `social_dependency` | Mantido |
| `institutional_trust_level` | `institutional_trust_level` | Mantido |
| `habit_plasticity` | `habit_plasticity` | Mantido |
| `learning_tolerance` | `digital_capability` | **Renomeado** — conceito mais amplo |
| `social_influence` | `friction_tolerance` | **Substituído** — novo conceito |
| — | `pragmatism` | **Novo** — foco em utilidade |

### Impacto

- `EmergentState` atual (4 deltas: perceived_risk_delta, initial_effort_delta, trust_barrier, social_barrier) será substituído por 9 estados emergentes (7 barriers + 2 appeals)
- `mechanism_interaction.py` será reescrito para o novo modelo
- Testes existentes serão atualizados

---

## RQ-005: Novo Motor Monte Carlo

### Decisão

Criar novo motor (`feature_monte_carlo.py`) separado do motor causal existente (`simulation_engine_service.py`).

### Racional

Existem dois motores de simulação no sistema:
1. **Causal engine** (`simulation_engine_service.py`): DAG-based, world-level, usado pelo wizard de simulação — **NÃO SERÁ MODIFICADO**
2. **Feature impact engine** (`engine.py`): Synth × executions, scorecard-based — **SERÁ SUBSTITUÍDO**

O novo motor:
- Recebe: lista de synths (com sensibilidades), 9 mecanismos (com mean values)
- Para cada synth × execução:
  1. Amostra cada mecanismo de Beta(mean×strength, (1-mean)×strength)
  2. Calcula 9 estados emergentes
  3. Calcula probabilidade = base − barrier_penalty + appeal_boost
  4. Amostra Bernoulli(probabilidade) → adotou/não adotou
- Retorna: taxas de adoção por synth e agregadas

### Base Probability

A probabilidade base será **0.5** (neutral prior). Mecanismos e sensibilidades ajustam a partir desse ponto:
- Barreiras reduzem
- Appeals aumentam
- Resultado clamped [0.0, 1.0]

---

## RQ-006: Backward Compatibility

### Decisão

Mecanismos novos (valor_intrinseco, friccao_operacional, frequencia_de_uso) terão default 0.0, garantindo que experimentos existentes não sejam afetados.

### Impacto

- Experimentos com apenas 6 mecanismos: novos mecanismos = 0.0 → emergent states associados = 0.0 → zero impacto
- Frontend já suporta lista dinâmica de mecanismos via API (spec 039)
- Seed script usa `ON CONFLICT DO NOTHING` — re-seed é idempotente
