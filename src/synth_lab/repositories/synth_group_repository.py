"""
T014 SynthGroupRepository for synth-lab.

Data access layer for synth group data. Uses SQLAlchemy ORM for database operations.

References:
    - Spec: specs/018-experiment-hub/spec.md
    - Data model: specs/018-experiment-hub/data-model.md
    - ORM models: synth_lab.models.orm.synth
"""

import math
from datetime import datetime, timezone

from pydantic import BaseModel, Field
from sqlalchemy import func as sqlfunc
from sqlalchemy import select
from sqlalchemy.orm import Session

from synth_lab.api.schemas.synth_group_stats import (
    CategoryCount,
    DemographicStats,
    DisabilityStats,
    HistogramBucket,
    HistogramData,
    SensitivityStats,
    SynthGroupStatistics,
)
from synth_lab.domain.entities.synth_group import (
    DEFAULT_SYNTH_GROUP_DESCRIPTION,
    DEFAULT_SYNTH_GROUP_ID,
    DEFAULT_SYNTH_GROUP_NAME,
    SynthGroup,
)
from synth_lab.models.orm.synth import Synth as SynthORM
from synth_lab.models.orm.synth import SynthGroup as SynthGroupORM
from synth_lab.models.pagination import PaginatedResponse, PaginationMeta, PaginationParams
from synth_lab.repositories.base import BaseRepository


class SynthGroupSummary(BaseModel):
    """Summary of a synth group for list display."""

    id: str = Field(description="Group ID.")
    name: str = Field(description="Group name.")
    description: str | None = Field(default=None, description="Group description.")
    synth_count: int = Field(default=0, description="Number of synths in group.")
    created_at: datetime = Field(description="Creation timestamp.")
    config: dict | None = Field(default=None, description="Distribution configuration.")


class SynthSummary(BaseModel):
    """Summary of a synth for group detail display."""

    id: str = Field(description="Synth ID.")
    nome: str = Field(description="Synth name.")
    descricao: str | None = Field(default=None, description="Synth description.")
    avatar_path: str | None = Field(default=None, description="Path to avatar image.")
    synth_group_id: str | None = Field(default=None, description="Group ID.")
    created_at: datetime = Field(description="Creation timestamp.")


class SynthGroupDetail(BaseModel):
    """Full synth group details including synths."""

    id: str = Field(description="Group ID.")
    name: str = Field(description="Group name.")
    description: str | None = Field(default=None, description="Group description.")
    synth_count: int = Field(default=0, description="Number of synths in group.")
    created_at: datetime = Field(description="Creation timestamp.")
    config: dict | None = Field(default=None, description="Distribution configuration.")
    synths: list[SynthSummary] = Field(default_factory=list, description="Synths in this group.")


class SynthGroupRepository(BaseRepository):
    """Repository for synth group data access.

    Uses SQLAlchemy ORM for database operations.
    """

    def __init__(self, session: Session | None = None):
        super().__init__(session=session)

    def ensure_default_group(self) -> SynthGroupSummary:
        """
        Ensure the default synth group exists.

        Creates the default group if it doesn't exist, returns it if it does.
        This is the group used when no specific group is provided during synth generation.

        Returns:
            SynthGroupSummary: The default synth group.
        """
        # Check if default group exists
        existing = self.get_by_id(DEFAULT_SYNTH_GROUP_ID)
        if existing:
            return existing

        now = datetime.now(timezone.utc)
        orm_group = SynthGroupORM(
            id=DEFAULT_SYNTH_GROUP_ID,
            name=DEFAULT_SYNTH_GROUP_NAME,
            description=DEFAULT_SYNTH_GROUP_DESCRIPTION,
            created_at=now.isoformat(),
        )
        self._add(orm_group)
        self._flush()
        self._commit()
        return self.get_by_id(DEFAULT_SYNTH_GROUP_ID)

    def create(self, group: SynthGroup, config: dict | None = None) -> SynthGroup:
        """
        Create a new synth group.

        Args:
            group: SynthGroup entity to create.
            config: Optional distribution configuration (JSONB).

        Returns:
            Created synth group with persisted data.
        """
        orm_group = SynthGroupORM(
            id=group.id,
            name=group.name,
            description=group.description,
            created_at=group.created_at.isoformat(),
            config=config,
            owner_id=group.owner_id,
        )
        self._add(orm_group)
        self._flush()
        self._commit()
        return group

    def create_with_config(
        self,
        group: SynthGroup,
        config: dict,
        synths: list[SynthORM] | None = None,
    ) -> SynthGroupSummary:
        """
        Create a new synth group with config and optionally synths atomically.

        Args:
            group: SynthGroup entity to create.
            config: Distribution configuration (JSONB).
            synths: Optional list of synth ORM objects to persist with the group.

        Returns:
            Created synth group summary with config.
        """
        orm_group = SynthGroupORM(
            id=group.id,
            name=group.name,
            description=group.description,
            created_at=group.created_at.isoformat(),
            config=config,
            owner_id=group.owner_id,
        )
        self._add(orm_group)

        # Add synths if provided
        if synths:
            for synth in synths:
                synth.synth_group_id = group.id
                self._add(synth)

        # Calculate synth count before commit to avoid DetachedInstanceError
        synth_count = len(synths) if synths else 0

        self._flush()
        self._commit()

        # Build summary manually to avoid accessing detached orm_group.synths relationship
        created_at = group.created_at
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        return SynthGroupSummary(
            id=orm_group.id,
            name=orm_group.name,
            description=orm_group.description,
            synth_count=synth_count,
            created_at=created_at,
            config=config,
        )

    def get_by_id(self, group_id: str) -> SynthGroupSummary | None:
        """
        Get a synth group by ID with synth count.

        Args:
            group_id: Group ID to retrieve.

        Returns:
            SynthGroupSummary if found, None otherwise.
        """
        orm_group = self.session.get(SynthGroupORM, group_id)
        if orm_group is None:
            return None
        return self._orm_to_summary(orm_group)

    def get_detail(self, group_id: str) -> SynthGroupDetail | None:
        """
        Get a synth group with full details including synths.

        Args:
            group_id: Group ID to retrieve.

        Returns:
            SynthGroupDetail if found, None otherwise.
        """
        orm_group = self.session.get(SynthGroupORM, group_id)
        if orm_group is None:
            return None

        created_at = orm_group.created_at
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        # Sort synths by created_at descending
        def get_sort_key(s: SynthORM) -> str:
            if isinstance(s.created_at, str):
                return s.created_at
            return s.created_at.isoformat()

        orm_synths = sorted(orm_group.synths, key=get_sort_key, reverse=True)

        synths = [self._orm_synth_to_summary(s) for s in orm_synths]

        return SynthGroupDetail(
            id=orm_group.id,
            name=orm_group.name,
            description=orm_group.description,
            synth_count=len(synths),
            created_at=created_at,
            config=orm_group.config,
            synths=synths,
        )

    def list_groups(
        self, params: PaginationParams, user_id: str | None = None
    ) -> PaginatedResponse[SynthGroupSummary]:
        """
        List synth groups with pagination.

        When user_id is provided, only returns groups owned by or shared with the user.

        Args:
            params: Pagination parameters.
            user_id: If provided, filter to groups the user can access.

        Returns:
            Paginated response with synth group summaries.
        """
        from sqlalchemy import or_

        from synth_lab.models.orm.share import SynthGroupShare as SynthGroupShareORM

        stmt = select(SynthGroupORM).order_by(SynthGroupORM.created_at.desc())
        count_base = select(SynthGroupORM)

        # Filter by user access (ownership or shares)
        if user_id:
            access_filter = or_(
                SynthGroupORM.owner_id == user_id,
                SynthGroupORM.id.in_(
                    select(SynthGroupShareORM.synth_group_id).where(
                        SynthGroupShareORM.user_id == user_id
                    )
                ),
            )
            stmt = stmt.where(access_filter)
            count_base = count_base.where(access_filter)

        count_stmt = select(sqlfunc.count()).select_from(count_base.subquery())
        total = self.session.execute(count_stmt).scalar() or 0

        stmt = stmt.limit(params.limit).offset(params.offset)
        groups = list(self.session.execute(stmt).scalars().all())

        summaries = [self._orm_to_summary(g) for g in groups]
        meta = PaginationMeta.from_params(total, params)
        return PaginatedResponse(data=summaries, pagination=meta)

    def delete(self, group_id: str) -> bool:
        """
        Delete a synth group.

        Nullifies synth_group_id references in synths table.

        Args:
            group_id: ID of group to delete.

        Returns:
            True if deleted, False if not found.
        """
        orm_group = self.session.get(SynthGroupORM, group_id)
        if orm_group is None:
            return False

        # Nullify synth references
        for synth in orm_group.synths:
            synth.synth_group_id = None

        self.session.delete(orm_group)
        self._flush()
        self._commit()
        return True

    def get_statistics(self, group_id: str) -> SynthGroupStatistics | None:
        """
        Compute aggregate statistics for a synth group.

        Extracts demographics and sensitivities from the JSONB data column
        and computes histogram buckets, means, and standard deviations.

        Args:
            group_id: Synth group ID.

        Returns:
            SynthGroupStatistics if group exists, None otherwise.
        """
        orm_group = self.session.get(SynthGroupORM, group_id)
        if orm_group is None:
            return None

        # Get all synths data for this group
        stmt = select(SynthORM.data).where(
            SynthORM.synth_group_id == group_id,
            SynthORM.data.isnot(None),
        )
        rows = list(self.session.execute(stmt).scalars().all())
        total = len(rows)

        if total == 0:
            return SynthGroupStatistics(group_id=group_id, total_synths=0)

        # Extract raw values
        ages: list[float] = []
        incomes: list[float] = []
        education_counts: dict[str, int] = {}
        family_counts: dict[str, int] = {}
        pcd_count = 0
        sensitivity_values: dict[str, list[float]] = {}

        for data in rows:
            if not isinstance(data, dict):
                continue

            demo = data.get("demografia", {})
            if demo:
                age = demo.get("idade")
                if age is not None:
                    ages.append(float(age))

                income = demo.get("renda_mensal")
                if income is not None:
                    incomes.append(float(income))

                edu = demo.get("escolaridade")
                if edu:
                    education_counts[edu] = education_counts.get(edu, 0) + 1

                family = demo.get("composicao_familiar", {})
                family_type = family.get("tipo") if isinstance(family, dict) else None
                if family_type:
                    family_counts[family_type] = family_counts.get(family_type, 0) + 1

            # Check disability (any non-zero severity)
            deficiencias = data.get("deficiencias", {})
            if deficiencias and isinstance(deficiencias, dict):
                has_disability = False
                for def_type in ["visual", "auditiva", "motora", "cognitiva"]:
                    def_data = deficiencias.get(def_type, {})
                    if isinstance(def_data, dict):
                        tipo = def_data.get("tipo", "nenhuma")
                        if tipo and tipo != "nenhuma":
                            has_disability = True
                            break
                if has_disability:
                    pcd_count += 1

            # Sensitivities
            sensitivities = data.get("sensitivities", {})
            if sensitivities and isinstance(sensitivities, dict):
                for key, val in sensitivities.items():
                    if isinstance(val, (int, float)):
                        sensitivity_values.setdefault(key, []).append(float(val))

        # Build demographic stats
        demographics = DemographicStats(
            age=self._build_age_histogram(ages, total),
            income=self._build_income_histogram(incomes, total),
            education=self._build_category_counts(education_counts, total),
            family_composition=self._build_category_counts(family_counts, total),
            disability=DisabilityStats(
                pcd_count=pcd_count,
                pcd_percentage=round(pcd_count / total * 100, 1) if total > 0 else 0.0,
                non_pcd_count=total - pcd_count,
                non_pcd_percentage=(
                    round((total - pcd_count) / total * 100, 1) if total > 0 else 0.0
                ),
            ),
        )

        # Build sensitivity stats
        sens_distributions: dict[str, HistogramData] = {}
        for key, values in sensitivity_values.items():
            sens_distributions[key] = self._build_sensitivity_histogram(values, total)

        return SynthGroupStatistics(
            group_id=group_id,
            total_synths=total,
            demographics=demographics,
            sensitivities=SensitivityStats(distributions=sens_distributions),
        )

    @staticmethod
    def _compute_stats(values: list[float]) -> tuple[float, float]:
        """Compute mean and standard deviation for a list of values."""
        if not values:
            return 0.0, 0.0
        mean = sum(values) / len(values)
        if len(values) < 2:
            return round(mean, 2), 0.0
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        return round(mean, 2), round(math.sqrt(variance), 2)

    @staticmethod
    def _build_age_histogram(ages: list[float], total: int) -> HistogramData:
        """Build age histogram with predefined buckets."""
        buckets_def = [
            ("15-29", 15, 30),
            ("30-44", 30, 45),
            ("45-59", 45, 60),
            ("60+", 60, 200),
        ]
        buckets: list[HistogramBucket] = []
        for label, low, high in buckets_def:
            count = sum(1 for a in ages if low <= a < high)
            pct = round(count / total * 100, 1) if total > 0 else 0.0
            buckets.append(HistogramBucket(label=label, count=count, percentage=pct))

        mean, std = SynthGroupRepository._compute_stats(ages)
        return HistogramData(buckets=buckets, mean=mean, std_dev=std)

    @staticmethod
    def _build_income_histogram(incomes: list[float], total: int) -> HistogramData:
        """Build income histogram with predefined buckets."""
        buckets_def = [
            ("0-1k", 0, 1000),
            ("1k-3k", 1000, 3000),
            ("3k-5k", 3000, 5000),
            ("5k-10k", 5000, 10000),
            ("10k+", 10000, float("inf")),
        ]
        buckets: list[HistogramBucket] = []
        for label, low, high in buckets_def:
            count = sum(1 for i in incomes if low <= i < high)
            pct = round(count / total * 100, 1) if total > 0 else 0.0
            buckets.append(HistogramBucket(label=label, count=count, percentage=pct))

        mean, std = SynthGroupRepository._compute_stats(incomes)
        return HistogramData(buckets=buckets, mean=mean, std_dev=std)

    @staticmethod
    def _build_category_counts(counts: dict[str, int], total: int) -> list[CategoryCount]:
        """Build category counts sorted by count descending."""
        result = []
        for label, count in sorted(counts.items(), key=lambda x: -x[1]):
            pct = round(count / total * 100, 1) if total > 0 else 0.0
            result.append(CategoryCount(label=label, count=count, percentage=pct))
        return result

    @staticmethod
    def _build_sensitivity_histogram(values: list[float], total: int) -> HistogramData:
        """Build sensitivity histogram with 0.05-width buckets in [0, 1] range."""
        buckets: list[HistogramBucket] = []
        step = 0.05
        for i in range(20):
            low = round(i * step, 2)
            high = round((i + 1) * step, 2)
            upper = high if i < 19 else 1.01  # inclusive upper for last bucket
            count = sum(1 for v in values if low <= v < upper)
            pct = round(count / total * 100, 1) if total > 0 else 0.0
            label = f"{low:.2f}"
            buckets.append(HistogramBucket(label=label, count=count, percentage=pct))

        mean, std = SynthGroupRepository._compute_stats(values)
        return HistogramData(buckets=buckets, mean=mean, std_dev=std)

    def _row_to_summary(self, row) -> SynthGroupSummary:
        """Convert a database row to SynthGroupSummary."""
        created_at = row["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        return SynthGroupSummary(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            synth_count=row["synth_count"],
            created_at=created_at,
        )

    def _row_to_synth_summary(self, row) -> SynthSummary:
        """Convert a database row to SynthSummary."""
        created_at = row["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        return SynthSummary(
            id=row["id"],
            nome=row["nome"],
            descricao=row["descricao"],
            avatar_path=row["avatar_path"],
            synth_group_id=row["synth_group_id"],
            created_at=created_at,
        )

    # =========================================================================
    # ORM conversion methods
    # =========================================================================

    def _orm_to_summary(self, orm_group: SynthGroupORM) -> SynthGroupSummary:
        """Convert ORM model to SynthGroupSummary."""
        created_at = orm_group.created_at
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        synth_count = len(orm_group.synths) if orm_group.synths else 0

        return SynthGroupSummary(
            id=orm_group.id,
            name=orm_group.name,
            description=orm_group.description,
            synth_count=synth_count,
            created_at=created_at,
            config=orm_group.config,
        )

    def _orm_synth_to_summary(self, orm_synth: SynthORM) -> SynthSummary:
        """Convert ORM Synth model to SynthSummary."""
        created_at = orm_synth.created_at
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        return SynthSummary(
            id=orm_synth.id,
            nome=orm_synth.nome,
            descricao=orm_synth.descricao,
            avatar_path=orm_synth.avatar_path,
            synth_group_id=orm_synth.synth_group_id,
            created_at=created_at,
        )


if __name__ == "__main__":
    import sys
    import tempfile
    from pathlib import Path

    from synth_lab.domain.entities.synth_group import SynthGroup

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Use a temporary database for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test.db"
        init_database(test_db_path)  # Initialize schema first
        db = DatabaseManager(test_db_path)
        repo = SynthGroupRepository()

        # Test 0: Default group should already exist after init_database
        total_tests += 1
        try:
            default_group = repo.get_by_id(DEFAULT_SYNTH_GROUP_ID)
            if default_group is None:
                all_validation_failures.append("Default group not found after init_database")
            elif default_group.name != DEFAULT_SYNTH_GROUP_NAME:
                all_validation_failures.append(f"Default group name mismatch: {default_group.name}")
        except Exception as e:
            all_validation_failures.append(f"Default group check failed: {e}")

        # Test 1: Create synth group
        total_tests += 1
        try:
            group = SynthGroup(name="Test Group", description="Test description")
            result = repo.create(group)
            if result.id != group.id:
                all_validation_failures.append(f"ID mismatch: {result.id} != {group.id}")
        except Exception as e:
            all_validation_failures.append(f"Create synth group failed: {e}")

        # Test 2: Get synth group by ID
        total_tests += 1
        try:
            retrieved = repo.get_by_id(group.id)
            if retrieved is None:
                all_validation_failures.append("Get by ID returned None")
            elif retrieved.name != "Test Group":
                all_validation_failures.append(f"Name mismatch: {retrieved.name}")
        except Exception as e:
            all_validation_failures.append(f"Get by ID failed: {e}")

        # Test 3: Get non-existent group
        total_tests += 1
        try:
            result = repo.get_by_id("grp_nonexist")
            if result is not None:
                all_validation_failures.append("Should return None for non-existent")
        except Exception as e:
            all_validation_failures.append(f"Get non-existent failed: {e}")

        # Test 4: List groups (should have default + created group = 2)
        total_tests += 1
        try:
            params = PaginationParams(limit=10, offset=0)
            result = repo.list_groups(params)
            # Default group + created group = 2
            if len(result.data) != 2:
                all_validation_failures.append(
                    f"Expected 2 groups (default + created), got {len(result.data)}"
                )
        except Exception as e:
            all_validation_failures.append(f"List groups failed: {e}")

        # Test 5: Delete group
        total_tests += 1
        try:
            result = repo.delete(group.id)
            if not result:
                all_validation_failures.append("Delete returned False")
            if repo.get_by_id(group.id) is not None:
                all_validation_failures.append("Group still exists after delete")
        except Exception as e:
            all_validation_failures.append(f"Delete failed: {e}")

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
