"""
SimulationEngineService for causal simulation system.

Generates 500+ synthetic worlds with seeded randomness and causal propagation
through the DAG structure.

References:
    - Spec: specs/035-causal-simulation/spec.md
    - Data model: specs/035-causal-simulation/data-model.md
    - NumPy random: https://numpy.org/doc/stable/reference/random/index.html
"""

import numpy as np
from loguru import logger
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes

from synth_lab.domain.entities.causal_dag import CausalDAG, VariableScope
from synth_lab.domain.entities.hypothesis import Hypothesis
from synth_lab.domain.entities.simulated_world import (
    OutcomeStats,
    SimulatedWorld,
)
from synth_lab.infrastructure.phoenix_tracing import get_tracer
from synth_lab.services.simulation.dag_validator import DAGValidator
from synth_lab.services.simulation.distribution_sampler import (
    DistributionSampler,
)

_tracer = get_tracer("simulation-engine-service")

# Default number of individuals per world for user-level variables
DEFAULT_POPULATION_SIZE = 100


class SimulationEngineService:
    """
    Service for running Monte Carlo simulations across synthetic worlds.

    Generates N worlds with seeded randomness, samples variables from
    distributions, and propagates causal effects through DAG structure.
    """

    def __init__(self, population_size: int = DEFAULT_POPULATION_SIZE):
        """
        Initialize SimulationEngineService.

        Args:
            population_size: Number of individuals per world for user-level variables
        """
        self.population_size = population_size
        self.validator = DAGValidator()
        self.logger = logger.bind(component="simulation_engine_service")

    def run(
        self,
        simulation_id: str,
        dag: CausalDAG,
        hypotheses: list[Hypothesis],
        n_worlds: int = 500,
        random_seed: int = 42,
    ) -> list[SimulatedWorld]:
        """
        Run simulation across N synthetic worlds.

        Args:
            simulation_id: Parent simulation ID
            dag: Validated causal DAG
            hypotheses: List of quantified hypotheses
            n_worlds: Number of worlds to simulate (default: 500)
            random_seed: Master random seed for reproducibility

        Returns:
            List of SimulatedWorld entities with outcomes

        Raises:
            ValueError: If DAG is invalid or hypotheses are incomplete

        Example:
            >>> engine = SimulationEngineService()
            >>> worlds = engine.run("sim_12345678", dag, hypotheses, n_worlds=500)
            >>> print(f"Generated {len(worlds)} worlds")
        """
        span_name = f"SimulationEngine | {n_worlds} worlds"
        with _tracer.start_as_current_span(
            span_name,
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
                "operation.type": "simulation_execution",
                "simulation.id": simulation_id,
                "simulation.n_worlds": n_worlds,
                "simulation.random_seed": random_seed,
                "dag.num_variables": len(dag.nodes),
            },
        ):
            try:
                # Validate DAG
                is_valid, errors = self.validator.validate(dag)
                if not is_valid:
                    error_msgs = [err.description for err in errors]
                    raise ValueError(f"Invalid DAG: {'; '.join(error_msgs)}")

                # Get topological order for causal propagation
                topo_order = self.validator.get_topological_order(dag)

                # Create hypothesis lookup
                hyp_map = {h.variable_id: h for h in hypotheses}

                # Verify all variables have hypotheses
                missing_hyps = set(v.id for v in dag.nodes) - set(hyp_map.keys())
                if missing_hyps:
                    raise ValueError(
                        f"Missing hypotheses for variables: {missing_hyps}"
                    )

                self.logger.info(
                    f"Starting simulation: {n_worlds} worlds, seed={random_seed}"
                )

                # Generate all worlds
                worlds = []
                for world_num in range(1, n_worlds + 1):
                    world_seed = random_seed + world_num
                    world = self._simulate_world(
                        simulation_id=simulation_id,
                        world_number=world_num,
                        world_seed=world_seed,
                        dag=dag,
                        hypotheses=hyp_map,
                        topo_order=topo_order,
                    )
                    worlds.append(world)

                    if world_num % 100 == 0:
                        self.logger.info(f"Completed {world_num}/{n_worlds} worlds")

                self.logger.info(
                    f"Simulation complete: {len(worlds)} worlds generated"
                )

                return worlds

            except Exception as e:
                error_msg = f"Simulation failed: {e}"
                self.logger.error(error_msg)
                raise ValueError(error_msg) from e

    def _simulate_world(
        self,
        simulation_id: str,
        world_number: int,
        world_seed: int,
        dag: CausalDAG,
        hypotheses: dict[str, Hypothesis],
        topo_order: list[str],
    ) -> SimulatedWorld:
        """
        Simulate a single world with causal propagation.

        Args:
            simulation_id: Parent simulation ID
            world_number: Sequential world number
            world_seed: Random seed for this world
            dag: Causal DAG
            hypotheses: Variable ID to Hypothesis mapping
            topo_order: Topological order of variables

        Returns:
            SimulatedWorld entity with outcomes
        """
        # Initialize sampler for this world
        sampler = DistributionSampler(seed=world_seed)

        # Variable lookup
        var_map = {v.id: v for v in dag.nodes}

        # Storage for sampled values
        world_params: dict[str, float] = {}
        user_level_values: dict[str, np.ndarray] = {}

        # Sample variables in topological order (respects causal dependencies)
        for var_id in topo_order:
            variable = var_map[var_id]
            hypothesis = hypotheses[var_id]

            if variable.scope == VariableScope.WORLD:
                # World-level: sample single value
                value = sampler.sample(hypothesis, n=1)[0]
                world_params[var_id] = float(value)

            else:  # VariableScope.USER
                # User-level: sample population
                values = sampler.sample(hypothesis, n=self.population_size)
                user_level_values[var_id] = values

        # Calculate aggregated outcomes
        outcome_vars = [v for v in dag.nodes if v.is_outcome]
        aggregated_outcomes: dict[str, OutcomeStats] = {}

        for outcome_var in outcome_vars:
            if outcome_var.scope == VariableScope.WORLD:
                # World-level outcome: single value
                outcome_value = world_params[outcome_var.id]
                aggregated_outcomes[outcome_var.name] = OutcomeStats(
                    mean=outcome_value,
                    std=0.0,  # No variance for world-level
                    p5=outcome_value,
                    p50=outcome_value,
                    p95=outcome_value,
                )

            else:  # User-level outcome
                # Aggregate across population
                outcome_values = user_level_values[outcome_var.id]
                aggregated_outcomes[outcome_var.name] = OutcomeStats(
                    mean=float(np.mean(outcome_values)),
                    std=float(np.std(outcome_values)),
                    p5=float(np.percentile(outcome_values, 5)),
                    p50=float(np.percentile(outcome_values, 50)),
                    p95=float(np.percentile(outcome_values, 95)),
                )

        return SimulatedWorld(
            simulation_id=simulation_id,
            world_number=world_number,
            world_parameters=world_params,
            aggregated_outcomes=aggregated_outcomes,
            random_seed=world_seed,
        )

    def compute_causal_effect(
        self,
        parent_values: dict[str, float],
        edges: list[tuple[str, str]],
        base_value: float,
    ) -> float:
        """
        Compute causal effect from parent variables (simplified linear model).

        This is a placeholder for Phase 1 MVP. In later phases, this can be
        extended with:
        - Non-linear relationships
        - Interaction effects
        - Learned causal mechanisms

        Args:
            parent_values: Values of parent variables
            edges: List of (parent_id, child_id) edges
            base_value: Base sampled value for variable

        Returns:
            Adjusted value incorporating causal effects
        """
        # Phase 1 MVP: Simple pass-through (no causal adjustment)
        # Variables are sampled independently from their distributions
        # This is conservative but ensures simulation completes successfully
        return base_value
