"""
T005 [TEST] SimulationRun + AnalysisInterpretation entity tests.

Tests for simulation result entities including ID generation,
stats schema validation, section enum, and constraints.

References:
    - Data model: specs/042-quantitative-analysis/data-model.md
"""

import pytest

from synth_lab.domain.entities.simulation_run import (
    VALID_SECTIONS,
    AnalysisInterpretation,
    SimulationRun,
    generate_interpretation_id,
    generate_simulation_run_id,
)


class TestGenerateSimulationRunId:
    """Tests for simulation run ID generation."""

    def test_generates_sr_prefix(self) -> None:
        """Verify ID starts with 'sr_' prefix."""
        sr_id = generate_simulation_run_id()
        assert sr_id.startswith("sr_"), f"ID should start with 'sr_': {sr_id}"

    def test_generates_8_char_hex_suffix(self) -> None:
        """Verify ID has 8-character hex suffix after prefix."""
        sr_id = generate_simulation_run_id()
        suffix = sr_id[3:]
        assert len(suffix) == 8, f"Suffix should be 8 chars: {suffix}"
        int(suffix, 16)

    def test_generates_unique_ids(self) -> None:
        """Verify IDs are unique."""
        ids = {generate_simulation_run_id() for _ in range(100)}
        assert len(ids) == 100


class TestGenerateInterpretationId:
    """Tests for interpretation ID generation."""

    def test_generates_ai_prefix(self) -> None:
        """Verify ID starts with 'ai_' prefix."""
        ai_id = generate_interpretation_id()
        assert ai_id.startswith("ai_"), f"ID should start with 'ai_': {ai_id}"

    def test_generates_8_char_hex_suffix(self) -> None:
        """Verify ID has 8-character hex suffix after prefix."""
        ai_id = generate_interpretation_id()
        suffix = ai_id[3:]
        assert len(suffix) == 8
        int(suffix, 16)


class TestSimulationRun:
    """Tests for SimulationRun entity."""

    def _make_stats(self) -> dict:
        return {"mean": 42.3, "median": 41.8, "std": 3.2, "p10": 38.1, "p90": 46.5}

    def _make_segments(self) -> dict:
        return {
            "age": {"18-29": {"rate": 55.2, "count": 45}},
            "income": {"baixa": {"rate": 35.4, "count": 50}},
            "education": {"baixa": {"rate": 33.1, "count": 48}},
        }

    def test_valid_simulation_run(self) -> None:
        """Create a valid simulation run."""
        run = SimulationRun(
            experiment_id="exp_12345678",
            causal_model_id="cm_abcdef12",
            n_synths=150,
            selections={"e1": 0, "e2": 2},
            stats=self._make_stats(),
            distribution=[0.42, 0.43, 0.41],
            segments=self._make_segments(),
            sensitivity=[{"edge_id": "e1", "header": "test", "impact": 12.5, "mean_low": 48.8, "mean_high": 36.3}],
        )
        assert run.id.startswith("sr_")
        assert run.n_iterations == 3000
        assert run.n_synths == 150

    def test_stats_must_have_required_keys(self) -> None:
        """Stats dict must contain mean, median, std, p10, p90."""
        with pytest.raises(ValueError):
            SimulationRun(
                experiment_id="exp_12345678",
                causal_model_id="cm_abcdef12",
                n_synths=150,
                selections={"e1": 0},
                stats={"mean": 42.3},  # Missing keys
                distribution=[0.42],
                segments=self._make_segments(),
                sensitivity=[],
            )

    def test_segments_must_have_required_keys(self) -> None:
        """Segments dict must contain age, income, education."""
        with pytest.raises(ValueError):
            SimulationRun(
                experiment_id="exp_12345678",
                causal_model_id="cm_abcdef12",
                n_synths=150,
                selections={"e1": 0},
                stats=self._make_stats(),
                distribution=[0.42],
                segments={"age": {}},  # Missing income, education
                sensitivity=[],
            )

    def test_n_synths_must_be_positive(self) -> None:
        """n_synths must be > 0."""
        with pytest.raises(ValueError):
            SimulationRun(
                experiment_id="exp_12345678",
                causal_model_id="cm_abcdef12",
                n_synths=0,
                selections={},
                stats=self._make_stats(),
                distribution=[],
                segments=self._make_segments(),
                sensitivity=[],
            )

    def test_model_dump_json(self) -> None:
        """Verify model_dump mode=json works."""
        run = SimulationRun(
            experiment_id="exp_12345678",
            causal_model_id="cm_abcdef12",
            n_synths=100,
            selections={"e1": 0},
            stats=self._make_stats(),
            distribution=[0.42],
            segments=self._make_segments(),
            sensitivity=[],
        )
        data = run.model_dump(mode="json")
        assert isinstance(data["created_at"], str)
        assert data["n_iterations"] == 3000


class TestAnalysisInterpretation:
    """Tests for AnalysisInterpretation entity."""

    def test_valid_interpretation(self) -> None:
        """Create a valid analysis interpretation."""
        interp = AnalysisInterpretation(
            simulation_run_id="sr_12345678",
            section="distribution",
            raw_text="Com 80% de confiança, a taxa fica entre 38% e 47%.",
            ai_text="A taxa de adoção do Pix Parcelado fica entre 38% e 47%.",
        )
        assert interp.id.startswith("ai_")
        assert interp.section == "distribution"
        assert interp.model == "gpt-4o-mini"

    def test_section_must_be_valid_enum(self) -> None:
        """Section must be one of: distribution, segments, sensitivity."""
        with pytest.raises(ValueError):
            AnalysisInterpretation(
                simulation_run_id="sr_12345678",
                section="invalid_section",
                raw_text="test",
                ai_text="test",
            )

    def test_all_valid_sections(self) -> None:
        """Verify all 3 valid sections are accepted."""
        for section in VALID_SECTIONS:
            interp = AnalysisInterpretation(
                simulation_run_id="sr_12345678",
                section=section,
                raw_text="test",
                ai_text="test",
            )
            assert interp.section == section

    def test_custom_model(self) -> None:
        """Allow custom model specification."""
        interp = AnalysisInterpretation(
            simulation_run_id="sr_12345678",
            section="segments",
            raw_text="test",
            ai_text="test",
            model="gpt-5.1",
        )
        assert interp.model == "gpt-5.1"
