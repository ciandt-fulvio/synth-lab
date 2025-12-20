# Research: Frontend Dashboard

**Feature**: 012-frontend-dashboard
**Date**: 2025-12-20

## Technology Stack Decisions

### Frontend Framework

**Decision**: React 18.3 + TypeScript 5.5 + Vite 6.3

**Rationale**: O projeto frontend já existe em `frontend/` com esta stack configurada. Reutilizar a infraestrutura existente reduz tempo de setup e mantém consistência.

**Alternatives Considered**:
- Next.js: Rejeitado - projeto já usa Vite, SSR não é necessário
- Vue/Svelte: Rejeitado - projeto já está em React

### UI Components

**Decision**: shadcn/ui + Radix UI + Tailwind CSS

**Rationale**: Já instalado e configurado no projeto. Todos os componentes necessários estão disponíveis:
- `Tabs` - navegação principal
- `Card` - cards de entrevistas e synths
- `Dialog` - modais/popups
- `Avatar` - imagens de synths
- `Badge` - status indicators
- `Progress` - barras de progresso Big Five
- `Select` - dropdowns de formulário
- `Button`, `Input`, `Label` - formulários

**Alternatives Considered**: Material UI, Chakra UI - rejeitados pois shadcn já está instalado

### Data Fetching

**Decision**: TanStack React Query 5.56

**Rationale**: Já instalado (`@tanstack/react-query`). Oferece:
- Cache automático
- Refetch em background
- Loading/error states
- Suporte a SSE via `useQuery` com refetch

**Alternatives Considered**: SWR, fetch nativo - React Query já está no projeto

### Routing

**Decision**: React Router DOM 6.26

**Rationale**: Já instalado e configurado em `App.tsx`. Estrutura existente:
- `/` - Index page
- `/*` - NotFound

**Novas rotas necessárias**:
- `/interviews` - lista de entrevistas
- `/interviews/:execId` - detalhes da entrevista
- `/synths` - lista de synths

### Charts/Visualization

**Decision**: Recharts 2.12

**Rationale**: Já instalado. Será usado para visualização do Big Five personality (barras horizontais ou radar chart).

**Alternatives Considered**: Chart.js, D3 - Recharts já está disponível

### Forms

**Decision**: React Hook Form 7.53 + Zod 3.23

**Rationale**: Já instalados. Usados para:
- Formulário de nova entrevista
- Validação de inputs

### Date Formatting

**Decision**: date-fns 3.6

**Rationale**: Já instalado. Formatação de datas em português.

### Icons

**Decision**: Lucide React 0.462

**Rationale**: Já instalado. Ícones para tabs, botões e status.

### Markdown Rendering

**Decision**: Adicionar react-markdown

**Rationale**: Componente `MarkdownPopup` já existe usando `react-markdown`, mas a dependência não está em package.json. Precisa ser adicionada.

**Ação necessária**: `pnpm add react-markdown`

### SSE (Server-Sent Events)

**Decision**: EventSource API nativa + hook customizado

**Rationale**: API nativa do browser, não precisa de biblioteca adicional. Criar hook `useSSE` para gerenciar conexão.

**Pattern**:
```typescript
const useResearchSSE = (execId: string) => {
  // Usa EventSource nativo
  // Retorna messages, status, isConnected
}
```

## API Integration

### Base URL

**Decision**: Usar proxy do Vite em desenvolvimento

**Rationale**: CORS já configurado no backend (`allow_origins=["*"]`), mas proxy é mais limpo.

**vite.config.ts update**:
```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, '')
    }
  }
}
```

### Endpoints Utilizados

| Endpoint | Método | Uso |
|----------|--------|-----|
| `/synths/list` | GET | Lista de synths |
| `/synths/{id}` | GET | Detalhes do synth |
| `/synths/{id}/avatar` | GET | Imagem do avatar |
| `/research/list` | GET | Lista de entrevistas |
| `/research/{id}` | GET | Detalhes da entrevista |
| `/research/{id}/transcripts` | GET | Transcrições |
| `/research/{id}/summary` | GET | Summary markdown |
| `/research/{id}/stream` | GET (SSE) | Stream de mensagens |
| `/research/execute` | POST | Iniciar entrevista |
| `/topics/list` | GET | Lista de tópicos |
| `/prfaq/{id}` | GET | Detalhes do PR/FAQ |
| `/prfaq/{id}/markdown` | GET | PR/FAQ markdown |
| `/prfaq/generate` | POST | Gerar PR/FAQ |

## Component Architecture

### Pages

```
src/pages/
├── Index.tsx              # Página principal com tabs
├── InterviewDetail.tsx    # Detalhes da entrevista
└── NotFound.tsx           # 404 (já existe)
```

### Components

```
src/components/
├── interviews/
│   ├── InterviewList.tsx       # Lista de cards
│   ├── InterviewCard.tsx       # Card individual
│   ├── NewInterviewDialog.tsx  # Modal de criação
│   └── InterviewMessages.tsx   # Lista de mensagens SSE
├── synths/
│   ├── SynthList.tsx           # Grid de cards
│   ├── SynthCard.tsx           # Card individual
│   └── SynthDetailDialog.tsx   # Modal de detalhes
├── shared/
│   ├── MarkdownPopup.tsx       # Já existe
│   ├── StatusBadge.tsx         # Badge de status
│   └── BigFiveChart.tsx        # Gráfico Big Five
└── ui/                         # shadcn (já existe)
```

### Hooks

```
src/hooks/
├── use-research.ts        # useQuery para research
├── use-synths.ts          # useQuery para synths
├── use-topics.ts          # useQuery para topics
└── use-sse.ts             # Hook para SSE
```

### Services/API

```
src/services/
├── api.ts                 # Configuração base fetch/axios
├── research-api.ts        # Funções de API research
├── synths-api.ts          # Funções de API synths
└── topics-api.ts          # Funções de API topics
```

## Missing Dependencies

| Package | Version | Reason |
|---------|---------|--------|
| react-markdown | ^9.0.0 | Renderização de markdown |
| remark-gfm | ^4.0.0 | GitHub Flavored Markdown |

**Instalação**: `pnpm add react-markdown remark-gfm`

## Constitution Compliance

### Test-First Development (Principle I)

**Frontend Testing Strategy**:
- Unit tests com Vitest para hooks e utilities
- Component tests com React Testing Library
- E2E tests com Playwright (opcional)

**Ação**: Adicionar Vitest como dev dependency

### Fast Test Battery (Principle II)

- Tests unitários de hooks devem rodar em < 0.5s cada
- Usar mocks para API calls

### File Size Limits (Principle V)

- Componentes TSX podem ter até 1000 linhas (exceção para HTML/TSX)
- Preferir componentes menores e composição

### Language (Principle VI)

- Código em inglês (nomes de variáveis, funções, componentes)
- Documentação em português
- i18n ready: strings externalizadas (futuro)

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| SSE connection drops | UX degradada | Retry automático com backoff |
| API lenta | Loading prolongado | Skeleton loading, cache |
| Avatares grandes | Performance | Lazy loading, placeholder |
| Muitos synths | Memory | Virtualização com react-window |
