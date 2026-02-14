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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


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


@router.post("/simulate", response_model=SimulationRunResponse, status_code=status.HTTP_201_CREATED)
async def run_simulation(experiment_id: str) -> SimulationRunResponse:
    """Run Monte Carlo simulation with current edge selections.

    Returns full results including stats, segments, sensitivity, and AI interpretations.
    Generates interview_guide automatically after simulation.
    """
    service = get_service()
    try:
        result = service.run_simulation(experiment_id)
        return SimulationRunResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except TimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(e)
        ) from e


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


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Router has expected routes
    total_tests += 1
    try:
        route_paths = [r.path for r in router.routes]
        expected = ["/generate", "/model", "/edges", "/simulate", "/results"]
        for path in expected:
            if path not in route_paths:
                all_validation_failures.append(f"Missing route: {path}")
    except Exception as e:
        all_validation_failures.append(f"Route check failed: {e}")

    if all_validation_failures:
        print(
            f"VALIDATION FAILED - {len(all_validation_failures)} of "
            f"{total_tests} tests failed:"
        )
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(
            f"VALIDATION PASSED - All {total_tests} tests produced expected results"
        )
        sys.exit(0)
