"""
Causal DAG API router for editing and validating DAG structures.

REST endpoints for DAG CRUD operations, validation, and versioning.

References:
    - Spec: specs/035-causal-simulation/spec.md
    - Data model: specs/035-causal-simulation/data-model.md
"""

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.orm import Session

from synth_lab.api.schemas.causal_dag import (
    DAGCompareRequest,
    DAGCompareResponse,
    DAGResponse,
    DAGUpdateRequest,
    DAGValidationRequest,
    DAGValidationResponse,
    DAGVersionResponse,
    EdgeSchema,
    SuggestedEdgeSchema,
    VariableEnrichRequest,
    VariableEnrichResponse,
    VariableSchema,
)
from synth_lab.domain.entities.causal_dag import (
    CausalDAG,
    Controllability,
    Edge,
    RelationshipType,
    Variable,
    VariableScope,
    VariableType,
)
from synth_lab.infrastructure.database_v2 import get_db_session
from synth_lab.repositories.causal_dag_repository import CausalDAGRepository
from synth_lab.repositories.hypothesis_repository import HypothesisRepository
from synth_lab.services.simulation.dag_validator import DAGValidator
from synth_lab.services.simulation.hypothesis_individual_service import HypothesisIndividualService
from synth_lab.services.simulation.variable_enrichment_service import VariableEnrichmentService

router = APIRouter(prefix="/simulations", tags=["dag"])


def _variable_to_schema(var: Variable) -> VariableSchema:
    """Convert Variable entity to schema."""
    return VariableSchema(
        name=var.name,
        label=var.name,  # Entity doesn't have label, use name
        variable_type=var.type,  # Already a string due to use_enum_values
        scope=var.scope,  # Already a string due to use_enum_values
        description=var.description,
        unit=None,  # Entity doesn't have unit field
        position_x=var.position_x,
        position_y=var.position_y,
    )


def _edge_to_schema(edge: Edge) -> EdgeSchema:
    """Convert Edge entity to schema."""
    return EdgeSchema(
        source=edge.from_var,  # Entity uses 'from_var' not 'source'
        target=edge.to_var,  # Entity uses 'to_var' not 'target'
        relationship_type=edge.relationship_type,  # Already a string due to use_enum_values
        strength=None,  # Entity doesn't have strength field
        description=None,  # Entity doesn't have description field
    )


def _schema_to_variable(schema: VariableSchema) -> Variable:
    """Convert schema to Variable entity."""
    # Map schema variable_type to entity VariableType
    # Schema uses input/intermediate/output, entity uses observable/latent/etc
    type_mapping = {
        "input": VariableType.OBSERVABLE,
        "intermediate": VariableType.OBSERVABLE,
        "output": VariableType.OBSERVABLE,
        "observable": VariableType.OBSERVABLE,
        "latent": VariableType.LATENT,
        "friction": VariableType.FRICTION,
        "failure": VariableType.FAILURE,
        "process": VariableType.PROCESS,
        "temporal": VariableType.TEMPORAL,
    }
    var_type = type_mapping.get(schema.variable_type.lower(), VariableType.OBSERVABLE)

    return Variable(
        id=f"var_{schema.name}",  # Generate ID from name
        name=schema.name,
        type=var_type,
        scope=VariableScope(schema.scope),
        description=schema.description or "",
        controllability=Controllability.MEDIUM,  # Default value
        is_intervention=False,  # Default value
        is_outcome=False,  # Default value
        position_x=schema.position_x,
        position_y=schema.position_y,
    )


def _schema_to_edge(schema: EdgeSchema) -> Edge:
    """Convert schema to Edge entity."""
    return Edge(
        from_var=schema.source,  # Schema uses 'source', entity uses 'from_var'
        to_var=schema.target,  # Schema uses 'target', entity uses 'to_var'
        relationship_type=RelationshipType(schema.relationship_type),
    )


# =============================================================================
# Endpoints
# =============================================================================


@router.get(
    "/{simulation_id}/dag",
    response_model=DAGResponse,
    summary="Get DAG for simulation",
    description="Retrieve the causal DAG structure for a simulation",
)
async def get_dag(
    simulation_id: str,
    db: Session = Depends(get_db_session),
) -> DAGResponse:
    """
    Get DAG by simulation ID.

    Args:
        simulation_id: Simulation ID
        db: Database session

    Returns:
        DAG with nodes and edges

    Raises:
        HTTPException: If DAG not found
    """
    dag_repo = CausalDAGRepository(session=db)
    dag = dag_repo.get_by_simulation_id(simulation_id)

    if dag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"DAG not found for simulation {simulation_id}",
        )

    return DAGResponse(
        id=dag.id,
        simulation_id=dag.simulation_id,
        nodes=[_variable_to_schema(v) for v in dag.nodes],
        edges=[_edge_to_schema(e) for e in dag.edges],
        version=dag.version,
        created_at=dag.created_at,
        updated_at=None,  # Entity doesn't have updated_at field
    )


@router.put(
    "/{simulation_id}/dag",
    response_model=DAGResponse,
    summary="Update DAG",
    description="Update the causal DAG structure (add/remove nodes and edges)",
)
async def update_dag(
    simulation_id: str,
    request: DAGUpdateRequest,
    db: Session = Depends(get_db_session),
) -> DAGResponse:
    """
    Update DAG structure.

    Supports:
    - Full replacement (nodes/edges fields)
    - Incremental updates (add_nodes, remove_nodes, add_edges, remove_edges)

    Args:
        simulation_id: Simulation ID
        request: Update request with changes
        db: Database session

    Returns:
        Updated DAG

    Raises:
        HTTPException: If DAG not found or validation fails
    """
    dag_repo = CausalDAGRepository(session=db)
    dag = dag_repo.get_by_simulation_id(simulation_id)

    if dag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"DAG not found for simulation {simulation_id}",
        )

    # Track new and removed nodes for hypothesis management
    new_nodes = []
    removed_node_ids = []

    # Apply updates
    if request.nodes is not None:
        # Full replacement of nodes
        dag.nodes = [_schema_to_variable(v) for v in request.nodes]
    else:
        # Incremental updates
        if request.add_nodes:
            for node_schema in request.add_nodes:
                new_var = _schema_to_variable(node_schema)
                dag.nodes.append(new_var)
                new_nodes.append(new_var)

        if request.remove_nodes:
            # Track removed variable IDs for hypothesis cleanup
            for node in dag.nodes:
                if node.name in request.remove_nodes:
                    removed_node_ids.append(node.id)

            dag.nodes = [n for n in dag.nodes if n.name not in request.remove_nodes]
            # Also remove edges connected to removed nodes
            dag.edges = [
                e
                for e in dag.edges
                if e.from_var not in request.remove_nodes and e.to_var not in request.remove_nodes
            ]

    if request.edges is not None:
        # Full replacement of edges
        dag.edges = [_schema_to_edge(e) for e in request.edges]
    else:
        # Incremental updates
        if request.add_edges:
            for edge_schema in request.add_edges:
                dag.edges.append(_schema_to_edge(edge_schema))

        if request.remove_edges:
            remove_set = set(request.remove_edges)
            dag.edges = [e for e in dag.edges if (e.from_var, e.to_var) not in remove_set]

    # Validate updated DAG (lenient mode for editing)
    is_valid, validation_errors, validation_warnings = DAGValidator.validate(dag)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Invalid DAG structure",
                "errors": [str(e) for e in validation_errors],
            },
        )

    # Log warnings but allow operation
    for warning in validation_warnings:
        logger.warning(f"DAG validation warning: {warning}")

    # Increment version
    dag.version += 1

    # Save updated DAG
    updated_dag = dag_repo.update(dag)
    logger.info(f"Updated DAG for simulation {simulation_id} to version {dag.version}")

    # Delete hypotheses for removed nodes
    if removed_node_ids:
        hypothesis_repo = HypothesisRepository(session=db)
        deleted_count = hypothesis_repo.delete_by_variable_ids(simulation_id, removed_node_ids)
        logger.info(f"Deleted {deleted_count} hypotheses for removed nodes")

    # Create hypotheses for new nodes
    if new_nodes:
        hypothesis_service = HypothesisIndividualService()
        hypothesis_repo = HypothesisRepository(session=db)
        new_hypotheses = []

        for new_var in new_nodes:
            try:
                hypothesis = hypothesis_service.quantify_variable(
                    simulation_id=simulation_id,
                    variable=new_var,
                    context_dag=updated_dag,
                )
                new_hypotheses.append(hypothesis)
                logger.info(f"Created hypothesis for new variable {new_var.name}")
            except Exception as e:
                logger.error(f"Failed to create hypothesis for {new_var.name}: {e}")
                # Continue with other nodes even if one fails

        if new_hypotheses:
            hypothesis_repo.create_batch(new_hypotheses)
            logger.info(f"Saved {len(new_hypotheses)} hypotheses for new nodes")

    return DAGResponse(
        id=updated_dag.id,
        simulation_id=updated_dag.simulation_id,
        nodes=[_variable_to_schema(v) for v in updated_dag.nodes],
        edges=[_edge_to_schema(e) for e in updated_dag.edges],
        version=updated_dag.version,
        created_at=updated_dag.created_at,
        updated_at=None,  # Entity doesn't have updated_at field
    )


@router.post(
    "/{simulation_id}/dag/validate",
    response_model=DAGValidationResponse,
    summary="Validate DAG structure",
    description="Check DAG for cycles, orphan nodes, and other structural issues",
)
async def validate_dag(
    simulation_id: str,
    request: DAGValidationRequest,
    db: Session = Depends(get_db_session),
) -> DAGValidationResponse:
    """
    Validate a proposed DAG structure.

    This endpoint validates without persisting changes.

    Args:
        simulation_id: Simulation ID (for context)
        request: Proposed nodes and edges
        db: Database session

    Returns:
        Validation result with errors and warnings
    """
    # Build temporary DAG for validation
    temp_dag = CausalDAG(
        simulation_id=simulation_id,
        nodes=[_schema_to_variable(v) for v in request.nodes],
        edges=[_schema_to_edge(e) for e in request.edges],
    )

    is_valid, validation_errors, validation_warnings = DAGValidator.validate(temp_dag)

    # Check for orphan nodes (nodes without any connections)
    connected_nodes = set()
    for edge in temp_dag.edges:
        connected_nodes.add(edge.from_var)
        connected_nodes.add(edge.to_var)

    all_nodes = {n.name for n in temp_dag.nodes}
    orphan_nodes = list(all_nodes - connected_nodes)

    # Check if any error is a cycle
    has_cycles = any(e.error_type == "cycle" for e in validation_errors)

    return DAGValidationResponse(
        valid=is_valid,
        errors=[str(e) for e in validation_errors],
        warnings=[str(w) for w in validation_warnings],
        has_cycles=has_cycles,
        orphan_nodes=orphan_nodes,
    )


@router.get(
    "/{simulation_id}/dag/versions",
    response_model=list[DAGVersionResponse],
    summary="List DAG versions",
    description="Get version history for a simulation's DAG",
)
async def list_dag_versions(
    simulation_id: str,
    db: Session = Depends(get_db_session),
) -> list[DAGVersionResponse]:
    """
    List all DAG versions for a simulation.

    Args:
        simulation_id: Simulation ID
        db: Database session

    Returns:
        List of version summaries
    """
    dag_repo = CausalDAGRepository(session=db)
    versions = dag_repo.get_versions(simulation_id)

    return [
        DAGVersionResponse(
            version=v["version"],
            created_at=v["created_at"],
            node_count=v["node_count"],
            edge_count=v["edge_count"],
            description=v.get("description"),
        )
        for v in versions
    ]


@router.post(
    "/{simulation_id}/dag/compare",
    response_model=DAGCompareResponse,
    summary="Compare DAG versions",
    description="Compare two versions of a DAG to see changes",
)
async def compare_dag_versions(
    simulation_id: str,
    request: DAGCompareRequest,
    db: Session = Depends(get_db_session),
) -> DAGCompareResponse:
    """
    Compare two DAG versions.

    Args:
        simulation_id: Simulation ID
        request: Versions to compare
        db: Database session

    Returns:
        Diff showing added/removed/modified elements
    """
    dag_repo = CausalDAGRepository(session=db)

    dag_a = dag_repo.get_version(simulation_id, request.version_a)
    dag_b = dag_repo.get_version(simulation_id, request.version_b)

    if dag_a is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {request.version_a} not found",
        )

    if dag_b is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {request.version_b} not found",
        )

    # Compare nodes
    nodes_a = {n.name: n for n in dag_a.nodes}
    nodes_b = {n.name: n for n in dag_b.nodes}

    added_nodes = list(set(nodes_b.keys()) - set(nodes_a.keys()))
    removed_nodes = list(set(nodes_a.keys()) - set(nodes_b.keys()))

    # Check for modified nodes
    modified_nodes = []
    for name in set(nodes_a.keys()) & set(nodes_b.keys()):
        if nodes_a[name] != nodes_b[name]:
            modified_nodes.append(name)

    # Compare edges
    edges_a = {(e.from_var, e.to_var) for e in dag_a.edges}
    edges_b = {(e.from_var, e.to_var) for e in dag_b.edges}

    added_edges = list(edges_b - edges_a)
    removed_edges = list(edges_a - edges_b)

    return DAGCompareResponse(
        added_nodes=added_nodes,
        removed_nodes=removed_nodes,
        added_edges=added_edges,
        removed_edges=removed_edges,
        modified_nodes=modified_nodes,
    )


@router.patch(
    "/{simulation_id}/dag/positions",
    response_model=DAGResponse,
    summary="Update node positions",
    description="Update visualization positions for DAG nodes without incrementing version",
)
async def update_node_positions(
    simulation_id: str,
    positions: dict[str, dict[str, float]],
    db: Session = Depends(get_db_session),
) -> DAGResponse:
    """
    Update node positions for visualization.

    This endpoint only updates position_x and position_y fields without
    incrementing the DAG version, since it's purely for UI state.

    Args:
        simulation_id: Simulation ID
        positions: Dict mapping node names to {x: float, y: float}
        db: Database session

    Returns:
        Updated DAG with new positions

    Example request:
        {
            "sistema_checkout": {"x": 100, "y": 200},
            "taxa_conversao": {"x": 400, "y": 200}
        }
    """
    dag_repo = CausalDAGRepository(session=db)
    dag = dag_repo.get_by_simulation_id(simulation_id)

    if dag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"DAG not found for simulation {simulation_id}",
        )

    # Update positions for matching nodes
    for node in dag.nodes:
        if node.name in positions:
            pos = positions[node.name]
            node.position_x = pos.get("x")
            node.position_y = pos.get("y")

    # Save in-place without incrementing version
    updated_dag = dag_repo.update_in_place(dag)
    logger.info(f"Updated node positions for DAG {simulation_id}")

    return DAGResponse(
        id=updated_dag.id,
        simulation_id=updated_dag.simulation_id,
        nodes=[_variable_to_schema(v) for v in updated_dag.nodes],
        edges=[_edge_to_schema(e) for e in updated_dag.edges],
        version=updated_dag.version,
        created_at=updated_dag.created_at,
        updated_at=None,  # Entity doesn't have updated_at field
    )


@router.post(
    "/{simulation_id}/dag/enrich-variable",
    response_model=VariableEnrichResponse,
    summary="Enrich variable metadata using LLM",
    description="Generate type, scope, description, and suggested edges for a new variable",
)
async def enrich_variable(
    simulation_id: str,
    request: VariableEnrichRequest,
    db: Session = Depends(get_db_session),
) -> VariableEnrichResponse:
    """
    Enrich a variable with LLM-generated metadata.

    This endpoint uses gpt-4o-mini to analyze the variable name in the context
    of the existing DAG and suggests:
    - Variable type (observable, latent, friction, etc.)
    - Scope (world vs user level)
    - Description in Portuguese
    - Controllability level
    - Whether it's an intervention or outcome
    - Suggested causal edges to existing variables

    This is designed to be called asynchronously when a user adds a node with
    only a name, enriching the node metadata without blocking the UI.

    Args:
        simulation_id: Simulation ID for DAG context
        request: Variable name and optional hints
        db: Database session

    Returns:
        Enriched variable metadata with suggested edges

    Example request:
        {
            "variable_name": "taxa_conversao",
            "intervention_hint": "Novo sistema de checkout",
            "outcome_hint": "Aumentar vendas"
        }
    """
    dag_repo = CausalDAGRepository(session=db)
    dag = dag_repo.get_by_simulation_id(simulation_id)

    if dag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"DAG not found for simulation {simulation_id}",
        )

    # Call enrichment service
    enrichment_service = VariableEnrichmentService()
    enriched_var, suggested_edges = enrichment_service.enrich(
        variable_name=request.variable_name,
        context_dag=dag,
        intervention_hint=request.intervention_hint,
        outcome_hint=request.outcome_hint,
    )

    logger.info(
        f"Enriched variable {request.variable_name}: "
        f"type={enriched_var.type.value}, {len(suggested_edges)} suggested edges"
    )

    return VariableEnrichResponse(
        name=enriched_var.name,
        variable_type=enriched_var.type.value,
        scope=enriched_var.scope.value,
        description=enriched_var.description,
        controllability=enriched_var.controllability.value,
        is_intervention=enriched_var.is_intervention,
        is_outcome=enriched_var.is_outcome,
        suggested_edges=[
            SuggestedEdgeSchema(
                source=e.from_var,
                target=e.to_var,
                relationship_type=e.relationship_type.value,
                rationale="Relação causal inferida pelo contexto do DAG",
            )
            for e in suggested_edges
        ],
    )
