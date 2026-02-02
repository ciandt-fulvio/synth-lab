"""
Simulations API router for causal simulation system.

REST endpoints for creating and running causal simulations.

References:
    - Spec: specs/035-causal-simulation/spec.md
    - Data model: specs/035-causal-simulation/data-model.md
"""

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.orm import Session

from synth_lab.api.schemas.simulation import (
    ConfirmDAGRequest,
    ConfirmDAGResponse,
    ProblemDecompositionUpdate,
    SimulationCreate,
    SimulationResponse,
    SimulationRunRequest,
    SimulationRunResponse,
)
from synth_lab.domain.entities.simulation import Simulation, SimulationStatus
from synth_lab.infrastructure.database_v2 import get_db_session
from synth_lab.repositories.causal_dag_repository import CausalDAGRepository
from synth_lab.repositories.hypothesis_repository import HypothesisRepository
from synth_lab.repositories.simulation_insight_repository import (
    SimulationInsightRepository,
)
from synth_lab.repositories.simulation_repository import SimulationRepository
from synth_lab.services.simulation.dag_constructor_service import (
    DAGConstructorService,
)
from synth_lab.services.simulation.evidence_calculator_service import (
    EvidenceCalculatorService,
)
from synth_lab.services.simulation.hypothesis_parametrizer_service import (
    HypothesisParametrizerService,
)
from synth_lab.services.simulation.insight_generator_service import (
    InsightGeneratorService,
)
from synth_lab.services.simulation.question_parser_service import (
    QuestionParserService,
)
from synth_lab.services.simulation.simulation_engine_service import (
    SimulationEngineService,
)

router = APIRouter(prefix="/simulations", tags=["simulations"])


# =============================================================================
# Endpoints
# =============================================================================


@router.post(
    "",
    response_model=SimulationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create simulation from question",
    description="Parse question and wait for validation before generating DAG",
)
async def create_simulation(
    request: SimulationCreate,
    db: Session = Depends(get_db_session),
) -> SimulationResponse:
    """
    Create a new causal simulation from a natural language question.

    This endpoint:
    1. Parses the question into structured problem decomposition
    2. Returns simulation in AWAITING_QUESTION_VALIDATION status
    3. User must call confirm-question to proceed to DAG generation

    Args:
        request: Question text and optional parameters
        db: Database session

    Returns:
        Created simulation with ID and problem decomposition

    Raises:
        HTTPException: If question parsing fails
    """
    try:
        # Initialize services
        parser_service = QuestionParserService()

        # Initialize repositories
        sim_repo = SimulationRepository(session=db)

        # Step 1: Parse question
        logger.info(f"Parsing question: {request.question_text[:100]}")
        problem = parser_service.parse(request.question_text)

        # Step 2: Create simulation entity in awaiting validation status
        simulation = Simulation(
            question_text=request.question_text,
            problem_decomposition=problem,
            status=SimulationStatus.AWAITING_QUESTION_VALIDATION,
            random_seed=request.random_seed,
            n_worlds=request.n_worlds,
        )

        # Step 3: Persist simulation
        simulation = sim_repo.create(simulation)
        logger.info(f"Created simulation: {simulation.id} - awaiting question validation")

        return SimulationResponse(
            id=simulation.id,
            question_text=simulation.question_text,
            problem_decomposition=simulation.problem_decomposition,
            status=simulation.status,
            random_seed=simulation.random_seed,
            n_worlds=simulation.n_worlds,
            created_at=simulation.created_at,
        )

    except ValueError as e:
        logger.error(f"Simulation creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        import traceback

        logger.error(f"Unexpected error creating simulation: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create simulation",
        )


@router.get(
    "/{simulation_id}",
    response_model=SimulationResponse,
    summary="Get simulation by ID",
    description="Retrieve simulation details including status and metadata",
)
async def get_simulation(
    simulation_id: str,
    db: Session = Depends(get_db_session),
) -> SimulationResponse:
    """
    Get simulation by ID.

    Args:
        simulation_id: Simulation ID
        db: Database session

    Returns:
        Simulation details

    Raises:
        HTTPException: If simulation not found
    """
    sim_repo = SimulationRepository(session=db)
    simulation = sim_repo.get(simulation_id)

    if simulation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation {simulation_id} not found",
        )

    return SimulationResponse(
        id=simulation.id,
        question_text=simulation.question_text,
        problem_decomposition=simulation.problem_decomposition,
        status=simulation.status,
        random_seed=simulation.random_seed,
        n_worlds=simulation.n_worlds,
        created_at=simulation.created_at,
    )


@router.get(
    "",
    response_model=list[SimulationResponse],
    summary="List simulations",
    description="List all simulations with optional status filter",
)
async def list_simulations(
    status: str | None = None,
    limit: int = 100,
    db: Session = Depends(get_db_session),
) -> list[SimulationResponse]:
    """
    List simulations with optional filtering.

    Args:
        status: Filter by status (optional)
        limit: Maximum number of results
        db: Database session

    Returns:
        List of simulations
    """
    sim_repo = SimulationRepository(session=db)

    # Convert status string to enum if provided
    status_filter = None
    if status:
        try:
            status_filter = SimulationStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}",
            )

    simulations = sim_repo.list(status=status_filter, limit=limit)

    return [
        SimulationResponse(
            id=sim.id,
            question_text=sim.question_text,
            problem_decomposition=sim.problem_decomposition,
            status=sim.status,
            random_seed=sim.random_seed,
            n_worlds=sim.n_worlds,
            created_at=sim.created_at,
        )
        for sim in simulations
    ]


@router.delete(
    "/{simulation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete simulation",
    description="Delete simulation and all associated data (DAG, hypotheses, worlds, insights)",
)
async def delete_simulation(
    simulation_id: str,
    db: Session = Depends(get_db_session),
) -> None:
    """
    Delete simulation by ID.

    Args:
        simulation_id: Simulation ID
        db: Database session

    Raises:
        HTTPException: If simulation not found
    """
    sim_repo = SimulationRepository(session=db)
    deleted = sim_repo.delete(simulation_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation {simulation_id} not found",
        )


# =============================================================================
# Wizard Flow Endpoints (Confirm Steps)
# =============================================================================


@router.put(
    "/{simulation_id}/problem-decomposition",
    response_model=SimulationResponse,
    summary="Update problem decomposition",
    description="Edit the structured problem decomposition before confirmation",
)
async def update_problem_decomposition(
    simulation_id: str,
    request: ProblemDecompositionUpdate,
    db: Session = Depends(get_db_session),
) -> SimulationResponse:
    """
    Update problem decomposition fields.

    Can only be called when simulation is in AWAITING_QUESTION_VALIDATION status.

    Args:
        simulation_id: Simulation ID
        request: Fields to update
        db: Database session

    Returns:
        Updated simulation

    Raises:
        HTTPException: If simulation not found or wrong status
    """
    sim_repo = SimulationRepository(session=db)
    simulation = sim_repo.get(simulation_id)

    if simulation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation {simulation_id} not found",
        )

    if simulation.status != SimulationStatus.AWAITING_QUESTION_VALIDATION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update problem decomposition when status is {simulation.status}",
        )

    # Update fields that were provided
    if simulation.problem_decomposition:
        from synth_lab.domain.entities.simulation import ProblemDecomposition

        current = simulation.problem_decomposition
        updated_data = current.model_dump()

        if request.intervention is not None:
            updated_data["intervention"] = request.intervention
        if request.primary_outcome is not None:
            updated_data["primary_outcome"] = request.primary_outcome
        if request.secondary_outcomes is not None:
            updated_data["secondary_outcomes"] = request.secondary_outcomes
        if request.unit_of_analysis is not None:
            updated_data["unit_of_analysis"] = request.unit_of_analysis
        if request.time_horizon is not None:
            updated_data["time_horizon"] = request.time_horizon
        if request.decision_type is not None:
            updated_data["decision_type"] = request.decision_type

        simulation.problem_decomposition = ProblemDecomposition(**updated_data)
        simulation = sim_repo.update(simulation)

    return SimulationResponse(
        id=simulation.id,
        question_text=simulation.question_text,
        problem_decomposition=simulation.problem_decomposition,
        status=simulation.status,
        random_seed=simulation.random_seed,
        n_worlds=simulation.n_worlds,
        created_at=simulation.created_at,
    )


@router.post(
    "/{simulation_id}/confirm-question",
    response_model=SimulationResponse,
    summary="Confirm question and generate DAG",
    description="Confirm the problem decomposition and proceed to generate causal DAG",
)
async def confirm_question(
    simulation_id: str,
    db: Session = Depends(get_db_session),
) -> SimulationResponse:
    """
    Confirm question validation and generate DAG.

    Args:
        simulation_id: Simulation ID
        db: Database session

    Returns:
        Simulation with updated status (awaiting_dag_validation)

    Raises:
        HTTPException: If simulation not found, wrong status, or DAG generation fails
    """
    try:
        sim_repo = SimulationRepository(session=db)
        dag_repo = CausalDAGRepository(session=db)

        simulation = sim_repo.get(simulation_id)

        if simulation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Simulation {simulation_id} not found",
            )

        if simulation.status != SimulationStatus.AWAITING_QUESTION_VALIDATION:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot confirm question when status is {simulation.status}",
            )

        # Update status to DAG construction
        simulation.status = SimulationStatus.DAG_CONSTRUCTION
        simulation = sim_repo.update(simulation)

        # Generate DAG + hypotheses in single unified LLM call
        dag_service = DAGConstructorService()
        hyp_repo = HypothesisRepository(session=db)
        dag, hypotheses = dag_service.generate(simulation.id, simulation.problem_decomposition)
        dag = dag_repo.create(dag)
        logger.info(f"Generated DAG with {len(dag.nodes)} variables")

        # Persist hypotheses
        if hypotheses:
            hyp_repo.create_batch(hypotheses)
            logger.info(f"Persisted {len(hypotheses)} hypotheses")

        # Update status to awaiting DAG validation
        simulation.status = SimulationStatus.AWAITING_DAG_VALIDATION
        simulation = sim_repo.update(simulation)

        return SimulationResponse(
            id=simulation.id,
            question_text=simulation.question_text,
            problem_decomposition=simulation.problem_decomposition,
            status=simulation.status,
            random_seed=simulation.random_seed,
            n_worlds=simulation.n_worlds,
            created_at=simulation.created_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DAG generation failed: {e}")
        # Update status to failed
        try:
            simulation.status = SimulationStatus.FAILED
            simulation.error_message = str(e)
            sim_repo.update(simulation)
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DAG generation failed: {str(e)}",
        )


@router.post(
    "/{simulation_id}/confirm-dag",
    response_model=ConfirmDAGResponse,
    summary="Confirm DAG and generate hypotheses",
    description="Confirm the causal DAG and proceed to generate hypothesis parameters",
)
async def confirm_dag(
    simulation_id: str,
    request: ConfirmDAGRequest | None = None,
    db: Session = Depends(get_db_session),
) -> ConfirmDAGResponse:
    """
    Confirm DAG validation and generate hypotheses.

    If scenario_profile is provided, uses HypothesisWizardService for profile-aware
    generation with clarification questions. Otherwise uses standard parametrizer.

    Args:
        simulation_id: Simulation ID
        request: Optional request with scenario_profile
        db: Database session

    Returns:
        Simulation with updated status and optional clarification questions

    Raises:
        HTTPException: If simulation not found, wrong status, or hypothesis generation fails
    """
    try:
        sim_repo = SimulationRepository(session=db)
        dag_repo = CausalDAGRepository(session=db)
        hyp_repo = HypothesisRepository(session=db)

        simulation = sim_repo.get(simulation_id)

        if simulation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Simulation {simulation_id} not found",
            )

        if simulation.status != SimulationStatus.AWAITING_DAG_VALIDATION:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot confirm DAG when status is {simulation.status}",
            )

        # Load DAG
        dag = dag_repo.get_by_simulation_id(simulation_id)
        if dag is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No DAG found for simulation",
            )

        # Update status to hypothesis generation
        simulation.status = SimulationStatus.HYPOTHESIS_GENERATION
        simulation = sim_repo.update(simulation)

        clarification_questions = []
        scenario_profile = request.scenario_profile if request else None

        if scenario_profile:
            # Use wizard service with scenario profile
            from synth_lab.domain.entities.hypothesis import ScenarioProfile
            from synth_lab.services.simulation.hypothesis_wizard_service import (
                HypothesisWizardService,
            )

            profile_enum = ScenarioProfile(scenario_profile)
            wizard_service = HypothesisWizardService(repository=hyp_repo)
            result = wizard_service.init_wizard(simulation.id, dag, profile_enum)
            n_hyps = len(result["hypotheses"])
            logger.info(f"Wizard generated {n_hyps} hypotheses with profile {scenario_profile}")
            clarification_questions = result.get("clarification_questions", [])
        else:
            # Standard parametrizer (backward compatible)
            hypothesis_service = HypothesisParametrizerService()
            hypotheses = hypothesis_service.quantify(simulation.id, dag)
            hypotheses = hyp_repo.create_batch(hypotheses)
            logger.info(f"Quantified {len(hypotheses)} hypotheses")

        # Update status to awaiting hypothesis validation
        simulation.status = SimulationStatus.AWAITING_HYPOTHESIS_VALIDATION
        simulation = sim_repo.update(simulation)

        return ConfirmDAGResponse(
            id=simulation.id,
            question_text=simulation.question_text,
            problem_decomposition=simulation.problem_decomposition,
            status=simulation.status,
            random_seed=simulation.random_seed,
            n_worlds=simulation.n_worlds,
            created_at=simulation.created_at,
            clarification_questions=[
                {
                    "variable_name": q["variable_name"],
                    "question_text": q["question_text"],
                    "criticality_score": q["criticality_score"],
                }
                for q in clarification_questions
            ],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Hypothesis generation failed: {e}")
        # Update status to failed
        try:
            simulation.status = SimulationStatus.FAILED
            simulation.error_message = str(e)
            sim_repo.update(simulation)
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hypothesis generation failed: {str(e)}",
        )


@router.post(
    "/{simulation_id}/confirm-hypotheses",
    response_model=SimulationResponse,
    summary="Confirm hypotheses and mark ready to run",
    description="Confirm the hypothesis parameters and mark simulation as ready to run",
)
async def confirm_hypotheses(
    simulation_id: str,
    db: Session = Depends(get_db_session),
) -> SimulationResponse:
    """
    Confirm hypotheses and mark simulation as ready to run.

    Args:
        simulation_id: Simulation ID
        db: Database session

    Returns:
        Simulation with updated status (ready_to_run)

    Raises:
        HTTPException: If simulation not found or wrong status
    """
    sim_repo = SimulationRepository(session=db)
    hyp_repo = HypothesisRepository(session=db)

    simulation = sim_repo.get(simulation_id)

    if simulation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation {simulation_id} not found",
        )

    if simulation.status != SimulationStatus.AWAITING_HYPOTHESIS_VALIDATION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot confirm hypotheses when status is {simulation.status}",
        )

    # Verify hypotheses exist
    hypotheses = hyp_repo.get_by_simulation_id(simulation_id)
    if not hypotheses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hypotheses found for simulation",
        )

    # Update status to ready to run
    simulation.status = SimulationStatus.READY_TO_RUN
    simulation = sim_repo.update(simulation)

    return SimulationResponse(
        id=simulation.id,
        question_text=simulation.question_text,
        problem_decomposition=simulation.problem_decomposition,
        status=simulation.status,
        random_seed=simulation.random_seed,
        n_worlds=simulation.n_worlds,
        created_at=simulation.created_at,
    )


@router.post(
    "/{simulation_id}/run",
    response_model=SimulationRunResponse,
    summary="Run simulation",
    description="Execute Monte Carlo simulation across N synthetic worlds",
)
async def run_simulation(
    simulation_id: str,
    request: SimulationRunRequest | None = None,
    db: Session = Depends(get_db_session),
) -> SimulationRunResponse:
    """
    Run simulation to generate synthetic worlds and insights.

    This endpoint:
    1. Loads DAG and hypotheses
    2. Runs simulation engine (500 worlds)
    3. Calculates evidence (percentiles, sensitivity, failures, clusters)
    4. Generates insights with LLM
    5. Persists all results

    Args:
        simulation_id: Simulation ID
        request: Optional run parameters
        db: Database session

    Returns:
        Run results summary

    Raises:
        HTTPException: If simulation not found or run fails
    """
    try:
        # Initialize repositories
        sim_repo = SimulationRepository(session=db)
        dag_repo = CausalDAGRepository(session=db)
        hyp_repo = HypothesisRepository(session=db)
        insight_repo = SimulationInsightRepository(session=db)

        # Load simulation
        simulation = sim_repo.get(simulation_id)
        if simulation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Simulation {simulation_id} not found",
            )

        # Validate simulation is ready to run
        if simulation.status != SimulationStatus.READY_TO_RUN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot run simulation when status is {simulation.status}. "
                f"Simulation must be in 'ready_to_run' status.",
            )

        # Update status
        simulation.status = SimulationStatus.SIMULATING
        simulation = sim_repo.update(simulation)

        # Load DAG and hypotheses
        dag = dag_repo.get_by_simulation_id(simulation_id)
        if dag is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No DAG found for simulation",
            )

        hypotheses = hyp_repo.get_by_simulation_id(simulation_id)
        if not hypotheses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hypotheses found for simulation",
            )

        logger.info(f"Running simulation {simulation_id} with {len(hypotheses)} hypotheses")

        # Run simulation
        engine = SimulationEngineService()
        worlds = engine.run(
            simulation_id=simulation_id,
            dag=dag,
            hypotheses=hypotheses,
            n_worlds=simulation.n_worlds or 500,
            random_seed=simulation.random_seed or 42,
        )

        # Calculate evidence
        evidence_service = EvidenceCalculatorService()
        evidence, failure_modes, clusters = evidence_service.aggregate(simulation_id, dag, worlds)

        # Generate insights
        insight_service = InsightGeneratorService()
        insights = insight_service.synthesize(simulation_id, dag, evidence, failure_modes, clusters)

        # Persist insights
        insights = insight_repo.create_batch(insights)

        # Update status
        simulation.status = SimulationStatus.COMPLETED
        simulation = sim_repo.update(simulation)

        logger.info(
            f"Simulation {simulation_id} completed: {len(worlds)} worlds, {len(insights)} insights"
        )

        return SimulationRunResponse(
            simulation_id=simulation_id,
            status="completed",
            n_worlds=len(worlds),
            n_insights=len(insights),
            outcome_distributions=evidence.outcome_distributions,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Simulation run failed: {e}")
        # Update status to failed
        try:
            simulation.status = SimulationStatus.FAILED
            sim_repo.update(simulation)
        except Exception:
            pass

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation run failed: {str(e)}",
        )


# =============================================================================
# Audit Trail Endpoints
# =============================================================================


class AuditTrailResponse(BaseModel):
    """Response schema for audit trail."""

    id: str
    simulation_id: str
    question: str
    random_seed: int
    n_worlds: int
    dag_version: int
    n_hypotheses: int
    n_failure_modes: int
    n_clusters: int
    n_insights: int
    created_at: str


class ReplayResponse(BaseModel):
    """Response schema for simulation replay."""

    simulation_id: str
    status: str
    n_worlds: int
    message: str


class ExportResponse(BaseModel):
    """Response schema for audit export."""

    audit_id: str
    simulation_id: str
    export_package: dict


@router.get(
    "/{simulation_id}/audit",
    response_model=AuditTrailResponse,
    summary="Get audit trail",
    description="Retrieve the audit trail for a simulation",
)
async def get_simulation_audit(
    simulation_id: str,
    db: Session = Depends(get_db_session),
) -> AuditTrailResponse:
    """
    Get audit trail for a simulation.

    Args:
        simulation_id: Simulation ID
        db: Database session

    Returns:
        Audit trail details

    Raises:
        HTTPException: If simulation or audit trail not found
    """
    from synth_lab.repositories.audit_trail_repository import AuditTrailRepository

    audit_repo = AuditTrailRepository(session=db)
    audit = audit_repo.get_by_simulation_id(simulation_id)

    if audit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No audit trail found for simulation {simulation_id}",
        )

    return AuditTrailResponse(
        id=audit.id,
        simulation_id=audit.simulation_id,
        question=audit.question,
        random_seed=audit.random_seed,
        n_worlds=audit.n_worlds,
        dag_version=audit.dag_snapshot.version,
        n_hypotheses=len(audit.hypotheses_snapshot),
        n_failure_modes=audit.evidence_snapshot.n_failure_modes,
        n_clusters=audit.evidence_snapshot.n_clusters,
        n_insights=len(audit.insights_snapshot),
        created_at=audit.created_at.isoformat(),
    )


@router.post(
    "/{simulation_id}/replay",
    response_model=ReplayResponse,
    summary="Replay simulation",
    description="Replay a simulation using stored audit trail for deterministic reproduction",
)
async def replay_simulation(
    simulation_id: str,
    db: Session = Depends(get_db_session),
) -> ReplayResponse:
    """
    Replay a simulation using stored audit trail.

    This reproduces identical results using the same seed and parameters.

    Args:
        simulation_id: Simulation ID
        db: Database session

    Returns:
        Replay results

    Raises:
        HTTPException: If simulation or audit trail not found
    """
    from synth_lab.repositories.audit_trail_repository import AuditTrailRepository
    from synth_lab.services.simulation.audit_trail_service import AuditTrailService

    audit_repo = AuditTrailRepository(session=db)
    audit_service = AuditTrailService(audit_repo=audit_repo)

    # Check audit trail exists
    audit = audit_repo.get_by_simulation_id(simulation_id)
    if audit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No audit trail found for simulation {simulation_id}",
        )

    try:
        # Replay simulation
        engine = SimulationEngineService()
        evidence_service = EvidenceCalculatorService()

        result = audit_service.replay(
            simulation_id=simulation_id,
            simulation_engine=engine,
            evidence_calculator=evidence_service,
        )

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Replay failed",
            )

        evidence, failure_modes, clusters = result

        return ReplayResponse(
            simulation_id=simulation_id,
            status="completed",
            n_worlds=audit.n_worlds,
            message=(
                f"Replay completed with {len(failure_modes)} failure modes, "
                f"{len(clusters)} clusters"
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Replay failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Replay failed: {str(e)}",
        )


@router.get(
    "/{simulation_id}/audit/export",
    response_model=ExportResponse,
    summary="Export audit trail",
    description="Export full audit trail as a portable JSON package",
)
async def export_simulation_audit(
    simulation_id: str,
    db: Session = Depends(get_db_session),
) -> ExportResponse:
    """
    Export audit trail as a portable package.

    Args:
        simulation_id: Simulation ID
        db: Database session

    Returns:
        Export package with complete audit data

    Raises:
        HTTPException: If simulation or audit trail not found
    """
    from synth_lab.repositories.audit_trail_repository import AuditTrailRepository
    from synth_lab.services.simulation.audit_trail_service import AuditTrailService

    audit_repo = AuditTrailRepository(session=db)
    audit_service = AuditTrailService(audit_repo=audit_repo)

    audit = audit_repo.get_by_simulation_id(simulation_id)
    if audit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No audit trail found for simulation {simulation_id}",
        )

    export_package = audit_service.export_audit(audit.id)
    if export_package is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Export failed",
        )

    return ExportResponse(
        audit_id=audit.id,
        simulation_id=simulation_id,
        export_package=export_package,
    )
