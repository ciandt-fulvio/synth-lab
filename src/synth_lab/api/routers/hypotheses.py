"""
Hypotheses API router for editing and versioning hypothesis parameters.

REST endpoints for hypothesis CRUD, validation, and version management.

References:
    - Spec: specs/035-causal-simulation/spec.md
    - Data model: specs/035-causal-simulation/data-model.md
"""

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.orm import Session

from synth_lab.api.schemas.hypothesis import (
    ClarificationQuestionSchema,
    CorrelationSchema,
    DistributionParameters,
    HypothesesBulkUpdateRequest,
    HypothesisCompareRequest,
    HypothesisCompareResponse,
    HypothesisSchema,
    HypothesisUpdateRequest,
    HypothesisVersionCreateRequest,
    HypothesisVersionSchema,
    ScenarioOptionSchema,
    WizardClarifyRequest,
    WizardClarifyResponse,
    WizardInitRequest,
    WizardInitResponse,
)
from synth_lab.domain.entities.hypothesis import (
    Correlation,
    DistributionType,
    Hypothesis,
    HypothesisParameters,
    Relevance,
    ScenarioProfile,
)
from synth_lab.infrastructure.database_v2 import get_db_session
from synth_lab.repositories.causal_dag_repository import CausalDAGRepository
from synth_lab.repositories.hypothesis_repository import HypothesisRepository
from synth_lab.services.simulation.hypothesis_wizard_service import (
    HypothesisWizardService,
)

router = APIRouter(prefix="/simulations", tags=["hypotheses"])


def _hypothesis_to_schema(hyp: Hypothesis) -> HypothesisSchema:
    """Convert Hypothesis entity to schema."""
    # Convert typed parameters to flat schema
    params = hyp.parameters
    dist_type = (
        hyp.distribution_type.value
        if hasattr(hyp.distribution_type, "value")
        else str(hyp.distribution_type)
    )

    # Map typed parameter fields to flat schema
    min_value = None
    max_value = None
    mean = None
    std_dev = None
    mode = None
    alpha = None
    beta = None

    if dist_type == "uniform":
        min_value = getattr(params, "low", getattr(params, "min", None))
        max_value = getattr(params, "high", getattr(params, "max", None))
    elif dist_type == "normal":
        mean = getattr(params, "mean", None)
        std_dev = getattr(params, "std", None)
    elif dist_type == "beta":
        alpha = getattr(params, "alpha", None)
        beta = getattr(params, "beta", None)
    elif dist_type == "lognormal":
        mean = getattr(params, "mu", getattr(params, "mean", None))
        std_dev = getattr(params, "sigma", None)
    elif dist_type == "bernoulli":
        # Bernoulli uses probability, map to mean for display
        mean = getattr(params, "probability", getattr(params, "p", None))

    # Convert scenario options if present
    scenario_options_schema = None
    if hyp.scenario_options:
        scenario_options_schema = [
            ScenarioOptionSchema(
                value=opt.value,
                label=opt.label,
                distribution_params=DistributionParameters(
                    distribution_type="triangular",
                    min_value=opt.distribution_params.min_value,
                    max_value=opt.distribution_params.max_value,
                    mode=opt.distribution_params.mode,
                ),
            )
            for opt in hyp.scenario_options
        ]

    # Get relevance as string
    relevance_str = (
        hyp.relevance.value if isinstance(hyp.relevance, Relevance) else (hyp.relevance or "medium")
    )

    return HypothesisSchema(
        id=hyp.id,
        simulation_id=hyp.simulation_id,
        variable_name=hyp.variable_name or hyp.variable_id,
        parameters=DistributionParameters(
            distribution_type=dist_type,
            min_value=min_value,
            max_value=max_value,
            mean=mean,
            std_dev=std_dev,
            mode=mode,
            alpha=alpha,
            beta=beta,
        ),
        relevance=relevance_str,
        range_min=hyp.range_min,
        range_max=hyp.range_max,
        correlations=[
            CorrelationSchema(
                target_variable=c.with_variable_name,
                correlation_coefficient=c.correlation,
                relationship_type="linear",
            )
            for c in (hyp.correlations or [])
        ],
        scenario_options=scenario_options_schema,
        selected_scenario=hyp.selected_scenario,
        version=hyp.version,
        rationale=getattr(hyp, "rationale", None),
        sources=getattr(hyp, "sources", []) or [],
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

        if update.selected_scenario is not None:
            hyp.selected_scenario = update.selected_scenario
            # If a scenario is selected, update parameters to match that scenario
            if hyp.scenario_options:
                for opt in hyp.scenario_options:
                    if opt.value == update.selected_scenario:
                        hyp.parameters = opt.distribution_params
                        break

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

    if request.selected_scenario is not None:
        hypothesis.selected_scenario = request.selected_scenario
        # If a scenario is selected, update parameters to match that scenario
        if hypothesis.scenario_options:
            for opt in hypothesis.scenario_options:
                if opt.value == request.selected_scenario:
                    hypothesis.parameters = opt.distribution_params
                    break

    if request.rationale:
        hypothesis.rationale = request.rationale

    # Increment version
    hypothesis.version += 1

    # Persist
    updated = hyp_repo.update(hypothesis)
    logger.info(f"Updated hypothesis for {variable_name} to version {updated.version}")

    return _hypothesis_to_schema(updated)


@router.patch(
    "/{simulation_id}/hypotheses/{hypothesis_id}",
    response_model=HypothesisSchema,
    summary="Partially update a hypothesis",
    description="Update relevance, range, or other fields of a single hypothesis by ID",
)
async def patch_hypothesis(
    simulation_id: str,
    hypothesis_id: str,
    request: HypothesisUpdateRequest,
    db: Session = Depends(get_db_session),
) -> HypothesisSchema:
    """
    Partially update a hypothesis (relevance, range, parameters).

    Validates range_min <= range_max when both are provided.
    """
    hyp_repo = HypothesisRepository(session=db)

    # Find hypothesis by ID
    hypotheses = hyp_repo.get_by_simulation_id(simulation_id)
    hypothesis = next((h for h in hypotheses if h.id == hypothesis_id), None)

    if hypothesis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hypothesis {hypothesis_id} not found in simulation {simulation_id}",
        )

    # Validate range_min <= range_max
    new_range_min = request.range_min if request.range_min is not None else hypothesis.range_min
    new_range_max = request.range_max if request.range_max is not None else hypothesis.range_max
    if new_range_min is not None and new_range_max is not None and new_range_min > new_range_max:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"range_min ({new_range_min}) must be <= range_max ({new_range_max})",
        )

    # Apply partial updates
    if request.relevance is not None:
        hypothesis.relevance = Relevance(request.relevance)

    if request.range_min is not None:
        hypothesis.range_min = request.range_min

    if request.range_max is not None:
        hypothesis.range_max = request.range_max

    if request.parameters is not None:
        hypothesis.parameters = _schema_to_parameters(request.parameters)

    if request.correlations is not None:
        hypothesis.correlations = [_schema_to_correlation(c) for c in request.correlations]

    if request.selected_scenario is not None:
        hypothesis.selected_scenario = request.selected_scenario

    if request.rationale is not None:
        hypothesis.rationale = request.rationale

    hypothesis.version += 1
    updated = hyp_repo.update(hypothesis)
    logger.info(f"PATCH hypothesis {hypothesis_id}: version {updated.version}")

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


@router.post(
    "/{simulation_id}/hypotheses/wizard/init",
    response_model=WizardInitResponse,
    status_code=status.HTTP_200_OK,
    summary="Initialize hypothesis wizard with scenario profile",
    description="""
    Generates baseline hypotheses for all DAG variables using the selected scenario profile
    (Conservative/Realistic/Optimistic). Returns generated hypotheses and clarification questions.

    Prerequisites:
    - Simulation must exist
    - CausalDAG must be validated and associated with simulation

    Side effects:
    - Creates/updates hypotheses in database
    """,
)
def init_wizard(
    simulation_id: str,
    request: WizardInitRequest,
    db: Session = Depends(get_db_session),
) -> WizardInitResponse:
    """
    Initialize hypothesis wizard with scenario profile selection.

    Args:
        simulation_id: Simulation ID (format sim_XXXXXXXX)
        request: Wizard init request with scenario_profile
        db: Database session

    Returns:
        WizardInitResponse with generated hypotheses and clarification questions

    Raises:
        HTTPException 404: If simulation or DAG not found
        HTTPException 400: If DAG is not validated
        HTTPException 500: If hypothesis generation fails
    """
    logger.info(
        "POST /simulations/{}/hypotheses/wizard/init - profile={}",
        simulation_id,
        request.scenario_profile,
    )

    # 1. Fetch CausalDAG for this simulation
    dag_repo = CausalDAGRepository(session=db)
    dag = dag_repo.get_by_simulation_id(simulation_id)

    if not dag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No DAG found for simulation {simulation_id}",
        )

    # 2. Validate DAG is ready
    if not dag.is_validated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DAG must be validated before initializing wizard",
        )

    # 3. Convert scenario_profile string to enum
    try:
        scenario_profile = ScenarioProfile(request.scenario_profile)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid scenario_profile: {request.scenario_profile}."
                " Must be one of: conservative, realistic, optimistic"
            ),
        )

    # 4. Initialize wizard service and generate hypotheses
    wizard_service = HypothesisWizardService()

    try:
        result = wizard_service.init_wizard(
            simulation_id=simulation_id,
            dag=dag,
            scenario_profile=scenario_profile,
        )
    except Exception as e:
        logger.error(f"Failed to initialize wizard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate hypotheses: {str(e)}",
        )

    # 5. Convert hypotheses to schemas
    hypotheses_schemas = [_hypothesis_to_schema(h) for h in result["hypotheses"]]

    # 6. Convert clarification questions to schemas
    clarification_questions_schemas = [
        ClarificationQuestionSchema(**q) for q in result["clarification_questions"]
    ]

    return WizardInitResponse(
        hypotheses=hypotheses_schemas,
        clarification_questions=clarification_questions_schemas,
    )


@router.post(
    "/{simulation_id}/hypotheses/wizard/clarify",
    response_model=WizardClarifyResponse,
    summary="Apply clarification responses to refine hypotheses",
    description="""
    Apply user's clarification responses to adjust hypothesis distributions.

    Takes qualitative responses ("more", "less", "equal", "dont_know") for
    critical variables and adjusts their distributions accordingly.

    Side effects:
    - Updates existing hypotheses in database
    """,
)
def clarify_wizard(
    simulation_id: str,
    request: WizardClarifyRequest,
    db: Session = Depends(get_db_session),
) -> WizardClarifyResponse:
    """
    Apply clarification responses to refine hypothesis distributions.

    Args:
        simulation_id: Simulation ID (format sim_XXXXXXXX)
        request: Wizard clarify request with clarification responses
        db: Database session

    Returns:
        WizardClarifyResponse with updated hypotheses

    Raises:
        HTTPException 404: If simulation or hypotheses not found
        HTTPException 400: If clarifications are invalid
        HTTPException 500: If update fails
    """
    logger.info(
        f"POST /simulations/{simulation_id}/hypotheses/wizard/clarify - "
        f"{len(request.responses)} responses"
    )

    # 1. Initialize wizard service
    wizard_service = HypothesisWizardService()

    # 2. Apply clarifications
    try:
        result = wizard_service.apply_clarifications(
            simulation_id=simulation_id,
            clarifications=[c.model_dump() for c in request.responses],
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to apply clarifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update hypotheses: {str(e)}",
        )

    # 3. Convert hypotheses to schemas
    hypotheses_schemas = [_hypothesis_to_schema(h) for h in result["hypotheses"]]

    return WizardClarifyResponse(hypotheses=hypotheses_schemas)
