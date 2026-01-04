"""
SQLAlchemy ORM models for synth-lab.

This package contains all SQLAlchemy ORM model definitions for database tables.
Models are organized by domain:

- base: DeclarativeBase, mixins, and custom types
- experiment: Experiment, InterviewGuide
- synth: Synth, SynthGroup
- analysis: AnalysisRun, SynthOutcome, AnalysisCache
- research: ResearchExecution, Transcript
- exploration: Exploration, ScenarioNode
- insight: ChartInsight, SensitivityResult, RegionAnalysis
- document: ExperimentDocument

Usage:
    from synth_lab.models.orm import Experiment, Synth, AnalysisRun

    # Or import specific modules
    from synth_lab.models.orm.experiment import Experiment, InterviewGuide
"""

from synth_lab.models.orm.analysis import AnalysisCache, AnalysisRun, SynthOutcome
from synth_lab.models.orm.base import (
    Base,
    JSONVariant,
    MutableJSON,
    MutableJSONList,
    SoftDeleteMixin,
    TimestampMixin,
    to_dict,
)
from synth_lab.models.orm.document import ExperimentDocument
from synth_lab.models.orm.experiment import Experiment, InterviewGuide
from synth_lab.models.orm.exploration import Exploration, ScenarioNode
from synth_lab.models.orm.insight import ChartInsight, RegionAnalysis, SensitivityResult
from synth_lab.models.orm.research import ResearchExecution, Transcript
from synth_lab.models.orm.synth import Synth, SynthGroup

__all__ = [
    # Base
    "Base",
    "JSONVariant",
    "MutableJSON",
    "MutableJSONList",
    "SoftDeleteMixin",
    "TimestampMixin",
    "to_dict",
    # Experiment
    "Experiment",
    "InterviewGuide",
    # Synth
    "Synth",
    "SynthGroup",
    # Analysis
    "AnalysisRun",
    "SynthOutcome",
    "AnalysisCache",
    # Research
    "ResearchExecution",
    "Transcript",
    # Exploration
    "Exploration",
    "ScenarioNode",
    # Insight
    "ChartInsight",
    "SensitivityResult",
    "RegionAnalysis",
    # Document
    "ExperimentDocument",
]
