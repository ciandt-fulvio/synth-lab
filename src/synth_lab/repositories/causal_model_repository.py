"""
Repository for causal model data access.

Handles CRUD operations for causal models and their edges.
Uses SQLAlchemy ORM for database operations.

References:
    - Data model: specs/042-quantitative-analysis/data-model.md
    - ORM models: synth_lab.models.orm.causal_model

Sample input:
    repo = CausalModelRepository(session=db_session)
    model = repo.get_by_experiment("exp_12345678")

Expected output:
    CausalModelORM instance with edges loaded, or None if not found.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from synth_lab.models.orm.causal_model import CausalEdge as CausalEdgeORM
from synth_lab.models.orm.causal_model import CausalModel as CausalModelORM
from synth_lab.repositories.base import BaseRepository


class CausalModelRepository(BaseRepository):
    """Repository for causal model data access.

    Usage:
        repo = CausalModelRepository(session=session)
        model = repo.get_by_experiment("exp_12345678")
    """

    def __init__(self, session: Session | None = None):
        super().__init__(session=session)

    def create_with_edges(
        self,
        model_id: str,
        experiment_id: str,
        label: str,
        intercept_mu: float,
        intercept_sigma: float,
        nodes: list,
        edges: list[dict],
        raw_llm_response: dict | None = None,
        node_metadata: dict | None = None,
    ) -> CausalModelORM:
        """
        Create a causal model with its edges in a single transaction.

        Args:
            model_id: Unique model ID (cm_xxx).
            experiment_id: Parent experiment ID.
            label: Model title from LLM.
            intercept_mu: Intercept mean.
            intercept_sigma: Intercept std dev.
            nodes: List of node names.
            edges: List of edge dicts with keys matching CausalEdge columns.
            raw_llm_response: Optional raw LLM response for debugging.
            node_metadata: Optional per-node metadata dict.

        Returns:
            Created CausalModelORM instance.
        """
        orm_model = CausalModelORM(
            id=model_id,
            experiment_id=experiment_id,
            label=label,
            intercept_mu=intercept_mu,
            intercept_sigma=intercept_sigma,
            nodes=nodes,
            node_metadata=node_metadata,
            raw_llm_response=raw_llm_response,
        )
        self._add(orm_model)
        self._flush()

        for edge_data in edges:
            orm_edge = CausalEdgeORM(
                id=edge_data["id"],
                causal_model_id=model_id,
                from_node=edge_data["from_node"],
                to_node=edge_data["to_node"],
                user_var=edge_data.get("user_var"),
                direction=edge_data["direction"],
                header=edge_data.get("header", ""),
                options=edge_data.get("options"),
                default_option=edge_data.get("default_option", 0),
                selected_option=edge_data.get("selected_option"),
                edge_type=edge_data.get("edge_type", "likert"),
                weight=edge_data.get("weight"),
            )
            self._add(orm_edge)

        self._flush()
        self._commit()
        return orm_model

    def get_by_experiment(self, experiment_id: str) -> CausalModelORM | None:
        """
        Get the causal model for an experiment with edges eagerly loaded.

        Args:
            experiment_id: Experiment ID.

        Returns:
            CausalModelORM with edges, or None if not found.
        """
        stmt = (
            select(CausalModelORM)
            .where(CausalModelORM.experiment_id == experiment_id)
            .options(joinedload(CausalModelORM.edges))
        )
        return self.session.execute(stmt).unique().scalar_one_or_none()

    def update_edge_selections(
        self,
        causal_model_id: str,
        selections: dict[str, int],
    ) -> dict[str, int]:
        """
        Batch update selected_option for edges.

        Args:
            causal_model_id: Causal model ID.
            selections: Dict of {edge_id: selected_option_index}.

        Returns:
            Dict with counts: {updated, skipped}.
        """
        updated = 0
        skipped = 0

        for edge_id, option_index in selections.items():
            orm_edge = self.session.get(
                CausalEdgeORM, (edge_id, causal_model_id)
            )
            if orm_edge is None:
                skipped += 1
                continue

            orm_edge.selected_option = option_index
            updated += 1

        self._flush()
        self._commit()
        return {"updated": updated, "skipped": skipped}

    def update_node_metadata(
        self,
        causal_model_id: str,
        node_metadata: dict,
    ) -> bool:
        """
        Update node_metadata JSONB for a causal model.

        Args:
            causal_model_id: Causal model ID.
            node_metadata: New node_metadata dict.

        Returns:
            True if updated, False if model not found.
        """
        orm_model = self.session.get(CausalModelORM, causal_model_id)
        if orm_model is None:
            return False

        orm_model.node_metadata = node_metadata
        self._flush()
        self._commit()
        return True

    def delete_by_experiment(self, experiment_id: str) -> bool:
        """
        Delete causal model and its edges for an experiment.

        Edges are deleted via CASCADE.

        Args:
            experiment_id: Experiment ID.

        Returns:
            True if a model was deleted, False if not found.
        """
        orm_model = self.get_by_experiment(experiment_id)
        if orm_model is None:
            return False

        self._delete(orm_model)
        self._flush()
        self._commit()
        return True


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Repository instantiation
    total_tests += 1
    try:
        repo = CausalModelRepository()
        if repo._session is not None:
            all_validation_failures.append("Session should be None initially")
        if repo._owns_session is not True:
            all_validation_failures.append("Should own session when none provided")
    except Exception as e:
        all_validation_failures.append(f"Init failed: {e}")

    # Test 2: Methods exist
    total_tests += 1
    try:
        repo = CausalModelRepository()
        methods = [
            "create_with_edges",
            "get_by_experiment",
            "update_edge_selections",
            "update_node_metadata",
            "delete_by_experiment",
        ]
        for method in methods:
            if not hasattr(repo, method):
                all_validation_failures.append(f"Missing method: {method}")
    except Exception as e:
        all_validation_failures.append(f"Method check failed: {e}")

    if all_validation_failures:
        print(
            f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:"
        )
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
