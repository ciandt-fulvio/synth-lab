"""
Summarizer agent for batch interview analysis.

This module provides the summarization agent that analyzes multiple interviews
to identify patterns, divergences, tensions, and insights across personas.

References:
- OpenAI Agents SDK: https://openai.github.io/openai-agents-python/agents/
- UX Research Synthesis Best Practices

Sample usage:
```python
from .summarizer import summarize_interviews

summary = await summarize_interviews(
    interview_results=results,
    topic_guide_name="compra-amazon",
    model="gpt-xxxx"
)
print(summary)
```
"""

from typing import Any

from agents import Agent, ModelSettings, Runner
from loguru import logger
from openai.types.shared import Reasoning
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes

from synth_lab.infrastructure.llm_client import supports_reasoning_effort
from synth_lab.infrastructure.phoenix_tracing import get_tracer

from .runner import InterviewResult

# Phoenix/OpenTelemetry tracer for observability
_tracer = get_tracer("summarizer")

# Summarizer system prompt based on user requirements
SUMMARIZER_INSTRUCTIONS = """
Você é um especialista em síntese de pesquisa UX qualitativa. Sua tarefa é analisar múltiplas entrevistas e gerar um relatório de síntese focado em insights acionáveis.

## Diretrizes de Análise

### 1) Padrões Recorrentes (O Núcleo)
- Identifique o que apareceu em múltiplas entrevistas
- Especialmente quando aparece em personas e contratos cognitivos diferentes
- Isso indica fricção estrutural, não individual

### 2) Divergências Relevantes (O Ouro)
- Destaque opiniões raras, mas fortes
- Especialmente quando:
  - vêm com emoção
  - vêm com narrativa concreta
  - contradizem o padrão geral
- Quanto mais diferente, mais precisa ser registrada, com contexto

### 3) Situações, Não Julgamentos
- Foque em "Em que situações isso acontece?"
- Evite "O que os usuários acham?"
- Isso evita resumo genérico

### 4) Citações Ancoradas
- Não "frases bonitas", mas citações curtas ligadas a:
  - tipo de persona
  - contrato cognitivo
  - situação específica
- Ex: "João citou que …"

### 5) Tensões, Não Médias
- Identifique onde os usuários discordam
- Onde um ganho causa perda em outro perfil
- Isso é muito mais útil que "pontos positivos vs negativos"

### 6) Ausências Importantes
- O que quase ninguém mencionou, mas seria esperado mencionar?

## Formato de Saída

Estruture seu relatório nas seguintes seções:

# Síntese de Pesquisa: {topic_guide}

## Resumo Executivo
(3-5 frases com os principais achados)

## Padrões Recorrentes
(Lista com contexto de padrões identificados)

## Divergências Relevantes
(Opiniões únicas com citações ancoradas)

## Tensões Identificadas
(Onde diferentes pessoas têm necessidades conflitantes)

## Ausências Notáveis
(O que não foi mencionado mas deveria ter sido)

## Citações-Chave
(Citações organizadas por tema, com contexto de persona)

## Recomendações
(Baseadas nas evidências encontradas)

---

## Entrevistas para Análise

{interviews_content}
"""


def _get_model_settings(model: str, reasoning_effort: str = "medium") -> ModelSettings | None:
    """
    Get model settings with reasoning effort configured.

    Args:
        model: Model name to check for reasoning_effort support.
        reasoning_effort: Reasoning effort level ("low", "medium", "high").

    Returns:
        ModelSettings with reasoning configured if supported, None otherwise.
    """
    if supports_reasoning_effort(model):
        return ModelSettings(reasoning=Reasoning(effort=reasoning_effort))  # type: ignore
    # Model doesn't support reasoning_effort, return None (no special settings)
    return None


def format_interview_for_summary(
    result: InterviewResult,
    synth_data: dict[str, Any],
) -> str:
    """
    Format a single interview result for the summarizer.

    Args:
        result: Interview result with messages
        synth_data: Full synth data including demographics and psychographics

    Returns:
        Formatted string representation of the interview
    """
    lines = []

    # Header with synth info
    lines.append(f"### Entrevista: {result.synth_name} (ID: {result.synth_id})")
    lines.append("")

    # Demographics
    demo = synth_data.get("demografia", {})
    lines.append("**Perfil Demográfico:**")
    lines.append(f"- Idade: {demo.get('idade', 'N/A')} anos")
    lines.append(f"- Gênero: {demo.get('identidade_genero', 'N/A')}")
    lines.append(f"- Escolaridade: {demo.get('escolaridade', 'N/A')}")
    lines.append(f"- Ocupação: {demo.get('ocupacao', 'N/A')}")
    loc = demo.get("localizacao", {})
    lines.append(f"- Localização: {loc.get('cidade', 'N/A')}, {loc.get('estado', 'N/A')}")
    lines.append("")

    # Conversation
    lines.append("**Transcrição:**")
    lines.append("")
    for msg in result.messages:
        speaker_label = "Entrevistador" if msg.speaker == "Interviewer" else result.synth_name
        lines.append(f"**{speaker_label}:** {msg.text}")
        lines.append("")

    lines.append("---")
    lines.append("")

    return "\n".join(lines)


def create_summarizer_agent(
    topic_guide_name: str,
    interviews_content: str,
    model: str = "gpt-4o-mini",
    reasoning_effort: str = "medium",
) -> Agent:
    """
    Create a summarizer agent for analyzing multiple interviews.

    Args:
        topic_guide_name: Name of the topic guide used
        interviews_content: Formatted content of all interviews
        model: LLM model to use
        reasoning_effort: Reasoning effort level

    Returns:
        Configured Agent instance
    """
    instructions = SUMMARIZER_INSTRUCTIONS.format(
        topic_guide=topic_guide_name,
        interviews_content=interviews_content,
    )

    # Build agent kwargs - only include model_settings if model supports it
    agent_kwargs = {
        "name": "Research Summarizer",
        "instructions": instructions,
        "model": model,
    }
    model_settings = _get_model_settings(model, reasoning_effort)
    if model_settings is not None:
        agent_kwargs["model_settings"] = model_settings

    return Agent(**agent_kwargs)


async def summarize_interviews(
    interview_results: list[tuple[InterviewResult, dict[str, Any]]],
    topic_guide_name: str,
    model: str = "gpt-4o-mini",
) -> str:
    """
    Summarize multiple interview results into a synthesis report.

    Args:
        interview_results: List of tuples (InterviewResult, synth_data)
        topic_guide_name: Name of the topic guide used
        model: LLM model to use for summarization

    Returns:
        Synthesis report as markdown string

    Sample usage:
    ```python
    results = [(result1, synth1), (result2, synth2), ...]
    summary = await summarize_interviews(results, "compra-amazon")
    print(summary)
    ```
    """
    logger.info(f"Summarizing {len(interview_results)} interviews with model={model}")

    with _tracer.start_as_current_span(
        f"Summarize {len(interview_results)} interviews: {topic_guide_name}",
        attributes={
            SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.AGENT.value,
            "topic_guide": topic_guide_name,
            "interview_count": len(interview_results),
            "model": model,
        },
    ) as span:
        # Format all interviews
        interviews_content_parts = []
        for i, (result, synth_data) in enumerate(interview_results):
            logger.debug(f"Formatting interview {i + 1}/{len(interview_results)}")
            formatted = format_interview_for_summary(result, synth_data)
            interviews_content_parts.append(formatted)

        interviews_content = "\n".join(interviews_content_parts)
        logger.info(f"Formatted interviews content length: {len(interviews_content)} chars")

        if span:
            span.set_attribute("content_length", len(interviews_content))

        # Create summarizer agent
        logger.info("Creating summarizer agent...")
        summarizer = create_summarizer_agent(
            topic_guide_name=topic_guide_name,
            interviews_content=interviews_content,
            model=model,
            reasoning_effort="medium",
        )

        # Run summarization
        logger.info("Running summarizer agent...")
        result = await Runner.run(
            summarizer,
            input="Analise as entrevistas fornecidas e gere o relatório de síntese conforme as diretrizes.",
        )

        summary = result.final_output
        logger.info(f"Summary generated: {len(summary)} characters")

        if span:
            span.set_attribute("summary_length", len(summary))

        return summary


if __name__ == "__main__":
    """Validation of summarizer module."""
    import sys

    print("=== Summarizer Module Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Test 1: Import works
    total_tests += 1
    try:
        from .summarizer import (
            create_summarizer_agent,
            format_interview_for_summary,
        )

        print("✓ All imports successful")
    except Exception as e:
        all_validation_failures.append(f"Import: {e}")

    # Test 2: format_interview_for_summary works
    total_tests += 1
    try:
        from .runner import ConversationMessage, InterviewResult

        mock_result = InterviewResult(
            messages=[
                ConversationMessage(speaker="Interviewer", text="Como você faz compras?"),
                ConversationMessage(speaker="Interviewee", text="Eu uso o celular."),
            ],
            synth_id="abc123",
            synth_name="Maria",
            topic_guide_name="compra-amazon",
            trace_path=None,
            total_turns=1,
        )
        mock_synth = {
            "nome": "Maria",
            "demografia": {
                "idade": 30,
                "identidade_genero": "feminino",
                "escolaridade": "Superior completo",
                "ocupacao": "Analista",
                "localizacao": {"cidade": "São Paulo", "estado": "SP"},
            },
            "psicografia": {
                "interesses": ["tecnologia", "compras"],
                "contratos_cognitivos": {
                    "nome": "Explorador Cauteloso",
                    "descricao": "Gosta de novidades mas com cuidado",
                },
            },
        }

        formatted = format_interview_for_summary(mock_result, mock_synth)
        assert "Maria" in formatted
        assert "Explorador Cauteloso" in formatted
        assert "Como você faz compras?" in formatted
        print("✓ format_interview_for_summary works correctly")
    except Exception as e:
        all_validation_failures.append(f"format_interview_for_summary: {e}")

    # Test 3: create_summarizer_agent works
    total_tests += 1
    try:
        agent = create_summarizer_agent(
            topic_guide_name="test-guide",
            interviews_content="Test content",
            model="gpt-4o-mini",
        )
        assert agent.name == "Research Summarizer"
        assert "test-guide" in agent.instructions  # type: ignore
        print("✓ create_summarizer_agent works correctly")
    except Exception as e:
        all_validation_failures.append(f"create_summarizer_agent: {e}")

    # Final validation result
    print()
    if all_validation_failures:
        print(
            f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:"
        )
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Summarizer module is validated and ready for use")
        sys.exit(0)
