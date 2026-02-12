"""
Feature Impact Simulation Services.

This module provides Monte Carlo simulation capabilities for evaluating
how product features impact different synth profiles.

Main components:
- sample_state: Sample user state with noise and scenario modifiers
- probability: Calculate attempt and success probabilities
- engine: Monte Carlo simulation engine
- chart_data_service: UX Research analysis chart data generation
- feature_extraction: Feature extraction utilities for ML algorithms
- outlier_service: Extreme cases and outlier detection
- explainability_service: SHAP analysis
"""

from synth_lab.services.simulation.chart_data_service import ChartDataService
from synth_lab.services.simulation.explainability_service import ExplainabilityService
from synth_lab.services.simulation.feature_extraction import (
    DEFAULT_FEATURES,
    extract_features,
    get_attribute_value,
    get_available_attributes,
    get_outcome_value,
)
from synth_lab.services.simulation.outlier_service import OutlierService

__all__ = [
    # Analysis (UX Research)
    "ChartDataService",
    "OutlierService",
    "ExplainabilityService",
    # Feature extraction
    "DEFAULT_FEATURES",
    "extract_features",
    "get_attribute_value",
    "get_available_attributes",
    "get_outcome_value",
]
