# Chrome DevTools Navigation

**IMPORTANTE**: Ao usar Chrome DevTools MCP para navegar/testar a UI:
1. **PRIMEIRO** consulte `.claude/ui-memory.md` para conhecer os elementos
2. Use seletores semânticos (texto/label), não UIDs
3. Faça apenas 1 snapshot por página para pegar UIDs atuais
4. Atualize `ui-memory.md` se a UI mudar

---

# Tech Stack

- You are building a React application.
- Use TypeScript.
- Use React Router. KEEP the routes in src/App.tsx
- Always put source code in the src folder.
- Put pages into src/pages/
- Put components into src/components/
- The main page (default page) is src/pages/Index.tsx
- UPDATE the main page to include the new components. OTHERWISE, the user can NOT see any components!
- ALWAYS try to use the shadcn/ui library.
- Tailwind CSS: always use Tailwind CSS for styling components. Utilize Tailwind classes extensively for layout, spacing, colors, and other design aspects.

Available packages and libraries:

- The lucide-react package is installed for icons.
- You ALREADY have ALL the shadcn/ui components and their dependencies installed. So you don't need to install them again.
- You have ALL the necessary Radix UI components installed.
- Use prebuilt components from the shadcn/ui library after importing them. Note that these files shouldn't be edited, so make new components if you need to change them.

---

# SynthLab Design System

**IMPORTANT**: When creating new pages or components, use these standardized patterns defined in `globals.css`.

## Color Palette

- **Primary**: `indigo-600` / `violet-600` (gradient for CTAs)
- **Neutral**: `slate-*` for text, borders, backgrounds
- **Semantic**: `green` (success), `red` (error), `amber` (warning), `blue` (info)
- **NEVER use**: `purple-*` standalone (use `indigo-*` instead for brand consistency)

## Button System

Use these CSS classes instead of inline Tailwind styles:

| Class | Usage | Example |
|-------|-------|---------|
| `.btn-primary` | Main CTAs (Salvar, Criar, Executar) | `<Button className="btn-primary">` |
| `.btn-secondary` | Cancel/Back actions | `<Button variant="outline" className="btn-secondary">` |
| `.btn-ghost` | Discrete actions with text | `<Button variant="ghost" className="btn-ghost">` |
| `.btn-ghost-icon` | Icon-only navigation buttons | `<Button variant="ghost" size="icon" className="btn-ghost-icon">` |

## Card System

| Class | Usage |
|-------|-------|
| `.card` | Standard container |
| `.card-hover` | Card with hover effect |
| `.card-dashed` | Empty/placeholder states |

## Icon Boxes

| Class | Usage |
|-------|-------|
| `.icon-box-primary` | Gradient icon container (page headers) |
| `.icon-box-neutral` | Gray icon container |
| `.icon-box-light` | Light indigo icon container |

## Badges

| Class | Usage |
|-------|-------|
| `.badge-primary` | Primary/brand badges |
| `.badge-success` | Success status |
| `.badge-error` | Error status |
| `.badge-warning` | Warning status |
| `.badge-info` | Info status |
| `.badge-neutral` | Neutral/default |

## Typography

| Class | Usage |
|-------|-------|
| `.text-page-title` | Page titles (2xl bold) |
| `.text-section-title` | Section headings (lg semibold) |
| `.text-card-title` | Card titles (base medium) |
| `.text-body` | Body text (sm slate-600) |
| `.text-meta` | Meta/helper text (xs slate-500) |

## Shared Components

### SynthLabHeader

Use for all page headers:

```tsx
import { SynthLabHeader } from '@/components/shared/SynthLabHeader';

// Home page (no back button)
<SynthLabHeader actions={<Button>Action</Button>} />

// Subpage with back navigation
<SynthLabHeader subtitle="Page Title" backTo="/" />

// With actions
<SynthLabHeader
  subtitle="Page Title"
  backTo="/"
  actions={<Button className="btn-primary">Action</Button>}
/>
```

## Page Structure Template

```tsx
export default function NewPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
      <SynthLabHeader subtitle="Page Title" backTo="/" />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page content */}
        <div className="card p-6">
          <h2 className="text-section-title">Section</h2>
          <p className="text-body">Content</p>
        </div>
      </main>
    </div>
  );
}
```

## Spacing Guidelines

- **Container padding**: `px-4 sm:px-6 lg:px-8`
- **Card padding**: `p-5` (20px) or `p-6` (24px)
- **Section gaps**: `gap-4` (16px) or `gap-6` (24px)
- **Bottom margins**: `mb-4`, `mb-6`, `mb-8`

## Icon Sizes

| Context | Size |
|---------|------|
| Page header icons | `h-6 w-6` |
| Section header icons | `h-5 w-5` |
| Badge/inline icons | `h-4 w-4` |
| Small inline icons | `h-3.5 w-3.5` |

## Loading States

- Spinner: `<Loader2 className="spinner h-5 w-5" />`
- Skeleton: `<Skeleton className="skeleton-pulse h-6 w-full" />`

## Gradients

| Class | Usage |
|-------|-------|
| `.gradient-primary` | Primary gradient (indigo→violet) |
| `.gradient-light` | Light background gradient |
| `.gradient-decorative` | Logo/decorative elements |
| `.logo-glow` | Logo glow effect |

---

## Toast Notifications (Sonner)

**IMPORTANT**: Use Sonner for all user feedback notifications.

### Configuration

The Toaster component is configured globally in `App.tsx`:
- Position: `top-right`
- Auto-dismiss: 5 seconds
- Close button: enabled
- Rich colors: enabled (semantic styling)

### Usage

```tsx
import { toast } from 'sonner';

// Success - Use after successful operations
toast.success('Operação realizada com sucesso');

// Error - Use for API errors and validation failures
toast.error('Erro ao executar operação');

// Warning - Use for non-critical issues
toast.warning('Atenção: verifique os dados');

// Info - Use for neutral information
toast.info('Processando sua solicitação...');

// With description
toast.error('Falha ao executar análise', {
  description: 'Gere personas sintéticas antes de continuar.',
});

// With action button
toast.error('Análise falhou', {
  action: {
    label: 'Tentar novamente',
    onClick: () => handleRetry(),
  },
});
```

### Color Mapping (Design System)

| Toast Type | Background | Text | Border |
|------------|------------|------|--------|
| `success` | `green-50` | `green-900` | `green-200` |
| `error` | `red-50` | `red-900` | `red-200` |
| `warning` | `amber-50` | `amber-900` | `amber-200` |
| `info` | `indigo-50` | `indigo-900` | `indigo-200` |

### Best Practices

1. **Always show toast on mutation errors**:
```tsx
const mutation = useSomeMutation();

const handleAction = () => {
  mutation.mutate(data, {
    onSuccess: () => toast.success('Salvo com sucesso'),
    onError: (error) => toast.error(error.message),
  });
};
```

2. **Use descriptions for actionable errors**:
```tsx
toast.error('Não foi possível executar', {
  description: 'Verifique se todos os campos estão preenchidos.',
});
```

3. **Avoid duplicate toasts** - React Query handles this automatically

4. **Keep messages concise** - Max 2 lines (title + description)
