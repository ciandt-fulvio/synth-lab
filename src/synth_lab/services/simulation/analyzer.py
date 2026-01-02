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
from sklearn.tree import DecisionTreeClassifier

from synth_lab.domain.entities import RegionAnalysis, RegionRule


class RegionAnalyzer:
    """
    Analyzes simulation outcomes to identify synth regions with distinct characteristics.

    Uses Decision Tree Classifier to find regions with high failure rates
    and extracts interpretable rules.
    """

    def __init__(
        self,
        max_depth: int = 3,
        min_samples_leaf: int = 30,
        min_samples_split: int = 60) -> None:
        """
        Initialize RegionAnalyzer.

        Args:
            max_depth: Maximum depth of decision tree (avoids overfitting)
            min_samples_leaf: Minimum samples per leaf node (6% of 500)
            min_samples_split: Minimum samples to split a node (12% of 500)
        """
        self.max_depth = max_depth
        self.min_samples_leaf = min_samples_leaf
        self.min_samples_split = min_samples_split
        self.logger = logger.bind(component="region_analyzer")

    def analyze_regions(
        self,
        outcomes: list[dict[str, Any]],
        simulation_id: str,
        min_failure_rate: float = 0.5) -> list[RegionAnalysis]:
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

        self.logger.info(f"Analyzing {len(outcomes)} outcomes for simulation {simulation_id}")

        # Extract features and labels
        X, feature_names = self._extract_features(outcomes)
        y = self._extract_labels(outcomes, min_failure_rate)

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

        # Extract rules for high-failure regions using REAL outcome data
        regions = self._extract_rules(
            tree=clf,
            feature_names=feature_names,
            X=X,
            outcomes=outcomes,
            simulation_id=simulation_id,
            min_failure_rate=min_failure_rate)

        self.logger.info(f"Found {len(regions)} high-failure regions")
        return regions

    def _extract_features(self, outcomes: list[dict[str, Any]]) -> tuple[np.ndarray, list[str]]:
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

    def _extract_labels(
        self, outcomes: list[dict[str, Any]], min_failure_rate: float
    ) -> np.ndarray:
        """
        Extract binary labels (failed vs not-failed).

        Uses adaptive threshold based on data distribution to ensure
        both classes are represented for decision tree learning.

        Args:
            outcomes: List of synth outcomes
            min_failure_rate: Minimum failure rate to identify as problematic

        Returns:
            Binary label array (1 = high failure, 0 = low failure)
        """
        failure_rates = [o.get("failed_rate", 0.0) for o in outcomes]

        # Use adaptive threshold to ensure we have both classes
        # Take the maximum of:
        # 1. The provided min_failure_rate
        # 2. The 60th percentile of actual failure rates (ensures ~40% high-failure samples)
        threshold = max(min_failure_rate, np.percentile(failure_rates, 60))

        # If even the 60th percentile is below min_failure_rate,
        # use median to ensure we have contrast
        if threshold >= max(failure_rates):
            threshold = np.median(failure_rates)

        self.logger.debug(
            f"Using adaptive threshold {threshold:.3f} for labels "
            f"(min_failure_rate={min_failure_rate:.3f}, "
            f"median={np.median(failure_rates):.3f}, "
            f"60th percentile={np.percentile(failure_rates, 60):.3f})"
        )

        labels = []
        for outcome in outcomes:
            failed_rate = outcome.get("failed_rate", 0.0)
            # Binary classification: high failure (1) vs low failure (0)
            label = 1 if failed_rate >= threshold else 0
            labels.append(label)

        return np.array(labels)

    def _extract_rules(
        self,
        tree: DecisionTreeClassifier,
        feature_names: list[str],
        X: np.ndarray,
        outcomes: list[dict[str, Any]],
        simulation_id: str,
        min_failure_rate: float) -> list[RegionAnalysis]:
        """
        Extract interpretable rules from decision tree.

        Uses leaf node assignments to calculate REAL failure rates from
        the original outcomes data.

        Args:
            tree: Trained DecisionTreeClassifier
            feature_names: Names of features
            X: Feature matrix
            outcomes: Original outcomes list (for calculating real rates)
            simulation_id: Simulation ID
            min_failure_rate: Minimum failure rate threshold

        Returns:
            List of RegionAnalysis objects
        """
        regions = []

        # Get leaf assignment for each sample
        leaf_ids = tree.apply(X)

        # Get tree structure for rule extraction
        tree_structure = tree.tree_

        # Group samples by leaf
        from collections import defaultdict

        leaf_to_indices: dict[int, list[int]] = defaultdict(list)
        for idx, leaf_id in enumerate(leaf_ids):
            leaf_to_indices[leaf_id].append(idx)

        # Calculate baseline failure rate
        baseline_failure = np.mean([o.get("failed_rate", 0.0) for o in outcomes])

        # Extract path for each leaf
        def get_path_to_leaf(node: int, target_leaf: int, path: list) -> list | None:
            """Get the decision path from root to a specific leaf."""
            if node == target_leaf:
                return path

            if tree_structure.feature[node] == -2:  # Leaf but not target
                return None

            feature_idx = tree_structure.feature[node]
            threshold_val = tree_structure.threshold[node]
            feature_name = feature_names[feature_idx]

            # Try left child (<=)
            left = tree_structure.children_left[node]
            result = get_path_to_leaf(
                left,
                target_leaf,
                path
                + [
                    RegionRule(
                        attribute=feature_name,
                        operator="<=",
                        threshold=round(threshold_val, 3))
                ])
            if result is not None:
                return result

            # Try right child (>)
            right = tree_structure.children_right[node]
            return get_path_to_leaf(
                right,
                target_leaf,
                path
                + [
                    RegionRule(
                        attribute=feature_name,
                        operator=">",
                        threshold=round(threshold_val, 3))
                ])

        # Process each leaf
        for leaf_id, sample_indices in leaf_to_indices.items():
            if len(sample_indices) < self.min_samples_leaf:
                continue  # Skip small leaves

            # Calculate REAL rates from outcomes
            leaf_outcomes = [outcomes[i] for i in sample_indices]
            avg_failed = np.mean([o.get("failed_rate", 0.0) for o in leaf_outcomes])
            avg_success = np.mean([o.get("success_rate", 0.0) for o in leaf_outcomes])
            avg_did_not_try = np.mean([o.get("did_not_try_rate", 0.0) for o in leaf_outcomes])

            # Only include high-failure regions
            if avg_failed < min_failure_rate:
                continue

            # Get rules for this leaf
            rules = get_path_to_leaf(0, leaf_id, [])
            if rules is None:
                continue

            # Simplify redundant rules
            simplified_rules = self._simplify_rules(rules)

            n_samples = len(sample_indices)
            synth_percentage = round((n_samples / len(X)) * 100, 1)
            failure_delta = round(avg_failed - baseline_failure, 3)

            region = RegionAnalysis(
                simulation_id=simulation_id,
                rules=simplified_rules,
                rule_text=self.format_rule_text(simplified_rules),
                synth_count=n_samples,
                synth_percentage=synth_percentage,
                did_not_try_rate=round(avg_did_not_try, 3),
                failed_rate=round(avg_failed, 3),
                success_rate=round(avg_success, 3),
                failure_delta=failure_delta)
            regions.append(region)

        # Sort by failure rate descending
        regions.sort(key=lambda r: r.failed_rate, reverse=True)

        return regions

    def _simplify_rules(self, rules: list[RegionRule]) -> list[RegionRule]:
        """
        Simplify redundant rules.

        For example: "x <= 0.5 AND x <= 0.3" becomes "x <= 0.3"
        And: "x > 0.3 AND x > 0.5" becomes "x > 0.5"

        Args:
            rules: List of RegionRule objects

        Returns:
            Simplified list of rules
        """
        from collections import defaultdict

        # Group by attribute
        by_attribute: dict[str, list[RegionRule]] = defaultdict(list)
        for rule in rules:
            by_attribute[rule.attribute].append(rule)

        simplified = []
        for attribute, attr_rules in by_attribute.items():
            # Separate by operator
            le_rules = [r for r in attr_rules if r.operator == "<="]
            gt_rules = [r for r in attr_rules if r.operator == ">"]

            # Keep only the tightest bound for each direction
            if le_rules:
                # Keep smallest threshold for <=
                min_rule = min(le_rules, key=lambda r: r.threshold)
                simplified.append(min_rule)

            if gt_rules:
                # Keep largest threshold for >
                max_rule = max(gt_rules, key=lambda r: r.threshold)
                simplified.append(max_rule)

        return simplified

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
        if analyzer.max_depth != 3:
            all_validation_failures.append(f"max_depth should be 3, got {analyzer.max_depth}")
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
            all_validation_failures.append(f"Should have 4 feature names, got {len(feature_names)}")
        else:
            print("Test 2 PASSED: Feature extraction works correctly")
    except Exception as e:
        all_validation_failures.append(f"Feature extraction failed: {e}")

    # Test 3: Extract labels
    total_tests += 1
    try:
        y = analyzer._extract_labels(test_outcomes, min_failure_rate=0.5)
        # With adaptive threshold, should find contrast between samples
        # First outcome has 0.6 failed_rate, second has 0.2
        if len(np.unique(y)) < 2:
            all_validation_failures.append(f"Labels should have 2 classes, got {np.unique(y)}")
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
            all_validation_failures.append(f"Rule text should be '{expected}', got '{rule_text}'")
        else:
            print("Test 4 PASSED: Rule formatting works correctly")
    except Exception as e:
        all_validation_failures.append(f"Rule formatting failed: {e}")

    # Test 5: Analyze regions with insufficient data
    total_tests += 1
    try:
        # Not enough samples (< min_samples_split=100)
        small_outcomes = test_outcomes[:2]
        regions = analyzer.analyze_regions(
            outcomes=small_outcomes,
            simulation_id="test_sim",
            min_failure_rate=0.5)
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
