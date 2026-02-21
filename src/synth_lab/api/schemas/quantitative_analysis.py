"""
API schemas for quantitative analysis.

Pydantic schemas for causal model and simulation API request/response handling.

References:
    - Contracts: specs/042-quantitative-analysis/contracts/api.md
    - Data model: specs/042-quantitative-analysis/data-model.md
"""

from pydantic import BaseModel, Field

# =============================================================================
# Causal Model Schemas
# =============================================================================


class LikertOptionResponse(BaseModel):
    """Likert option in API response."""

    text: str = Field(description="Self-contained assertion text in Portuguese BR.")
    mu: float = Field(description="Coupling strength [0, 1].")
    sigma: float = Field(description="Uncertainty fraction [0, 1].")


class CausalNodeResponse(BaseModel):
    """Per-node metadata in API response."""

    name: str = Field(description="Node display name.")
    node_type: str = Field(
        description="Node type: demographic, sensitivity, product, interaction, outcome."
    )
    product_calibration: str | None = Field(
        default=None, description="Product calibration: low/medium/high."
    )
    product_description: str | None = Field(
        default=None, description="LLM-generated product description."
    )
    sensitivity_key: str | None = Field(
        default=None, description="Sensitivity key (YAML or custom)."
    )
    description: str | None = Field(
        default=None, description="LLM-generated explanation of this node's role."
    )
    # Premissa fields (interaction + outcome nodes)
    header: str | None = Field(
        default=None, description="Contextual header for the node's premissa."
    )
    options: list[LikertOptionResponse] | None = Field(
        default=None, description="5 Likert options (null for non-calibratable nodes)."
    )
    default_option: int | None = Field(
        default=None, description="LLM-suggested default option index."
    )
    selected_option: int | None = Field(
        default=None, description="PM's selected option (null = not answered)."
    )


class CausalEdgeResponse(BaseModel):
    """Causal edge in API response."""

    id: str = Field(description="Edge identifier (e.g., 'e1').")
    from_node: str = Field(description="Source node name.")
    to_node: str = Field(description="Target node name.")
    user_var: str | None = Field(
        default=None, description="Mapped userVar (null for product/interaction edges)."
    )
    direction: int = Field(description="1 (direct) or -1 (inverse).")
    header: str = Field(description="Contextual assertion header.")
    options: list[LikertOptionResponse] = Field(
        default_factory=list, description="5 Likert options (empty for fixed edges)."
    )
    default_option: int = Field(description="LLM-suggested default index.")
    selected_option: int | None = Field(description="PM's selection (null = not answered).")
    edge_type: str = Field(default="likert", description="Edge type: 'likert' or 'fixed'.")
    weight: float | None = Field(default=None, description="LLM-suggested weight.")


class CausalModelResponse(BaseModel):
    """Response for causal model endpoints."""

    id: str = Field(description="Unique causal model ID (cm_xxx).")
    experiment_id: str = Field(description="Parent experiment ID.")
    label: str = Field(description="Model title from LLM.")
    intercept_mu: float = Field(description="Intercept mean.")
    intercept_sigma: float = Field(description="Intercept std dev.")
    nodes: list[str] = Field(description="DAG node names.")
    node_metadata: dict[str, CausalNodeResponse] | None = Field(
        default=None, description="Per-node metadata keyed by node name."
    )
    edges: list[CausalEdgeResponse] = Field(description="DAG edges with Likert assertions.")
    created_at: str = Field(description="ISO 8601 creation timestamp.")


# =============================================================================
# Edge Update Schemas
# =============================================================================


class EdgeUpdateRequest(BaseModel):
    """Request to update edge selections."""

    selections: dict[str, int] = Field(
        description="Map of edge_id to selected_option index.",
        examples=[{"e1": 0, "e3": 2, "e5": 4}],
    )


class EdgeUpdateResponse(BaseModel):
    """Response after updating edge selections."""

    updated_count: int = Field(description="Number of edges updated.")
    all_answered: bool = Field(description="True if all edges have a selection.")
    answered_count: int = Field(description="Number of edges with a selection.")
    total_edges: int = Field(description="Total number of edges in the model.")


# =============================================================================
# Node Selections Schemas
# =============================================================================


class NodeSelectionsRequest(BaseModel):
    """Request to update node premissa selections."""

    selections: dict[str, int] = Field(
        description="Map of node_name to selected_option index.",
        examples=[{"Confiança para Usar": 1, "Adoção": 2}],
    )


class NodeSelectionsResponse(BaseModel):
    """Response after updating node premissa selections."""

    updated_count: int = Field(description="Number of nodes updated.")
    all_answered: bool = Field(description="True if all calibratable nodes have a selection.")
    answered_count: int = Field(description="Number of nodes with a selection.")
    total_nodes: int = Field(description="Total calibratable nodes (interaction + outcome).")


# =============================================================================
# Product Calibration Schemas
# =============================================================================


class ProductCalibrationRequest(BaseModel):
    """Request to update product node calibrations."""

    calibrations: dict[str, str] = Field(
        description="Map of product node name to calibration level (low/medium/high).",
        examples=[{"Facilidade de Uso": "high", "Transparência": "low"}],
    )


class ProductCalibrationResponse(BaseModel):
    """Response after updating product calibrations."""

    updated_count: int = Field(description="Number of product nodes updated.")


# =============================================================================
# Simulation Schemas
# =============================================================================


class SimulationStatsResponse(BaseModel):
    """Aggregated simulation statistics."""

    mean: float = Field(description="Mean adoption rate (%).")
    median: float = Field(description="Median adoption rate (%).")
    std: float = Field(description="Standard deviation (pp).")
    p10: float = Field(description="10th percentile (%).")
    p90: float = Field(description="90th percentile (%).")


class SegmentResultResponse(BaseModel):
    """Result for a single segment bucket."""

    rate: float = Field(description="Adoption rate in this segment (%).")
    count: int = Field(description="Number of synths in this segment.")


class SensitivityItemResponse(BaseModel):
    """Sensitivity result for a single edge."""

    edge_id: str = Field(description="Edge identifier.")
    header: str = Field(description="Edge assertion header.")
    impact: float = Field(description="Impact in percentage points.")
    mean_low: float = Field(description="Mean with strongest option (option 0).")
    mean_high: float = Field(description="Mean with weakest option (option 4).")


class InterpretationResponse(BaseModel):
    """AI interpretation for a section."""

    raw_text: str = Field(description="Raw statistical text.")
    ai_text: str = Field(description="AI-generated contextual interpretation.")


class SimulationInterpretationsResponse(BaseModel):
    """All 3 section interpretations."""

    distribution: InterpretationResponse | None = Field(
        default=None, description="Distribution interpretation."
    )
    segments: InterpretationResponse | None = Field(
        default=None, description="Segments interpretation."
    )
    sensitivity: InterpretationResponse | None = Field(
        default=None, description="Sensitivity interpretation."
    )


class SegmentsResponse(BaseModel):
    """Segment breakdown by age, income, education."""

    age: dict[str, SegmentResultResponse] = Field(description="Age segment results.")
    income: dict[str, SegmentResultResponse] = Field(description="Income segment results.")
    education: dict[str, SegmentResultResponse] = Field(description="Education segment results.")


class SimulationRunResponse(BaseModel):
    """Response for simulation run endpoints."""

    id: str = Field(description="Unique simulation run ID (sr_xxx).")
    experiment_id: str = Field(description="Parent experiment ID.")
    causal_model_id: str = Field(description="Causal model used.")
    n_iterations: int = Field(description="Number of Monte Carlo iterations.")
    n_synths: int = Field(description="Number of synths used.")
    stats: SimulationStatsResponse = Field(description="Aggregated statistics.")
    distribution: list[float] = Field(description="Raw Monte Carlo distribution array.")
    segments: SegmentsResponse = Field(description="Segment breakdowns.")
    sensitivity: list[SensitivityItemResponse] = Field(
        description="Per-edge sensitivity, sorted by impact desc."
    )
    interpretations: SimulationInterpretationsResponse = Field(
        description="AI interpretations per section."
    )
    created_at: str = Field(description="ISO 8601 creation timestamp.")
