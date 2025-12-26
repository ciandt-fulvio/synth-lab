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
"""

from synth_lab.services.simulation.chart_data_service import ChartDataService
from synth_lab.services.simulation.feature_extraction import (
    DEFAULT_FEATURES,
    extract_features,
    get_attribute_value,
    get_available_attributes,
    get_outcome_value,
)
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
    "DEFAULT_FEATURES",
    "extract_features",
    "get_attribute_value",
    "get_available_attributes",
    "get_outcome_value",
]
