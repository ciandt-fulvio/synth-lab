"""
Exploration API router for LLM-assisted scenario exploration.

REST endpoints for creating and managing scenario explorations,
including tree visualization and winning path retrieval.

References:
    - Spec: specs/024-llm-scenario-exploration/spec.md
    - API contract: specs/024-llm-scenario-exploration/contracts/exploration-api.yaml
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from loguru import logger

from synth_lab.api.schemas.exploration import (
    ActionCatalogResponse,
    ActionCategoryResponse,
    ActionExampleResponse,
    ExplorationCreate,
    ExplorationResponse,
    ExplorationTreeResponse,
    ImpactRangeResponse,
    PathStepResponse,
    WinningPathResponse,
    exploration_to_response,
    node_to_response,
)
from synth_lab.infrastructure.database import get_database
from synth_lab.repositories.synth_repository import SynthRepository
from synth_lab.services.exploration.action_catalog import get_action_catalog_service
from synth_lab.services.exploration.exploration_service import (
    ExperimentNotFoundError,
    ExplorationNotFoundError,
    ExplorationService,
    NoBaselineAnalysisError,
    NoScorecardError,
)

router = APIRouter()


# =============================================================================
# Helper Functions
# =============================================================================


def get_exploration_service() -> ExplorationService:
    """Get exploration service instance."""
    return ExplorationService()


# =============================================================================
# Exploration Endpoints
# =============================================================================


@router.post("", response_model=ExplorationResponse, status_code=status.HTTP_201_CREATED)
async def create_exploration(data: ExplorationCreate) -> ExplorationResponse:
    """
    Start a new scenario exploration from an experiment.

    Creates an exploration session with a root node based on the
    experiment's scorecard and baseline analysis.

    Args:
        data: Exploration creation parameters including experiment_id and goal.

    Returns:
        ExplorationResponse: The created exploration.

    Raises:
        404: Experiment not found.
        422: Experiment has no scorecard or no completed analysis.
    """
    service = get_exploration_service()
    try:
        exploration = service.start_exploration(
            experiment_id=data.experiment_id,
            goal_value=data.goal_value,
            beam_width=data.beam_width,
            max_depth=data.max_depth,
            max_llm_calls=data.max_llm_calls,
            n_executions=data.n_executions,
            seed=data.seed,
        )
        logger.info(f"Created exploration {exploration.id} for experiment {data.experiment_id}")
        return exploration_to_response(exploration)

    except ExperimentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {data.experiment_id} not found",
        )
    except NoScorecardError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Experiment {data.experiment_id} has no scorecard data",
        )
    except NoBaselineAnalysisError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Experiment {data.experiment_id} has no completed baseline analysis",
        )


@router.post("/{exploration_id}/run", response_model=ExplorationResponse)
async def run_exploration(
    exploration_id: str,
    background_tasks: BackgroundTasks,
) -> ExplorationResponse:
    """
    Run an exploration in the background.

    Triggers the exploration loop which will run until termination
    (goal achieved, limits reached, or no viable paths).

    Args:
        exploration_id: The exploration ID to run.

    Returns:
        ExplorationResponse: Current exploration state (will update in background).

    Raises:
        404: Exploration not found.
    """
    service = get_exploration_service()
    try:
        exploration = service.get_exploration(exploration_id)

        # Get synths for simulation (derives simulation_attributes from observables)
        db = get_database()
        synth_repo = SynthRepository(db)
        synth_dicts = synth_repo.get_synths_for_simulation(
            experiment_id=exploration.experiment_id,
            limit=200,
        )

        if not synth_dicts:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No synths found for this experiment's analysis",
            )

        # Run exploration in background
        async def run_exploration_task():
            try:
                await service.run_exploration(exploration_id, synth_dicts)
            except Exception as e:
                logger.error(f"Exploration {exploration_id} failed: {e}")

        background_tasks.add_task(run_exploration_task)
        logger.info(f"Started exploration {exploration_id} in background")

        return exploration_to_response(exploration)

    except ExplorationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exploration {exploration_id} not found",
        )


@router.get("/{exploration_id}", response_model=ExplorationResponse)
async def get_exploration(exploration_id: str) -> ExplorationResponse:
    """
    Get an exploration by ID.

    Args:
        exploration_id: The exploration ID.

    Returns:
        ExplorationResponse: The exploration data.

    Raises:
        404: Exploration not found.
    """
    service = get_exploration_service()
    try:
        exploration = service.get_exploration(exploration_id)
        return exploration_to_response(exploration)
    except ExplorationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exploration {exploration_id} not found",
        )


@router.get("/{exploration_id}/tree", response_model=ExplorationTreeResponse)
async def get_exploration_tree(exploration_id: str) -> ExplorationTreeResponse:
    """
    Get the complete exploration tree.

    Returns the exploration with all nodes and status counts.

    Args:
        exploration_id: The exploration ID.

    Returns:
        ExplorationTreeResponse: Complete tree structure.

    Raises:
        404: Exploration not found.
    """
    service = get_exploration_service()
    try:
        tree_data = service.get_exploration_tree(exploration_id)
        return ExplorationTreeResponse(
            exploration=exploration_to_response(tree_data["exploration"]),
            nodes=[node_to_response(node) for node in tree_data["nodes"]],
            node_count_by_status=tree_data["node_count_by_status"],
        )
    except ExplorationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exploration {exploration_id} not found",
        )


@router.get("/{exploration_id}/winning-path", response_model=WinningPathResponse | None)
async def get_winning_path(exploration_id: str) -> WinningPathResponse | None:
    """
    Get the path from root to winning node.

    Returns None if exploration hasn't achieved the goal.

    Args:
        exploration_id: The exploration ID.

    Returns:
        WinningPathResponse or None: Path info if winner exists.

    Raises:
        404: Exploration not found.
    """
    service = get_exploration_service()
    try:
        path_data = service.get_winning_path(exploration_id)
        if path_data is None:
            return None

        return WinningPathResponse(
            exploration_id=path_data["exploration_id"],
            winner_node_id=path_data["winner_node_id"],
            path=[
                PathStepResponse(
                    depth=step["depth"],
                    action=step["action"],
                    category=step["category"],
                    rationale=step["rationale"],
                    success_rate=step["success_rate"],
                    delta_success_rate=step["delta_success_rate"],
                )
                for step in path_data["path"]
            ],
            total_improvement=path_data["total_improvement"],
        )
    except ExplorationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exploration {exploration_id} not found",
        )


# =============================================================================
# Action Catalog Endpoints
# =============================================================================


@router.get("/catalog/actions", response_model=ActionCatalogResponse)
async def get_action_catalog() -> ActionCatalogResponse:
    """
    Get the complete action catalog.

    Returns all action categories with examples and typical impacts.

    Returns:
        ActionCatalogResponse: The action catalog.
    """
    catalog_service = get_action_catalog_service()
    catalog = catalog_service.get_catalog()

    return ActionCatalogResponse(
        version=catalog.version,
        categories=[
            ActionCategoryResponse(
                id=cat.id,
                name=cat.name,
                description=cat.description,
                examples=[
                    ActionExampleResponse(
                        action=example.action,
                        typical_impacts={
                            k: ImpactRangeResponse(min=v.min, max=v.max)
                            for k, v in example.typical_impacts.items()
                        },
                    )
                    for example in cat.examples
                ],
            )
            for cat in catalog.categories
        ],
    )


if __name__ == "__main__":
    import sys
    import tempfile
    from pathlib import Path

    from synth_lab.domain.entities.analysis_run import AggregatedOutcomes, AnalysisRun
    from synth_lab.domain.entities.experiment import (
        Experiment,
        ScorecardData,
        ScorecardDimension,
    )
    from synth_lab.infrastructure.database import DatabaseManager, init_database
    from synth_lab.repositories.analysis_repository import AnalysisRepository
    from synth_lab.repositories.experiment_repository import ExperimentRepository
    from synth_lab.repositories.exploration_repository import ExplorationRepository
    from synth_lab.services.exploration.exploration_service import ExplorationService
    from synth_lab.services.exploration.tree_manager import TreeManager

    all_validation_failures = []
    total_tests = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test.db"
        init_database(test_db_path)
        db = DatabaseManager(test_db_path)

        experiment_repo = ExperimentRepository(db)
        analysis_repo = AnalysisRepository(db)
        exploration_repo = ExplorationRepository(db)
        tree_manager = TreeManager(exploration_repo)

        service = ExplorationService(
            exploration_repo=exploration_repo,
            experiment_repo=experiment_repo,
            analysis_repo=analysis_repo,
            tree_manager=tree_manager,
        )

        # Create test experiment with scorecard
        experiment = Experiment(
            name="Test Experiment",
            hypothesis="Test hypothesis",
            scorecard_data=ScorecardData(
                feature_name="Test Feature",
                description_text="Test description",
                complexity=ScorecardDimension(score=0.45),
                initial_effort=ScorecardDimension(score=0.30),
                perceived_risk=ScorecardDimension(score=0.25),
                time_to_value=ScorecardDimension(score=0.40),
            ),
        )
        experiment_repo.create(experiment)

        # Create analysis
        analysis = AnalysisRun(
            experiment_id=experiment.id,
            status="completed",
            aggregated_outcomes=AggregatedOutcomes(
                success_rate=0.25,
                failed_rate=0.45,
                did_not_try_rate=0.30,
            ),
        )
        analysis_repo.create(analysis)

        # Test 1: exploration_to_response conversion
        total_tests += 1
        try:
            exploration = service.start_exploration(
                experiment_id=experiment.id,
                goal_value=0.40,
            )
            response = exploration_to_response(exploration)
            if response.id != exploration.id:
                all_validation_failures.append(f"ID mismatch: {response.id}")
            if response.experiment_id != experiment.id:
                all_validation_failures.append(f"Experiment ID mismatch: {response.experiment_id}")
            if response.goal.value != 0.40:
                all_validation_failures.append(f"Goal value mismatch: {response.goal.value}")
        except Exception as e:
            all_validation_failures.append(f"exploration_to_response failed: {e}")

        # Test 2: node_to_response conversion
        total_tests += 1
        try:
            tree_data = service.get_exploration_tree(exploration.id)
            nodes = tree_data["nodes"]
            if len(nodes) != 1:
                all_validation_failures.append(f"Should have 1 node: {len(nodes)}")
            node_response = node_to_response(nodes[0])
            if node_response.depth != 0:
                all_validation_failures.append(f"Root depth should be 0: {node_response.depth}")
            if node_response.simulation_results is None:
                all_validation_failures.append("Root should have simulation results")
        except Exception as e:
            all_validation_failures.append(f"node_to_response failed: {e}")

        # Test 3: Action catalog response
        total_tests += 1
        try:
            catalog_service = get_action_catalog_service()
            catalog = catalog_service.get_catalog()
            if len(catalog.categories) != 5:
                all_validation_failures.append(f"Should have 5 categories: {len(catalog.categories)}")
        except Exception as e:
            all_validation_failures.append(f"Action catalog failed: {e}")

        db.close()

    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
