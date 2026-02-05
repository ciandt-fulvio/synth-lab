# Quickstart: Mechanism-Based Simulation

**Feature**: 038-mechanism-based-simulation
**Date**: 2026-02-04

## Objetivo

Permitir que simulações Monte Carlo diferenciem features com mesmos scores de scorecard mas naturezas diferentes, através de mecanismos estruturais que interagem com sensibilidades dos usuários.

## Arquitetura Resumida

```
                    ANTES
┌──────────────────────────────────────────────┐
│  Scorecard (4 números)                        │
│  └─> Probabilidade ─> Adoção                  │
│                                               │
│  ⚠️ Features diferentes com mesmos scores     │
│     produzem resultados idênticos             │
└──────────────────────────────────────────────┘

                    AGORA
┌──────────────────────────────────────────────┐
│  Scorecard + Mechanisms (6 mecanismos)        │
│       ↓                                       │
│  × Sensitivities (6 sensibilidades por synth) │
│       ↓                                       │
│  = Emergent States (barreiras contextuais)    │
│       ↓                                       │
│  Probabilidade Modificada ─> Adoção           │
│                                               │
│  ✅ Features diferentes produzem resultados   │
│     diferentes mesmo com mesmos scores        │
└──────────────────────────────────────────────┘
```

## Conceitos Principais

### 1. Mecanismos (Feature Side)

| Mecanismo | Significado | Exemplo |
|-----------|-------------|---------|
| `irreversibility` | Ação não pode ser desfeita | Transferência Pix |
| `network_effect` | Valor depende de outros usarem | WhatsApp |
| `institutional_trust` | Requer confiança na instituição | Banco digital |
| `habit_displacement` | Substitui hábito existente | Migrar de cartão para Pix |
| `learning_curve` | Requer aprendizado | Nova interface |
| `social_visibility` | Uso é visível para outros | Compra em grupo |

### 2. Sensibilidades (User Side)

| Sensibilidade | Significado | Interação |
|---------------|-------------|-----------|
| `risk_aversion` | Evita riscos | × irreversibility |
| `social_dependency` | Segue outros | × network_effect |
| `institutional_trust_level` | Confia em instituições | × institutional_trust |
| `habit_plasticity` | Adapta hábitos facilmente | × habit_displacement |
| `learning_tolerance` | Tolera aprendizado | × learning_curve |
| `social_influence` | Influenciado por visibilidade | × social_visibility |

### 3. Estados Emergentes

```python
# Exemplo: Feature "Pix via WhatsApp"
mechanisms = {irreversibility: 0.9, network_effect: 0.7, ...}

# Usuário com alta aversão a risco
sensitivities = {risk_aversion: 0.8, social_dependency: 0.3, ...}

# Estado emergente
perceived_risk_delta = 0.9 × 0.8 = 0.72  # Barreira alta!
social_barrier = 0.7 × (1 - 0.3) = 0.49  # Moderada

# Resultado: Usuário provavelmente NÃO tenta
```

## Fluxo de Desenvolvimento

### Backend

```
1. Criar entidades
   src/synth_lab/domain/entities/
   ├── feature_mechanisms.py      # FeatureMechanisms Pydantic model
   └── user_sensitivities.py      # UserSensitivities Pydantic model

2. Modificar simulação
   src/synth_lab/services/simulation/
   ├── mechanism_interaction.py   # NEW: Cálculo de estados emergentes
   ├── engine.py                  # MODIFY: Usar mecanismos se disponíveis
   └── probability.py             # MODIFY: Aceitar emergent states

3. Atualizar schemas
   src/synth_lab/api/schemas/
   └── experiments.py             # MODIFY: Adicionar mechanisms

4. Testes
   tests/unit/
   ├── test_feature_mechanisms.py
   ├── test_user_sensitivities.py
   └── test_mechanism_interaction.py
   tests/integration/
   └── test_mechanism_simulation.py
```

### Frontend

```
1. Adicionar tipos
   frontend/src/types/
   └── simulation.ts              # MODIFY: FeatureMechanisms types

2. Criar componente
   frontend/src/components/
   └── MechanismEditor.tsx        # NEW: Sliders para mecanismos

3. Atualizar página
   frontend/src/pages/
   └── ExperimentDetail.tsx       # MODIFY: Mostrar mecanismos
```

## Comandos de Desenvolvimento

```bash
# Backend - rodar testes
pytest tests/unit/test_feature_mechanisms.py -v
pytest tests/unit/test_mechanism_interaction.py -v
pytest tests/integration/test_mechanism_simulation.py -v

# Backend - validação local
uv run python -m synth_lab.domain.entities.feature_mechanisms
uv run python -m synth_lab.services.simulation.mechanism_interaction

# Frontend
cd frontend && npm run dev
cd frontend && npm run lint
```

## Validação de Sucesso

| Critério | Como Testar |
|----------|-------------|
| SC-001: Variância ≥15% | Simular 2 features same-score, different-mechanisms |
| SC-003: Zero regressão | Rodar experimentos existentes, comparar resultados |
| SC-004: Reprodutibilidade | Same seed = same results |

## Exemplos de Uso

### 1. Criar Experimento com Mecanismos

```python
# API Request
PATCH /experiments/exp_12345678
{
  "scorecard": {
    "complexity": {"score": 0.4},
    "initial_effort": {"score": 0.3},
    "perceived_risk": {"score": 0.2},
    "time_to_value": {"score": 0.5}
  },
  "mechanisms": {
    "irreversibility": 0.9,
    "network_effect": 0.7,
    "institutional_trust": 0.8,
    "habit_displacement": 0.4,
    "learning_curve": 0.5,
    "social_visibility": 0.3
  },
  "feature_types": ["financial", "social"]
}
```

### 2. Comparar Features no Mesmo Mundo

```python
# API Request
POST /analysis/compare
{
  "experiment_ids": ["exp_12345678", "exp_87654321"],
  "seed": 42,
  "n_executions": 100
}

# Response
{
  "world_seed": 42,
  "synth_count": 500,
  "comparisons": [
    {
      "experiment_id": "exp_12345678",
      "feature_name": "Pix via WhatsApp",
      "aggregated_success": 0.45,
      "top_mechanism_effects": [
        {"mechanism": "irreversibility", "sensitivity": "risk_aversion", "product": 0.66}
      ]
    },
    {
      "experiment_id": "exp_87654321",
      "feature_name": "Nova Homepage",
      "aggregated_success": 0.62,
      "top_mechanism_effects": [
        {"mechanism": "learning_curve", "sensitivity": "learning_tolerance", "product": 0.16}
      ]
    }
  ],
  "summary": {
    "best_feature_id": "exp_87654321",
    "variance_between_features": 0.17
  }
}
```

### 3. Explicar Diferenças de Segmento

```python
# API Request
POST /analysis/ana_12345678/explain-segment
{
  "synth_ids": ["synth_001", "synth_002", "synth_003"],
  "compare_to_population": true
}

# Response
{
  "segment_size": 3,
  "segment_avg_success": 0.25,
  "population_avg_success": 0.45,
  "top_differentiating_factors": [
    {
      "interaction": {"mechanism": "irreversibility", "sensitivity": "risk_aversion", "product": 0.81},
      "segment_avg": 0.81,
      "population_avg": 0.54,
      "delta": 0.27
    }
  ],
  "explanation_text": "Este segmento tem adoção 20% menor que a população porque são muito mais sensíveis à irreversibilidade da ação (risco percebido emergente de 0.81 vs 0.54)."
}
```

## Compatibilidade

- Experimentos existentes SEM mecanismos: Funcionam identicamente ao antes
- Synths SEM sensibilidades: Usam valores neutros (0.5)
- APIs existentes: Continuam funcionando, mecanismos são opcionais
