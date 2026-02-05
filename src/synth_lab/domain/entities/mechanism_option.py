"""
MechanismOption entity for narrative mechanism configuration.

A text option for a mechanism with a mapped numeric value.

Note: This is a convenience re-export. The primary definition is in
mechanism_definition.py to keep related entities together.

References:
    - Spec: specs/039-narrative-mechanism-config/spec.md
    - Data model: specs/039-narrative-mechanism-config/data-model.md
"""

from synth_lab.domain.entities.mechanism_definition import MechanismOption

__all__ = ["MechanismOption"]
