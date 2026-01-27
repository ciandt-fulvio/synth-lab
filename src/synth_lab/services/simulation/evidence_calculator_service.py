"""
EvidenceCalculatorService for causal simulation system.

Aggregates simulation results into percentiles, sensitivity analysis, failure
modes, and behavioral clusters for comprehensive uncertainty analysis.

References:
    - Spec: specs/035-causal-simulation/spec.md
    - Data model: specs/035-causal-simulation/data-model.md
    - NumPy percentiles: https://numpy.org/doc/stable/reference/generated/numpy.percentile.html
"""

import numpy as np
from loguru import logger
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes

from synth_lab.domain.entities.causal_dag import CausalDAG
from synth_lab.domain.entities.simulated_world import (
    BehavioralCluster,
    Evidence,
    FailureMode,
    PercentileDistribution,
    SimulatedWorld,
    VarianceContribution,
)
from synth_lab.infrastructure.phoenix_tracing import get_tracer
from synth_lab.services.simulation.cluster_detector import ClusterDetector
from synth_lab.services.simulation.failure_mode_detector import (
    FailureModeDetector,
)
from synth_lab.services.simulation.sensitivity_analyzer import (
    SensitivityAnalyzer,
)

_tracer = get_tracer("evidence-calculator-service")


class EvidenceCalculatorService:
    """
    Service for aggregating simulation results into statistical evidence.

    Computes percentile distributions, variance decomposition, failure modes,
    and behavioral clusters from simulated worlds.
    """

    def __init__(
        self,
        cluster_detector: ClusterDetector | None = None,
        failure_detector: FailureModeDetector | None = None,
    ):
        """
        Initialize EvidenceCalculatorService.

        Args:
            cluster_detector: Cluster detector. Defaults to new instance.
            failure_detector: Failure mode detector. Defaults to new instance.
        """
        self.cluster_detector = cluster_detector or ClusterDetector()
        self.failure_detector = failure_detector or FailureModeDetector()
        self.logger = logger.bind(component="evidence_calculator_service")

    def aggregate(
        self,
        simulation_id: str,
        dag: CausalDAG,
        worlds: list[SimulatedWorld],
    ) -> tuple[Evidence, list[FailureMode], list[BehavioralCluster]]:
        """
        Aggregate simulation results into statistical evidence.

        Args:
            simulation_id: Parent simulation ID
            dag: Causal DAG
            worlds: List of simulated worlds

        Returns:
            Tuple of (Evidence, FailureModes, BehavioralClusters)

        Raises:
            ValueError: If aggregation fails

        Example:
            >>> calculator = EvidenceCalculatorService()
            >>> evidence, failures, clusters = calculator.aggregate(
            ...     "sim_12345678", dag, worlds
            ... )
            >>> print(f"p50: {evidence.outcome_distributions['adoption_rate'].p50}")
        """
        span_name = f"EvidenceCalculator | {len(worlds)} worlds"
        with _tracer.start_as_current_span(
            span_name,
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
                "operation.type": "evidence_calculation",
                "simulation.id": simulation_id,
                "simulation.n_worlds": len(worlds),
            },
        ):
            try:
                self.logger.info(
                    f"Aggregating evidence from {len(worlds)} worlds"
                )

                # Extract outcome variables
                outcome_vars = [v for v in dag.nodes if v.is_outcome]

                # Build matrices for analysis
                variable_matrix, outcome_matrix, var_names, outcome_names = (
                    self._build_matrices(worlds, dag, outcome_vars)
                )

                # Calculate percentile distributions
                outcome_distributions = self._calculate_percentiles(
                    outcome_matrix, outcome_names
                )

                # Calculate variance explained (sensitivity analysis)
                variance_explained = self._calculate_variance(
                    variable_matrix, outcome_matrix, var_names, outcome_names
                )

                # Calculate correlation matrix
                correlation_matrix = SensitivityAnalyzer.compute_correlation_matrix(
                    variable_matrix, var_names
                )

                # Create Evidence entity
                evidence = Evidence(
                    simulation_id=simulation_id,
                    outcome_distributions=outcome_distributions,
                    variance_explained=variance_explained,
                    correlation_matrix=correlation_matrix,
                )

                # Detect failure modes for each outcome
                failure_modes = self._detect_failure_modes(
                    evidence.id,
                    variable_matrix,
                    outcome_matrix,
                    var_names,
                    outcome_names,
                )

                # Detect behavioral clusters
                world_ids = [w.id for w in worlds]
                clusters = self.cluster_detector.detect_clusters(
                    variable_matrix=variable_matrix,
                    outcome_matrix=outcome_matrix,
                    variable_names=var_names,
                    outcome_names=outcome_names,
                    world_ids=world_ids,
                    evidence_id=evidence.id,
                )

                self.logger.info(
                    f"Evidence aggregation complete: {len(outcome_distributions)} outcomes, "
                    f"{len(failure_modes)} failure modes, {len(clusters)} clusters"
                )

                return evidence, failure_modes, clusters

            except Exception as e:
                error_msg = f"Evidence calculation failed: {e}"
                self.logger.error(error_msg)
                raise ValueError(error_msg) from e

    def _build_matrices(
        self,
        worlds: list[SimulatedWorld],
        dag: CausalDAG,
        outcome_vars: list,
    ) -> tuple[np.ndarray, np.ndarray, list[str], list[str]]:
        """
        Build matrices for statistical analysis.

        Args:
            worlds: List of simulated worlds
            dag: Causal DAG
            outcome_vars: List of outcome variables

        Returns:
            Tuple of (variable_matrix, outcome_matrix, var_names, outcome_names)
        """
        n_worlds = len(worlds)

        # Extract all world-level variables (for variance analysis)
        # Note: world_parameters is keyed by variable ID, not name
        world_vars = [v for v in dag.nodes if v.id in worlds[0].world_parameters]
        var_names = [v.name for v in world_vars]
        n_vars = len(var_names)

        # Build variable matrix (n_worlds x n_vars)
        variable_matrix = np.zeros((n_worlds, n_vars))
        for i, world in enumerate(worlds):
            for j, var in enumerate(world_vars):
                variable_matrix[i, j] = world.world_parameters.get(var.id, 0.0)

        # Build outcome matrix (n_worlds x n_outcomes)
        outcome_names = [v.name for v in outcome_vars]
        n_outcomes = len(outcome_names)
        outcome_matrix = np.zeros((n_worlds, n_outcomes))

        for i, world in enumerate(worlds):
            for j, outcome_name in enumerate(outcome_names):
                if outcome_name in world.aggregated_outcomes:
                    outcome_matrix[i, j] = world.aggregated_outcomes[
                        outcome_name
                    ].mean

        return variable_matrix, outcome_matrix, var_names, outcome_names

    def _calculate_percentiles(
        self, outcome_matrix: np.ndarray, outcome_names: list[str]
    ) -> dict[str, PercentileDistribution]:
        """
        Calculate percentile distributions for outcomes.

        Args:
            outcome_matrix: Matrix of outcome values (n_worlds x n_outcomes)
            outcome_names: Names of outcomes

        Returns:
            Dictionary mapping outcome names to PercentileDistribution
        """
        distributions = {}

        for i, outcome_name in enumerate(outcome_names):
            values = outcome_matrix[:, i]

            distributions[outcome_name] = PercentileDistribution(
                p5=float(np.percentile(values, 5)),
                p25=float(np.percentile(values, 25)),
                p50=float(np.percentile(values, 50)),
                p75=float(np.percentile(values, 75)),
                p95=float(np.percentile(values, 95)),
                mean=float(np.mean(values)),
                std=float(np.std(values)),
            )

        return distributions

    def _calculate_variance(
        self,
        variable_matrix: np.ndarray,
        outcome_matrix: np.ndarray,
        var_names: list[str],
        outcome_names: list[str],
    ) -> list[VarianceContribution]:
        """
        Calculate variance explained for each outcome.

        Uses first outcome variable for variance decomposition.

        Args:
            variable_matrix: Matrix of variable values
            outcome_matrix: Matrix of outcome values
            var_names: Variable names
            outcome_names: Outcome names

        Returns:
            List of VarianceContribution entities
        """
        # For MVP, analyze first outcome only
        if len(outcome_names) == 0:
            return []

        primary_outcome = outcome_matrix[:, 0]

        contributions = SensitivityAnalyzer.analyze_variance(
            variable_matrix, primary_outcome, var_names
        )

        return contributions

    def _detect_failure_modes(
        self,
        evidence_id: str,
        variable_matrix: np.ndarray,
        outcome_matrix: np.ndarray,
        var_names: list[str],
        outcome_names: list[str],
    ) -> list[FailureMode]:
        """
        Detect failure modes for outcomes.

        Args:
            evidence_id: Parent evidence ID
            variable_matrix: Matrix of variable values
            outcome_matrix: Matrix of outcome values
            var_names: Variable names
            outcome_names: Outcome names

        Returns:
            List of FailureMode entities
        """
        all_failure_modes = []

        # For MVP, detect failure modes for first outcome only
        if len(outcome_names) == 0:
            return []

        outcome_name = outcome_names[0]
        outcome_values = outcome_matrix[:, 0]

        # Define failure threshold (below p25 is considered "poor outcome")
        failure_threshold = float(np.percentile(outcome_values, 25))

        failure_modes = self.failure_detector.detect_failure_modes(
            variable_matrix=variable_matrix,
            outcome_vector=outcome_values,
            variable_names=var_names,
            outcome_name=outcome_name,
            evidence_id=evidence_id,
            outcome_failure_threshold=failure_threshold,
        )

        all_failure_modes.extend(failure_modes)

        return all_failure_modes
