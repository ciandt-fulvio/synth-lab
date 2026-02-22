"""
Quantitative analysis API router.

REST endpoints for causal model generation, edge selection, and simulation.

References:
    - Contracts: specs/042-quantitative-analysis/contracts/api.md
    - Spec: specs/042-quantitative-analysis/spec.md
"""

from fastapi import APIRouter, HTTPException, status

from synth_lab.api.schemas.quantitative_analysis import (
    CausalModelResponse,
    EdgeUpdateRequest,
    EdgeUpdateResponse,
    MultiScenarioRequest,
    MultiScenarioResponse,
    NodeSelectionsRequest,
    NodeSelectionsResponse,
    ProductCalibrationRequest,
    ProductCalibrationResponse,
    SimulationRunResponse,
)
from synth_lab.services.quantitative_analysis_service import (
    QuantitativeAnalysisService,
)

router = APIRouter()


def get_service() -> QuantitativeAnalysisService:
    """Get quantitative analysis service instance."""
    return QuantitativeAnalysisService()


@router.post("/generate", response_model=CausalModelResponse, status_code=status.HTTP_201_CREATED)
async def generate_causal_model(experiment_id: str) -> CausalModelResponse:
    """Generate a causal DAG for an experiment via LLM (gpt-5.1).

    Deletes any existing model for this experiment and generates a new one.
    All selected_option values start as null.
    """
    service = get_service()
    try:
        result = service.generate_causal_model(experiment_id)
        return CausalModelResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get("/model", response_model=CausalModelResponse)
async def get_causal_model(experiment_id: str) -> CausalModelResponse:
    """Get the current causal model for an experiment with edge selections."""
    service = get_service()
    result = service.get_causal_model(experiment_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No causal model for experiment: {experiment_id}",
        )
    return CausalModelResponse(**result)


@router.patch("/edges", response_model=EdgeUpdateResponse)
async def update_edge_selections(
    experiment_id: str,
    request: EdgeUpdateRequest,
) -> EdgeUpdateResponse:
    """Update PM's Likert selections for causal model edges.

    Accepts partial updates — only specified edges are modified.
    """
    service = get_service()
    try:
        result = service.update_edge_selections(experiment_id, request.selections)
        return EdgeUpdateResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/node-selections", response_model=NodeSelectionsResponse)
async def update_node_selections(
    experiment_id: str,
    request: NodeSelectionsRequest,
) -> NodeSelectionsResponse:
    """Update PM's premissa selections for interaction/outcome nodes.

    Accepts partial updates — only specified nodes are modified.
    """
    service = get_service()
    try:
        result = service.update_node_selections(experiment_id, request.selections)
        return NodeSelectionsResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/product-calibration", response_model=ProductCalibrationResponse)
async def update_product_calibration(
    experiment_id: str,
    request: ProductCalibrationRequest,
) -> ProductCalibrationResponse:
    """Update product node calibrations (low/medium/high).

    Accepts partial updates — only specified product nodes are modified.
    """
    service = get_service()
    try:
        result = service.update_product_calibrations(experiment_id, request.calibrations)
        return ProductCalibrationResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/simulate", response_model=SimulationRunResponse, status_code=status.HTTP_201_CREATED)
async def run_simulation(experiment_id: str) -> SimulationRunResponse:
    """Run Monte Carlo simulation with current edge selections.

    Returns full results including stats, segments, sensitivity, and AI interpretations.
    """
    service = get_service()
    try:
        result = service.run_simulation(experiment_id)
        return SimulationRunResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except TimeoutError as e:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(e)) from e


@router.post("/generate-interview-guide", status_code=status.HTTP_201_CREATED)
async def generate_interview_guide(experiment_id: str) -> dict:
    """Generate interview guide from the latest simulation sensitivity results.

    Uses the top sensitivity premisses to create a focused interview guide.
    Overwrites any existing guide for this experiment.
    """
    service = get_service()
    try:
        result = service.generate_interview_guide(experiment_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.post("/generate-simulation-summary", status_code=status.HTTP_201_CREATED)
async def generate_simulation_summary(experiment_id: str) -> dict:
    """Generate or regenerate the simulation summary report.

    Creates a rich markdown document combining simulation results,
    interpretations, demographics, and interview suggestions.
    """
    service = get_service()
    try:
        result = service.generate_simulation_summary(experiment_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get("/results", response_model=SimulationRunResponse)
async def get_simulation_results(experiment_id: str) -> SimulationRunResponse:
    """Get results from the latest simulation run."""
    service = get_service()
    result = service.get_simulation_results(experiment_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No simulation results for experiment: {experiment_id}",
        )
    return SimulationRunResponse(**result)


# =============================================================================
# Multi-Scenario Endpoints
# =============================================================================


@router.post(
    "/simulate-scenarios",
    response_model=MultiScenarioResponse,
    status_code=status.HTTP_201_CREATED,
)
async def run_multi_scenario_simulation(
    experiment_id: str,
    request: MultiScenarioRequest | None = None,
) -> MultiScenarioResponse:
    """Run multi-scenario simulation batch with per-synth results.

    If called without body (or with scenarios=null), auto-generates random
    scenarios by sampling {low, medium, high} for each product node.
    """
    service = get_service()
    try:
        scenarios = None
        n_scenarios = None
        n_repetitions = 10
        if request:
            scenarios = [s.calibrations for s in request.scenarios] if request.scenarios else None
            n_scenarios = request.n_scenarios
            n_repetitions = request.n_repetitions
        result = service.run_multi_scenario_simulation(
            experiment_id, scenarios, n_scenarios, n_repetitions,
        )
        return MultiScenarioResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/scenario-batch/{batch_id}", response_model=MultiScenarioResponse)
async def get_scenario_batch(
    experiment_id: str,
    batch_id: str,
) -> MultiScenarioResponse:
    """Get batch results (aggregate per scenario)."""
    service = get_service()
    batch = service.simulation_run_repo.get_batch_by_id(batch_id)
    if batch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch not found: {batch_id}",
        )
    scenarios = []
    for run in batch.runs:
        scenarios.append({
            "run_id": run.id,
            "product_values": run.product_values or {},
            "stats": run.stats,
            "n_synths": run.n_synths,
        })
    return MultiScenarioResponse(
        batch_id=batch.id,
        experiment_id=batch.experiment_id,
        n_scenarios=batch.n_scenarios,
        n_synths=batch.n_synths,
        n_repetitions=batch.n_repetitions,
        status=batch.status,
        scenarios=scenarios,
    )



if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Router has expected routes
    total_tests += 1
    try:
        route_paths = [r.path for r in router.routes]
        expected = [
            "/generate",
            "/model",
            "/edges",
            "/simulate",
            "/generate-interview-guide",
            "/generate-simulation-summary",
            "/results",
        ]
        for path in expected:
            if path not in route_paths:
                all_validation_failures.append(f"Missing route: {path}")
    except Exception as e:
        all_validation_failures.append(f"Route check failed: {e}")

    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
