# Research: Mini-Jaeger Local para Conversas LLM Multi-turn

**Feature**: 008-trace-visualizer | **Date**: 2025-12-17 | **Phase**: 0 (Research)

## Architectural Decisions Summary

All architectural decisions were provided upfront during planning. No additional research required.

### Decision 1: Conversation as Trace Root

**Problem**: How to model multi-turn conversations in trace format?

**Decision**: Treat entire conversation as single trace (root span), with turns as children.

**Rationale**:
- Aligns with user mental model (conversation = session)
- Enables visualization of entire conversation lifecycle
- Supports FR-010 (hierarchical tree)

**Alternatives Considered**:
- Each turn as separate trace → Rejected: loses conversation context
- Each step as trace → Rejected: too granular, hard to navigate

**Implementation Impact**: Trace object contains array of Turn objects.

---

### Decision 2: Turn as First-Class Concept

**Problem**: How to represent conversation iterations in hierarchy?

**Decision**: Turn is explicit entity between Trace and Step levels.

**Rationale**:
- Matches cognitive model (user input → processing → output)
- Provides natural grouping for visualization (FR-003: expand/collapse)
- Simplifies debugging ("which turn failed?")

**Alternatives Considered**:
- Flat span list → Rejected: hard to understand conversation flow
- Implicit grouping by time → Rejected: fragile, requires heuristics

**Implementation Impact**: Turn dataclass with turn_number, start_time, end_time, steps array.

---

### Decision 3: Explicit Span Types

**Problem**: How to differentiate operations in UI without external metadata?

**Decision**: Type field with semantic values: `llm_call`, `tool_call`, `turn`, `error`, `logic`.

**Rationale**:
- Enables FR-007 (semantic colors: LLM=Blue, Tool=Green, Error=Red)
- Provides clear debugging context
- Self-documenting trace files

**Alternatives Considered**:
- Generic "operation" type with metadata → Rejected: requires parsing attributes
- No types, infer from attributes → Rejected: fragile, hard to extend

**Implementation Impact**: SpanType enum in models.py, color mapping in styles.css.

---

### Decision 4: Content in Span Attributes

**Problem**: Where to store prompts, responses, tool arguments?

**Decision**: Store in `attributes` dict, not top-level fields.

**Rationale**:
- OTel compatibility (attributes are standard span metadata)
- Flexible schema (easy to add new fields)
- Keeps span structure clean (id, type, timestamps, attributes)

**Example**:
```json
{
  "span_id": "abc123",
  "type": "llm_call",
  "attributes": {
    "prompt": "What is the weather?",
    "response": "I don't have access to weather data.",
    "model": "claude-sonnet-4-5"
  }
}
```

**Alternatives Considered**:
- Top-level fields (prompt, response) → Rejected: inflexible, non-standard
- Separate content storage → Rejected: breaks portability (FR-008)

**Implementation Impact**: Span dataclass has `attributes: Dict[str, Any]`.

---

### Decision 5: JSON Persistence Format

**Problem**: How to store traces for portability and version control?

**Decision**: Self-contained JSON files with `.trace.json` extension.

**Structure**:
```json
{
  "trace_id": "uuid",
  "start_time": "ISO 8601",
  "end_time": "ISO 8601",
  "duration_ms": 12345,
  "turns": [
    {
      "turn_id": "uuid",
      "turn_number": 1,
      "start_time": "ISO 8601",
      "end_time": "ISO 8601",
      "duration_ms": 5000,
      "steps": [
        {
          "span_id": "uuid",
          "type": "llm_call",
          "start_time": "ISO 8601",
          "end_time": "ISO 8601",
          "duration_ms": 3000,
          "attributes": {
            "prompt": "...",
            "response": "...",
            "model": "claude-sonnet-4-5"
          }
        }
      ]
    }
  ]
}
```

**Rationale**:
- Human-readable (supports FR-008: export/import)
- Versionable (Git-friendly)
- Portable (no database required, satisfies SC-003)
- Self-contained (all data in one file)

**Alternatives Considered**:
- SQLite database → Rejected: harder to share, not Git-friendly
- Binary format (protobuf) → Rejected: not human-readable
- JSONL (line-delimited) → Rejected: harder to parse entire trace

**Implementation Impact**: persistence.py with save_trace(trace, path) and load_trace(path).

---

### Decision 6: Static HTML UI

**Problem**: How to visualize traces without external dependencies?

**Decision**: Single-page HTML app with vanilla JavaScript (no bundler, no npm).

**Components**:
- `index.html`: Shell, file upload, waterfall container, detail panel
- `waterfall.js`: Timeline rendering (spans as horizontal bars)
- `trace-renderer.js`: JSON parsing, data transformation
- `details.js`: Sidebar interaction (click → show details)
- `styles.css`: Layout, semantic colors

**Rationale**:
- Zero dependencies (satisfies constraint)
- Offline-capable (no server required)
- Trivial distribution (single HTML file can be self-contained)
- No build step (edit and refresh)

**Alternatives Considered**:
- React/Vue app → Rejected: requires npm, bundler, violates zero-dep constraint
- Server-based UI (Flask/FastAPI) → Rejected: not offline-capable
- Desktop app (Electron/Tauri) → Rejected: overkill for MVP, harder to distribute

**Implementation Impact**: logui/ directory with 5 files, loaded via file:// protocol.

---

### Decision 7: Deferred OTel Integration

**Problem**: Should MVP integrate with OpenTelemetry?

**Decision**: Design compatible with OTel, but defer integration to Phase 2+.

**Phase 1 (MVP)**:
- Stdlib-only SDK (no otel-python dependency)
- Custom JSON format
- Local visualization only

**Phase 2+ (Future)**:
- Add optional OTel exporter
- Support OTel JSON format import
- Bridge to Jaeger/Datadog

**Rationale**:
- Keeps MVP simple (constitution: stdlib only)
- Avoids heavyweight dependencies
- Maintains compatibility (span structure matches OTel model)
- Allows future integration without rewriting

**OTel Compatibility Points**:
- Span structure: id, parent_id, name, start_time, end_time, attributes
- Trace/span IDs: use UUID format compatible with OTel trace ID format
- Attributes: align with OTel semantic conventions where applicable

**Implementation Impact**: None for MVP. Future: add `exporters/otel_exporter.py`.

---

## Known Risks

### Risk 1: Large Traces (>100 Steps)

**Description**: UI may become slow with many spans.

**Impact**: Medium (affects UX for complex conversations)

**Mitigation**:
- Phase 1: Document size limits in quickstart.md
- Phase 2+: Implement virtual scrolling or pagination if needed
- Performance target: <2s load time for 100 steps (SC-006)

---

### Risk 2: JSON Schema Evolution

**Description**: Adding fields may break old traces.

**Impact**: Medium (affects portability)

**Mitigation**:
- Phase 1: Version JSON schema (add `"schema_version": "1.0"`)
- Phase 2+: Add migration tool if schema changes significantly
- Follow semantic versioning for schema

---

### Risk 3: Manual UI Testing

**Description**: No automated UI tests for waterfall rendering.

**Impact**: Medium (may miss regressions)

**Mitigation**:
- Create comprehensive BDD checklist from spec.md acceptance criteria
- Test with real traces (not synthetic data)
- Document visual testing process in quickstart.md

---

### Risk 4: Span Hierarchy Depth

**Description**: Deeply nested spans (>3 levels) may be hard to visualize.

**Impact**: Low (unlikely in MVP scope)

**Mitigation**:
- Limit MVP to 3 levels: Trace → Turn → Step
- Future: Add collapse/expand for deep hierarchies

---

## Technology Stack (Final)

### Python SDK
- **Language**: Python 3.13+
- **Dependencies**: stdlib only (dataclasses, json, datetime, uuid)
- **Testing**: pytest
- **Modules**: tracer.py, models.py, persistence.py

### HTML UI
- **Languages**: HTML5, CSS3, ES6+ JavaScript
- **Dependencies**: Zero (vanilla JS)
- **Testing**: Manual (BDD checklist)
- **Files**: index.html, waterfall.js, trace-renderer.js, details.js, styles.css

### Storage
- **Format**: JSON (`.trace.json` files)
- **Location**: Local filesystem
- **Size Target**: <2MB per trace

---

## Open Questions

None. All decisions finalized.

---

## Next Steps

✅ Research complete → Proceed to Phase 1 (Design Artifacts)
