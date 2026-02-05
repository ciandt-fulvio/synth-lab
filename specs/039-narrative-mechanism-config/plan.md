# Implementation Plan: Narrative Mechanism Configuration

**Branch**: `039-narrative-mechanism-config` | **Date**: 2026-02-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/039-narrative-mechanism-config/spec.md`

## Summary

Substituir a interface de sliders do Step 2 do wizard de criação de experimento por uma abordagem narrativa onde mecanismos e suas opções ficam cadastrados no banco de dados, a LLM gera um texto narrativo com placeholders para mecanismos relevantes, e o usuário ajusta intensidades via dropdowns inline no texto.

## Technical Context

**Language/Version**: Python 3.13+ (backend), TypeScript 5.5+ (frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0+, Pydantic, OpenAI SDK (gpt-4o-mini), React 18, TanStack Query, shadcn/ui
**Storage**: PostgreSQL 14+ (novas tabelas para mecanismos/opções, JSONB para narrativa gerada)
**Testing**: pytest (backend), Vitest (frontend)
**Target Platform**: Web application (Linux server backend, browser frontend)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: Geração de narrativa < 5 segundos (SC-005)
**Constraints**: Mecanismos e opções devem ser extensíveis sem deploy (SC-006)
**Scale/Scope**: MVP com 6 mecanismos, 5 opções cada, 5 tipos de feature

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| Test-First Development (TDD/BDD) | ✅ PASS | Tests escritos antes da implementação |
| Fast Test Battery (<5s) | ✅ PASS | Unit tests para entidades e schemas |
| Complete Test Battery before PR | ✅ PASS | Integration tests para API endpoints |
| Frequent Commits | ✅ PASS | Commits atômicos por milestone |
| Simplicity (<30 lines/fn, <500 lines/file) | ✅ PASS | Funções pequenas, arquivos modulares |
| Language (code=EN, docs=PT) | ✅ PASS | Código em inglês, docs em português |
| Architecture - Router pattern | ✅ PASS | Router → Service → Repository |
| Architecture - Phoenix tracing | ✅ PASS | LLM calls com _tracer.start_as_current_span() |
| Architecture - Alembic migrations | ✅ PASS | Novas tabelas via migrations |
| Frontend - Components puros | ✅ PASS | NarrativeMechanismEditor sem fetch interno |
| Frontend - Hooks para data | ✅ PASS | useMechanisms, useGenerateNarrative hooks |

## Project Structure

### Documentation (this feature)

```text
specs/039-narrative-mechanism-config/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (OpenAPI)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
# Backend
src/synth_lab/
├── domain/entities/
│   ├── mechanism_definition.py    # NEW: MechanismDefinition entity
│   ├── mechanism_option.py        # NEW: MechanismOption entity
│   └── feature_type.py            # NEW: FeatureType entity
├── repositories/
│   └── mechanism_repository.py    # NEW: Data access for mechanisms
├── services/
│   └── narrative_service.py       # NEW: LLM narrative generation
├── api/
│   ├── schemas/
│   │   └── mechanisms.py          # NEW: API schemas
│   └── routers/
│       └── mechanisms.py          # NEW: API endpoints

# Frontend
frontend/src/
├── components/
│   └── experiments/
│       └── NarrativeMechanismEditor.tsx  # NEW: Main component
├── hooks/
│   ├── use-mechanisms.ts          # NEW: Fetch mechanisms/options
│   └── use-narrative.ts           # NEW: Generate narrative mutation
├── services/
│   └── mechanisms-api.ts          # NEW: API client
└── types/
    └── mechanisms.ts              # NEW: TypeScript types

# Database
alembic/versions/
└── xxx_add_mechanism_tables.py    # NEW: Migration for new tables

# Seeds
scripts/
└── seed_mechanisms.py             # NEW: Seed mechanism definitions
```

**Structure Decision**: Web application pattern seguindo arquitetura existente do synth-lab. Novas entidades em `domain/entities/`, novo repositório para acesso a dados, novo serviço para lógica LLM, novos endpoints em router dedicado.

## Complexity Tracking

> Nenhuma violação de constitution detectada.
