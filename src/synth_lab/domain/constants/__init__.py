"""
Domain constants for synth-lab.

Contains metadata, mappings, and configuration constants used
across the application.
"""

from synth_lab.domain.constants.demographic_factors import (
    DISABILITY_SEVERITY_MAP,
    EDUCATION_FACTOR_MAP,
    FAMILY_PRESSURE_MAP,
)

__all__ = [
    "EDUCATION_FACTOR_MAP",
    "DISABILITY_SEVERITY_MAP",
    "FAMILY_PRESSURE_MAP",
]
