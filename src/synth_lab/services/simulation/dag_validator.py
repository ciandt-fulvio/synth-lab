"""
DAG Validator for causal simulation system.

Validates causal DAG structures for cycles, orphan nodes, and structural issues.
Uses NetworkX for graph algorithms.

References:
    - Spec: specs/035-causal-simulation/spec.md
    - NetworkX cycles: https://networkx.org/documentation/stable/reference/algorithms/cycles.html
    - NetworkX DAG: https://networkx.org/documentation/stable/reference/algorithms/dag.html
"""

import networkx as nx

from synth_lab.domain.entities.causal_dag import CausalDAG, ValidationError


class DAGValidator:
    """
    Validator for causal DAG structures.

    Validates DAGs for structural issues:
    - Cycles (DAG must be acyclic)
    - Orphan nodes (disconnected components)
    - Missing intervention/outcome variables
    - Invalid edge references
    """

    @staticmethod
    def validate(
        dag: CausalDAG, strict: bool = False
    ) -> tuple[bool, list[ValidationError], list[ValidationError]]:
        """
        Validate a causal DAG structure.

        Args:
            dag: CausalDAG entity to validate
            strict: If True, treat warnings as errors (for final simulation run)

        Returns:
            Tuple of (is_valid, errors, warnings)
            - is_valid: True if DAG passes critical validation checks
            - errors: Critical errors that block operations (cycles, invalid refs)
            - warnings: Non-critical issues (orphan nodes, missing markers)

        Example:
            >>> dag = CausalDAG(...)
            >>> is_valid, errors, warnings = DAGValidator.validate(dag)
            >>> if not is_valid:
            ...     print(f"Validation failed: {errors}")
        """
        errors: list[ValidationError] = []
        warnings: list[ValidationError] = []

        # Build NetworkX graph from DAG
        G = DAGValidator._build_networkx_graph(dag)

        # ERROR: Detect cycles (critical - blocks everything)
        if not nx.is_directed_acyclic_graph(G):
            try:
                cycle = nx.find_cycle(G, orientation="original")
                cycle_nodes = [edge[0] for edge in cycle]
                errors.append(
                    ValidationError(
                        error_type="cycle",
                        description=f"DAG contains cycle: {' → '.join(cycle_nodes)}",
                        affected_nodes=cycle_nodes,
                    )
                )
            except nx.NetworkXNoCycle:
                pass  # Should not happen if is_directed_acyclic_graph is False

        # ERROR: Verify all edge references point to valid nodes (critical)
        node_names = {node.name for node in dag.nodes}
        for edge in dag.edges:
            if edge.from_var not in node_names:
                errors.append(
                    ValidationError(
                        error_type="invalid_edge_source",
                        description=f"Edge source '{edge.from_var}' not found in nodes",
                        affected_nodes=[edge.from_var],
                    )
                )
            if edge.to_var not in node_names:
                errors.append(
                    ValidationError(
                        error_type="invalid_edge_target",
                        description=f"Edge target '{edge.to_var}' not found in nodes",
                        affected_nodes=[edge.to_var],
                    )
                )

        # WARNING: Detect orphan nodes (allowed during editing, issue for simulation)
        if len(G.nodes()) > 0 and not nx.is_weakly_connected(G):
            components = list(nx.weakly_connected_components(G))
            if len(components) > 1:
                for component in components[1:]:  # Skip largest component
                    warning = ValidationError(
                        error_type="orphan_nodes",
                        description=f"Disconnected component: {', '.join(component)}",
                        affected_nodes=list(component),
                    )
                    if strict:
                        errors.append(warning)
                    else:
                        warnings.append(warning)

        # WARNING: Verify intervention variable exists
        intervention_nodes = [node.name for node in dag.nodes if node.is_intervention]
        if len(intervention_nodes) == 0:
            warning = ValidationError(
                error_type="missing_intervention",
                description="No intervention variable marked (is_intervention=True)",
                affected_nodes=[],
            )
            if strict:
                errors.append(warning)
            else:
                warnings.append(warning)
        elif len(intervention_nodes) > 1:
            warning = ValidationError(
                error_type="multiple_interventions",
                description=f"Multiple intervention variables: {', '.join(intervention_nodes)}",
                affected_nodes=intervention_nodes,
            )
            if strict:
                errors.append(warning)
            else:
                warnings.append(warning)

        # WARNING: Verify at least one outcome variable exists
        outcome_nodes = [node.name for node in dag.nodes if node.is_outcome]
        if len(outcome_nodes) == 0:
            warning = ValidationError(
                error_type="missing_outcome",
                description="No outcome variable marked (is_outcome=True)",
                affected_nodes=[],
            )
            if strict:
                errors.append(warning)
            else:
                warnings.append(warning)

        is_valid = len(errors) == 0
        return is_valid, errors, warnings

    @staticmethod
    def _build_networkx_graph(dag: CausalDAG) -> nx.DiGraph:
        """
        Build NetworkX DiGraph from CausalDAG entity.

        Args:
            dag: CausalDAG entity

        Returns:
            NetworkX directed graph
        """
        G = nx.DiGraph()

        # Add nodes using variable names (since edges reference names)
        for node in dag.nodes:
            G.add_node(node.name, **node.model_dump())

        # Add edges (edges already use variable names in from_var/to_var)
        for edge in dag.edges:
            G.add_edge(edge.from_var, edge.to_var, **edge.model_dump())

        return G

    @staticmethod
    def get_topological_order(dag: CausalDAG) -> list[str]:
        """
        Get topological ordering of variables (for causal propagation).

        Args:
            dag: CausalDAG entity (must be valid)

        Returns:
            List of variable IDs in topological order

        Raises:
            ValueError: If DAG contains cycles

        Example:
            >>> order = DAGValidator.get_topological_order(dag)
            >>> # Variables can be simulated in this order
        """
        G = DAGValidator._build_networkx_graph(dag)

        if not nx.is_directed_acyclic_graph(G):
            raise ValueError("Cannot compute topological order: DAG contains cycles")

        return list(nx.topological_sort(G))
