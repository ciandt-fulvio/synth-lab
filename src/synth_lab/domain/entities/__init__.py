"""Domain entities for synth-lab."""

from synth_lab.domain.entities.experiment import (
    Experiment,
    generate_experiment_id,
)
from synth_lab.domain.entities.experiment_material import (
    MATERIAL_TYPE_LABELS,
    MIME_TYPE_MAP,
    DescriptionStatus,
    ExperimentMaterial,
    ExperimentMaterialSummary,
    FileType,
    MaterialType,
    generate_material_id,
    get_file_type_from_mime,
)
from synth_lab.domain.entities.feature_mechanisms import FeatureMechanisms
from synth_lab.domain.entities.simulation_attributes import (
    SimulationAttributes,
    SimulationLatentTraits,
    SimulationObservables,
)
from synth_lab.domain.entities.simulation_context import SimulationContext
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
from synth_lab.domain.entities.user_sensitivities import UserSensitivities

__all__ = [
    # Experiment
    "Experiment",
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
    # Feature mechanisms (new in 038-mechanism-based-simulation)
    "FeatureMechanisms",
    # Simulation attributes
    "SimulationAttributes",
    "SimulationLatentTraits",
    "SimulationObservables",
    # Simulation context (for interview coherence)
    "SimulationContext",
    # Synth group
    "DEFAULT_SYNTH_GROUP_DESCRIPTION",
    "DEFAULT_SYNTH_GROUP_ID",
    "DEFAULT_SYNTH_GROUP_NAME",
    "SynthGroup",
    "generate_synth_group_id",
    # Synth outcome
    "SynthOutcome",
    "generate_outcome_id",
    # User sensitivities (new in 038-mechanism-based-simulation)
    "UserSensitivities",
]
