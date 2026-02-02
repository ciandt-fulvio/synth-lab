"""
Distribution Sampler for causal simulation system.

Provides seeded random sampling from various probability distributions using
NumPy and SciPy. Supports uniform, normal, beta, lognormal, and Bernoulli.

References:
    - Spec: specs/035-causal-simulation/spec.md
    - NumPy random: https://numpy.org/doc/stable/reference/random/index.html
    - SciPy stats: https://docs.scipy.org/doc/scipy/reference/stats.html
"""

import numpy as np
from scipy import stats

from synth_lab.domain.entities.hypothesis import (
    BernoulliParams,
    BetaParams,
    DistributionType,
    Hypothesis,
    LogNormalParams,
    NormalParams,
    UniformParams,
)


class DistributionSampler:
    """
    Seeded random sampler for probability distributions.

    All sampling uses deterministic seeded randomness for reproducibility.
    """

    def __init__(self, seed: int):
        """
        Initialize sampler with random seed.

        Args:
            seed: Random seed for reproducibility

        Example:
            >>> sampler = DistributionSampler(seed=42)
            >>> sample = sampler.sample(hypothesis, n=100)
        """
        self.rng = np.random.default_rng(seed)

    def sample(self, hypothesis: Hypothesis, n: int = 1) -> np.ndarray:
        """
        Sample from a hypothesis distribution.

        Args:
            hypothesis: Hypothesis entity with distribution type and parameters
            n: Number of samples to draw

        Returns:
            NumPy array of samples (shape: (n,))

        Raises:
            ValueError: If distribution type is unsupported

        Example:
            >>> hyp = Hypothesis(
            ...     distribution_type=DistributionType.NORMAL,
            ...     parameters=NormalParams(mean=10, std=2)
            ... )
            >>> samples = sampler.sample(hyp, n=500)
        """
        # Validate range bounds
        range_min = hypothesis.range_min
        range_max = hypothesis.range_max
        if range_min is not None and range_max is not None and range_min > range_max:
            raise ValueError(f"range_min ({range_min}) must be <= range_max ({range_max})")

        dist_type = hypothesis.distribution_type
        params = hypothesis.parameters

        if dist_type == DistributionType.UNIFORM:
            samples = self._sample_uniform(params, n)
        elif dist_type == DistributionType.NORMAL:
            samples = self._sample_normal(params, n)
        elif dist_type == DistributionType.BETA:
            samples = self._sample_beta(params, n)
        elif dist_type == DistributionType.LOGNORMAL:
            samples = self._sample_lognormal(params, n)
        elif dist_type == DistributionType.BERNOULLI:
            samples = self._sample_bernoulli(params, n)
        else:
            raise ValueError(f"Unsupported distribution type: {dist_type}")

        # Apply range clamping if bounds are specified
        if range_min is not None or range_max is not None:
            samples = np.clip(samples, a_min=range_min, a_max=range_max)

        return samples

    def _sample_uniform(self, params: UniformParams, n: int) -> np.ndarray:
        """
        Sample from uniform distribution.

        Args:
            params: Uniform distribution parameters (low, high)
            n: Number of samples

        Returns:
            NumPy array of samples
        """
        return self.rng.uniform(low=params.low, high=params.high, size=n)

    def _sample_normal(self, params: NormalParams, n: int) -> np.ndarray:
        """
        Sample from normal distribution.

        Args:
            params: Normal distribution parameters (mean, std)
            n: Number of samples

        Returns:
            NumPy array of samples
        """
        return self.rng.normal(loc=params.mean, scale=params.std, size=n)

    def _sample_beta(self, params: BetaParams, n: int) -> np.ndarray:
        """
        Sample from beta distribution (bounded [0, 1]).

        Args:
            params: Beta distribution parameters (alpha, beta)
            n: Number of samples

        Returns:
            NumPy array of samples (all values in [0, 1])
        """
        return self.rng.beta(a=params.alpha, b=params.beta, size=n)

    def _sample_lognormal(self, params: LogNormalParams, n: int) -> np.ndarray:
        """
        Sample from lognormal distribution (positive values only).

        Args:
            params: LogNormal distribution parameters (mean, sigma)
            n: Number of samples

        Returns:
            NumPy array of samples (all values > 0)
        """
        return self.rng.lognormal(mean=params.mean, sigma=params.sigma, size=n)

    def _sample_bernoulli(self, params: BernoulliParams, n: int) -> np.ndarray:
        """
        Sample from Bernoulli distribution (binary outcomes).

        Args:
            params: Bernoulli distribution parameters (p)
            n: Number of samples

        Returns:
            NumPy array of samples (0 or 1)
        """
        return self.rng.binomial(n=1, p=params.p, size=n).astype(float)

    def sample_correlated(
        self,
        hypotheses: list[Hypothesis],
        correlation_matrix: np.ndarray,
        n: int = 1,
    ) -> np.ndarray:
        """
        Sample from multiple correlated distributions.

        Uses Gaussian copula method to induce correlations between variables.

        Args:
            hypotheses: List of Hypothesis entities
            correlation_matrix: Correlation matrix (shape: (n_vars, n_vars))
            n: Number of samples to draw

        Returns:
            NumPy array of samples (shape: (n, n_vars))

        Raises:
            ValueError: If correlation matrix is invalid

        Example:
            >>> hyps = [hyp1, hyp2, hyp3]
            >>> corr = np.array([[1.0, 0.6, 0.3],
            ...                  [0.6, 1.0, 0.4],
            ...                  [0.3, 0.4, 1.0]])
            >>> samples = sampler.sample_correlated(hyps, corr, n=500)
        """
        n_vars = len(hypotheses)

        # Validate correlation matrix
        if correlation_matrix.shape != (n_vars, n_vars):
            raise ValueError(
                f"Correlation matrix shape {correlation_matrix.shape} "
                f"does not match number of variables {n_vars}"
            )

        # Generate correlated standard normal samples (Gaussian copula)
        mean = np.zeros(n_vars)
        correlated_normals = self.rng.multivariate_normal(mean, correlation_matrix, size=n)

        # Transform to uniform [0, 1] via standard normal CDF
        uniform_samples = stats.norm.cdf(correlated_normals)

        # Transform uniform samples to target distributions via inverse CDF
        samples = np.zeros((n, n_vars))
        for i, hypothesis in enumerate(hypotheses):
            samples[:, i] = self._inverse_cdf_transform(uniform_samples[:, i], hypothesis)

        return samples

    def _inverse_cdf_transform(
        self, uniform_samples: np.ndarray, hypothesis: Hypothesis
    ) -> np.ndarray:
        """
        Transform uniform [0, 1] samples to target distribution via inverse CDF.

        Args:
            uniform_samples: Uniform samples in [0, 1]
            hypothesis: Target distribution

        Returns:
            Transformed samples from target distribution
        """
        dist_type = hypothesis.distribution_type
        params = hypothesis.parameters

        if dist_type == DistributionType.UNIFORM:
            low, high = params.low, params.high
            return low + (high - low) * uniform_samples

        elif dist_type == DistributionType.NORMAL:
            return stats.norm.ppf(uniform_samples, loc=params.mean, scale=params.std)

        elif dist_type == DistributionType.BETA:
            return stats.beta.ppf(uniform_samples, a=params.alpha, b=params.beta)

        elif dist_type == DistributionType.LOGNORMAL:
            return stats.lognorm.ppf(uniform_samples, s=params.sigma, scale=np.exp(params.mean))

        elif dist_type == DistributionType.BERNOULLI:
            return (uniform_samples < params.p).astype(float)

        else:
            raise ValueError(f"Unsupported distribution type: {dist_type}")
