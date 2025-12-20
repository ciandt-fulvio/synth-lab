# Implementation Plan: Frontend Dashboard

**Branch**: `012-frontend-dashboard` | **Date**: 2025-12-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/012-frontend-dashboard/spec.md`

## Summary

Implementar um frontend React para o synth-lab que consome a API REST existente. O dashboard terá duas tabs principais: "Interviews" (lista e detalhes de pesquisas/entrevistas) e "Synths" (galeria de personas sintéticas). Inclui funcionalidades de streaming SSE para acompanhamento em tempo real, popups markdown para relatórios, e formulário para criar novas pesquisas.

## Technical Context

**Language/Version**: TypeScript 5.5.3 + React 18.3.1
**Primary Dependencies**: Vite 6.3.4, shadcn/ui, TanStack React Query 5.56, React Router DOM 6.26, Tailwind CSS 3.4
**Storage**: N/A (frontend consome API REST do backend)
**Testing**: Vitest + React Testing Library (a configurar)
**Target Platform**: Web (navegadores modernos: Chrome, Firefox, Safari, Edge)
**Project Type**: Web application (frontend only, consumindo backend existente)
**Performance Goals**: < 3s para carregamento inicial, < 1s latência SSE
**Constraints**: Deve usar stack existente em `frontend/`, responsivo
**Scale/Scope**: ~15 componentes, ~5 hooks, ~4 services

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First Development | PASS | Vitest será configurado, testes antes de implementação |
| II. Fast Test Battery | PASS | Testes unitários de hooks < 0.5s cada |
| III. Complete Test Battery Before PR | PASS | Todos os testes passarão antes do PR |
| IV. Frequent Commits | PASS | Commit a cada componente/hook completado |
| V. Simplicity & Code Quality | PASS | Componentes < 1000 linhas (exceção TSX), funções < 30 linhas |
| VI. Language | PASS | Código em inglês, docs em português, i18n ready |
| VII. Architecture | N/A | Frontend segue estrutura própria, não backend |

## Project Structure

### Documentation (this feature)

```text
specs/012-frontend-dashboard/
├── spec.md              # Especificação da feature
├── plan.md              # Este arquivo
├── research.md          # Decisões técnicas e research
├── data-model.md        # TypeScript interfaces
├── quickstart.md        # Guia de uso
├── checklists/
│   └── requirements.md  # Checklist de qualidade
└── tasks.md             # Tarefas (gerado por /speckit.tasks)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── components/
│   │   ├── interviews/
│   │   │   ├── InterviewList.tsx
│   │   │   ├── InterviewCard.tsx
│   │   │   ├── NewInterviewDialog.tsx
│   │   │   └── InterviewMessages.tsx
│   │   ├── synths/
│   │   │   ├── SynthList.tsx
│   │   │   ├── SynthCard.tsx
│   │   │   ├── SynthDetailDialog.tsx
│   │   │   └── BigFiveChart.tsx
│   │   ├── shared/
│   │   │   ├── MarkdownPopup.tsx (já existe)
│   │   │   └── StatusBadge.tsx
│   │   └── ui/ (shadcn - já existe)
│   ├── hooks/
│   │   ├── use-research.ts
│   │   ├── use-synths.ts
│   │   ├── use-topics.ts
│   │   └── use-sse.ts
│   ├── services/
│   │   ├── api.ts
│   │   ├── research-api.ts
│   │   ├── synths-api.ts
│   │   └── topics-api.ts
│   ├── types/
│   │   ├── index.ts
│   │   ├── research.ts
│   │   ├── synth.ts
│   │   ├── topic.ts
│   │   ├── prfaq.ts
│   │   ├── events.ts
│   │   └── common.ts
│   ├── lib/
│   │   ├── query-keys.ts
│   │   ├── schemas.ts
│   │   └── utils.ts (já existe)
│   ├── pages/
│   │   ├── Index.tsx (modificar)
│   │   ├── InterviewDetail.tsx (novo)
│   │   └── NotFound.tsx (já existe)
│   └── App.tsx (modificar rotas)
└── tests/
    ├── hooks/
    │   ├── use-research.test.ts
    │   ├── use-synths.test.ts
    │   └── use-sse.test.ts
    └── components/
        ├── InterviewCard.test.tsx
        └── SynthCard.test.tsx
```

**Structure Decision**: Web application frontend-only. Utiliza estrutura existente em `frontend/` com adição de diretórios `types/`, `services/`, e novos componentes organizados por domínio (`interviews/`, `synths/`).

## Implementation Phases

### Phase 1: Foundation & Types (P1 - Setup)

1. Configurar Vitest para testes
2. Adicionar dependências (react-markdown, remark-gfm)
3. Configurar proxy do Vite para API
4. Criar todas as interfaces TypeScript em `types/`
5. Criar query-keys e schemas em `lib/`

### Phase 2: API Services & Hooks (P1 - Infrastructure)

1. Criar `services/api.ts` - configuração base
2. Criar `services/synths-api.ts` - funções de API
3. Criar `services/research-api.ts` - funções de API
4. Criar `services/topics-api.ts` - funções de API
5. Criar `hooks/use-synths.ts` - React Query hooks
6. Criar `hooks/use-research.ts` - React Query hooks
7. Criar `hooks/use-topics.ts` - React Query hooks
8. Criar `hooks/use-sse.ts` - SSE hook

### Phase 3: Synth Components (P1 - User Story 3 & 4)

1. Criar `SynthCard.tsx` - card com avatar e info básica
2. Criar `SynthList.tsx` - grid de cards com paginação
3. Criar `BigFiveChart.tsx` - visualização Big Five
4. Criar `SynthDetailDialog.tsx` - modal de detalhes

### Phase 4: Interview Components (P1 - User Story 1 & 2)

1. Criar `StatusBadge.tsx` - badge de status
2. Criar `InterviewCard.tsx` - card de entrevista
3. Criar `InterviewList.tsx` - lista com paginação
4. Atualizar `MarkdownPopup.tsx` - garantir funcionalidade
5. Criar `InterviewDetail.tsx` (page) - detalhes completos

### Phase 5: Navigation & Routing (P1 - Integration)

1. Atualizar `App.tsx` - adicionar rotas
2. Atualizar `Index.tsx` - tabs Interviews/Synths
3. Integrar todos os componentes

### Phase 6: New Interview (P2 - User Story 5)

1. Criar `NewInterviewDialog.tsx` - formulário de criação
2. Integrar com `InterviewList.tsx`

### Phase 7: Real-time & PR/FAQ (P3 - User Story 6 & 7)

1. Criar `InterviewMessages.tsx` - lista com SSE
2. Integrar SSE na página de detalhes
3. Adicionar funcionalidade de gerar PR/FAQ

## Dependencies

### Runtime Dependencies (adicionar)

```json
{
  "react-markdown": "^9.0.0",
  "remark-gfm": "^4.0.0"
}
```

### Dev Dependencies (adicionar)

```json
{
  "vitest": "^2.0.0",
  "@testing-library/react": "^16.0.0",
  "@testing-library/jest-dom": "^6.0.0",
  "jsdom": "^25.0.0"
}
```

## Testing Strategy

### Unit Tests (Fast Battery)

- Hooks: `use-research`, `use-synths`, `use-sse`
- Utilities: formatters, helpers
- Target: < 5s total, < 0.5s each

### Component Tests

- Cards: `InterviewCard`, `SynthCard`
- Lists: `InterviewList`, `SynthList`
- Dialogs: `SynthDetailDialog`, `NewInterviewDialog`

### Integration Tests

- Full flows com mock API
- SSE connection handling

## Complexity Tracking

> Nenhuma violação identificada

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |

## Related Documents

- [spec.md](./spec.md) - Especificação da feature
- [research.md](./research.md) - Decisões técnicas
- [data-model.md](./data-model.md) - TypeScript interfaces
- [quickstart.md](./quickstart.md) - Guia de uso
