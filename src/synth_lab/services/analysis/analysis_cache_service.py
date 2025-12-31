"""
Analysis Cache Service for synth-lab.

Pre-computes and caches chart data after analysis completion.
Provides fast retrieval of cached data for chart endpoints.

References:
    - Entity: domain/entities/analysis_cache.py
    - Repository: repositories/analysis_cache_repository.py
    - Charts: services/simulation/chart_data_service.py
"""

import time
from typing import Any

from loguru import logger

from synth_lab.domain.entities.analysis_cache import CacheKeys
from synth_lab.infrastructure.database import DatabaseManager, get_database
from synth_lab.repositories.analysis_cache_repository import AnalysisCacheRepository
from synth_lab.repositories.analysis_outcome_repository import AnalysisOutcomeRepository
from synth_lab.services.simulation.chart_data_service import ChartDataService
from synth_lab.services.simulation.clustering_service import ClusteringService
from synth_lab.services.simulation.explainability_service import ExplainabilityService
from synth_lab.services.simulation.outlier_service import OutlierService


class AnalysisCacheService:
    """
    Service for pre-computing and caching analysis chart data.

    Computes all standard charts after analysis completion and saves
    them to the cache for fast retrieval.
    """

    # Default parameters for cached charts
    DEFAULT_PARAMS = {
        CacheKeys.TRY_VS_SUCCESS: {"x_threshold": 0.5, "y_threshold": 0.5},
        CacheKeys.DISTRIBUTION: {"sort_by": "success_rate", "order": "desc", "limit": 50},
        CacheKeys.HEATMAP: {
            "x_axis": "digital_literacy",
            "y_axis": "domain_expertise",
            "bins": 5,
            "metric": "failed_rate",
        },
        CacheKeys.SCATTER: {
            "x_axis": "digital_literacy",
            "y_axis": "success_rate",
        },
        CacheKeys.CORRELATIONS: {},
        CacheKeys.EXTREME_CASES: {"n_per_category": 5},
        CacheKeys.OUTLIERS: {"contamination": 0.1},
        CacheKeys.SHAP_SUMMARY: {"features": None},
    }

    def __init__(
        self,
        db: DatabaseManager | None = None,
        cache_repo: AnalysisCacheRepository | None = None,
        outcome_repo: AnalysisOutcomeRepository | None = None,
        chart_service: ChartDataService | None = None,
        clustering_service: ClusteringService | None = None,
        outlier_service: OutlierService | None = None,
        explainability_service: ExplainabilityService | None = None,
    ):
        self.db = db or get_database()
        self.cache_repo = cache_repo or AnalysisCacheRepository(self.db)
        self.outcome_repo = outcome_repo or AnalysisOutcomeRepository(self.db)
        self.chart_service = chart_service or ChartDataService()
        self.clustering_service = clustering_service or ClusteringService()
        self.outlier_service = outlier_service or OutlierService()
        self.explainability_service = explainability_service or ExplainabilityService()
        self.logger = logger.bind(component="analysis_cache_service")

    def pre_compute_all(self, analysis_id: str) -> dict[str, bool]:
        """
        Pre-compute all standard charts for an analysis.

        Called after analysis completes to populate cache.

        Args:
            analysis_id: Analysis ID.

        Returns:
            Dict of cache_key -> success status.
        """
        start_time = time.time()
        self.logger.info(f"Pre-computing cache for analysis {analysis_id}")

        # Load outcomes once
        outcomes, _ = self.outcome_repo.get_outcomes(analysis_id)
        if not outcomes:
            self.logger.warning(f"No outcomes found for analysis {analysis_id}")
            return {}

        results: dict[str, bool] = {}
        cache_entries: dict[str, dict[str, Any]] = {}

        # Phase 1: Overview charts
        try:
            chart = self.chart_service.get_try_vs_success(
                simulation_id=analysis_id,
                outcomes=outcomes,
                **self.DEFAULT_PARAMS[CacheKeys.TRY_VS_SUCCESS],
            )
            cache_entries[CacheKeys.TRY_VS_SUCCESS] = chart.model_dump()
            results[CacheKeys.TRY_VS_SUCCESS] = True
        except Exception as e:
            self.logger.error(f"Failed to compute {CacheKeys.TRY_VS_SUCCESS}: {e}")
            results[CacheKeys.TRY_VS_SUCCESS] = False

        try:
            chart = self.chart_service.get_outcome_distribution(
                simulation_id=analysis_id,
                outcomes=outcomes,
                **self.DEFAULT_PARAMS[CacheKeys.DISTRIBUTION],
            )
            cache_entries[CacheKeys.DISTRIBUTION] = chart.model_dump()
            results[CacheKeys.DISTRIBUTION] = True
        except Exception as e:
            self.logger.error(f"Failed to compute {CacheKeys.DISTRIBUTION}: {e}")
            results[CacheKeys.DISTRIBUTION] = False

        # Phase 2: Problem Location charts
        try:
            chart = self.chart_service.get_failure_heatmap(
                simulation_id=analysis_id,
                outcomes=outcomes,
                **self.DEFAULT_PARAMS[CacheKeys.HEATMAP],
            )
            cache_entries[CacheKeys.HEATMAP] = chart.model_dump()
            results[CacheKeys.HEATMAP] = True
        except Exception as e:
            self.logger.error(f"Failed to compute {CacheKeys.HEATMAP}: {e}")
            results[CacheKeys.HEATMAP] = False

        try:
            chart = self.chart_service.get_scatter_correlation(
                simulation_id=analysis_id,
                outcomes=outcomes,
                **self.DEFAULT_PARAMS[CacheKeys.SCATTER],
            )
            cache_entries[CacheKeys.SCATTER] = chart.model_dump()
            results[CacheKeys.SCATTER] = True
        except Exception as e:
            self.logger.error(f"Failed to compute {CacheKeys.SCATTER}: {e}")
            results[CacheKeys.SCATTER] = False

        try:
            chart = self.chart_service.get_attribute_correlations(
                simulation_id=analysis_id,
                outcomes=outcomes,
            )
            cache_entries[CacheKeys.CORRELATIONS] = chart.model_dump()
            results[CacheKeys.CORRELATIONS] = True
        except Exception as e:
            self.logger.error(f"Failed to compute {CacheKeys.CORRELATIONS}: {e}")
            results[CacheKeys.CORRELATIONS] = False

        # Phase 4: Edge Cases
        try:
            chart = self.outlier_service.get_extreme_cases(
                simulation_id=analysis_id,
                outcomes=outcomes,
                **self.DEFAULT_PARAMS[CacheKeys.EXTREME_CASES],
            )
            cache_entries[CacheKeys.EXTREME_CASES] = chart.model_dump()
            results[CacheKeys.EXTREME_CASES] = True
        except Exception as e:
            self.logger.error(f"Failed to compute {CacheKeys.EXTREME_CASES}: {e}")
            results[CacheKeys.EXTREME_CASES] = False

        try:
            chart = self.outlier_service.detect_outliers(
                simulation_id=analysis_id,
                outcomes=outcomes,
                **self.DEFAULT_PARAMS[CacheKeys.OUTLIERS],
            )
            cache_entries[CacheKeys.OUTLIERS] = chart.model_dump()
            results[CacheKeys.OUTLIERS] = True
        except Exception as e:
            self.logger.error(f"Failed to compute {CacheKeys.OUTLIERS}: {e}")
            results[CacheKeys.OUTLIERS] = False

        # Phase 5: Explainability
        try:
            chart = self.explainability_service.get_shap_summary(
                simulation_id=analysis_id,
                outcomes=outcomes,
                **self.DEFAULT_PARAMS[CacheKeys.SHAP_SUMMARY],
            )
            cache_entries[CacheKeys.SHAP_SUMMARY] = chart.model_dump()
            results[CacheKeys.SHAP_SUMMARY] = True
        except Exception as e:
            self.logger.error(f"Failed to compute {CacheKeys.SHAP_SUMMARY}: {e}")
            results[CacheKeys.SHAP_SUMMARY] = False

        # Phase 3: Segmentation (auto clustering + PCA + Radar)
        kmeans_result = None
        try:
            # Run automatic K-Means clustering
            kmeans_result = self.clustering_service.cluster_kmeans(
                simulation_id=analysis_id,
                outcomes=outcomes,
                n_clusters=None,  # Auto-detect via elbow
            )
            self.logger.info(f"Auto-clustering completed with k={kmeans_result.n_clusters}")
        except Exception as e:
            self.logger.warning(f"Failed to auto-cluster: {e}")

        if kmeans_result:
            # PCA Scatter
            try:
                chart = self.clustering_service.get_pca_scatter(
                    simulation_id=analysis_id,
                    outcomes=outcomes,
                    kmeans_result=kmeans_result,
                )
                cache_entries[CacheKeys.PCA_SCATTER] = chart.model_dump()
                results[CacheKeys.PCA_SCATTER] = True
            except Exception as e:
                self.logger.error(f"Failed to compute {CacheKeys.PCA_SCATTER}: {e}")
                results[CacheKeys.PCA_SCATTER] = False

            # Radar Comparison
            try:
                chart = self.clustering_service.radar_comparison(kmeans_result)
                cache_entries[CacheKeys.RADAR_COMPARISON] = chart.model_dump()
                results[CacheKeys.RADAR_COMPARISON] = True
            except Exception as e:
                self.logger.error(f"Failed to compute {CacheKeys.RADAR_COMPARISON}: {e}")
                results[CacheKeys.RADAR_COMPARISON] = False

        # Save all entries to cache
        if cache_entries:
            saved = self.cache_repo.save_many(analysis_id, cache_entries)
            self.logger.info(f"Saved {saved} cache entries")

        elapsed = time.time() - start_time
        success_count = sum(1 for v in results.values() if v)
        self.logger.info(
            f"Cache pre-computation completed in {elapsed:.2f}s: "
            f"{success_count}/{len(results)} charts cached"
        )

        return results

    def get_cached(
        self,
        analysis_id: str,
        cache_key: str,
    ) -> dict[str, Any] | None:
        """
        Get cached chart data.

        Args:
            analysis_id: Analysis ID.
            cache_key: Cache key (e.g., 'try_vs_success').

        Returns:
            Cached data dict if found, None otherwise.
        """
        cache = self.cache_repo.get(analysis_id, cache_key)
        if cache is None:
            return None
        return cache.data

    def is_cached(self, analysis_id: str, cache_key: str) -> bool:
        """
        Check if a cache entry exists.

        Args:
            analysis_id: Analysis ID.
            cache_key: Cache key.

        Returns:
            True if cached, False otherwise.
        """
        return self.cache_repo.get(analysis_id, cache_key) is not None

    def get_cache_status(self, analysis_id: str) -> dict[str, bool]:
        """
        Get cache status for all standard charts.

        Args:
            analysis_id: Analysis ID.

        Returns:
            Dict of cache_key -> is_cached.
        """
        all_keys = [
            CacheKeys.TRY_VS_SUCCESS,
            CacheKeys.DISTRIBUTION,
            CacheKeys.HEATMAP,
            CacheKeys.SCATTER,
            CacheKeys.CORRELATIONS,
            CacheKeys.EXTREME_CASES,
            CacheKeys.OUTLIERS,
            CacheKeys.SHAP_SUMMARY,
            CacheKeys.PCA_SCATTER,
            CacheKeys.RADAR_COMPARISON,
        ]

        cached = self.cache_repo.get_all(analysis_id)
        cached_keys = {c.cache_key for c in cached}

        return {key: key in cached_keys for key in all_keys}

    def invalidate(self, analysis_id: str) -> int:
        """
        Invalidate all cache entries for an analysis.

        Args:
            analysis_id: Analysis ID.

        Returns:
            Number of entries invalidated.
        """
        count = self.cache_repo.delete_all(analysis_id)
        self.logger.info(f"Invalidated {count} cache entries for {analysis_id}")
        return count


if __name__ == "__main__":
    import sys
    import tempfile
    from pathlib import Path

    from synth_lab.domain.entities.analysis_run import AnalysisRun
    from synth_lab.domain.entities.experiment import Experiment
    from synth_lab.infrastructure.database import init_database
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

        exp_repo = ExperimentRepository(db)
        ana_repo = AnalysisRepository(db)
        cache_service = AnalysisCacheService(db=db)

        # Create parent experiment and analysis
        exp = Experiment(name="Test", hypothesis="Test hypothesis")
        exp_repo.create(exp)

        analysis = AnalysisRun(experiment_id=exp.id, status="completed")
        ana_repo.create(analysis)

        # Test 1: get_cached returns None for empty cache
        total_tests += 1
        try:
            result = cache_service.get_cached(analysis.id, "try_vs_success")
            if result is not None:
                all_validation_failures.append("get_cached should return None for empty cache")
        except Exception as e:
            all_validation_failures.append(f"get_cached failed: {e}")

        # Test 2: is_cached returns False for empty cache
        total_tests += 1
        try:
            result = cache_service.is_cached(analysis.id, "try_vs_success")
            if result:
                all_validation_failures.append("is_cached should return False for empty cache")
        except Exception as e:
            all_validation_failures.append(f"is_cached failed: {e}")

        # Test 3: get_cache_status shows all uncached
        total_tests += 1
        try:
            status = cache_service.get_cache_status(analysis.id)
            if any(status.values()):
                all_validation_failures.append("get_cache_status should show all uncached")
        except Exception as e:
            all_validation_failures.append(f"get_cache_status failed: {e}")

        # Test 4: pre_compute_all with no outcomes returns empty
        total_tests += 1
        try:
            results = cache_service.pre_compute_all(analysis.id)
            if results:  # Should be empty dict since no outcomes
                all_validation_failures.append(f"pre_compute_all with no outcomes: {results}")
        except Exception as e:
            all_validation_failures.append(f"pre_compute_all failed: {e}")

        # Test 5: invalidate returns 0 for empty cache
        total_tests += 1
        try:
            count = cache_service.invalidate(analysis.id)
            if count != 0:
                all_validation_failures.append(f"invalidate should return 0: {count}")
        except Exception as e:
            all_validation_failures.append(f"invalidate failed: {e}")

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
