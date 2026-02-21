"""
Causal model entities for quantitative analysis.

Represents a causal DAG with typed nodes (5 types) and edges, where each edge
is either a Likert-scale assertion (calibratable) or a fixed structural edge.

Node types:
    - DEMOGRAPHIC: root nodes from synth data (age, income, etc.)
    - SENSITIVITY: user behavioral traits (from YAML rules or custom LLM configs)
    - PRODUCT: exogenous product/feature characteristics (calibratable low/medium/high)
    - INTERACTION: endogenous nodes combining user + product signals
    - OUTCOME: final adoption/conversion node

References:
    - Spec: specs/042-quantitative-analysis/spec.md
    - Data model: specs/042-quantitative-analysis/data-model.md
"""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator

# Valid userVar values (10 fixed extractors)
VALID_USER_VARS = frozenset({
    "ageNorm",
    "incomeNorm",
    "eduNorm",
    "familySizeNorm",
    "hasVisualDisab",
    "hasMotorDisab",
    "digitalCapability",
    "riskAversion",
    "institutionalTrust",
    "frictionTolerance",
})


class NodeType(str, Enum):
    """Type of node in the causal DAG."""

    DEMOGRAPHIC = "demographic"
    SENSITIVITY = "sensitivity"
    PRODUCT = "product"
    INTERACTION = "interaction"
    OUTCOME = "outcome"


# Valid product calibration levels and their numeric values
PRODUCT_CALIBRATION_VALUES = {
    "low": 0.2,
    "medium": 0.5,
    "high": 0.8,
}


def generate_causal_model_id() -> str:
    """Generate a causal model ID with cm_ prefix and 8-char hex suffix."""
    return f"cm_{secrets.token_hex(4)}"


class LikertOption(BaseModel):
    """Single Likert option with hidden mu/sigma parameters."""

    text: str = Field(description="Self-contained assertion text in Portuguese BR.")
    mu: float = Field(ge=0.0, le=1.0, description="Coupling strength [0, 1].")
    sigma: float = Field(ge=0.0, le=1.0, description="Uncertainty fraction [0, 1].")


class CausalEdge(BaseModel):
    """
    Edge in the causal DAG.

    Each edge represents a causal assertion between two nodes.
    - "likert" edges have 5 options the PM evaluates.
    - "fixed" edges are structural (e.g., demographic→sensitivity) with no options.
    """

    id: str = Field(description="Edge identifier (e.g., 'e1', 'e2').")
    from_node: str = Field(max_length=50, description="Source node name.")
    to_node: str = Field(max_length=50, description="Target node name.")
    user_var: str | None = Field(
        default=None,
        description="Mapped userVar from synth attributes (null for product/interaction edges).",
    )
    direction: int = Field(description="Relationship direction: 1 (direct) or -1 (inverse).")
    header: str = Field(max_length=300, description="Contextual header for the assertion.")
    options: list[LikertOption] = Field(
        default_factory=list,
        description="5 Likert options for 'likert' edges, empty for 'fixed' edges.",
    )
    default_option: int = Field(
        default=0, ge=0, le=4, description="LLM-suggested default option index."
    )
    selected_option: int | None = Field(
        default=None,
        description="PM's selected option index (null = not answered).",
    )
    edge_type: str = Field(
        default="likert",
        description="Edge type: 'likert' (calibratable with 5 options) or 'fixed' (structural).",
    )
    weight: float | None = Field(
        default=None,
        description="LLM-suggested weight for interaction edges.",
    )

    @field_validator("user_var")
    @classmethod
    def validate_user_var(cls, v: str | None) -> str | None:
        """Ensure userVar is one of the 10 valid values when set."""
        if v is not None and v not in VALID_USER_VARS:
            raise ValueError(
                f"user_var must be one of {sorted(VALID_USER_VARS)} or None, got '{v}'"
            )
        return v

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, v: int) -> int:
        """Direction must be 1 or -1."""
        if v not in (1, -1):
            raise ValueError(f"direction must be 1 or -1, got {v}")
        return v

    @field_validator("options")
    @classmethod
    def validate_options_count(cls, v: list[LikertOption]) -> list[LikertOption]:
        """Must have exactly 5 options for likert edges, 0 for fixed."""
        if len(v) not in (0, 5):
            raise ValueError(f"options must have exactly 0 or 5 items, got {len(v)}")
        return v

    @field_validator("selected_option")
    @classmethod
    def validate_selected_option(cls, v: int | None) -> int | None:
        """Selected option must be in [0, 4] when set."""
        if v is not None and (v < 0 or v > 4):
            raise ValueError(f"selected_option must be 0-4 or None, got {v}")
        return v

    @field_validator("edge_type")
    @classmethod
    def validate_edge_type(cls, v: str) -> str:
        """Edge type must be 'likert' or 'fixed'."""
        if v not in ("likert", "fixed"):
            raise ValueError(f"edge_type must be 'likert' or 'fixed', got '{v}'")
        return v


class CausalNode(BaseModel):
    """Metadata for a node in the causal DAG."""

    name: str = Field(description="Node display name.")
    node_type: NodeType = Field(description="Type of node.")
    sensitivity_key: str | None = Field(
        default=None,
        description="Sensitivity key (YAML key or 'custom_N') for sensitivity nodes.",
    )
    custom_config: dict | None = Field(
        default=None,
        description="Custom sensitivity config {base, rules, strength} for LLM-created.",
    )
    product_calibration: str | None = Field(
        default=None,
        description="Product calibration level: 'low', 'medium', or 'high'.",
    )
    product_description: str | None = Field(
        default=None,
        description="LLM-generated description for product nodes.",
    )
    description: str | None = Field(
        default=None,
        description="LLM-generated explanation of this node's role in the causal model.",
    )
    # Premissa fields (interaction + outcome nodes only)
    header: str | None = Field(
        default=None,
        description="Contextual header for the node's premissa assertion.",
    )
    options: list[LikertOption] = Field(
        default_factory=list,
        description="5 Likert options for interaction/outcome nodes.",
    )
    default_option: int = Field(
        default=2, ge=0, le=4, description="LLM-suggested default option index.",
    )
    selected_option: int | None = Field(
        default=None,
        description="PM's selected option index (null = not answered).",
    )

    @field_validator("product_calibration")
    @classmethod
    def validate_calibration(cls, v: str | None) -> str | None:
        """Product calibration must be low/medium/high when set."""
        if v is not None and v not in PRODUCT_CALIBRATION_VALUES:
            raise ValueError(
                f"product_calibration must be one of {list(PRODUCT_CALIBRATION_VALUES)}, got '{v}'"
            )
        return v


class CausalModel(BaseModel):
    """
    Causal model generated by LLM.

    Contains the DAG structure with typed nodes and metadata.
    Edges are stored separately but logically belong to this model.
    1:1 relationship with experiment.
    """

    id: str = Field(
        default_factory=generate_causal_model_id,
        pattern=r"^cm_[a-f0-9]{8}$",
        description="Unique causal model ID.",
    )
    experiment_id: str = Field(description="Parent experiment ID.")
    label: str = Field(max_length=200, description="Model title (LLM-generated).")
    intercept_mu: float = Field(ge=-3.0, le=3.0, description="Intercept mean [-3, 3].")
    intercept_sigma: float = Field(ge=0.1, le=1.0, description="Intercept std dev [0.1, 1].")
    nodes: list[str] = Field(description="DAG node names.")
    node_metadata: dict[str, dict] | None = Field(
        default=None,
        description="Per-node metadata keyed by node name. Each value is a CausalNode dict.",
    )
    edges: list[CausalEdge] = Field(default_factory=list, description="DAG edges.")
    raw_llm_response: dict[str, Any] | None = Field(
        default=None, description="Raw LLM response for debugging."
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp.",
    )


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Generate ID
    total_tests += 1
    try:
        cm_id = generate_causal_model_id()
        if not cm_id.startswith("cm_"):
            all_validation_failures.append(f"ID should start with 'cm_': {cm_id}")
        if len(cm_id) != 11:
            all_validation_failures.append(f"ID should be 11 chars: {len(cm_id)}")
    except Exception as e:
        all_validation_failures.append(f"Generate ID failed: {e}")

    # Test 2: Create valid model with node_metadata
    total_tests += 1
    try:
        model = CausalModel(
            experiment_id="exp_12345678",
            label="Test Model",
            intercept_mu=0.1,
            intercept_sigma=0.4,
            nodes=["Idade", "Renda", "Aversão a Risco", "Facilidade", "Confiança", "Adoção"],
            node_metadata={
                "Idade": {"name": "Idade", "node_type": "demographic"},
                "Facilidade": {
                    "name": "Facilidade",
                    "node_type": "product",
                    "product_calibration": "medium",
                },
            },
        )
        if not model.id.startswith("cm_"):
            all_validation_failures.append(f"Model ID invalid: {model.id}")
    except Exception as e:
        all_validation_failures.append(f"Create model failed: {e}")

    # Test 3: Valid likert edge
    total_tests += 1
    try:
        edge = CausalEdge(
            id="e1",
            from_node="Idade",
            to_node="Digital",
            user_var="ageNorm",
            direction=-1,
            header="Test header",
            options=[
                LikertOption(text=f"Option {i}", mu=0.8 - i * 0.15, sigma=0.15 + i * 0.05)
                for i in range(5)
            ],
            default_option=0,
            edge_type="likert",
        )
        if edge.selected_option is not None:
            all_validation_failures.append("selected_option should default to None")
    except Exception as e:
        all_validation_failures.append(f"Create likert edge failed: {e}")

    # Test 4: Valid fixed edge (no options, no user_var)
    total_tests += 1
    try:
        fixed_edge = CausalEdge(
            id="e2",
            from_node="Idade",
            to_node="Aversão a Risco",
            user_var=None,
            direction=1,
            header="Idade → Aversão a Risco",
            options=[],
            edge_type="fixed",
            weight=0.7,
        )
        if fixed_edge.edge_type != "fixed":
            all_validation_failures.append("edge_type should be 'fixed'")
        if fixed_edge.weight != 0.7:
            all_validation_failures.append(f"weight should be 0.7, got {fixed_edge.weight}")
    except Exception as e:
        all_validation_failures.append(f"Create fixed edge failed: {e}")

    # Test 5: NodeType enum
    total_tests += 1
    try:
        assert NodeType.DEMOGRAPHIC.value == "demographic"
        assert NodeType.PRODUCT.value == "product"
        assert NodeType.INTERACTION.value == "interaction"
        assert NodeType.OUTCOME.value == "outcome"
    except AssertionError as e:
        all_validation_failures.append(f"NodeType enum: {e}")

    # Test 6: CausalNode validation
    total_tests += 1
    try:
        node = CausalNode(
            name="Facilidade de Cancelamento",
            node_type=NodeType.PRODUCT,
            product_calibration="medium",
            product_description="Ease of cancellation",
        )
        if node.product_calibration != "medium":
            all_validation_failures.append("product_calibration should be 'medium'")
    except Exception as e:
        all_validation_failures.append(f"CausalNode creation failed: {e}")

    # Test 7: Invalid product calibration rejected
    total_tests += 1
    try:
        CausalNode(
            name="Test",
            node_type=NodeType.PRODUCT,
            product_calibration="invalid",
        )
        all_validation_failures.append("Should reject invalid product_calibration")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Wrong exception for invalid calibration: {e}")

    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
