"""Domain entities for synth-lab."""

from synth_lab.domain.entities.artifact_state import (
    ArtifactState,
    ArtifactStateEnum,
    ArtifactType,
    PRFAQStatus,
    compute_prfaq_state,
    compute_summary_state,
)
from synth_lab.domain.entities.assumption_log import (
    AssumptionLog,
    LogEntry,
    generate_log_id,
)
from synth_lab.domain.entities.feature_scorecard import (
    FeatureScorecard,
    ScorecardDimension,
    ScorecardIdentification,
    generate_scorecard_id,
)
from synth_lab.domain.entities.region_analysis import (
    RegionAnalysis,
    RegionRule,
    format_rules_as_text,
    generate_region_id,
)
from synth_lab.domain.entities.scenario import (
    PREDEFINED_SCENARIOS,
    Scenario,
)
from synth_lab.domain.entities.sensitivity_result import (
    DimensionSensitivity,
    SensitivityResult,
)
from synth_lab.domain.entities.simulation_attributes import (
    SimulationAttributes,
    SimulationLatentTraits,
    SimulationObservables,
)
from synth_lab.domain.entities.simulation_run import (
    SimulationConfig,
    SimulationRun,
    generate_simulation_id,
)
from synth_lab.domain.entities.synth_outcome import (
    SynthOutcome,
)

__all__ = [
    # Artifact state
    "ArtifactState",
    "ArtifactStateEnum",
    "ArtifactType",
    "PRFAQStatus",
    "compute_prfaq_state",
    "compute_summary_state",
    # Assumption log
    "AssumptionLog",
    "LogEntry",
    "generate_log_id",
    # Feature scorecard
    "FeatureScorecard",
    "ScorecardDimension",
    "ScorecardIdentification",
    "generate_scorecard_id",
    # Region analysis
    "RegionAnalysis",
    "RegionRule",
    "format_rules_as_text",
    "generate_region_id",
    # Scenario
    "PREDEFINED_SCENARIOS",
    "Scenario",
    # Sensitivity result
    "DimensionSensitivity",
    "SensitivityResult",
    # Simulation attributes
    "SimulationAttributes",
    "SimulationLatentTraits",
    "SimulationObservables",
    # Simulation run
    "SimulationConfig",
    "SimulationRun",
    "generate_simulation_id",
    # Synth outcome
    "SynthOutcome",
]
