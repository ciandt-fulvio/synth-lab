"""
Monte Carlo simulation engine with Beta-sampled mechanisms and emergent states.

Replaces the old ``engine.py`` with a simplified model:
    1. Sample each mechanism from Beta(mean*15, (1-mean)*15)
    2. Calculate emergent state (7 barriers + 2 appeals)
    3. Compute adoption probability from emergent states
    4. Sample binary adoption via Bernoulli(prob)

References:
    - Spec: specs/040-mechanism-sensitivity-update/spec.md
    - Contracts: specs/040-mechanism-sensitivity-update/contracts/simulation-api.md
    - NumPy Beta distribution: https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.beta.html

Sample usage:
    from synth_lab.services.simulation.feature_monte_carlo import run_simulation
    from synth_lab.domain.entities.feature_mechanisms import FeatureMechanisms

    mechanisms = FeatureMechanisms(irreversibility=0.8, valor_intrinseco=0.9)
    synths = [{"id": "s1", "sensitivities": {"risk_aversion": 0.7, ...}}, ...]
    results = run_simulation(synths, mechanisms, n_executions=100, seed=42)

Expected output:
    SimulationResults(
        outcomes=[SynthOutcome(synth_id="s1", adoption_rate=0.35, ...)],
        aggregate_adoption_rate=0.35,
        n_synths=1,
        n_executions=100,
    )
"""

from dataclasses import dataclass

import numpy as np

from synth_lab.domain.entities.feature_mechanisms import FeatureMechanisms
from synth_lab.domain.entities.user_sensitivities import UserSensitivities
from synth_lab.services.sensitivity_deriver import derive_sensitivities
from synth_lab.services.simulation.emergent_calculator import calculate_emergent_state

# Beta distribution concentration parameter.
# Higher values produce tighter distributions around the mean.
BETA_STRENGTH: int = 15

# Names of the 9 mechanism fields on FeatureMechanisms.
_MECHANISM_FIELDS: list[str] = [
    "irreversibility",
    "network_effect",
    "institutional_trust",
    "habit_displacement",
    "learning_curve",
    "social_visibility",
    "valor_intrinseco",
    "friccao_operacional",
    "frequencia_de_uso",
]

# 9 sensitivity field names (excluding _meta).
_SENSITIVITY_FIELDS: list[str] = [
    "risk_aversion",
    "social_dependency",
    "institutional_trust_level",
    "habit_plasticity",
    "friction_tolerance",
    "pragmatism",
    "digital_capability",
    "motor_ability",
    "subject_domain",
]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class SynthOutcome:
    """Simulation outcome for a single synth."""

    synth_id: str
    adoption_rate: float
    n_executions: int
    mean_probability: float


@dataclass
class SimulationResults:
    """Aggregated simulation results across all synths."""

    outcomes: list[SynthOutcome]
    aggregate_adoption_rate: float
    n_synths: int
    n_executions: int


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _sample_mechanisms(
    mechanisms: FeatureMechanisms,
    rng: np.random.Generator,
) -> FeatureMechanisms:
    """Sample each mechanism from a Beta distribution around its mean.

    For each of the 9 mechanism fields:
        - mean == 0.0 -> return 0.0 (skip sampling, avoids degenerate Beta)
        - mean == 1.0 -> return 1.0 (skip sampling, avoids degenerate Beta)
        - otherwise   -> sample Beta(mean * BETA_STRENGTH, (1 - mean) * BETA_STRENGTH)

    Args:
        mechanisms: Feature mechanisms with mean values in [0, 1].
        rng: NumPy random generator for reproducibility.

    Returns:
        New FeatureMechanisms with sampled values.
    """
    sampled: dict[str, float] = {}
    for field_name in _MECHANISM_FIELDS:
        mean = getattr(mechanisms, field_name)
        if mean == 0.0:
            sampled[field_name] = 0.0
        elif mean == 1.0:
            sampled[field_name] = 1.0
        else:
            alpha = mean * BETA_STRENGTH
            beta = (1.0 - mean) * BETA_STRENGTH
            sampled[field_name] = float(rng.beta(alpha, beta))
    return FeatureMechanisms(**sampled)


def _get_sensitivities(synth_data: dict) -> UserSensitivities:
    """Extract or derive user sensitivities from synth data.

    If ``synth_data`` already contains a ``"sensitivities"`` key, the stored
    values are used directly (excluding ``"_meta"``). Otherwise,
    ``derive_sensitivities`` is called to compute them from demographics.

    Args:
        synth_data: Full synth dict (may contain sensitivities or demographics).

    Returns:
        UserSensitivities populated from stored or derived values.
    """
    stored = synth_data.get("sensitivities")
    if stored is not None:
        kwargs = {k: v for k, v in stored.items() if k != "_meta"}
        return UserSensitivities(**kwargs)

    derived = derive_sensitivities(synth_data)
    kwargs = {k: v for k, v in derived.items() if k != "_meta"}
    return UserSensitivities(**kwargs)


def _calculate_adoption_probability(
    emergent_state: object,
    base_probability: float = 0.5,
    barrier_weight: float = 0.12,
    appeal_weight: float = 0.18,
) -> float:
    """Compute adoption probability from emergent state barriers and appeals.

    Formula:
        prob = base
             - sum(8 barriers) * barrier_weight
             + sum(3 appeals)  * appeal_weight

    Result is clamped to [0.0, 1.0].

    Weights are rebalanced for 8 barriers + 3 appeals (previously 7+2)
    to keep the probability range roughly the same.

    Args:
        emergent_state: EmergentState with barrier and appeal fields.
        base_probability: Starting probability before adjustments.
        barrier_weight: Weight applied to each barrier's contribution.
        appeal_weight: Weight applied to each appeal's contribution.

    Returns:
        Adoption probability in [0.0, 1.0].
    """
    barriers = [
        emergent_state.perceived_risk,
        emergent_state.trust_barrier,
        emergent_state.habit_resistance,
        emergent_state.learning_frustration,
        emergent_state.friction_burden,
        emergent_state.social_pressure,
        emergent_state.network_barrier,
        emergent_state.motor_barrier,
    ]
    appeals = [
        emergent_state.intrinsic_appeal,
        emergent_state.frequency_value,
        emergent_state.domain_advantage,
    ]

    prob = base_probability - sum(barriers) * barrier_weight + sum(appeals) * appeal_weight
    return max(0.0, min(1.0, prob))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_simulation(
    synths: list[dict],
    mechanisms: FeatureMechanisms,
    n_executions: int = 100,
    seed: int | None = None,
) -> SimulationResults:
    """Run Monte Carlo simulation for feature adoption.

    For each synth:
        1. Obtain user sensitivities (stored or derived).
        2. For each execution:
            a. Sample mechanisms from Beta distributions.
            b. Calculate emergent state (barriers + appeals).
            c. Compute adoption probability.
            d. Sample binary outcome via Bernoulli(prob).
        3. Compute adoption_rate = adopted_count / n_executions.

    Args:
        synths: List of synth dicts. Each may contain ``"sensitivities"``
            or demographic data for on-demand derivation.
        mechanisms: Feature mechanisms with mean values in [0, 1].
        n_executions: Number of Monte Carlo iterations per synth.
        seed: Random seed for reproducibility (None for random).

    Returns:
        SimulationResults with per-synth outcomes and aggregate adoption rate.
    """
    rng = np.random.default_rng(seed)
    outcomes: list[SynthOutcome] = []

    for synth in synths:
        synth_id = synth.get("id", "unknown")
        sensitivities = _get_sensitivities(synth)

        adopted_count = 0
        probability_sum = 0.0

        for _ in range(n_executions):
            sampled = _sample_mechanisms(mechanisms, rng)
            emergent = calculate_emergent_state(sampled, sensitivities)
            prob = _calculate_adoption_probability(emergent)
            probability_sum += prob
            if rng.random() < prob:
                adopted_count += 1

        adoption_rate = adopted_count / n_executions
        mean_probability = probability_sum / n_executions

        outcomes.append(
            SynthOutcome(
                synth_id=synth_id,
                adoption_rate=round(adoption_rate, 4),
                n_executions=n_executions,
                mean_probability=round(mean_probability, 4),
            )
        )

    aggregate = sum(o.adoption_rate for o in outcomes) / len(outcomes) if outcomes else 0.0

    return SimulationResults(
        outcomes=outcomes,
        aggregate_adoption_rate=round(aggregate, 4),
        n_synths=len(synths),
        n_executions=n_executions,
    )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    import time

    from synth_lab.domain.entities.emergent_state import EmergentState

    _failures: list[str] = []
    _total = 0

    def _sens(
        ra=0.5, sd=0.5, it=0.5, hp=0.5, ft=0.5, pr=0.5, dc=0.5, ma=0.5, dom=0.5,
    ) -> dict:
        """Build a compact sensitivities dict."""
        return {
            "risk_aversion": ra,
            "social_dependency": sd,
            "institutional_trust_level": it,
            "habit_plasticity": hp,
            "friction_tolerance": ft,
            "pragmatism": pr,
            "digital_capability": dc,
            "motor_ability": ma,
            "subject_domain": dom,
        }

    def _es(**kw) -> EmergentState:
        """Build EmergentState with defaults=0.0 for unspecified fields."""
        defaults = dict(
            perceived_risk=0.0,
            trust_barrier=0.0,
            habit_resistance=0.0,
            learning_frustration=0.0,
            friction_burden=0.0,
            social_pressure=0.0,
            network_barrier=0.0,
            motor_barrier=0.0,
            intrinsic_appeal=0.0,
            frequency_value=0.0,
            domain_advantage=0.0,
        )
        defaults.update(kw)
        return EmergentState(**defaults)

    # ---- Test 1: Beta sampling edge cases ----
    _total += 1
    try:
        rng = np.random.default_rng(42)
        s0 = _sample_mechanisms(FeatureMechanisms(irreversibility=0.0), rng)
        if s0.irreversibility != 0.0:
            _failures.append(f"T1: mean=0.0 should stay 0.0, got {s0.irreversibility}")
        s1 = _sample_mechanisms(FeatureMechanisms(irreversibility=1.0), rng)
        if s1.irreversibility != 1.0:
            _failures.append(f"T1: mean=1.0 should stay 1.0, got {s1.irreversibility}")
        samples = [
            _sample_mechanisms(FeatureMechanisms(irreversibility=0.5), rng).irreversibility
            for _ in range(200)
        ]
        avg = sum(samples) / len(samples)
        if not (0.3 < avg < 0.7):
            _failures.append(f"T1: mean=0.5 average should be ~0.5, got {avg:.4f}")
    except Exception as e:
        _failures.append(f"T1 (Beta sampling): {e}")

    # ---- Test 2: Adoption probability with all zeros -> 0.5 ----
    _total += 1
    try:
        prob = _calculate_adoption_probability(_es())
        if abs(prob - 0.5) > 0.001:
            _failures.append(f"T2: All zeros should give 0.5, got {prob}")
    except Exception as e:
        _failures.append(f"T2 (zero probability): {e}")

    # ---- Test 3: High barriers -> low probability ----
    _total += 1
    try:
        prob = _calculate_adoption_probability(
            _es(
                perceived_risk=0.8,
                trust_barrier=0.7,
                habit_resistance=0.6,
                learning_frustration=0.5,
                friction_burden=0.4,
                social_pressure=0.3,
                network_barrier=0.2,
                motor_barrier=0.3,
            )
        )
        if prob >= 0.3:
            _failures.append(f"T3: High barriers should give low prob, got {prob}")
    except Exception as e:
        _failures.append(f"T3 (high barriers): {e}")

    # ---- Test 4: High appeals -> high probability ----
    _total += 1
    try:
        prob = _calculate_adoption_probability(
            _es(intrinsic_appeal=0.9, frequency_value=0.8, domain_advantage=0.7)
        )
        if prob <= 0.7:
            _failures.append(f"T4: High appeals should give high prob, got {prob}")
    except Exception as e:
        _failures.append(f"T4 (high appeals): {e}")

    # ---- Test 5: Full simulation with 2 synths (young vs elderly) ----
    _total += 1
    try:
        young = {
            "id": "young_tech",
            "sensitivities": _sens(
                ra=0.3, sd=0.6, hp=0.8, ft=0.7, pr=0.7, dc=0.9, ma=0.9, dom=0.6,
            ),
        }
        elderly = {
            "id": "elderly_user",
            "sensitivities": _sens(
                ra=0.9, sd=0.3, it=0.4, hp=0.2, ft=0.2, pr=0.4, dc=0.2, ma=0.4, dom=0.3,
            ),
        }
        mechs = FeatureMechanisms(
            irreversibility=0.7,
            network_effect=0.5,
            institutional_trust=0.6,
            habit_displacement=0.5,
            learning_curve=0.6,
            social_visibility=0.3,
            valor_intrinseco=0.8,
            friccao_operacional=0.4,
            frequencia_de_uso=0.7,
        )
        results = run_simulation([young, elderly], mechs, n_executions=500, seed=42)

        if results.n_synths != 2:
            _failures.append(f"T5: Expected 2 synths, got {results.n_synths}")
        if results.n_executions != 500:
            _failures.append(f"T5: Expected 500 executions, got {results.n_executions}")
        yo, eo = results.outcomes[0], results.outcomes[1]
        if yo.adoption_rate <= eo.adoption_rate:
            _failures.append(
                f"T5: Young ({yo.adoption_rate}) should > elderly ({eo.adoption_rate})"
            )
        for o in results.outcomes:
            if not (0.0 <= o.adoption_rate <= 1.0):
                _failures.append(f"T5: adoption_rate out of range: {o.adoption_rate}")
            if not (0.0 <= o.mean_probability <= 1.0):
                _failures.append(f"T5: mean_probability out of range: {o.mean_probability}")
        if not (0.0 <= results.aggregate_adoption_rate <= 1.0):
            _failures.append(f"T5: aggregate out of range: {results.aggregate_adoption_rate}")
    except Exception as e:
        _failures.append(f"T5 (full simulation): {e}")

    # ---- Test 6: Performance -- 100 synths x 100 executions < 1 second ----
    _total += 1
    try:
        perf_synths = [{"id": f"p{i}", "sensitivities": _sens()} for i in range(100)]
        perf_mechs = FeatureMechanisms(**{f: 0.5 for f in _MECHANISM_FIELDS})
        start = time.perf_counter()
        _ = run_simulation(perf_synths, perf_mechs, n_executions=100, seed=42)
        elapsed = time.perf_counter() - start
        if elapsed > 1.0:
            _failures.append(f"T6: 100x100 took {elapsed:.3f}s (should be < 1s)")
    except Exception as e:
        _failures.append(f"T6 (performance): {e}")

    # ---- Test 7: Reproducibility -- same seed -> same results ----
    _total += 1
    try:
        rs = [{"id": "repro", "sensitivities": _sens(ra=0.6, sd=0.4, pr=0.6, dc=0.7)}]
        rm = FeatureMechanisms(irreversibility=0.5, valor_intrinseco=0.8)
        r1 = run_simulation(rs, rm, n_executions=200, seed=99)
        r2 = run_simulation(rs, rm, n_executions=200, seed=99)
        a1, a2 = r1.outcomes[0].adoption_rate, r2.outcomes[0].adoption_rate
        if a1 != a2:
            _failures.append(f"T7: adoption_rate differs: {a1} vs {a2}")
        p1, p2 = r1.outcomes[0].mean_probability, r2.outcomes[0].mean_probability
        if p1 != p2:
            _failures.append(f"T7: mean_probability differs: {p1} vs {p2}")
    except Exception as e:
        _failures.append(f"T7 (reproducibility): {e}")

    # ---- Final report ----
    if _failures:
        print(f"VALIDATION FAILED - {len(_failures)} of {_total} tests failed:")
        for f in _failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {_total} tests produced expected results")
        sys.exit(0)
