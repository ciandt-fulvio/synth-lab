"""
Context formatter for simulation results in interviews.

Formats SimulationContext into text for interviewee prompts,
ensuring interview responses are coherent with prior simulation results.

References:
    - Spec: specs/022-observable-latent-traits/spec.md (FR-016, FR-017, US2)
    - Data model: specs/022-observable-latent-traits/data-model.md
"""

from dataclasses import dataclass
from typing import Literal

from synth_lab.domain.entities.simulation_context import SimulationContext
from synth_lab.domain.entities.synth_outcome import SynthOutcome


@dataclass
class ExperienceClassification:
    """Classification of experience based on simulation results."""

    sentiment: Literal["positive", "negative", "neutral"]
    reason: str
    non_attempt_reason: str | None = None


def classify_experience(
    synth_outcome: SynthOutcome,
    avg_adopted_rate: float,
    threshold: float = 0.05) -> ExperienceClassification:
    """
    Classify synth experience based on simulation results.

    Compares individual performance against group average to determine
    appropriate sentiment for interview context generation.

    Args:
        synth_outcome: Individual synth simulation results.
        avg_adopted_rate: Average adopted rate across all synths in analysis.
        threshold: Deviation from average to classify as positive/negative.
                   Default 0.05 (5%).

    Returns:
        ExperienceClassification with sentiment, reason, and non_attempt_reason.

    Rules:
        - POSITIVE: adopted_rate > avg + threshold
        - NEGATIVE: adopted_rate < avg - threshold
        - NEUTRAL: adopted_rate within threshold of average
    """
    adopted_rate = synth_outcome.adopted_rate
    attrs = synth_outcome.synth_attributes

    # Determine sentiment based on comparison with average
    if adopted_rate > avg_adopted_rate + threshold:
        sentiment: Literal["positive", "negative", "neutral"] = "positive"
        reason = f"Adoção {adopted_rate:.0%} acima da média ({avg_adopted_rate:.0%})"
    elif adopted_rate < avg_adopted_rate - threshold:
        sentiment = "negative"
        reason = f"Adoção {adopted_rate:.0%} abaixo da média ({avg_adopted_rate:.0%})"
    else:
        sentiment = "neutral"
        reason = f"Adoção {adopted_rate:.0%} próximo da média ({avg_adopted_rate:.0%})"

    # Generate behavior description based on latent traits and adopted rate
    latent = attrs.latent_traits
    observables = attrs.observables

    behavior_reason = _generate_behavior_description(
        adopted_rate=adopted_rate,
        digital_literacy=observables.digital_literacy,
        trust_mean=latent.trust_mean,
        exploration_prob=latent.exploration_prob,
        friction_tolerance=latent.friction_tolerance_mean)

    return ExperienceClassification(
        sentiment=sentiment,
        reason=reason,
        non_attempt_reason=behavior_reason)


def _generate_behavior_description(
    adopted_rate: float,
    digital_literacy: float,
    trust_mean: float,
    exploration_prob: float,
    friction_tolerance: float) -> str:
    """
    Generate deterministic behavior description based on synth attributes.

    Returns a human-readable explanation of the synth's behavior pattern
    based on their latent traits and observable attributes.
    """
    parts = []

    # Describe adoption behavior
    if adopted_rate < 0.3:
        parts.append("Raramente adota funcionalidades novas")
    elif adopted_rate < 0.6:
        parts.append("Adota funcionalidades novas apenas quando necessário")
    elif adopted_rate < 0.8:
        parts.append("Geralmente disposto(a) a adotar funcionalidades")
    else:
        parts.append("Sempre adota funcionalidades disponíveis")

    # Add reason based on dominant trait
    if digital_literacy < 0.3:
        parts.append("pode não perceber que a funcionalidade existe ou como acessá-la")
    elif trust_mean < 0.3:
        parts.append("prefere métodos tradicionais por insegurança com tecnologia")
    elif exploration_prob < 0.3:
        parts.append("prefere seguir padrões conhecidos a explorar novidades")
    elif friction_tolerance < 0.3:
        parts.append("desiste facilmente quando encontra dificuldades")
    elif digital_literacy > 0.7 and trust_mean > 0.7:
        parts.append("confortável com tecnologia e confiante em novas soluções")
    elif adopted_rate > 0.6:
        parts.append("adapta-se bem quando decide experimentar")
    else:
        parts.append("experiência mista com novas funcionalidades")

    return "; ".join(parts)


def create_simulation_context_from_outcome(outcome: SynthOutcome) -> SimulationContext:
    """
    Create SimulationContext from SynthOutcome entity.

    Converts the outcome's rates into a SimulationContext that can be
    formatted for interview prompts.

    Args:
        outcome: SynthOutcome with simulation results

    Returns:
        SimulationContext populated from outcome data

    Example:
        >>> outcome = SynthOutcome(
        ...     analysis_id="ana_12345678",
        ...     synth_id="abc123",
        ...     adopted_rate=0.60,
        ...     not_adopted_rate=0.40,
        ...     synth_attributes=...,
        ... )
        >>> ctx = create_simulation_context_from_outcome(outcome)
        >>> ctx.adopted_rate
        0.6
    """
    return SimulationContext(
        synth_id=outcome.synth_id,
        analysis_id=outcome.analysis_id,
        adopted_rate=outcome.adopted_rate,
        not_adopted_rate=outcome.not_adopted_rate,
        n_executions=100,  # Default, not stored in outcome
    )


def format_simulation_context(context: SimulationContext) -> str:
    """
    Format SimulationContext into text for interviewee prompt.

    Creates a narrative description of the synth's prior experience based on
    simulation results. The text will be inserted into the interviewee's
    initial_context_section.

    Args:
        context: SimulationContext with simulation results

    Returns:
        Formatted text describing prior experience

    Example:
        >>> ctx = SimulationContext(
        ...     synth_id="abc123",
        ...     analysis_id="ana_12345678",
        ...     adopted_rate=0.60,
        ...     not_adopted_rate=0.40,
        ...     n_executions=100,
        ... )
        >>> text = format_simulation_context(ctx)
        >>> "60%" in text  # adopted rate mentioned
        True
    """
    # Calculate percentages for readability
    adopted_pct = int(context.adopted_rate * 100)
    not_adopted_pct = int(context.not_adopted_rate * 100)

    # Get performance label
    perf_label = context.performance_label

    # Build narrative based on adoption rate
    if context.adopted_rate >= 0.8:
        adoption_narrative = (
            f"Você adotou esta funcionalidade em {adopted_pct}% das situações. "
            f"Seu desempenho foi {perf_label}."
        )
    elif context.adopted_rate >= 0.6:
        adoption_narrative = (
            f"Você adotou esta funcionalidade em {adopted_pct}% das situações, "
            f"enquanto em {not_adopted_pct}% não adotou. "
            f"Seu desempenho geral foi {perf_label}."
        )
    elif context.adopted_rate >= 0.4:
        adoption_narrative = (
            f"Você adotou esta funcionalidade em {adopted_pct}% das situações, "
            f"mas não adotou em {not_adopted_pct}%. "
            f"Seu desempenho foi {perf_label}."
        )
    elif context.adopted_rate >= 0.2:
        adoption_narrative = (
            f"Você teve dificuldades com a adoção: apenas {adopted_pct}% de adoção, "
            f"com {not_adopted_pct}% de não adoção. Seu desempenho foi {perf_label}."
        )
    else:
        adoption_narrative = (
            f"Você encontrou muita dificuldade: apenas {adopted_pct}% de adoção, "
            f"com {not_adopted_pct}% de não adoção. Desempenho {perf_label}."
        )

    # Combine narratives
    return f"""[CONTEXTO DA SIMULAÇÃO]
{adoption_narrative}

Baseie suas respostas nesta experiência prévia. Se você adotou frequentemente,
demonstre confiança. Se teve dificuldades, mostre hesitação ou frustração apropriadas."""


def format_simulation_context_brief(context: SimulationContext) -> str:
    """
    Format a brief version of simulation context.

    Useful for logging or debugging.

    Args:
        context: SimulationContext with simulation results

    Returns:
        Brief one-line summary
    """
    return (
        f"Adoção: {context.adopted_rate:.0%}, "
        f"Não adoção: {context.not_adopted_rate:.0%} "
        f"({context.performance_label})"
    )


if __name__ == "__main__":
    import sys

    all_validation_failures: list[str] = []
    total_tests = 0

    # Test 1: High adopted rate formatting
    total_tests += 1
    try:
        ctx = SimulationContext(
            synth_id="abc123",
            analysis_id="ana_12345678",
            adopted_rate=0.85,
            not_adopted_rate=0.15,
            n_executions=100)
        text = format_simulation_context(ctx)
        if "85%" not in text:
            all_validation_failures.append("High adopted rate not mentioned")
        if "excelente" not in text:
            all_validation_failures.append("'excelente' label not found for high adoption")
    except Exception as e:
        all_validation_failures.append(f"High adoption test failed: {e}")

    # Test 2: Low adopted rate formatting
    total_tests += 1
    try:
        ctx = SimulationContext(
            synth_id="abc123",
            analysis_id="ana_12345678",
            adopted_rate=0.15,
            not_adopted_rate=0.85,
            n_executions=100)
        text = format_simulation_context(ctx)
        if "15%" not in text:
            all_validation_failures.append("Low adopted rate not mentioned")
        if "muito baixo" not in text:
            all_validation_failures.append("'muito baixo' label not found for low adoption")
    except Exception as e:
        all_validation_failures.append(f"Low adoption test failed: {e}")

    # Test 3: format_simulation_context_brief works
    total_tests += 1
    try:
        ctx = SimulationContext(
            synth_id="abc123",
            analysis_id="ana_12345678",
            adopted_rate=0.50,
            not_adopted_rate=0.50,
            n_executions=100)
        brief = format_simulation_context_brief(ctx)
        if "50%" not in brief:
            all_validation_failures.append("Brief format missing adopted rate")
        if "moderado" not in brief:
            all_validation_failures.append("Brief format missing performance label")
    except Exception as e:
        all_validation_failures.append(f"Brief format test failed: {e}")

    # Test 4: Contains instruction for behavior coherence
    total_tests += 1
    try:
        ctx = SimulationContext(
            synth_id="abc123",
            analysis_id="ana_12345678",
            adopted_rate=0.70,
            not_adopted_rate=0.30,
            n_executions=100)
        text = format_simulation_context(ctx)
        if "Baseie suas respostas" not in text:
            all_validation_failures.append("Behavior instruction not found")
        if "CONTEXTO DA SIMULAÇÃO" not in text:
            all_validation_failures.append("Section header not found")
    except Exception as e:
        all_validation_failures.append(f"Instruction test failed: {e}")

    # Test 5: Moderate adopted rate narrative
    total_tests += 1
    try:
        ctx = SimulationContext(
            synth_id="abc123",
            analysis_id="ana_12345678",
            adopted_rate=0.45,
            not_adopted_rate=0.55,
            n_executions=100)
        text = format_simulation_context(ctx)
        if "moderado" not in text:
            all_validation_failures.append("'moderado' not found for moderate adopted rate")
    except Exception as e:
        all_validation_failures.append(f"Moderate adoption test failed: {e}")

    # Test 6: create_simulation_context_from_outcome
    total_tests += 1
    try:
        from synth_lab.domain.entities.simulation_attributes import (
            SimulationAttributes,
            SimulationLatentTraits,
            SimulationObservables)

        sample_attrs = SimulationAttributes(
            observables=SimulationObservables(
                digital_literacy=0.35,
                similar_tool_experience=0.42,
                motor_ability=0.85,
                time_availability=0.28,
                domain_expertise=0.55),
            latent_traits=SimulationLatentTraits(
                capability_mean=0.42,
                trust_mean=0.39,
                friction_tolerance_mean=0.35,
                exploration_prob=0.38))
        outcome = SynthOutcome(
            analysis_id="ana_12345678",
            synth_id="test123",
            adopted_rate=0.60,
            not_adopted_rate=0.40,
            synth_attributes=sample_attrs)
        ctx = create_simulation_context_from_outcome(outcome)
        if ctx.synth_id != "test123":
            all_validation_failures.append(f"synth_id mismatch: {ctx.synth_id}")
        if ctx.analysis_id != "ana_12345678":
            all_validation_failures.append(f"analysis_id mismatch: {ctx.analysis_id}")
        if abs(ctx.adopted_rate - 0.60) > 0.001:
            all_validation_failures.append(f"adopted_rate should be 0.60, got {ctx.adopted_rate}")
        if abs(ctx.not_adopted_rate - 0.40) > 0.001:
            all_validation_failures.append(f"not_adopted_rate should be 0.40, got {ctx.not_adopted_rate}")
    except Exception as e:
        all_validation_failures.append(f"create_simulation_context_from_outcome test failed: {e}")

    # Final validation result
    if all_validation_failures:
        failed = len(all_validation_failures)
        print(f"VALIDATION FAILED - {failed} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Context formatter ready for use")
        sys.exit(0)
