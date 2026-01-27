"""
HypothesisIndividualService for creating hypotheses for individual variables.

Used when nodes are added to the DAG after initial hypothesis generation.
Creates a single hypothesis using LLM with context from existing DAG.

References:
    - Spec: specs/035-causal-simulation/spec.md
    - Main service: hypothesis_parametrizer_service.py
"""

import json

from loguru import logger
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes

from synth_lab.domain.entities.causal_dag import CausalDAG, Variable
from synth_lab.domain.entities.hypothesis import (
    BernoulliParams,
    BetaParams,
    Correlation,
    DistributionType,
    Hypothesis,
    LogNormalParams,
    NormalParams,
    UniformParams,
    generate_hypothesis_id,
)
from synth_lab.infrastructure.llm_client import LLMClient
from synth_lab.infrastructure.phoenix_tracing import get_tracer

_tracer = get_tracer("hypothesis-individual-service")


class HypothesisIndividualService:
    """
    Service for creating hypotheses for individual variables.

    Used when:
    - User adds a new node to the DAG manually
    - Re-quantification of a single variable is needed

    Unlike HypothesisParametrizerService which quantifies all variables at once,
    this service focuses on a single variable with context from the existing DAG.
    """

    def __init__(self):
        """Initialize service with LLM client."""
        self.llm = LLMClient()
        self.logger = logger.bind(component="hypothesis_individual_service")

    def quantify_variable(
        self,
        simulation_id: str,
        variable: Variable,
        context_dag: CausalDAG,
    ) -> Hypothesis:
        """
        Quantify a single variable using LLM.

        Args:
            simulation_id: Parent simulation ID
            variable: The variable to quantify
            context_dag: Full DAG for context (other variables for correlations)

        Returns:
            Hypothesis entity with distribution and correlations

        Example:
            >>> service = HypothesisIndividualService()
            >>> new_var = Variable(name="price", type="observable", ...)
            >>> hypothesis = service.quantify_variable("sim_123", new_var, dag)
        """
        span_name = f"HypothesisIndividual | {variable.name}"
        with _tracer.start_as_current_span(
            span_name,
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.LLM.value,
                "operation.type": "hypothesis_individual_quantification",
                "simulation.id": simulation_id,
                "variable.id": variable.id,
                "variable.name": variable.name,
                "variable.type": (
                    variable.type if isinstance(variable.type, str) else variable.type.value
                ),
            },
        ):
            try:
                # Build prompt for single variable
                prompt = self._build_prompt(variable, context_dag)

                # Call LLM
                response_str = self.llm.complete_json(
                    messages=[{"role": "user", "content": prompt}],
                    model="gpt-4o",
                )

                # Parse response
                hypothesis = self._parse_response(
                    simulation_id, variable, response_str, context_dag
                )

                self.logger.info(
                    f"Quantified variable {variable.name}: {hypothesis.distribution_type.value}"
                )

                return hypothesis

            except Exception as e:
                self.logger.error(f"Failed to quantify {variable.name}: {e}")
                # Return default hypothesis on error
                return self._create_default_hypothesis(simulation_id, variable)

    def _build_prompt(self, variable: Variable, context_dag: CausalDAG) -> str:
        """Build LLM prompt for quantifying a single variable."""
        # Get context from existing variables
        other_vars = [v for v in context_dag.nodes if v.id != variable.id]
        other_vars_str = "\n".join(
            f"- {v.name} ({v.type if isinstance(v.type, str) else v.type.value}, "
            f"{v.scope if isinstance(v.scope, str) else v.scope.value}): {v.description}"
            for v in other_vars[:10]  # Limit context
        )

        # Get edges involving this variable
        edges_str = ""
        for edge in context_dag.edges:
            if edge.from_var == variable.name or edge.to_var == variable.name:
                edges_str += f"- {edge.from_var} → {edge.to_var}\n"

        prompt = f"""You are a quantitative analyst helping parametrize a causal simulation.

## New Variable to Quantify

- **Name**: {variable.name}
- **Type**: {variable.type if isinstance(variable.type, str) else variable.type.value}
- **Scope**: {variable.scope if isinstance(variable.scope, str) else variable.scope.value}
- **Description**: {variable.description}

## Context: Other Variables in the Model
{other_vars_str if other_vars_str else "(No other variables)"}

## Causal Relationships Involving This Variable
{edges_str if edges_str else "(No relationships defined yet)"}

## Task

Suggest a probability distribution for "{variable.name}" with reasonable default parameters.

Choose from:
- **uniform**: For values in a range (min, max)
- **normal**: For values around a mean (mean, std)
- **beta**: For probabilities/rates 0-1 (alpha, beta)
- **lognormal**: For positive skewed values (mu, sigma)
- **bernoulli**: For binary outcomes (probability)

Also suggest correlations with other variables if relevant (correlation coefficient -1 to 1).

## Response Format (JSON only, no markdown)

{{
  "distribution_type": "normal|uniform|beta|lognormal|bernoulli",
  "parameters": {{
    // For normal: "mean", "std"
    // For uniform: "min", "max"
    // For beta: "alpha", "beta"
    // For lognormal: "mu", "sigma"
    // For bernoulli: "probability"
  }},
  "correlations": [
    {{
      "with_variable_name": "other_variable_name",
      "correlation": 0.5,
      "rationale": "Why correlated"
    }}
  ],
  "rationale": "Brief explanation of why this distribution and parameters"
}}
"""
        return prompt

    def _parse_response(
        self,
        simulation_id: str,
        variable: Variable,
        response_str: str,
        context_dag: CausalDAG,
    ) -> Hypothesis:
        """Parse LLM response into Hypothesis entity."""
        try:
            data = json.loads(response_str)
        except json.JSONDecodeError:
            self.logger.warning("Failed to parse LLM response, using defaults")
            return self._create_default_hypothesis(simulation_id, variable)

        # Parse distribution type
        dist_type_str = data.get("distribution_type", "uniform").lower()
        try:
            dist_type = DistributionType(dist_type_str)
        except ValueError:
            dist_type = DistributionType.UNIFORM

        # Parse parameters
        params_data = data.get("parameters", {})
        parameters = self._parse_parameters(dist_type, params_data)

        # Parse correlations
        correlations = []
        name_to_id = {v.name: v.id for v in context_dag.nodes}
        for corr_data in data.get("correlations", []):
            var_name = corr_data.get("with_variable_name", "")
            if var_name in name_to_id:
                correlations.append(
                    Correlation(
                        with_variable_id=name_to_id[var_name],
                        with_variable_name=var_name,
                        correlation=float(corr_data.get("correlation", 0)),
                        rationale=corr_data.get("rationale", ""),
                    )
                )

        return Hypothesis(
            id=generate_hypothesis_id(),
            simulation_id=simulation_id,
            variable_id=variable.id,
            variable_name=variable.name,
            distribution_type=dist_type,
            parameters=parameters,
            correlations=correlations,
            version=1,
        )

    def _parse_parameters(self, dist_type: DistributionType, params_data: dict):
        """Parse distribution parameters from LLM response."""
        if dist_type == DistributionType.UNIFORM:
            return UniformParams(
                min=float(params_data.get("min", 0)),
                max=float(params_data.get("max", 1)),
            )
        elif dist_type == DistributionType.NORMAL:
            return NormalParams(
                mean=float(params_data.get("mean", 0)),
                std=float(params_data.get("std", 1)),
            )
        elif dist_type == DistributionType.BETA:
            return BetaParams(
                alpha=float(params_data.get("alpha", 2)),
                beta=float(params_data.get("beta", 5)),
            )
        elif dist_type == DistributionType.LOGNORMAL:
            return LogNormalParams(
                mu=float(params_data.get("mu", 0)),
                sigma=float(params_data.get("sigma", 1)),
            )
        elif dist_type == DistributionType.BERNOULLI:
            return BernoulliParams(
                probability=float(params_data.get("probability", 0.5)),
            )
        else:
            return UniformParams(min=0, max=1)

    def _create_default_hypothesis(self, simulation_id: str, variable: Variable) -> Hypothesis:
        """Create default hypothesis when LLM fails."""
        # Choose default based on variable type
        var_type = variable.type if isinstance(variable.type, str) else variable.type.value

        if var_type in ("failure", "bernoulli"):
            dist_type = DistributionType.BERNOULLI
            parameters = BernoulliParams(probability=0.1)
        elif var_type == "observable":
            dist_type = DistributionType.NORMAL
            parameters = NormalParams(mean=0, std=1)
        else:
            dist_type = DistributionType.UNIFORM
            parameters = UniformParams(min=0, max=1)

        return Hypothesis(
            id=generate_hypothesis_id(),
            simulation_id=simulation_id,
            variable_id=variable.id,
            variable_name=variable.name,
            distribution_type=dist_type,
            parameters=parameters,
            correlations=[],
            version=1,
        )
