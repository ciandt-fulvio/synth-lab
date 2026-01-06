# Arquitetura do Frontend - synth-lab

## Visão Geral

O frontend do **synth-lab** é uma aplicação React com TypeScript, seguindo uma arquitetura em camadas que separa responsabilidades entre UI, lógica de estado, e comunicação com a API.

```
┌─────────────────────────────────────────────────────────────────┐
│                         UI LAYER                                 │
│  pages/           - Páginas (rotas)                             │
│  components/      - Componentes reutilizáveis                   │
│  components/ui/   - Componentes base (shadcn/ui)                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       STATE LAYER                                │
│  hooks/           - Custom hooks (React Query, lógica)          │
│  lib/query-keys.ts - Chaves de cache centralizadas              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SERVICE LAYER                               │
│  services/*-api.ts - Funções de chamada à API REST              │
│  services/api.ts   - Cliente HTTP base (fetchAPI)               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       DATA LAYER                                 │
│  types/           - TypeScript types/interfaces                 │
│  data/            - Dados estáticos, constantes                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Estrutura de Diretórios

```
frontend/src/
├── App.tsx                    # Rotas (React Router)
├── main.tsx                   # Entry point
├── globals.css                # Estilos globais (Tailwind)
│
├── pages/                     # Páginas (uma por rota)
│   ├── Index.tsx              # Página principal
│   ├── Synths.tsx             # Lista de synths
│   ├── ExperimentDetail.tsx   # Detalhes de experiment
│   └── ...
│
├── components/                # Componentes reutilizáveis
│   ├── ui/                    # shadcn/ui (NÃO EDITAR)
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   └── ...
│   ├── shared/                # Componentes compartilhados
│   │   ├── Pagination.tsx
│   │   └── ...
│   ├── experiments/           # Componentes de experiments
│   │   ├── ExperimentCard.tsx
│   │   └── NewExperimentDialog.tsx
│   └── synths/                # Componentes de synths
│       └── SynthCard.tsx
│
├── hooks/                     # Custom hooks
│   ├── use-experiments.ts     # CRUD de experiments
│   ├── use-synths.ts          # CRUD de synths
│   ├── use-tags.ts            # CRUD de tags
│   ├── use-sse.ts             # Server-Sent Events
│   └── use-toast.ts           # Notificações
│
├── services/                  # Chamadas à API
│   ├── api.ts                 # Cliente base (fetchAPI)
│   ├── experiments-api.ts     # API de experiments
│   ├── synths-api.ts          # API de synths
│   └── ...
│
├── types/                     # TypeScript types
│   ├── index.ts               # Types compartilhados
│   ├── experiment.ts          # Types de experiment
│   └── ...
│
├── lib/                       # Utilitários
│   ├── utils.ts               # Funções helper (cn, etc)
│   └── query-keys.ts          # Chaves React Query
│
└── data/                      # Dados estáticos
    └── ...
```

---

## Regras por Camada

### 1. Pages (`pages/`)

**Responsabilidades:**
- Composição de componentes
- Binding de rotas
- Layout da página
- Chamada de hooks para dados

**PERMITIDO:**
```tsx
// pages/Experiments.tsx
export default function Experiments() {
  const { data, isLoading } = useExperiments();  // ✅ Hook para dados
  const [isDialogOpen, setIsDialogOpen] = useState(false);  // ✅ Estado local de UI

  if (isLoading) return <Loading />;

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold">Experiments</h1>
      <Button onClick={() => setIsDialogOpen(true)}>New</Button>

      {/* ✅ Composição de componentes */}
      {data?.data.map(exp => (
        <ExperimentCard key={exp.id} experiment={exp} />
      ))}

      <NewExperimentDialog
        open={isDialogOpen}
        onOpenChange={setIsDialogOpen}
      />
    </div>
  );
}
```

**PROIBIDO:**
```tsx
// ❌ Fetch direto na página
export default function Experiments() {
  const [data, setData] = useState([]);

  useEffect(() => {
    fetch('/api/experiments').then(r => r.json()).then(setData);  // ❌
  }, []);
}

// ❌ Lógica de negócio na página
export default function Experiments() {
  const handleCreate = async (data) => {
    // ❌ Validação de negócio
    if (data.name.length > 100) {
      toast.error("Name too long");
      return;
    }
    // ❌ Chamada API direta
    await fetch('/api/experiments', { method: 'POST', body: JSON.stringify(data) });
  };
}
```

**Regra de Ouro:** Pages apenas compõem componentes e usam hooks.

---

### 2. Components (`components/`)

**Responsabilidades:**
- UI reutilizável
- Receber dados via props
- Emitir eventos via callbacks

**Organização:**
```
components/
├── ui/            # shadcn/ui - NÃO EDITAR DIRETAMENTE
├── shared/        # Componentes genéricos (Pagination, Loading)
├── experiments/   # Componentes específicos de experiments
├── synths/        # Componentes específicos de synths
└── ...
```

**PERMITIDO:**
```tsx
// components/experiments/ExperimentCard.tsx
interface ExperimentCardProps {
  experiment: Experiment;
  onSelect?: (id: string) => void;  // ✅ Callback
}

export function ExperimentCard({ experiment, onSelect }: ExperimentCardProps) {
  return (
    <Card onClick={() => onSelect?.(experiment.id)}>
      <CardHeader>
        <CardTitle>{experiment.name}</CardTitle>
      </CardHeader>
      <CardContent>
        <p>{experiment.hypothesis}</p>
      </CardContent>
    </Card>
  );
}
```

**PROIBIDO:**
```tsx
// ❌ Fetch dentro de componente
export function ExperimentCard({ id }: { id: string }) {
  const [data, setData] = useState(null);
  useEffect(() => {
    fetch(`/api/experiments/${id}`).then(r => r.json()).then(setData);
  }, [id]);
}

// ❌ Chamada de mutation dentro de componente
export function ExperimentCard({ experiment }) {
  const handleDelete = async () => {
    await fetch(`/api/experiments/${experiment.id}`, { method: 'DELETE' });
  };
}
```

**Regra de Ouro:** Componentes são puros - recebem props, retornam JSX.

---

### 3. Hooks (`hooks/`)

**Responsabilidades:**
- Encapsular React Query (useQuery, useMutation)
- Gerenciar estado complexo
- Abstrair lógica reutilizável

**Padrão para CRUD:**
```tsx
// hooks/use-experiments.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import {
  listExperiments,
  createExperiment,
  deleteExperiment
} from '@/services/experiments-api';

// ✅ Hook de listagem
export function useExperiments(params?: PaginationParams) {
  return useQuery({
    queryKey: [...queryKeys.experimentsList, params],
    queryFn: () => listExperiments(params),
  });
}

// ✅ Hook de detalhes
export function useExperiment(id: string) {
  return useQuery({
    queryKey: queryKeys.experimentDetail(id),
    queryFn: () => getExperiment(id),
    enabled: !!id,  // Só executa se tiver ID
  });
}

// ✅ Hook de criação
export function useCreateExperiment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ExperimentCreate) => createExperiment(data),
    onSuccess: () => {
      // Invalida cache para refetch
      queryClient.invalidateQueries({ queryKey: queryKeys.experimentsList });
    },
  });
}

// ✅ Hook de deleção
export function useDeleteExperiment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteExperiment(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.experimentsList });
    },
  });
}
```

**PROIBIDO:**
```tsx
// ❌ Fetch direto no hook (sem React Query)
export function useExperiments() {
  const [data, setData] = useState([]);
  useEffect(() => {
    fetch('/api/experiments').then(r => r.json()).then(setData);
  }, []);
  return data;
}

// ❌ Chamada API inline
export function useCreateExperiment() {
  return async (data) => {
    const response = await fetch('/api/experiments', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return response.json();
  };
}
```

#### Hooks de Tags (`use-tags.ts`)

Hooks para gerenciamento de tags em experimentos.

| Hook | Parâmetros | Retorno | Propósito |
|------|------------|---------|-----------|
| `useTags` | - | `UseQueryResult<Tag[], Error>` | Listar todas as tags disponíveis |
| `useCreateTag` | - | `UseMutationResult<Tag, Error, TagCreateRequest>` | Criar nova tag |
| `useAddTagToExperiment` | - | `UseMutationResult<void, Error, { experimentId: string; data: AddTagRequest }>` | Adicionar tag a um experimento |
| `useRemoveTagFromExperiment` | - | `UseMutationResult<void, Error, { experimentId: string; tagName: string }>` | Remover tag de um experimento |

**Types utilizados:**
```tsx
// types/tag.ts
interface Tag {
  id: string;
  name: string;
  color: string;
  created_at: string;
}

interface TagCreateRequest {
  name: string;
  color?: string;
}

interface AddTagRequest {
  tag_name: string;
}
```

**Dependências internas:**
- `@tanstack/react-query`: `useQuery`, `useMutation`, `useQueryClient`
- `@/lib/query-keys`: `queryKeys.tags()`, `queryKeys.experiments()`
- `@/services/tags-api`: `listTags`, `createTag`, `addTagToExperiment`, `removeTagFromExperiment`

**Exemplo de uso:**
```tsx
// components/experiments/TagSelector.tsx
import { useTags, useAddTagToExperiment, useRemoveTagFromExperiment } from '@/hooks/use-tags';

function TagSelector({ experimentId, currentTags }: Props) {
  const { data: tags, isLoading } = useTags();
  const addTag = useAddTagToExperiment();
  const removeTag = useRemoveTagFromExperiment();

  const handleAddTag = (tagName: string) => {
    addTag.mutate(
      { experimentId, data: { tag_name: tagName } },
      { onSuccess: () => toast.success('Tag adicionada') }
    );
  };

  const handleRemoveTag = (tagName: string) => {
    removeTag.mutate(
      { experimentId, tagName },
      { onSuccess: () => toast.success('Tag removida') }
    );
  };

  return (
    <div>
      {currentTags.map(tag => (
        <Badge key={tag.name} onClick={() => handleRemoveTag(tag.name)}>
          {tag.name} ×
        </Badge>
      ))}
      <Select onValueChange={handleAddTag}>
        {tags?.map(tag => (
          <SelectItem key={tag.id} value={tag.name}>{tag.name}</SelectItem>
        ))}
      </Select>
    </div>
  );
}
```

**Invalidação de cache:**
- `useCreateTag`: invalida `queryKeys.tags()`
- `useAddTagToExperiment`: invalida `queryKeys.experiments()`
- `useRemoveTagFromExperiment`: invalida `queryKeys.experiments()`

---

### 4. Services (`services/`)

**Responsabilidades:**
- Funções de chamada à API
- Serialização/deserialização
- Tratamento de erros HTTP

**Padrão:**
```tsx
// services/api.ts - Cliente base
export class APIError extends Error {
  constructor(
    message: string,
    public status?: number,
    public data?: unknown
  ) {
    super(message);
    this.name = 'APIError';
  }
}

export async function fetchAPI<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`/api${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new APIError(
      errorData?.detail || `HTTP error ${response.status}`,
      response.status,
      errorData
    );
  }

  return response.json();
}
```

```tsx
// services/experiments-api.ts
import { fetchAPI } from './api';
import type { Experiment, ExperimentCreate, PaginatedResponse } from '@/types';

export async function listExperiments(
  params?: PaginationParams
): Promise<PaginatedResponse<Experiment>> {
  const query = new URLSearchParams();
  if (params?.limit) query.set('limit', String(params.limit));
  if (params?.offset) query.set('offset', String(params.offset));

  return fetchAPI(`/experiments?${query}`);
}

export async function getExperiment(id: string): Promise<Experiment> {
  return fetchAPI(`/experiments/${id}`);
}

export async function createExperiment(data: ExperimentCreate): Promise<Experiment> {
  return fetchAPI('/experiments', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function deleteExperiment(id: string): Promise<void> {
  return fetchAPI(`/experiments/${id}`, { method: 'DELETE' });
}
```

---

### 5. Types (`types/`)

**Responsabilidades:**
- Definir interfaces TypeScript
- Manter tipos sincronizados com backend

**Padrão:**
```tsx
// types/experiment.ts
export interface Experiment {
  id: string;
  name: string;
  hypothesis: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface ExperimentCreate {
  name: string;
  hypothesis: string;
  description?: string;
}

export interface ExperimentUpdate {
  name?: string;
  hypothesis?: string;
  description?: string;
}
```

```tsx
// types/index.ts - Types compartilhados
export interface PaginationParams {
  limit?: number;
  offset?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface PaginationMeta {
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: PaginationMeta;
}
```

---

### 6. Lib (`lib/`)

**Responsabilidades:**
- Utilitários compartilhados
- Configurações de libraries

**Query Keys (centralizado):**
```tsx
// lib/query-keys.ts
export const queryKeys = {
  // Experiments
  experimentsList: ['experiments', 'list'] as const,
  experimentDetail: (id: string) => ['experiments', 'detail', id] as const,

  // Synths
  synthsList: ['synths', 'list'] as const,
  synthDetail: (id: string) => ['synths', 'detail', id] as const,

  // Research
  executionsList: ['executions', 'list'] as const,
  executionDetail: (id: string) => ['executions', 'detail', id] as const,
};
```

**Utilidades:**
```tsx
// lib/utils.ts
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

// Combina classes Tailwind de forma segura
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

---

## Páginas Principais

### Index (`pages/Index.tsx`)

**Rota:** `/`

**Descrição:** Página principal (home) que exibe a lista de experimentos em grid. Oferece busca por texto, filtro por tags, e ordenação. Estilo "Research Observatory" com animações suaves de entrada.

**Estrutura:**
- **Header**: SynthLabHeader com botão de navegação para Synths
- **Filtros**: PopularTags (filtros rápidos), ExperimentsFilter (busca + ordenação)
- **Grid**: Cards de experimentos com informações resumidas
- **Modal**: Dialog para criação de novo experimento

**Componentes utilizados:**

| Componente | Diretório | Uso |
|------------|-----------|-----|
| `SynthLabHeader` | `shared/` | Header global com título e ações |
| `PopularTags` | `experiments/` | Filtros rápidos por tags populares |
| `ExperimentsFilter` | `experiments/` | Campo de busca e seletor de ordenação |
| `ExperimentCard` | `experiments/` | Card individual de experimento |
| `EmptyState` | `experiments/` | Estado vazio quando não há experimentos |
| `ExperimentForm` | `experiments/` | Formulário de criação de experimento |
| `Dialog`, `DialogContent`, `DialogHeader`, `DialogTitle` | `ui/` | Modal de criação |
| `Button`, `Skeleton` | `ui/` | Componentes base |

**Hooks utilizados:**

| Hook | Arquivo | Propósito |
|------|---------|-----------|
| `useExperiments` | `use-experiments.ts` | Lista paginada de experimentos com filtros |
| `useCreateExperiment` | `use-experiments.ts` | Mutation para criar experimento (com optimistic update) |
| `useToast` | `use-toast.ts` | Notificações de sucesso/erro |
| `useNavigate` | `react-router-dom` | Navegação para detalhes e Synths |

**Endpoints do Backend:**

| Método | Endpoint | Ação |
|--------|----------|------|
| `GET` | `/experiments/list?search=&tag=&sort_by=&sort_order=` | Listar experimentos com filtros |
| `POST` | `/experiments` | Criar novo experimento |
| `GET` | `/tags` | Listar tags disponíveis (via PopularTags) |

**Fluxo de Dados:**
1. Ao montar, carrega lista de experimentos via `useExperiments(params)`
2. Estado local gerencia: busca (`search`), tag selecionada (`selectedTag`), ordenação (`sortOption`)
3. Parâmetros são convertidos para `ExperimentsListParams` via `useMemo`
4. React Query mantém cache com `placeholderData` para UX suave durante re-fetches
5. Criação usa optimistic update: card aparece imediatamente, rollback em caso de erro
6. Navegação para `/experiments/:id` ao clicar em um card

**Estados da UI:**
- **Loading**: Grid de skeletons (3 cards)
- **Error**: Mensagem de erro em destaque vermelho
- **Empty (sem busca)**: EmptyState com CTA para criar experimento
- **Empty (com busca)**: Mensagem "Nenhum resultado para [termo]"
- **Com dados**: Grid responsivo de ExperimentCards

---

### ExperimentDetail (`pages/ExperimentDetail.tsx`)

**Rota:** `/experiments/:id`

**Descrição:** Página de detalhes de um experimento, estruturada como um "Research Observatory" com cabeçalho read-only e sistema de abas para navegação entre diferentes aspectos do experimento.

**Estrutura:**
- **Header**: Nome, hipótese, descrição (truncada), scorecard sliders (animados), TagSelector
- **Tabs**: Análise | Entrevistas | Explorações | Materiais | Relatórios

**Componentes utilizados:**

| Componente | Diretório | Uso |
|------------|-----------|-----|
| `SynthLabHeader` | `shared/` | Header global com botão de voltar |
| `TagSelector` | `experiments/` | Seletor/editor de tags do experimento |
| `AnalysisPhaseTabs` | `experiments/` | Navegação entre fases da análise |
| `PhaseOverview`, `PhaseLocation`, `PhaseSegmentation`, `PhaseEdgeCases` | `experiments/results/` | Conteúdo de cada fase da análise |
| `ViewSummaryButton` | `experiments/results/` | Botão para visualizar resumo |
| `ExplorationList` | `exploration/` | Lista de explorações do experimento |
| `NewExplorationDialog` | `exploration/` | Modal para criar nova exploração |
| `NewInterviewFromExperimentDialog` | `experiments/` | Modal para criar nova entrevista |
| `MaterialUpload` | `experiments/` | Upload de materiais/arquivos |
| `MaterialGallery` | `experiments/` | Galeria de materiais anexados |
| `DocumentsList` | `experiments/` | Lista de relatórios/documentos gerados |

**Hooks utilizados:**

| Hook | Arquivo | Propósito |
|------|---------|-----------|
| `useExperiment` | `use-experiments.ts` | Dados do experimento |
| `useRunAnalysis` | `use-experiments.ts` | Mutation para executar análise |
| `useDeleteExperiment` | `use-experiments.ts` | Mutation para deletar experimento |
| `useExplorations` | `use-exploration.ts` | Lista de explorações |
| `useMaterials` | `use-materials.ts` | Lista de materiais anexados |
| `useDocuments` | `use-documents.ts` | Lista de documentos/relatórios |
| `useTags` | `use-tags.ts` | Lista de tags disponíveis |
| `useAddTagToExperiment` | `use-tags.ts` | Adicionar tag ao experimento |
| `useRemoveTagFromExperiment` | `use-tags.ts` | Remover tag do experimento |

**Endpoints do Backend:**

| Método | Endpoint | Ação |
|--------|----------|------|
| `GET` | `/experiments/{id}` | Buscar detalhes do experimento |
| `POST` | `/experiments/{id}/run-analysis` | Executar análise |
| `DELETE` | `/experiments/{id}` | Deletar experimento |
| `GET` | `/experiments/{id}/explorations` | Listar explorações |
| `GET` | `/experiments/{id}/materials` | Listar materiais |
| `POST` | `/experiments/{id}/materials` | Upload de material |
| `GET` | `/experiments/{id}/documents` | Listar documentos |
| `GET` | `/tags` | Listar tags disponíveis |
| `POST` | `/experiments/{id}/tags` | Adicionar tag ao experimento |
| `DELETE` | `/experiments/{id}/tags/{tag_name}` | Remover tag do experimento |

**Fluxo de Dados:**
1. Ao montar, carrega dados do experimento via `useExperiment(id)`
2. Tab ativa é sincronizada com query param `?tab=`
3. Cada tab carrega dados específicos via hooks dedicados
4. Mutations invalidam cache apropriado após sucesso

---

## Mecanismos Transversais

### 1. Roteamento (React Router)

**Todas as rotas em `App.tsx`:**

| Path | Componente | Descrição |
|------|------------|-----------|
| `/` | `Index` | Lista de experimentos (home) com busca, filtro por tags e ordenação |
| `/experiments/:id` | `ExperimentDetail` | Detalhes de um experimento com abas: Análise, Entrevistas, Explorações, Materiais, Relatórios |
| `/experiments/:id/simulations/:simId` | `SimulationDetail` | Detalhes de uma simulação |
| `/experiments/:id/explorations/:explorationId` | `ExplorationDetail` | Detalhes de uma exploração |
| `/experiments/:expId/interviews/:execId` | `InterviewDetail` | Detalhes de entrevista (rota nova) |
| `/interviews/:execId` | `InterviewDetail` | Detalhes de entrevista (rota legada) |
| `/synths` | `Synths` | Catálogo de synths |
| `*` | `NotFound` | Página 404 |

```tsx
// App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Index />} />
        <Route path="/experiments/:id" element={<ExperimentDetail />} />
        <Route path="/experiments/:id/simulations/:simId" element={<SimulationDetail />} />
        <Route path="/experiments/:id/explorations/:explorationId" element={<ExplorationDetail />} />
        <Route path="/experiments/:expId/interviews/:execId" element={<InterviewDetail />} />
        <Route path="/interviews/:execId" element={<InterviewDetail />} />
        <Route path="/synths" element={<Synths />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}
```

---

### 2. Estado do Servidor (React Query)

**Configuração em `main.tsx`:**
```tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,  // 5 minutos
      retry: 1,
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <QueryClientProvider client={queryClient}>
    <App />
  </QueryClientProvider>
);
```

---

### 3. Notificações (Sonner/Toast)

**Configuração:** O `Toaster` está configurado globalmente em `App.tsx`:
- Posição: `top-right`
- Auto-dismiss: 5 segundos
- Botão de fechar: habilitado
- Cores semânticas: habilitadas

**Tipos de toast e cores:**

| Tipo | Uso | Background | Border |
|------|-----|------------|--------|
| `toast.success()` | Operações bem-sucedidas | `green-50` | `green-200` |
| `toast.error()` | Erros de API/validação | `red-50` | `red-200` |
| `toast.warning()` | Avisos não-críticos | `amber-50` | `amber-200` |
| `toast.info()` | Informações neutras | `indigo-50` | `indigo-200` |

**Padrão para mutations:**
```tsx
import { toast } from 'sonner';

const mutation = useCreateExperiment();

const handleCreate = (data: FormData) => {
  mutation.mutate(data, {
    onSuccess: () => toast.success('Experimento criado com sucesso'),
    onError: (error) => toast.error(error.message),  // Mensagem vem da API
  });
};
```

**Toast com descrição:**
```tsx
toast.error('Não foi possível executar', {
  description: 'Verifique se todos os campos estão preenchidos.',
});
```

**Toast com ação:**
```tsx
toast.error('Análise falhou', {
  action: {
    label: 'Tentar novamente',
    onClick: () => handleRetry(),
  },
});
```

**IMPORTANTE:**
- Sempre mostrar toast em erros de mutation
- Mensagens de erro vêm do backend (campo `detail` do FastAPI)
- Evitar toasts duplicados (React Query gerencia isso)
- Manter mensagens concisas (máximo 2 linhas)

---

### 4. Formulários (React Hook Form + Zod)

**Padrão:**
```tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const schema = z.object({
  name: z.string().min(1, 'Required').max(100, 'Too long'),
  hypothesis: z.string().min(1, 'Required').max(500, 'Too long'),
});

type FormData = z.infer<typeof schema>;

export function NewExperimentForm({ onSubmit }: Props) {
  const form = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { name: '', hypothesis: '' },
  });

  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      <Input {...form.register('name')} />
      {form.formState.errors.name && (
        <span>{form.formState.errors.name.message}</span>
      )}
      {/* ... */}
    </form>
  );
}
```

---

## Checklist de Code Review

### Para novas páginas:
- [ ] Página em `pages/`?
- [ ] Rota adicionada em `App.tsx`?
- [ ] Usa hooks para dados (não fetch direto)?

### Para novos componentes:
- [ ] Componente é puro (props → JSX)?
- [ ] Não faz fetch direto?
- [ ] Organizado no diretório correto (`shared/`, `experiments/`, etc)?
- [ ] Não edita componentes de `ui/` (shadcn)?

### Para novos hooks:
- [ ] Usa React Query para dados do servidor?
- [ ] Query keys em `lib/query-keys.ts`?
- [ ] Invalida cache após mutations?

### Para novas APIs:
- [ ] Função em `services/*-api.ts`?
- [ ] Usa `fetchAPI` base?
- [ ] Types correspondentes em `types/`?

### Para mutations:
- [ ] Toast de sucesso em `onSuccess`?
- [ ] Toast de erro em `onError` com `error.message`?
- [ ] Mensagens em português?

### Geral:
- [ ] TypeScript sem `any`?
- [ ] Tailwind CSS para estilos?
- [ ] Componentes shadcn/ui quando possível?

---

## Exemplos de Violações Comuns

### 1. Fetch Direto em Componente (ERRADO)
```tsx
// ❌ ERRADO
export function ExperimentList() {
  const [experiments, setExperiments] = useState([]);

  useEffect(() => {
    fetch('/api/experiments')
      .then(r => r.json())
      .then(setExperiments);
  }, []);

  return <div>{experiments.map(...)}</div>;
}
```

**CORRETO:**
```tsx
// hooks/use-experiments.ts
export function useExperiments() {
  return useQuery({
    queryKey: queryKeys.experimentsList,
    queryFn: () => listExperiments(),
  });
}

// components/experiments/ExperimentList.tsx
export function ExperimentList() {
  const { data, isLoading } = useExperiments();  // ✅

  if (isLoading) return <Loading />;
  return <div>{data?.data.map(...)}</div>;
}
```

### 2. Lógica de Negócio em Componente (ERRADO)
```tsx
// ❌ ERRADO
export function CreateExperimentForm() {
  const handleSubmit = async (data) => {
    // Validação de negócio no frontend
    if (data.name.includes('admin')) {
      toast.error('Reserved name');
      return;
    }

    await fetch('/api/experiments', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  };
}
```

**CORRETO:**
```tsx
// Validação está no backend (service)
// Frontend só faz validação de formato (Zod schema)
export function CreateExperimentForm() {
  const mutation = useCreateExperiment();

  const handleSubmit = async (data: FormData) => {
    try {
      await mutation.mutateAsync(data);
      toast.success('Created');
    } catch (error) {
      // Backend retorna erro se nome for reservado
      toast.error(error.message);
    }
  };
}
```

### 3. Query Keys Inline (ERRADO)
```tsx
// ❌ ERRADO - Keys inline
export function useExperiments() {
  return useQuery({
    queryKey: ['experiments', 'list'],  // ❌ Duplicação
    queryFn: () => listExperiments(),
  });
}

export function useDeleteExperiment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteExperiment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['experiments', 'list'] });  // ❌
    },
  });
}
```

**CORRETO:**
```tsx
// lib/query-keys.ts
export const queryKeys = {
  experimentsList: ['experiments', 'list'] as const,
};

// hooks/use-experiments.ts
export function useExperiments() {
  return useQuery({
    queryKey: queryKeys.experimentsList,  // ✅ Centralizado
    queryFn: () => listExperiments(),
  });
}
```

---

## Referências

- **React**: https://react.dev/
- **TypeScript**: https://www.typescriptlang.org/docs/
- **React Router**: https://reactrouter.com/
- **TanStack Query**: https://tanstack.com/query/latest
- **shadcn/ui**: https://ui.shadcn.com/
- **Tailwind CSS**: https://tailwindcss.com/docs
- **React Hook Form**: https://react-hook-form.com/
- **Zod**: https://zod.dev/
