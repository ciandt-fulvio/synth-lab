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
from sklearn.inspection import partial_dependence

from synth_lab.domain.entities import (
    PDPComparison,
    PDPPoint,
    PDPResult,
    ShapContribution,
    ShapExplanation,
    ShapSummary,
    SynthOutcome)
from synth_lab.services.simulation.feature_extraction import (
    DEFAULT_FEATURES,
    extract_features,
    get_attribute_value)

# Minimum synths required for reliable SHAP analysis
MIN_SYNTHS_FOR_SHAP = 20


class ExplainabilityService:
    """
    Service for generating SHAP explanations and Partial Dependence Plots.

    Trains a GradientBoostingRegressor internally to predict success_rate,
    then uses SHAP TreeExplainer for individual explanations and sklearn
    partial_dependence for feature effect analysis.
    """

    def __init__(self):
        """Initialize ExplainabilityService with empty cache."""
        self._model_cache: dict[str, tuple[GradientBoostingRegressor, float]] = {}
        self._shap_values_cache: dict[str, np.ndarray] = {}

    def _train_model(
        self,
        outcomes: list[SynthOutcome],
        features: list[str] | None = None) -> tuple[GradientBoostingRegressor, float]:
        """
        Train a GradientBoostingRegressor to predict success_rate.

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
            outcomes,
            features=features,
            include_outcomes=False)

        # Target variable is success_rate
        y = np.array([o.success_rate for o in outcomes])

        # Train model
        model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            random_state=42,
            validation_fraction=0.1,
            n_iter_no_change=10)
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
        features: list[str] | None = None) -> ShapExplanation:
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
            outcomes,
            features=features,
            include_outcomes=False)

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
        baseline_prediction = float(np.mean([o.success_rate for o in outcomes]))

        # Get model prediction
        predicted_success_rate = float(model.predict(X[target_idx : target_idx + 1])[0])

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
                    impact="positive" if shap_value > 0 else "negative")
            )

        # Sort by absolute SHAP value (most important first)
        contributions.sort(key=lambda c: abs(c.shap_value), reverse=True)

        # Generate explanation text
        explanation_text = self._generate_explanation_text(
            synth_id=synth_id,
            contributions=contributions,
            predicted=predicted_success_rate,
            actual=target_outcome.success_rate,
            baseline=baseline_prediction)

        return ShapExplanation(
            synth_id=synth_id,
            simulation_id=simulation_id,
            predicted_success_rate=predicted_success_rate,
            actual_success_rate=target_outcome.success_rate,
            baseline_prediction=baseline_prediction,
            contributions=contributions,
            explanation_text=explanation_text,
            model_type="gradient_boosting")

    def _generate_explanation_text(
        self,
        synth_id: str,
        contributions: list[ShapContribution],
        predicted: float,
        actual: float,
        baseline: float) -> str:
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
        self,
        simulation_id: str,
        outcomes: list[SynthOutcome],
        features: list[str] | None = None) -> ShapSummary:
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
            outcomes,
            features=features,
            include_outcomes=False)

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
            feature_importances.keys(),
            key=lambda f: feature_importances[f],
            reverse=True)

        # Top 10 features
        top_features = sorted_features[:10]

        return ShapSummary(
            simulation_id=simulation_id,
            feature_importances=feature_importances,
            top_features=top_features,
            total_synths=len(outcomes),
            model_score=score)

    def calculate_pdp(
        self,
        simulation_id: str,
        outcomes: list[SynthOutcome],
        feature: str,
        features: list[str] | None = None,
        grid_resolution: int = 20) -> PDPResult:
        """
        Calculate Partial Dependence Plot for a feature.

        Shows how changing the feature value affects the predicted
        success rate, averaging over all other features.

        Args:
            simulation_id: Simulation identifier.
            outcomes: List of all SynthOutcome entities.
            feature: Feature name to analyze.
            features: All feature names to use. Defaults to latent traits.
            grid_resolution: Number of points in PDP curve.

        Returns:
            PDPResult with PDP curve and effect classification.

        Raises:
            ValueError: If feature not found.
        """
        if not outcomes:
            raise ValueError("Outcomes list is empty")

        # Use default features if not specified
        if features is None:
            features = DEFAULT_FEATURES.copy()

        # Verify feature exists
        if feature not in features:
            # Try to add it
            try:
                get_attribute_value(outcomes[0], feature)
                features = [feature] + [f for f in features if f != feature]
            except ValueError:
                raise ValueError(f"Feature '{feature}' not found in synth attributes")

        # Train model
        model, score = self._train_model(outcomes, features)

        # Extract features
        X, synth_ids, feature_names = extract_features(
            outcomes,
            features=features,
            include_outcomes=False)

        # Find feature index
        try:
            feature_idx = feature_names.index(feature)
        except ValueError:
            raise ValueError(f"Feature '{feature}' not found in feature list")

        # Calculate partial dependence
        pd_result = partial_dependence(
            model,
            X,
            features=[feature_idx],
            kind="average",
            grid_resolution=grid_resolution)

        # Extract values
        grid_values = pd_result["grid_values"][0]
        avg_predictions = pd_result["average"][0]

        # Build PDP points
        pdp_values = [
            PDPPoint(
                feature_value=float(grid_values[i]),
                predicted_success=float(avg_predictions[i]),
                confidence_lower=None,  # Could add confidence intervals later
                confidence_upper=None)
            for i in range(len(grid_values))
        ]

        # Classify effect type
        effect_type, effect_strength = self._classify_effect(list(avg_predictions))

        # Calculate baseline value
        baseline_value = float(np.mean(X[:, feature_idx]))

        # Human-readable display name
        display_name = feature.replace("_", " ").title()

        return PDPResult(
            simulation_id=simulation_id,
            feature_name=feature,
            feature_display_name=display_name,
            pdp_values=pdp_values,
            effect_type=effect_type,
            effect_strength=effect_strength,
            baseline_value=baseline_value)

    def _classify_effect(
        self,
        values: list[float]) -> tuple[str, float]:
        """
        Classify the type of effect based on PDP values.

        Args:
            values: List of predicted values along PDP curve.

        Returns:
            Tuple of (effect_type, effect_strength).
            Effect types: monotonic_increasing, monotonic_decreasing, non_linear, flat
        """
        if len(values) < 2:
            return "flat", 0.0

        values_arr = np.array(values)

        # Calculate effect strength (range of predictions)
        effect_strength = float(np.max(values_arr) - np.min(values_arr))

        # Check if flat (very small range)
        if effect_strength < 0.01:
            return "flat", effect_strength

        # Calculate differences
        diffs = np.diff(values_arr)

        # Check monotonicity
        positive_diffs = np.sum(diffs > 0)
        negative_diffs = np.sum(diffs < 0)
        total_diffs = len(diffs)

        # Consider monotonic if >80% of differences are in same direction
        monotonic_threshold = 0.8

        if positive_diffs / total_diffs >= monotonic_threshold:
            return "monotonic_increasing", effect_strength
        elif negative_diffs / total_diffs >= monotonic_threshold:
            return "monotonic_decreasing", effect_strength
        else:
            return "non_linear", effect_strength

    def compare_pdps(
        self,
        simulation_id: str,
        outcomes: list[SynthOutcome],
        features: list[str],
        grid_resolution: int = 20) -> PDPComparison:
        """
        Compare PDPs across multiple features.

        Args:
            simulation_id: Simulation identifier.
            outcomes: List of all SynthOutcome entities.
            features: List of feature names to compare.
            grid_resolution: Number of points in each PDP curve.

        Returns:
            PDPComparison with all PDPs and ranking.
        """
        pdp_results = []

        for feature in features:
            pdp = self.calculate_pdp(
                simulation_id=simulation_id,
                outcomes=outcomes,
                feature=feature,
                features=features,
                grid_resolution=grid_resolution)
            pdp_results.append(pdp)

        # Rank by effect strength (descending)
        sorted_pdps = sorted(pdp_results, key=lambda p: p.effect_strength, reverse=True)
        feature_ranking = [p.feature_name for p in sorted_pdps]

        return PDPComparison(
            simulation_id=simulation_id,
            pdp_results=pdp_results,
            feature_ranking=feature_ranking,
            total_synths=len(outcomes))

    # =============================================================================
    # Router-compatible wrapper methods
    # =============================================================================

    def get_shap_explanation(
        self,
        simulation_id: str,
        outcomes: list[SynthOutcome],
        synth_id: str,
        features: list[str] | None = None) -> ShapExplanation:
        """Wrapper for explain_synth for API router compatibility."""
        return self.explain_synth(
            simulation_id=simulation_id,
            outcomes=outcomes,
            synth_id=synth_id,
            features=features)

    def get_pdp(
        self,
        simulation_id: str,
        outcomes: list[SynthOutcome],
        feature: str,
        features: list[str] | None = None,
        grid_resolution: int = 20) -> PDPResult:
        """Wrapper for calculate_pdp for API router compatibility."""
        return self.calculate_pdp(
            simulation_id=simulation_id,
            outcomes=outcomes,
            feature=feature,
            features=features,
            grid_resolution=grid_resolution)

    def get_pdp_comparison(
        self,
        simulation_id: str,
        outcomes: list[SynthOutcome],
        features: list[str],
        grid_resolution: int = 20) -> PDPComparison:
        """Wrapper for compare_pdps for API router compatibility."""
        return self.compare_pdps(
            simulation_id=simulation_id,
            outcomes=outcomes,
            features=features,
            grid_resolution=grid_resolution)


# =============================================================================
# Validation
# =============================================================================

if __name__ == "__main__":
    import sys

    from synth_lab.domain.entities.simulation_attributes import (
        SimulationAttributes,
        SimulationLatentTraits,
        SimulationObservables)

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
        success_rate = np.clip(base_success + noise, 0.05, 0.95)
        failed_rate = np.clip(0.4 - 0.2 * capability + np.random.randn() * 0.1, 0.05, 0.5)
        did_not_try_rate = max(0.0, 1.0 - success_rate - failed_rate)

        total = success_rate + failed_rate + did_not_try_rate
        success_rate /= total
        failed_rate /= total
        did_not_try_rate /= total

        outcomes.append(
            SynthOutcome(
                synth_id=f"synth_{i:03d}",
                simulation_id="sim_test",
                success_rate=success_rate,
                failed_rate=failed_rate,
                did_not_try_rate=did_not_try_rate,
                synth_attributes=SimulationAttributes(
                    observables=SimulationObservables(
                        digital_literacy=0.5,
                        similar_tool_experience=0.5,
                        motor_ability=0.5,
                        time_availability=0.5,
                        domain_expertise=0.5),
                    latent_traits=SimulationLatentTraits(
                        capability_mean=capability,
                        trust_mean=trust,
                        friction_tolerance_mean=friction,
                        exploration_prob=exploration)))
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
            simulation_id="sim_test",
            outcomes=outcomes,
            synth_id="synth_010")
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
        summary = service.get_shap_summary(
            simulation_id="sim_test",
            outcomes=outcomes)
        if not summary.feature_importances:
            all_validation_failures.append("No feature importances")
        if not summary.top_features:
            all_validation_failures.append("No top features")
        else:
            print(f"Test 3 PASSED: SHAP summary, top feature: {summary.top_features[0]}")
    except Exception as e:
        all_validation_failures.append(f"SHAP summary failed: {e}")

    # Test 4: PDP calculation
    total_tests += 1
    try:
        pdp = service.calculate_pdp(
            simulation_id="sim_test",
            outcomes=outcomes,
            feature="trust_mean")
        if not pdp.pdp_values:
            all_validation_failures.append("No PDP values")
        if pdp.effect_type not in [
            "monotonic_increasing",
            "monotonic_decreasing",
            "non_linear",
            "flat",
        ]:
            all_validation_failures.append(f"Invalid effect type: {pdp.effect_type}")
        else:
            print(
                f"Test 4 PASSED: PDP calculated, effect={pdp.effect_type}, strength={pdp.effect_strength:.3f}"
            )
    except Exception as e:
        all_validation_failures.append(f"PDP calculation failed: {e}")

    # Test 5: PDP comparison
    total_tests += 1
    try:
        comparison = service.compare_pdps(
            simulation_id="sim_test",
            outcomes=outcomes,
            features=["capability_mean", "trust_mean"])
        if len(comparison.pdp_results) != 2:
            all_validation_failures.append(f"Expected 2 PDPs, got {len(comparison.pdp_results)}")
        if len(comparison.feature_ranking) != 2:
            all_validation_failures.append(
                f"Expected 2 in ranking, got {len(comparison.feature_ranking)}"
            )
        else:
            print(f"Test 5 PASSED: PDP comparison, ranking: {comparison.feature_ranking}")
    except Exception as e:
        all_validation_failures.append(f"PDP comparison failed: {e}")

    # Test 6: Effect classification
    total_tests += 1
    try:
        # Monotonic increasing
        effect_type, strength = service._classify_effect([0.1, 0.2, 0.3, 0.4, 0.5])
        if effect_type != "monotonic_increasing":
            all_validation_failures.append(f"Expected monotonic_increasing, got {effect_type}")

        # Monotonic decreasing
        effect_type, strength = service._classify_effect([0.5, 0.4, 0.3, 0.2, 0.1])
        if effect_type != "monotonic_decreasing":
            all_validation_failures.append(f"Expected monotonic_decreasing, got {effect_type}")

        # Flat
        effect_type, strength = service._classify_effect([0.5, 0.5, 0.5, 0.5])
        if effect_type != "flat":
            all_validation_failures.append(f"Expected flat, got {effect_type}")

        print("Test 6 PASSED: Effect classification works correctly")
    except Exception as e:
        all_validation_failures.append(f"Effect classification failed: {e}")

    # Test 7: Synth not found error
    total_tests += 1
    try:
        service.explain_synth(
            simulation_id="sim_test",
            outcomes=outcomes,
            synth_id="nonexistent")
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
