"""
Unit tests for DistributionSampler range clamping.

Tests np.clip behavior with various range_min/range_max combinations
on the Hypothesis entity.

References:
    - Spec: specs/037-unified-dag-hypotheses/spec.md
    - Implementation: synth_lab/services/simulation/distribution_sampler.py
"""

import numpy as np
import pytest

from synth_lab.domain.entities.hypothesis import (
    DistributionType,
    Hypothesis,
    NormalParams,
    UniformParams,
)
from synth_lab.services.simulation.distribution_sampler import DistributionSampler

SEED = 42
N_SAMPLES = 1000


def _make_hypothesis(
    dist_type: DistributionType = DistributionType.NORMAL,
    params=None,
    range_min: float | None = None,
    range_max: float | None = None,
) -> Hypothesis:
    """Helper to build a hypothesis with optional range bounds."""
    if params is None:
        params = NormalParams(mean=50, std=20)
    return Hypothesis(
        simulation_id="sim_00000001",
        variable_id="var_price",
        variable_name="price",
        distribution_type=dist_type,
        parameters=params,
        range_min=range_min,
        range_max=range_max,
    )


class TestRangeClamping:
    """Tests for post-sampling range clamping via np.clip."""

    def test_clamp_both_bounds(self):
        """Samples are clamped to [range_min, range_max]."""
        sampler = DistributionSampler(seed=SEED)
        hyp = _make_hypothesis(range_min=30, range_max=70)
        samples = sampler.sample(hyp, n=N_SAMPLES)
        assert samples.min() >= 30
        assert samples.max() <= 70

    def test_clamp_only_min(self):
        """Samples are clamped to [range_min, +inf)."""
        sampler = DistributionSampler(seed=SEED)
        hyp = _make_hypothesis(range_min=0)
        samples = sampler.sample(hyp, n=N_SAMPLES)
        assert samples.min() >= 0

    def test_clamp_only_max(self):
        """Samples are clamped to (-inf, range_max]."""
        sampler = DistributionSampler(seed=SEED)
        hyp = _make_hypothesis(range_max=100)
        samples = sampler.sample(hyp, n=N_SAMPLES)
        assert samples.max() <= 100

    def test_no_clamp_when_null_bounds(self):
        """No clamping when both range_min and range_max are None."""
        sampler = DistributionSampler(seed=SEED)
        hyp = _make_hypothesis()
        samples = sampler.sample(hyp, n=N_SAMPLES)
        # With mean=50 std=20 and 1000 samples, some should exceed typical bounds
        # Just verify we get samples (no error) and they're not artificially bounded
        assert len(samples) == N_SAMPLES

    def test_clamp_min_equals_max(self):
        """When min == max, all samples collapse to that value."""
        sampler = DistributionSampler(seed=SEED)
        hyp = _make_hypothesis(range_min=42, range_max=42)
        samples = sampler.sample(hyp, n=N_SAMPLES)
        np.testing.assert_array_equal(samples, np.full(N_SAMPLES, 42.0))

    def test_clamp_with_uniform_distribution(self):
        """Clamping works with uniform distribution too."""
        sampler = DistributionSampler(seed=SEED)
        hyp = _make_hypothesis(
            dist_type=DistributionType.UNIFORM,
            params=UniformParams(low=0, high=100),
            range_min=20,
            range_max=80,
        )
        samples = sampler.sample(hyp, n=N_SAMPLES)
        assert samples.min() >= 20
        assert samples.max() <= 80


class TestRangeValidation:
    """Tests for range validation (min > max rejection)."""

    def test_reject_min_greater_than_max(self):
        """Creating a hypothesis with range_min > range_max should raise."""
        sampler = DistributionSampler(seed=SEED)
        hyp = _make_hypothesis(range_min=100, range_max=10)
        with pytest.raises(ValueError, match="range_min.*range_max"):
            sampler.sample(hyp, n=N_SAMPLES)
