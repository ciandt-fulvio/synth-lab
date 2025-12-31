"""
LLM-powered insights for feature scorecards..

Generates justifications, impact hypotheses, and adjustment suggestions
using LLM calls with Phoenix tracing.

Functions:
- generate_justification(): Generate justification for scorecard scores
- generate_impact_hypotheses(): Generate hypotheses about impact on synth groups
- generate_suggested_adjustments(): Generate suggestions to improve scores

References:
    - Spec: specs/016-feature-impact-simulation/spec.md (FR-012, FR-013)
    - LLM Client: src/synth_lab/infrastructure/llm_client.py

Sample usage:
    from synth_lab.services.simulation.scorecard_llm import ScorecardLLM

    llm = ScorecardLLM()
    justification = llm.generate_justification(scorecard)

Expected output:
    str: LLM-generated text justifying the scorecard scores
"""

import json

from loguru import logger
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes

from synth_lab.domain.entities import FeatureScorecard
from synth_lab.infrastructure.llm_client import LLMClient, get_llm_client
from synth_lab.infrastructure.phoenix_tracing import get_tracer

# Phoenix/OpenTelemetry tracer for observability
_tracer = get_tracer("scorecard-llm")


class ScorecardLLM:
    """LLM-powered scorecard insights generator."""

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        """
        Initialize with optional LLM client.

        Args:
            llm_client: LLM client instance. If None, uses global client.
        """
        self.llm = llm_client or get_llm_client()
        self.logger = logger.bind(component="scorecard_llm")

    def generate_justification(self, scorecard: FeatureScorecard) -> str:
        """
        Generate a justification for the scorecard scores.

        Args:
            scorecard: Feature scorecard to analyze

        Returns:
            str: LLM-generated justification text
        """
        feature_name = scorecard.identification.feature_name
        span_name = f"ScorecardJustify | {feature_name[:30]}"
        with _tracer.start_as_current_span(
            span_name,
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
                "scorecard.id": scorecard.id,
                "feature.name": feature_name,
                "operation.type": "scorecard_justification",
            },
        ):
            prompt = self._build_justification_prompt(scorecard)

            messages = [
                {
                    "role": "system",
                    "content": (
                        "Voce e um especialista em UX e design de produto. "
                        "Analise o scorecard da feature e justifique os scores atribuidos "
                        "de forma objetiva e tecnica. Escreva em portugues brasileiro."
                    ),
                },
                {"role": "user", "content": prompt},
            ]

            response = self.llm.complete(
                messages=messages,
                temperature=0.7,
                operation_name="generate_justification",
            )

            self.logger.info(f"Generated justification for scorecard {scorecard.id}")
            return response

    def generate_impact_hypotheses(
        self,
        scorecard: FeatureScorecard,
        num_hypotheses: int = 3,
    ) -> list[str]:
        """
        Generate hypotheses about impact on different synth groups.

        Args:
            scorecard: Feature scorecard to analyze
            num_hypotheses: Number of hypotheses to generate

        Returns:
            list[str]: List of impact hypotheses
        """
        feature_name = scorecard.identification.feature_name
        span_name = f"ScorecardHypotheses | {feature_name[:30]} | n={num_hypotheses}"
        with _tracer.start_as_current_span(
            span_name,
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
                "scorecard.id": scorecard.id,
                "feature.name": feature_name,
                "operation.type": "scorecard_hypotheses",
                "hypotheses.count": num_hypotheses,
            },
        ):
            prompt = self._build_hypotheses_prompt(scorecard, num_hypotheses)

            messages = [
                {
                    "role": "system",
                    "content": (
                        "Voce e um especialista em comportamento de usuarios e simulacao. "
                        "Gere hipoteses sobre como diferentes perfis de usuarios serao impactados "
                        "pela feature. Considere usuarios com diferentes niveis de letramento digital, "
                        "disponibilidade de tempo, e experiencia previa. Retorne um JSON array com as hipoteses. "
                        "Escreva em portugues brasileiro."
                    ),
                },
                {"role": "user", "content": prompt},
            ]

            response = self.llm.complete_json(
                messages=messages,
                temperature=0.8,
                operation_name="generate_impact_hypotheses",
            )

            try:
                data = json.loads(response)
                if isinstance(data, dict) and "hypotheses" in data:
                    hypotheses = data["hypotheses"]
                elif isinstance(data, list):
                    hypotheses = data
                else:
                    hypotheses = [response]
            except json.JSONDecodeError:
                hypotheses = [response]

            self.logger.info(f"Generated {len(hypotheses)} hypotheses for scorecard {scorecard.id}")
            return hypotheses[:num_hypotheses]

    def generate_suggested_adjustments(
        self,
        scorecard: FeatureScorecard,
    ) -> list[str]:
        """
        Generate suggestions to improve scorecard dimensions.

        Args:
            scorecard: Feature scorecard to analyze

        Returns:
            list[str]: List of suggested adjustments
        """
        feature_name = scorecard.identification.feature_name
        span_name = f"ScorecardAdjustments | {feature_name[:30]}"
        with _tracer.start_as_current_span(
            span_name,
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
                "scorecard.id": scorecard.id,
                "feature.name": feature_name,
                "operation.type": "scorecard_adjustments",
            },
        ):
            prompt = self._build_adjustments_prompt(scorecard)

            messages = [
                {
                    "role": "system",
                    "content": (
                        "Voce e um especialista em UX e design de produto. "
                        "Sugira ajustes concretos para melhorar os scores do scorecard. "
                        "Foque em reducir complexidade, esforco inicial, risco percebido "
                        "e tempo para valor. Retorne um JSON array com as sugestoes. "
                        "Escreva em portugues brasileiro."
                    ),
                },
                {"role": "user", "content": prompt},
            ]

            response = self.llm.complete_json(
                messages=messages,
                temperature=0.7,
                operation_name="generate_suggested_adjustments",
            )

            try:
                data = json.loads(response)
                if isinstance(data, dict) and "suggestions" in data:
                    suggestions = data["suggestions"]
                elif isinstance(data, list):
                    suggestions = data
                else:
                    suggestions = [response]
            except json.JSONDecodeError:
                suggestions = [response]

            self.logger.info(
                f"Generated {len(suggestions)} suggestions for scorecard {scorecard.id}"
            )
            return suggestions

    def _build_justification_prompt(self, scorecard: FeatureScorecard) -> str:
        """Build prompt for justification generation."""
        return f"""
Analise o seguinte scorecard de feature e justifique os scores atribuidos:

## Feature
- Nome: {scorecard.identification.feature_name}
- Cenario de uso: {scorecard.identification.use_scenario}
- Descricao: {scorecard.description_text}

## Scores (escala 0-1, onde 0 e o melhor e 1 e o pior)

### Complexidade: {scorecard.complexity.score:.2f}
- Regras aplicadas: {", ".join(scorecard.complexity.rules_applied) or "Nenhuma"}
- Incerteza: [{scorecard.complexity.min_uncertainty:.2f} - {scorecard.complexity.max_uncertainty:.2f}]

### Esforco Inicial: {scorecard.initial_effort.score:.2f}
- Regras aplicadas: {", ".join(scorecard.initial_effort.rules_applied) or "Nenhuma"}
- Incerteza: [{scorecard.initial_effort.min_uncertainty:.2f} - {scorecard.initial_effort.max_uncertainty:.2f}]

### Risco Percebido: {scorecard.perceived_risk.score:.2f}
- Regras aplicadas: {", ".join(scorecard.perceived_risk.rules_applied) or "Nenhuma"}
- Incerteza: [{scorecard.perceived_risk.min_uncertainty:.2f} - {scorecard.perceived_risk.max_uncertainty:.2f}]

### Tempo para Valor: {scorecard.time_to_value.score:.2f}
- Regras aplicadas: {", ".join(scorecard.time_to_value.rules_applied) or "Nenhuma"}
- Incerteza: [{scorecard.time_to_value.min_uncertainty:.2f} - {scorecard.time_to_value.max_uncertainty:.2f}]

Por favor, justifique cada score considerando as regras aplicadas e o cenario de uso. Máximo de 20 tokens por score.
"""

    def _build_hypotheses_prompt(
        self,
        scorecard: FeatureScorecard,
        num_hypotheses: int,
    ) -> str:
        """Build prompt for impact hypotheses generation."""
        return f"""
Com base no scorecard abaixo, gere {num_hypotheses} hipoteses sobre como diferentes grupos de usuarios serao impactados:

## Feature
- Nome: {scorecard.identification.feature_name}
- Cenario de uso: {scorecard.identification.use_scenario}
- Descricao: {scorecard.description_text}

## Scores
- Complexidade: {scorecard.complexity.score:.2f}
- Esforco Inicial: {scorecard.initial_effort.score:.2f}
- Risco Percebido: {scorecard.perceived_risk.score:.2f}
- Tempo para Valor: {scorecard.time_to_value.score:.2f}

## Perfis de usuarios a considerar
- Usuarios com baixo letramento digital (digital_literacy < 0.3)
- Usuarios com pouco tempo disponivel (time_availability < 0.3)
- Usuarios sem experiencia com ferramentas similares (similar_tool_experience < 0.3)
- Usuarios experientes (todos os atributos > 0.7)

Retorne um JSON no formato:
{{"hypotheses": ["hipotese 1", "hipotese 2", ...]}}
"""

    def _build_adjustments_prompt(self, scorecard: FeatureScorecard) -> str:
        """Build prompt for adjustment suggestions."""
        # Identify dimensions with high scores (bad)
        dimensions = [
            ("Complexidade", scorecard.complexity.score),
            ("Esforco Inicial", scorecard.initial_effort.score),
            ("Risco Percebido", scorecard.perceived_risk.score),
            ("Tempo para Valor", scorecard.time_to_value.score),
        ]
        worst_dimensions = sorted(dimensions, key=lambda x: x[1], reverse=True)[:2]
        worst_names = [d[0] for d in worst_dimensions]

        return f"""
Sugira 10 ajustes concretos para melhorar o scorecard da feature abaixo:

## Feature
- Nome: {scorecard.identification.feature_name}
- Cenario de uso: {scorecard.identification.use_scenario}
- Descricao: {scorecard.description_text}

## Scores atuais (0=melhor, 1=pior)
- Complexidade: {scorecard.complexity.score:.2f}
- Esforco Inicial: {scorecard.initial_effort.score:.2f}
- Risco Percebido: {scorecard.perceived_risk.score:.2f}
- Tempo para Valor: {scorecard.time_to_value.score:.2f}

Por favor, justifique cada score considerando as regras aplicadas e o cenario de uso. Máximo de 20 tokens por score.


## Areas que mais precisam de melhoria
{", ".join(worst_names)}

Foque em sugestoes praticas e acionaveis que a equipe de produto pode implementar.

Retorne um JSON no formato:
{{"suggestions": ["sugestao 1", "sugestao 2", ...]}}
"""


if __name__ == "__main__":
    import sys

    from synth_lab.domain.entities import ScorecardDimension, ScorecardIdentification

    print("=== Scorecard LLM Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Create test scorecard
    test_scorecard = FeatureScorecard(
        identification=ScorecardIdentification(
            feature_name="Novo Fluxo de Onboarding",
            use_scenario="Primeiro acesso ao produto",
        ),
        description_text="Fluxo de onboarding simplificado com 3 passos e wizard interativo",
        complexity=ScorecardDimension(
            score=0.4,
            rules_applied=["2 conceitos novos", "wizard interativo"],
        ),
        initial_effort=ScorecardDimension(score=0.3),
        perceived_risk=ScorecardDimension(
            score=0.2,
            min_uncertainty=0.1,
            max_uncertainty=0.3,
        ),
        time_to_value=ScorecardDimension(score=0.5),
    )

    # Test 1: Prompt building for justification
    total_tests += 1
    try:
        llm = ScorecardLLM()
        prompt = llm._build_justification_prompt(test_scorecard)
        if "Novo Fluxo de Onboarding" not in prompt:
            all_validation_failures.append("Justification prompt missing feature name")
        elif "Complexidade: 0.40" not in prompt:
            all_validation_failures.append("Justification prompt missing complexity score")
        else:
            print("Test 1 PASSED: Justification prompt built correctly")
    except Exception as e:
        all_validation_failures.append(f"Justification prompt build failed: {e}")

    # Test 2: Prompt building for hypotheses
    total_tests += 1
    try:
        prompt = llm._build_hypotheses_prompt(test_scorecard, 3)
        if "digital_literacy" not in prompt:
            all_validation_failures.append("Hypotheses prompt missing digital_literacy")
        elif '{"hypotheses"' not in prompt:
            all_validation_failures.append("Hypotheses prompt missing JSON format instruction")
        else:
            print("Test 2 PASSED: Hypotheses prompt built correctly")
    except Exception as e:
        all_validation_failures.append(f"Hypotheses prompt build failed: {e}")

    # Test 3: Prompt building for adjustments
    total_tests += 1
    try:
        prompt = llm._build_adjustments_prompt(test_scorecard)
        if "Areas que mais precisam de melhoria" not in prompt:
            all_validation_failures.append("Adjustments prompt missing improvement areas")
        elif '{"suggestions"' not in prompt:
            all_validation_failures.append("Adjustments prompt missing JSON format instruction")
        else:
            print("Test 3 PASSED: Adjustments prompt built correctly")
    except Exception as e:
        all_validation_failures.append(f"Adjustments prompt build failed: {e}")

    # Test 4: Worst dimensions identification
    total_tests += 1
    try:
        # Create scorecard with specific scores to test sorting
        test_scorecard2 = FeatureScorecard(
            identification=ScorecardIdentification(
                feature_name="Test",
                use_scenario="Test",
            ),
            description_text="Test",
            complexity=ScorecardDimension(score=0.9),  # Worst
            initial_effort=ScorecardDimension(score=0.2),
            perceived_risk=ScorecardDimension(score=0.8),  # Second worst
            time_to_value=ScorecardDimension(score=0.3),
        )
        prompt = llm._build_adjustments_prompt(test_scorecard2)
        if "Complexidade" not in prompt or "Risco Percebido" not in prompt:
            all_validation_failures.append(
                "Adjustments prompt should identify Complexidade and Risco Percebido as worst"
            )
        else:
            print("Test 4 PASSED: Worst dimensions correctly identified")
    except Exception as e:
        all_validation_failures.append(f"Worst dimensions test failed: {e}")

    # Test 5: ScorecardLLM instantiation
    total_tests += 1
    try:
        # Without explicit client, should use global
        llm1 = ScorecardLLM()
        if llm1.llm is None:
            all_validation_failures.append("ScorecardLLM should have llm client")

        # With explicit client
        from synth_lab.infrastructure.llm_client import LLMClient

        custom_client = LLMClient(api_key="test-key")
        llm2 = ScorecardLLM(llm_client=custom_client)
        if llm2.llm is not custom_client:
            all_validation_failures.append("ScorecardLLM should use provided client")
        else:
            print("Test 5 PASSED: ScorecardLLM instantiation works correctly")
    except Exception as e:
        all_validation_failures.append(f"ScorecardLLM instantiation failed: {e}")

    # Final result
    print()
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("\nNote: Actual LLM calls require OPENAI_API_KEY and are not tested in validation")
        sys.exit(0)
