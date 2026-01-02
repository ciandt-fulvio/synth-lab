"""
AnalysisCacheRepository for synth-lab.

Data access layer for pre-computed analysis cache in PostgreSQL database.
Provides CRUD operations for chart data caching.

Uses SQLAlchemy ORM for database operations.

References:
    - Entity: domain/entities/analysis_cache.py
    - ORM models: synth_lab.models.orm.analysis
    - Database: infrastructure/database.py (v12)
"""

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from synth_lab.domain.entities.analysis_cache import AnalysisCache, CacheKeys
from synth_lab.domain.entities.chart_insight import ChartInsight
from synth_lab.domain.entities.executive_summary import ExecutiveSummary
from synth_lab.models.orm.analysis import AnalysisCache as AnalysisCacheORM
from synth_lab.repositories.base import BaseRepository


class AnalysisCacheRepository(BaseRepository):
    """Repository for analysis cache data access.

    Uses SQLAlchemy ORM for database operations.
    """

    def __init__(
        self,
session: Session | None = None):
        super().__init__( session=session)

    def get(self, analysis_id: str, cache_key: str) -> AnalysisCache | None:
        """
        Get a cache entry by analysis_id and cache_key.

        Args:
            analysis_id: Analysis ID.
            cache_key: Cache key (e.g., 'try_vs_success').

        Returns:
            AnalysisCache if found, None otherwise.
        """
        orm_cache = self.session.get(AnalysisCacheORM, (analysis_id, cache_key))
        if orm_cache is None:
            return None
        return self._orm_to_cache(orm_cache)
    def get_all(self, analysis_id: str) -> list[AnalysisCache]:
        """
        Get all cache entries for an analysis.

        Args:
            analysis_id: Analysis ID.

        Returns:
            List of AnalysisCache entries.
        """
        stmt = (
            select(AnalysisCacheORM)
            .where(AnalysisCacheORM.analysis_id == analysis_id)
            .order_by(AnalysisCacheORM.cache_key)
        )
        result = self.session.execute(stmt)
        return [self._orm_to_cache(orm_cache) for orm_cache in result.scalars().all()]
    def save(
        self,
        analysis_id: str,
        cache_key: str,
        data: dict[str, Any],
        params: dict[str, Any] | None = None) -> AnalysisCache:
        """
        Save or update a cache entry.

        Uses INSERT OR REPLACE to handle both insert and update.

        Args:
            analysis_id: Analysis ID.
            cache_key: Cache key.
            data: Chart data to cache.
            params: Optional parameters used for computation.

        Returns:
            Created/updated AnalysisCache.
        """
        now = datetime.now(timezone.utc)

        # Check if entry exists (composite primary key)
        orm_cache = self.session.get(AnalysisCacheORM, (analysis_id, cache_key))
        if orm_cache is not None:
            # Update existing entry
            orm_cache.data = data
            orm_cache.params = params
            orm_cache.computed_at = now.isoformat()
        else:
            # Create new entry
            orm_cache = AnalysisCacheORM(
                analysis_id=analysis_id,
                cache_key=cache_key,
                data=data,
                params=params,
                computed_at=now.isoformat())
            self._add(orm_cache)
        self._flush()
        self._commit()
        return AnalysisCache(
            analysis_id=analysis_id,
            cache_key=cache_key,
            data=data,
            params=params,
            computed_at=now)
    def save_many(
        self,
        analysis_id: str,
        entries: dict[str, dict[str, Any]]) -> int:
        """
        Save multiple cache entries in a single transaction.

        Args:
            analysis_id: Analysis ID.
            entries: Dict of cache_key -> data.

        Returns:
            Number of entries saved.
        """
        now = datetime.now(timezone.utc)

        for cache_key, data in entries.items():
            # Check if entry exists (composite primary key)
            orm_cache = self.session.get(AnalysisCacheORM, (analysis_id, cache_key))
            if orm_cache is not None:
                # Update existing entry
                orm_cache.data = data
                orm_cache.params = None
                orm_cache.computed_at = now.isoformat()
            else:
                # Create new entry
                orm_cache = AnalysisCacheORM(
                    analysis_id=analysis_id,
                    cache_key=cache_key,
                    data=data,
                    params=None,
                    computed_at=now.isoformat())
                self._add(orm_cache)
        self._flush()
        self._commit()
        return len(entries)
    def delete(self, analysis_id: str, cache_key: str) -> bool:
        """
        Delete a specific cache entry.

        Args:
            analysis_id: Analysis ID.
            cache_key: Cache key.

        Returns:
            True if deleted, False if not found.
        """
        orm_cache = self.session.get(AnalysisCacheORM, (analysis_id, cache_key))
        if orm_cache is None:
            return False
        self.session.delete(orm_cache)
        self._flush()
        self._commit()
        return True
    def delete_all(self, analysis_id: str) -> int:
        """
        Delete all cache entries for an analysis.

        Args:
            analysis_id: Analysis ID.

        Returns:
            Number of entries deleted.
        """
        stmt = select(AnalysisCacheORM).where(
            AnalysisCacheORM.analysis_id == analysis_id
        )
        result = self.session.execute(stmt)
        orm_caches = result.scalars().all()
        count = len(orm_caches)
        for orm_cache in orm_caches:
            self.session.delete(orm_cache)
        if count > 0:
            self._flush()
            self._commit()
        return count
    def _row_to_cache(self, row) -> AnalysisCache:
        """Convert a database row to AnalysisCache entity."""
        computed_at = row["computed_at"]
        if isinstance(computed_at, str):
            computed_at = datetime.fromisoformat(computed_at)

        data = json.loads(row["data"])
        params = json.loads(row["params"]) if row["params"] else None

        return AnalysisCache(
            analysis_id=row["analysis_id"],
            cache_key=row["cache_key"],
            data=data,
            params=params,
            computed_at=computed_at)

    def _orm_to_cache(self, orm_cache: AnalysisCacheORM) -> AnalysisCache:
        """Convert ORM model to AnalysisCache entity."""
        computed_at = orm_cache.computed_at
        if isinstance(computed_at, str):
            computed_at = datetime.fromisoformat(computed_at)

        # ORM stores data and params as dict directly (JSON type)
        data = orm_cache.data or {}
        params = orm_cache.params

        return AnalysisCache(
            analysis_id=orm_cache.analysis_id,
            cache_key=orm_cache.cache_key,
            data=data,
            params=params,
            computed_at=computed_at)

    # Insight-specific methods (Feature 023)

    def store_chart_insight(self, insight: ChartInsight) -> ChartInsight:
        """
        Store a chart insight in the cache.

        Args:
            insight: ChartInsight entity to store.

        Returns:
            Stored insight.
        """
        cache_key = self._get_insight_cache_key(insight.chart_type)
        self.save(insight.analysis_id, cache_key, insight.to_cache_json())
        return insight

    def get_chart_insight(self, analysis_id: str, chart_type: str) -> ChartInsight | None:
        """
        Get a chart insight from the cache.

        Args:
            analysis_id: Analysis ID.
            chart_type: Chart type (e.g., 'try_vs_success').

        Returns:
            ChartInsight if found, None otherwise.
        """
        cache_key = self._get_insight_cache_key(chart_type)
        cache = self.get(analysis_id, cache_key)
        if cache is None:
            return None
        return ChartInsight.from_cache_json(cache.data)

    def get_all_chart_insights(self, analysis_id: str) -> list[ChartInsight]:
        """
        Get all chart insights for an analysis.

        Args:
            analysis_id: Analysis ID.

        Returns:
            List of ChartInsight entities.
        """
        all_cache = self.get_all(analysis_id)
        insights = []
        for cache in all_cache:
            if cache.cache_key.startswith("insight_"):
                try:
                    insight = ChartInsight.from_cache_json(cache.data)
                    insights.append(insight)
                except Exception:
                    # Skip invalid insight entries
                    continue
        return insights

    def store_executive_summary(self, summary: ExecutiveSummary) -> ExecutiveSummary:
        """
        Store an executive summary in the cache.

        Args:
            summary: ExecutiveSummary entity to store.

        Returns:
            Stored summary.
        """
        self.save(summary.analysis_id, CacheKeys.EXECUTIVE_SUMMARY, summary.to_cache_json())
        return summary

    def get_executive_summary(self, analysis_id: str) -> ExecutiveSummary | None:
        """
        Get the executive summary from the cache.

        Args:
            analysis_id: Analysis ID.

        Returns:
            ExecutiveSummary if found, None otherwise.
        """
        cache = self.get(analysis_id, CacheKeys.EXECUTIVE_SUMMARY)
        if cache is None:
            return None
        return ExecutiveSummary.from_cache_json(cache.data)

    def _get_insight_cache_key(self, chart_type: str) -> str:
        """
        Get the cache key for a chart insight.

        Args:
            chart_type: Chart type (e.g., 'try_vs_success').

        Returns:
            Cache key (e.g., 'insight_try_vs_success').
        """
        # Map chart types to their insight cache keys
        insight_key_map = {
            "try_vs_success": CacheKeys.INSIGHT_TRY_VS_SUCCESS,
            "shap_summary": CacheKeys.INSIGHT_SHAP_SUMMARY,
            "pdp": CacheKeys.INSIGHT_PDP,
            "pca_scatter": CacheKeys.INSIGHT_PCA_SCATTER,
            "radar_comparison": CacheKeys.INSIGHT_RADAR_COMPARISON,
            "extreme_cases": CacheKeys.INSIGHT_EXTREME_CASES,
            "outliers": CacheKeys.INSIGHT_OUTLIERS,
        }
        return insight_key_map.get(chart_type, f"insight_{chart_type}")


if __name__ == "__main__":
    import sys
    import tempfile
    from pathlib import Path

    from synth_lab.domain.entities.analysis_run import AnalysisRun
    from synth_lab.domain.entities.experiment import Experiment
    from synth_lab.repositories.analysis_repository import AnalysisRepository
    from synth_lab.repositories.experiment_repository import ExperimentRepository

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Use a temporary database for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test.db"
        init_database(test_db_path)
        db = DatabaseManager(test_db_path)

        exp_repo = ExperimentRepository()
        ana_repo = AnalysisRepository()
        cache_repo = AnalysisCacheRepository()

        # Create parent experiment and analysis
        exp = Experiment(name="Test", hypothesis="Test hypothesis")
        exp_repo.create(exp)

        analysis = AnalysisRun(experiment_id=exp.id, status="completed")
        ana_repo.create(analysis)

        # Test 1: Save cache entry
        total_tests += 1
        try:
            cache = cache_repo.save(
                analysis.id,
                "try_vs_success",
                {"quadrants": [1, 2, 3, 4], "count": 100})
            if cache.cache_key != "try_vs_success":
                all_validation_failures.append(f"cache_key mismatch: {cache.cache_key}")
        except Exception as e:
            all_validation_failures.append(f"Save cache failed: {e}")

        # Test 2: Get cache entry
        total_tests += 1
        try:
            retrieved = cache_repo.get(analysis.id, "try_vs_success")
            if retrieved is None:
                all_validation_failures.append("Get returned None")
            elif retrieved.data.get("count") != 100:
                all_validation_failures.append(f"data mismatch: {retrieved.data}")
        except Exception as e:
            all_validation_failures.append(f"Get cache failed: {e}")

        # Test 3: Save many
        total_tests += 1
        try:
            count = cache_repo.save_many(
                analysis.id,
                {
                    "distribution": {"items": []},
                    "heatmap": {"bins": []},
                })
            if count != 2:
                all_validation_failures.append(f"save_many count mismatch: {count}")
        except Exception as e:
            all_validation_failures.append(f"Save many failed: {e}")

        # Test 4: Get all
        total_tests += 1
        try:
            all_cache = cache_repo.get_all(analysis.id)
            if len(all_cache) != 3:  # 1 from test 1 + 2 from test 3
                all_validation_failures.append(f"get_all count mismatch: {len(all_cache)}")
        except Exception as e:
            all_validation_failures.append(f"Get all failed: {e}")

        # Test 5: Delete single
        total_tests += 1
        try:
            result = cache_repo.delete(analysis.id, "heatmap")
            if not result:
                all_validation_failures.append("Delete returned False")
            if cache_repo.get(analysis.id, "heatmap") is not None:
                all_validation_failures.append("Entry still exists after delete")
        except Exception as e:
            all_validation_failures.append(f"Delete single failed: {e}")

        # Test 6: Delete all
        total_tests += 1
        try:
            count = cache_repo.delete_all(analysis.id)
            if count != 2:  # 3 - 1 deleted
                all_validation_failures.append(f"delete_all count mismatch: {count}")
            if len(cache_repo.get_all(analysis.id)) != 0:
                all_validation_failures.append("Entries still exist after delete_all")
        except Exception as e:
            all_validation_failures.append(f"Delete all failed: {e}")

        # Test 7: CASCADE delete (when analysis is deleted)
        total_tests += 1
        try:
            # Re-create cache
            cache_repo.save(analysis.id, "test_cascade", {"test": True})

            # Delete analysis
            ana_repo.delete(analysis.id)

            # Cache should be gone (CASCADE)
            if cache_repo.get(analysis.id, "test_cascade") is not None:
                all_validation_failures.append("CASCADE delete did not work")
        except Exception as e:
            all_validation_failures.append(f"CASCADE delete test failed: {e}")

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
