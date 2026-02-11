"""
Analysis Execution Service for synth-lab.

Executes Monte Carlo simulation for experiment analysis using the
mechanism-based feature_monte_carlo engine.

References:
    - Spec: specs/040-mechanism-sensitivity-update/spec.md
    - Engine: src/synth_lab/services/simulation/feature_monte_carlo.py
"""

import asyncio
import threading
from datetime import datetime, timezone
from typing import Any

from loguru import logger

from synth_lab.domain.entities.analysis_run import AggregatedOutcomes, AnalysisConfig, AnalysisRun
from synth_lab.repositories.analysis_outcome_repository import AnalysisOutcomeRepository
from synth_lab.repositories.analysis_repository import AnalysisRepository
from synth_lab.repositories.experiment_repository import ExperimentRepository
from synth_lab.services.simulation.feature_monte_carlo import run_simulation


class AnalysisExecutionService:
    """Service for executing experiment analysis with Monte Carlo simulation."""

    def __init__(
        self,
        analysis_repo: AnalysisRepository | None = None,
        experiment_repo: ExperimentRepository | None = None,
        outcome_repo: AnalysisOutcomeRepository | None = None):
        self.analysis_repo = analysis_repo or AnalysisRepository()
        self.experiment_repo = experiment_repo or ExperimentRepository()
        self.outcome_repo = outcome_repo or AnalysisOutcomeRepository()
        self.logger = logger.bind(component="analysis_execution_service")

    def execute_analysis(
        self,
        experiment_id: str,
        config: AnalysisConfig | None = None) -> AnalysisRun:
        """
        Execute a Monte Carlo analysis for an experiment.

        Workflow:
        1. Validate experiment exists and has mechanisms
        2. Delete existing analysis if present
        3. Create new analysis with "running" status
        4. Load synths from database
        5. Execute mechanism-based Monte Carlo simulation
        6. Save synth outcomes
        7. Update analysis with results

        Args:
            experiment_id: Experiment ID to analyze
            config: Optional analysis configuration

        Returns:
            Completed AnalysisRun with results

        Raises:
            ValueError: If experiment not found or has no mechanisms
        """
        self.logger.info(f"Starting analysis for experiment {experiment_id}")

        # Validate experiment
        experiment = self.experiment_repo.get_by_id(experiment_id)
        if experiment is None:
            raise ValueError(f"Experimento não encontrado: {experiment_id}")

        # Extract mechanisms from scorecard_data
        mechanisms = None
        if experiment.scorecard_data and experiment.scorecard_data.mechanisms:
            mechanisms = experiment.scorecard_data.mechanisms

        if mechanisms is None or not mechanisms.has_any_mechanism():
            raise ValueError(
                f"O experimento '{experiment.name}' precisa ter mecanismos configurados."
            )

        # Delete existing analysis if present
        existing = self.analysis_repo.get_by_experiment_id(experiment_id)
        if existing:
            self.outcome_repo.delete_outcomes(existing.id)
            self.analysis_repo.delete(existing.id)
            self.logger.info(f"Deleted existing analysis {existing.id}")

        # Use default config if not provided
        if config is None:
            config = AnalysisConfig()

        # Load synths
        synths = self._load_synths(limit=config.n_synths)
        if not synths:
            raise ValueError(
                "Nenhum synth encontrado para análise. "
                "Gere personas sintéticas antes de executar a análise."
            )

        self.logger.info(f"Loaded {len(synths)} synths for analysis")

        # Create analysis run
        analysis = AnalysisRun(
            experiment_id=experiment_id,
            config=config,
            status="running",
            started_at=datetime.now(timezone.utc),
            total_synths=len(synths))
        self.analysis_repo.create(analysis)

        try:
            # Execute Monte Carlo simulation
            import time

            start_time = time.time()
            results = run_simulation(
                synths=synths,
                mechanisms=mechanisms,
                n_executions=config.n_executions,
                seed=config.seed,
            )
            execution_time = time.time() - start_time

            # Convert to outcome dicts
            synths_by_id = {s["id"]: s for s in synths}
            outcome_dicts = []
            for mc_outcome in results.outcomes:
                synth_data = synths_by_id[mc_outcome.synth_id]

                # Build synth_attributes: include sensitivities alongside legacy attrs
                synth_attrs = dict(synth_data.get("simulation_attributes", {}))
                if synth_data.get("sensitivities") and "sensitivities" not in synth_attrs:
                    synth_attrs["sensitivities"] = synth_data["sensitivities"]

                outcome_dicts.append({
                    "synth_id": mc_outcome.synth_id,
                    "adopted_rate": mc_outcome.adoption_rate,
                    "not_adopted_rate": round(1.0 - mc_outcome.adoption_rate, 4),
                    "synth_attributes": synth_attrs,
                })
            self.outcome_repo.save_outcomes(analysis.id, outcome_dicts)

            # Update analysis with results
            aggregated = AggregatedOutcomes(
                adopted_rate=results.aggregate_adoption_rate,
                not_adopted_rate=round(1.0 - results.aggregate_adoption_rate, 4))

            updated_analysis = self.analysis_repo.update_status(
                analysis_id=analysis.id,
                status="completed",
                completed_at=datetime.now(timezone.utc),
                total_synths=results.n_synths,
                aggregated_outcomes=aggregated,
                execution_time_seconds=execution_time)

            self.logger.info(
                f"Analysis {analysis.id} completed in {execution_time:.2f}s "
                f"with {results.n_synths} synths"
            )

            # Pre-compute chart cache for fast retrieval
            self._pre_compute_cache(analysis.id)

            return updated_analysis or analysis

        except Exception as e:
            self.logger.error(f"Analysis {analysis.id} failed: {e}")
            self.analysis_repo.update_status(
                analysis_id=analysis.id,
                status="failed",
                completed_at=datetime.now(timezone.utc))
            raise

    def _load_synths(self, limit: int = 500) -> list[dict[str, Any]]:
        """Load synths from database with sensitivities and demographics.

        The new engine's ``_get_sensitivities()`` handles both:
        - v3.1.0 synths: stored sensitivities used directly
        - Legacy synths: derives sensitivities from demographics
        """
        from sqlalchemy import select

        from synth_lab.infrastructure.database_v2 import get_session
        from synth_lab.models.orm.synth import Synth as SynthORM

        with get_session() as session:
            stmt = select(SynthORM).where(SynthORM.data.isnot(None)).limit(limit)
            orm_synths = list(session.execute(stmt).scalars().all())

        synths = []
        for orm_synth in orm_synths:
            data = orm_synth.data if isinstance(orm_synth.data, dict) else {}

            synths.append({
                "id": orm_synth.id,
                "nome": orm_synth.nome,
                "sensitivities": data.get("sensitivities"),
                "demografia": data.get("demografia"),
                "psicografia": data.get("psicografia"),
                "simulation_attributes": data.get("simulation_attributes", {}),
            })

        return synths

    def _pre_compute_cache(self, analysis_id: str) -> None:
        """
        Pre-compute chart cache for an analysis in background thread.

        Runs asynchronously after analysis completes to populate cache.
        Uses a separate thread to avoid blocking the response.
        Failures are logged but don't affect the analysis result.

        Args:
            analysis_id: Analysis ID to cache charts for.
        """
        logger_ref = self.logger  # Capture logger for thread

        def _compute_in_background() -> None:
            try:
                from synth_lab.services.analysis.analysis_cache_service import AnalysisCacheService

                # Create fresh cache service (with new DB connection for thread safety)
                cache_service = AnalysisCacheService()
                results = cache_service.pre_compute_all(analysis_id)

                success_count = sum(1 for v in results.values() if v)
                logger_ref.info(
                    f"Pre-computed {success_count}/{len(results)} chart caches for {analysis_id}"
                )

                # Trigger insight generation after cache is ready
                self._trigger_insight_generation(analysis_id)
            except Exception as e:
                # Cache failures shouldn't affect the analysis result
                logger_ref.warning(f"Failed to pre-compute cache for {analysis_id}: {e}")

        thread = threading.Thread(target=_compute_in_background, daemon=True)
        thread.start()
        self.logger.debug(f"Started background cache pre-computation for {analysis_id}")

    def _trigger_insight_generation(self, analysis_id: str) -> None:
        """
        Trigger AI insight generation for all charts after cache is ready.

        Runs in background thread (daemon) to generate chart insights and executive summary.
        Uses asyncio for parallel LLM calls to minimize total generation time.
        Failures are logged but don't affect the analysis result.

        Args:
            analysis_id: Analysis ID to generate insights for.

        References:
            - Spec: specs/023-quantitative-ai-insights/spec.md (US3, automatic generation)
            - Service: src/synth_lab/services/insight_service.py
            - Service: src/synth_lab/services/executive_summary_service.py
        """
        logger_ref = self.logger  # Capture logger for thread

        def _generate_in_background() -> None:
            try:
                # Run async insight generation
                asyncio.run(self._generate_insights_parallel(analysis_id))
            except Exception as e:
                logger_ref.warning(f"Failed to generate insights for {analysis_id}: {e}")

        thread = threading.Thread(target=_generate_in_background, daemon=True)
        thread.start()
        logger_ref.info(f"Started background insight generation for {analysis_id}")

    async def _generate_insights_parallel(self, analysis_id: str) -> None:
        """
        Generate insights for all 7 chart types in parallel using asyncio.

        Creates concurrent tasks for each chart type to minimize total generation time.
        After all insights complete, generates executive summary.

        Args:
            analysis_id: Analysis ID to generate insights for.

        References:
            - Spec: specs/023-quantitative-ai-insights/spec.md (US3, parallel generation)
        """
        logger_ref = self.logger

        try:
            from synth_lab.repositories.analysis_cache_repository import AnalysisCacheRepository
            from synth_lab.services.executive_summary_service import ExecutiveSummaryService
            from synth_lab.services.insight_service import InsightService

            cache_repo = AnalysisCacheRepository()
            insight_service = InsightService(cache_repo=cache_repo)
            summary_service = ExecutiveSummaryService(cache_repo=cache_repo)

            # Map chart_type to cache_key (only charts with pre-computed cache)
            from synth_lab.domain.entities.analysis_cache import CacheKeys

            CHART_TYPE_TO_CACHE_KEY = {
                "shap_summary": CacheKeys.SHAP_SUMMARY,
                "extreme_cases": CacheKeys.EXTREME_CASES,
                "outliers": CacheKeys.OUTLIERS,
                "pca_scatter": CacheKeys.PCA_SCATTER,
                "radar_comparison": CacheKeys.RADAR_COMPARISON,
            }

            # Filter to only charts that actually exist in cache
            cached_entries = cache_repo.get_all(analysis_id)
            cached_keys = {entry.cache_key for entry in cached_entries}

            chart_types = [
                chart_type
                for chart_type, cache_key in CHART_TYPE_TO_CACHE_KEY.items()
                if cache_key in cached_keys
            ]

            skipped = [
                chart_type
                for chart_type, cache_key in CHART_TYPE_TO_CACHE_KEY.items()
                if cache_key not in cached_keys
            ]
            if skipped:
                logger_ref.debug(
                    f"Skipping insights for charts not in cache: {skipped}"
                )

            logger_ref.info(
                f"Generating insights for {len(chart_types)} charts: {analysis_id}"
            )

            # Generate all insights in parallel
            async def generate_single_insight(chart_type: str) -> None:
                try:
                    # Get cache key for this chart type
                    cache_key = CHART_TYPE_TO_CACHE_KEY.get(chart_type)
                    if cache_key is None:
                        logger_ref.warning(f"No cache key mapping for {chart_type}, skipping")
                        return

                    # Get chart data from cache
                    cache_entry = cache_repo.get(analysis_id, cache_key)
                    if cache_entry is None:
                        logger_ref.warning(
                            f"No cache entry for {cache_key} in analysis {analysis_id}, skipping"
                        )
                        return

                    chart_data = cache_entry.data

                    # Generate insight
                    insight = insight_service.generate_insight(
                        analysis_id, chart_type, chart_data
                    )
                    logger_ref.info(
                        f"Generated {chart_type} insight for {analysis_id}: {insight.status}"
                    )
                except Exception as e:
                    logger_ref.error(f"Failed to generate {chart_type} insight: {e}")

            # Run all tasks in parallel
            tasks = [generate_single_insight(ct) for ct in chart_types]
            await asyncio.gather(*tasks, return_exceptions=True)

            logger_ref.info(f"All chart insights completed for {analysis_id}")

            # Generate executive summary after all insights
            try:
                # Get experiment_id from analysis_run
                analysis_run = self.analysis_repo.get_by_id(analysis_id)
                if not analysis_run:
                    logger_ref.error(f"Analysis run not found: {analysis_id}")
                    return

                experiment_id = analysis_run.experiment_id

                # Generate markdown summary (saves to experiment_documents)
                summary_service.generate_markdown_summary(experiment_id, analysis_id)
                logger_ref.info(f"Generated executive summary for {experiment_id}/{analysis_id}")
            except Exception as e:
                logger_ref.error(f"Failed to generate executive summary: {e}")

        except Exception as e:
            logger_ref.error(f"Insight generation failed for {analysis_id}: {e}")


if __name__ == "__main__":
    import sys

    all_validation_failures: list[str] = []
    total_tests = 0

    # Test 1: Service initialization
    total_tests += 1
    try:
        db = get_database()
        service = AnalysisExecutionService()
        if service is None:
            all_validation_failures.append("Service initialization failed")
    except Exception as e:
        all_validation_failures.append(f"Service init failed: {e}")

    # Test 2: Execute analysis for non-existent experiment
    total_tests += 1
    try:
        service.execute_analysis("nonexistent_exp")
        all_validation_failures.append("Should raise ValueError for non-existent experiment")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error: {e}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
