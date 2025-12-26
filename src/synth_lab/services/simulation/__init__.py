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
"""

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
    "ScorecardService",
    "ScorecardNotFoundError",
    "ValidationError",
    "ScorecardLLM",
    "SimulationService",
    "list_scenarios",
    "get_scenario",
]
