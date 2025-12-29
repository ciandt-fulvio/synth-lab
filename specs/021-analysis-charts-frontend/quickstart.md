# Quickstart: Analysis Charts Frontend

**Feature**: 021-analysis-charts-frontend
**Date**: 2025-12-28

## Visão Geral

Este guia mostra como implementar novos componentes de gráfico seguindo os padrões estabelecidos no projeto.

---

## 1. Estrutura de Arquivos

Para adicionar um novo gráfico (ex: SHAP Summary), crie:

```
frontend/src/
├── components/experiments/results/
│   ├── ShapSummarySection.tsx     # Section wrapper com explicação
│   └── charts/
│       └── ShapSummaryChart.tsx   # Componente do gráfico
├── hooks/
│   └── use-explainability.ts      # Hooks React Query (adicionar)
```

---

## 2. Implementar Hook

Adicione o hook em `use-explainability.ts`:

```typescript
// frontend/src/hooks/use-explainability.ts
import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import { getShapSummary } from '@/services/simulation-api';

export function useShapSummary(simulationId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.simulation.shapSummary(simulationId),
    queryFn: () => getShapSummary(simulationId),
    enabled: !!simulationId && enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
```

---

## 3. Implementar Chart Component

```typescript
// frontend/src/components/experiments/results/charts/ShapSummaryChart.tsx
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import type { ShapSummary } from '@/types/simulation';

interface ShapSummaryChartProps {
  data: ShapSummary;
}

const COLORS = {
  positive: '#22c55e',  // green-500
  negative: '#ef4444',  // red-500
  mixed: '#f59e0b',     // amber-500
};

export function ShapSummaryChart({ data }: ShapSummaryChartProps) {
  const chartData = data.feature_importance.map((fi) => ({
    feature: fi.feature,
    importance: fi.mean_abs_shap,
    direction: fi.direction,
  }));

  return (
    <ResponsiveContainer width="100%" height={350}>
      <BarChart
        data={chartData}
        layout="vertical"
        margin={{ top: 10, right: 30, left: 100, bottom: 10 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis type="number" stroke="#64748b" fontSize={12} />
        <YAxis
          type="category"
          dataKey="feature"
          stroke="#64748b"
          fontSize={12}
          width={90}
        />
        <Tooltip
          content={({ active, payload }) => {
            if (!active || !payload?.[0]) return null;
            const d = payload[0].payload;
            return (
              <div className="bg-white rounded-lg shadow-lg border border-slate-200 p-3 text-sm">
                <p className="font-medium">{d.feature}</p>
                <p>Importância: {d.importance.toFixed(3)}</p>
                <p>Direção: {d.direction}</p>
              </div>
            );
          }}
        />
        <Bar dataKey="importance" radius={[0, 4, 4, 0]}>
          {chartData.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={COLORS[entry.direction as keyof typeof COLORS]}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
```

---

## 4. Implementar Section Component

```typescript
// frontend/src/components/experiments/results/ShapSummarySection.tsx
import { useState } from 'react';
import { HelpCircle, BarChart3 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { ChartErrorBoundary } from '@/components/shared/ErrorBoundary';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { ShapSummaryChart } from './charts/ShapSummaryChart';
import { useShapSummary } from '@/hooks/use-explainability';

interface ShapSummarySectionProps {
  simulationId: string;
}

export function ShapSummarySection({ simulationId }: ShapSummarySectionProps) {
  const [showExplanation, setShowExplanation] = useState(false);
  const shapSummary = useShapSummary(simulationId);

  return (
    <Card className="card">
      <CardHeader className="pb-2">
        <CardTitle className="text-card-title flex items-center gap-2">
          <BarChart3 className="h-4 w-4 text-slate-500" />
          Importância de Features (SHAP)
        </CardTitle>
        <p className="text-meta">
          Quanto cada atributo contribui para o sucesso ou falha
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Explanation section - collapsible */}
        <Collapsible open={showExplanation} onOpenChange={setShowExplanation}>
          <div className="bg-gradient-to-r from-slate-50 to-indigo-50 border border-slate-200 rounded-lg p-3">
            <CollapsibleTrigger asChild>
              <Button
                variant="ghost"
                className="w-full flex items-center justify-between p-0 h-auto hover:bg-transparent"
              >
                <div className="flex items-center gap-2 text-indigo-700">
                  <HelpCircle className="h-4 w-4" />
                  <span className="text-sm font-medium">
                    Como interpretar este gráfico?
                  </span>
                </div>
                <span className="text-xs text-indigo-600">
                  {showExplanation ? 'Ocultar' : 'Ver explicação'}
                </span>
              </Button>
            </CollapsibleTrigger>

            <CollapsibleContent className="mt-3 space-y-3 text-sm text-slate-700">
              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">
                  O que é SHAP?
                </h4>
                <p className="text-xs">
                  SHAP (SHapley Additive exPlanations) mede quanto cada
                  atributo contribui para a predição de sucesso ou falha.
                </p>
              </div>
              <div>
                <h4 className="font-semibold text-slate-800 mb-1 text-sm">
                  Como ler o gráfico?
                </h4>
                <ul className="mt-1 ml-4 list-disc space-y-0.5 text-xs">
                  <li>
                    <strong>Barras maiores</strong>: Atributos mais importantes
                  </li>
                  <li>
                    <strong className="text-green-600">Verde</strong>: Aumenta
                    a chance de sucesso
                  </li>
                  <li>
                    <strong className="text-red-600">Vermelho</strong>: Diminui
                    a chance de sucesso
                  </li>
                  <li>
                    <strong className="text-amber-600">Amarelo</strong>: Efeito
                    misto (depende do valor)
                  </li>
                </ul>
              </div>
            </CollapsibleContent>
          </div>
        </Collapsible>

        {/* Chart area with loading/error/empty states */}
        {shapSummary.isLoading && (
          <div
            className="flex flex-col items-center justify-center gap-4"
            style={{ height: 350 }}
          >
            <Skeleton className="w-full h-full rounded-lg" />
          </div>
        )}

        {shapSummary.isError && !shapSummary.isLoading && (
          <div
            className="flex flex-col items-center justify-center gap-4 text-center"
            style={{ height: 350 }}
          >
            <div className="icon-box-neutral">
              <AlertCircle className="h-6 w-6 text-red-500" />
            </div>
            <div>
              <p className="text-body text-red-600 font-medium mb-1">Erro</p>
              <p className="text-meta">
                Erro ao carregar os dados. Tente novamente.
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => shapSummary.refetch()}
              className="btn-secondary"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Tentar Novamente
            </Button>
          </div>
        )}

        {!shapSummary.data &&
          !shapSummary.isLoading &&
          !shapSummary.isError && (
            <div
              className="flex flex-col items-center justify-center gap-4 text-center"
              style={{ height: 350 }}
            >
              <div className="icon-box-neutral">
                <BarChart3 className="h-6 w-6 text-slate-400" />
              </div>
              <div>
                <p className="text-body text-slate-500 font-medium mb-1">
                  Sem Dados
                </p>
                <p className="text-meta">
                  Nenhum dado disponível para este gráfico.
                </p>
              </div>
            </div>
          )}

        {!shapSummary.isLoading &&
          !shapSummary.isError &&
          shapSummary.data && (
            <div style={{ minHeight: 350 }}>
              <ChartErrorBoundary chartName="SHAP Summary">
                <ShapSummaryChart data={shapSummary.data} />
              </ChartErrorBoundary>
            </div>
          )}
      </CardContent>
    </Card>
  );
}
```

---

## 5. Integrar na Phase

Adicione o section component na phase correspondente:

```typescript
// frontend/src/components/experiments/results/PhaseExplainability.tsx
import { ShapSummarySection } from './ShapSummarySection';
import { ShapWaterfallSection } from './ShapWaterfallSection';
import { PDPSection } from './PDPSection';

interface PhaseExplainabilityProps {
  simulationId: string;
}

export function PhaseExplainability({ simulationId }: PhaseExplainabilityProps) {
  return (
    <div className="space-y-6">
      <ShapSummarySection simulationId={simulationId} />
      <ShapWaterfallSection simulationId={simulationId} />
      <PDPSection simulationId={simulationId} />
    </div>
  );
}
```

---

## 6. Executar e Testar

```bash
# Start frontend dev server
cd frontend
npm run dev

# Navigate to experiment with analysis
# http://localhost:5173/experiments/{id}
# Select "Aprofundamento" tab
```

---

## Checklist de Implementação

- [ ] Hook criado em `hooks/use-*.ts`
- [ ] Query key existe em `lib/query-keys.ts`
- [ ] API function existe em `services/simulation-api.ts`
- [ ] Types existem em `types/simulation.ts`
- [ ] Chart component criado em `components/.../charts/`
- [ ] Section component criado com:
  - [ ] Card wrapper
  - [ ] Collapsible explanation
  - [ ] Loading state
  - [ ] Error state com retry
  - [ ] Empty state
  - [ ] ChartErrorBoundary
- [ ] Section integrado na Phase correspondente
- [ ] Exportado em `components/.../results/index.ts`

---

## Recursos

- [Recharts Documentation](https://recharts.org/)
- [TanStack Query](https://tanstack.com/query)
- [shadcn/ui](https://ui.shadcn.com/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Design System](../../frontend/CLAUDE.md)
