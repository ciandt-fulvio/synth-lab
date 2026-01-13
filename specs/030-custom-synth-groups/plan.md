# Implementation Plan: Grupos de Synths Customizados

**Branch**: `030-custom-synth-groups` | **Date**: 2026-01-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/030-custom-synth-groups/spec.md`

## Summary

Permitir que PMs criem grupos de synths com distribuições demográficas customizadas (idade, escolaridade, deficiências, composição familiar, domain expertise) para simular públicos específicos como aposentados, PcD, universitários e especialistas.

**Technical Approach**:
- Adicionar coluna `config` JSONB na tabela `synth_groups` para armazenar configurações de distribuição
- Modificar módulos gen_synth (`demographics.py`, `disabilities.py`, `simulation_attributes.py`) para aceitar distribuições customizadas
- Criar componentes frontend para slider-histograma com redistribuição automática
- API REST com POST para criar grupo + gerar 500 synths de forma síncrona

## Technical Context

**Language/Version**: Python 3.13+ (backend), TypeScript 5.5+ (frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0+, Pydantic, React 18, TanStack Query, shadcn/ui
**Storage**: PostgreSQL 14+ (JSONB for config), S3-compatible (avatars)
**Testing**: pytest (backend), Vitest (frontend)
**Target Platform**: Web application (browser + Linux server)
**Project Type**: Web application (fullstack)
**Performance Goals**: Gerar 500 synths em < 30 segundos, API response < 5s
**Constraints**: Request síncrono (sem job queue), distribuições devem somar 100%
**Scale/Scope**: ~10 grupos customizados por PM, 500 synths fixos por grupo

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First Development | PASS | Tests will be written before implementation code |
| II. Fast Test Battery | PASS | Unit tests for validation logic < 5s |
| III. Complete Test Battery | PASS | Integration tests for API + gen_synth before PR |
| IV. Frequent Commits | PASS | Atomic commits per logical change |
| V. Simplicity | PASS | Reutiliza gen_synth modules existentes |
| VI. Language | PASS | Code in English, docs in Portuguese |
| VII. Architecture | PASS | Follows router→service→repository pattern |

**Architecture Compliance**:
- Router: `request → service.create_with_config() → response`
- Service: Lógica de validação e orquestração de gen_synth
- Repository: SQL parametrizado para INSERT com JSONB
- Frontend: Components puros, hooks para React Query, fetchAPI em services

## Project Structure

### Documentation (this feature)

```text
specs/030-custom-synth-groups/
├── plan.md              # This file
├── research.md          # Phase 0 output - codebase analysis
├── data-model.md        # Phase 1 output - entity schemas
├── quickstart.md        # Phase 1 output - development guide
├── contracts/           # Phase 1 output - API contracts
│   ├── synth-groups-api.yaml   # OpenAPI spec
│   └── frontend-types.ts       # TypeScript types
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/synth_lab/
├── api/
│   ├── routers/
│   │   └── synth_groups.py       # MODIFY: add POST with config
│   └── schemas/
│       └── synth_group.py        # CREATE: Pydantic request/response schemas
├── services/
│   └── synth_group_service.py    # MODIFY: add create_with_config()
├── repositories/
│   └── synth_group_repository.py # MODIFY: support config JSONB
├── domain/
│   ├── entities/
│   │   └── synth_group.py        # MODIFY: add config field
│   └── constants/
│       └── group_defaults.py     # CREATE: IBGE default values
├── gen_synth/
│   ├── demographics.py           # MODIFY: accept custom_distributions
│   ├── disabilities.py           # MODIFY: accept rate/severity config
│   └── simulation_attributes.py  # MODIFY: accept alpha/beta params
└── alembic/versions/
    └── xxx_add_config_column.py  # CREATE: migration

frontend/src/
├── components/synths/
│   ├── CreateSynthGroupModal.tsx     # CREATE: main modal
│   ├── DistributionSlider.tsx        # CREATE: slider-histogram
│   ├── DistributionSliderGroup.tsx   # CREATE: group with reset
│   └── SynthGroupSelect.tsx          # CREATE: "Baseado em" select
├── hooks/
│   └── use-synth-groups.ts           # CREATE: React Query hooks
├── services/
│   └── synth-groups-api.ts           # MODIFY: add create function
├── lib/
│   └── query-keys.ts                 # MODIFY: add synth-groups keys
└── types/
    └── synthGroup.ts                 # MODIFY: add GroupConfig types

tests/
├── services/
│   └── test_synth_group_service.py   # CREATE: service tests
├── api/
│   └── test_synth_groups_router.py   # CREATE: router tests
└── gen_synth/
    ├── test_demographics_custom.py   # CREATE: custom distribution tests
    └── test_disabilities_custom.py   # CREATE: custom rate tests
```

**Structure Decision**: Web application with existing synth-lab structure. Backend in `src/synth_lab/`, frontend in `frontend/src/`. Uses established patterns from codebase (services, repositories, React Query hooks).

## Files to Create/Modify

### Backend Summary

| File | Action | Description |
|------|--------|-------------|
| `api/routers/synth_groups.py` | Modify | Add POST with config |
| `api/schemas/synth_group.py` | Create | Pydantic schemas for request/response |
| `services/synth_group_service.py` | Modify | Add create_with_config method |
| `repositories/synth_group_repository.py` | Modify | Support config JSONB column |
| `domain/entities/synth_group.py` | Modify | Add config field to entity |
| `domain/constants/group_defaults.py` | Create | IBGE default constants |
| `gen_synth/demographics.py` | Modify | Accept custom_distributions |
| `gen_synth/disabilities.py` | Modify | Accept rate and severity config |
| `gen_synth/simulation_attributes.py` | Modify | Accept alpha/beta for expertise |
| `alembic/versions/xxx_add_config.py` | Create | Migration for config column |

### Frontend Summary

| File | Action | Description |
|------|--------|-------------|
| `pages/SynthsPage.tsx` | Modify | Add group selection + create button |
| `components/synths/CreateSynthGroupModal.tsx` | Create | Main modal component |
| `components/synths/DistributionSlider.tsx` | Create | Slider-histogram component |
| `components/synths/DistributionSliderGroup.tsx` | Create | Group with reset button |
| `components/synths/SynthGroupSelect.tsx` | Create | Dropdown for "Baseado em" |
| `hooks/use-synth-groups.ts` | Create | useQuery/useMutation hooks |
| `services/synth-groups-api.ts` | Modify | Add createSynthGroup function |
| `lib/query-keys.ts` | Modify | Add synth-groups keys |
| `types/synthGroup.ts` | Modify | Add GroupConfig types |

### Database Summary

| Action | Description |
|--------|-------------|
| Migration | Add `config` JSONB column to `synth_groups` table |
| Seed | Update Default group with explicit IBGE config |

## Key Design Decisions

1. **Storage**: JSONB column for flexible distribution config storage
2. **Generation**: Synchronous (blocking request), 500 synths per group
3. **Education Mapping**: 4-level UI expands to 8-level internal (backend)
4. **Disability Logic**: Dynamic severity distribution based on rate threshold (8%)
5. **Slider UX**: Auto-redistribution to maintain 100% sum
6. **Groups**: Immutable after creation, Default group seeded with IBGE

## Complexity Tracking

> No constitution violations to justify. Design follows established patterns.

| Aspect | Approach | Rationale |
|--------|----------|-----------|
| Config storage | JSONB column | Flexible schema, PostgreSQL native |
| Synth generation | Modify existing modules | Reuse validated IBGE logic |
| Slider redistribution | Frontend local state | Form-local, no global state needed |

## Related Artifacts

- **Research**: [research.md](./research.md) - Codebase analysis and decisions
- **Data Model**: [data-model.md](./data-model.md) - Entity schemas and validation
- **API Contract**: [contracts/synth-groups-api.yaml](./contracts/synth-groups-api.yaml) - OpenAPI spec
- **Frontend Types**: [contracts/frontend-types.ts](./contracts/frontend-types.ts) - TypeScript definitions
- **Quickstart**: [quickstart.md](./quickstart.md) - Development guide
