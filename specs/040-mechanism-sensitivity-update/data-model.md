# Data Model: Mechanism & Sensitivity Update

**Feature**: 040-mechanism-sensitivity-update
**Date**: 2026-02-06

## Entidades Modificadas

### 1. UserSensitivities (REESCRITA)

**Arquivo**: `src/synth_lab/domain/entities/user_sensitivities.py`

**Antes (6 campos):**
```
risk_aversion, social_dependency, institutional_trust_level,
habit_plasticity, learning_tolerance, social_influence
```

**Depois (7 campos):**

| Campo | Tipo | Default | Range | Descrição |
|-------|------|---------|-------|-----------|
| `risk_aversion` | float | 0.5 | [0,1] | Aversão a ações irreversíveis |
| `social_dependency` | float | 0.5 | [0,1] | Necessidade de validação social |
| `institutional_trust_level` | float | 0.5 | [0,1] | Confiança em instituições |
| `habit_plasticity` | float | 0.5 | [0,1] | Flexibilidade para mudar rotinas |
| `friction_tolerance` | float | 0.5 | [0,1] | Tolerância a processos complexos |
| `pragmatism` | float | 0.5 | [0,1] | Foco em utilidade vs hedônico |
| `digital_capability` | float | 0.5 | [0,1] | Habilidade técnica digital |

**Metadados** (persistidos junto com sensibilidades no synth):

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `_meta.derivation_version` | str | Versão do YAML rules (ex: "1.0") |
| `_meta.config_name` | str | Nome do arquivo config usado |
| `_meta.applied_rules` | list[str] | Lista de rules que foram aplicadas |

---

### 2. FeatureMechanisms (ESTENDIDA)

**Arquivo**: `src/synth_lab/domain/entities/feature_mechanisms.py`

**3 campos novos adicionados:**

| Campo | Tipo | Default | Range | Descrição |
|-------|------|---------|-------|-----------|
| `valor_intrinseco` | float | 0.0 | [0,1] | Melhora real na vida do usuário |
| `friccao_operacional` | float | 0.0 | [0,1] | Atrito/passos/erros no uso |
| `frequencia_de_uso` | float | 0.0 | [0,1] | Cadência de uso esperada |

**Total**: 9 mecanismos (6 existentes + 3 novos).

---

### 3. EmergentState (REESCRITA)

**Arquivo**: `src/synth_lab/domain/entities/emergent_state.py`

**Antes (4 deltas):**
```
perceived_risk_delta, initial_effort_delta, trust_barrier, social_barrier
```

**Depois (9 estados emergentes):**

#### Barreiras (7)

| Estado | Fórmula | Tipo |
|--------|---------|------|
| `perceived_risk` | `irreversibility × risk_aversion` | Affinity |
| `trust_barrier` | `institutional_trust × (1 − institutional_trust_level)` | Resistance |
| `habit_resistance` | `habit_displacement × (1 − habit_plasticity)` | Resistance |
| `learning_frustration` | `learning_curve × (1 − digital_capability)` | Resistance |
| `friction_burden` | `friccao_operacional × (1 − friction_tolerance)` | Resistance |
| `social_pressure` | `social_visibility × social_dependency` | Affinity |
| `network_barrier` | `network_effect × (1 − social_dependency)` | Resistance |

#### Appeals (2)

| Estado | Fórmula | Tipo |
|--------|---------|------|
| `intrinsic_appeal` | `valor_intrinseco × pragmatism` | Appeal |
| `frequency_value` | `frequencia_de_uso × pragmatism` | Appeal |

#### Metadata

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `top_contributors` | list[InteractionContribution] | Top 3 interações por produto |
| `raw_interactions` | dict[str, float] | Todos os 9 produtos mechanism×sensitivity |

---

## Entidades Novas

### 4. SensitivityRules (YAML Config)

**Arquivo**: `src/synth_lab/config/sensitivity_rules.yaml`

```yaml
version: "1.0"
description: "Calibração default para população brasileira"

sensitivities:
  risk_aversion:
    description: "Aversão a ações irreversíveis"
    base: 0.60
    rules:
      - condition:
          field: "demografia.idade"
          operator: ">="
          value: 60
        adjustment: 0.10
        reason: "Idosos são mais conservadores"
      - condition:
          field: "demografia.idade"
          operator: "<="
          value: 25
        adjustment: -0.05
        reason: "Jovens são mais aventureiros"
      - condition:
          field: "demografia.escolaridade"
          operator: "in"
          value: ["ensino superior completo", "pós-graduação"]
        adjustment: -0.05
        reason: "Maior escolaridade → menor aversão"

  social_dependency:
    base: 0.50
    rules:
      - condition: {field: "demografia.idade", operator: "<=", value: 30}
        adjustment: 0.10
        reason: "Jovens mais dependentes socialmente"
      - condition: {field: "demografia.idade", operator: ">=", value: 55}
        adjustment: -0.05
        reason: "Mais velhos são mais independentes"

  institutional_trust_level:
    base: 0.50
    rules:
      - condition: {field: "demografia.idade", operator: ">=", value: 50}
        adjustment: 0.10
        reason: "Mais velhos confiam mais em instituições"
      - condition:
          field: "demografia.escolaridade"
          operator: "in"
          value: ["ensino superior completo", "pós-graduação"]
        adjustment: 0.05
        reason: "Mais escolaridade → mais confiança institucional"

  habit_plasticity:
    base: 0.55
    rules:
      - condition: {field: "demografia.idade", operator: "<=", value: 30}
        adjustment: 0.10
        reason: "Jovens mudam hábitos com facilidade"
      - condition: {field: "demografia.idade", operator: ">=", value: 60}
        adjustment: -0.15
        reason: "Idosos são mais rígidos"

  friction_tolerance:
    base: 0.50
    rules:
      - condition: {field: "demografia.idade", operator: "<=", value: 30}
        adjustment: 0.05
        reason: "Jovens toleram mais fricção"
      - condition: {field: "demografia.idade", operator: ">=", value: 60}
        adjustment: -0.10
        reason: "Idosos toleram menos fricção"
      - condition:
          field: "composicao_familiar.tipo"
          operator: "contains"
          value: "monoparental"
        adjustment: -0.05
        reason: "Pais solo têm menos paciência"
      - condition:
          field: "deficiencias.motora.tipo"
          operator: "in"
          value: ["moderada", "severa"]
        adjustment: -0.10
        reason: "Deficiência motora reduz tolerância"

  pragmatism:
    base: 0.55
    rules:
      - condition: {field: "demografia.idade", operator: ">=", value: 35}
        adjustment: 0.05
        reason: "Adultos são mais pragmáticos"
      - condition:
          field: "demografia.escolaridade"
          operator: "in"
          value: ["ensino superior completo", "pós-graduação"]
        adjustment: 0.05
        reason: "Mais escolaridade → mais pragmatismo"

  digital_capability:
    base: 0.50
    rules:
      - condition: {field: "demografia.idade", operator: "<=", value: 30}
        adjustment: 0.15
        reason: "Nativos digitais"
      - condition: {field: "demografia.idade", operator: ">=", value: 60}
        adjustment: -0.20
        reason: "Idosos têm menor capacidade digital"
      - condition:
          field: "demografia.escolaridade"
          operator: "in"
          value: ["ensino superior completo", "pós-graduação"]
        adjustment: 0.10
        reason: "Mais escolaridade → mais digital"
      - condition:
          field: "deficiencias.visual.tipo"
          operator: "in"
          value: ["moderada", "severa"]
        adjustment: -0.10
        reason: "Deficiência visual impacta capacidade digital"
```

**Operadores suportados:**

| Operador | Tipo | Exemplo |
|----------|------|---------|
| `>=`, `<=`, `>`, `<`, `==` | Numérico | `{field: "idade", operator: ">=", value: 60}` |
| `contains` | String (case-insensitive) | `{field: "tipo", operator: "contains", value: "mono"}` |
| `contains_any` | String (qualquer match) | `{field: "interesses", operator: "contains_any", value: ["tech", "games"]}` |
| `in` | String em lista | `{field: "escolaridade", operator: "in", value: ["superior", "pós"]}` |

---

## Entidades Não Modificadas

- **Simulation** (sim_*): Mantida — o causal engine não muda
- **CausalDAG**: Mantida
- **Hypothesis**: Mantida
- **MechanismDefinition**: Mantida (apenas novos registros no seed)
- **MechanismOption**: Mantida (apenas novos registros no seed)
- **FeatureType**: Mantida

## Storage

- Sensibilidades: JSONB no campo `data` do synth (chave `sensitivities`)
- Mecanismos: JSONB no `scorecard_data` do experiment (chave `mechanisms`)
- Nenhuma migração de schema necessária — tudo usa campos JSONB existentes

## Diagrama de Fluxo

```
Synth Generation:
  demografia → YAML rules → 7 sensitivities → persisted in synth.data.sensitivities

Experiment Configuration:
  user selects mechanisms (9 options) → saved in experiment.scorecard_data.mechanisms

Simulation Execution:
  For each synth × execution:
    1. Sample each mechanism from Beta(mean×15, (1-mean)×15)
    2. Load synth sensitivities (or derive on-demand)
    3. Calculate 9 emergent states
    4. base_prob (0.5) − barrier_penalty + appeal_boost → clamped [0,1]
    5. Bernoulli(prob) → adopted / not adopted
```
