"""
ExperimentService for synth-lab.

Business logic layer for experiment operations.

References:
    - Spec: specs/019-experiment-refactor/spec.md
    - Data model: specs/019-experiment-refactor/data-model.md
"""

from synth_lab.domain.entities.experiment import Experiment
from synth_lab.models.pagination import PaginatedResponse, PaginationParams
from synth_lab.repositories.experiment_repository import ExperimentRepository, ExperimentSummary


class ExperimentService:
    """Service for experiment business logic."""

    # Validation constants
    NAME_MAX_LENGTH = 100
    HYPOTHESIS_MAX_LENGTH = 500
    DESCRIPTION_MAX_LENGTH = 2000

    def __init__(self, repository: ExperimentRepository | None = None):
        """
        Initialize service.

        Args:
            repository: Experiment repository. Defaults to new instance.
        """
        self.repository = repository or ExperimentRepository()

    def create_experiment(
        self,
        name: str,
        hypothesis: str,
        synth_group_id: str,
        description: str | None = None,
        owner_id: str | None = None) -> Experiment:
        """
        Create a new experiment.

        Args:
            name: Short name of the feature (max 100 chars).
            hypothesis: Description of hypothesis to test (max 500 chars).
            synth_group_id: ID of the synth group to use (required).
            description: Additional context (max 2000 chars).
            owner_id: UUID of the user who owns this experiment.

        Returns:
            Created experiment.

        Raises:
            ValueError: If validation fails.
        """
        # Validate required fields
        if not name or not name.strip():
            raise ValueError("name is required and cannot be empty")
        if not hypothesis or not hypothesis.strip():
            raise ValueError("hypothesis is required and cannot be empty")
        if not synth_group_id or not synth_group_id.strip():
            raise ValueError("synth_group_id is required and cannot be empty")

        # Validate max lengths
        if len(name) > self.NAME_MAX_LENGTH:
            raise ValueError(
                f"name must not exceed {self.NAME_MAX_LENGTH} characters (got {len(name)})"
            )
        if len(hypothesis) > self.HYPOTHESIS_MAX_LENGTH:
            raise ValueError(
                f"hypothesis must not exceed {self.HYPOTHESIS_MAX_LENGTH} characters (got {len(hypothesis)})"
            )
        if description and len(description) > self.DESCRIPTION_MAX_LENGTH:
            raise ValueError(
                f"description must not exceed {self.DESCRIPTION_MAX_LENGTH} characters"
            )

        # Create experiment entity
        experiment = Experiment(
            name=name.strip(),
            hypothesis=hypothesis.strip(),
            description=description.strip() if description else None,
            synth_group_id=synth_group_id,
            owner_id=owner_id)

        return self.repository.create(experiment)

    def get_experiment(self, experiment_id: str) -> Experiment | None:
        """
        Get an experiment by ID.

        Args:
            experiment_id: Experiment ID.

        Returns:
            Experiment if found, None otherwise.
        """
        return self.repository.get_by_id(experiment_id)

    def get_experiment_detail(self, experiment_id: str) -> ExperimentSummary | None:
        """
        Get experiment detail with interview counts.

        Args:
            experiment_id: Experiment ID.

        Returns:
            ExperimentSummary with counts if found, None otherwise.
        """
        # List experiments and filter by ID to get counts
        params = PaginationParams(limit=200, offset=0)
        result = self.repository.list_experiments(params)

        for exp in result.data:
            if exp.id == experiment_id:
                return exp

        return None

    def list_experiments(
        self, params: PaginationParams | None = None, user_id: str | None = None
    ) -> PaginatedResponse[ExperimentSummary]:
        """
        List experiments with pagination.

        Args:
            params: Pagination parameters.
            user_id: If provided, filter to experiments the user can access.

        Returns:
            Paginated list of experiment summaries.
        """
        params = params or PaginationParams()
        return self.repository.list_experiments(params, user_id=user_id)

    def update_experiment(
        self,
        experiment_id: str,
        name: str | None = None,
        hypothesis: str | None = None,
        description: str | None = None,
        synth_group_id: str | None = None) -> Experiment | None:
        """
        Update an experiment.

        Args:
            experiment_id: ID of experiment to update.
            name: New name (optional).
            hypothesis: New hypothesis (optional).
            description: New description (optional).
            synth_group_id: New synth group ID (optional).

        Returns:
            Updated experiment if found, None otherwise.

        Raises:
            ValueError: If validation fails.
        """
        # Validate max lengths if provided
        if name is not None:
            if len(name) > self.NAME_MAX_LENGTH:
                raise ValueError(f"name must not exceed {self.NAME_MAX_LENGTH} characters")
        if hypothesis is not None:
            if len(hypothesis) > self.HYPOTHESIS_MAX_LENGTH:
                raise ValueError(
                    f"hypothesis must not exceed {self.HYPOTHESIS_MAX_LENGTH} characters"
                )
        if description is not None:
            if len(description) > self.DESCRIPTION_MAX_LENGTH:
                raise ValueError(
                    f"description must not exceed {self.DESCRIPTION_MAX_LENGTH} characters"
                )

        return self.repository.update(
            experiment_id,
            name=name,
            hypothesis=hypothesis,
            description=description,
            synth_group_id=synth_group_id)

    def delete_experiment(self, experiment_id: str) -> bool:
        """
        Delete an experiment.

        Args:
            experiment_id: ID of experiment to delete.

        Returns:
            True if deleted, False if not found.
        """
        return self.repository.delete(experiment_id)
