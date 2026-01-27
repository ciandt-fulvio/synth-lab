"""
QuestionParserService for causal simulation system.

Parses natural language business questions into structured problem decompositions
using LLM with Phoenix tracing for observability.

References:
    - Spec: specs/035-causal-simulation/spec.md
    - Data model: specs/035-causal-simulation/data-model.md
    - Phoenix: https://docs.arize.com/phoenix
"""

import json
from typing import Any

from loguru import logger
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes

from synth_lab.domain.entities.simulation import ProblemDecomposition
from synth_lab.infrastructure.llm_client import LLMClient, get_llm_client
from synth_lab.infrastructure.phoenix_tracing import get_tracer

_tracer = get_tracer("question-parser-service")

# Model for question parsing (needs reasoning for complex questions)
PARSER_MODEL = "gpt-4o"


class QuestionParserService:
    """
    Service for parsing natural language questions into structured problems.

    Uses LLM to extract intervention, outcomes, time horizon, and decision type
    from business questions.
    """

    def __init__(self, llm_client: LLMClient | None = None):
        """
        Initialize QuestionParserService.

        Args:
            llm_client: LLM client for generation. Defaults to singleton.
        """
        self.llm = llm_client or get_llm_client()
        self.logger = logger.bind(component="question_parser_service")

    def parse(self, question_text: str) -> ProblemDecomposition:
        """
        Parse natural language question into structured problem decomposition.

        Args:
            question_text: Natural language business question

        Returns:
            ProblemDecomposition with extracted intervention, outcomes, etc.

        Raises:
            ValueError: If question cannot be parsed or is ambiguous

        Example:
            >>> parser = QuestionParserService()
            >>> problem = parser.parse(
            ...     "What will be the adoption rate for a weekly meal subscription?"
            ... )
            >>> print(problem.intervention)  # "Launch weekly meal subscription service"
            >>> print(problem.primary_outcome)  # "adoption_rate"
        """
        span_name = f"QuestionParser | {question_text[:50]}..."
        with _tracer.start_as_current_span(
            span_name,
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
                "operation.type": "question_parsing",
                "llm.model": PARSER_MODEL,
                "question.length": len(question_text),
            },
        ):
            try:
                # Build prompt for question parsing
                prompt = self._build_parsing_prompt(question_text)

                # Call LLM with gpt-4o (reasoning needed)
                self.logger.info(f"Parsing question: {question_text[:100]}")
                llm_response_str = self.llm.complete_json(
                    messages=[{"role": "user", "content": prompt}],
                    model=PARSER_MODEL,
                )

                # Parse LLM response
                llm_response = json.loads(llm_response_str)

                # Validate response structure
                self._validate_response(llm_response)

                # Convert to ProblemDecomposition entity
                problem = ProblemDecomposition(
                    intervention=llm_response["intervention"],
                    primary_outcome=llm_response["primary_outcome"],
                    secondary_outcomes=llm_response.get("secondary_outcomes", []),
                    unit_of_analysis=llm_response["unit_of_analysis"],
                    time_horizon=llm_response["time_horizon"],
                    decision_type=llm_response["decision_type"],
                )

                self.logger.info(
                    f"Successfully parsed question: intervention={problem.intervention}, "
                    f"outcome={problem.primary_outcome}"
                )

                return problem

            except json.JSONDecodeError as e:
                error_msg = f"Failed to parse LLM response as JSON: {e}"
                self.logger.error(error_msg)
                raise ValueError(error_msg) from e

            except Exception as e:
                error_msg = f"Question parsing failed: {e}"
                self.logger.error(error_msg)
                raise ValueError(error_msg) from e

    def _build_parsing_prompt(self, question_text: str) -> str:
        """
        Build prompt for question parsing.

        Args:
            question_text: Natural language question

        Returns:
            Formatted prompt string
        """
        return f"""Você é um analista de negócios que estrutura perguntas em linguagem natural em decomposições de problemas para simulação causal.

**Pergunta**: "{question_text}"

Extraia os seguintes componentes:

1. **intervention**: Qual ação ou mudança está sendo avaliada? (ex: "Lançar serviço de assinatura semanal de refeições")
2. **primary_outcome**: Métrica principal de interesse (ex: "taxa_de_adocao", "lifetime_value_cliente")
3. **secondary_outcomes**: Métricas adicionais para acompanhar (lista de strings, pode ser vazia)
4. **unit_of_analysis**: Nível de análise - um de: "user", "customer", "transaction", "account", "session", "cohort"
5. **time_horizon**: Horizonte de tempo para previsão (ex: "3 meses", "1 ano", "6 meses")
6. **decision_type**: Categoria de decisão - um de: "product_launch", "feature_rollout", "pricing_change", "process_improvement", "capacity_planning", "market_entry"

**Regras importantes**:
- `primary_outcome` deve ser um nome de variável em snake_case (ex: "taxa_churn", "taxa_conversao")
- `time_horizon` deve ser uma duração simples (ex: "6 meses", não "nos próximos 6 meses")
- Se a pergunta for ambígua ou faltar informação crítica, use seu melhor julgamento baseado no contexto
- Escolha o `decision_type` mais relevante da lista acima
- Responda em português brasileiro para os campos de texto (intervention, primary_outcome, secondary_outcomes)

**Formato de saída** (apenas JSON, sem markdown):
{{
  "intervention": "string",
  "primary_outcome": "string",
  "secondary_outcomes": ["string"],
  "unit_of_analysis": "string",
  "time_horizon": "string",
  "decision_type": "string"
}}

Retorne APENAS o objeto JSON, sem texto ou formatação adicional.
"""

    def _validate_response(self, response: dict[str, Any]) -> None:
        """
        Validate LLM response structure.

        Args:
            response: Parsed JSON response from LLM

        Raises:
            ValueError: If response is invalid
        """
        required_fields = [
            "intervention",
            "primary_outcome",
            "unit_of_analysis",
            "time_horizon",
            "decision_type",
        ]

        for field in required_fields:
            if field not in response or not response[field]:
                raise ValueError(f"Missing required field: {field}")

        # Validate unit_of_analysis
        valid_units = [
            "user",
            "customer",
            "transaction",
            "account",
            "session",
            "cohort",
        ]
        if response["unit_of_analysis"] not in valid_units:
            self.logger.warning(
                f"Invalid unit_of_analysis: {response['unit_of_analysis']}, "
                f"using 'user' as fallback"
            )
            response["unit_of_analysis"] = "user"

        # Validate decision_type
        valid_types = [
            "product_launch",
            "feature_rollout",
            "pricing_change",
            "process_improvement",
            "capacity_planning",
            "market_entry",
        ]
        if response["decision_type"] not in valid_types:
            self.logger.warning(
                f"Invalid decision_type: {response['decision_type']}, "
                f"using 'feature_rollout' as fallback"
            )
            response["decision_type"] = "feature_rollout"
