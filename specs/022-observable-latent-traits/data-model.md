# Data Model: Observable vs. Latent Traits

**Feature**: 022-observable-latent-traits
**Date**: 2025-12-29

## Entity Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                          Synth                                   │
├─────────────────────────────────────────────────────────────────┤
│ id, nome, descricao, link_photo, created_at, version            │
│ demografia, psicografia, deficiencias, capacidades_tecnologicas │
│ simulation_attributes ─────────────────────────────────────────►│
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SimulationAttributes                          │
├─────────────────────────────────────────────────────────────────┤
│ observables: SimulationObservables                               │
│ latent_traits: SimulationLatentTraits                           │
└─────────────────────────────────────────────────────────────────┘
          │                                    │
          ▼                                    ▼
┌─────────────────────────┐     ┌─────────────────────────────────┐
│  SimulationObservables  │────►│    SimulationLatentTraits       │
│  (Visível ao PM)        │     │    (Interno - Simulações)       │
├─────────────────────────┤     ├─────────────────────────────────┤
│ digital_literacy: float │     │ capability_mean: float          │
│ similar_tool_exp: float │     │ trust_mean: float               │
│ motor_ability: float    │     │ friction_tolerance_mean: float  │
│ time_availability: float│     │ exploration_prob: float         │
│ domain_expertise: float │     └─────────────────────────────────┘
└─────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     ObservableWithLabel                          │
│                     (API Response Only)                          │
├─────────────────────────────────────────────────────────────────┤
│ key: string           # digital_literacy                         │
│ name: string          # Literacia Digital                        │
│ value: float          # 0.42                                     │
│ label: string         # Médio                                    │
│ description: string   # Familiaridade com tecnologia...          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Entity Definitions

### SimulationObservables (Existing - No Changes)

**Location**: `src/synth_lab/domain/entities/simulation_attributes.py`

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `digital_literacy` | float | [0, 1] | Familiaridade com tecnologia e interfaces digitais |
| `similar_tool_experience` | float | [0, 1] | Experiência prévia com ferramentas semelhantes |
| `motor_ability` | float | [0, 1] | Capacidade motora/física para interação |
| `time_availability` | float | [0, 1] | Tempo típico disponível para uso |
| `domain_expertise` | float | [0, 1] | Conhecimento do domínio/área do produto |

**Generation Rules** (Updated):
- `digital_literacy`: Beta(α, β) ajustado por escolaridade e idade
- `similar_tool_experience`: Beta(3, 3) - simétrico (baseline)
- `motor_ability`: Beta(α, β) ajustado por deficiência motora
- `time_availability`: Beta(α, β) ajustado por composição familiar
- `domain_expertise`: Beta(3, 3) - simétrico (baseline)

---

### SimulationLatentTraits (Existing - No Changes)

**Location**: `src/synth_lab/domain/entities/simulation_attributes.py`

| Field | Type | Range | Derivation Formula |
|-------|------|-------|-------------------|
| `capability_mean` | float | [0, 1] | 0.40×DL + 0.35×EXP + 0.15×MOT + 0.10×DOM |
| `trust_mean` | float | [0, 1] | 0.60×EXP + 0.40×DL |
| `friction_tolerance_mean` | float | [0, 1] | 0.40×TIME + 0.35×DL + 0.25×EXP |
| `exploration_prob` | float | [0, 1] | 0.50×DL + 0.30×(1-EXP) + 0.20×TIME |

**Legend**:
- DL = digital_literacy
- EXP = similar_tool_experience
- MOT = motor_ability
- TIME = time_availability
- DOM = domain_expertise

---

### ObservableLabel (New - API Response)

**Location**: `src/synth_lab/api/schemas/synth_schemas.py`

| Field | Type | Example |
|-------|------|---------|
| `key` | string | "digital_literacy" |
| `name` | string | "Literacia Digital" |
| `value` | float | 0.42 |
| `label` | string | "Médio" |
| `description` | string | "Familiaridade com tecnologia e interfaces digitais" |

**Label Ranges**:
| Value Range | Label |
|-------------|-------|
| 0.00 - 0.20 | Muito Baixo |
| 0.20 - 0.40 | Baixo |
| 0.40 - 0.60 | Médio |
| 0.60 - 0.80 | Alto |
| 0.80 - 1.00 | Muito Alto |

---

### SimulationContext (New - Interview Context)

**Location**: `src/synth_lab/services/research_agentic/context.py`

| Field | Type | Description |
|-------|------|-------------|
| `synth_id` | string | ID do synth na simulação |
| `analysis_id` | string | ID da análise/simulação |
| `attempt_rate` | float | Taxa de tentativa [0, 1] |
| `success_rate` | float | Taxa de sucesso [0, 1] |
| `failure_rate` | float | Taxa de falha [0, 1] |
| `n_executions` | int | Número de execuções Monte Carlo |

**Usage**: Passado para `format_interviewee_instructions()` quando entrevista está conectada a simulação.

---

## Validation Rules

### SimulationObservables
- All values MUST be in range [0, 1]
- All values MUST be float
- No field can be None

### SimulationLatentTraits
- All values MUST be in range [0, 1] (enforced by clamp)
- Derived from observables - never set directly
- Immutable after derivation

### ObservableLabel
- `value` MUST match corresponding observable value
- `label` MUST be one of: "Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"
- `key` MUST be valid observable field name

### SimulationContext
- `attempt_rate + success_rate + failure_rate` SHOULD equal 1.0 (or close)
- All rates MUST be in range [0, 1]
- `n_executions` MUST be positive integer

---

## State Transitions

### Synth Lifecycle

```
[Created] ──► [Stored] ──► [Used in Simulation] ──► [Interviewed]
    │             │                  │                    │
    ▼             ▼                  ▼                    ▼
 Generate     Persist          Extract latents     Pass observables
 observables  to PostgreSQL        for probability     + sim context
 from demo-   with JSON        calculations        to interviewee
 graphics     encoding                             prompt
```

### Observable → Latent Derivation (One-Way)

```
Demographics ──► generate_observables() ──► SimulationObservables
                                                     │
                                                     ▼
                                           derive_latent_traits()
                                                     │
                                                     ▼
                                           SimulationLatentTraits
```

**Note**: Latent traits are ALWAYS derived. Never stored independently. If observables change, latents must be recalculated.

---

## Database Schema

### synths table (Existing - No Schema Change)

```sql
CREATE TABLE synths (
    id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    descricao TEXT,
    link_photo TEXT,
    created_at TEXT NOT NULL,
    version TEXT,
    data JSON NOT NULL  -- Contains all nested objects including simulation_attributes
);
```

**JSON structure in `data` column**:
```json
{
  "demografia": {...},
  "psicografia": {...},
  "deficiencias": {...},
  "capacidades_tecnologicas": {...},
  "simulation_attributes": {
    "observables": {
      "digital_literacy": 0.42,
      "similar_tool_experience": 0.35,
      "motor_ability": 0.85,
      "time_availability": 0.28,
      "domain_expertise": 0.55
    },
    "latent_traits": {
      "capability_mean": 0.45,
      "trust_mean": 0.38,
      "friction_tolerance_mean": 0.32,
      "exploration_prob": 0.41
    }
  }
}
```

---

## Observable Metadata (For API/Frontend)

```python
OBSERVABLE_METADATA = {
    "digital_literacy": {
        "name": "Literacia Digital",
        "description": "Familiaridade com tecnologia e interfaces digitais"
    },
    "similar_tool_experience": {
        "name": "Experiência com Ferramentas Similares",
        "description": "Uso prévio de ferramentas semelhantes ao produto"
    },
    "motor_ability": {
        "name": "Capacidade Motora",
        "description": "Habilidade física para interagir com interfaces"
    },
    "time_availability": {
        "name": "Disponibilidade de Tempo",
        "description": "Tempo típico disponível para uso do produto"
    },
    "domain_expertise": {
        "name": "Conhecimento do Domínio",
        "description": "Expertise na área/domínio do produto"
    }
}
```

---

## Relationships

```
Synth (1) ─────────────────► (1) SimulationAttributes
                                      │
                                      ├── (1) SimulationObservables
                                      │
                                      └── (1) SimulationLatentTraits

SimulationResult (1) ──────► (1) SimulationContext
       │
       └── synth_id ─────────► Synth

Interview (1) ──────────────► (0..1) SimulationContext
       │                            (optional - may interview without prior simulation)
       └── synth_id ─────────► Synth
```
