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


# =============================================================================
# Multi-Scenario Simulation Schemas
# =============================================================================


class ScenarioInput(BaseModel):
    """One scenario's product calibrations."""

    calibrations: dict[str, str] = Field(
        description="Map of product node name to calibration (low/medium/high).",
        examples=[{"1-Clique Ativado": "high", "Badges de Seguranca": "low"}],
    )


class MultiScenarioRequest(BaseModel):
    """Request to run a multi-scenario simulation batch.

    If scenarios is omitted, the system auto-generates n_scenarios random
    scenarios by sampling {low, medium, high} for each product node.
    """

    n_scenarios: int | None = Field(
        default=None, ge=1, le=1000,
        description="Number of random scenarios. Default from config (100).",
    )
    scenarios: list[ScenarioInput] | None = Field(
        default=None,
        description="Explicit scenarios. If omitted, auto-generated randomly.",
    )
    n_repetitions: int = Field(
        default=30, ge=1, le=100,
        description="MC repetitions per synth (default 30).",
    )


class ScenarioRunResponse(BaseModel):
    """Summary of one scenario run within a batch."""

    run_id: str = Field(description="Simulation run ID (sr_xxx).")
    product_values: dict[str, str] = Field(
        description="Product calibrations used for this scenario."
    )
    stats: SimulationStatsResponse = Field(description="Aggregated statistics.")
    n_synths: int = Field(description="Number of synths used.")


class MultiScenarioResponse(BaseModel):
    """Response for multi-scenario simulation batch."""

    batch_id: str = Field(description="Batch ID (sb_xxx).")
    experiment_id: str = Field(description="Parent experiment ID.")
    n_scenarios: int = Field(description="Number of scenarios run.")
    n_synths: int = Field(description="Number of synths per scenario.")
    n_repetitions: int = Field(description="MC repetitions per synth.")
    status: str = Field(description="Batch status: running/completed/failed.")
    created_at: str | None = Field(default=None, description="ISO 8601 batch creation timestamp.")
    scenarios: list[ScenarioRunResponse] = Field(
        description="Per-scenario results summary."
    )


# =============================================================================
# Synth Attribute Insights Schemas
# =============================================================================


class SynthAttributeCorrelation(BaseModel):
    """Pearson r between a synth attribute and adoption probability."""

    attribute: str = Field(description="Attribute key (e.g. 'risk_aversion').")
    label: str = Field(description="Human-readable label in Portuguese.")
    r_value: float = Field(description="Pearson r correlation coefficient.")
    is_positive: bool = Field(description="True if r_value > 0.")


class SynthSegmentHeatmapCell(BaseModel):
    """One cell of the 3×3 segment heatmap."""

    row_bin: str = Field(description="Row bin label: 'Baixo' | 'Médio' | 'Alto'.")
    col_bin: str = Field(description="Column bin label: 'Baixo' | 'Médio' | 'Alto'.")
    adoption_pct: float = Field(description="Mean adoption % for this cell.")
    count: int = Field(description="Number of synths in this cell.")


class SynthAttributeInsightsResponse(BaseModel):
    """Synth attribute correlation and segment heatmap insights."""

    correlations: list[SynthAttributeCorrelation] = Field(
        description="Pearson r per attribute, sorted by |r| descending."
    )
    heatmap_row_attr: str = Field(description="Attribute with highest |r| (row axis).")
    heatmap_col_attr: str = Field(description="Attribute with 2nd highest |r| (col axis).")
    heatmap_row_label: str = Field(description="Human label for row axis.")
    heatmap_col_label: str = Field(description="Human label for column axis.")
    heatmap: list[SynthSegmentHeatmapCell] = Field(description="9 cells of the 3×3 heatmap.")


# =============================================================================
# Simulation Report Schema
# =============================================================================


class SimulationReportResponse(BaseModel):
    """LLM-generated analysis report for a simulation batch."""

    id: str = Field(description="Unique report ID (srp_xxx).")
    experiment_id: str = Field(description="Parent experiment ID.")
    batch_id: str = Field(description="Parent batch ID (sb_xxx).")
    content: str = Field(description="Markdown content generated by LLM.")
    model: str = Field(description="LLM model used.")
    created_at: str = Field(description="ISO 8601 creation timestamp.")


