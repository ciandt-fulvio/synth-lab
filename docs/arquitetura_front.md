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

## Mecanismos Transversais

### 1. Roteamento (React Router)

**Todas as rotas em `App.tsx`:**
```tsx
// App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Index />} />
        <Route path="/synths" element={<Synths />} />
        <Route path="/experiments" element={<Experiments />} />
        <Route path="/experiments/:id" element={<ExperimentDetail />} />
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

**Padrão:**
```tsx
import { toast } from 'sonner';

// Em hooks ou componentes
const mutation = useCreateExperiment();

const handleCreate = async (data) => {
  try {
    await mutation.mutateAsync(data);
    toast.success('Experiment created');
  } catch (error) {
    toast.error('Failed to create experiment');
  }
};
```

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
