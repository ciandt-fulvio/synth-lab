"""
Analysis Execution Service for synth-lab.

Executes Monte Carlo simulation for experiment analysis.
Converts experiment's embedded scorecard to simulation format and runs engine.

References:
    - Spec: specs/019-experiment-refactor/spec.md
    - Engine: src/synth_lab/services/simulation/engine.py
"""

import asyncio
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loguru import logger

from synth_lab.domain.entities import Scenario
from synth_lab.domain.entities.analysis_run import (
    AggregatedOutcomes,
    AnalysisConfig,
    AnalysisRun,
)
from synth_lab.domain.entities.experiment import Experiment
from synth_lab.domain.entities.feature_scorecard import (
    FeatureScorecard,
    ScorecardDimension,
    ScorecardIdentification,
)
from synth_lab.infrastructure.database import DatabaseManager, get_database
from synth_lab.repositories.analysis_outcome_repository import AnalysisOutcomeRepository
from synth_lab.repositories.analysis_repository import AnalysisRepository
from synth_lab.repositories.experiment_repository import ExperimentRepository
from synth_lab.services.simulation.engine import MonteCarloEngine


class AnalysisExecutionService:
    """Service for executing experiment analysis with Monte Carlo simulation."""

    def __init__(
        self,
        db: DatabaseManager | None = None,
        analysis_repo: AnalysisRepository | None = None,
        experiment_repo: ExperimentRepository | None = None,
        outcome_repo: AnalysisOutcomeRepository | None = None,
    ):
        self.db = db or get_database()
        self.analysis_repo = analysis_repo or AnalysisRepository(self.db)
        self.experiment_repo = experiment_repo or ExperimentRepository(self.db)
        self.outcome_repo = outcome_repo or AnalysisOutcomeRepository(self.db)
        self.logger = logger.bind(component="analysis_execution_service")

    def execute_analysis(
        self,
        experiment_id: str,
        config: AnalysisConfig | None = None,
    ) -> AnalysisRun:
        """
        Execute a Monte Carlo analysis for an experiment.

        Workflow:
        1. Validate experiment exists and has scorecard
        2. Delete existing analysis if present
        3. Create new analysis with "running" status
        4. Load synths from database
        5. Convert experiment scorecard to simulation format
        6. Execute Monte Carlo simulation
        7. Save synth outcomes
        8. Update analysis with results

        Args:
            experiment_id: Experiment ID to analyze
            config: Optional analysis configuration

        Returns:
            Completed AnalysisRun with results

        Raises:
            ValueError: If experiment not found or has no scorecard
        """
        self.logger.info(f"Starting analysis for experiment {experiment_id}")

        # Validate experiment
        experiment = self.experiment_repo.get_by_id(experiment_id)
        if experiment is None:
            raise ValueError(f"Experimento não encontrado: {experiment_id}")

        if not experiment.has_scorecard():
            raise ValueError(
                f"O experimento '{experiment.name}' precisa ter um scorecard configurado. "
                "Edite o experimento e preencha o scorecard antes de executar a análise."
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
            total_synths=len(synths),
        )
        self.analysis_repo.create(analysis)

        try:
            # Convert experiment scorecard to simulation format
            scorecard = self._convert_scorecard(experiment)
            scenario = self._load_default_scenario()

            # Execute Monte Carlo simulation
            import time

            start_time = time.time()
            engine = MonteCarloEngine(seed=config.seed, sigma=config.sigma)
            results = engine.run_simulation(
                synths=synths,
                scorecard=scorecard,
                scenario=scenario,
                n_executions=config.n_executions,
            )
            execution_time = time.time() - start_time

            # Save outcomes
            outcome_dicts = [
                {
                    "synth_id": o.synth_id,
                    "did_not_try_rate": o.did_not_try_rate,
                    "failed_rate": o.failed_rate,
                    "success_rate": o.success_rate,
                    "synth_attributes": o.synth_attributes,
                }
                for o in results.synth_outcomes
            ]
            self.outcome_repo.save_outcomes(analysis.id, outcome_dicts)

            # Update analysis with results
            aggregated = AggregatedOutcomes(
                did_not_try_rate=results.aggregated_did_not_try,
                failed_rate=results.aggregated_failed,
                success_rate=results.aggregated_success,
            )

            updated_analysis = self.analysis_repo.update_status(
                analysis_id=analysis.id,
                status="completed",
                completed_at=datetime.now(timezone.utc),
                total_synths=results.total_synths,
                aggregated_outcomes=aggregated,
                execution_time_seconds=execution_time,
            )

            self.logger.info(
                f"Analysis {analysis.id} completed in {execution_time:.2f}s "
                f"with {results.total_synths} synths"
            )

            # Pre-compute chart cache for fast retrieval
            self._pre_compute_cache(analysis.id)

            return updated_analysis or analysis

        except Exception as e:
            self.logger.error(f"Analysis {analysis.id} failed: {e}")
            self.analysis_repo.update_status(
                analysis_id=analysis.id,
                status="failed",
                completed_at=datetime.now(timezone.utc),
            )
            raise

    def _load_synths(self, limit: int = 500) -> list[dict[str, Any]]:
        """Load synths from database with simulation attributes.

        For v2.3.0+ synths: Uses pre-computed observables from synth.data
        and derives latent_traits at simulation time.

        For legacy synths: Generates default observables based on Big Five.
        """
        from synth_lab.domain.entities.simulation_attributes import (
            SimulationObservables,
        )
        from synth_lab.gen_synth.simulation_attributes import derive_latent_traits

        sql = """
            SELECT id, nome, data
            FROM synths
            WHERE data IS NOT NULL
            LIMIT ?
        """
        rows = self.db.fetchall(sql, (limit,))

        synths = []
        for row in rows:
            data = json.loads(row["data"]) if row["data"] else {}

            # Extract simulation_attributes if present (new format with latent_traits)
            sim_attrs = data.get("simulation_attributes", {})

            # If already has complete simulation_attributes, use directly
            if sim_attrs.get("latent_traits") and sim_attrs.get("observables"):
                synths.append(
                    {
                        "id": row["id"],
                        "nome": row["nome"],
                        "simulation_attributes": sim_attrs,
                    }
                )
                continue

            # Check if synth has pre-computed observables (v2.3.0+)
            existing_observables = data.get("observables")
            if existing_observables and all(
                k in existing_observables
                for k in [
                    "digital_literacy",
                    "similar_tool_experience",
                    "motor_ability",
                    "time_availability",
                    "domain_expertise",
                ]
            ):
                # Use existing observables and derive latent traits
                observables = SimulationObservables.model_validate(existing_observables)
                latent_traits = derive_latent_traits(observables)

                sim_attrs = {
                    "observables": observables.model_dump(),
                    "latent_traits": latent_traits.model_dump(),
                }
            else:
                # Legacy synth - derive from Big Five personality traits
                big_five = data.get("psicografia", {}).get("personalidade_big_five", {})
                openness = big_five.get("abertura", 50) / 100
                conscientiousness = big_five.get("conscienciosidade", 50) / 100
                extraversion = big_five.get("extroversao", 50) / 100
                agreeableness = big_five.get("amabilidade", 50) / 100
                neuroticism = big_five.get("neuroticismo", 50) / 100

                # Derive latent traits from Big Five
                capability_mean = round(0.5 * openness + 0.5 * conscientiousness, 3)
                trust_mean = round(0.6 * agreeableness + 0.4 * (1 - neuroticism), 3)
                friction_tolerance = 0.5 * conscientiousness + 0.5 * (1 - neuroticism)
                friction_tolerance_mean = round(friction_tolerance, 3)
                exploration_prob = round(0.6 * openness + 0.4 * extraversion, 3)

                sim_attrs = {
                    "observables": {
                        "digital_literacy": round(openness * 0.7 + conscientiousness * 0.3, 3),
                        "similar_tool_experience": 0.5,  # Default
                        "motor_ability": 1.0,  # Default (no disability)
                        "time_availability": round(1 - neuroticism * 0.3, 3),
                        "domain_expertise": 0.5,  # Default
                    },
                    "latent_traits": {
                        "capability_mean": capability_mean,
                        "trust_mean": trust_mean,
                        "friction_tolerance_mean": friction_tolerance_mean,
                        "exploration_prob": exploration_prob,
                    },
                }

            synths.append(
                {
                    "id": row["id"],
                    "nome": row["nome"],
                    "simulation_attributes": sim_attrs,
                }
            )

        return synths

    def _convert_scorecard(self, experiment: Experiment) -> FeatureScorecard:
        """Convert experiment's embedded scorecard to FeatureScorecard entity."""
        sc = experiment.scorecard_data
        if sc is None:
            raise ValueError("Experiment has no scorecard data")

        return FeatureScorecard(
            experiment_id=experiment.id,
            identification=ScorecardIdentification(
                feature_name=sc.feature_name,
                use_scenario=sc.scenario if sc.scenario else "baseline",
            ),
            description_text=sc.description_text,
            complexity=ScorecardDimension(
                score=sc.complexity.score,
                rules_applied=sc.complexity.rules_applied or [],
            ),
            initial_effort=ScorecardDimension(
                score=sc.initial_effort.score,
                rules_applied=sc.initial_effort.rules_applied or [],
            ),
            perceived_risk=ScorecardDimension(
                score=sc.perceived_risk.score,
                rules_applied=sc.perceived_risk.rules_applied or [],
            ),
            time_to_value=ScorecardDimension(
                score=sc.time_to_value.score,
                rules_applied=sc.time_to_value.rules_applied or [],
            ),
            justification=sc.justification,
            impact_hypotheses=sc.impact_hypotheses or [],
        )

    def _load_default_scenario(self) -> Scenario:
        """Load the baseline scenario for analysis."""
        return self._default_scenario("baseline")

    def _load_all_scenarios(self) -> list[Scenario]:
        """Load all scenarios (baseline, crisis, first-use) from JSON file."""
        scenario_ids = ["baseline", "crisis", "first-use"]
        scenarios_path = Path("data/scenarios.json")

        if scenarios_path.exists():
            with open(scenarios_path) as f:
                data = json.load(f)
                scenarios_data = data.get("scenarios", [])

                loaded = []
                for sid in scenario_ids:
                    for s in scenarios_data:
                        if s.get("id") == sid:
                            loaded.append(Scenario.model_validate(s))
                            break
                    else:
                        # Scenario not found, use default
                        loaded.append(self._default_scenario(sid))

                return loaded

        # Default scenarios if file not found
        return [self._default_scenario(sid) for sid in scenario_ids]

    def _default_scenario(self, scenario_id: str) -> Scenario:
        """Create a default scenario by ID."""
        defaults = {
            "baseline": {
                "name": "Baseline",
                "description": "Standard adoption scenario",
                "motivation_modifier": 0.0,
                "trust_modifier": 0.0,
                "friction_modifier": 0.0,
                "task_criticality": 0.5,
            },
            "crisis": {
                "name": "Crisis",
                "description": "High urgency scenario",
                "motivation_modifier": 0.2,
                "trust_modifier": -0.1,
                "friction_modifier": -0.15,
                "task_criticality": 0.85,
            },
            "first-use": {
                "name": "First Use",
                "description": "Initial exploration scenario",
                "motivation_modifier": 0.1,
                "trust_modifier": -0.2,
                "friction_modifier": 0.0,
                "task_criticality": 0.2,
            },
        }
        cfg = defaults.get(scenario_id, defaults["baseline"])
        return Scenario(
            id=scenario_id,
            name=cfg["name"],
            description=cfg["description"],
            motivation_modifier=cfg["motivation_modifier"],
            trust_modifier=cfg["trust_modifier"],
            friction_modifier=cfg["friction_modifier"],
            task_criticality=cfg["task_criticality"],
            w_complexity=0.25,
            w_effort=0.25,
            w_risk=0.25,
            w_time_to_value=0.25,
        )

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
                from synth_lab.services.analysis.analysis_cache_service import (
                    AnalysisCacheService,
                )

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
            from synth_lab.repositories.analysis_cache_repository import (
                AnalysisCacheRepository,
            )
            from synth_lab.services.executive_summary_service import (
                ExecutiveSummaryService,
            )
            from synth_lab.services.insight_service import InsightService

            cache_repo = AnalysisCacheRepository()
            insight_service = InsightService(cache_repo=cache_repo)
            summary_service = ExecutiveSummaryService(cache_repo=cache_repo)

            # Map chart_type to cache_key (only charts with pre-computed cache)
            from synth_lab.domain.entities.analysis_cache import CacheKeys

            CHART_TYPE_TO_CACHE_KEY = {
                "try_vs_success": CacheKeys.TRY_VS_SUCCESS,
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
                summary = summary_service.generate_summary(analysis_id)
                logger_ref.info(
                    f"Generated executive summary for {analysis_id}: {summary.status}"
                )
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
        service = AnalysisExecutionService(db)
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
