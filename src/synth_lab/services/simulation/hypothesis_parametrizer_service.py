"""
HypothesisParametrizerService for causal simulation system.

Quantifies variables with probability distributions, ranges, and correlations
using LLM to suggest reasonable parameters.

References:
    - Spec: specs/035-causal-simulation/spec.md
    - Data model: specs/035-causal-simulation/data-model.md
    - SciPy distributions: https://docs.scipy.org/doc/scipy/reference/stats.html
"""

import json
from typing import Any

from loguru import logger
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes

from synth_lab.domain.entities.causal_dag import CausalDAG
from synth_lab.domain.entities.hypothesis import (
    BernoulliParams,
    BetaParams,
    Correlation,
    DistributionType,
    Hypothesis,
    LogNormalParams,
    NormalParams,
    UniformParams,
)
from synth_lab.infrastructure.llm_client import LLMClient, get_llm_client
from synth_lab.infrastructure.phoenix_tracing import get_tracer

_tracer = get_tracer("hypothesis-parametrizer-service")

# Model for hypothesis parametrization (needs reasoning for reasonable ranges)
PARAMETRIZER_MODEL = "gpt-4o"


class HypothesisParametrizerService:
    """
    Service for quantifying variables with probability distributions.

    Uses LLM to suggest distribution types and parameters based on variable
    characteristics and domain knowledge.
    """

    def __init__(self, llm_client: LLMClient | None = None):
        """
        Initialize HypothesisParametrizerService.

        Args:
            llm_client: LLM client for generation. Defaults to singleton.
        """
        self.llm = llm_client or get_llm_client()
        self.logger = logger.bind(component="hypothesis_parametrizer_service")

    def quantify(self, simulation_id: str, dag: CausalDAG) -> list[Hypothesis]:
        """
        Quantify all variables in DAG with probability distributions.

        Args:
            simulation_id: Parent simulation ID
            dag: Validated causal DAG

        Returns:
            List of Hypothesis entities (one per variable)

        Raises:
            ValueError: If parametrization fails

        Example:
            >>> parametrizer = HypothesisParametrizerService()
            >>> hypotheses = parametrizer.quantify("sim_12345678", dag)
            >>> for hyp in hypotheses:
            ...     print(f"{hyp.variable_name}: {hyp.distribution_type}")
        """
        span_name = f"HypothesisParametrizer | {len(dag.nodes)} variables"
        with _tracer.start_as_current_span(
            span_name,
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
                "operation.type": "hypothesis_parametrization",
                "llm.model": PARAMETRIZER_MODEL,
                "simulation.id": simulation_id,
                "dag.num_variables": len(dag.nodes),
            },
        ):
            try:
                # Build prompt for hypothesis parametrization
                prompt = self._build_parametrization_prompt(dag)

                # Call LLM with gpt-4o (reasoning needed)
                self.logger.info(
                    f"Quantifying {len(dag.nodes)} variables for simulation {simulation_id}"
                )
                llm_response_str = self.llm.complete_json(
                    messages=[{"role": "user", "content": prompt}],
                    model=PARAMETRIZER_MODEL,
                )

                # Parse LLM response
                llm_response = json.loads(llm_response_str)

                # Convert to Hypothesis entities
                hypotheses = self._parse_hypotheses_response(
                    simulation_id, dag, llm_response
                )

                self.logger.info(
                    f"Successfully quantified {len(hypotheses)} hypotheses"
                )

                return hypotheses

            except json.JSONDecodeError as e:
                error_msg = f"Failed to parse LLM response as JSON: {e}"
                self.logger.error(error_msg)
                raise ValueError(error_msg) from e

            except Exception as e:
                error_msg = f"Hypothesis parametrization failed: {e}"
                self.logger.error(error_msg)
                raise ValueError(error_msg) from e

    def _build_parametrization_prompt(self, dag: CausalDAG) -> str:
        """
        Build prompt for hypothesis parametrization.

        Args:
            dag: Causal DAG with variables

        Returns:
            Formatted prompt string
        """
        # Serialize variables for prompt
        variables_summary = []
        for var in dag.nodes:
            variables_summary.append(
                f"- {var.id}: {var.name} ({var.type}, {var.scope}, {var.controllability})"
            )

        variables_text = "\n".join(variables_summary)

        return f"""Você é um especialista em estatística quantificando variáveis com distribuições de probabilidade para simulação.

**Variáveis para quantificar**:
{variables_text}

**Tarefa**: Para cada variável, sugira uma distribuição de probabilidade com parâmetros realistas.

**Distribuições disponíveis**:
1. **uniform**: Uniforme(low, high) - Probabilidade igual em todo o intervalo
   - Use para: Variáveis desconhecidas, sem conhecimento prévio
   - Exemplo: {{\"type\": \"uniform\", \"params\": {{\"low\": 0.0, \"high\": 1.0}}}}

2. **normal**: Normal(mean, std) - Distribuição em forma de sino
   - Use para: Métricas contínuas com tendência central
   - Exemplo: {{\"type\": \"normal\", \"params\": {{\"mean\": 0.5, \"std\": 0.1}}}}

3. **beta**: Beta(alpha, beta) - Distribuição limitada [0, 1]
   - Use para: Probabilidades, taxas, percentuais
   - Exemplo: {{\"type\": \"beta\", \"params\": {{\"alpha\": 3.0, \"beta\": 7.0}}}}

4. **lognormal**: LogNormal(mean, sigma) - Apenas positiva, assimétrica à direita
   - Use para: Valores monetários, durações de tempo, taxas de crescimento
   - Exemplo: {{\"type\": \"lognormal\", \"params\": {{\"mean\": 3.0, \"sigma\": 0.5}}}}

5. **bernoulli**: Bernoulli(p) - Resultados binários (0 ou 1)
   - Use para: Eventos binários, resultados sim/não
   - Exemplo: {{\"type\": \"bernoulli\", \"params\": {{\"p\": 0.3}}}}

**Diretrizes**:
- Escolha a distribuição baseada no tipo de variável e domínio
- Use valores de parâmetros realistas (ex: taxas de conversão 2-15%, não 50%)
- Para taxas/percentuais, use distribuição beta limitada [0, 1]
- Para valores monetários, use lognormal (apenas positiva)
- Para resultados binários (modos de falha), use bernoulli
- Sugira 1-3 correlações chave entre variáveis (apenas se causalmente significativas)

**Formato de saída** (apenas JSON, sem markdown):
{{
  "hypotheses": [
    {{
      "variable_id": "var_001",
      "variable_name": "nome_variavel",
      "distribution_type": "uniform|normal|beta|lognormal|bernoulli",
      "parameters": {{}},  // Parâmetros específicos da distribuição
      "correlations": [  // Opcional, apenas se significativo
        {{
          "with_variable_id": "var_002",
          "with_variable_name": "outra_var",
          "correlation": 0.6,
          "rationale": "Por que estas variáveis são correlacionadas"
        }}
      ]
    }}
  ]
}}

Retorne APENAS o objeto JSON, sem texto ou formatação adicional.
"""

    def _parse_hypotheses_response(
        self, simulation_id: str, dag: CausalDAG, response: dict[str, Any]
    ) -> list[Hypothesis]:
        """
        Parse LLM response into Hypothesis entities.

        Maps LLM-generated variable IDs to actual DAG variable IDs using name lookup.

        Args:
            simulation_id: Parent simulation ID
            dag: Causal DAG (for variable lookup)
            response: Parsed JSON response from LLM

        Returns:
            List of Hypothesis entities
        """
        hypotheses = []

        # Create mappings from variable name to actual DAG variable ID
        name_to_id = {node.name: node.id for node in dag.nodes}

        for hyp_data in response.get("hypotheses", []):
            # Parse distribution type with fallback for unsupported types
            raw_dist_type = hyp_data["distribution_type"]
            try:
                dist_type = DistributionType(raw_dist_type)
            except ValueError:
                self.logger.warning(
                    f"Unsupported distribution type '{raw_dist_type}', "
                    f"falling back to uniform"
                )
                dist_type = DistributionType.UNIFORM

            # Parse distribution parameters
            params_data = hyp_data["parameters"]
            if dist_type == DistributionType.UNIFORM:
                # Handle fallback case with default params
                params = UniformParams(
                    low=params_data.get("low", 0.0),
                    high=params_data.get("high", 1.0),
                )
            elif dist_type == DistributionType.NORMAL:
                params = NormalParams(**params_data)
            elif dist_type == DistributionType.BETA:
                params = BetaParams(**params_data)
            elif dist_type == DistributionType.LOGNORMAL:
                params = LogNormalParams(**params_data)
            elif dist_type == DistributionType.BERNOULLI:
                params = BernoulliParams(**params_data)
            else:
                # This shouldn't happen due to fallback above
                params = UniformParams(low=0.0, high=1.0)

            # Get actual variable ID from DAG (LLM might use different format)
            var_name = hyp_data["variable_name"]
            actual_var_id = name_to_id.get(var_name, hyp_data["variable_id"])

            # Parse correlations with mapped IDs
            correlations = []
            for corr_data in hyp_data.get("correlations", []):
                corr_var_name = corr_data["with_variable_name"]
                actual_corr_id = name_to_id.get(
                    corr_var_name, corr_data["with_variable_id"]
                )
                correlations.append(
                    Correlation(
                        with_variable_id=actual_corr_id,
                        with_variable_name=corr_var_name,
                        correlation=corr_data["correlation"],
                        rationale=corr_data["rationale"],
                    )
                )

            hypotheses.append(
                Hypothesis(
                    simulation_id=simulation_id,
                    variable_id=actual_var_id,
                    variable_name=var_name,
                    distribution_type=dist_type,
                    parameters=params,
                    correlations=correlations,
                )
            )

        return hypotheses
