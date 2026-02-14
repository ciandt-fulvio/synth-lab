"""
T004 [TEST] CausalModel + CausalEdge entity tests.

Tests for causal model domain entities including ID generation,
field validation, userVar enum, and Likert option constraints.

References:
    - Data model: specs/042-quantitative-analysis/data-model.md
"""

import pytest

from synth_lab.domain.entities.causal_model import (
    VALID_USER_VARS,
    CausalEdge,
    CausalModel,
    LikertOption,
    generate_causal_model_id,
)


class TestGenerateCausalModelId:
    """Tests for causal model ID generation."""

    def test_generates_cm_prefix(self) -> None:
        """Verify ID starts with 'cm_' prefix."""
        cm_id = generate_causal_model_id()
        assert cm_id.startswith("cm_"), f"ID should start with 'cm_': {cm_id}"

    def test_generates_8_char_hex_suffix(self) -> None:
        """Verify ID has 8-character hex suffix after prefix."""
        cm_id = generate_causal_model_id()
        suffix = cm_id[3:]  # Remove 'cm_' prefix
        assert len(suffix) == 8, f"Suffix should be 8 chars: {suffix}"
        int(suffix, 16)  # Valid hex

    def test_generates_unique_ids(self) -> None:
        """Verify IDs are unique."""
        ids = {generate_causal_model_id() for _ in range(100)}
        assert len(ids) == 100, "Generated IDs should be unique"


class TestLikertOption:
    """Tests for LikertOption model."""

    def test_valid_option(self) -> None:
        """Create a valid Likert option."""
        opt = LikertOption(text="Strong effect claim.", mu=0.80, sigma=0.15)
        assert opt.text == "Strong effect claim."
        assert opt.mu == 0.80
        assert opt.sigma == 0.15

    def test_mu_must_be_between_0_and_1(self) -> None:
        """Mu must be in [0, 1]."""
        with pytest.raises(ValueError):
            LikertOption(text="test", mu=1.5, sigma=0.1)
        with pytest.raises(ValueError):
            LikertOption(text="test", mu=-0.1, sigma=0.1)

    def test_sigma_must_be_between_0_and_1(self) -> None:
        """Sigma must be in [0, 1]."""
        with pytest.raises(ValueError):
            LikertOption(text="test", mu=0.5, sigma=1.5)
        with pytest.raises(ValueError):
            LikertOption(text="test", mu=0.5, sigma=-0.1)


class TestCausalEdge:
    """Tests for CausalEdge entity."""

    def _make_options(self) -> list[LikertOption]:
        """Create 5 valid Likert options."""
        return [
            LikertOption(text="Forte efeito.", mu=0.80, sigma=0.15),
            LikertOption(text="Efeito significativo.", mu=0.65, sigma=0.25),
            LikertOption(text="Não sei dizer.", mu=0.50, sigma=0.50),
            LikertOption(text="Efeito fraco.", mu=0.30, sigma=0.25),
            LikertOption(text="Sem efeito.", mu=0.15, sigma=0.15),
        ]

    def test_valid_edge(self) -> None:
        """Create a valid causal edge."""
        edge = CausalEdge(
            id="e1",
            from_node="Idade",
            to_node="Familiaridade Digital",
            user_var="ageNorm",
            direction=-1,
            header="A respeito de quanto a Familiaridade Digital é influenciada pela idade",
            options=self._make_options(),
            default_option=0,
        )
        assert edge.id == "e1"
        assert edge.direction == -1
        assert edge.selected_option is None

    def test_user_var_must_be_valid_enum(self) -> None:
        """userVar must be one of the 10 valid values."""
        with pytest.raises(ValueError):
            CausalEdge(
                id="e1",
                from_node="A",
                to_node="B",
                user_var="invalidVar",
                direction=1,
                header="test",
                options=self._make_options(),
                default_option=0,
            )

    def test_all_valid_user_vars(self) -> None:
        """Verify all 10 userVars are accepted."""
        for var in VALID_USER_VARS:
            edge = CausalEdge(
                id="e1",
                from_node="A",
                to_node="B",
                user_var=var,
                direction=1,
                header="test",
                options=self._make_options(),
                default_option=0,
            )
            assert edge.user_var == var

    def test_direction_must_be_1_or_minus_1(self) -> None:
        """Direction must be exactly 1 or -1."""
        with pytest.raises(ValueError):
            CausalEdge(
                id="e1",
                from_node="A",
                to_node="B",
                user_var="ageNorm",
                direction=0,
                header="test",
                options=self._make_options(),
                default_option=0,
            )

    def test_options_must_have_exactly_5(self) -> None:
        """Options list must have exactly 5 items."""
        with pytest.raises(ValueError):
            CausalEdge(
                id="e1",
                from_node="A",
                to_node="B",
                user_var="ageNorm",
                direction=1,
                header="test",
                options=self._make_options()[:3],
                default_option=0,
            )

    def test_default_option_range_0_to_4(self) -> None:
        """Default option must be in [0, 4]."""
        with pytest.raises(ValueError):
            CausalEdge(
                id="e1",
                from_node="A",
                to_node="B",
                user_var="ageNorm",
                direction=1,
                header="test",
                options=self._make_options(),
                default_option=5,
            )

    def test_selected_option_nullable(self) -> None:
        """Selected option can be None (not yet answered)."""
        edge = CausalEdge(
            id="e1",
            from_node="A",
            to_node="B",
            user_var="ageNorm",
            direction=1,
            header="test",
            options=self._make_options(),
            default_option=2,
        )
        assert edge.selected_option is None

    def test_selected_option_range_0_to_4(self) -> None:
        """Selected option must be in [0, 4] when set."""
        with pytest.raises(ValueError):
            CausalEdge(
                id="e1",
                from_node="A",
                to_node="B",
                user_var="ageNorm",
                direction=1,
                header="test",
                options=self._make_options(),
                default_option=2,
                selected_option=5,
            )


class TestCausalModel:
    """Tests for CausalModel entity."""

    def _make_options(self) -> list[LikertOption]:
        return [
            LikertOption(text="Forte.", mu=0.80, sigma=0.15),
            LikertOption(text="Significativo.", mu=0.65, sigma=0.25),
            LikertOption(text="Incerto.", mu=0.50, sigma=0.50),
            LikertOption(text="Fraco.", mu=0.30, sigma=0.25),
            LikertOption(text="Nenhum.", mu=0.15, sigma=0.15),
        ]

    def test_valid_model(self) -> None:
        """Create a valid causal model."""
        model = CausalModel(
            experiment_id="exp_12345678",
            label="Modelo Causal: Pix Parcelado",
            intercept_mu=0.1,
            intercept_sigma=0.4,
            nodes=["Idade", "Renda", "Escolaridade", "Confiança", "Valor", "Digital", "Adoção"],
        )
        assert model.id.startswith("cm_")
        assert model.experiment_id == "exp_12345678"
        assert len(model.nodes) == 7

    def test_nodes_count_7_to_10(self) -> None:
        """Nodes list must have 7-10 items."""
        # Too few
        with pytest.raises(ValueError):
            CausalModel(
                experiment_id="exp_12345678",
                label="test",
                intercept_mu=0.1,
                intercept_sigma=0.4,
                nodes=["A", "B", "C"],
            )
        # Too many
        with pytest.raises(ValueError):
            CausalModel(
                experiment_id="exp_12345678",
                label="test",
                intercept_mu=0.1,
                intercept_sigma=0.4,
                nodes=[f"N{i}" for i in range(11)],
            )

    def test_intercept_mu_range(self) -> None:
        """Intercept mu must be in [-1.0, 1.0]."""
        with pytest.raises(ValueError):
            CausalModel(
                experiment_id="exp_12345678",
                label="test",
                intercept_mu=1.5,
                intercept_sigma=0.4,
                nodes=["A", "B", "C", "D", "E", "F", "G"],
            )

    def test_intercept_sigma_range(self) -> None:
        """Intercept sigma must be in [0.1, 1.0]."""
        with pytest.raises(ValueError):
            CausalModel(
                experiment_id="exp_12345678",
                label="test",
                intercept_mu=0.1,
                intercept_sigma=0.05,
                nodes=["A", "B", "C", "D", "E", "F", "G"],
            )

    def test_model_dump_json(self) -> None:
        """Verify model_dump produces valid JSON-serializable dict."""
        model = CausalModel(
            experiment_id="exp_12345678",
            label="Test",
            intercept_mu=0.1,
            intercept_sigma=0.4,
            nodes=["A", "B", "C", "D", "E", "F", "G"],
        )
        data = model.model_dump(mode="json")
        assert isinstance(data["created_at"], str)
        assert data["nodes"] == ["A", "B", "C", "D", "E", "F", "G"]
