"""
Explainability service for UX Research analysis using SHAP and PDP.

Provides SHAP (SHapley Additive exPlanations) for understanding individual
synth predictions and Partial Dependence Plots for understanding feature effects.

References:
    - SHAP: https://github.com/shap/shap
    - SHAP Paper: https://arxiv.org/abs/1705.07874
    - PDP: https://scikit-learn.org/stable/modules/partial_dependence.html

Sample Input:
    outcomes: list[SynthOutcome], synth_id: str

Expected Output:
    ShapExplanation: Feature contributions explaining why synth succeeded/failed
    PDPResult: How changing features affects success probability
"""

import numpy as np
from loguru import logger
from sklearn.ensemble import GradientBoostingRegressor

from synth_lab.domain.entities import ShapContribution, ShapExplanation, ShapSummary, SynthOutcome
from synth_lab.services.simulation.feature_extraction import DEFAULT_FEATURES, extract_features

# Minimum synths required for reliable SHAP analysis
MIN_SYNTHS_FOR_SHAP = 20


class ExplainabilityService:
    """
    Service for generating SHAP explanations and Partial Dependence Plots.

    Trains a GradientBoostingRegressor internally to predict adopted_rate,
    then uses SHAP TreeExplainer for individual explanations and sklearn
    partial_dependence for feature effect analysis.
    """

    def __init__(self):
        """Initialize ExplainabilityService with empty cache."""
        self._model_cache: dict[str, tuple[GradientBoostingRegressor, float]] = {}
        self._shap_values_cache: dict[str, np.ndarray] = {}

    def _train_model(
        self, outcomes: list[SynthOutcome], features: list[str] | None = None
    ) -> tuple[GradientBoostingRegressor, float]:
        """
        Train a GradientBoostingRegressor to predict adopted_rate.

        The model is cached per simulation_id for reuse.

        Args:
            outcomes: List of SynthOutcome entities.
            features: Feature names to use. Defaults to latent traits.

        Returns:
            Tuple of (trained model, R² score).
        """
        if not outcomes:
            raise ValueError("Outcomes list is empty")

        analysis_id = outcomes[0].analysis_id
        cache_key = f"{analysis_id}:{','.join(features or DEFAULT_FEATURES)}"

        # Return cached model if available
        if cache_key in self._model_cache:
            return self._model_cache[cache_key]

        # Extract features
        X, synth_ids, feature_names = extract_features(
            outcomes, features=features, include_outcomes=False
        )

        # Target variable is adopted_rate
        y = np.array([o.adopted_rate for o in outcomes])

        # Train model
        model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            random_state=42,
            validation_fraction=0.1,
            n_iter_no_change=10,
        )
        model.fit(X, y)

        # Calculate R² score
        score = float(model.score(X, y))

        logger.info(
            f"Trained GradientBoostingRegressor for {analysis_id}, "
            f"R²={score:.3f}, features={feature_names}"
        )

        # Cache the model
        self._model_cache[cache_key] = (model, score)

        return model, score

    def explain_synth(
        self,
        simulation_id: str,
        outcomes: list[SynthOutcome],
        synth_id: str,
        features: list[str] | None = None,
    ) -> ShapExplanation:
        """
        Generate SHAP explanation for a specific synth.

        Explains why the synth had its success rate by showing the contribution
        of each feature.

        Args:
            simulation_id: Simulation identifier.
            outcomes: List of all SynthOutcome entities.
            synth_id: ID of the synth to explain.
            features: Feature names to use. Defaults to latent traits.

        Returns:
            ShapExplanation with feature contributions.

        Raises:
            ValueError: If synth not found or not enough synths.
        """
        import shap

        if len(outcomes) < MIN_SYNTHS_FOR_SHAP:
            raise ValueError(
                f"SHAP requires at least {MIN_SYNTHS_FOR_SHAP} synths, got {len(outcomes)}"
            )

        # Find the synth
        target_outcome = None
        target_idx = None
        for idx, outcome in enumerate(outcomes):
            if outcome.synth_id == synth_id:
                target_outcome = outcome
                target_idx = idx
                break

        if target_outcome is None:
            raise ValueError(f"Synth {synth_id} not found in outcomes")

        # Train model
        model, score = self._train_model(outcomes, features)

        # Extract features
        X, synth_ids, feature_names = extract_features(
            outcomes, features=features, include_outcomes=False
        )

        # Get SHAP values using TreeExplainer
        cache_key = f"{simulation_id}:{','.join(features or DEFAULT_FEATURES)}"

        if cache_key not in self._shap_values_cache:
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X)
            self._shap_values_cache[cache_key] = shap_values
        else:
            shap_values = self._shap_values_cache[cache_key]

        # Get values for this specific synth
        synth_shap_values = shap_values[target_idx]
        synth_features = X[target_idx]

        # Calculate baseline (expected value)
        baseline_prediction = float(np.mean([o.adopted_rate for o in outcomes]))

        # Get model prediction
        predicted_adopted_rate = float(model.predict(X[target_idx : target_idx + 1])[0])

        # Build contributions list
        contributions = []
        for i, feature_name in enumerate(feature_names):
            shap_value = float(synth_shap_values[i])
            feature_value = float(synth_features[i])

            # Calculate baseline value for this feature
            feature_baseline = float(np.mean(X[:, i]))

            contributions.append(
                ShapContribution(
                    feature_name=feature_name,
                    feature_value=feature_value,
                    shap_value=shap_value,
                    baseline_value=feature_baseline,
                    impact="positive" if shap_value > 0 else "negative",
                )
            )

        # Sort by absolute SHAP value (most important first)
        contributions.sort(key=lambda c: abs(c.shap_value), reverse=True)

        # Generate explanation text
        explanation_text = self._generate_explanation_text(
            synth_id=synth_id,
            contributions=contributions,
            predicted=predicted_adopted_rate,
            actual=target_outcome.adopted_rate,
            baseline=baseline_prediction,
        )

        return ShapExplanation(
            synth_id=synth_id,
            simulation_id=simulation_id,
            predicted_adopted_rate=predicted_adopted_rate,
            actual_adopted_rate=target_outcome.adopted_rate,
            baseline_prediction=baseline_prediction,
            contributions=contributions,
            explanation_text=explanation_text,
            model_type="gradient_boosting",
        )

    def _generate_explanation_text(
        self,
        synth_id: str,
        contributions: list[ShapContribution],
        predicted: float,
        actual: float,
        baseline: float,
    ) -> str:
        """
        Generate human-readable explanation text from SHAP values.

        Args:
            synth_id: Synth identifier.
            contributions: List of SHAP contributions (sorted by importance).
            predicted: Model's predicted success rate.
            actual: Actual observed success rate.
            baseline: Baseline (average) prediction.

        Returns:
            Human-readable explanation string.
        """
        if not contributions:
            return f"Synth {synth_id} has success rate {actual:.1%}."

        # Take top 3 contributors
        top_contributors = contributions[:3]

        # Build explanation
        parts = []

        # Opening statement
        if actual > baseline:
            parts.append(
                f"Synth {synth_id} performs above average "
                f"(success: {actual:.1%} vs baseline: {baseline:.1%})."
            )
        else:
            parts.append(
                f"Synth {synth_id} performs below average "
                f"(success: {actual:.1%} vs baseline: {baseline:.1%})."
            )

        # Feature contributions
        positive_features = [c for c in top_contributors if c.impact == "positive"]
        negative_features = [c for c in top_contributors if c.impact == "negative"]

        if positive_features:
            feature_names = ", ".join(
                f"{c.feature_name} ({c.feature_value:.2f})" for c in positive_features[:2]
            )
            parts.append(f"Key factors contributing positively: {feature_names}.")

        if negative_features:
            feature_names = ", ".join(
                f"{c.feature_name} ({c.feature_value:.2f})" for c in negative_features[:2]
            )
            parts.append(f"Key factors contributing negatively: {feature_names}.")

        return " ".join(parts)

    def get_shap_summary(
        self, simulation_id: str, outcomes: list[SynthOutcome], features: list[str] | None = None
    ) -> ShapSummary:
        """
        Generate global SHAP summary showing feature importance.

        Computes mean absolute SHAP values across all synths to rank
        features by their overall impact on predictions.

        Args:
            simulation_id: Simulation identifier.
            outcomes: List of all SynthOutcome entities.
            features: Feature names to use. Defaults to latent traits.

        Returns:
            ShapSummary with feature importances.

        Raises:
            ValueError: If not enough synths.
        """
        import shap

        if not outcomes:
            raise ValueError("Outcomes list is empty")

        if len(outcomes) < MIN_SYNTHS_FOR_SHAP:
            raise ValueError(
                f"SHAP requires at least {MIN_SYNTHS_FOR_SHAP} synths, got {len(outcomes)}"
            )

        # Train model
        model, score = self._train_model(outcomes, features)

        # Extract features
        X, synth_ids, feature_names = extract_features(
            outcomes, features=features, include_outcomes=False
        )

        # Get SHAP values
        cache_key = f"{simulation_id}:{','.join(features or DEFAULT_FEATURES)}"

        if cache_key not in self._shap_values_cache:
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X)
            self._shap_values_cache[cache_key] = shap_values
        else:
            shap_values = self._shap_values_cache[cache_key]

        # Calculate mean absolute SHAP values per feature
        mean_abs_shap = np.mean(np.abs(shap_values), axis=0)

        # Build feature importance dict
        feature_importances = {
            feature_names[i]: float(mean_abs_shap[i]) for i in range(len(feature_names))
        }

        # Sort features by importance
        sorted_features = sorted(
            feature_importances.keys(), key=lambda f: feature_importances[f], reverse=True
        )

        # Top 10 features
        top_features = sorted_features[:10]

        return ShapSummary(
            simulation_id=simulation_id,
            feature_importances=feature_importances,
            top_features=top_features,
            total_synths=len(outcomes),
            model_score=score,
        )

    # =============================================================================
    # Router-compatible wrapper methods
    # =============================================================================

    def get_shap_explanation(
        self,
        simulation_id: str,
        outcomes: list[SynthOutcome],
        synth_id: str,
        features: list[str] | None = None,
    ) -> ShapExplanation:
        """Wrapper for explain_synth for API router compatibility."""
        return self.explain_synth(
            simulation_id=simulation_id, outcomes=outcomes, synth_id=synth_id, features=features
        )


# =============================================================================
# Validation
# =============================================================================

if __name__ == "__main__":
    import sys

    from synth_lab.domain.entities.simulation_attributes import (
        SimulationAttributes,
        SimulationLatentTraits,
        SimulationObservables,
    )

    all_validation_failures: list[str] = []
    total_tests = 0

    # Create sample outcomes
    np.random.seed(42)
    outcomes = []

    for i in range(50):
        capability = 0.3 + np.random.rand() * 0.6
        trust = 0.2 + np.random.rand() * 0.7
        friction = 0.2 + np.random.rand() * 0.6
        exploration = 0.3 + np.random.rand() * 0.4

        base_success = 0.3 * capability + 0.4 * trust + 0.2 * friction
        noise = np.random.randn() * 0.1
        adopted_rate = np.clip(base_success + noise, 0.05, 0.95)
        not_adopted_rate = round(1.0 - adopted_rate, 3)

        outcomes.append(
            SynthOutcome(
                synth_id=f"synth_{i:03d}",
                simulation_id="sim_test",
                adopted_rate=adopted_rate,
                not_adopted_rate=not_adopted_rate,
                synth_attributes=SimulationAttributes(
                    observables=SimulationObservables(
                        digital_literacy=0.5,
                        similar_tool_experience=0.5,
                        motor_ability=0.5,
                        time_availability=0.5,
                        domain_expertise=0.5,
                    ),
                    latent_traits=SimulationLatentTraits(
                        capability_mean=capability,
                        trust_mean=trust,
                        friction_tolerance_mean=friction,
                        exploration_prob=exploration,
                    ),
                ),
            )
        )

    service = ExplainabilityService()

    # Test 1: Train model
    total_tests += 1
    try:
        model, score = service._train_model(outcomes)
        if model is None:
            all_validation_failures.append("Model is None")
        if not (0.0 <= score <= 1.0):
            all_validation_failures.append(f"Invalid R² score: {score}")
        else:
            print(f"Test 1 PASSED: Model trained, R²={score:.3f}")
    except Exception as e:
        all_validation_failures.append(f"Train model failed: {e}")

    # Test 2: SHAP explanation
    total_tests += 1
    try:
        explanation = service.explain_synth(
            simulation_id="sim_test", outcomes=outcomes, synth_id="synth_010"
        )
        if not explanation.contributions:
            all_validation_failures.append("No contributions in explanation")
        if explanation.explanation_text == "":
            all_validation_failures.append("Empty explanation text")
        else:
            print(
                f"Test 2 PASSED: SHAP explanation generated, {len(explanation.contributions)} features"
            )
    except Exception as e:
        all_validation_failures.append(f"SHAP explanation failed: {e}")

    # Test 3: SHAP summary
    total_tests += 1
    try:
        summary = service.get_shap_summary(simulation_id="sim_test", outcomes=outcomes)
        if not summary.feature_importances:
            all_validation_failures.append("No feature importances")
        if not summary.top_features:
            all_validation_failures.append("No top features")
        else:
            print(f"Test 3 PASSED: SHAP summary, top feature: {summary.top_features[0]}")
    except Exception as e:
        all_validation_failures.append(f"SHAP summary failed: {e}")

    # Test 4: Synth not found error
    total_tests += 1
    try:
        service.explain_synth(simulation_id="sim_test", outcomes=outcomes, synth_id="nonexistent")
        all_validation_failures.append("Should have raised ValueError for nonexistent synth")
    except ValueError as e:
        if "not found" in str(e):
            print("Test 7 PASSED: Correct error for nonexistent synth")
        else:
            all_validation_failures.append(f"Wrong error message: {e}")
    except Exception as e:
        all_validation_failures.append(f"Wrong exception type: {e}")

    # Final result
    print()
    if all_validation_failures:
        failed = len(all_validation_failures)
        print(f"❌ VALIDATION FAILED - {failed} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
