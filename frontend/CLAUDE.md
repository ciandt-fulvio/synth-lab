# Frontend Guidelines

## Tech Stack

- **Framework**: React 18 + TypeScript 5.5 + Vite
- **UI**: shadcn/ui (Radix) + Tailwind CSS
- **Data**: TanStack Query + React Router DOM
- **Icons**: lucide-react

## Project Structure

```
src/
├── pages/           # Route pages (Index, ExperimentDetail, etc.)
├── components/
│   ├── ui/          # shadcn/ui primitives (DO NOT EDIT)
│   ├── shared/      # Reusable components (StatusBadge, SynthLabHeader, etc.)
│   ├── experiments/ # Experiment-specific components
│   ├── exploration/ # Exploration tree components
│   ├── interviews/  # Interview/research components
│   ├── synths/      # Synth management components
│   └── chat/        # Chat components
├── hooks/           # Custom React hooks (use-*.ts)
├── services/        # API clients (*-api.ts)
├── types/           # TypeScript types (by domain)
└── lib/             # Utilities (query-keys.ts, utils.ts, schemas.ts)
```

## Architecture Rules

| Layer | Responsibility | Reference |
|-------|---------------|-----------|
| **Pages** | Compose components + use hooks | `pages/ExperimentDetail.tsx` |
| **Components** | Pure (props → JSX), NO fetch | `components/experiments/` |
| **Hooks** | React Query (useQuery, useMutation) | `hooks/use-experiments.ts` |
| **Services** | API calls using `fetchAPI` | `services/experiments-api.ts` |
| **Query Keys** | Centralized cache keys | `lib/query-keys.ts` |

---

## Design System

Defined in `globals.css`. Use CSS classes, not inline Tailwind for common patterns.

### Colors

- **Primary**: `indigo-600` / `violet-600` (gradients)
- **Neutral**: `slate-*`
- **Semantic**: `green` (success), `red` (error), `amber` (warning), `blue` (info)
- **NEVER**: `purple-*` standalone

### CSS Classes

| Category | Classes | Reference |
|----------|---------|-----------|
| **Buttons** | `.btn-primary`, `.btn-secondary`, `.btn-ghost`, `.btn-ghost-icon` | `globals.css:287` |
| **Cards** | `.card`, `.card-hover`, `.card-dashed` | `globals.css:322` |
| **Icon Boxes** | `.icon-box-primary`, `.icon-box-neutral`, `.icon-box-light` | `globals.css:342` |
| **Badges** | `.badge-success`, `.badge-error`, `.badge-warning`, `.badge-info`, `.badge-neutral` | `globals.css:362` |
| **Typography** | `.text-page-title`, `.text-section-title`, `.text-card-title`, `.text-body`, `.text-meta` | `globals.css:391` |
| **Gradients** | `.gradient-primary`, `.gradient-light`, `.gradient-decorative` | `globals.css:450` |

### Icon Sizes

| Context | Size |
|---------|------|
| Page header | `h-6 w-6` |
| Section header | `h-5 w-5` |
| Badge/inline | `h-4 w-4` or `h-3.5 w-3.5` |

---

## Shared Components

### SynthLabHeader

Page header with optional back navigation and actions.

```tsx
import { SynthLabHeader } from '@/components/shared/SynthLabHeader';
```

Reference: `components/shared/SynthLabHeader.tsx`

### StatusBadge

**Use for ALL status indicators.** DO NOT create new badge components.

```tsx
import { StatusBadge, EXECUTION_STATUS_CONFIG, EXPLORATION_STATUS_CONFIG } from '@/components/shared/StatusBadge';

<StatusBadge status={execution.status} config={EXECUTION_STATUS_CONFIG} />
```

Available configs:
- `EXECUTION_STATUS_CONFIG` - Interviews (pending, running, generating_summary, completed, failed)
- `EXPLORATION_STATUS_CONFIG` - Explorations (running, goal_achieved, depth_limit_reached, etc.)
- `NODE_STATUS_CONFIG` - Scenario nodes (active, dominated, winner, expansion_failed)

Reference: `components/shared/StatusBadge.tsx`

### Other Shared Components

| Component | Purpose | File |
|-----------|---------|------|
| `ChartContainer` | Wrapper for charts with loading/error states | `shared/ChartContainer.tsx` |
| `ErrorBoundary` | React error boundary | `shared/ErrorBoundary.tsx` |
| `TranscriptDialog` | Interview transcript viewer | `shared/TranscriptDialog.tsx` |
| `MarkdownPopup` | Markdown content popup | `shared/MarkdownPopup.tsx` |
| `ArtifactButton` | Toggle button for artifacts | `shared/ArtifactButton.tsx` |

---

## Data Fetching Pattern

### Hook Structure

```tsx
// hooks/use-something.ts
import { useQuery, useMutation } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import { getSomething, createSomething } from '@/services/something-api';

export function useSomething(id: string) {
  return useQuery({
    queryKey: queryKeys.somethingDetail(id),
    queryFn: () => getSomething(id),
  });
}
```

Reference: `hooks/use-experiments.ts`, `hooks/use-exploration.ts`

### Service Structure

```tsx
// services/something-api.ts
import { fetchAPI } from './api';

export async function getSomething(id: string): Promise<Something> {
  return fetchAPI(`/something/${id}`);
}
```

Reference: `services/api.ts` (base), `services/experiments-api.ts`

---

## Toast Notifications

Use Sonner for all user feedback.

```tsx
import { toast } from 'sonner';

toast.success('Salvo com sucesso');
toast.error('Erro ao salvar', { description: 'Detalhes do erro' });
```

Configuration: `App.tsx` (Toaster component)

---

## Page Template

```tsx
export default function NewPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
      <SynthLabHeader subtitle="Page Title" backTo="/" />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Content */}
      </main>
    </div>
  );
}
```

Reference: `pages/ExperimentDetail.tsx`

---

## Chrome DevTools Navigation

When using Chrome DevTools MCP:
1. Consult `.claude/ui-memory.md` first
2. Use semantic selectors (text/label), not UIDs
3. One snapshot per page for current UIDs
4. Update `ui-memory.md` if UI changes
