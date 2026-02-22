"""
Simulation run entities for quantitative analysis.

Represents Monte Carlo simulation results and AI-generated interpretations.

References:
    - Spec: specs/042-quantitative-analysis/spec.md
    - Data model: specs/042-quantitative-analysis/data-model.md
"""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, field_validator

# Valid interpretation sections
VALID_SECTIONS = frozenset({"distribution", "segments", "sensitivity"})

# Required keys in stats dict
REQUIRED_STATS_KEYS = frozenset({"mean", "median", "std", "p10", "p90"})

# Required keys in segments dict
REQUIRED_SEGMENT_KEYS = frozenset({"age", "income", "education"})


def generate_simulation_run_id() -> str:
    """Generate a simulation run ID with sr_ prefix and 8-char hex suffix."""
    return f"sr_{secrets.token_hex(4)}"


def generate_interpretation_id() -> str:
    """Generate an interpretation ID with ai_ prefix and 8-char hex suffix."""
    return f"ai_{secrets.token_hex(4)}"


class SimulationRun(BaseModel):
    """
    Result of a Monte Carlo simulation run.

    Immutable after creation — a new run is created for each simulation.
    """

    id: str = Field(
        default_factory=generate_simulation_run_id,
        pattern=r"^sr_[a-f0-9]{8}$",
        description="Unique simulation run ID.",
    )
    experiment_id: str = Field(description="Parent experiment ID.")
    causal_model_id: str = Field(description="Causal model used for simulation.")
    n_iterations: int = Field(default=3000, gt=0, description="Monte Carlo iterations.")
    n_synths: int = Field(gt=0, description="Number of synths used.")
    selections: dict[str, int] = Field(
        description="Edge selections at simulation time: {edge_id: option_index}."
    )
    stats: dict[str, float] = Field(
        description="Aggregated stats: {mean, median, std, p10, p90}."
    )
    distribution: list[float] = Field(
        description="Adoption rate per iteration (array of floats)."
    )
    segments: dict[str, Any] = Field(
        description="Results by segment: {age, income, education}."
    )
    sensitivity: list[dict[str, Any]] = Field(
        description="Sensitivity per edge: [{edge_id, header, impact, mean_low, mean_high}]."
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp.",
    )

    @field_validator("stats")
    @classmethod
    def validate_stats_keys(cls, v: dict[str, float]) -> dict[str, float]:
        """Stats must contain required keys."""
        missing = REQUIRED_STATS_KEYS - set(v.keys())
        if missing:
            raise ValueError(f"stats missing required keys: {missing}")
        return v

    @field_validator("segments")
    @classmethod
    def validate_segments_keys(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Segments must contain age, income, education."""
        missing = REQUIRED_SEGMENT_KEYS - set(v.keys())
        if missing:
            raise ValueError(f"segments missing required keys: {missing}")
        return v


class AnalysisInterpretation(BaseModel):
    """
    AI-generated interpretation for a simulation result section.

    One per section (distribution, segments, sensitivity) per run.
    """

    id: str = Field(
        default_factory=generate_interpretation_id,
        pattern=r"^ai_[a-f0-9]{8}$",
        description="Unique interpretation ID.",
    )
    simulation_run_id: str = Field(description="Parent simulation run ID.")
    section: str = Field(description="Section: distribution, segments, or sensitivity.")
    raw_text: str = Field(description="Raw statistical interpretation (no LLM).")
    ai_text: str = Field(description="AI-generated contextual interpretation.")
    model: str = Field(default="gpt-4o-mini", max_length=50, description="LLM model used.")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp.",
    )

    @field_validator("section")
    @classmethod
    def validate_section(cls, v: str) -> str:
        """Section must be one of the valid values."""
        if v not in VALID_SECTIONS:
            raise ValueError(f"section must be one of {sorted(VALID_SECTIONS)}, got '{v}'")
        return v


def generate_batch_id() -> str:
    """Generate a simulation batch ID with sb_ prefix and 8-char hex suffix."""
    return f"sb_{secrets.token_hex(4)}"


class SimulationBatch(BaseModel):
    """
    Groups multiple scenario runs for one experiment.
    """

    id: str = Field(
        default_factory=generate_batch_id,
        pattern=r"^sb_[a-f0-9]{8}$",
        description="Unique batch ID.",
    )
    experiment_id: str = Field(description="Parent experiment ID.")
    causal_model_id: str = Field(description="Causal model used.")
    n_scenarios: int = Field(gt=0, description="Number of scenarios.")
    n_synths: int = Field(gt=0, description="Number of synths per scenario.")
    n_repetitions: int = Field(default=10, gt=0, description="MC repetitions per synth.")
    status: str = Field(default="running", description="running/completed/failed.")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp.",
    )

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid = {"running", "completed", "failed"}
        if v not in valid:
            raise ValueError(f"status must be one of {sorted(valid)}, got '{v}'")
        return v


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Generate IDs
    total_tests += 1
    try:
        sr_id = generate_simulation_run_id()
        ai_id = generate_interpretation_id()
        if not sr_id.startswith("sr_"):
            all_validation_failures.append(f"sr_id should start with 'sr_': {sr_id}")
        if not ai_id.startswith("ai_"):
            all_validation_failures.append(f"ai_id should start with 'ai_': {ai_id}")
    except Exception as e:
        all_validation_failures.append(f"ID generation failed: {e}")

    # Test 2: Valid run
    total_tests += 1
    try:
        run = SimulationRun(
            experiment_id="exp_12345678",
            causal_model_id="cm_abcdef12",
            n_synths=100,
            selections={"e1": 0, "e2": 2},
            stats={"mean": 42.3, "median": 41.8, "std": 3.2, "p10": 38.1, "p90": 46.5},
            distribution=[0.42, 0.43],
            segments={
                "age": {"18-29": {"rate": 55.2, "count": 45}},
                "income": {"baixa": {"rate": 35.4, "count": 50}},
                "education": {"baixa": {"rate": 33.1, "count": 48}},
            },
            sensitivity=[],
        )
        if run.n_iterations != 3000:
            all_validation_failures.append(f"Default iterations should be 3000: {run.n_iterations}")
    except Exception as e:
        all_validation_failures.append(f"Create run failed: {e}")

    # Test 3: Valid interpretation
    total_tests += 1
    try:
        interp = AnalysisInterpretation(
            simulation_run_id="sr_12345678",
            section="distribution",
            raw_text="Raw text",
            ai_text="AI text",
        )
        if interp.model != "gpt-4o-mini":
            all_validation_failures.append(f"Default model should be gpt-4o-mini: {interp.model}")
    except Exception as e:
        all_validation_failures.append(f"Create interpretation failed: {e}")

    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
