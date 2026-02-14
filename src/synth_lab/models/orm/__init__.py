"""
SQLAlchemy ORM models for synth-lab.

This package contains all SQLAlchemy ORM model definitions for database tables.
Models are organized by domain:

- base: DeclarativeBase, mixins, and custom types
- experiment: Experiment, InterviewGuide
- synth: Synth, SynthGroup
- research: ResearchExecution, Transcript
- document: ExperimentDocument
- material: ExperimentMaterial

Usage:
    from synth_lab.models.orm import Experiment, Synth

    # Or import specific modules
    from synth_lab.models.orm.experiment import Experiment, InterviewGuide
"""

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
from synth_lab.models.orm.material import ExperimentMaterial
from synth_lab.models.orm.research import ResearchExecution, Transcript
from synth_lab.models.orm.share import ExperimentShare, PermissionLevel, SynthGroupShare
from synth_lab.models.orm.synth import Synth, SynthGroup
from synth_lab.models.orm.tag import ExperimentTag, Tag
from synth_lab.models.orm.user import User

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
    # Research
    "ResearchExecution",
    "Transcript",
    # Document
    "ExperimentDocument",
    # Material
    "ExperimentMaterial",
    # Tag
    "Tag",
    "ExperimentTag",
    # User
    "User",
    # Share
    "ExperimentShare",
    "SynthGroupShare",
    "PermissionLevel",
]
