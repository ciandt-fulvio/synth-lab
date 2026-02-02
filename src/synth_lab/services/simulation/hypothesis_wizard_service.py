"""
HypothesisWizardService para geração simplificada de hipóteses.

Fornece wizard guiado com seleção de perfil de cenário (Conservador/Realista/Otimista)
e perguntas de clarificação qualitativas para refinar distribuições.

Referências:
    - Spec: specs/036-simplified-hypothesis-wizard/spec.md
    - Research: specs/036-simplified-hypothesis-wizard/research.md
    - Data Model: specs/036-simplified-hypothesis-wizard/data-model.md
"""

from loguru import logger

from synth_lab.domain.entities.causal_dag import CausalDAG, Variable
from synth_lab.domain.entities.hypothesis import Hypothesis, ScenarioProfile
from synth_lab.infrastructure.llm_client import LLMClient, get_llm_client
from synth_lab.infrastructure.phoenix_tracing import get_tracer
from synth_lab.repositories.hypothesis_repository import HypothesisRepository
from synth_lab.services.simulation.hypothesis_parametrizer_service import (
    HypothesisParametrizerService,
)

# Phoenix/OpenTelemetry tracer for observability
_tracer = get_tracer("hypothesis-wizard-service")


class HypothesisWizardService:
    """
    Serviço para geração simplificada de hipóteses via wizard.

    Orquestra:
    1. Seleção de perfil de cenário (Conservador/Realista/Otimista)
    2. Geração de hipóteses com ajustes de perfil
    3. Identificação de variáveis críticas
    4. Geração de perguntas de clarificação
    5. Aplicação de respostas qualitativas a distribuições
    """

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        parametrizer: HypothesisParametrizerService | None = None,
        repository: HypothesisRepository | None = None,
    ):
        """
        Inicializa HypothesisWizardService.

        Args:
            llm_client: Cliente LLM para geração. Padrão: singleton.
            parametrizer: Service para geração de hipóteses. Padrão: novo.
            repository: Repository para persistência. Padrão: novo.
        """
        self.llm = llm_client or get_llm_client()
        self._parametrizer = parametrizer or HypothesisParametrizerService(llm_client=self.llm)
        self._repository = repository or HypothesisRepository()
        self.logger = logger.bind(component="hypothesis_wizard_service")

    def _classify_decision_context(self, dag: CausalDAG) -> str:
        """
        Classifica contexto de decisão como 'simple' ou 'complex'.

        Heurística (Decision 4 do research.md):
        - Simple: ≤5 nodes
        - Complex: >10 nodes OU >3 outcomes OU >4 controllables OU high connectivity

        Args:
            dag: CausalDAG a classificar

        Returns:
            str: "simple" ou "complex"
        """
        from synth_lab.domain.entities.causal_dag import Controllability

        num_nodes = len(dag.nodes)
        num_edges = len(dag.edges)
        num_outcomes = sum(1 for v in dag.nodes if v.is_outcome)
        num_controllable = sum(
            1
            for v in dag.nodes
            if v.controllability in [Controllability.MEDIUM, Controllability.HIGH]
        )

        # Complex: large DAG or many outcomes/controllables (check first!)
        if num_nodes > 10 or num_outcomes > 3 or num_controllable > 4:
            return "complex"

        # Medium: check connectivity
        if num_nodes > 0 and num_edges / num_nodes > 1.5:  # Highly connected
            return "complex"

        # Simple: small DAG with clear focus
        if num_nodes <= 5:
            return "simple"

        return "simple"

    def _apply_profile_adjustments(
        self, hypothesis: Hypothesis, profile: ScenarioProfile
    ) -> Hypothesis:
        """
        Aplica ajustes de perfil de cenário aos parâmetros de distribuição.

        Implementa Decision 1 do research.md com ajustes por tipo de distribuição:
        - Conservative: piora outcomes (mean -, variance +)
        - Realistic: sem mudança (baseline)
        - Optimistic: melhora outcomes (mean +, variance -)

        Args:
            hypothesis: Hypothesis entity com distribuição
            profile: ScenarioProfile (CONSERVATIVE, REALISTIC, OPTIMISTIC)

        Returns:
            Hypothesis: Nova instância com parâmetros ajustados
        """
        from copy import deepcopy

        from synth_lab.domain.entities.hypothesis import (
            DistributionType,
            ScenarioProfile,
        )

        # Realistic = no change
        if profile == ScenarioProfile.REALISTIC:
            return hypothesis

        # Deep copy para não modificar original
        adjusted = deepcopy(hypothesis)

        # Ajustes por tipo de distribuição
        if hypothesis.distribution_type == DistributionType.NORMAL:
            params = adjusted.parameters
            if profile == ScenarioProfile.CONSERVATIVE:
                # μ - 0.5σ, σ × 1.5
                params.mean = params.mean - 0.5 * params.std
                params.std = params.std * 1.5
            elif profile == ScenarioProfile.OPTIMISTIC:
                # μ + 0.5σ, σ × 0.75
                params.mean = params.mean + 0.5 * params.std
                params.std = params.std * 0.75

        elif hypothesis.distribution_type == DistributionType.BETA:
            params = adjusted.parameters
            if profile == ScenarioProfile.CONSERVATIVE:
                # α × 0.7, β × 1.3 (shift toward failure)
                params.alpha = params.alpha * 0.7
                params.beta = params.beta * 1.3
            elif profile == ScenarioProfile.OPTIMISTIC:
                # α × 1.3, β × 0.7 (shift toward success)
                params.alpha = params.alpha * 1.3
                params.beta = params.beta * 0.7

        elif hypothesis.distribution_type == DistributionType.UNIFORM:
            params = adjusted.parameters
            range_val = params.high - params.low
            if profile == ScenarioProfile.CONSERVATIVE:
                # low - 0.2×range, high - 0.1×range
                params.low = params.low - 0.2 * range_val
                params.high = params.high - 0.1 * range_val
            elif profile == ScenarioProfile.OPTIMISTIC:
                # low + 0.1×range, high + 0.2×range
                params.low = params.low + 0.1 * range_val
                params.high = params.high + 0.2 * range_val

        elif hypothesis.distribution_type == DistributionType.LOGNORMAL:
            params = adjusted.parameters
            if profile == ScenarioProfile.CONSERVATIVE:
                # μ - 0.3, σ × 1.4
                params.mean = params.mean - 0.3
                params.sigma = params.sigma * 1.4
            elif profile == ScenarioProfile.OPTIMISTIC:
                # μ + 0.3, σ × 0.8
                params.mean = params.mean + 0.3
                params.sigma = params.sigma * 0.8

        elif hypothesis.distribution_type == DistributionType.BERNOULLI:
            params = adjusted.parameters
            if profile == ScenarioProfile.CONSERVATIVE:
                # p × 0.8
                params.p = params.p * 0.8
            elif profile == ScenarioProfile.OPTIMISTIC:
                # p × 1.2 (capped at 1.0)
                params.p = min(params.p * 1.2, 1.0)

        elif hypothesis.distribution_type == DistributionType.TRIANGULAR:
            params = adjusted.parameters
            range_val = params.max_value - params.min_value
            if profile == ScenarioProfile.CONSERVATIVE:
                # min - 0.15×range, mode - 0.1×range, max - 0.1×range
                params.min_value = params.min_value - 0.15 * range_val
                params.mode = params.mode - 0.1 * range_val
                params.max_value = params.max_value - 0.1 * range_val
            elif profile == ScenarioProfile.OPTIMISTIC:
                # min + 0.1×range, mode + 0.1×range, max + 0.15×range
                params.min_value = params.min_value + 0.1 * range_val
                params.mode = params.mode + 0.1 * range_val
                params.max_value = params.max_value + 0.15 * range_val

        return adjusted

    def init_wizard(
        self, simulation_id: str, dag: CausalDAG, scenario_profile: ScenarioProfile
    ) -> dict:
        """
        Inicializa wizard de hipóteses com perfil de cenário.

        Gera hipóteses baseline para todas as variáveis do DAG e aplica ajustes
        de perfil de cenário (Conservative/Realistic/Optimistic).

        Args:
            simulation_id: ID da simulação (formato sim_XXXXXXXX)
            dag: CausalDAG validado
            scenario_profile: ScenarioProfile (CONSERVATIVE, REALISTIC, OPTIMISTIC)

        Returns:
            dict com:
                - hypotheses: Lista de Hypothesis entities geradas e ajustadas
                - clarification_questions: Lista de perguntas de clarificação (vazio por ora)

        Raises:
            ValueError: Se geração de hipóteses falhar
        """
        with _tracer.start_as_current_span(
            "init_wizard",
            attributes={
                "simulation_id": simulation_id,
                "scenario_profile": str(scenario_profile),
            },
        ):
            self.logger.info(
                f"Initializing wizard for sim {simulation_id} profile={scenario_profile}"
            )

            # 1. Generate baseline hypotheses using parametrizer
            baseline_hypotheses = self._parametrizer.quantify(simulation_id, dag)
            self.logger.debug(f"Generated {len(baseline_hypotheses)} baseline hypotheses")

            # 2. Apply scenario profile adjustments
            adjusted_hypotheses = [
                self._apply_profile_adjustments(hyp, scenario_profile)
                for hyp in baseline_hypotheses
            ]
            self.logger.debug(f"Applied {scenario_profile} profile adjustments")

            # 3. Persist hypotheses (create new)
            persisted_hypotheses = self._repository.create_batch(adjusted_hypotheses)
            self.logger.info(f"Persisted {len(persisted_hypotheses)} hypotheses")

            # 4. Generate clarification questions for critical variables
            clarification_questions = self.generate_clarification_questions(
                dag, persisted_hypotheses
            )
            self.logger.debug(f"Generated {len(clarification_questions)} clarification questions")

            return {
                "hypotheses": persisted_hypotheses,
                "clarification_questions": clarification_questions,
            }

    def _calculate_impact_score(self, variable: Variable, dag: CausalDAG) -> float:
        """
        Calculate impact score for a variable.

        Impact score combines multiple factors:
        - is_outcome: 3.0 (outcome variables are most important)
        - controllability: MEDIUM=1.5, HIGH=2.5
        - out_degree: 1.0 per outgoing edge (influence on other variables)

        Args:
            variable: Variable entity to score
            dag: CausalDAG for calculating out_degree

        Returns:
            float: Impact score (typically 0.0 - 10.0)
        """
        from synth_lab.domain.entities.causal_dag import Controllability

        score = 0.0

        # Is outcome variable?
        if variable.is_outcome:
            score += 3.0

        # Controllability
        if variable.controllability == Controllability.MEDIUM:
            score += 1.5
        elif variable.controllability == Controllability.HIGH:
            score += 2.5

        # Out-degree (number of outgoing edges)
        out_degree = sum(1 for edge in dag.edges if edge.from_var == variable.id)
        score += out_degree * 1.0

        return score

    def _calculate_uncertainty_score(self, hypothesis: Hypothesis) -> float:
        """
        Calculate uncertainty score for a hypothesis.

        Uncertainty score is the distribution variance coefficient:
        - Normal/LogNormal: σ / μ (coefficient of variation)
        - Beta: sqrt(αβ / ((α+β)²(α+β+1))) (standard deviation)
        - Uniform: (max - min) / (max + min) (relative range)
        - Bernoulli: sqrt(p(1-p)) (standard deviation)
        - Triangular: (max - min) / mode (relative spread)

        Args:
            hypothesis: Hypothesis entity with distribution

        Returns:
            float: Uncertainty score (typically 0.0 - 1.0)
        """
        import math

        from synth_lab.domain.entities.hypothesis import DistributionType

        params = hypothesis.parameters
        dist_type = hypothesis.distribution_type

        if dist_type == DistributionType.NORMAL:
            # Coefficient of variation: σ / μ
            if params.mean == 0:
                return 1.0  # Infinite uncertainty
            return abs(params.std / params.mean)

        elif dist_type == DistributionType.LOGNORMAL:
            # Coefficient of variation: σ / μ
            if params.mean == 0:
                return 1.0
            return abs(params.sigma / params.mean)

        elif dist_type == DistributionType.BETA:
            # Standard deviation: sqrt(αβ / ((α+β)²(α+β+1)))
            alpha = params.alpha
            beta = params.beta
            variance = (alpha * beta) / ((alpha + beta) ** 2 * (alpha + beta + 1))
            return math.sqrt(variance)

        elif dist_type == DistributionType.UNIFORM:
            # Relative range: (max - min) / (max + min)
            if (params.low + params.high) == 0:
                return 1.0
            return abs((params.high - params.low) / (params.high + params.low))

        elif dist_type == DistributionType.BERNOULLI:
            # Standard deviation: sqrt(p(1-p))
            return math.sqrt(params.p * (1 - params.p))

        elif dist_type == DistributionType.TRIANGULAR:
            # Relative spread: (max - min) / mode
            if params.mode == 0:
                return 1.0
            return abs((params.max_value - params.min_value) / params.mode)

        else:
            # Fallback: assume medium uncertainty
            return 0.5

    def _rank_critical_variables(self, dag: CausalDAG, hypotheses: list[Hypothesis]) -> list[dict]:
        """
        Rank variables by criticality score (impact × uncertainty).

        Returns top 3-5 critical variables that would benefit most from clarification.
        Filters out variables with uncertainty_score < 0.3 (too certain to need clarification).

        Args:
            dag: CausalDAG for calculating impact scores
            hypotheses: List of Hypothesis entities

        Returns:
            List of dicts with {variable_id, variable_name, criticality_score}
        """
        # Calculate criticality for each variable
        criticality_data = []

        # Create variable lookup
        var_by_id = {v.id: v for v in dag.nodes}

        for hyp in hypotheses:
            variable = var_by_id.get(hyp.variable_id)
            if not variable:
                continue

            impact = self._calculate_impact_score(variable, dag)
            uncertainty = self._calculate_uncertainty_score(hyp)

            # Filter out low-uncertainty variables (< 0.3)
            if uncertainty < 0.3:
                continue

            criticality = impact * uncertainty

            criticality_data.append(
                {
                    "variable_id": hyp.variable_id,
                    "variable_name": hyp.variable_name,
                    "criticality_score": criticality,
                    "impact_score": impact,
                    "uncertainty_score": uncertainty,
                }
            )

        # Sort by criticality descending
        criticality_data.sort(key=lambda x: x["criticality_score"], reverse=True)

        # Take top N where N = min(5, max(3, num_variables))
        num_critical = min(5, max(3, len(criticality_data)))

        return criticality_data[:num_critical]

    def _generate_clarification_question(self, variable: Variable) -> str:
        """
        Generate clarification question for a variable.

        Uses algorithmic templates based on variable metadata.

        Args:
            variable: Variable entity

        Returns:
            str: Clarification question text
        """
        # Use variable label if available, otherwise use name
        var_label = variable.name

        # Generic question asking about magnitude/frequency
        question = f"{var_label} tende a ser maior ou menor que a média?"

        return question

    def _apply_response_adjustment(self, hypothesis: Hypothesis, response: str) -> Hypothesis:
        """
        Apply qualitative response adjustment to hypothesis distribution.

        Implements Decision 3 from research.md with response-specific adjustments:
        - "more": shift mean up, reduce variance
        - "less": shift mean down, reduce variance
        - "equal": no change (keep profile defaults)
        - "dont_know": keep mean, increase variance

        Args:
            hypothesis: Hypothesis entity with distribution
            response: Response type ("more", "less", "equal", "dont_know")

        Returns:
            Hypothesis: New instance with adjusted parameters
        """
        from copy import deepcopy

        from synth_lab.domain.entities.hypothesis import (
            DistributionType,
        )

        # "equal" = no change
        if response == "equal":
            return hypothesis

        # Deep copy to avoid modifying original
        adjusted = deepcopy(hypothesis)

        # Apply distribution-specific adjustments
        if hypothesis.distribution_type == DistributionType.NORMAL:
            params = adjusted.parameters
            if response == "more":
                # μ += 0.5σ, σ ×= 0.8
                params.mean = params.mean + 0.5 * params.std
                params.std = params.std * 0.8
            elif response == "less":
                # μ -= 0.5σ, σ ×= 0.8
                params.mean = params.mean - 0.5 * params.std
                params.std = params.std * 0.8
            elif response == "dont_know":
                # σ ×= 1.5 (keep mean)
                params.std = params.std * 1.5

        elif hypothesis.distribution_type == DistributionType.LOGNORMAL:
            params = adjusted.parameters
            if response == "more":
                # μ += 0.5σ, σ ×= 0.8
                params.mean = params.mean + 0.5 * params.sigma
                params.sigma = params.sigma * 0.8
            elif response == "less":
                # μ -= 0.5σ, σ ×= 0.8
                params.mean = params.mean - 0.5 * params.sigma
                params.sigma = params.sigma * 0.8
            elif response == "dont_know":
                # σ ×= 1.5 (keep mean)
                params.sigma = params.sigma * 1.5

        elif hypothesis.distribution_type == DistributionType.BETA:
            params = adjusted.parameters
            if response == "more":
                # α ×= 1.3, β ×= 0.8 (shift toward success)
                params.alpha = params.alpha * 1.3
                params.beta = params.beta * 0.8
            elif response == "less":
                # α ×= 0.8, β ×= 1.3 (shift toward failure)
                params.alpha = params.alpha * 0.8
                params.beta = params.beta * 1.3
            elif response == "dont_know":
                # α ×= 0.7, β ×= 0.7 (increase variance)
                params.alpha = params.alpha * 0.7
                params.beta = params.beta * 0.7

        elif hypothesis.distribution_type == DistributionType.UNIFORM:
            params = adjusted.parameters
            range_val = params.high - params.low
            if response == "more":
                # min += 0.2×range, max += 0.3×range
                params.low = params.low + 0.2 * range_val
                params.high = params.high + 0.3 * range_val
            elif response == "less":
                # min -= 0.3×range, max -= 0.2×range
                params.low = params.low - 0.3 * range_val
                params.high = params.high - 0.2 * range_val
            elif response == "dont_know":
                # min -= 0.2×range, max += 0.2×range
                params.low = params.low - 0.2 * range_val
                params.high = params.high + 0.2 * range_val

        elif hypothesis.distribution_type == DistributionType.BERNOULLI:
            params = adjusted.parameters
            if response == "more":
                # p ×= 1.2 (capped at 1.0)
                params.p = min(params.p * 1.2, 1.0)
            elif response == "less":
                # p ×= 0.8
                params.p = params.p * 0.8
            elif response == "dont_know":
                # Convert to Beta for higher uncertainty
                # Note: In practice, we keep as Bernoulli but this is the concept
                # For now, we don't change Bernoulli on "dont_know"
                pass

        elif hypothesis.distribution_type == DistributionType.TRIANGULAR:
            params = adjusted.parameters
            range_val = params.max_value - params.min_value
            if response == "more":
                # min += 0.1×range, mode += 0.15×range, max += 0.1×range
                params.min_value = params.min_value + 0.1 * range_val
                params.mode = params.mode + 0.15 * range_val
                params.max_value = params.max_value + 0.1 * range_val
            elif response == "less":
                # min -= 0.1×range, mode -= 0.15×range, max -= 0.1×range
                params.min_value = params.min_value - 0.1 * range_val
                params.mode = params.mode - 0.15 * range_val
                params.max_value = params.max_value - 0.1 * range_val
            elif response == "dont_know":
                # min -= 0.2×range, max += 0.2×range
                params.min_value = params.min_value - 0.2 * range_val
                params.max_value = params.max_value + 0.2 * range_val

        return adjusted

    def generate_clarification_questions(
        self, dag: CausalDAG, hypotheses: list[Hypothesis]
    ) -> list[dict]:
        """
        Generate 3-5 clarification questions for critical variables.

        Implements Decision 2 (criticality ranking) and Decision 4 (decision context)
        from research.md.

        Args:
            dag: CausalDAG for ranking variables
            hypotheses: List of Hypothesis entities with baseline distributions

        Returns:
            List[dict]: Clarification questions with variable_name, question_text, criticality_score
        """
        # Rank critical variables
        critical_vars = self._rank_critical_variables(dag, hypotheses)

        # Generate questions for each critical variable
        questions = []
        var_by_id = {v.id: v for v in dag.nodes}

        for var_info in critical_vars:
            variable = var_by_id.get(var_info["variable_id"])
            if not variable:
                continue

            question_text = self._generate_clarification_question(variable)

            questions.append(
                {
                    "variable_name": var_info["variable_name"],
                    "question_text": question_text,
                    "criticality_score": var_info["criticality_score"],
                }
            )

        return questions

    def apply_clarifications(self, simulation_id: str, clarifications: list[dict]) -> dict:
        """
        Apply clarification responses to refine hypothesis distributions.

        Takes user's qualitative responses ("more"/"less"/"equal"/"dont_know") and
        adjusts distributions accordingly using _apply_response_adjustment().

        Args:
            simulation_id: ID da simulação (formato sim_XXXXXXXX)
            clarifications: List of dicts with {variable_name, response}

        Returns:
            dict com:
                - hypotheses: Lista de Hypothesis entities atualizadas

        Raises:
            ValueError: Se simulation_id não existir ou clarifications inválidas
        """
        with _tracer.start_as_current_span(
            "apply_clarifications",
            attributes={
                "simulation_id": simulation_id,
                "num_clarifications": len(clarifications),
            },
        ):
            self.logger.info(
                f"Applying {len(clarifications)} clarifications for simulation {simulation_id}"
            )

            # 1. Load all hypotheses for this simulation
            hypotheses = self._repository.get_by_simulation(simulation_id)
            if not hypotheses:
                raise ValueError(f"No hypotheses found for simulation {simulation_id}")

            # 2. Create lookup for quick access
            hyp_by_var_name = {hyp.variable_name: hyp for hyp in hypotheses}

            # 3. Apply adjustments based on responses
            updated_hypotheses = []
            for clarification in clarifications:
                var_name = clarification.get("variable_name")
                response = clarification.get("response")

                if not var_name or not response:
                    self.logger.warning(f"Skipping invalid clarification: {clarification}")
                    continue

                hypothesis = hyp_by_var_name.get(var_name)
                if not hypothesis:
                    self.logger.warning(f"Hypothesis not found for variable {var_name}")
                    continue

                # Apply response adjustment
                adjusted = self._apply_response_adjustment(hypothesis, response)
                updated_hypotheses.append(adjusted)

            # 4. Persist updated hypotheses
            if updated_hypotheses:
                persisted = self._repository.update_batch(updated_hypotheses)
                self.logger.info(f"Updated {len(persisted)} hypotheses")
                return {"hypotheses": persisted}
            else:
                self.logger.info("No hypotheses updated (no valid clarifications)")
                return {"hypotheses": hypotheses}

    def _identify_high_uncertainty_variables(
        self, hypotheses: list[Hypothesis], threshold: float = 0.5
    ) -> list[dict]:
        """
        Identify variables with high uncertainty for display purposes.

        Returns variables whose uncertainty_score exceeds threshold, indicating
        they would benefit from clarification or have significant impact on
        simulation results.

        Args:
            hypotheses: List of Hypothesis entities
            threshold: Uncertainty score threshold (default 0.5)

        Returns:
            List[dict]: Variables with high uncertainty {variable_name, uncertainty_score}
        """
        high_uncertainty_vars = []

        for hyp in hypotheses:
            uncertainty = self._calculate_uncertainty_score(hyp)

            if uncertainty >= threshold:
                high_uncertainty_vars.append(
                    {
                        "variable_name": hyp.variable_name,
                        "uncertainty_score": uncertainty,
                    }
                )

        # Sort by uncertainty descending
        high_uncertainty_vars.sort(key=lambda x: x["uncertainty_score"], reverse=True)

        return high_uncertainty_vars
