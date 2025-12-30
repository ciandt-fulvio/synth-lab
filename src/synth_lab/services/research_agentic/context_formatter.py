"""
Context formatter for simulation results in interviews.

Formats SimulationContext into text for interviewee prompts,
ensuring interview responses are coherent with prior simulation results.

References:
    - Spec: specs/022-observable-latent-traits/spec.md (FR-016, FR-017, US2)
    - Data model: specs/022-observable-latent-traits/data-model.md
"""

from synth_lab.domain.entities.simulation_context import SimulationContext
from synth_lab.domain.entities.synth_outcome import SynthOutcome


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
        ...     did_not_try_rate=0.20,
        ...     failed_rate=0.20,
        ...     success_rate=0.60,
        ...     synth_attributes=...,
        ... )
        >>> ctx = create_simulation_context_from_outcome(outcome)
        >>> ctx.attempt_rate
        0.8
    """
    # attempt_rate = 1 - did_not_try_rate
    attempt_rate = 1.0 - outcome.did_not_try_rate

    return SimulationContext(
        synth_id=outcome.synth_id,
        analysis_id=outcome.analysis_id,
        attempt_rate=attempt_rate,
        success_rate=outcome.success_rate,
        failure_rate=outcome.failed_rate,
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
        ...     attempt_rate=0.80,
        ...     success_rate=0.60,
        ...     failure_rate=0.20,
        ...     n_executions=100,
        ... )
        >>> text = format_simulation_context(ctx)
        >>> "80%" in text  # attempt rate mentioned
        True
        >>> "60%" in text  # success rate mentioned
        True
    """
    # Calculate percentages for readability
    attempt_pct = int(context.attempt_rate * 100)
    success_pct = int(context.success_rate * 100)
    failure_pct = int(context.failure_rate * 100)
    no_attempt_pct = int(context.no_attempt_rate * 100)

    # Get performance label
    perf_label = context.performance_label

    # Build narrative based on attempt behavior
    if context.attempt_rate < 0.3:
        attempt_narrative = (
            f"Você raramente tentou usar esta funcionalidade ({attempt_pct}% das vezes). "
            f"Na maioria das situações ({no_attempt_pct}%), você preferiu não tentar."
        )
    elif context.attempt_rate < 0.6:
        attempt_narrative = (
            f"Você tentou usar esta funcionalidade em cerca de metade das situações "
            f"({attempt_pct}% das vezes). "
            f"Em {no_attempt_pct}% das vezes, você optou por não tentar."
        )
    elif context.attempt_rate < 0.8:
        attempt_narrative = (
            f"Você geralmente tentou usar esta funcionalidade ({attempt_pct}% das vezes). "
            f"Apenas {no_attempt_pct}% das vezes você decidiu não tentar."
        )
    else:
        attempt_narrative = (
            f"Você quase sempre tentou usar esta funcionalidade ({attempt_pct}% das vezes). "
            f"Raramente ({no_attempt_pct}%) você deixou de tentar."
        )

    # Build narrative based on success/failure
    if context.success_rate >= 0.8:
        outcome_narrative = (
            f"Quando você tentou, teve sucesso em {success_pct}% das vezes. "
            f"Seu desempenho foi {perf_label}."
        )
    elif context.success_rate >= 0.6:
        outcome_narrative = (
            f"Quando tentou, teve sucesso em {success_pct}% das vezes e falhou em {failure_pct}%. "
            f"Seu desempenho geral foi {perf_label}."
        )
    elif context.success_rate >= 0.4:
        outcome_narrative = (
            f"Quando tentou, conseguiu em {success_pct}% das vezes, mas falhou em {failure_pct}%. "
            f"Seu desempenho foi {perf_label}."
        )
    elif context.success_rate >= 0.2:
        outcome_narrative = (
            f"Você teve dificuldades: apenas {success_pct}% de sucesso quando tentou, "
            f"com {failure_pct}% de falhas. Seu desempenho foi {perf_label}."
        )
    else:
        outcome_narrative = (
            f"Você encontrou muita dificuldade: apenas {success_pct}% de sucesso, "
            f"com {failure_pct}% de falhas quando tentou. Desempenho {perf_label}."
        )

    # Combine narratives
    return f"""[CONTEXTO DA SIMULAÇÃO]
{attempt_narrative}

{outcome_narrative}

Baseie suas respostas nesta experiência prévia. Se você teve sucesso frequente,
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
        f"Tentativa: {context.attempt_rate:.0%}, "
        f"Sucesso: {context.success_rate:.0%}, "
        f"Falha: {context.failure_rate:.0%} "
        f"({context.performance_label})"
    )


if __name__ == "__main__":
    import sys

    all_validation_failures: list[str] = []
    total_tests = 0

    # Test 1: High success rate formatting
    total_tests += 1
    try:
        ctx = SimulationContext(
            synth_id="abc123",
            analysis_id="ana_12345678",
            attempt_rate=0.90,
            success_rate=0.85,
            failure_rate=0.05,
            n_executions=100,
        )
        text = format_simulation_context(ctx)
        if "90%" not in text:
            all_validation_failures.append("High attempt rate not mentioned")
        if "85%" not in text:
            all_validation_failures.append("High success rate not mentioned")
        if "excelente" not in text:
            all_validation_failures.append("'excelente' label not found for high success")
    except Exception as e:
        all_validation_failures.append(f"High success test failed: {e}")

    # Test 2: Low success rate formatting
    total_tests += 1
    try:
        ctx = SimulationContext(
            synth_id="abc123",
            analysis_id="ana_12345678",
            attempt_rate=0.50,
            success_rate=0.15,
            failure_rate=0.35,
            n_executions=100,
        )
        text = format_simulation_context(ctx)
        if "50%" not in text:
            all_validation_failures.append("Medium attempt rate not mentioned")
        if "15%" not in text:
            all_validation_failures.append("Low success rate not mentioned")
        if "muito baixo" not in text:
            all_validation_failures.append("'muito baixo' label not found for low success")
    except Exception as e:
        all_validation_failures.append(f"Low success test failed: {e}")

    # Test 3: Low attempt rate formatting
    total_tests += 1
    try:
        ctx = SimulationContext(
            synth_id="abc123",
            analysis_id="ana_12345678",
            attempt_rate=0.20,
            success_rate=0.60,
            failure_rate=0.20,
            n_executions=100,
        )
        text = format_simulation_context(ctx)
        if "raramente" not in text.lower():
            all_validation_failures.append("'raramente' not found for low attempt rate")
        if "80%" not in text:  # no_attempt_rate
            all_validation_failures.append("High no-attempt rate (80%) not mentioned")
    except Exception as e:
        all_validation_failures.append(f"Low attempt test failed: {e}")

    # Test 4: format_simulation_context_brief works
    total_tests += 1
    try:
        ctx = SimulationContext(
            synth_id="abc123",
            analysis_id="ana_12345678",
            attempt_rate=0.75,
            success_rate=0.50,
            failure_rate=0.25,
            n_executions=100,
        )
        brief = format_simulation_context_brief(ctx)
        if "75%" not in brief:
            all_validation_failures.append("Brief format missing attempt rate")
        if "50%" not in brief:
            all_validation_failures.append("Brief format missing success rate")
        if "moderado" not in brief:
            all_validation_failures.append("Brief format missing performance label")
    except Exception as e:
        all_validation_failures.append(f"Brief format test failed: {e}")

    # Test 5: Contains instruction for behavior coherence
    total_tests += 1
    try:
        ctx = SimulationContext(
            synth_id="abc123",
            analysis_id="ana_12345678",
            attempt_rate=0.80,
            success_rate=0.70,
            failure_rate=0.10,
            n_executions=100,
        )
        text = format_simulation_context(ctx)
        if "Baseie suas respostas" not in text:
            all_validation_failures.append("Behavior instruction not found")
        if "CONTEXTO DA SIMULAÇÃO" not in text:
            all_validation_failures.append("Section header not found")
    except Exception as e:
        all_validation_failures.append(f"Instruction test failed: {e}")

    # Test 6: Medium attempt rate narrative
    total_tests += 1
    try:
        ctx = SimulationContext(
            synth_id="abc123",
            analysis_id="ana_12345678",
            attempt_rate=0.55,
            success_rate=0.40,
            failure_rate=0.15,
            n_executions=100,
        )
        text = format_simulation_context(ctx)
        if "metade" not in text.lower():
            all_validation_failures.append("'metade' not found for medium attempt rate")
    except Exception as e:
        all_validation_failures.append(f"Medium attempt test failed: {e}")

    # Test 7: High attempt but moderate success
    total_tests += 1
    try:
        ctx = SimulationContext(
            synth_id="abc123",
            analysis_id="ana_12345678",
            attempt_rate=0.85,
            success_rate=0.45,
            failure_rate=0.40,
            n_executions=100,
        )
        text = format_simulation_context(ctx)
        if "quase sempre" not in text.lower():
            all_validation_failures.append("'quase sempre' not found for high attempt")
        if "moderado" not in text:
            all_validation_failures.append("'moderado' label not found")
    except Exception as e:
        all_validation_failures.append(f"High attempt moderate success test failed: {e}")

    # Test 8: create_simulation_context_from_outcome
    total_tests += 1
    try:
        from synth_lab.domain.entities.simulation_attributes import (
            SimulationAttributes,
            SimulationLatentTraits,
            SimulationObservables,
        )

        sample_attrs = SimulationAttributes(
            observables=SimulationObservables(
                digital_literacy=0.35,
                similar_tool_experience=0.42,
                motor_ability=0.85,
                time_availability=0.28,
                domain_expertise=0.55,
            ),
            latent_traits=SimulationLatentTraits(
                capability_mean=0.42,
                trust_mean=0.39,
                friction_tolerance_mean=0.35,
                exploration_prob=0.38,
            ),
        )
        outcome = SynthOutcome(
            analysis_id="ana_12345678",
            synth_id="test123",
            did_not_try_rate=0.20,
            failed_rate=0.20,
            success_rate=0.60,
            synth_attributes=sample_attrs,
        )
        ctx = create_simulation_context_from_outcome(outcome)
        if ctx.synth_id != "test123":
            all_validation_failures.append(f"synth_id mismatch: {ctx.synth_id}")
        if ctx.analysis_id != "ana_12345678":
            all_validation_failures.append(f"analysis_id mismatch: {ctx.analysis_id}")
        if abs(ctx.attempt_rate - 0.80) > 0.001:
            all_validation_failures.append(f"attempt_rate should be 0.80, got {ctx.attempt_rate}")
        if abs(ctx.success_rate - 0.60) > 0.001:
            all_validation_failures.append(f"success_rate should be 0.60, got {ctx.success_rate}")
        if abs(ctx.failure_rate - 0.20) > 0.001:
            all_validation_failures.append(f"failure_rate should be 0.20, got {ctx.failure_rate}")
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
