"""
Analysis Cache entity for synth-lab.

Represents pre-computed chart data cached after analysis completion.
Cache is invalidated automatically when analysis is re-run (CASCADE delete).

References:
    - Spec: Cache automático pós-análise
    - Related: analysis_run.py, chart_data_service.py
"""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class AnalysisCache(BaseModel):
    """
    Pre-computed chart data for an analysis.

    Attributes:
        analysis_id: Parent analysis ID
        cache_key: Unique key for this cache entry (e.g., 'try_vs_success')
        data: Serialized chart data (dict that will be JSON-encoded)
        params: Optional parameters used for computation (for cache invalidation)
        computed_at: When this cache entry was created
    """

    analysis_id: str = Field(
        pattern=r"^ana_[a-f0-9]{8}$",
        description="Parent analysis ID.",
    )

    cache_key: str = Field(
        min_length=1,
        max_length=50,
        description="Cache key identifying the data type.",
    )

    data: dict[str, Any] = Field(
        description="Pre-computed chart data.",
    )

    params: dict[str, Any] | None = Field(
        default=None,
        description="Parameters used for computation.",
    )

    computed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this cache entry was created.",
    )


# Standard cache keys for charts
class CacheKeys:
    """Standard cache keys for pre-computed data."""

    # Phase 1: Overview
    TRY_VS_SUCCESS = "try_vs_success"
    DISTRIBUTION = "distribution"

    # Phase 2: Problem Location
    HEATMAP = "heatmap"
    SCATTER = "scatter"
    CORRELATIONS = "correlations"

    # Phase 3: Segmentation (dynamic - clustering_k{n})
    @staticmethod
    def clustering(k: int) -> str:
        return f"clustering_k{k}"

    ELBOW = "elbow"
    PCA_SCATTER = "pca_scatter"
    RADAR_COMPARISON = "radar_comparison"

    # Phase 4: Edge Cases
    EXTREME_CASES = "extreme_cases"
    OUTLIERS = "outliers"

    # Phase 5: Explainability
    SHAP_SUMMARY = "shap_summary"

    # AI-Generated Insights (Individual Charts)
    INSIGHT_TRY_VS_SUCCESS = "insight_try_vs_success"
    INSIGHT_SHAP_SUMMARY = "insight_shap_summary"
    INSIGHT_PDP = "insight_pdp"
    INSIGHT_PCA_SCATTER = "insight_pca_scatter"
    INSIGHT_RADAR_COMPARISON = "insight_radar_comparison"
    INSIGHT_EXTREME_CASES = "insight_extreme_cases"
    INSIGHT_OUTLIERS = "insight_outliers"

    # AI-Generated Executive Summary
    EXECUTIVE_SUMMARY = "executive_summary"


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Create cache entry
    total_tests += 1
    try:
        cache = AnalysisCache(
            analysis_id="ana_12345678",
            cache_key="try_vs_success",
            data={"quadrants": [], "summary": {}},
        )
        if cache.cache_key != "try_vs_success":
            all_validation_failures.append(f"cache_key mismatch: {cache.cache_key}")
        if cache.params is not None:
            all_validation_failures.append("params should be None by default")
    except Exception as e:
        all_validation_failures.append(f"Create cache entry failed: {e}")

    # Test 2: Create with params
    total_tests += 1
    try:
        cache = AnalysisCache(
            analysis_id="ana_12345678",
            cache_key="heatmap",
            data={"bins": []},
            params={"x_axis": "digital_literacy", "y_axis": "trust_mean"},
        )
        if cache.params is None:
            all_validation_failures.append("params should not be None")
        if cache.params.get("x_axis") != "digital_literacy":
            all_validation_failures.append("params x_axis mismatch")
    except Exception as e:
        all_validation_failures.append(f"Create with params failed: {e}")

    # Test 3: CacheKeys helper
    total_tests += 1
    try:
        key = CacheKeys.clustering(5)
        if key != "clustering_k5":
            all_validation_failures.append(f"clustering key mismatch: {key}")
    except Exception as e:
        all_validation_failures.append(f"CacheKeys helper failed: {e}")

    # Test 4: Invalid analysis_id format
    total_tests += 1
    try:
        AnalysisCache(
            analysis_id="invalid",
            cache_key="test",
            data={},
        )
        all_validation_failures.append("Should reject invalid analysis_id format")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for invalid analysis_id: {e}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
