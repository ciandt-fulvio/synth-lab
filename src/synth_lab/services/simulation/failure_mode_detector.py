"""
Failure Mode Detector for causal simulation system.

Identifies patterns where specific variable conditions predict poor outcomes
using rule-based analysis and chi-square tests for statistical significance.

References:
    - Spec: specs/035-causal-simulation/spec.md
    - SciPy chi-square: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.chi2_contingency.html
"""

import numpy as np
from scipy import stats

from synth_lab.domain.entities.simulated_world import (
    FailureMode,
    OutcomeThreshold,
    SeverityLevel,
    VariableCondition,
)


class FailureModeDetector:
    """
    Detector for failure modes in simulated worlds.

    Identifies patterns where specific variable ranges predict poor outcomes,
    using rule-based thresholding and chi-square tests.
    """

    def __init__(
        self,
        min_frequency: float = 0.1,
        min_chi_square: float = 3.84,  # p < 0.05
    ):
        """
        Initialize failure mode detector.

        Args:
            min_frequency: Minimum frequency threshold (0-1) for pattern
            min_chi_square: Minimum chi-square statistic for significance
        """
        self.min_frequency = min_frequency
        self.min_chi_square = min_chi_square

    def detect_failure_modes(
        self,
        variable_matrix: np.ndarray,
        outcome_vector: np.ndarray,
        variable_names: list[str],
        outcome_name: str,
        evidence_id: str,
        outcome_failure_threshold: float,
    ) -> list[FailureMode]:
        """
        Detect failure modes in simulated worlds.

        Identifies variable ranges that predict outcome values below the failure
        threshold with statistical significance.

        Args:
            variable_matrix: World variable values (shape: (n_worlds, n_vars))
            outcome_vector: World outcome values (shape: (n_worlds,))
            variable_names: Names of variables (length: n_vars)
            outcome_name: Name of the outcome variable
            evidence_id: Parent evidence ID
            outcome_failure_threshold: Threshold below which outcome is "failure"

        Returns:
            List of FailureMode entities

        Example:
            >>> detector = FailureModeDetector(min_frequency=0.15)
            >>> failure_modes = detector.detect_failure_modes(
            ...     var_matrix, outcomes, var_names, "adoption_rate", evd_id, 0.20
            ... )
            >>> for fm in failure_modes:
            ...     print(f"{fm.description} (frequency: {fm.frequency:.1%})")
        """
        n_worlds, n_vars = variable_matrix.shape
        failure_modes = []

        # Identify failed worlds
        failed_mask = outcome_vector < outcome_failure_threshold
        n_failed = np.sum(failed_mask)

        if n_failed < 2:
            # Not enough failures to detect patterns
            return []

        # For each variable, test different threshold splits
        for i, var_name in enumerate(variable_names):
            var_values = variable_matrix[:, i]

            # Test different percentile thresholds
            percentiles = [10, 25, 50, 75, 90]
            for percentile in percentiles:
                threshold = np.percentile(var_values, percentile)

                # Test both directions: < threshold and > threshold
                for operator, condition_mask in [
                    ("<", var_values < threshold),
                    (">", var_values > threshold),
                ]:
                    # Check if this pattern predicts failures
                    pattern_failed = np.sum(failed_mask & condition_mask)
                    pattern_total = np.sum(condition_mask)

                    if pattern_total == 0:
                        continue

                    # Calculate frequency of failure given pattern
                    pattern_failure_rate = pattern_failed / pattern_total

                    # Calculate overall failure rate
                    overall_failure_rate = n_failed / n_worlds

                    # Pattern must have higher failure rate than overall
                    if pattern_failure_rate <= overall_failure_rate:
                        continue

                    # Pattern frequency must be above minimum
                    pattern_frequency = pattern_total / n_worlds
                    if pattern_frequency < self.min_frequency:
                        continue

                    # Perform chi-square test for independence
                    contingency_table = np.array(
                        [
                            [pattern_failed, pattern_total - pattern_failed],
                            [
                                n_failed - pattern_failed,
                                n_worlds - pattern_total - n_failed + pattern_failed,
                            ],
                        ]
                    )

                    try:
                        chi2, p_value, _, _ = stats.chi2_contingency(
                            contingency_table
                        )
                    except ValueError:
                        # Chi-square test failed (likely due to zeros)
                        continue

                    # Check significance
                    if chi2 < self.min_chi_square:
                        continue

                    # Create FailureMode entity
                    pattern = {
                        var_name: VariableCondition(
                            operator=operator, value=float(threshold)
                        )
                    }

                    outcome_threshold_obj = {
                        outcome_name: OutcomeThreshold(
                            operator="<", value=float(outcome_failure_threshold)
                        )
                    }

                    severity = self._classify_severity(
                        pattern_failure_rate, pattern_frequency
                    )

                    description = self._generate_description(
                        var_name,
                        operator,
                        threshold,
                        outcome_name,
                        outcome_failure_threshold,
                        pattern_failure_rate,
                    )

                    failure_mode = FailureMode(
                        evidence_id=evidence_id,
                        pattern=pattern,
                        outcome_threshold=outcome_threshold_obj,
                        frequency=float(pattern_failure_rate),
                        severity=severity,
                        description=description,
                    )

                    failure_modes.append(failure_mode)

        # Remove duplicate/overlapping failure modes
        failure_modes = self._deduplicate_failure_modes(failure_modes)

        # Sort by severity and frequency
        failure_modes.sort(
            key=lambda fm: (
                self._severity_rank(fm.severity),
                fm.frequency,
            ),
            reverse=True,
        )

        return failure_modes

    def _classify_severity(
        self, failure_rate: float, pattern_frequency: float
    ) -> SeverityLevel:
        """
        Classify severity of failure mode based on failure rate and frequency.

        Args:
            failure_rate: Rate of failure given pattern (0-1)
            pattern_frequency: Frequency of pattern in worlds (0-1)

        Returns:
            Severity level
        """
        # Impact = failure_rate * pattern_frequency
        impact = failure_rate * pattern_frequency

        if impact >= 0.25:  # Affects >25% of worlds with high failure
            return SeverityLevel.CRITICAL
        elif impact >= 0.15:
            return SeverityLevel.HIGH
        elif impact >= 0.08:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW

    def _severity_rank(self, severity: SeverityLevel) -> int:
        """
        Convert severity to rank for sorting.

        Args:
            severity: Severity level

        Returns:
            Numeric rank (higher = more severe)
        """
        rank_map = {
            SeverityLevel.CRITICAL: 4,
            SeverityLevel.HIGH: 3,
            SeverityLevel.MEDIUM: 2,
            SeverityLevel.LOW: 1,
        }
        return rank_map.get(severity, 0)

    def _generate_description(
        self,
        var_name: str,
        operator: str,
        threshold: float,
        outcome_name: str,
        outcome_threshold: float,
        failure_rate: float,
    ) -> str:
        """
        Generate human-readable description of failure mode.

        Args:
            var_name: Variable name
            operator: Comparison operator
            threshold: Variable threshold value
            outcome_name: Outcome name
            outcome_threshold: Outcome threshold value
            failure_rate: Failure rate given pattern

        Returns:
            Human-readable description
        """
        return (
            f"When {var_name} {operator} {threshold:.2f}, "
            f"{outcome_name} falls below {outcome_threshold:.2f} "
            f"in {failure_rate:.0%} of simulated worlds"
        )

    def _deduplicate_failure_modes(
        self, failure_modes: list[FailureMode]
    ) -> list[FailureMode]:
        """
        Remove duplicate or highly overlapping failure modes.

        Keeps the most severe/frequent instance of overlapping patterns.

        Args:
            failure_modes: List of failure modes (may contain duplicates)

        Returns:
            Deduplicated list of failure modes
        """
        # Simple deduplication: keep unique variable + operator combinations
        seen_patterns = set()
        unique_modes = []

        for fm in failure_modes:
            # Create pattern signature
            pattern_sig = tuple(
                (var, cond.operator, round(cond.value, 2))
                for var, cond in fm.pattern.items()
            )

            if pattern_sig not in seen_patterns:
                seen_patterns.add(pattern_sig)
                unique_modes.append(fm)

        return unique_modes
