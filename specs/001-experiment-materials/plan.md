# Implementation Plan: Experiment Materials Upload

**Branch**: `001-experiment-materials` | **Date**: 2026-01-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-experiment-materials/spec.md`

## Summary

Implementar sistema de upload de materiais visuais (imagens, vídeos, documentos) para experimentos, permitindo que synths acessem esses materiais durante entrevistas simuladas via tool LLM. Upload utiliza presigned URLs para S3-compatible Railway Buckets, com geração assíncrona de descrições via GPT-4o-mini.

## Technical Context

**Language/Version**: Python 3.13+ (backend), TypeScript 5.5+ (frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0+, Pydantic, OpenAI SDK, boto3 (S3), React 18, TanStack Query, shadcn/ui
**Storage**: PostgreSQL 14+ (metadata), S3-compatible storage (files)
**Testing**: pytest, vitest
**Target Platform**: Railway (production/staging)
**Project Type**: Web application (FastAPI backend + React frontend)
**Performance Goals**:
- Upload completo < 30s para arquivos típicos (< 10MB)
- 50 uploads concorrentes sem degradação
- Preview de thumbnails < 2s após seleção
**Constraints**:
- Máximo 10 arquivos por experimento
- Máximo 250MB total por experimento
- Arquivos individuais: 25MB (imagens/docs), 100MB (vídeos)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Gate I: Test-First Development (TDD/BDD) ✅
- **Compliance**: Implementação seguirá TDD
- Acceptance scenarios definidos no spec.md em formato Given-When-Then
- Testes serão escritos ANTES da implementação

### Gate II: Fast Test Battery ✅
- **Compliance**: Testes unitários rápidos para services e repositories
- Testes de integração com mocks de S3/LLM para manter < 5s

### Gate III: Complete Test Battery Before PR ✅
- **Compliance**: Testes E2E de upload e visualização antes de PR
- Coverage threshold será mantido

### Gate IV: Frequent Commits ✅
- **Compliance**: Commits atômicos por componente
- Estrutura: domain → repository → service → router → frontend

### Gate V: Simplicity and Code Quality ✅
- **Compliance**:
- Funções < 30 linhas
- Arquivos < 500 linhas
- Padrões existentes reutilizados (tools.py, repository pattern)

### Gate VI: Language ✅
- **Compliance**:
- Código em inglês
- Documentação em português
- Mensagens UI i18n-ready

### Gate VII: Architecture ✅
- **Compliance**:
- Router: request → service → response
- Lógica em services
- SQL em repositories
- LLM calls com Phoenix tracing
- Frontend: Pages compõem, Components puros, Hooks encapsulam queries

## Project Structure

### Documentation (this feature)

```text
specs/001-experiment-materials/
├── plan.md              # Este arquivo
├── spec.md              # Especificação de requisitos
├── research.md          # Decisões técnicas e alternativas
├── data-model.md        # Entidades e schemas
├── quickstart.md        # Guia de implementação
├── contracts/           # Contratos de API
│   └── materials-api.yaml
└── tasks.md             # Tarefas de implementação (criado por /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/synth_lab/
│   ├── api/
│   │   ├── routers/
│   │   │   └── materials.py          # NEW: Router de materials
│   │   └── schemas/
│   │       └── materials.py          # NEW: Schemas de request/response
│   ├── domain/
│   │   └── entities/
│   │       └── experiment_material.py # NEW: Entidade de domínio
│   ├── models/
│   │   └── orm/
│   │       └── material.py           # NEW: ORM model
│   ├── repositories/
│   │   └── experiment_material_repository.py # NEW: Repository
│   ├── services/
│   │   ├── material_service.py       # NEW: Serviço principal
│   │   ├── material_description_service.py # NEW: Geração de descrições
│   │   └── research_agentic/
│   │       └── tools.py              # MODIFY: Adicionar ver_material
│   └── infrastructure/
│       └── storage_client.py         # NEW: Cliente S3
└── tests/
    ├── unit/
    │   └── services/
    │       └── test_material_service.py
    └── integration/
        └── test_materials_api.py

frontend/
├── src/
│   ├── components/
│   │   └── experiments/
│   │       ├── MaterialUpload.tsx    # NEW: Componente de upload
│   │       └── MaterialGallery.tsx   # NEW: Galeria de previews
│   ├── hooks/
│   │   └── use-materials.ts          # NEW: Hooks de materials
│   ├── services/
│   │   └── materials-api.ts          # NEW: Funções de API
│   └── types/
│       └── material.ts               # NEW: Types
└── tests/
    └── components/
        └── MaterialUpload.test.tsx
```

**Structure Decision**: Web application (backend/ + frontend/) - estrutura já existente no projeto. Novos arquivos adicionados seguindo padrões estabelecidos.

## Complexity Tracking

> Nenhuma violação de constitution identificada.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |

---

## Phase 0: Research Summary

Todas as decisões técnicas documentadas em [research.md](./research.md):

| Decisão | Escolha | Rationale |
|---------|---------|-----------|
| Storage Backend | Railway Buckets (S3) | Nativo Railway, presigned URLs grátis |
| Upload Flow | Presigned URLs | Não roteia pelo backend, escalável |
| Descrições | GPT-4o-mini async | Rápido, barato, suporta visão |
| Tool Entrevista | `ver_material` function_tool | Segue padrão existente |
| Banco de Dados | Nova tabela `experiment_materials` | Separação clara de responsabilidades |

---

## Phase 1: Design Summary

### Data Model

Documentado em [data-model.md](./data-model.md):

- **ExperimentMaterial**: Nova entidade com 12 campos
- Relacionamento 1:N com Experiment (cascade delete)
- Estados de descrição: pending → generating → completed/failed

### API Contracts

Documentado em [contracts/materials-api.yaml](./contracts/materials-api.yaml):

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/experiments/{id}/materials` | GET | Listar materiais |
| `/experiments/{id}/materials/upload-url` | POST | Obter URL de upload |
| `/experiments/{id}/materials/confirm` | POST | Confirmar upload |
| `/experiments/{id}/materials/reorder` | PUT | Reordenar materiais |
| `/experiments/{id}/materials/{mid}` | GET | Obter material |
| `/experiments/{id}/materials/{mid}` | DELETE | Remover material |
| `/experiments/{id}/materials/{mid}/view-url` | GET | URL de visualização |
| `/experiments/{id}/materials/{mid}/retry-description` | POST | Reprocessar descrição |

### Quickstart Guide

Documentado em [quickstart.md](./quickstart.md):

- Configuração de ambiente
- Fluxo de upload passo a passo
- Implementação de backend (storage, service, description)
- Implementação de frontend (dropzone, hooks)
- Integração com sistema de entrevistas

---

## Post-Design Constitution Re-Check

### Gate VII: Architecture (Re-check) ✅

Verificação pós-design:

- [x] Router apenas faz request → service → response
- [x] MaterialService contém toda lógica de negócio
- [x] ExperimentMaterialRepository encapsula SQL
- [x] MaterialDescriptionService usa Phoenix tracing para LLM
- [x] Frontend: MaterialUpload é componente puro, useMaterials encapsula query

### Additional Checks

- [x] Não há SQL no router
- [x] Não há prompts LLM no router
- [x] Validações de negócio estão no service
- [x] Schemas Pydantic definidos em api/schemas/
- [x] Query keys centralizadas no frontend

---

## Implementation Scope

Esta feature será implementada em **4 fases incrementais**:

### P1: Upload e Storage (Core)
- Endpoint de upload com presigned URLs
- Tabela e repository de materials
- Confirmação e persistência de metadata
- Frontend: dropzone e upload

### P2: Visualização e Preview
- Geração de thumbnails (imagens, vídeos, PDFs)
- Galeria de preview na página do experimento
- Visualização em tela cheia

### P3: Processamento de Descrições
- Geração assíncrona com GPT-4o-mini
- Status de processamento (pending/generating/completed/failed)
- Retry de descrições com falha

### P4: Integração com Entrevistas
- Tool `ver_material` para agentes
- Integração no runner de entrevistas
- Referências em PR-FAQ

---

## Next Steps

1. ✅ Phase 0: Research completed → research.md
2. ✅ Phase 1: Design completed → data-model.md, contracts/, quickstart.md
3. ⏳ Execute `/speckit.tasks` para gerar tasks.md
4. ⏳ Execute `/speckit.implement` para implementar tasks

---

## References

- [Railway Storage Buckets](https://docs.railway.com/guides/storage-buckets)
- [OpenAI Vision API](https://platform.openai.com/docs/guides/images-vision)
- [react-dropzone](https://react-dropzone.js.org/)
