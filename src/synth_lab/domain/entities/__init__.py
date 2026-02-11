"""Domain entities for synth-lab."""

from synth_lab.domain.entities.analysis_run import (
    AggregatedOutcomes,
    AnalysisConfig,
    AnalysisRun,
    generate_analysis_id,
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
    ScatterCorrelationChart,
    SynthDistribution,
    TrendlinePoint,
)
from synth_lab.domain.entities.chart_insight import ChartInsight
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
    generate_experiment_id,
)
from synth_lab.domain.entities.experiment_material import (
    DescriptionStatus,
    ExperimentMaterial,
    ExperimentMaterialSummary,
    FileType,
    MaterialType,
    MATERIAL_TYPE_LABELS,
    MIME_TYPE_MAP,
    generate_material_id,
    get_file_type_from_mime,
)
from synth_lab.domain.entities.emergent_state import (
    EmergentState,
    InteractionContribution,
)
from synth_lab.domain.entities.explainability import (
    PDPComparison,
    PDPPoint,
    PDPResult,
    ShapContribution,
    ShapExplanation,
    ShapSummary,
)
from synth_lab.domain.entities.feature_mechanisms import FeatureMechanisms
from synth_lab.domain.entities.feature_type import FeatureType, generate_feature_type_id
from synth_lab.domain.entities.mechanism_definition import (
    MechanismDefinition,
    MechanismOption,
    generate_mechanism_definition_id,
)
from synth_lab.domain.entities.narrative_response import (
    NarrativeResponse,
    SelectedMechanism,
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
from synth_lab.domain.entities.scenario import (
    PREDEFINED_SCENARIOS,
    Scenario,
)
from synth_lab.domain.entities.simulation_attributes import (
    SimulationAttributes,
    SimulationLatentTraits,
    SimulationObservables,
)
from synth_lab.domain.entities.user_sensitivities import UserSensitivities
from synth_lab.domain.entities.simulation_context import SimulationContext
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
    # AI-Generated Insights (new in 023-quantitative-ai-insights)
    "ChartInsight",
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
    "ScatterCorrelationChart",
    "SynthDistribution",
    "TrendlinePoint",
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
    # Emergent state (new in 038-mechanism-based-simulation)
    "EmergentState",
    "InteractionContribution",
    # Experiment (updated in v7 - embedded scorecard)
    "Experiment",
    "ScorecardData",
    "generate_experiment_id",
    # Experiment Material (new in 001-experiment-materials)
    "DescriptionStatus",
    "ExperimentMaterial",
    "ExperimentMaterialSummary",
    "FileType",
    "MaterialType",
    "MATERIAL_TYPE_LABELS",
    "MIME_TYPE_MAP",
    "generate_material_id",
    "get_file_type_from_mime",
    # Explainability
    "PDPComparison",
    "PDPPoint",
    "PDPResult",
    "ShapContribution",
    "ShapExplanation",
    "ShapSummary",
    # Feature mechanisms (new in 038-mechanism-based-simulation)
    "FeatureMechanisms",
    # Feature types (new in 039-narrative-mechanism-config)
    "FeatureType",
    "generate_feature_type_id",
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
    # Scenario
    "PREDEFINED_SCENARIOS",
    "Scenario",
    # Simulation attributes
    "SimulationAttributes",
    "SimulationLatentTraits",
    "SimulationObservables",
    # Simulation context (for interview coherence)
    "SimulationContext",
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
    # User sensitivities (new in 038-mechanism-based-simulation)
    "UserSensitivities",
    # Mechanism configuration (new in 039-narrative-mechanism-config)
    "MechanismDefinition",
    "MechanismOption",
    "generate_mechanism_definition_id",
    "NarrativeResponse",
    "SelectedMechanism",
]
