"""
Region analysis service for feature impact simulation.

Identifies synth regions with high failure rates using Decision Tree Classifier
and extracts interpretable rules.

Classes:
- RegionAnalyzer: Analyzes simulation outcomes to identify problematic regions

References:
    - Spec: specs/016-feature-impact-simulation/spec.md
    - Research: specs/016-feature-impact-simulation/research.md (Decision Tree section)

Sample usage:
    from synth_lab.services.simulation.analyzer import RegionAnalyzer

    analyzer = RegionAnalyzer()
    regions = analyzer.analyze_regions(
        outcomes=synth_outcomes,
        min_failure_rate=0.5,
        max_depth=4
    )

Expected output:
    List of RegionAnalysis with interpretable rules like:
    "capability_mean < 0.48 AND trust_mean < 0.4"
"""

from typing import Any

import numpy as np
from loguru import logger
from sklearn.tree import DecisionTreeClassifier, export_text

from synth_lab.domain.entities import RegionAnalysis, RegionRule


class RegionAnalyzer:
    """
    Analyzes simulation outcomes to identify synth regions with distinct characteristics.

    Uses Decision Tree Classifier to find regions with high failure rates
    and extracts interpretable rules.
    """

    def __init__(
        self,
        max_depth: int = 4,
        min_samples_leaf: int = 20,
        min_samples_split: int = 40,
    ) -> None:
        """
        Initialize RegionAnalyzer.

        Args:
            max_depth: Maximum depth of decision tree (avoids overfitting)
            min_samples_leaf: Minimum samples per leaf node (4% of 500)
            min_samples_split: Minimum samples to split a node (8% of 500)
        """
        self.max_depth = max_depth
        self.min_samples_leaf = min_samples_leaf
        self.min_samples_split = min_samples_split
        self.logger = logger.bind(component="region_analyzer")

    def analyze_regions(
        self,
        outcomes: list[dict[str, Any]],
        simulation_id: str,
        min_failure_rate: float = 0.5,
    ) -> list[RegionAnalysis]:
        """
        Analyze simulation outcomes to identify high-failure regions.

        Uses Decision Tree to find combinations of synth attributes
        that lead to high failure rates.

        Args:
            outcomes: List of synth outcomes with attributes and rates
            simulation_id: ID of the simulation being analyzed
            min_failure_rate: Minimum failure rate to consider a region problematic

        Returns:
            List of RegionAnalysis with interpretable rules

        Raises:
            ValueError: If outcomes list is empty or malformed
        """
        if not outcomes:
            raise ValueError("Outcomes list cannot be empty")

        self.logger.info(
            f"Analyzing {len(outcomes)} outcomes for simulation {simulation_id}"
        )

        # Extract features and labels
        X, feature_names = self._extract_features(outcomes)
        y = self._extract_labels(outcomes)

        if len(X) < self.min_samples_split:
            self.logger.warning(
                f"Not enough samples ({len(X)}) for analysis. "
                f"Need at least {self.min_samples_split}"
            )
            return []

        # Train decision tree classifier
        clf = DecisionTreeClassifier(
            max_depth=self.max_depth,
            min_samples_leaf=self.min_samples_leaf,
            min_samples_split=self.min_samples_split,
            class_weight="balanced",  # Handle imbalanced classes
            random_state=42,  # For reproducibility
        )

        clf.fit(X, y)

        # Extract rules for high-failure regions
        regions = self._extract_rules(
            tree=clf,
            feature_names=feature_names,
            X=X,
            y=y,
            simulation_id=simulation_id,
            min_failure_rate=min_failure_rate,
        )

        self.logger.info(f"Found {len(regions)} high-failure regions")
        return regions

    def _extract_features(
        self, outcomes: list[dict[str, Any]]
    ) -> tuple[np.ndarray, list[str]]:
        """
        Extract feature matrix from outcomes.

        Extracts latent traits (capability, trust, friction_tolerance, exploration_prob)
        from synth attributes.

        Args:
            outcomes: List of synth outcomes

        Returns:
            Tuple of (feature_matrix, feature_names)
        """
        features = []
        feature_names = [
            "capability_mean",
            "trust_mean",
            "friction_tolerance_mean",
            "exploration_prob",
        ]

        for outcome in outcomes:
            attrs = outcome.get("synth_attributes", {})
            latent = attrs.get("latent_traits", {})

            # Extract latent traits in consistent order
            row = [
                latent.get("capability_mean", 0.5),
                latent.get("trust_mean", 0.5),
                latent.get("friction_tolerance_mean", 0.5),
                latent.get("exploration_prob", 0.5),
            ]
            features.append(row)

        return np.array(features), feature_names

    def _extract_labels(self, outcomes: list[dict[str, Any]]) -> np.ndarray:
        """
        Extract binary labels (failed vs not-failed).

        Uses failed_rate >= 0.5 as threshold for "failed" label.

        Args:
            outcomes: List of synth outcomes

        Returns:
            Binary label array (1 = high failure, 0 = low failure)
        """
        labels = []
        for outcome in outcomes:
            failed_rate = outcome.get("failed_rate", 0.0)
            # Binary classification: high failure (1) vs low failure (0)
            label = 1 if failed_rate >= 0.5 else 0
            labels.append(label)

        return np.array(labels)

    def _extract_rules(
        self,
        tree: DecisionTreeClassifier,
        feature_names: list[str],
        X: np.ndarray,
        y: np.ndarray,
        simulation_id: str,
        min_failure_rate: float,
    ) -> list[RegionAnalysis]:
        """
        Extract interpretable rules from decision tree.

        Walks the tree structure to extract rules for leaf nodes
        with high failure rates.

        Args:
            tree: Trained DecisionTreeClassifier
            feature_names: Names of features
            X: Feature matrix
            y: Label array
            simulation_id: Simulation ID
            min_failure_rate: Minimum failure rate threshold

        Returns:
            List of RegionAnalysis objects
        """
        regions = []

        # Get tree structure
        tree_structure = tree.tree_
        feature = tree_structure.feature
        threshold = tree_structure.threshold
        value = tree_structure.value

        # Track paths to leaf nodes
        def recurse(node: int, rules: list[RegionRule]) -> None:
            """Recursively traverse tree and extract rules."""
            # Check if leaf node
            if tree_structure.feature[node] == -2:  # Leaf node
                # Calculate failure rate for this leaf
                samples_in_leaf = tree_structure.value[node][0]
                total_samples = samples_in_leaf.sum()
                if total_samples == 0:
                    return

                # Count high-failure samples (y=1)
                # Handle case where leaf might only have one class
                if len(samples_in_leaf) < 2:
                    # Only one class in tree - skip this leaf
                    return

                high_failure_count = samples_in_leaf[1]
                failure_rate = high_failure_count / total_samples

                # Only include regions with high failure rate
                if failure_rate >= min_failure_rate:
                    # Calculate samples in this region
                    n_samples = int(total_samples)

                    # Calculate avg failure rate for synths in this region
                    avg_failure = round(failure_rate, 3)
                    avg_success = round(1.0 - failure_rate, 3)

                    # Format rule text
                    rule_text = self.format_rule_text(rules)

                    # Calculate percentage (assume total population from X shape)
                    synth_percentage = round((n_samples / len(X)) * 100, 1)

                    # Create RegionAnalysis
                    region = RegionAnalysis(
                        simulation_id=simulation_id,
                        rules=rules.copy(),
                        rule_text=rule_text,
                        synth_count=n_samples,
                        synth_percentage=synth_percentage,
                        did_not_try_rate=0.0,  # Not tracked in binary classification
                        failed_rate=avg_failure,
                        success_rate=avg_success,
                        failure_delta=0.0,  # Will be calculated when comparing to population
                    )
                    regions.append(region)
                return

            # Internal node - split on feature
            feature_idx = tree_structure.feature[node]
            threshold_val = tree_structure.threshold[node]
            feature_name = feature_names[feature_idx]

            # Left child: feature <= threshold
            left_child = tree_structure.children_left[node]
            recurse(
                left_child,
                rules
                + [
                    RegionRule(
                        attribute=feature_name,
                        operator="<=",
                        threshold=round(threshold_val, 3),
                    )
                ],
            )

            # Right child: feature > threshold
            right_child = tree_structure.children_right[node]
            recurse(
                right_child,
                rules
                + [
                    RegionRule(
                        attribute=feature_name,
                        operator=">",
                        threshold=round(threshold_val, 3),
                    )
                ],
            )

        # Start recursion from root
        recurse(node=0, rules=[])

        return regions

    def format_rule_text(self, rules: list[RegionRule]) -> str:
        """
        Format rules as human-readable text.

        Args:
            rules: List of RegionRule objects

        Returns:
            Formatted rule text like "capability < 0.48 AND trust < 0.4"
        """
        if not rules:
            return "No rules"

        rule_strings = []
        for rule in rules:
            rule_strings.append(f"{rule.attribute} {rule.operator} {rule.threshold}")

        return " AND ".join(rule_strings)


if __name__ == "__main__":
    import sys

    print("=== Region Analyzer Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Test 1: Initialize analyzer
    total_tests += 1
    try:
        analyzer = RegionAnalyzer()
        if analyzer.max_depth != 4:
            all_validation_failures.append(f"max_depth should be 4, got {analyzer.max_depth}")
        else:
            print("Test 1 PASSED: Analyzer initialized with correct defaults")
    except Exception as e:
        all_validation_failures.append(f"Analyzer initialization failed: {e}")

    # Test 2: Extract features from outcomes
    total_tests += 1
    try:
        test_outcomes = [
            {
                "synth_id": "synth_1",
                "failed_rate": 0.6,
                "success_rate": 0.3,
                "did_not_try_rate": 0.1,
                "synth_attributes": {
                    "latent_traits": {
                        "capability_mean": 0.3,
                        "trust_mean": 0.4,
                        "friction_tolerance_mean": 0.5,
                        "exploration_prob": 0.6,
                    }
                },
            },
            {
                "synth_id": "synth_2",
                "failed_rate": 0.2,
                "success_rate": 0.7,
                "did_not_try_rate": 0.1,
                "synth_attributes": {
                    "latent_traits": {
                        "capability_mean": 0.8,
                        "trust_mean": 0.7,
                        "friction_tolerance_mean": 0.6,
                        "exploration_prob": 0.5,
                    }
                },
            },
        ]

        X, feature_names = analyzer._extract_features(test_outcomes)
        if X.shape != (2, 4):
            all_validation_failures.append(f"Feature matrix shape should be (2, 4), got {X.shape}")
        elif len(feature_names) != 4:
            all_validation_failures.append(
                f"Should have 4 feature names, got {len(feature_names)}"
            )
        else:
            print("Test 2 PASSED: Feature extraction works correctly")
    except Exception as e:
        all_validation_failures.append(f"Feature extraction failed: {e}")

    # Test 3: Extract labels
    total_tests += 1
    try:
        y = analyzer._extract_labels(test_outcomes)
        expected_labels = np.array([1, 0])  # First has high failure, second doesn't
        if not np.array_equal(y, expected_labels):
            all_validation_failures.append(f"Labels should be [1, 0], got {y}")
        else:
            print("Test 3 PASSED: Label extraction works correctly")
    except Exception as e:
        all_validation_failures.append(f"Label extraction failed: {e}")

    # Test 4: Format rule text
    total_tests += 1
    try:
        test_rules = [
            RegionRule(attribute="capability_mean", operator="<=", threshold=0.48),
            RegionRule(attribute="trust_mean", operator="<=", threshold=0.4),
        ]
        rule_text = analyzer.format_rule_text(test_rules)
        expected = "capability_mean <= 0.48 AND trust_mean <= 0.4"
        if rule_text != expected:
            all_validation_failures.append(
                f"Rule text should be '{expected}', got '{rule_text}'"
            )
        else:
            print("Test 4 PASSED: Rule formatting works correctly")
    except Exception as e:
        all_validation_failures.append(f"Rule formatting failed: {e}")

    # Test 5: Analyze regions with insufficient data
    total_tests += 1
    try:
        # Not enough samples (< min_samples_split=40)
        small_outcomes = test_outcomes[:2]
        regions = analyzer.analyze_regions(
            outcomes=small_outcomes,
            simulation_id="test_sim",
            min_failure_rate=0.5,
        )
        if len(regions) != 0:
            all_validation_failures.append(
                f"Should return empty list for insufficient data, got {len(regions)} regions"
            )
        else:
            print("Test 5 PASSED: Handles insufficient data correctly")
    except Exception as e:
        all_validation_failures.append(f"Insufficient data handling failed: {e}")

    # Final result
    print()
    if all_validation_failures:
        print(
            f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:"
        )
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("RegionAnalyzer is validated and ready for use")
        sys.exit(0)
