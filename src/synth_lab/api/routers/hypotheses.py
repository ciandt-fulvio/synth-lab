"""
Hypotheses API router for editing and versioning hypothesis parameters.

REST endpoints for hypothesis CRUD, validation, and version management.

References:
    - Spec: specs/035-causal-simulation/spec.md
    - Data model: specs/035-causal-simulation/data-model.md
"""

from fastapi import APIRouter, HTTPException, status, Depends
from loguru import logger
from sqlalchemy.orm import Session

from synth_lab.api.schemas.hypothesis import (
    CorrelationSchema,
    DistributionParameters,
    HypothesesBulkUpdateRequest,
    HypothesisCompareRequest,
    HypothesisCompareResponse,
    HypothesisSchema,
    HypothesisUpdateRequest,
    HypothesisVersionCreateRequest,
    HypothesisVersionSchema,
)
from synth_lab.domain.entities.hypothesis import (
    Correlation,
    DistributionType,
    Hypothesis,
    HypothesisParameters,
)
from synth_lab.infrastructure.database_v2 import get_db_session
from synth_lab.repositories.hypothesis_repository import HypothesisRepository

router = APIRouter(prefix="/simulations", tags=["hypotheses"])


def _hypothesis_to_schema(hyp: Hypothesis) -> HypothesisSchema:
    """Convert Hypothesis entity to schema."""
    return HypothesisSchema(
        id=hyp.id,
        simulation_id=hyp.simulation_id,
        variable_name=hyp.variable_name,
        parameters=DistributionParameters(
            distribution_type=hyp.parameters.distribution_type.value,
            min_value=hyp.parameters.min_value,
            max_value=hyp.parameters.max_value,
            mean=hyp.parameters.mean,
            std_dev=hyp.parameters.std_dev,
            mode=hyp.parameters.mode,
            alpha=hyp.parameters.alpha,
            beta=hyp.parameters.beta,
        ),
        correlations=[
            CorrelationSchema(
                target_variable=c.target_variable,
                correlation_coefficient=c.correlation_coefficient,
                relationship_type=c.relationship_type,
            )
            for c in hyp.correlations
        ],
        version=hyp.version,
        rationale=hyp.rationale,
        sources=hyp.sources,
        created_at=hyp.created_at,
    )


def _schema_to_parameters(params: DistributionParameters) -> HypothesisParameters:
    """Convert schema to HypothesisParameters entity."""
    return HypothesisParameters(
        distribution_type=DistributionType(params.distribution_type),
        min_value=params.min_value,
        max_value=params.max_value,
        mean=params.mean,
        std_dev=params.std_dev,
        mode=params.mode,
        alpha=params.alpha,
        beta=params.beta,
    )


def _schema_to_correlation(corr: CorrelationSchema) -> Correlation:
    """Convert schema to Correlation entity."""
    return Correlation(
        target_variable=corr.target_variable,
        correlation_coefficient=corr.correlation_coefficient,
        relationship_type=corr.relationship_type,
    )


# =============================================================================
# Endpoints
# =============================================================================


@router.get(
    "/{simulation_id}/hypotheses",
    response_model=list[HypothesisSchema],
    summary="Get hypotheses for simulation",
    description="Retrieve all quantified hypotheses for a simulation",
)
async def get_hypotheses(
    simulation_id: str,
    db: Session = Depends(get_db_session),
) -> list[HypothesisSchema]:
    """
    Get all hypotheses for a simulation.

    Args:
        simulation_id: Simulation ID
        db: Database session

    Returns:
        List of hypotheses with parameters and correlations
    """
    hyp_repo = HypothesisRepository(session=db)
    hypotheses = hyp_repo.get_by_simulation_id(simulation_id)

    return [_hypothesis_to_schema(hyp) for hyp in hypotheses]


@router.put(
    "/{simulation_id}/hypotheses",
    response_model=list[HypothesisSchema],
    summary="Update hypotheses",
    description="Update hypothesis parameters for multiple variables",
)
async def update_hypotheses(
    simulation_id: str,
    request: HypothesesBulkUpdateRequest,
    db: Session = Depends(get_db_session),
) -> list[HypothesisSchema]:
    """
    Update multiple hypotheses at once.

    Args:
        simulation_id: Simulation ID
        request: Updates keyed by variable name
        db: Database session

    Returns:
        Updated hypotheses

    Raises:
        HTTPException: If validation fails
    """
    hyp_repo = HypothesisRepository(session=db)
    hypotheses = hyp_repo.get_by_simulation_id(simulation_id)

    if not hypotheses:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No hypotheses found for simulation {simulation_id}",
        )

    # Create lookup by variable name
    hyp_by_var = {h.variable_name: h for h in hypotheses}

    # Apply updates
    updated = []
    for var_name, update in request.updates.items():
        if var_name not in hyp_by_var:
            logger.warning(f"Variable {var_name} not found, skipping")
            continue

        hyp = hyp_by_var[var_name]

        if update.parameters:
            hyp.parameters = _schema_to_parameters(update.parameters)

        if update.correlations is not None:
            hyp.correlations = [_schema_to_correlation(c) for c in update.correlations]

        if update.rationale:
            hyp.rationale = update.rationale

        # Increment version
        hyp.version += 1
        updated.append(hyp)

    # Persist updates
    if updated:
        hyp_repo.update_batch(updated)
        logger.info(f"Updated {len(updated)} hypotheses for simulation {simulation_id}")

    # Return all hypotheses
    return [_hypothesis_to_schema(h) for h in hypotheses]


@router.put(
    "/{simulation_id}/hypotheses/{variable_name}",
    response_model=HypothesisSchema,
    summary="Update single hypothesis",
    description="Update hypothesis parameters for a single variable",
)
async def update_hypothesis(
    simulation_id: str,
    variable_name: str,
    request: HypothesisUpdateRequest,
    db: Session = Depends(get_db_session),
) -> HypothesisSchema:
    """
    Update a single hypothesis.

    Args:
        simulation_id: Simulation ID
        variable_name: Variable name
        request: Update request
        db: Database session

    Returns:
        Updated hypothesis

    Raises:
        HTTPException: If hypothesis not found
    """
    hyp_repo = HypothesisRepository(session=db)
    hypothesis = hyp_repo.get_by_variable(simulation_id, variable_name)

    if hypothesis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hypothesis for variable {variable_name} not found",
        )

    # Apply updates
    if request.parameters:
        hypothesis.parameters = _schema_to_parameters(request.parameters)

    if request.correlations is not None:
        hypothesis.correlations = [_schema_to_correlation(c) for c in request.correlations]

    if request.rationale:
        hypothesis.rationale = request.rationale

    # Increment version
    hypothesis.version += 1

    # Persist
    updated = hyp_repo.update(hypothesis)
    logger.info(f"Updated hypothesis for {variable_name} to version {updated.version}")

    return _hypothesis_to_schema(updated)


@router.post(
    "/{simulation_id}/hypotheses/versions",
    response_model=HypothesisVersionSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Save hypothesis version",
    description="Create a named snapshot of current hypothesis state",
)
async def save_hypothesis_version(
    simulation_id: str,
    request: HypothesisVersionCreateRequest,
    db: Session = Depends(get_db_session),
) -> HypothesisVersionSchema:
    """
    Save current hypothesis state as a named version.

    Args:
        simulation_id: Simulation ID
        request: Version name and description
        db: Database session

    Returns:
        Created version info
    """
    hyp_repo = HypothesisRepository(session=db)

    # Get current max version
    versions = hyp_repo.get_versions(simulation_id)
    next_version = max([v["version"] for v in versions], default=0) + 1

    # Create version snapshot
    version_info = hyp_repo.save_version(
        simulation_id,
        version=next_version,
        name=request.name,
        description=request.description,
    )

    logger.info(f"Saved hypothesis version {next_version} for simulation {simulation_id}")

    return HypothesisVersionSchema(
        version=version_info["version"],
        created_at=version_info["created_at"],
        name=version_info.get("name"),
        description=version_info.get("description"),
    )


@router.get(
    "/{simulation_id}/hypotheses/versions",
    response_model=list[HypothesisVersionSchema],
    summary="List hypothesis versions",
    description="Get version history for simulation hypotheses",
)
async def list_hypothesis_versions(
    simulation_id: str,
    db: Session = Depends(get_db_session),
) -> list[HypothesisVersionSchema]:
    """
    List all hypothesis versions for a simulation.

    Args:
        simulation_id: Simulation ID
        db: Database session

    Returns:
        List of version summaries
    """
    hyp_repo = HypothesisRepository(session=db)
    versions = hyp_repo.get_versions(simulation_id)

    return [
        HypothesisVersionSchema(
            version=v["version"],
            created_at=v["created_at"],
            name=v.get("name"),
            description=v.get("description"),
        )
        for v in versions
    ]


@router.get(
    "/{simulation_id}/hypotheses/versions/{version}",
    response_model=list[HypothesisSchema],
    summary="Get hypothesis version",
    description="Get hypotheses at a specific version",
)
async def get_hypothesis_version(
    simulation_id: str,
    version: int,
    db: Session = Depends(get_db_session),
) -> list[HypothesisSchema]:
    """
    Get hypotheses at a specific version.

    Args:
        simulation_id: Simulation ID
        version: Version number
        db: Database session

    Returns:
        Hypotheses at the specified version
    """
    hyp_repo = HypothesisRepository(session=db)
    hypotheses = hyp_repo.get_at_version(simulation_id, version)

    if not hypotheses:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version} not found",
        )

    return [_hypothesis_to_schema(hyp) for hyp in hypotheses]


@router.post(
    "/{simulation_id}/hypotheses/compare",
    response_model=HypothesisCompareResponse,
    summary="Compare hypothesis versions",
    description="Compare two hypothesis versions to see changes",
)
async def compare_hypothesis_versions(
    simulation_id: str,
    request: HypothesisCompareRequest,
    db: Session = Depends(get_db_session),
) -> HypothesisCompareResponse:
    """
    Compare two hypothesis versions.

    Args:
        simulation_id: Simulation ID
        request: Versions to compare
        db: Database session

    Returns:
        Diff showing changed parameters
    """
    hyp_repo = HypothesisRepository(session=db)

    hyps_a = hyp_repo.get_at_version(simulation_id, request.version_a)
    hyps_b = hyp_repo.get_at_version(simulation_id, request.version_b)

    if not hyps_a:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {request.version_a} not found",
        )

    if not hyps_b:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {request.version_b} not found",
        )

    # Create lookups
    hyps_a_by_var = {h.variable_name: h for h in hyps_a}
    hyps_b_by_var = {h.variable_name: h for h in hyps_b}

    changed_variables = []
    parameter_changes = {}
    correlation_changes = {}

    # Compare each variable
    all_vars = set(hyps_a_by_var.keys()) | set(hyps_b_by_var.keys())

    for var_name in all_vars:
        hyp_a = hyps_a_by_var.get(var_name)
        hyp_b = hyps_b_by_var.get(var_name)

        if hyp_a is None or hyp_b is None:
            changed_variables.append(var_name)
            continue

        # Compare parameters
        params_a = hyp_a.parameters.model_dump()
        params_b = hyp_b.parameters.model_dump()

        if params_a != params_b:
            changed_variables.append(var_name)
            parameter_changes[var_name] = {
                "before": params_a,
                "after": params_b,
            }

        # Compare correlations
        corrs_a = {c.target_variable: c for c in hyp_a.correlations}
        corrs_b = {c.target_variable: c for c in hyp_b.correlations}

        if set(corrs_a.keys()) != set(corrs_b.keys()):
            if var_name not in changed_variables:
                changed_variables.append(var_name)
            correlation_changes[var_name] = {
                "before": [c.model_dump() for c in hyp_a.correlations],
                "after": [c.model_dump() for c in hyp_b.correlations],
            }

    return HypothesisCompareResponse(
        changed_variables=changed_variables,
        parameter_changes=parameter_changes,
        correlation_changes=correlation_changes,
    )
