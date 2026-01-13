"""
T018 SynthGroupService for synth-lab.

Business logic layer for synth group operations.

References:
    - Spec: specs/018-experiment-hub/spec.md
    - Data model: specs/018-experiment-hub/data-model.md
    - Custom groups: specs/030-custom-synth-groups/spec.md
"""

from datetime import datetime, timezone
from typing import Any

import numpy as np

from synth_lab.domain.entities.synth_group import SynthGroup
from synth_lab.gen_synth.config import load_config_data
from synth_lab.gen_synth.synth_builder import assemble_synth_with_config
from synth_lab.models.orm.synth import Synth as SynthORM
from synth_lab.models.pagination import PaginatedResponse, PaginationParams
from synth_lab.repositories.synth_group_repository import (
    SynthGroupDetail,
    SynthGroupRepository,
    SynthGroupSummary,
)


class SynthGroupService:
    """Service for synth group business logic."""

    def __init__(self, repository: SynthGroupRepository | None = None):
        """
        Initialize service.

        Args:
            repository: Synth group repository. Defaults to new instance.
        """
        self.repository = repository or SynthGroupRepository()

    def create_group(
        self,
        name: str,
        description: str | None = None,
        group_id: str | None = None) -> SynthGroupSummary:
        """
        Create a new synth group.

        Args:
            name: Descriptive name for the group.
            description: Optional description.
            group_id: Optional custom ID.

        Returns:
            Created synth group summary.

        Raises:
            ValueError: If validation fails.
        """
        # Validate required fields
        if not name or not name.strip():
            raise ValueError("name is required and cannot be empty")

        # Create group entity
        if group_id:
            group = SynthGroup(
                id=group_id,
                name=name.strip(),
                description=description.strip() if description else None)
        else:
            group = SynthGroup(
                name=name.strip(),
                description=description.strip() if description else None)

        self.repository.create(group)

        # Return as summary (with synth_count)
        return self.repository.get_by_id(group.id)

    def create_with_config(
        self,
        name: str,
        config: dict[str, Any],
        description: str | None = None,
    ) -> SynthGroupSummary:
        """
        Create a new synth group with custom distribution config and generate synths.

        This method:
        1. Validates the group configuration
        2. Generates N synths using custom distributions
        3. Persists group and synths atomically

        Args:
            name: Descriptive name for the group.
            config: Group configuration with:
                - n_synths: Number of synths to generate (default 500)
                - distributions: Custom distributions for demographics
            description: Optional description.

        Returns:
            Created synth group summary with synth count.

        Raises:
            ValueError: If validation fails.
        """
        # Validate required fields
        if not name or not name.strip():
            raise ValueError("name is required and cannot be empty")

        # Get number of synths to generate
        n_synths = config.get("n_synths", 500)
        if n_synths < 1 or n_synths > 1000:
            raise ValueError("n_synths must be between 1 and 1000")

        # Load base configuration for synth generation
        base_config = load_config_data()

        # Create RNG for reproducibility within this batch
        rng = np.random.default_rng()

        # Generate synths using custom distributions
        synth_orms: list[SynthORM] = []
        for _ in range(n_synths):
            synth_data = assemble_synth_with_config(base_config, config, rng)

            # Convert to ORM model
            synth_orm = SynthORM(
                id=synth_data["id"],
                nome=synth_data["nome"],
                descricao=synth_data.get("descricao"),
                link_photo=synth_data.get("link_photo"),
                avatar_path=None,
                created_at=synth_data.get("created_at", datetime.now(timezone.utc).isoformat()),
                version=synth_data.get("version", "2.3.0"),
                data=synth_data,
            )
            synth_orms.append(synth_orm)

        # Create group entity
        group = SynthGroup(
            name=name.strip(),
            description=description.strip() if description else None,
        )

        # Persist group and synths atomically
        return self.repository.create_with_config(
            group=group,
            config=config,
            synths=synth_orms,
        )

    def get_or_create_group(
        self,
        name: str,
        description: str | None = None,
        group_id: str | None = None) -> SynthGroupSummary:
        """
        Get existing group by name or create new one.

        Args:
            name: Group name to search or create.
            description: Description for new group (ignored if exists).
            group_id: Optional custom ID for new group.

        Returns:
            Existing or newly created synth group summary.
        """
        # Search for existing group with same name
        params = PaginationParams(limit=200, offset=0)
        result = self.repository.list_groups(params)

        for group in result.data:
            if group.name == name:
                return group

        # Create new group if not found
        return self.create_group(
            name=name,
            description=description,
            group_id=group_id)

    def create_auto_group(self, prefix: str = "Geração") -> SynthGroupSummary:
        """
        Create a group with auto-generated name based on timestamp.

        Args:
            prefix: Prefix for the group name.

        Returns:
            Created synth group summary.
        """
        now = datetime.now()
        # Format: "Geração Dezembro 2025" or similar
        month_names = [
            "Janeiro",
            "Fevereiro",
            "Março",
            "Abril",
            "Maio",
            "Junho",
            "Julho",
            "Agosto",
            "Setembro",
            "Outubro",
            "Novembro",
            "Dezembro",
        ]
        month_name = month_names[now.month - 1]
        name = f"{prefix} {month_name} {now.year}"

        # Add time if name already exists
        existing = self._find_group_by_name(name)
        if existing:
            name = f"{name} ({now.strftime('%H:%M')})"

        return self.create_group(name=name)

    def get_group(self, group_id: str) -> SynthGroupSummary | None:
        """
        Get a synth group by ID.

        Args:
            group_id: Group ID.

        Returns:
            Synth group summary if found, None otherwise.
        """
        return self.repository.get_by_id(group_id)

    def get_group_detail(self, group_id: str) -> SynthGroupDetail | None:
        """
        Get synth group detail with list of synths.

        Args:
            group_id: Group ID.

        Returns:
            SynthGroupDetail if found, None otherwise.
        """
        return self.repository.get_detail(group_id)

    def list_groups(
        self, params: PaginationParams | None = None
    ) -> PaginatedResponse[SynthGroupSummary]:
        """
        List synth groups with pagination.

        Args:
            params: Pagination parameters.

        Returns:
            Paginated list of synth group summaries.
        """
        params = params or PaginationParams()
        return self.repository.list_groups(params)

    def delete_group(self, group_id: str) -> bool:
        """
        Delete a synth group.

        Args:
            group_id: ID of group to delete.

        Returns:
            True if deleted, False if not found.
        """
        return self.repository.delete(group_id)

    def _find_group_by_name(self, name: str) -> SynthGroupSummary | None:
        """Find a group by exact name match."""
        params = PaginationParams(limit=200, offset=0)
        result = self.repository.list_groups(params)

        for group in result.data:
            if group.name == name:
                return group

        return None


if __name__ == "__main__":
    import sys
    import tempfile
    from pathlib import Path


    # Validation
    all_validation_failures = []
    total_tests = 0

    # Use a temporary database for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test.db"
        init_database(test_db_path)
        db = DatabaseManager(test_db_path)
        repo = SynthGroupRepository()
        service = SynthGroupService(repo)

        # Test 1: Create group
        total_tests += 1
        try:
            group = service.create_group(name="Test Group")
            if not group.id.startswith("grp_"):
                all_validation_failures.append(f"ID should start with grp_: {group.id}")
        except Exception as e:
            all_validation_failures.append(f"Create group failed: {e}")

        # Test 2: Validate name required
        total_tests += 1
        try:
            service.create_group(name="")
            all_validation_failures.append("Should reject empty name")
        except ValueError:
            pass  # Expected

        # Test 3: Get or create - existing
        total_tests += 1
        try:
            second = service.get_or_create_group(name="Test Group")
            if second.id != group.id:
                all_validation_failures.append("Should return same group")
        except Exception as e:
            all_validation_failures.append(f"Get or create failed: {e}")

        # Test 4: Get or create - new
        total_tests += 1
        try:
            new_group = service.get_or_create_group(name="New Group")
            if new_group.name != "New Group":
                all_validation_failures.append(f"Name mismatch: {new_group.name}")
        except Exception as e:
            all_validation_failures.append(f"Get or create new failed: {e}")

        # Test 5: Auto generate group
        total_tests += 1
        try:
            auto_group = service.create_auto_group()
            if auto_group.name is None or len(auto_group.name) == 0:
                all_validation_failures.append("Auto group should have name")
        except Exception as e:
            all_validation_failures.append(f"Auto generate failed: {e}")

        # Test 6: List groups
        total_tests += 1
        try:
            result = service.list_groups()
            if len(result.data) < 3:
                all_validation_failures.append(f"Should have at least 3 groups: {len(result.data)}")
        except Exception as e:
            all_validation_failures.append(f"List groups failed: {e}")

        db.close()

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
