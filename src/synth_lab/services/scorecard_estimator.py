"""
Scorecard dimension estimator using LLM.

Generates AI-powered estimates for scorecard dimensions based on
experiment data (name, hypothesis, description).

References:
    - Spec: specs/018-experiment-hub/spec.md (US4)
    - Architecture: docs/arquitetura.md (LLM in services with tracing)

Sample usage:
    from synth_lab.services.scorecard_estimator import ScorecardEstimator

    estimator = ScorecardEstimator()
    estimate = estimator.estimate_from_experiment(experiment)

Expected output:
    ScorecardEstimate with complexity, initial_effort, perceived_risk, time_to_value
"""

import json

from loguru import logger
from pydantic import BaseModel, Field

from synth_lab.infrastructure.llm_client import LLMClient, get_llm_client
from synth_lab.infrastructure.phoenix_tracing import get_tracer
from synth_lab.repositories.experiment_repository import ExperimentSummary

# Phoenix/OpenTelemetry tracer for observability
_tracer = get_tracer("scorecard-estimator")


class DimensionEstimate(BaseModel):
    """AI-generated dimension estimate."""

    value: float = Field(ge=0.0, le=1.0, description="Estimated score value in [0,1]")
    justification: str = Field(description="Brief justification for the score")
    min: float = Field(ge=0.0, le=1.0, description="Minimum uncertainty bound")
    max: float = Field(ge=0.0, le=1.0, description="Maximum uncertainty bound")


class ScorecardEstimate(BaseModel):
    """Complete scorecard estimate with all dimensions."""

    complexity: DimensionEstimate
    initial_effort: DimensionEstimate
    perceived_risk: DimensionEstimate
    time_to_value: DimensionEstimate


class ScorecardEstimationError(Exception):
    """Raised when scorecard estimation fails."""

    pass


class ScorecardEstimateInput(BaseModel):
    """Input for scorecard estimation (without experiment ID)."""

    name: str = Field(description="Feature name")
    hypothesis: str = Field(description="Hypothesis to test")
    description: str | None = Field(default=None, description="Additional description")


class ScorecardEstimator:
    """LLM-powered scorecard dimension estimator."""

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        """
        Initialize with optional LLM client.

        Args:
            llm_client: LLM client instance. If None, uses global client.
        """
        self.llm = llm_client or get_llm_client()
        self.logger = logger.bind(component="scorecard_estimator")

    def estimate_from_text(
        self,
        name: str,
        hypothesis: str,
        description: str | None = None,
    ) -> ScorecardEstimate:
        """
        Generate scorecard dimension estimates from text input.

        This method allows estimation without an existing experiment ID,
        useful for forms where the user wants to get AI estimates before
        creating the experiment.

        Args:
            name: Feature name.
            hypothesis: Hypothesis to test.
            description: Optional additional description.

        Returns:
            ScorecardEstimate with all dimension estimates.

        Raises:
            ScorecardEstimationError: If LLM call fails or returns invalid data.
        """
        with _tracer.start_as_current_span(
            "ScorecardEstimator: estimate_from_text",
            attributes={
                "feature_name": name,
            },
        ):
            prompt = self._build_prompt_from_text(name, hypothesis, description)

            self.logger.info(f"Estimating scorecard for feature: {name}")

            try:
                response = self.llm.complete_json(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    operation_name="Scorecard AI Estimation (Form)",
                )

                data = json.loads(response)

                estimate = ScorecardEstimate(
                    complexity=DimensionEstimate(**data["complexity"]),
                    initial_effort=DimensionEstimate(**data["initial_effort"]),
                    perceived_risk=DimensionEstimate(**data["perceived_risk"]),
                    time_to_value=DimensionEstimate(**data["time_to_value"]),
                )

                self.logger.info(f"Generated estimate for feature: {name}")
                return estimate

            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse LLM response: {e}")
                raise ScorecardEstimationError(f"Failed to parse AI response: {e}")
            except KeyError as e:
                self.logger.error(f"Missing field in LLM response: {e}")
                raise ScorecardEstimationError(f"AI response missing required field: {e}")
            except Exception as e:
                self.logger.error(f"Scorecard estimation failed: {e}")
                raise ScorecardEstimationError(f"AI estimation failed: {e}")

    def estimate_from_experiment(
        self,
        experiment: ExperimentSummary,
    ) -> ScorecardEstimate:
        """
        Generate scorecard dimension estimates from experiment data.

        Uses LLM to analyze the experiment's name, hypothesis, and description
        to estimate complexity, initial_effort, perceived_risk, and time_to_value.

        Args:
            experiment: Experiment with name, hypothesis, and description.

        Returns:
            ScorecardEstimate with all dimension estimates.

        Raises:
            ScorecardEstimationError: If LLM call fails or returns invalid data.
        """
        with _tracer.start_as_current_span(
            "ScorecardEstimator: estimate",
            attributes={
                "experiment_id": experiment.id,
                "experiment_name": experiment.name,
            },
        ):
            prompt = self._build_prompt(experiment)

            self.logger.info(f"Estimating scorecard for experiment {experiment.id}")

            try:
                response = self.llm.complete_json(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,  # Lower temperature for more consistent results
                    operation_name="Scorecard AI Estimation",
                )

                data = json.loads(response)

                estimate = ScorecardEstimate(
                    complexity=DimensionEstimate(**data["complexity"]),
                    initial_effort=DimensionEstimate(**data["initial_effort"]),
                    perceived_risk=DimensionEstimate(**data["perceived_risk"]),
                    time_to_value=DimensionEstimate(**data["time_to_value"]),
                )

                self.logger.info(f"Generated estimate for experiment {experiment.id}")
                return estimate

            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse LLM response: {e}")
                raise ScorecardEstimationError(f"Failed to parse AI response: {e}")
            except KeyError as e:
                self.logger.error(f"Missing field in LLM response: {e}")
                raise ScorecardEstimationError(f"AI response missing required field: {e}")
            except Exception as e:
                self.logger.error(f"Scorecard estimation failed: {e}")
                raise ScorecardEstimationError(f"AI estimation failed: {e}")

    def _build_prompt_from_text(
        self,
        name: str,
        hypothesis: str,
        description: str | None,
    ) -> str:
        """
        Build the estimation prompt from text inputs.

        Args:
            name: Feature name.
            hypothesis: Hypothesis to test.
            description: Optional additional description.

        Returns:
            Formatted prompt string.
        """
        return self._build_prompt_content(name, hypothesis, description)

    def _build_prompt(self, experiment: ExperimentSummary) -> str:
        """
        Build the estimation prompt from experiment data.

        Args:
            experiment: Experiment to build prompt for.

        Returns:
            Formatted prompt string.
        """
        return self._build_prompt_content(
            experiment.name,
            experiment.hypothesis,
            experiment.description,
        )

    def _build_prompt_content(
        self,
        name: str,
        hypothesis: str,
        description: str | None,
    ) -> str:
        """
        Build the estimation prompt content.

        Args:
            name: Feature name.
            hypothesis: Hypothesis to test.
            description: Optional additional description.

        Returns:
            Formatted prompt string.
        """
        return f"""Você é um especialista em UX e product management.
Sua tarefa é analisar uma feature/hipótese e estimar as dimensões do scorecard.

## Feature
Nome: {name}
Hipótese: {hypothesis}
Descrição: {description or "Não fornecida"}

## Regras de Scoring (0 = baixo / 1 = alto)

### Complexity (0.0-1.0)
Base: 0.0
- +0.2 por conceito novo para o usuário
- +0.2 se há estados invisíveis ou não óbvios
- +0.2 se usa termos técnicos
- +0.2 se envolve ação irreversível
- +0.2 se feedback é fraco ou atrasado

### Initial Effort
- 0.1: uso imediato, sem configuração
- 0.3: 1-2 passos simples
- 0.5: requer configuração básica
- 0.7+: requer onboarding dedicado

### Perceived Risk
- 0.1: totalmente reversível
- 0.4: afeta dados do usuário
- 0.7+: afeta dinheiro ou reputação

### Time to Value
- 0.1: valor imediato
- 0.3: valor na mesma sessão
- 0.6: valor após alguns dias
- 0.8+: valor futuro/incerto

## Instruções
1. Analise a feature considerando as regras acima
2. Para cada dimensão, forneça:
   - value: o score estimado (0.0 a 1.0)
   - justification: 1-2 frases objetivas explicando o score
   - min/max: intervalo de incerteza (ex: se value=0.4, min pode ser 0.3 e max 0.5)

Responda APENAS com o JSON no formato abaixo, sem texto adicional:
{{
  "complexity": {{"value": 0.XX, "justification": "...", "min": 0.XX, "max": 0.XX}},
  "initial_effort": {{"value": 0.XX, "justification": "...", "min": 0.XX, "max": 0.XX}},
  "perceived_risk": {{"value": 0.XX, "justification": "...", "min": 0.XX, "max": 0.XX}},
  "time_to_value": {{"value": 0.XX, "justification": "...", "min": 0.XX, "max": 0.XX}}
}}"""


if __name__ == "__main__":
    import sys
    from datetime import datetime

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Test 1: Prompt building
    total_tests += 1
    try:
        estimator = ScorecardEstimator()
        exp = ExperimentSummary(
            id="exp_test123",
            name="Dark Mode Toggle",
            hypothesis="Users will prefer dark mode for night usage",
            description="Add a toggle in settings",
            simulation_count=0,
            interview_count=0,
            created_at=datetime.now(),
            updated_at=None,
        )
        prompt = estimator._build_prompt(exp)
        if "Dark Mode Toggle" not in prompt:
            all_validation_failures.append("Prompt should contain experiment name")
        if "Complexity" not in prompt:
            all_validation_failures.append("Prompt should contain dimension names")
    except Exception as e:
        all_validation_failures.append(f"Prompt building failed: {e}")

    # Test 2: Model validation
    total_tests += 1
    try:
        estimate = DimensionEstimate(
            value=0.5,
            justification="Test justification",
            min=0.4,
            max=0.6,
        )
        if estimate.value != 0.5:
            all_validation_failures.append("DimensionEstimate value mismatch")
    except Exception as e:
        all_validation_failures.append(f"Model validation failed: {e}")

    # Test 3: Invalid value range
    total_tests += 1
    try:
        DimensionEstimate(value=1.5, justification="test", min=0.1, max=0.2)
        all_validation_failures.append("Should reject value > 1.0")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Wrong exception for invalid value: {e}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
