"""
Sensitivity Analyzer for causal simulation system.

Performs variance decomposition to identify which variables explain the most
variance in outcomes. Uses correlation-based and regression-based methods.

References:
    - Spec: specs/035-causal-simulation/spec.md
    - NumPy variance: https://numpy.org/doc/stable/reference/generated/numpy.var.html
    - scikit-learn R²: https://scikit-learn.org/stable/modules/model_evaluation.html#r2-score
"""

import numpy as np
from sklearn.linear_model import LinearRegression

from synth_lab.domain.entities.simulated_world import VarianceContribution


class SensitivityAnalyzer:
    """
    Analyzer for variance decomposition and sensitivity analysis.

    Identifies which input variables explain the most variance in outcome
    variables across simulated worlds.
    """

    @staticmethod
    def analyze_variance(
        variable_matrix: np.ndarray,
        outcome_vector: np.ndarray,
        variable_names: list[str],
    ) -> list[VarianceContribution]:
        """
        Analyze variance contributions of variables to outcome.

        Uses squared correlation (R²) to measure variance explained by each
        variable independently. Results are sorted by importance.

        Args:
            variable_matrix: Matrix of variable values (shape: (n_worlds, n_vars))
            outcome_vector: Vector of outcome values (shape: (n_worlds,))
            variable_names: Names of variables (length: n_vars)

        Returns:
            List of VarianceContribution entities, sorted by importance (descending)

        Raises:
            ValueError: If dimensions don't match

        Example:
            >>> var_matrix = np.array([[1.0, 0.5], [2.0, 0.6], [1.5, 0.7]])
            >>> outcomes = np.array([0.3, 0.4, 0.35])
            >>> names = ["var1", "var2"]
            >>> contributions = SensitivityAnalyzer.analyze_variance(
            ...     var_matrix, outcomes, names
            ... )
            >>> print(f"Top driver: {contributions[0].variable_name}")
        """
        n_worlds, n_vars = variable_matrix.shape

        if len(outcome_vector) != n_worlds:
            raise ValueError(
                f"Outcome vector length {len(outcome_vector)} does not match "
                f"number of worlds {n_worlds}"
            )

        if len(variable_names) != n_vars:
            raise ValueError(
                f"Variable names length {len(variable_names)} does not match "
                f"number of variables {n_vars}"
            )

        # Calculate variance explained for each variable
        # Collect (name, r_squared) tuples for sorting before creating entities
        var_results = []
        for i, var_name in enumerate(variable_names):
            var_values = variable_matrix[:, i]

            # Calculate R² (squared correlation)
            correlation = np.corrcoef(var_values, outcome_vector)[0, 1]
            r_squared = correlation**2 if not np.isnan(correlation) else 0.0

            var_results.append((var_name, r_squared))

        # Sort by variance explained (descending)
        var_results.sort(key=lambda x: x[1], reverse=True)

        # Create entities with proper ranks
        contributions = [
            VarianceContribution(
                variable_name=name,
                variance_explained=float(r_sq),
                rank=rank,
            )
            for rank, (name, r_sq) in enumerate(var_results, start=1)
        ]

        return contributions

    @staticmethod
    def analyze_joint_variance(
        variable_matrix: np.ndarray,
        outcome_vector: np.ndarray,
        variable_names: list[str],
    ) -> dict[str, float]:
        """
        Analyze joint variance contribution using multivariate regression.

        Uses linear regression to measure partial variance explained by each
        variable while controlling for other variables.

        Args:
            variable_matrix: Matrix of variable values (shape: (n_worlds, n_vars))
            outcome_vector: Vector of outcome values (shape: (n_worlds,))
            variable_names: Names of variables (length: n_vars)

        Returns:
            Dictionary mapping variable names to partial R² values

        Example:
            >>> partial_r2 = SensitivityAnalyzer.analyze_joint_variance(
            ...     var_matrix, outcomes, names
            ... )
            >>> print(f"Partial R² for var1: {partial_r2['var1']:.3f}")
        """
        n_worlds, n_vars = variable_matrix.shape

        # Fit full model
        model = LinearRegression()
        model.fit(variable_matrix, outcome_vector)
        full_r2 = model.score(variable_matrix, outcome_vector)

        # Calculate partial R² for each variable
        partial_r2 = {}
        for i, var_name in enumerate(variable_names):
            # Create reduced model excluding variable i
            reduced_vars = np.delete(variable_matrix, i, axis=1)

            # Fit reduced model
            reduced_model = LinearRegression()
            reduced_model.fit(reduced_vars, outcome_vector)
            reduced_r2 = reduced_model.score(reduced_vars, outcome_vector)

            # Partial R² = difference in R²
            partial_r2[var_name] = max(0.0, full_r2 - reduced_r2)

        return partial_r2

    @staticmethod
    def compute_correlation_matrix(
        variable_matrix: np.ndarray, variable_names: list[str]
    ) -> dict[str, dict[str, float]]:
        """
        Compute correlation matrix between all variables.

        Args:
            variable_matrix: Matrix of variable values (shape: (n_worlds, n_vars))
            variable_names: Names of variables (length: n_vars)

        Returns:
            Nested dictionary: {var1: {var2: correlation_coefficient}}

        Example:
            >>> corr_matrix = SensitivityAnalyzer.compute_correlation_matrix(
            ...     var_matrix, names
            ... )
            >>> print(f"Correlation: {corr_matrix['var1']['var2']:.3f}")
        """
        # Compute NumPy correlation matrix
        corr_np = np.corrcoef(variable_matrix.T)

        # Convert to nested dictionary
        corr_dict = {}
        for i, var1 in enumerate(variable_names):
            corr_dict[var1] = {}
            for j, var2 in enumerate(variable_names):
                corr_dict[var1][var2] = float(corr_np[i, j])

        return corr_dict

    @staticmethod
    def identify_top_drivers(
        contributions: list[VarianceContribution], top_n: int = 5
    ) -> list[VarianceContribution]:
        """
        Identify top N drivers of variance.

        Args:
            contributions: List of variance contributions (must be sorted)
            top_n: Number of top drivers to return

        Returns:
            Top N variance contributors

        Example:
            >>> top_drivers = SensitivityAnalyzer.identify_top_drivers(
            ...     contributions, top_n=3
            ... )
            >>> for driver in top_drivers:
            ...     print(f"{driver.variable_name}: {driver.variance_explained:.1%}")
        """
        return contributions[:top_n]
