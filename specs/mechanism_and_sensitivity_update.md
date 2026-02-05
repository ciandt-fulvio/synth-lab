# Mechanism and Sensitivity Update Plan

**Created**: 2026-02-05
**Status**: Approved
**Type**: Enhancement

---

## 🎯 Objectives

1. ✅ Create YAML-based derivation system for **7 user sensitivities** from raw synth data
2. ✅ Add **3 new mechanisms** to the feature mechanism system
3. ✅ Integrate sensitivities into **synth_builder** (persist to database)
4. ✅ Update **Monte Carlo simulation** to use sensitivities + 9 mechanisms
5. ✅ Create comprehensive **tests** (validation blocks + pytest)

---

## 📊 Overview

### Current State (6 mechanisms, no sensitivities)
- 6 feature mechanisms exist: irreversibility, network_effect, institutional_trust, habit_displacement, learning_curve, social_visibility
- No user sensitivities defined
- Monte Carlo uses basic probability calculations

### Target State (9 mechanisms, 7 sensitivities)
- 9 feature mechanisms (6 existing + 3 new)
- 7 user sensitivities derived from raw synth data (YAML rules)
- Monte Carlo uses emergent states (mechanism × sensitivity interactions)

---

## 🔢 The 7 User Sensitivities

| # | Sensitivity | Description | Derived From |
|---|-------------|-------------|--------------|
| 1 | `risk_aversion` | Aversão a ações irreversíveis | idade, escolaridade |
| 2 | `social_dependency` | Necessidade de validação social | idade |
| 3 | `institutional_trust_level` | Confiança em instituições | idade, escolaridade |
| 4 | `habit_plasticity` | Flexibilidade para mudar rotinas | idade |
| 5 | `friction_tolerance` | Tolerância a processos complexos | idade, composição_familiar, deficiências |
| 6 | `pragmatism` | Foco em utilidade vs hedônico | idade, ocupação, escolaridade |
| 7 | `digital_capability` | Habilidade técnica digital | idade, escolaridade, deficiências |

---

## 🔧 The 3 New Mechanisms

| # | Mechanism | Description | Range | Polarity |
|---|-----------|-------------|-------|----------|
| 7 | `valor_intrinseco` | Melhora real na vida do usuário | 0=cosmético, 1=transformador | Positiva |
| 8 | `friccao_operacional` | Atrito/passos/erros no uso | 0=1 clique, 1=muitos passos | Negativa |
| 9 | `frequencia_de_uso` | Cadência de uso esperada | 0=raro, 1=diário | Neutra |

---

## 🔗 Mechanism × Sensitivity Interactions

### Interaction Matrix (9 × 7)

| Mechanism | Sensitivities | Emergent State | Effect |
|-----------|--------------|----------------|--------|
| `irreversibility` | `risk_aversion` | `perceived_risk` | Barrier |
| `institutional_trust` | `institutional_trust_level` | `trust_barrier` | Barrier |
| `habit_displacement` | `habit_plasticity` | `habit_resistance` | Barrier |
| `learning_curve` | `digital_capability` | `learning_frustration` | Barrier |
| `friccao_operacional` 🆕 | `friction_tolerance` | `friction_burden` | Barrier |
| `social_visibility` | `social_dependency` | `social_pressure` | Barrier |
| `network_effect` | `social_dependency` | `network_barrier` | Barrier |
| `valor_intrinseco` 🆕 | `pragmatism` | `intrinsic_appeal` | Appeal |
| `frequencia_de_uso` 🆕 | `pragmatism` | `frequency_value` | Appeal |

**Formula**: `emergent_value = mechanism_intensity × user_sensitivity`

---

## 📂 Implementation Plan

### Phase 1: Foundation (Sensitivities)

#### 1.1 Create YAML Rules
**File**: `src/synth_lab/config/sensitivity_rules.yaml`

**Structure**:
```yaml
version: "1.0"
description: "Default sensitivity calibration for Brazilian population"

sensitivities:
  risk_aversion:
    description: "Aversão a ações irreversíveis"
    base: 0.60
    rules:
      - condition: {field: "idade", operator: ">=", value: 60}
        adjustment: 0.10
        reason: "Idosos são mais conservadores"
      - condition: {field: "idade", operator: "<=", value: 25}
        adjustment: -0.05
        reason: "Jovens são mais aventureiros"
  # ... (7 sensitivities total)
```

**Operators supported**:
- Numeric: `>=`, `<=`, `>`, `<`, `==`
- String: `contains` (case-insensitive), `contains_any`, `in`

---

#### 1.2 Create Sensitivity Deriver
**File**: `src/synth_lab/services/sensitivity_deriver.py`

**Functions**:
```python
load_sensitivity_rules(config_name: str) -> dict
  # Load YAML rules

get_nested_value(data: dict, field_path: str) -> Any
  # Access nested fields (e.g., "composicao_familiar.tipo")

evaluate_condition(condition: dict, synth_data: dict) -> bool
  # Evaluate YAML condition against synth data

derive_sensitivities(synth_data: dict, config_name: str) -> dict
  # MAIN FUNCTION: Derive 7 sensitivities + metadata
  # Returns: {
  #   "risk_aversion": 0.73,
  #   "social_dependency": 0.45,
  #   ...
  #   "_meta": {
  #     "derivation_version": "1.0",
  #     "config_name": "sensitivity_rules.yaml",
  #     "applied_rules": ["risk_aversion:Idosos...", ...]
  #   }
  # }
```

**Validation block**: Tests loading config, young person (low risk_aversion), elderly person (high risk_aversion), metadata presence.

---

#### 1.3 Create User Sensitivities Entity
**File**: `src/synth_lab/domain/entities/user_sensitivities.py` (NEW)

**Content**:
```python
class UserSensitivities(BaseModel):
    """User sensitivities (7 total) for mechanism interactions."""

    risk_aversion: float = Field(default=0.5, ge=0.0, le=1.0)
    social_dependency: float = Field(default=0.5, ge=0.0, le=1.0)
    institutional_trust_level: float = Field(default=0.5, ge=0.0, le=1.0)
    habit_plasticity: float = Field(default=0.5, ge=0.0, le=1.0)
    friction_tolerance: float = Field(default=0.5, ge=0.0, le=1.0)
    pragmatism: float = Field(default=0.5, ge=0.0, le=1.0)
    digital_capability: float = Field(default=0.5, ge=0.0, le=1.0)
```

---

#### 1.4 Create Unit Tests
**File**: `tests/unit/services/test_sensitivity_deriver.py`

**Test Cases** (30+):
- Helper functions (get_nested_value, evaluate_condition)
- Load config
- Risk aversion (young vs elderly)
- Habit plasticity (young vs elderly)
- Friction tolerance (single parent, disabilities)
- Digital capability (young vs elderly with disabilities)
- Pragmatism (adult vs creative professional)
- Metadata presence
- All 7 sensitivities present
- Edge cases (missing fields, clamping)
- Parametrized tests by age

**Fixtures**:
- `young_synth_data` (25yo, tech-savvy, living alone)
- `elderly_synth_data` (65yo, low education, disabilities)
- `single_parent_synth_data` (35yo, monoparental, busy)

---

### Phase 2: Integration (Synth Builder)

#### 2.1 Integrate Deriver into Synth Builder
**File**: `src/synth_lab/gen_synth/synth_builder.py`

**Changes**:
```python
from synth_lab.services.sensitivity_deriver import derive_sensitivities

def build_synth(config_data: dict) -> dict:
    """Build synth with demographics, disabilities, and sensitivities."""

    # ... existing code: generate demografia, deficiencias, psicografia ...

    synth_data = {
        "demografia": demografia,
        "deficiencias": deficiencias,
        "psicografia": psicografia,
    }

    # 🆕 DERIVE AND PERSIST SENSITIVITIES
    sensitivities = derive_sensitivities(synth_data)
    synth_data["sensitivities"] = sensitivities

    return synth_data
```

---

#### 2.2 Create Integration Tests
**File**: `tests/integration/test_synth_generation_with_sensitivities.py`

**Tests**:
```python
def test_synth_created_with_sensitivities()
  # Synth should have sensitivities after creation

def test_elderly_synth_has_correct_sensitivities()
  # Elderly synth should have high risk_aversion, low plasticity

def test_sensitivities_persisted_to_database()
  # Sensitivities should be saved to database
```

---

### Phase 3: New Mechanisms

#### 3.1 Add 3 New Mechanisms to Domain Entity
**File**: `src/synth_lab/domain/entities/feature_mechanisms.py`

**Changes**:
```python
class FeatureMechanisms(BaseModel):
    """Feature mechanisms (9 total)."""

    # 6 existing (keep)
    irreversibility: float = Field(default=0.0, ge=0.0, le=1.0)
    network_effect: float = Field(default=0.0, ge=0.0, le=1.0)
    institutional_trust: float = Field(default=0.0, ge=0.0, le=1.0)
    habit_displacement: float = Field(default=0.0, ge=0.0, le=1.0)
    learning_curve: float = Field(default=0.0, ge=0.0, le=1.0)
    social_visibility: float = Field(default=0.0, ge=0.0, le=1.0)

    # 3 NEW 🆕
    valor_intrinseco: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Melhora real na vida (0=cosmético, 1=transformador)"
    )

    friccao_operacional: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Atrito no uso (0=1 clique, 1=muitos passos)"
    )

    frequencia_de_uso: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Cadência de uso (0=raro, 1=diário)"
    )

    def has_any_mechanism(self) -> bool:
        return any([
            self.irreversibility > 0,
            self.network_effect > 0,
            self.institutional_trust > 0,
            self.habit_displacement > 0,
            self.learning_curve > 0,
            self.social_visibility > 0,
            self.valor_intrinseco > 0,  # NEW
            self.friccao_operacional > 0,  # NEW
            self.frequencia_de_uso > 0,  # NEW
        ])
```

---

#### 3.2 Update Seed Script
**File**: `scripts/seed_mechanisms.py`

**Changes**: Add to `MECHANISM_DEFINITIONS`:

```python
# NEW 1: Valor Intrínseco
{
    "key": "valor_intrinseco",
    "label_pt": "Valor Intrínseco",
    "description": "Quanto a feature melhora a vida do usuário",
    "options": [
        {"label": "cosmético (melhora superficial)", "value": 0.00, "display_order": 1},
        {"label": "pequeno ganho de utilidade", "value": 0.25, "display_order": 2},
        {"label": "melhora moderada", "value": 0.50, "display_order": 3},
        {"label": "melhora significativa", "value": 0.75, "display_order": 4},
        {"label": "transformador (muda forma de fazer algo)", "value": 1.00, "display_order": 5},
    ],
},

# NEW 2: Fricção Operacional
{
    "key": "friccao_operacional",
    "label_pt": "Fricção Operacional",
    "description": "Quantidade de atrito/passos/erros no uso",
    "options": [
        {"label": "sem fricção (1 clique)", "value": 0.00, "display_order": 1},
        {"label": "fricção mínima", "value": 0.25, "display_order": 2},
        {"label": "fricção moderada", "value": 0.50, "display_order": 3},
        {"label": "fricção alta (muitos passos)", "value": 0.75, "display_order": 4},
        {"label": "fricção extrema (cadastros, erros)", "value": 1.00, "display_order": 5},
    ],
},

# NEW 3: Frequência de Uso
{
    "key": "frequencia_de_uso",
    "label_pt": "Frequência de Uso",
    "description": "Cadência de uso esperada se adotado",
    "options": [
        {"label": "raríssimo (1x por ano ou menos)", "value": 0.00, "display_order": 1},
        {"label": "ocasional (mensal)", "value": 0.25, "display_order": 2},
        {"label": "regular (semanal)", "value": 0.50, "display_order": 3},
        {"label": "frequente (várias vezes por semana)", "value": 0.75, "display_order": 4},
        {"label": "diário ou mais", "value": 1.00, "display_order": 5},
    ],
},
```

**Execute**:
```bash
DATABASE_URL="postgresql://..." python scripts/seed_mechanisms.py
```

---

### Phase 4: Emergent State Calculation

#### 4.1 Create Emergent State Calculator
**File**: `src/synth_lab/services/simulation/emergent_calculator.py` (NEW)

**Content**:
```python
@dataclass
class InteractionContribution:
    """Single mechanism × sensitivity contribution."""
    mechanism: str
    sensitivity: str
    product: float


@dataclass
class EmergentState:
    """Emergent states from 9 mechanisms × 7 sensitivities."""

    # Barriers (negative - hinder adoption)
    perceived_risk: float
    trust_barrier: float
    habit_resistance: float
    learning_frustration: float
    friction_burden: float
    social_pressure: float
    network_barrier: float

    # Appeals (positive - facilitate adoption)
    intrinsic_appeal: float
    frequency_value: float

    # Metadata
    top_contributors: list[InteractionContribution]
    raw_interactions: dict[str, float]

    @classmethod
    def calculate(
        cls,
        mechanisms: FeatureMechanisms,
        sensitivities: UserSensitivities
    ) -> "EmergentState":
        """Calculate emergent state from interactions."""

        # Barriers
        perceived_risk = mechanisms.irreversibility * sensitivities.risk_aversion
        trust_barrier = mechanisms.institutional_trust * (1 - sensitivities.institutional_trust_level)
        habit_resistance = mechanisms.habit_displacement * (1 - sensitivities.habit_plasticity)
        learning_frustration = mechanisms.learning_curve * (1 - sensitivities.digital_capability)
        friction_burden = mechanisms.friccao_operacional * (1 - sensitivities.friction_tolerance)
        social_pressure = mechanisms.social_visibility * sensitivities.social_dependency
        network_barrier = mechanisms.network_effect * (1 - sensitivities.social_dependency)

        # Appeals
        intrinsic_appeal = mechanisms.valor_intrinseco * sensitivities.pragmatism
        frequency_value = mechanisms.frequencia_de_uso * sensitivities.pragmatism

        # ... track interactions and top contributors ...

        return cls(...)
```

---

#### 4.2 Create Emergent State Tests
**File**: `tests/integration/test_emergent_state_calculation.py`

**Tests**:
```python
def test_high_risk_feature_with_risk_averse_user()
  # High irreversibility × high risk_aversion = high perceived_risk

def test_intrinsic_value_boosts_adoption()
  # High valor_intrínseco × high pragmatism = high appeal

def test_friction_with_intolerant_user()
  # High fricção_operacional × low friction_tolerance = high burden
```

---

### Phase 5: Monte Carlo Integration

#### 5.1 Update Probability Calculator
**File**: `src/synth_lab/services/simulation/probability_calculator.py`

**Changes**:
```python
def calculate_probability_with_emergent(
    scorecard: dict,
    emergent_state: EmergentState
) -> float:
    """Calculate probability considering emergent states."""

    # Base probability from scorecard
    base_prob = calculate_base_probability(scorecard)

    # Sum barriers (negative impact)
    total_barriers = (
        emergent_state.perceived_risk +
        emergent_state.trust_barrier +
        emergent_state.habit_resistance +
        emergent_state.learning_frustration +
        emergent_state.friction_burden +
        emergent_state.social_pressure +
        emergent_state.network_barrier
    )

    # Sum appeals (positive impact)
    total_appeals = (
        emergent_state.intrinsic_appeal +
        emergent_state.frequency_value
    )

    # Apply adjustments (weights TBD - calibrate with real data)
    barrier_penalty = total_barriers * 0.15
    appeal_boost = total_appeals * 0.20

    adjusted_prob = base_prob - barrier_penalty + appeal_boost

    return max(0.0, min(1.0, adjusted_prob))
```

---

#### 5.2 Update Monte Carlo Engine
**File**: `src/synth_lab/services/simulation/simulation_engine.py`

**Changes**:
```python
from synth_lab.services.sensitivity_deriver import derive_sensitivities
from synth_lab.services.simulation.emergent_calculator import EmergentState
from synth_lab.services.simulation.probability_calculator import calculate_probability_with_emergent

def run_monte_carlo(
    experiment_id: str,
    synth_group_id: str,
    n_executions: int = 100
) -> dict:
    """Run Monte Carlo with mechanism-based approach."""

    experiment = get_experiment(experiment_id)
    synths = get_synths(synth_group_id)

    mechanisms = FeatureMechanisms(**experiment.scorecard_data.get("mechanisms", {}))

    outcomes = []

    for synth in synths:
        # Get sensitivities (already persisted or derive on-demand)
        if "sensitivities" in synth.data:
            sens_dict = synth.data["sensitivities"]
        else:
            sens_dict = derive_sensitivities(synth.data)

        sensitivities = UserSensitivities(**sens_dict)

        for execution in range(n_executions):
            # Calculate emergent state
            emergent = EmergentState.calculate(mechanisms, sensitivities)

            # Calculate probability with emergent adjustments
            probability = calculate_probability_with_emergent(
                scorecard=experiment.scorecard_data,
                emergent_state=emergent
            )

            # Sample outcome
            outcome = {
                "synth_id": synth.id,
                "execution": execution,
                "adotou": probability > np.random.random(),
                "probability": probability,
                "emergent_state": emergent.to_dict(),
            }
            outcomes.append(outcome)

    return aggregate_outcomes(outcomes)
```

---

## 📊 Summary of Changes

### New Files (7)
1. ✅ `src/synth_lab/config/sensitivity_rules.yaml`
2. ✅ `src/synth_lab/services/sensitivity_deriver.py`
3. ✅ `src/synth_lab/domain/entities/user_sensitivities.py`
4. ✅ `src/synth_lab/services/simulation/emergent_calculator.py`
5. ✅ `tests/unit/services/test_sensitivity_deriver.py`
6. ✅ `tests/integration/test_synth_generation_with_sensitivities.py`
7. ✅ `tests/integration/test_emergent_state_calculation.py`

### Modified Files (5)
1. ✅ `src/synth_lab/domain/entities/feature_mechanisms.py` (+ 3 mechanisms)
2. ✅ `src/synth_lab/gen_synth/synth_builder.py` (integrate deriver)
3. ✅ `scripts/seed_mechanisms.py` (+ 3 mechanisms seed data)
4. ✅ `src/synth_lab/services/simulation/probability_calculator.py` (use emergent)
5. ✅ `src/synth_lab/services/simulation/simulation_engine.py` (integrate emergent)

---

## 🧪 Testing Strategy

### Level 1: Validation Blocks (for agents)
- Embedded in production code (`if __name__ == "__main__"`)
- Quick smoke tests during development
- Run: `python src/synth_lab/services/sensitivity_deriver.py`

### Level 2: Unit Tests (pytest)
- Comprehensive test coverage (30+ test cases)
- Parametrized tests for age ranges
- Edge case handling
- Run: `pytest tests/unit/services/test_sensitivity_deriver.py -v`

### Level 3: Integration Tests (pytest)
- End-to-end synth generation with sensitivities
- Database persistence validation
- Emergent state calculation correctness
- Run: `pytest tests/integration/ -v`

---

## 🚀 Execution Commands

```bash
# 1. Run sensitivity deriver validation
python src/synth_lab/services/sensitivity_deriver.py

# 2. Run unit tests
pytest tests/unit/services/test_sensitivity_deriver.py -v

# 3. Seed new mechanisms to database
DATABASE_URL="postgresql://synthlab:synthlab@localhost:5432/synthlab" \
python scripts/seed_mechanisms.py

# 4. Run integration tests
pytest tests/integration/test_synth_generation_with_sensitivities.py -v
pytest tests/integration/test_emergent_state_calculation.py -v

# 5. Run full test suite
pytest tests/ -v
```

---

## 🎯 Success Criteria

- ✅ All 7 sensitivities derive correctly from synth data
- ✅ YAML rules are transparent and auditable
- ✅ New synths have sensitivities persisted to database
- ✅ All 3 new mechanisms seed successfully
- ✅ Monte Carlo produces different outcomes for same scorecard with different mechanisms
- ✅ Emergent states correctly calculate mechanism × sensitivity interactions
- ✅ All validation blocks pass
- ✅ All unit tests pass (100% coverage for deriver)
- ✅ All integration tests pass

---

## 📝 Future Work (Out of Scope)

- Multiple YAML calibrations per user context
- Script to recalculate sensitivities for existing synths
- UI for viewing/editing sensitivity rules
- Calibration of barrier_penalty and appeal_boost weights with real data
- A/B testing old vs new Monte Carlo approach
- Performance optimization for large synth populations

---

## 🔗 References

- Spec 038: `specs/038-mechanism-based-simulation/`
- Spec 039: `specs/039-narrative-mechanism-config/`
- CLAUDE.md: Architecture and validation guidelines
