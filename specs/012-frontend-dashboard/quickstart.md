# Quickstart: Frontend Dashboard

**Feature**: 012-frontend-dashboard
**Date**: 2025-12-20

## Pré-requisitos

- Node.js 18+ instalado
- pnpm instalado (`npm install -g pnpm`)
- Backend synth-lab rodando em `http://localhost:8000`

## Setup Inicial

### 1. Instalar Dependências

```bash
cd frontend
pnpm install
```

### 2. Instalar Dependências Adicionais

```bash
# Markdown rendering
pnpm add react-markdown remark-gfm

# Testing (opcional, para TDD)
pnpm add -D vitest @testing-library/react @testing-library/jest-dom jsdom
```

### 3. Configurar Proxy para API

Editar `vite.config.ts`:

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";

export default defineConfig({
  server: {
    host: "::",
    port: 8080,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
```

### 4. Iniciar Backend (terminal separado)

```bash
# Na raiz do projeto synth-lab
make api
# ou
uv run uvicorn synth_lab.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Iniciar Frontend

```bash
cd frontend
pnpm dev
```

Acesse: http://localhost:8080

## Estrutura de Diretórios

```
frontend/src/
├── components/
│   ├── interviews/          # Componentes de entrevistas
│   │   ├── InterviewList.tsx
│   │   ├── InterviewCard.tsx
│   │   ├── NewInterviewDialog.tsx
│   │   └── InterviewMessages.tsx
│   ├── synths/              # Componentes de synths
│   │   ├── SynthList.tsx
│   │   ├── SynthCard.tsx
│   │   ├── SynthDetailDialog.tsx
│   │   └── BigFiveChart.tsx
│   ├── shared/              # Componentes compartilhados
│   │   ├── MarkdownPopup.tsx
│   │   └── StatusBadge.tsx
│   └── ui/                  # shadcn/ui (já existe)
├── hooks/
│   ├── use-research.ts      # Hooks para research API
│   ├── use-synths.ts        # Hooks para synths API
│   ├── use-topics.ts        # Hooks para topics API
│   └── use-sse.ts           # Hook para SSE
├── services/
│   ├── api.ts               # Configuração base
│   ├── research-api.ts      # API de research
│   ├── synths-api.ts        # API de synths
│   └── topics-api.ts        # API de topics
├── types/
│   ├── research.ts          # Types de research
│   ├── synth.ts             # Types de synth
│   ├── topic.ts             # Types de topic
│   ├── prfaq.ts             # Types de PR/FAQ
│   ├── events.ts            # Types de SSE
│   └── common.ts            # Types compartilhados
├── lib/
│   ├── query-keys.ts        # React Query keys
│   ├── schemas.ts           # Zod schemas
│   └── utils.ts             # Utilities
├── pages/
│   ├── Index.tsx            # Página principal
│   ├── InterviewDetail.tsx  # Detalhes da entrevista
│   └── NotFound.tsx         # 404
└── App.tsx                  # Rotas
```

## Fluxos Principais

### Visualizar Lista de Entrevistas

1. Acesse a aplicação
2. A tab "Interviews" está selecionada por padrão
3. Cards de entrevistas são carregados via `/api/research/list`

### Criar Nova Entrevista

1. Na tab "Interviews", clique em "Nova Entrevista"
2. Selecione um tópico (carregado de `/api/topics/list`)
3. Escolha synths específicos ou quantidade aleatória
4. Configure parâmetros (max_turns, modelo)
5. Clique em "Iniciar"
6. É redirecionado para a página de detalhes com streaming

### Visualizar Detalhes da Entrevista

1. Clique em um card de entrevista
2. Navega para `/interviews/:execId`
3. Vê detalhes, lista de synths participantes
4. Se em andamento, mensagens aparecem em tempo real (SSE)
5. Pode ver Summary (markdown) se disponível
6. Pode gerar ou ver PR/FAQ

### Visualizar Lista de Synths

1. Clique na tab "Synths"
2. Grid de cards de synths é carregado via `/api/synths/list`
3. Clique em um card para ver detalhes no modal

### Visualizar Detalhes do Synth

1. Clique em um synth
2. Modal abre com dados completos
3. Avatar carregado de `/api/synths/:id/avatar`
4. Seções: Demografia, Psicografia (Big Five chart), Comportamento, etc.

## Comandos Úteis

```bash
# Desenvolvimento
pnpm dev                 # Inicia servidor dev

# Build
pnpm build              # Build de produção
pnpm preview            # Preview do build

# Linting
pnpm lint               # Executa ESLint

# Testes (após configurar Vitest)
pnpm test               # Executa testes
pnpm test:watch         # Testes em watch mode
```

## Endpoints da API

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/synths/list` | GET | Lista synths |
| `/api/synths/{id}` | GET | Detalhes do synth |
| `/api/synths/{id}/avatar` | GET | Avatar PNG |
| `/api/research/list` | GET | Lista entrevistas |
| `/api/research/{id}` | GET | Detalhes da entrevista |
| `/api/research/{id}/transcripts` | GET | Transcrições |
| `/api/research/{id}/summary` | GET | Summary markdown |
| `/api/research/{id}/stream` | GET | SSE stream |
| `/api/research/execute` | POST | Criar entrevista |
| `/api/topics/list` | GET | Lista tópicos |
| `/api/prfaq/{id}` | GET | Detalhes PR/FAQ |
| `/api/prfaq/{id}/markdown` | GET | PR/FAQ markdown |
| `/api/prfaq/generate` | POST | Gerar PR/FAQ |

## Troubleshooting

### CORS Error

Se receber erro de CORS, verifique:
1. Backend está rodando em `localhost:8000`
2. Proxy está configurado em `vite.config.ts`
3. Requests usam `/api/` prefix

### SSE não conecta

1. Verifique se o endpoint `/api/research/{id}/stream` está acessível
2. Verifique Network tab no DevTools
3. SSE usa EventSource nativo, não precisa de biblioteca

### Avatar não carrega

1. Verifique se synth tem avatar gerado
2. Avatar é servido de `/api/synths/{id}/avatar`
3. Verifique se o backend retorna 200 ou 404

### React Query cache

Para invalidar cache manualmente:

```typescript
import { useQueryClient } from '@tanstack/react-query';

const queryClient = useQueryClient();
queryClient.invalidateQueries({ queryKey: ['research', 'list'] });
```
