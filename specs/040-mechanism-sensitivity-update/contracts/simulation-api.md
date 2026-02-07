# API Contracts: Mechanism & Sensitivity Update

**Feature**: 040-mechanism-sensitivity-update
**Date**: 2026-02-06

## Nota

Esta feature **não adiciona novos endpoints** — ela modifica o comportamento interno do motor de simulação e da geração de synths. Os endpoints existentes continuam com a mesma interface externa.

## Contratos Internos (Service Layer)

### 1. SensitivityDeriver

```python
# src/synth_lab/services/sensitivity_deriver.py

def load_sensitivity_rules(config_name: str = "sensitivity_rules") -> dict:
    """Carrega YAML rules do diretório config/."""

def get_nested_value(data: dict, field_path: str) -> Any:
    """Acessa campos aninhados (ex: 'demografia.idade')."""

def evaluate_condition(condition: dict, synth_data: dict) -> bool:
    """Avalia condição YAML contra dados do synth."""

def derive_sensitivities(
    synth_data: dict,
    config_name: str = "sensitivity_rules"
) -> dict:
    """
    Função principal. Retorna dict com 7 sensibilidades + metadata.

    Input:
        synth_data = {
            "demografia": {"idade": 25, "escolaridade": "ensino superior completo", ...},
            "deficiencias": {"motora": {"tipo": "nenhuma"}, ...},
            "composicao_familiar": {"tipo": "casal com filhos", ...},
        }

    Output:
        {
            "risk_aversion": 0.50,
            "social_dependency": 0.60,
            "institutional_trust_level": 0.55,
            "habit_plasticity": 0.65,
            "friction_tolerance": 0.55,
            "pragmatism": 0.60,
            "digital_capability": 0.75,
            "_meta": {
                "derivation_version": "1.0",
                "config_name": "sensitivity_rules",
                "applied_rules": [
                    "risk_aversion: Jovens são mais aventureiros",
                    "digital_capability: Nativos digitais",
                    "digital_capability: Mais escolaridade → mais digital"
                ]
            }
        }
    """
```

### 2. EmergentCalculator

```python
# src/synth_lab/services/simulation/emergent_calculator.py

def calculate_emergent_state(
    mechanisms: FeatureMechanisms,
    sensitivities: UserSensitivities,
) -> EmergentState:
    """
    Calcula 9 estados emergentes.

    Input:
        mechanisms = FeatureMechanisms(
            irreversibility=0.8, valor_intrinseco=0.9, ...
        )
        sensitivities = UserSensitivities(
            risk_aversion=0.7, pragmatism=0.8, ...
        )

    Output:
        EmergentState(
            # 7 barriers
            perceived_risk=0.56,        # 0.8 × 0.7
            trust_barrier=0.0,
            habit_resistance=0.0,
            learning_frustration=0.0,
            friction_burden=0.0,
            social_pressure=0.0,
            network_barrier=0.0,
            # 2 appeals
            intrinsic_appeal=0.72,      # 0.9 × 0.8
            frequency_value=0.0,
            # metadata
            top_contributors=[...],
            raw_interactions={...},
        )
    """
```

### 3. FeatureMonteCarloEngine

```python
# src/synth_lab/services/simulation/feature_monte_carlo.py

BETA_STRENGTH = 15  # Fixo

class FeatureMonteCarloEngine:
    def __init__(self, seed: int | None = None):
        self.rng = np.random.default_rng(seed)

    def run_simulation(
        self,
        synths: list[dict],
        mechanisms: FeatureMechanisms,
        n_executions: int = 100,
    ) -> SimulationResults:
        """
        Input:
            synths: lista de dicts com synth data (incluindo sensitivities)
            mechanisms: 9 mecanismos com mean values [0,1]
            n_executions: iterações por synth

        Output:
            SimulationResults com:
            - synth_outcomes: list[SynthOutcomeResult] com adoption_rate por synth
            - aggregated_adoption_rate: float
            - total_synths: int
            - n_executions: int
            - execution_time_seconds: float
        """

    def _sample_mechanisms(
        self,
        mechanisms: FeatureMechanisms,
    ) -> FeatureMechanisms:
        """
        Amostra cada mecanismo de Beta(mean×strength, (1-mean)×strength).
        Mecanismos com mean=0.0 ficam 0.0 e mean=1.0 ficam 1.0 (sem amostragem — evita Beta degenerada).
        """

    def _calculate_adoption_probability(
        self,
        emergent_state: EmergentState,
        base_probability: float = 0.5,
        barrier_weight: float = 0.15,
        appeal_weight: float = 0.20,
    ) -> float:
        """
        prob = base - sum(barriers) × barrier_weight + sum(appeals) × appeal_weight
        clamped [0.0, 1.0]
        """
```

## Dados Persistidos

### Synth Data (JSONB) — novo campo `sensitivities`

```json
{
    "id": "a1b2c3",
    "nome": "João Silva",
    "demografia": { "idade": 25, "escolaridade": "ensino superior completo", ... },
    "deficiencias": { "motora": { "tipo": "nenhuma" }, ... },
    "sensitivities": {
        "risk_aversion": 0.50,
        "social_dependency": 0.60,
        "institutional_trust_level": 0.55,
        "habit_plasticity": 0.65,
        "friction_tolerance": 0.55,
        "pragmatism": 0.60,
        "digital_capability": 0.75,
        "_meta": {
            "derivation_version": "1.0",
            "config_name": "sensitivity_rules",
            "applied_rules": ["..."]
        }
    }
}
```

### Experiment scorecard_data (JSONB) — campo `mechanisms` expandido

```json
{
    "mechanisms": {
        "irreversibility": 0.75,
        "network_effect": 0.50,
        "institutional_trust": 0.25,
        "habit_displacement": 0.50,
        "learning_curve": 0.75,
        "social_visibility": 0.25,
        "valor_intrinseco": 0.75,
        "friccao_operacional": 0.50,
        "frequencia_de_uso": 0.50
    }
}
```
