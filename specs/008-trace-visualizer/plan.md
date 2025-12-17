# Implementation Plan: Mini-Jaeger Local para Conversas LLM Multi-turn

**Branch**: `008-trace-visualizer` | **Date**: 2025-12-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/008-trace-visualizer/spec.md`

## Summary

Construir uma ferramenta local de visualização de traces para conversas multi-turn com LLMs. Traces são registrados como hierarquias de spans (conversa → turns → etapas), persistidos em JSON, e visualizados em formato waterfall via HTML estático. Foco: desenvolvimento/debugging, sem dependências externas.

**MVP** (P1): Visualização waterfall + inspeção de detalhes
**Próxima iteração** (P2): Exportação/importação + cores semânticas

## Technical Context

**Language/Version**: Python 3.13+ (SDK) + HTML5/CSS3/JavaScript (UI)
**Primary Dependencies**:
- Python SDK: stdlib only (dataclasses, json, datetime, uuid)
- UI: zero dependencies (vanilla JS/HTML)

**Storage**: JSON files (local filesystem)
**Testing**: pytest (Python SDK), manual testing (UI)
**Target Platform**: Desktop/local (macOS, Linux, Windows)
**Project Type**: Hybrid (Python SDK + static HTML UI)
**Performance Goals**: Traces com <100 etapas carregam em <2s; detalhes aparecem em <1s
**Constraints**:
- Zero dependências externas para UI
- Compatível com versionamento (JSON é auto-contido)
- Offline-capable (não requer servidor)

**Scale/Scope**:
- Initial: traces com até 100 etapas
- Single developer usage (não suporta concorrência)
- ~1-2MB max file size por trace

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Test-First Development (TDD/BDD)
- ✅ **PASS**: Python SDK will use TDD (unit tests → implementation)
- ✅ **PASS**: UI will have BDD acceptance tests (manual validation)
- ✅ **PASS**: All FR will have test coverage

### II. Fast Test Battery (<5s)
- ✅ **PASS**: Python SDK tests will run in <5s
- ✅ **PASS**: No slow integration tests required for MVP
- ⚠️ **NOTE**: UI testing is manual (static HTML, no automated suite)

### III. Complete Test Battery Before PR
- ✅ **PASS**: Python SDK tests will be complete before PR
- ✅ **PASS**: UI validation via manual testing checklist

### IV. Frequent Version Control Commits
- ✅ **PASS**: Planned: commits at each FR completion

### V. Simplicity and Code Quality
- ✅ **PASS**: Zero external dependencies for UI (vanilla JS)
- ✅ **PASS**: Python SDK will use stdlib only
- ✅ **PASS**: Target: <300 lines per Python module, <1000 lines per HTML file

### VI. Language
- ✅ **PASS**: Code in English, documentation in Portuguese

**OVERALL**: ✅ PASS - All principles satisfied

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/synth_lab/trace_visualizer/
├── tracer.py                 # SDK: Tracer class and span recording
├── models.py                 # SDK: Span, Turn, Trace dataclasses
├── persistence.py            # SDK: JSON write/read
└── __init__.py               # SDK: Public API

tests/unit/synth_lab/trace_visualizer/
├── test_tracer.py
├── test_models.py
└── test_persistence.py

# UI (static, deployed as HTML artifact)
logui/
├── index.html                # Main UI shell
├── styles.css                # Waterfall visualization styles
├── waterfall.js              # Timeline rendering
├── details.js                # Detail panel interaction
└── trace-renderer.js         # JSON trace loading/parsing

# Documentation
specs/008-trace-visualizer/
├── spec.md
├── plan.md (this file)
├── research.md               # (Phase 0 output)
├── data-model.md             # (Phase 1 output)
├── quickstart.md             # (Phase 1 output)
├── contracts/                # (Phase 1 output)
└── tasks.md                  # (Phase 2 output)
```

**Structure Decision**: Hybrid project - Python SDK + static HTML UI. SDK is part of synth_lab package; UI is standalone HTML file that loads JSON traces. No bundling or build step needed for UI.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

N/A - No constitution violations. All principles satisfied.

## Implementation Phases

### Phase 0: Research & Technical Decisions ✅

**Output**: `research.md`

All architectural decisions have been provided upfront:
- Conversation as trace root (multi-turn support)
- Turn as first-class concept (FR-010)
- Explicit span types for semantic coloring (FR-007)
- Content in span attributes (FR-005, FR-011, FR-012)
- Local JSON persistence (FR-008, FR-009)
- Static HTML UI with zero dependencies
- Deferred OTel integration (Phase 2+)

No unknowns require research. Proceed to Phase 1.

### Phase 1: Design Artifacts

**Outputs**: `data-model.md`, `quickstart.md`, `contracts/`

**Tasks**:
1. Define entity models (Trace, Turn, Step/Span) with attributes
2. Specify JSON schema for trace files
3. Document SDK API surface (context managers, decorators)
4. Create quickstart guide with usage examples
5. Define contracts (if applicable - may be minimal for local tool)

**Estimated Effort**: 1-2 hours documentation

### Phase 2: Task Generation

**Output**: `tasks.md` (via `/speckit.tasks` command)

Break down implementation by user story:
- US-1 (P1): Visualização waterfall → FR-001 to FR-004
- US-2 (P1): Inspeção de detalhes → FR-005, FR-006
- US-3 (P2): Exportação/importação → FR-008, FR-009
- US-4 (P2): Cores semânticas → FR-007

Each task will specify:
- Test-first approach (write test → implement → validate)
- Success criteria from spec.md
- Dependencies between tasks

### Phase 3: Implementation

Execute tasks from tasks.md in dependency order using TDD:
1. **SDK Core** (tracer.py, models.py, persistence.py)
2. **SDK Tests** (test_tracer.py, test_models.py, test_persistence.py)
3. **UI Core** (index.html, waterfall.js, trace-renderer.js)
4. **UI Details** (details.js, styles.css)
5. **Manual Testing** (BDD acceptance scenarios from spec.md)

**Commits**: After each functional requirement is complete and tested

## Key Design Decisions

### 1. Span Hierarchy Design

**Decision**: Three-level hierarchy: Trace → Turn → Step

**Rationale**:
- **Trace**: Represents entire conversation session (root span)
- **Turn**: First-class concept representing user input → processing → output cycle
- **Step**: Internal operations (LLM calls, tool calls, logic)

This matches cognitive model of multi-turn conversations and provides clear visualization hierarchy.

### 2. Explicit Span Types

**Decision**: Typed spans with semantic meaning

**Types**:
- `llm_call`: LLM API invocation
- `tool_call`: Tool/function execution
- `turn`: Conversation iteration
- `error`: Failed operation
- `logic`: Business logic execution

**Rationale**: Enables semantic coloring in UI (FR-007) and provides clear debugging context.

### 3. Content Storage Strategy

**Decision**: Store content in span attributes, not separate fields

**Structure**:
```json
{
  "span_id": "uuid",
  "type": "llm_call",
  "attributes": {
    "prompt": "user message",
    "response": "assistant message",
    "model": "claude-sonnet-4-5"
  }
}
```

**Rationale**: Maintains OTel compatibility (attributes map), flexible schema, easy to extend.

### 4. JSON Persistence Format

**Decision**: Self-contained JSON files with `.trace.json` extension

**Structure**:
```json
{
  "trace_id": "uuid",
  "start_time": "2025-12-17T10:00:00Z",
  "end_time": "2025-12-17T10:05:30Z",
  "duration_ms": 330000,
  "turns": [
    {
      "turn_id": "uuid",
      "turn_number": 1,
      "steps": [...]
    }
  ]
}
```

**Rationale**: Human-readable, versionable, portable, no external dependencies (FR-008, FR-009).

### 5. UI Architecture

**Decision**: Static HTML with vanilla JavaScript (no build step)

**Components**:
- `index.html`: Shell and structure
- `waterfall.js`: Timeline rendering with D3-style positioning
- `trace-renderer.js`: JSON parsing and data transformation
- `details.js`: Sidebar interaction
- `styles.css`: Layout and semantic colors

**Rationale**: Zero dependencies, works offline, trivial to distribute, no bundling required.

### 6. OpenTelemetry Compatibility

**Decision**: Design compatible with OTel, but defer integration to Phase 2+

**Compatibility Points**:
- Span structure matches OTel span model
- Attributes align with OTel semantic conventions
- Trace/span IDs can be OTel-compatible UUIDs
- JSON format can export to OTel JSON format

**Rationale**: Keep MVP simple (stdlib only) while maintaining future integration path.

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Large traces (>100 steps) cause UI slowness | Medium | Implement virtual scrolling if needed (P3) |
| JSON files become too large (>5MB) | Low | Document size limits, add warning in UI |
| Manual testing is insufficient for UI | Medium | Create comprehensive BDD checklist from spec.md |
| Span hierarchy becomes too deep | Low | Limit nesting depth to 3 levels (Trace→Turn→Step) |
| JSON schema evolves, breaks old traces | Medium | Version schema, add migration path in Phase 2 |

## Success Metrics

From spec.md Success Criteria:
- **SC-001**: Developers explain behavior from waterfall only (BDD test)
- **SC-002**: Identify bottlenecks in <10s (BDD test)
- **SC-003**: Works without external infra (architecture validates)
- **SC-004**: `.trace.json` portable (BDD test)
- **SC-005**: Details appear in <1s (performance test)
- **SC-006**: 100-step traces load in <2s (performance test)
- **SC-007**: Colors distinguishable (manual validation)

## Next Steps

1. ✅ Complete plan.md (this file)
2. 🔄 Generate research.md (Phase 0 output)
3. 🔄 Generate data-model.md (Phase 1 output)
4. 🔄 Generate quickstart.md (Phase 1 output)
5. 🔄 Generate contracts/ (Phase 1 output - may be minimal)
6. ⏳ Run `/speckit.tasks` to generate tasks.md (Phase 2)
7. ⏳ Begin TDD implementation (Phase 3)
