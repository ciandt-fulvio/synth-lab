# Referência de Fórmulas da Simulação Monte Carlo

Todas as fórmulas de cálculo da simulação Monte Carlo que determinam os outcomes (did_not_try, failed, success).

**Versão do Schema**: 2.3.0

---

## Visão Geral do Processo

A simulação Monte Carlo executa **N synths × M execuções** para estimar taxas de outcome. Para cada execução:

1. **Amostra estado do usuário** com ruído gaussiano e modificadores de cenário
2. **Calcula P(attempt)** - probabilidade de tentar usar o feature
3. **Calcula P(success|attempt)** - probabilidade de sucesso dado que tentou
4. **Amostra outcome** baseado nas probabilidades
5. **Agrega resultados** por synth e globalmente

---

## 1. Amostragem de Estado do Usuário

### Função: `sample_user_state()`

Amostra o estado do usuário a partir dos **latent traits** com ruído e modificadores de cenário.

| Variável | Fórmula | Descrição |
|----------|---------|-----------|
| **capability** | `capability ~ Normal(capability_mean, σ)` <br/> clamped [0,1] | Capacidade amostrada com ruído gaussiano |
| **trust** | `trust ~ Normal(trust_mean, σ) + trust_modifier` <br/> clamped [0,1] | Confiança amostrada + modificador de cenário |
| **friction_tolerance** | `friction ~ Normal(friction_tolerance_mean, σ) + friction_modifier` <br/> clamped [0,1] | Tolerância a fricção amostrada + modificador |
| **explores** | `explores ~ Bernoulli(exploration_prob)` | Explorador (boolean) amostrado via Bernoulli |
| **motivation** | `motivation = clamp(task_criticality + motivation_modifier, [0,1])` | Motivação = criticidade da tarefa + modificador |

### Parâmetros

| Parâmetro | Tipo | Default | Descrição |
|-----------|------|---------|-----------|
| `σ` (sigma) | `float` | 0.1 | Desvio padrão do ruído gaussiano |
| `latent_traits` | `dict` | - | `{capability_mean, trust_mean, friction_tolerance_mean, exploration_prob}` |
| `scenario` | `dict` | - | `{trust_modifier, friction_modifier, motivation_modifier, task_criticality}` |

### Exemplo

```python
# Latent traits do synth
latent_traits = {
    "capability_mean": 0.6,
    "trust_mean": 0.5,
    "friction_tolerance_mean": 0.4,
    "exploration_prob": 0.5
}

# Cenário baseline (sem modificadores)
scenario = {
    "trust_modifier": 0.0,
    "friction_modifier": 0.0,
    "motivation_modifier": 0.0,
    "task_criticality": 0.5
}

# Resultado: UserState com valores amostrados
# capability ≈ 0.6 ± σ, trust ≈ 0.5 ± σ, etc.
```

---

## 2. Probabilidade de Tentativa

### Função: `calculate_p_attempt()`

Calcula a probabilidade do usuário **tentar** usar o feature.

### Fórmula Logit

```
logit = w_motivation × motivation
      + w_trust × trust
      - w_risk × perceived_risk
      - w_effort × initial_effort
      + w_explore × explores
      + intercept
```

### Pesos Calibrados

| Peso | Valor | Interpretação |
|------|-------|---------------|
| `w_motivation` | 2.0 | Motivação é forte preditor de tentativa |
| `w_trust` | 1.5 | Confiança aumenta disposição para tentar |
| `w_risk` | -2.0 | Risco percebido **reduz** tentativas |
| `w_effort` | -1.5 | Esforço inicial **reduz** tentativas |
| `w_explore` | 1.0 | Exploradores são mais propensos a tentar |
| `intercept` | 0.0 | Sem viés base |

### Transformação Sigmoid

```
P(attempt) = sigmoid(logit) = 1 / (1 + e^(-logit))
```

### Exemplo

```python
# Estado do usuário
user_state = {
    "motivation": 0.7,
    "trust": 0.6,
    "explores": True  # 1.0
}

# Scorecard do feature
scorecard = {
    "perceived_risk": 0.3,
    "initial_effort": 0.4
}

# Cálculo
logit = 2.0×0.7 + 1.5×0.6 - 2.0×0.3 - 1.5×0.4 + 1.0×1.0
      = 1.4 + 0.9 - 0.6 - 0.6 + 1.0
      = 2.1

P(attempt) = sigmoid(2.1) ≈ 0.891  # Alta probabilidade de tentar
```

---

## 3. Probabilidade de Sucesso

### Função: `calculate_p_success()`

Calcula a probabilidade de **sucesso** dado que o usuário tentou.

### Fórmula Logit

```
logit = w_capability × capability
      + w_friction × friction_tolerance
      - w_complexity × complexity
      - w_ttv × time_to_value
      + intercept
```

### Pesos Calibrados

| Peso | Valor | Interpretação |
|------|-------|---------------|
| `w_capability` | 2.5 | Capacidade é o preditor mais forte de sucesso |
| `w_friction` | 1.5 | Tolerância a fricção ajuda a completar tarefas |
| `w_complexity` | -2.0 | Complexidade **reduz** sucesso |
| `w_ttv` | -1.5 | Tempo até valor **reduz** sucesso |
| `intercept` | 0.0 | Sem viés base |

### Transformação Sigmoid

```
P(success|attempt) = sigmoid(logit) = 1 / (1 + e^(-logit))
```

### Exemplo

```python
# Estado do usuário
user_state = {
    "capability": 0.8,
    "friction_tolerance": 0.5
}

# Scorecard do feature
scorecard = {
    "complexity": 0.4,
    "time_to_value": 0.3
}

# Cálculo
logit = 2.5×0.8 + 1.5×0.5 - 2.0×0.4 - 1.5×0.3
      = 2.0 + 0.75 - 0.8 - 0.45
      = 1.5

P(success|attempt) = sigmoid(1.5) ≈ 0.818  # Alta probabilidade de sucesso
```

---

## 4. Amostragem de Outcome

### Função: `sample_outcome()`

Amostra o outcome final usando árvore de decisão probabilística.

### Árvore de Decisão

```
1. Sample u1 ~ Uniform(0,1)
   IF u1 ≥ P(attempt):
      RETURN "did_not_try"

2. Sample u2 ~ Uniform(0,1)
   IF u2 ≥ P(success|attempt):
      RETURN "failed"

3. RETURN "success"
```

### Probabilidades Exatas de Outcomes

Para análise matemática (sem amostragem):

| Outcome | Fórmula | Descrição |
|---------|---------|-----------|
| **P(did_not_try)** | `1 - P(attempt)` | Probabilidade de não tentar |
| **P(failed)** | `P(attempt) × (1 - P(success\|attempt))` | Tentou mas falhou |
| **P(success)** | `P(attempt) × P(success\|attempt)` | Tentou e teve sucesso |

**Garantia**: `P(did_not_try) + P(failed) + P(success) = 1.0`

### Exemplo

```python
# Com P(attempt) = 0.891, P(success|attempt) = 0.818

P(did_not_try) = 1 - 0.891 = 0.109  (10.9%)
P(failed) = 0.891 × (1 - 0.818) = 0.162  (16.2%)
P(success) = 0.891 × 0.818 = 0.729  (72.9%)
```

---

## 5. Agregação de Resultados

### Por Synth (M execuções)

Para cada synth, executa **M simulações** e conta outcomes:

```
did_not_try_rate = count("did_not_try") / M
failed_rate = count("failed") / M
success_rate = count("success") / M
```

**Arredondamento**: 3 casas decimais
**Garantia**: `did_not_try_rate + failed_rate + success_rate = 1.000`

### Agregação Global (N synths)

Calcula média das rates de todos os synths:

```
aggregated_did_not_try = (Σ did_not_try_rate_i) / N
aggregated_failed = (Σ failed_rate_i) / N
aggregated_success = (Σ success_rate_i) / N
```

**Arredondamento**: 3 casas decimais
**Garantia**: `aggregated_did_not_try + aggregated_failed + aggregated_success = 1.000`

---

## 6. Configuração de Simulação

### SimulationConfig

| Parâmetro | Default | Range | Descrição |
|-----------|---------|-------|-----------|
| `n_synths` | 500 | ≥1 | Número de synths a simular |
| `n_executions` | 100 | ≥1 | Número de execuções por synth |
| `sigma` | 0.05 | [0.0, 0.5] | Nível de ruído na amostragem de traits |
| `seed` | `None` | - | Seed aleatória para reprodutibilidade |

### Performance Target

- **Target**: 100 synths × 100 execuções em < 1 segundo
- **Total de amostragens**: N × M (exemplo: 500 × 100 = 50.000 execuções)

---

## 7. Fluxo Completo de Simulação

### Pseudocódigo

```python
FOR each synth in synths:
    outcomes = {"did_not_try": 0, "failed": 0, "success": 0}

    FOR i in range(n_executions):
        # 1. Amostra estado do usuário
        user_state = sample_user_state(
            latent_traits=synth.latent_traits,
            scenario=scenario,
            sigma=sigma,
            rng=rng
        )

        # 2. Calcula probabilidades
        p_attempt = calculate_p_attempt(user_state, scorecard)
        p_success = calculate_p_success(user_state, scorecard)

        # 3. Amostra outcome
        outcome = sample_outcome(p_attempt, p_success, rng)
        outcomes[outcome] += 1

    # 4. Calcula rates para o synth
    synth.did_not_try_rate = outcomes["did_not_try"] / n_executions
    synth.failed_rate = outcomes["failed"] / n_executions
    synth.success_rate = outcomes["success"] / n_executions

# 5. Agrega globalmente
aggregated_did_not_try = mean([s.did_not_try_rate for s in synths])
aggregated_failed = mean([s.failed_rate for s in synths])
aggregated_success = mean([s.success_rate for s in synths])
```

---

## 8. Inputs da Simulação

### De Onde Vêm os Dados

| Input | Fonte | Quando Gerado |
|-------|-------|---------------|
| **Latent Traits** | Derivados de `observables` via `derive_latent_traits()` | Durante criação do synth |
| **Observables** | Gerados via `generate_observables_correlated()` | Durante criação do synth |
| **Scorecard Scores** | Definidos pelo PM para o feature | Antes da simulação |
| **Scenario Modifiers** | Escolhidos pelo PM (baseline, crisis, etc.) | Antes da simulação |

### Persistência

| Entidade | Campos Diretos | Campos JSON |
|----------|----------------|-------------|
| `synth_outcomes` | id, analysis_id, synth_id, did_not_try_rate, failed_rate, success_rate | `synth_attributes` (observables, latent_traits) |

---

## 9. Fatores que Influenciam Outcomes

### Did Not Try (Alta Taxa)

**Aumenta quando:**
- ❌ Baixa motivação (`motivation < 0.3`)
- ❌ Baixa confiança (`trust < 0.3`)
- ❌ Alto risco percebido (`perceived_risk > 0.7`)
- ❌ Alto esforço inicial (`initial_effort > 0.7`)
- ❌ Não é explorador (`explores = False`)

### Failed (Alta Taxa)

**Aumenta quando:**
- ✅ Usuário tentou (passou P(attempt))
- ❌ Baixa capacidade (`capability < 0.3`)
- ❌ Baixa tolerância a fricção (`friction_tolerance < 0.3`)
- ❌ Alta complexidade (`complexity > 0.7`)
- ❌ Alto tempo até valor (`time_to_value > 0.7`)

### Success (Alta Taxa)

**Aumenta quando:**
- ✅ Alta motivação + confiança (passa P(attempt))
- ✅ Alta capacidade (`capability > 0.7`)
- ✅ Alta tolerância a fricção (`friction_tolerance > 0.7`)
- ✅ Baixa complexidade (`complexity < 0.3`)
- ✅ Baixo tempo até valor (`time_to_value < 0.3`)

---

## 10. Exemplos de Interpretação

### Exemplo 1: Feature Simples e Confiável

```
Scorecard:
  complexity: 0.2 (muito simples)
  initial_effort: 0.1 (muito fácil)
  perceived_risk: 0.1 (muito seguro)
  time_to_value: 0.2 (valor rápido)

Synth típico (capability_mean=0.6, trust_mean=0.7):
  P(attempt) ≈ 0.95 (altíssima)
  P(success|attempt) ≈ 0.92 (altíssima)

Outcome esperado:
  did_not_try: ~5%
  failed: ~4%
  success: ~91%
```

### Exemplo 2: Feature Complexo e Arriscado

```
Scorecard:
  complexity: 0.8 (muito complexo)
  initial_effort: 0.7 (trabalhoso)
  perceived_risk: 0.8 (arriscado)
  time_to_value: 0.7 (demora)

Synth típico (capability_mean=0.4, trust_mean=0.5):
  P(attempt) ≈ 0.22 (baixíssima)
  P(success|attempt) ≈ 0.25 (baixíssima)

Outcome esperado:
  did_not_try: ~78%
  failed: ~17%
  success: ~5%
```

---

## 11. Validação Matemática

### Propriedades Garantidas

1. **Todas as probabilidades em [0,1]**:
   - `0 ≤ P(attempt) ≤ 1`
   - `0 ≤ P(success|attempt) ≤ 1`
   - Garantido pela função `sigmoid()`

2. **Outcomes mutuamente exclusivos**:
   - `P(did_not_try) + P(failed) + P(success) = 1.0`
   - Garantido pela árvore de decisão

3. **Rates por synth somam 1.0**:
   - `did_not_try_rate + failed_rate + success_rate = 1.000`
   - Arredondamento para 3 decimais

4. **Rates agregadas somam 1.0**:
   - `aggregated_did_not_try + aggregated_failed + aggregated_success = 1.000`
   - Garantido pela média aritmética

---

## 12. Referências de Implementação

| Módulo | Arquivo | Função Principal |
|--------|---------|------------------|
| **Engine** | `services/simulation/engine.py` | `MonteCarloEngine.run_simulation()` |
| **Probabilidade** | `services/simulation/probability.py` | `calculate_p_attempt()`, `calculate_p_success()` |
| **Amostragem** | `services/simulation/sample_state.py` | `sample_user_state()` |
| **Atributos** | `gen_synth/simulation_attributes.py` | `derive_latent_traits()` |

---

## Changelog

### v2.3.0 (Atual)
- Documentação inicial das fórmulas de simulação
- Pesos calibrados: `w_motivation=2.0`, `w_capability=2.5`
- Sigma default: 0.05 (ruído reduzido)

---

## Notas Importantes

⚠️ **Não modifique os pesos sem recalibração**: Os pesos das fórmulas foram calibrados para produzir distribuições realistas. Alterações podem desbalancear a simulação.

📊 **Performance**: A simulação usa vetorização numpy onde possível. Para N=500, M=100 (50.000 execuções), o tempo típico é < 0.5 segundos.

🎲 **Reprodutibilidade**: Use `seed` para resultados reproduzíveis. Mesma seed + mesmos inputs = mesmos outcomes.
