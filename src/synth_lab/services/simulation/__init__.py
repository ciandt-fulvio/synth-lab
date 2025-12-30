"""
Feature Impact Simulation Services.

This module provides Monte Carlo simulation capabilities for evaluating
how product features impact different synth profiles.

Main components:
- sample_state: Sample user state with noise and scenario modifiers
- probability: Calculate attempt and success probabilities
- engine: Monte Carlo simulation engine
- simulation_service: Simulation orchestration and execution
- scorecard_service: Feature scorecard management
- scorecard_llm: LLM integration for insights
- chart_data_service: UX Research analysis chart data generation
- feature_extraction: Feature extraction utilities for ML algorithms
- clustering_service: K-Means and Hierarchical clustering
- outlier_service: Extreme cases and outlier detection
- explainability_service: SHAP and PDP analysis
- insight_service: LLM-generated chart insights
"""

from synth_lab.services.simulation.chart_data_service import ChartDataService
from synth_lab.services.simulation.clustering_service import ClusteringService
from synth_lab.services.simulation.explainability_service import ExplainabilityService
from synth_lab.services.simulation.feature_extraction import (
    DEFAULT_FEATURES,
    extract_features,
    get_attribute_value,
    get_available_attributes,
    get_outcome_value,
)

# NOTE: InsightService temporarily disabled during feature 023 migration
# from synth_lab.services.simulation.insight_service import (
#     InsightGenerationError,
#     InsightService,
# )
from synth_lab.services.simulation.outlier_service import OutlierService
from synth_lab.services.simulation.scorecard_llm import ScorecardLLM
from synth_lab.services.simulation.scorecard_service import (
    ScorecardNotFoundError,
    ScorecardService,
    ValidationError,
)
from synth_lab.services.simulation.simulation_service import (
    SimulationService,
    get_scenario,
    list_scenarios,
)

__all__ = [
    # Scorecard
    "ScorecardService",
    "ScorecardNotFoundError",
    "ValidationError",
    "ScorecardLLM",
    # Simulation
    "SimulationService",
    "list_scenarios",
    "get_scenario",
    # Analysis (UX Research)
    "ChartDataService",
    "ClusteringService",
    "OutlierService",
    "ExplainabilityService",
    # NOTE: InsightService temporarily disabled during feature 023 migration
    # "InsightService",
    # "InsightGenerationError",
    # Feature extraction
    "DEFAULT_FEATURES",
    "extract_features",
    "get_attribute_value",
    "get_available_attributes",
    "get_outcome_value",
]
