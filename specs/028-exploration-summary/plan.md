# Implementation Plan: Exploration Summary and PRFAQ Generation

**Branch**: `028-exploration-summary` | **Date**: 2026-01-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/028-exploration-summary/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Generate narrative summaries and PRFAQ documents for completed explorations by using LLM to transform the winning path (root to best leaf node) into actionable insights. Similar to interview guide generation, but triggered manually by users on completed explorations (status=GOAL_ACHIEVED, DEPTH_LIMIT_REACHED, or COST_LIMIT_REACHED).

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0+, Pydantic, OpenAI SDK, Arize Phoenix
**Storage**: PostgreSQL 14+ (existing tables: explorations, scenario_nodes, experiments)
**Testing**: pytest with async support
**Target Platform**: Linux server (backend) + React 18 frontend (TypeScript 5.5+)
**Project Type**: Web application (fullstack)
**Performance Goals**: Summary generation <30s for typical paths (5 nodes), PRFAQ generation <45s
**Constraints**: LLM calls must be traced with Phoenix, must handle concurrent generation requests
**Scale/Scope**: ~10-50 explorations/month, tree depths up to 10 nodes, single user sessions

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Architecture Rules Compliance

✅ **Backend Architecture** (from `docs/arquitetura.md`):
- Router: Will follow `request → service.method() → response` pattern
- Business logic: Summary/PRFAQ generation services (separate from routers)
- Data access: Repository pattern for exploration_summary and exploration_prfaq tables
- LLM calls: Will use Phoenix tracing (`_tracer.start_as_current_span()`)
- SQL: Parametrized queries in repositories

✅ **Frontend Architecture** (from `docs/arquitetura_front.md`):
- Pages: ExplorationDetail page will compose Summary/PRFAQ components
- Components: Pure display components (props → JSX), no direct API calls
- Hooks: useGenerateSummary/useSummaryStatus with TanStack Query
- Services: fetchAPI functions for summary/PRFAQ endpoints

✅ **Test-First Development**:
- Will write tests before implementation (Red-Green-Refactor)
- Fast battery: Unit tests for services/repos (<5s total)
- Slow battery: Integration tests with DB + LLM mocking

✅ **Code Quality**:
- Functions <30 lines, single-purpose
- Files <500 lines (TSX may be up to 1000)
- Dependencies: Reusing existing LLMClient, no new packages needed

✅ **Language Standards**:
- Code: English (classes, variables, functions)
- Documentation: Portuguese
- User-facing strings: i18n-ready

### Pre-Design Assessment

**No Constitution Violations Anticipated**

This feature follows existing patterns:
- Similar to interview_guide_generator_service (async LLM generation)
- Uses existing Phoenix tracing infrastructure
- Follows repository pattern (like interview_guide_repository)
- No new architectural patterns or dependencies

**Gates Status**: ✅ PASS - Proceed to Phase 0

## Project Structure

### Documentation (this feature)

```text
specs/028-exploration-summary/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── exploration-summary-api.yaml  # OpenAPI spec for new endpoints
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# Backend (Python) - REUTILIZA INFRAESTRUTURA EXISTENTE
src/synth_lab/
├── domain/entities/
│   └── experiment_document.py        # EXISTING: Reusar entity, enums
├── models/orm/
│   └── document.py                   # EXISTING: Reusar ORM model
├── repositories/
│   └── experiment_document_repository.py  # EXISTING: Reusar repository
├── services/
│   ├── exploration_summary_generator_service.py  # NEW: LLM summary generation
│   └── exploration_prfaq_generator_service.py    # NEW: LLM PRFAQ generation
├── api/
│   ├── routers/
│   │   └── exploration.py            # MODIFY: Add document endpoints wrapper
│   └── schemas/
│       └── documents.py              # EXISTING: Reusar response schemas
└── infrastructure/
    └── llm_client.py                 # EXISTING: Reuse for LLM calls

# Database Migrations
# NÃO PRECISA! Tabela experiment_documents já existe

# Backend Tests
tests/synth_lab/
└── unit/
    └── services/
        ├── test_exploration_summary_generator_service.py  # NEW
        └── test_exploration_prfaq_generator_service.py    # NEW

# Frontend (TypeScript/React)
frontend/src/
├── pages/
│   └── ExplorationDetail.tsx         # MODIFY: Add Summary/PRFAQ sections
├── components/
│   └── exploration/
│       ├── ExplorationSummaryCard.tsx        # NEW: Display summary
│       ├── ExplorationPRFAQCard.tsx          # NEW: Display PRFAQ
│       └── GenerateDocumentButton.tsx        # NEW: Trigger generation
├── hooks/
│   ├── useGenerateExplorationSummary.ts     # NEW: TanStack Query mutation
│   ├── useGenerateExplorationPRFAQ.ts       # NEW: TanStack Query mutation
│   ├── useExplorationSummary.ts             # NEW: Fetch summary
│   └── useExplorationPRFAQ.ts               # NEW: Fetch PRFAQ
├── services/
│   └── exploration.ts                # MODIFY: Add document API calls
└── lib/
    └── query-keys.ts                 # MODIFY: Add query keys

# Frontend Tests
frontend/tests/
├── components/
│   └── exploration/
│       └── ExplorationSummaryCard.test.tsx   # NEW
└── hooks/
    └── useGenerateExplorationSummary.test.ts # NEW
```

**Structure Decision**: Web application (fullstack) - REUTILIZAÇÃO MÁXIMA

Esta feature **reutiliza infraestrutura existente**:
- ✅ Tabela: `experiment_documents` (já existe)
- ✅ Entity: `ExperimentDocument` (já existe)
- ✅ Enums: `DocumentType`, `DocumentStatus` (já existem)
- ✅ Repository: `ExperimentDocumentRepository` (já existe)
- ✅ Schemas: `ExperimentDocumentResponse` (já existe)
- ❌ Migration: Não precisa

**Novos arquivos necessários** (apenas 2 services + endpoints + frontend):
- `exploration_summary_generator_service.py` - Gera summary via LLM
- `exploration_prfaq_generator_service.py` - Gera PRFAQ via LLM
- Endpoints wrapper em `exploration.py` router
- Componentes/hooks frontend

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations - this section is not applicable for this feature.

---

## Phase Completion Status

### Phase 0: Research ✅ COMPLETE
**Output**: [research.md](./research.md)

**Key Decisions**:
1. Winning path construction via parent_id traversal
2. LLM prompt structure (Portuguese, non-sequential narrative)
3. PRFAQ format (Press Release + FAQ + Recommendations)
4. Tiebreaker logic (success_rate → depth → created_at)
5. Database schema (two tables with status tracking)

**Status**: All research questions resolved, no NEEDS CLARIFICATION markers remain

---

### Phase 1: Design & Contracts ✅ COMPLETE
**Outputs**:
- [data-model.md](./data-model.md) - Entity definitions, ORM models, validation
- [contracts/exploration-summary-api.yaml](./contracts/exploration-summary-api.yaml) - OpenAPI spec
- [quickstart.md](./quickstart.md) - Developer guide

**Key Artifacts**:
1. **Entities**: ExplorationSummary, ExplorationPRFAQ, GenerationStatus enum
2. **Tables**: exploration_summary, exploration_prfaq (with indexes)
3. **Repositories**: Summary and PRFAQ repositories (CRUD operations)
4. **API Endpoints**: 6 endpoints (POST/GET/DELETE for summary and PRFAQ)
5. **Migration**: Alembic script for table creation

**Agent Context**: Updated CLAUDE.md with Python 3.13+, FastAPI stack, PostgreSQL

---

### Post-Design Constitution Re-Check ✅ PASS

**Backend Architecture**: ✅ Compliant
- Routers call service methods only (no business logic in routers)
- Services contain LLM generation logic (ExplorationSummaryService, ExplorationPRFAQService)
- Repositories handle all SQL queries (parametrized, no string interpolation)
- Phoenix tracing applied to all LLM calls

**Frontend Architecture**: ✅ Compliant
- Pages compose components (ExplorationDetail integrates Summary/PRFAQ cards)
- Components are pure (props → JSX, no API calls)
- Hooks encapsulate TanStack Query (useGenerateExplorationSummary, etc.)
- Services provide fetchAPI wrappers (exploration.ts)

**Test-First Development**: ✅ Planned
- Fast battery: Entity validation, repository CRUD, service logic (<5s)
- Slow battery: Integration tests, E2E API tests
- Tests written before implementation (TDD/BDD)

**Code Quality**: ✅ No violations expected
- Files under 500 lines (entities ~150, services ~250, repositories ~200)
- Functions under 30 lines (single-purpose methods)
- No new dependencies (reuses LLMClient, Phoenix, TanStack Query)

**Documentation**: ✅ Complete
- Code: English (classes, variables, functions)
- Docs: Portuguese (quickstart.md, comments in LLM prompts)
- User-facing: i18n-ready (button labels, error messages)

**Final Assessment**: No constitution violations introduced by design

---

## Next Steps

**Phase 2: Task Generation** (via `/speckit.tasks`)
- Break down implementation into atomic tasks
- Assign priorities (P1: Summary, P2: PRFAQ, P3: UI polish)
- Define acceptance criteria for each task
- Generate tasks.md for implementation tracking

**Implementation Workflow**:
1. Run `/speckit.tasks` to generate task list
2. Follow TDD: Write test → Run (fail) → Implement → Run (pass) → Refactor
3. Commit at each logical milestone (per Constitution IV)
4. Run fast test battery before each commit (Constitution II)
5. Run complete test battery before PR (Constitution III)

**Estimated Complexity**:
- Backend: ~15 files (entities, ORM, repos, services, API, migration, tests)
- Frontend: ~10 files (hooks, components, service, tests)
- Total LOC: ~2500-3000 lines (including tests)
- Development Time: 2-3 days (with TDD)

---

## Planning Summary

This plan defines a complete implementation strategy for Exploration Summary and PRFAQ generation:

✅ **Technical Context**: Python 3.13+, FastAPI, PostgreSQL, React 18, TypeScript 5.5+
✅ **Constitution Compliance**: All architecture rules followed, no violations
✅ **Research Complete**: All unknowns resolved, LLM prompts designed
✅ **Design Complete**: Entities, tables, APIs, contracts documented
✅ **Quickstart Ready**: Developer guide with code examples and testing strategy

**Branch**: `028-exploration-summary`
**Plan File**: `/Users/fulvio/Projects/synth-lab/specs/028-exploration-summary/plan.md`
**Generated Artifacts**:
- research.md (Phase 0)
- data-model.md (Phase 1)
- contracts/exploration-summary-api.yaml (Phase 1)
- quickstart.md (Phase 1)

---

## ⚠️ CRITICAL CORRECTIONS APPLIED (v3 - FINAL)

**Date**: 2026-01-02
**Reason**: Deviated from `experiment_documents` pattern → Corrected to REUTILIZAR tabela existente

### Histórico de Correções

1. **v1 (Errado)**: Criava 2 tabelas separadas (`exploration_summary`, `exploration_prfaq`)
2. **v2 (Ainda errado)**: Criava 1 tabela (`exploration_documents`)
3. **v3 (CORRETO)**: Reutiliza `experiment_documents` existente (NÃO cria tabela)

### Princípio Correto ✅

**Explorations pertencem a Experiments. Documentos de exploration vão em `experiment_documents`.**

```python
# Exploration tem experiment_id
exploration = Exploration(id="expl_...", experiment_id="exp_...")

# Documento vai na tabela EXISTENTE usando experiment_id da exploration
doc = ExperimentDocument(
    experiment_id=exploration.experiment_id,  # ← USA EXPERIMENT_ID!
    document_type=DocumentType.SUMMARY,
    metadata={
        "source": "exploration",
        "exploration_id": exploration.id,
        "winning_path_nodes": [...]
    }
)
```

### O Que Reutilizar (JÁ EXISTE)

| Item | Arquivo | Status |
|------|---------|--------|
| Tabela | `experiment_documents` | ✅ Existente |
| Entity | `ExperimentDocument` | ✅ Existente |
| Enums | `DocumentType`, `DocumentStatus` | ✅ Existentes |
| Repository | `ExperimentDocumentRepository` | ✅ Existente |
| Schemas | `ExperimentDocumentResponse` | ✅ Existente |
| Migration | N/A | ✅ Não precisa |

### O Que Criar (NOVO)

| Item | Arquivo | Propósito |
|------|---------|-----------|
| Service | `exploration_summary_generator_service.py` | Gera summary via LLM |
| Service | `exploration_prfaq_generator_service.py` | Gera PRFAQ via LLM |
| Endpoints | `exploration.py` (modificar) | Wrapper para documents |
| Frontend | Components + Hooks | UI para geração |

### Validação Final

- [x] Reutiliza tabela `experiment_documents` (NÃO cria tabela nova)
- [x] Reutiliza `ExperimentDocument` entity
- [x] Reutiliza `DocumentType` e `DocumentStatus` enums
- [x] Reutiliza `ExperimentDocumentRepository`
- [x] Metadata JSON identifica origem (`source: "exploration"`)
- [x] Zero migrations necessárias
- [x] Apenas 2 services novos no backend

---

**Ready for**: `/speckit.tasks` (Phase 2 - Task Generation)
