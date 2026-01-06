"""
ExperimentMaterial repository for synth-lab.

Data access layer for experiment materials (images, videos, documents).
Uses SQLAlchemy ORM for database operations.

References:
    - Entity: synth_lab.domain.entities.experiment_material
    - ORM model: synth_lab.models.orm.material
    - Data model: specs/001-experiment-materials/data-model.md
"""

from datetime import datetime

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from synth_lab.domain.entities.experiment_material import (
    DescriptionStatus,
    ExperimentMaterial,
    ExperimentMaterialSummary,
    FileType,
    MaterialType,
)
from synth_lab.models.orm.material import ExperimentMaterial as ExperimentMaterialORM
from synth_lab.repositories.base import BaseRepository


class MaterialNotFoundError(Exception):
    """Raised when a material is not found."""

    def __init__(self, material_id: str):
        self.material_id = material_id
        super().__init__(f"Material {material_id} not found")


class MaterialLimitExceededError(Exception):
    """Raised when material limits are exceeded."""

    def __init__(self, message: str):
        super().__init__(message)


class ExperimentMaterialRepository(BaseRepository):
    """Repository for experiment material data access.

    Uses SQLAlchemy ORM for database operations.

    Usage:
        # ORM mode (SQLAlchemy)
        repo = ExperimentMaterialRepository(session=session)

        # Without session (creates new session from global factory)
        repo = ExperimentMaterialRepository()
    """

    def __init__(self, session: Session | None = None):
        super().__init__(session=session)
        self.logger = logger.bind(component="experiment_material_repository")

    def get_by_id(self, material_id: str) -> ExperimentMaterial | None:
        """
        Get a material by its ID.

        Args:
            material_id: Material ID (mat_XXXXXXXXXXXX format).

        Returns:
            ExperimentMaterial or None if not found.
        """
        orm_mat = self._get_by_id(ExperimentMaterialORM, material_id)
        if orm_mat is None:
            return None
        return self._orm_to_entity(orm_mat)

    def list_by_experiment(
        self,
        experiment_id: str,
        order_by: str = "display_order",
    ) -> list[ExperimentMaterial]:
        """
        List all materials for an experiment.

        Args:
            experiment_id: Experiment ID.
            order_by: Field to order by (default: display_order).

        Returns:
            List of materials ordered by specified field.
        """
        stmt = select(ExperimentMaterialORM).where(
            ExperimentMaterialORM.experiment_id == experiment_id
        )

        if order_by == "display_order":
            stmt = stmt.order_by(ExperimentMaterialORM.display_order)
        elif order_by == "created_at":
            stmt = stmt.order_by(ExperimentMaterialORM.created_at.desc())

        orm_materials = list(self.session.execute(stmt).scalars().all())
        return [self._orm_to_entity(orm_mat) for orm_mat in orm_materials]

    def list_summaries_by_experiment(
        self,
        experiment_id: str,
    ) -> list[ExperimentMaterialSummary]:
        """
        List material summaries for an experiment.

        Args:
            experiment_id: Experiment ID.

        Returns:
            List of material summaries.
        """
        materials = self.list_by_experiment(experiment_id)
        return [ExperimentMaterialSummary.from_material(m) for m in materials]

    def create(self, material: ExperimentMaterial) -> ExperimentMaterial:
        """
        Create a new material record.

        Args:
            material: Material entity to create.

        Returns:
            Created material.
        """
        orm_mat = ExperimentMaterialORM(
            id=material.id,
            experiment_id=material.experiment_id,
            file_type=material.file_type.value,
            file_url=material.file_url,
            thumbnail_url=material.thumbnail_url,
            file_name=material.file_name,
            file_size=material.file_size,
            mime_type=material.mime_type,
            material_type=material.material_type.value,
            description=material.description,
            description_status=material.description_status.value,
            display_order=material.display_order,
            created_at=material.created_at.isoformat(),
        )
        self._add(orm_mat)
        self._flush()
        self._commit()

        self.logger.info(
            f"Created material {material.id} ({material.file_name}) "
            f"for experiment {material.experiment_id}"
        )
        return material

    def update(self, material: ExperimentMaterial) -> ExperimentMaterial:
        """
        Update an existing material.

        Args:
            material: Material entity with updated values.

        Returns:
            Updated material.
        """
        orm_mat = self._get_by_id(ExperimentMaterialORM, material.id)
        if orm_mat is None:
            raise MaterialNotFoundError(material.id)

        orm_mat.file_url = material.file_url
        orm_mat.thumbnail_url = material.thumbnail_url
        orm_mat.description = material.description
        orm_mat.description_status = material.description_status.value
        orm_mat.display_order = material.display_order

        self._flush()
        self._commit()

        self.logger.info(f"Updated material {material.id}")
        return material

    def update_file_url(self, material_id: str, file_url: str) -> None:
        """
        Update material file URL after upload confirmation.

        Args:
            material_id: Material ID.
            file_url: Full S3 URL of the uploaded file.
        """
        orm_mat = self._get_by_id(ExperimentMaterialORM, material_id)
        if orm_mat is None:
            raise MaterialNotFoundError(material_id)

        orm_mat.file_url = file_url
        self._flush()
        self._commit()

        self.logger.info(f"Updated file URL for material {material_id}")

    def update_description(
        self,
        material_id: str,
        description: str | None,
        status: DescriptionStatus,
    ) -> None:
        """
        Update material description and status.

        Args:
            material_id: Material ID.
            description: AI-generated description (or None if failed).
            status: New description status.
        """
        orm_mat = self._get_by_id(ExperimentMaterialORM, material_id)
        if orm_mat is None:
            raise MaterialNotFoundError(material_id)

        orm_mat.description = description
        orm_mat.description_status = status.value
        self._flush()
        self._commit()

        self.logger.info(
            f"Updated description for material {material_id}: status={status.value}"
        )

    def update_thumbnail(self, material_id: str, thumbnail_url: str) -> None:
        """
        Update material thumbnail URL.

        Args:
            material_id: Material ID.
            thumbnail_url: S3 URL of the generated thumbnail.
        """
        orm_mat = self._get_by_id(ExperimentMaterialORM, material_id)
        if orm_mat is None:
            raise MaterialNotFoundError(material_id)

        orm_mat.thumbnail_url = thumbnail_url
        self._flush()
        self._commit()

        self.logger.info(f"Updated thumbnail for material {material_id}")

    def reorder(self, experiment_id: str, material_ids: list[str]) -> None:
        """
        Reorder materials by updating display_order.

        Args:
            experiment_id: Experiment ID.
            material_ids: Material IDs in the new order.
        """
        for order, material_id in enumerate(material_ids):
            orm_mat = self._get_by_id(ExperimentMaterialORM, material_id)
            if orm_mat is None:
                raise MaterialNotFoundError(material_id)
            if orm_mat.experiment_id != experiment_id:
                raise ValueError(
                    f"Material {material_id} does not belong to experiment {experiment_id}"
                )
            orm_mat.display_order = order

        self._flush()
        self._commit()

        self.logger.info(
            f"Reordered {len(material_ids)} materials for experiment {experiment_id}"
        )

    def delete(self, material_id: str) -> bool:
        """
        Delete a material record.

        Args:
            material_id: Material ID.

        Returns:
            True if deleted, False if not found.
        """
        orm_mat = self._get_by_id(ExperimentMaterialORM, material_id)
        if orm_mat is None:
            return False

        experiment_id = orm_mat.experiment_id
        self._delete(orm_mat)
        self._flush()
        self._commit()

        self.logger.info(
            f"Deleted material {material_id} from experiment {experiment_id}"
        )
        return True

    def count_by_experiment(self, experiment_id: str) -> int:
        """
        Count materials for an experiment.

        Args:
            experiment_id: Experiment ID.

        Returns:
            Number of materials.
        """
        stmt = select(func.count()).where(
            ExperimentMaterialORM.experiment_id == experiment_id
        )
        result = self.session.execute(stmt).scalar()
        return result or 0

    def get_total_size_by_experiment(self, experiment_id: str) -> int:
        """
        Get total file size for an experiment.

        Args:
            experiment_id: Experiment ID.

        Returns:
            Total file size in bytes.
        """
        stmt = select(func.sum(ExperimentMaterialORM.file_size)).where(
            ExperimentMaterialORM.experiment_id == experiment_id
        )
        result = self.session.execute(stmt).scalar()
        return result or 0

    def get_next_display_order(self, experiment_id: str) -> int:
        """
        Get the next display order for a new material.

        Args:
            experiment_id: Experiment ID.

        Returns:
            Next display order (0-indexed).
        """
        stmt = select(func.max(ExperimentMaterialORM.display_order)).where(
            ExperimentMaterialORM.experiment_id == experiment_id
        )
        result = self.session.execute(stmt).scalar()
        return (result or -1) + 1

    def get_pending_descriptions(self, limit: int = 100) -> list[ExperimentMaterial]:
        """
        Get materials pending description generation.

        Args:
            limit: Maximum number of materials to return.

        Returns:
            List of materials with pending status.
        """
        stmt = (
            select(ExperimentMaterialORM)
            .where(
                ExperimentMaterialORM.description_status == DescriptionStatus.PENDING.value
            )
            .order_by(ExperimentMaterialORM.created_at)
            .limit(limit)
        )
        orm_materials = list(self.session.execute(stmt).scalars().all())
        return [self._orm_to_entity(orm_mat) for orm_mat in orm_materials]

    def _orm_to_entity(self, orm_mat: ExperimentMaterialORM) -> ExperimentMaterial:
        """Convert ORM model to ExperimentMaterial entity."""
        created_at = orm_mat.created_at
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        return ExperimentMaterial(
            id=orm_mat.id,
            experiment_id=orm_mat.experiment_id,
            file_type=FileType(orm_mat.file_type),
            file_url=orm_mat.file_url,
            thumbnail_url=orm_mat.thumbnail_url,
            file_name=orm_mat.file_name,
            file_size=orm_mat.file_size,
            mime_type=orm_mat.mime_type,
            material_type=MaterialType(orm_mat.material_type),
            description=orm_mat.description,
            description_status=DescriptionStatus(orm_mat.description_status),
            display_order=orm_mat.display_order,
            created_at=created_at,
        )


if __name__ == "__main__":
    import sys

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Test 1: Repository initialization
    total_tests += 1
    try:
        repo = ExperimentMaterialRepository()
        if not hasattr(repo, "logger"):
            all_validation_failures.append("Repository should have logger")
        if repo._session is not None:
            all_validation_failures.append("Session should be None initially")
    except Exception as e:
        all_validation_failures.append(f"Repository init failed: {e}")

    # Test 2: Methods exist
    total_tests += 1
    try:
        repo = ExperimentMaterialRepository()
        methods = [
            "get_by_id",
            "list_by_experiment",
            "list_summaries_by_experiment",
            "create",
            "update",
            "update_file_url",
            "update_description",
            "update_thumbnail",
            "reorder",
            "delete",
            "count_by_experiment",
            "get_total_size_by_experiment",
            "get_next_display_order",
            "get_pending_descriptions",
        ]
        for method in methods:
            if not hasattr(repo, method):
                all_validation_failures.append(f"Missing method: {method}")
    except Exception as e:
        all_validation_failures.append(f"Method check failed: {e}")

    # Test 3: Exception classes
    total_tests += 1
    try:
        err = MaterialNotFoundError("mat_123456789012")
        if "mat_123456789012" not in str(err):
            all_validation_failures.append("MaterialNotFoundError should include ID")

        limit_err = MaterialLimitExceededError("Too many files")
        if "Too many files" not in str(limit_err):
            all_validation_failures.append("MaterialLimitExceededError should include message")
    except Exception as e:
        all_validation_failures.append(f"Exception class test failed: {e}")

    # Test 4: ORM to entity conversion function exists
    total_tests += 1
    try:
        repo = ExperimentMaterialRepository()
        if not hasattr(repo, "_orm_to_entity"):
            all_validation_failures.append("Missing _orm_to_entity method")
    except Exception as e:
        all_validation_failures.append(f"ORM conversion test failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(
            f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:"
        )
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("ExperimentMaterialRepository is validated and ready for use")
        sys.exit(0)
