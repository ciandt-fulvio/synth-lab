"""
Explanation service for mechanism×sensitivity segment explanations.

Aggregates emergent state contributions across segment synths and compares
to full population to identify differentiating factors.

References:
    - Spec: specs/038-mechanism-based-simulation/spec.md
    - User Story 3: View emergent states explanation

Sample usage:
    from synth_lab.services.analysis.explanation_service import explain_segment

    explanation = explain_segment(
        synth_outcomes=analysis_run.synth_outcomes,
        segment_synth_ids=["synth_1", "synth_2"],
        compare_to_population=True,
    )

Expected output:
    SegmentExplanation with segment_avg_success, population_avg_success,
    top_differentiating_factors, and explanation_text
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from loguru import logger


@dataclass
class InteractionContribution:
    """Single mechanism × sensitivity interaction contribution."""

    mechanism: str
    sensitivity: str
    product: float


@dataclass
class DifferentiatingFactor:
    """Factor that differentiates segment from population."""

    interaction: InteractionContribution
    segment_avg: float
    population_avg: float
    delta: float


@dataclass
class SegmentExplanation:
    """Explanation of segment behavior via mechanism×sensitivity interactions."""

    segment_size: int
    segment_avg_success: float
    population_avg_success: float
    top_differentiating_factors: list[DifferentiatingFactor]
    explanation_text: str


def explain_segment(
    synth_outcomes: list[dict],
    segment_synth_ids: list[str],
    compare_to_population: bool = True,
    max_factors: int = 3,
) -> SegmentExplanation:
    """
    Generate explanation for why a segment of synths behaves differently.

    Aggregates mechanism×sensitivity interactions across segment synths
    and compares to the full population to identify top differentiating factors.

    Args:
        synth_outcomes: List of synth outcome dicts with synth_id, success_rate,
                       and synth_attributes containing emergent_explanation.
        segment_synth_ids: List of synth IDs that define the segment to explain.
        compare_to_population: Whether to compare to population or just show segment values.
        max_factors: Maximum number of differentiating factors to return.

    Returns:
        SegmentExplanation with success rates, differentiating factors, and explanation text.
    """
    log = logger.bind(component="explanation_service")

    # Separate segment and population outcomes
    segment_outcomes = []
    population_outcomes = []
    segment_set = set(segment_synth_ids)

    for outcome in synth_outcomes:
        synth_id = outcome.get("synth_id", "")
        if synth_id in segment_set:
            segment_outcomes.append(outcome)
        population_outcomes.append(outcome)

    if not segment_outcomes:
        log.warning("No matching synths found for segment", segment_ids=segment_synth_ids[:5])
        return SegmentExplanation(
            segment_size=0,
            segment_avg_success=0.0,
            population_avg_success=_calculate_avg_success(population_outcomes),
            top_differentiating_factors=[],
            explanation_text="No synths found matching the specified segment IDs.",
        )

    # Calculate success rates
    segment_avg_success = _calculate_avg_success(segment_outcomes)
    population_avg_success = _calculate_avg_success(population_outcomes)

    # Extract interaction values
    segment_interactions = _extract_interactions(segment_outcomes)
    population_interactions = _extract_interactions(population_outcomes)

    # Calculate differentiating factors
    factors = _calculate_differentiating_factors(
        segment_interactions,
        population_interactions,
        compare_to_population,
        max_factors,
    )

    # Generate explanation text
    explanation_text = _generate_explanation_text(
        segment_size=len(segment_outcomes),
        segment_avg_success=segment_avg_success,
        population_avg_success=population_avg_success,
        factors=factors,
    )

    log.info(
        "Segment explanation generated",
        segment_size=len(segment_outcomes),
        population_size=len(population_outcomes),
        n_factors=len(factors),
    )

    return SegmentExplanation(
        segment_size=len(segment_outcomes),
        segment_avg_success=round(segment_avg_success, 3),
        population_avg_success=round(population_avg_success, 3),
        top_differentiating_factors=factors,
        explanation_text=explanation_text,
    )


def _calculate_avg_success(outcomes: list[dict]) -> float:
    """Calculate average success rate across outcomes."""
    if not outcomes:
        return 0.0
    rates = [o.get("success_rate", 0.0) for o in outcomes]
    return mean(rates) if rates else 0.0


def _extract_interactions(outcomes: list[dict]) -> dict[str, list[float]]:
    """
    Extract interaction values from outcomes.

    Returns dict mapping interaction key (mechanism:sensitivity) to list of values.
    """
    interactions: dict[str, list[float]] = {}

    for outcome in outcomes:
        attrs = outcome.get("synth_attributes", {})
        explanation = attrs.get("emergent_explanation", {})
        raw = explanation.get("raw_interactions", {})

        for key, value in raw.items():
            if key not in interactions:
                interactions[key] = []
            interactions[key].append(value)

    return interactions


def _calculate_differentiating_factors(
    segment_interactions: dict[str, list[float]],
    population_interactions: dict[str, list[float]],
    compare_to_population: bool,
    max_factors: int,
) -> list[DifferentiatingFactor]:
    """Calculate top differentiating factors between segment and population."""
    factors = []

    for key, segment_values in segment_interactions.items():
        pop_values = population_interactions.get(key, [])
        if not segment_values:
            continue

        segment_avg = mean(segment_values)
        pop_avg = mean(pop_values) if pop_values else 0.0
        delta = segment_avg - pop_avg if compare_to_population else segment_avg

        # Parse key into mechanism and sensitivity
        parts = key.split(":")
        if len(parts) == 2:
            mechanism, sensitivity = parts
        else:
            mechanism, sensitivity = key, "unknown"

        factors.append(
            DifferentiatingFactor(
                interaction=InteractionContribution(
                    mechanism=mechanism,
                    sensitivity=sensitivity,
                    product=round(segment_avg, 3),
                ),
                segment_avg=round(segment_avg, 3),
                population_avg=round(pop_avg, 3),
                delta=round(delta, 3),
            )
        )

    # Sort by absolute delta (biggest differences first)
    factors.sort(key=lambda f: abs(f.delta), reverse=True)

    return factors[:max_factors]


def _generate_explanation_text(
    segment_size: int,
    segment_avg_success: float,
    population_avg_success: float,
    factors: list[DifferentiatingFactor],
) -> str:
    """Generate human-readable explanation text."""
    if not factors:
        return (
            f"Segment of {segment_size} synths has {segment_avg_success:.1%} success rate "
            f"(population: {population_avg_success:.1%}). No mechanism×sensitivity interactions found."
        )

    diff_pct = (segment_avg_success - population_avg_success) * 100
    direction = "higher" if diff_pct > 0 else "lower"

    lines = [
        f"Segment of {segment_size} synths has {segment_avg_success:.1%} success rate, "
        f"{abs(diff_pct):.1f}pp {direction} than population ({population_avg_success:.1%}).",
        "",
        "Top differentiating factors:",
    ]

    for i, factor in enumerate(factors, 1):
        interaction = factor.interaction
        delta_direction = "higher" if factor.delta > 0 else "lower"
        lines.append(
            f"  {i}. {interaction.mechanism} × {interaction.sensitivity}: "
            f"segment avg {factor.segment_avg:.2f} is {abs(factor.delta):.2f} {delta_direction} "
            f"than population avg {factor.population_avg:.2f}"
        )

    return "\n".join(lines)


# =============================================================================
# Validation
# =============================================================================

if __name__ == "__main__":
    import sys

    all_validation_failures: list[str] = []
    total_tests = 0

    # Test 1: Basic segment explanation
    total_tests += 1
    try:
        outcomes = [
            {
                "synth_id": "synth_1",
                "success_rate": 0.8,
                "synth_attributes": {
                    "emergent_explanation": {
                        "raw_interactions": {
                            "irreversibility:risk_aversion": 0.72,
                            "network_effect:social_dependency": 0.24,
                        }
                    }
                },
            },
            {
                "synth_id": "synth_2",
                "success_rate": 0.7,
                "synth_attributes": {
                    "emergent_explanation": {
                        "raw_interactions": {
                            "irreversibility:risk_aversion": 0.68,
                            "network_effect:social_dependency": 0.28,
                        }
                    }
                },
            },
            {
                "synth_id": "synth_3",
                "success_rate": 0.4,
                "synth_attributes": {
                    "emergent_explanation": {
                        "raw_interactions": {
                            "irreversibility:risk_aversion": 0.18,
                            "network_effect:social_dependency": 0.56,
                        }
                    }
                },
            },
        ]

        result = explain_segment(
            synth_outcomes=outcomes,
            segment_synth_ids=["synth_1", "synth_2"],
        )

        if result.segment_size != 2:
            all_validation_failures.append(f"segment_size should be 2: {result.segment_size}")
        if result.segment_avg_success != 0.75:
            all_validation_failures.append(
                f"segment_avg_success should be 0.75: {result.segment_avg_success}"
            )
        # Population includes all 3, so avg = (0.8 + 0.7 + 0.4) / 3 ≈ 0.633
        expected_pop = round((0.8 + 0.7 + 0.4) / 3, 3)
        if result.population_avg_success != expected_pop:
            all_validation_failures.append(
                f"population_avg_success should be {expected_pop}: {result.population_avg_success}"
            )
    except Exception as e:
        all_validation_failures.append(f"Basic segment explanation failed: {e}")

    # Test 2: Empty segment
    total_tests += 1
    try:
        result = explain_segment(
            synth_outcomes=outcomes,
            segment_synth_ids=["nonexistent_synth"],
        )
        if result.segment_size != 0:
            all_validation_failures.append(f"Empty segment size should be 0: {result.segment_size}")
        if "No synths found" not in result.explanation_text:
            all_validation_failures.append("Empty segment should have 'No synths found' message")
    except Exception as e:
        all_validation_failures.append(f"Empty segment test failed: {e}")

    # Test 3: Differentiating factors sorted by absolute delta
    total_tests += 1
    try:
        result = explain_segment(
            synth_outcomes=outcomes,
            segment_synth_ids=["synth_1", "synth_2"],
            max_factors=2,
        )
        if len(result.top_differentiating_factors) > 2:
            all_validation_failures.append(
                f"max_factors=2 should limit factors: {len(result.top_differentiating_factors)}"
            )
        # First factor should have biggest delta
        if result.top_differentiating_factors:
            first_delta = abs(result.top_differentiating_factors[0].delta)
            for factor in result.top_differentiating_factors[1:]:
                if abs(factor.delta) > first_delta:
                    all_validation_failures.append("Factors not sorted by absolute delta")
                    break
    except Exception as e:
        all_validation_failures.append(f"Differentiating factors test failed: {e}")

    # Test 4: No emergent_explanation in outcomes (graceful handling)
    total_tests += 1
    try:
        basic_outcomes = [
            {"synth_id": "s1", "success_rate": 0.5, "synth_attributes": {}},
            {"synth_id": "s2", "success_rate": 0.6, "synth_attributes": {}},
        ]
        result = explain_segment(
            synth_outcomes=basic_outcomes,
            segment_synth_ids=["s1"],
        )
        if result.segment_size != 1:
            all_validation_failures.append("Should handle missing emergent_explanation")
        if result.top_differentiating_factors:
            all_validation_failures.append("Should have no factors without emergent_explanation")
    except Exception as e:
        all_validation_failures.append(f"Missing emergent_explanation test failed: {e}")

    # Test 5: Explanation text generation
    total_tests += 1
    try:
        result = explain_segment(
            synth_outcomes=outcomes,
            segment_synth_ids=["synth_1", "synth_2"],
        )
        if "success rate" not in result.explanation_text.lower():
            all_validation_failures.append("Explanation should mention success rate")
        if "higher" not in result.explanation_text.lower() and "lower" not in result.explanation_text.lower():
            all_validation_failures.append("Explanation should mention direction")
    except Exception as e:
        all_validation_failures.append(f"Explanation text test failed: {e}")

    # Test 6: InteractionContribution and DifferentiatingFactor dataclasses
    total_tests += 1
    try:
        contrib = InteractionContribution(
            mechanism="irreversibility",
            sensitivity="risk_aversion",
            product=0.72,
        )
        factor = DifferentiatingFactor(
            interaction=contrib,
            segment_avg=0.72,
            population_avg=0.45,
            delta=0.27,
        )
        if contrib.mechanism != "irreversibility":
            all_validation_failures.append("InteractionContribution mechanism incorrect")
        if factor.delta != 0.27:
            all_validation_failures.append("DifferentiatingFactor delta incorrect")
    except Exception as e:
        all_validation_failures.append(f"Dataclass test failed: {e}")

    # Final validation result
    if all_validation_failures:
        failed = len(all_validation_failures)
        print(f"VALIDATION FAILED - {failed} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
