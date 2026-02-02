# Research Findings: Unified DAG & Hypothesis Generation

**Date**: 2026-02-02
**Feature**: 037-unified-dag-hypotheses
**Purpose**: Document research decisions for unified generation, relevance weighting, range clamping, and drawer-based editing

## Decision 1: Unified DAG + Hypothesis Structured Output

**Question**: How to combine DAG generation and hypothesis parametrization into a single LLM call?

**Decision**: Extend the existing `DAGResponse` structured output schema to include hypothesis data per variable. The LLM will produce nodes, edges, assumptions, risks, AND distribution hypotheses in one response.

**Extended Schema**:
```python
class LLMHypothesis(BaseModel):
    variable_name: str
    distribution_type: str  # "normal", "uniform", "beta", etc.
    parameters: dict        # Type-specific params
    relevance: str          # "low", "medium", "high"
    range_min: float | None
    range_max: float | None
    reasoning: str          # Brief justification

class UnifiedDAGResponse(BaseModel):
    variables: list[LLMVariable]     # 8-20 (existing)
    edges: list[LLMEdge]            # (existing)
    assumptions: list[LLMAssumption] # 2-3 (existing)
    risks: list[LLMRisk]           # 2-3 (existing)
    hypotheses: list[LLMHypothesis] # 1 per variable (NEW)
```

**Model Selection**: `gpt-4o-mini` instead of `gpt-4o`
- Current DAG generation uses `gpt-4o` (~$0.03-0.05 per call, 15-20s)
- Current hypothesis parametrization uses `gpt-4o` (~$0.03-0.05 per call, 10-15s)
- Combined with `gpt-4o-mini`: ~$0.005-0.01 per call, 8-15s total
- Net savings: ~80% cost reduction, ~50% latency reduction

**Rationale**:
- One structured output call eliminates the second LLM round-trip entirely
- `gpt-4o-mini` handles structured outputs well (JSON mode, function calling)
- The combined prompt is larger but within `gpt-4o-mini`'s context window
- Hypothesis quality may be slightly lower than `gpt-4o` but acceptable for defaults (user can fine-tune via drawer)

**Alternatives Considered**:
- **Keep two calls but parallelize** - Rejected because still doubles cost and adds orchestration complexity
- **Use gpt-4o for combined call** - Rejected because the whole point is speed; gpt-4o-mini is 3-5x faster
- **Use gpt-4o for DAG only, generate hypotheses algorithmically** - Rejected because algorithmic hypothesis generation lacks domain knowledge for realistic distributions

**Implementation Note**: Reuse the existing few-shot examples from `hypothesis_parametrizer_service.py` by embedding them in the unified prompt. The prompt will have two sections: DAG structure generation and hypothesis parametrization.

---

## Decision 2: Relevance Attribute Design

**Question**: How should relevance be stored, displayed, and used?

**Decision**: Add `relevance` as a string enum column on the `hypotheses` table with three levels.

**Levels**:
| Level | Meaning | Visual Saturation | Default |
|-------|---------|------------------|---------|
| `high` | Critical to simulation outcome, must be carefully parametrized | 100% (current) | No |
| `medium` | Contributes to outcome, reasonable defaults sufficient | ~70% | Yes (fallback) |
| `low` | Minor influence, can be ignored for most analyses | ~40% | No |

**LLM Assignment**: The unified prompt instructs the LLM to assign relevance based on:
- Variables that are outcomes or interventions → typically `high`
- Variables with high out-degree (many downstream effects) → typically `high`
- Variables that are external/uncontrollable context → typically `low` or `medium`
- Critical uncertainties → typically `high`

**Database**: New column `relevance VARCHAR(10) DEFAULT 'medium' NOT NULL` on `hypotheses` table.

**Domain Entity**: New field `relevance: Relevance` (enum: LOW, MEDIUM, HIGH) on `Hypothesis` dataclass.

**Rationale**:
- Three levels are sufficient for visual differentiation without overwhelming users
- String enum is simpler than numeric weights and directly maps to visual rendering
- Default `medium` ensures backward compatibility (existing hypotheses render at 70% saturation, close to current 100%)
- LLM-assigned relevance leverages domain knowledge (e.g., "marketing spend" is high-relevance for a revenue model)

**Alternatives Considered**:
- **Numeric 0-1 weight** - Rejected because continuous values are harder to interpret visually and harder for LLM to assign consistently
- **Two levels (high/low)** - Rejected because too coarse; medium is needed for the majority of variables
- **Computed from DAG structure** - Rejected because structural importance (out-degree) doesn't capture domain relevance (e.g., a low-degree variable can still be critical)

---

## Decision 3: Range Clamping Strategy

**Question**: How should range (min/max) be stored and applied during simulation?

**Decision**: Use existing `range_min`/`range_max` columns on `hypotheses` ORM (already exist but unused). Apply clamping as a post-sampling step using `np.clip()`.

**Storage**: Already exists in ORM:
```python
range_min = Column(Float, nullable=True)  # Already exists
range_max = Column(Float, nullable=True)  # Already exists
```

**Domain Entity**: Add `range_min: float | None` and `range_max: float | None` to `Hypothesis` dataclass (currently missing from entity).

**Clamping Logic** (in `DistributionSampler`):
```python
def sample(self, hypothesis: Hypothesis, n: int) -> np.ndarray:
    samples = self._sample_by_type(hypothesis, n)
    if hypothesis.range_min is not None or hypothesis.range_max is not None:
        samples = np.clip(
            samples,
            a_min=hypothesis.range_min,
            a_max=hypothesis.range_max,
        )
    return samples
```

**LLM Assignment**: The unified prompt instructs the LLM to assign ranges based on:
- Physical constraints (e.g., probability: 0-1, count: ≥0, rate: 0-100%)
- Domain knowledge (e.g., "discount rate" typically 0-50%, "response time" typically 0-3600s)
- Leave `null` when no natural bounds exist

**Validation**: Frontend validates `min ≤ max` when both provided. Backend rejects invalid ranges with 422.

**Rationale**:
- Reuses existing ORM columns (zero migration for columns themselves)
- `np.clip` is the standard NumPy approach for bounded sampling
- Post-sampling clamping is simpler than modifying distribution parameters to respect bounds
- Optional ranges (null = no clamp) maintain backward compatibility

**Alternatives Considered**:
- **Truncated distributions** - Rejected because complex to implement per distribution type and changes distribution shape
- **Rejection sampling** - Rejected because slow for narrow ranges with wide distributions
- **Pre-clamp parameter adjustment** - Rejected because modifying distribution parameters to respect bounds is mathematically complex

---

## Decision 4: Drawer Component Selection

**Question**: Which UI component to use for node detail editing?

**Decision**: Use the existing `Sheet` component (Radix Dialog-based, right-side panel) from `frontend/src/components/ui/sheet.tsx`.

**Why Sheet over Drawer**:
- Sheet supports `side="right"` (spec requirement: "right-side drawer")
- Drawer component is Vaul-based (bottom-up, mobile-optimized) — wrong direction
- Sheet already has overlay, close button, smooth animations
- Sheet matches the specification's "drawer slides in from right" description

**Layout**:
```
┌─────────────────────────────────────────┬──────────────────┐
│                                         │ Sheet (w-[400px]) │
│         DAG Visualization               │                  │
│         (ReactFlow)                     │ Variable Name    │
│                                         │ Description      │
│                                         │ ────────────     │
│                                         │ Relevance: [▼]   │
│                                         │ Range:           │
│                                         │  Min: [____]     │
│                                         │  Max: [____]     │
│                                         │ ────────────     │
│                                         │ [Save] [Cancel]  │
│                                         │                  │
└─────────────────────────────────────────┴──────────────────┘
```

**Responsive**: On screens < 768px, sheet takes full width (`className="w-full sm:w-[400px]"`).

**Rationale**:
- Reuses existing component (zero new dependencies)
- Right-side panel is standard for detail editing in data-heavy applications
- Does not obscure the DAG (user can still see graph context)
- Sheet supports click-outside-to-close (FR-014)

---

## Decision 5: Node Visual Saturation Implementation

**Question**: How to implement relevance-driven color saturation on DAG nodes?

**Decision**: Use HSL color manipulation on existing scope-based colors.

**Current Colors** (in DAGNodeCard):
- User scope: `#7c3aed` (violet) → HSL(263, 84%, 58%)
- World scope: `#06b6d4` (cyan) → HSL(189, 95%, 42%)

**Saturation Mapping**:
```
high:   HSL(H, S × 1.0, L)  → Full color (current behavior)
medium: HSL(H, S × 0.7, L)  → 70% saturation
low:    HSL(H, S × 0.4, L)  → 40% saturation
```

**Implementation** (in DAGNodeCard):
```tsx
function getNodeColor(scope: string, relevance: string): string {
  const baseColors = {
    user: { h: 263, s: 84, l: 58 },
    world: { h: 189, s: 95, l: 42 },
  };
  const saturationMultiplier = { high: 1.0, medium: 0.7, low: 0.4 };
  const { h, s, l } = baseColors[scope] || baseColors.world;
  const adjustedS = s * (saturationMultiplier[relevance] || 1.0);
  return `hsl(${h}, ${adjustedS}%, ${l}%)`;
}
```

**Rationale**:
- HSL manipulation is clean and predictable
- Only saturation changes (not hue or lightness), preserving color identity
- Backward compatible: existing nodes with no relevance → default `medium` → 70% (close to current 100%)
- No external library needed (pure CSS HSL values)

---

## Decision 6: Fallback Strategy for Incomplete LLM Responses

**Question**: What happens if the unified LLM response is missing hypothesis data for some variables?

**Decision**: Assign sensible defaults for any variable missing hypothesis data.

**Defaults**:
```python
DEFAULT_HYPOTHESIS = {
    "distribution_type": "uniform",
    "parameters": {"min": 0, "max": 1},
    "relevance": "medium",
    "range_min": None,
    "range_max": None,
}
```

**Detection**: After parsing the unified response, compare variables list vs hypotheses list. For any variable without a matching hypothesis, create a default.

**Logging**: Log a warning for each defaulted variable:
```python
logger.warning(
    f"Variable '{var.name}' missing hypothesis in LLM response, "
    f"using uniform default"
)
```

**Rationale**:
- Uniform distribution is the least informative (maximally uncertain) — safest default
- Medium relevance ensures the variable is visible but not highlighted
- No range clamp allows full distribution sampling
- Warning log enables debugging without failing the user's workflow

---

## Decision 7: Tooltip Removal and Drawer Trigger

**Question**: How to transition from hover tooltips to click-to-drawer?

**Decision**: Remove the existing tooltip portal from DAGNodeCard and make the entire node clickable to open the sheet.

**Current Behavior**: Hover over node → tooltip shows variable description via portal
**New Behavior**: Click on node → sheet opens with full detail view (name, description, relevance, range)

**Implementation**:
- Remove `onMouseEnter`/`onMouseLeave` handlers from DAGNodeCard
- Remove tooltip portal rendering
- Add `onClick` handler that calls `onEditNode(variable)` (already exists as prop)
- Parent component (`DAGVisualization`) manages sheet open/close state

**Rationale**:
- Click is more intentional than hover (reduces accidental triggers)
- Sheet provides more space for editing controls
- Eliminates tooltip z-index/positioning issues
- Mobile-friendly (no hover on touch devices)

---

## Research Summary

**Key Findings**:
1. **Unified generation**: Single `gpt-4o-mini` call replaces two `gpt-4o` calls (~80% cost reduction, ~50% latency reduction)
2. **Relevance**: Three-level enum (low/medium/high) with HSL saturation mapping for visual weight
3. **Range clamping**: Post-sampling `np.clip()` using existing ORM columns
4. **Drawer**: Use existing Sheet component (right-side, Radix-based) — NOT Vaul drawer
5. **Node saturation**: HSL manipulation on existing scope colors
6. **Fallbacks**: Uniform distribution default for missing hypotheses
7. **Tooltip → Drawer**: Replace hover tooltip with click-to-sheet interaction

**Implementation Implications**:
- **One Alembic migration**: Add `relevance` column to `hypotheses` table
- **One service refactor**: Merge DAG constructor + hypothesis parametrizer into unified service
- **One frontend component**: New `NodeDetailSheet` wrapping existing Sheet
- **Minimal risk**: Existing ORM columns reused, backward-compatible defaults

**Next Phase**: Proceed to Phase 1 (Design & Contracts) with these decisions finalized.
