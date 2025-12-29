"""Domain entities for synth-lab."""

from synth_lab.domain.entities.analysis_run import (
    AggregatedOutcomes,
    AnalysisConfig,
    AnalysisRun,
    generate_analysis_id,
)
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
from synth_lab.domain.entities.chart_data import (
    AttributeCorrelation,
    AttributeCorrelationChart,
    BoxPlotChart,
    BoxPlotStats,
    CorrelationPoint,
    CorrelationStats,
    FailureHeatmapChart,
    HeatmapCell,
    OutcomeDistributionChart,
    RegionBoxPlot,
    SankeyChart,
    SankeyLink,
    SankeyNode,
    ScatterCorrelationChart,
    SynthDistribution,
    TrendlinePoint,
    TryVsSuccessChart,
    TryVsSuccessPoint,
)
from synth_lab.domain.entities.cluster_result import (
    ClusterProfile,
    ClusterRadar,
    DendrogramBranch,
    DendrogramChart,
    DendrogramNode,
    DendrogramTreeNode,
    ElbowDataPoint,
    HierarchicalResult,
    KMeansResult,
    PCAScatterChart,
    PCAScatterPoint,
    RadarAxis,
    RadarChart,
    SuggestedCut,
)
from synth_lab.domain.entities.experiment import (
    Experiment,
    ScorecardData,
    ScorecardDimension as ExperimentScorecardDimension,
    generate_experiment_id,
)
from synth_lab.domain.entities.explainability import (
    PDPComparison,
    PDPPoint,
    PDPResult,
    ShapContribution,
    ShapExplanation,
    ShapSummary,
)
from synth_lab.domain.entities.feature_scorecard import (
    FeatureScorecard,
    ScorecardDimension,
    ScorecardIdentification,
    generate_scorecard_id,
)
from synth_lab.domain.entities.outlier_result import (
    ExtremeCasesTable,
    ExtremeSynth,
    OutlierResult,
    OutlierSynth,
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
from synth_lab.domain.entities.synth_group import (
    DEFAULT_SYNTH_GROUP_DESCRIPTION,
    DEFAULT_SYNTH_GROUP_ID,
    DEFAULT_SYNTH_GROUP_NAME,
    SynthGroup,
    generate_synth_group_id,
)
from synth_lab.domain.entities.synth_outcome import (
    SynthOutcome,
    generate_outcome_id,
)

__all__ = [
    # Analysis run (new in v7)
    "AggregatedOutcomes",
    "AnalysisConfig",
    "AnalysisRun",
    "generate_analysis_id",
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
    # Chart data (analysis)
    "AttributeCorrelation",
    "AttributeCorrelationChart",
    "BoxPlotChart",
    "BoxPlotStats",
    "CorrelationPoint",
    "CorrelationStats",
    "FailureHeatmapChart",
    "HeatmapCell",
    "OutcomeDistributionChart",
    "RegionBoxPlot",
    "SankeyChart",
    "SankeyLink",
    "SankeyNode",
    "ScatterCorrelationChart",
    "SynthDistribution",
    "TrendlinePoint",
    "TryVsSuccessChart",
    "TryVsSuccessPoint",
    # Cluster result
    "ClusterProfile",
    "ClusterRadar",
    "DendrogramBranch",
    "DendrogramChart",
    "DendrogramNode",
    "DendrogramTreeNode",
    "ElbowDataPoint",
    "HierarchicalResult",
    "KMeansResult",
    "PCAScatterChart",
    "PCAScatterPoint",
    "RadarAxis",
    "RadarChart",
    "SuggestedCut",
    # Experiment (updated in v7 - embedded scorecard)
    "Experiment",
    "ExperimentScorecardDimension",
    "ScorecardData",
    "generate_experiment_id",
    # Explainability
    "PDPComparison",
    "PDPPoint",
    "PDPResult",
    "ShapContribution",
    "ShapExplanation",
    "ShapSummary",
    # Feature scorecard (legacy)
    "FeatureScorecard",
    "ScorecardDimension",
    "ScorecardIdentification",
    "generate_scorecard_id",
    # Outlier result
    "ExtremeCasesTable",
    "ExtremeSynth",
    "OutlierResult",
    "OutlierSynth",
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
    # Simulation run (legacy)
    "SimulationConfig",
    "SimulationRun",
    "generate_simulation_id",
    # Synth group
    "DEFAULT_SYNTH_GROUP_DESCRIPTION",
    "DEFAULT_SYNTH_GROUP_ID",
    "DEFAULT_SYNTH_GROUP_NAME",
    "SynthGroup",
    "generate_synth_group_id",
    # Synth outcome (updated in v7 - uses analysis_id)
    "SynthOutcome",
    "generate_outcome_id",
]
