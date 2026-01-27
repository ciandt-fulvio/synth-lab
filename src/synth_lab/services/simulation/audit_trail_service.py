"""
AuditTrailService for causal simulation system.

Provides audit trail recording and deterministic replay for simulations.

References:
    - Spec: specs/035-causal-simulation/spec.md
    - Data model: specs/035-causal-simulation/data-model.md
"""

from loguru import logger
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes

from synth_lab.domain.entities.audit_trail import (
    AuditTrail,
    DAGSnapshot,
    EvidenceSnapshot,
    HypothesisSnapshotItem,
    InsightSnapshot,
)
from synth_lab.domain.entities.causal_dag import CausalDAG
from synth_lab.domain.entities.hypothesis import Hypothesis
from synth_lab.domain.entities.simulated_world import (
    BehavioralCluster,
    Evidence,
    FailureMode,
)
from synth_lab.domain.entities.simulation import Simulation
from synth_lab.infrastructure.phoenix_tracing import get_tracer
from synth_lab.repositories.audit_trail_repository import AuditTrailRepository

_tracer = get_tracer("audit-trail-service")


class AuditTrailService:
    """
    Service for recording and replaying simulation audit trails.

    Captures all inputs and outputs to enable exact replay of simulations.
    """

    def __init__(self, audit_repo: AuditTrailRepository):
        """
        Initialize AuditTrailService.

        Args:
            audit_repo: Repository for audit trail storage
        """
        self.audit_repo = audit_repo
        self.logger = logger.bind(component="audit_trail_service")

    def record(
        self,
        simulation: Simulation,
        dag: CausalDAG,
        hypotheses: list[Hypothesis],
        evidence: Evidence,
        failure_modes: list[FailureMode],
        clusters: list[BehavioralCluster],
        insights: list[dict],
    ) -> AuditTrail:
        """
        Record a complete audit trail for a simulation run.

        Args:
            simulation: Completed simulation
            dag: Causal DAG used in simulation
            hypotheses: Hypotheses used in simulation
            evidence: Computed evidence
            failure_modes: Detected failure modes
            clusters: Detected clusters
            insights: Generated insights

        Returns:
            Created audit trail

        Example:
            >>> audit = audit_service.record(
            ...     simulation, dag, hypotheses, evidence, failure_modes, clusters, insights
            ... )
            >>> print(f"Audit trail created: {audit.id}")
        """
        span_name = f"AuditTrail.record | {simulation.id}"
        with _tracer.start_as_current_span(
            span_name,
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
                "operation.type": "audit_record",
                "simulation.id": simulation.id,
            },
        ):
            self.logger.info(f"Recording audit trail for simulation {simulation.id}")

            # Create DAG snapshot
            dag_snapshot = DAGSnapshot(
                version=dag.version,
                nodes=[node.model_dump() for node in dag.nodes],
                edges=[edge.model_dump() for edge in dag.edges],
            )

            # Create hypotheses snapshot
            hypotheses_snapshot = [
                HypothesisSnapshotItem(
                    variable_id=h.variable_id,
                    variable_name=h.variable_name,
                    distribution_type=h.distribution_type.value,
                    parameters=h.parameters.model_dump(),
                )
                for h in hypotheses
            ]

            # Create evidence snapshot
            evidence_snapshot = EvidenceSnapshot(
                outcome_distributions={
                    name: dist.model_dump()
                    for name, dist in evidence.outcome_distributions.items()
                },
                variance_explained=[vc.model_dump() for vc in evidence.variance_explained],
                n_failure_modes=len(failure_modes),
                n_clusters=len(clusters),
            )

            # Create insights snapshot
            insights_snapshot = [
                InsightSnapshot(
                    id=i.get("id", ""),
                    insight_type=i.get("insight_type", "recommendation"),
                    title=i.get("title", ""),
                    description=i.get("description", "")[:200],
                )
                for i in insights
            ]

            # Create audit trail
            audit_trail = AuditTrail(
                simulation_id=simulation.id,
                question=simulation.question_text,
                dag_snapshot=dag_snapshot,
                hypotheses_snapshot=hypotheses_snapshot,
                random_seed=simulation.random_seed or 42,
                n_worlds=simulation.n_worlds or 500,
                evidence_snapshot=evidence_snapshot,
                insights_snapshot=insights_snapshot,
            )

            # Persist audit trail
            audit_trail = self.audit_repo.create(audit_trail)

            self.logger.info(f"Audit trail created: {audit_trail.id}")

            return audit_trail

    def get_audit(self, simulation_id: str) -> AuditTrail | None:
        """
        Get the latest audit trail for a simulation.

        Args:
            simulation_id: Simulation ID

        Returns:
            Latest audit trail or None
        """
        return self.audit_repo.get_by_simulation_id(simulation_id)

    def get_replay_config(self, audit_id: str) -> dict | None:
        """
        Get configuration for replaying a simulation.

        Args:
            audit_id: Audit trail ID

        Returns:
            Replay configuration dict or None
        """
        audit = self.audit_repo.get(audit_id)
        if audit is None:
            return None
        return audit.get_replay_config()

    def export_audit(self, audit_id: str) -> dict | None:
        """
        Export full audit trail as a portable package.

        Args:
            audit_id: Audit trail ID

        Returns:
            Export package dict or None
        """
        audit = self.audit_repo.get(audit_id)
        if audit is None:
            return None
        return audit.to_export_package()

    def replay(
        self,
        simulation_id: str,
        simulation_engine,
        evidence_calculator,
    ) -> tuple[Evidence, list[FailureMode], list[BehavioralCluster]] | None:
        """
        Replay a simulation using stored audit trail.

        Reproduces identical results using the same seed and parameters.

        Args:
            simulation_id: Simulation ID to replay
            simulation_engine: SimulationEngineService instance
            evidence_calculator: EvidenceCalculatorService instance

        Returns:
            Tuple of (evidence, failure_modes, clusters) or None if not found

        Example:
            >>> evidence, failures, clusters = audit_service.replay(
            ...     "sim_12345678", engine, calculator
            ... )
        """
        span_name = f"AuditTrail.replay | {simulation_id}"
        with _tracer.start_as_current_span(
            span_name,
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
                "operation.type": "audit_replay",
                "simulation.id": simulation_id,
            },
        ):
            # Get audit trail
            audit = self.audit_repo.get_by_simulation_id(simulation_id)
            if audit is None:
                self.logger.warning(f"No audit trail found for simulation {simulation_id}")
                return None

            self.logger.info(
                f"Replaying simulation {simulation_id} with seed {audit.random_seed}"
            )

            # Reconstruct DAG from snapshot
            from synth_lab.domain.entities.causal_dag import CausalDAG, Variable, Edge

            nodes = [Variable(**node_data) for node_data in audit.dag_snapshot.nodes]
            edges = [Edge(**edge_data) for edge_data in audit.dag_snapshot.edges]

            dag = CausalDAG(
                simulation_id=simulation_id,
                version=audit.dag_snapshot.version,
                nodes=nodes,
                edges=edges,
            )

            # Reconstruct hypotheses from snapshot
            from synth_lab.domain.entities.hypothesis import (
                DistributionType,
                Hypothesis,
                NormalParams,
                UniformParams,
            )

            hypotheses = []
            for h_snap in audit.hypotheses_snapshot:
                # Determine distribution type and params
                dist_type = DistributionType(h_snap.distribution_type)
                if dist_type == DistributionType.NORMAL:
                    params = NormalParams(**h_snap.parameters)
                else:
                    params = UniformParams(**h_snap.parameters)

                hyp = Hypothesis(
                    simulation_id=simulation_id,
                    variable_id=h_snap.variable_id,
                    variable_name=h_snap.variable_name,
                    distribution_type=dist_type,
                    parameters=params,
                )
                hypotheses.append(hyp)

            # Run simulation with same seed
            worlds = simulation_engine.run(
                simulation_id=simulation_id,
                dag=dag,
                hypotheses=hypotheses,
                n_worlds=audit.n_worlds,
                random_seed=audit.random_seed,
            )

            # Calculate evidence
            evidence, failure_modes, clusters = evidence_calculator.aggregate(
                simulation_id, dag, worlds
            )

            self.logger.info(
                f"Replay completed: {len(worlds)} worlds, "
                f"{len(failure_modes)} failure modes, {len(clusters)} clusters"
            )

            return evidence, failure_modes, clusters
