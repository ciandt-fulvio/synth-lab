# Frontend Contracts: AI-Generated Insights

**Feature**: 023-quantitative-ai-insights
**Date**: 2025-12-29

## Overview

Frontend component and hook contracts for displaying AI-generated insights in the quantitative results UI.

## Component Hierarchy

```
ExperimentResultsPage
├─ ResultsHeader
│  └─ ViewSummaryButton (NEW)
│     └─ ExecutiveSummaryModal (NEW)
├─ PhaseOverview (Try vs Success)
│  ├─ TryVsSuccessChart
│  └─ InsightSection (NEW)
├─ PDPSection
│  ├─ PDPChart
│  └─ InsightSection (NEW)
├─ RadarSection (Profile Comparison)
│  ├─ RadarComparisonChart
│  └─ InsightSection (NEW)
├─ PCAScatterSection
│  ├─ PCAScatterChart
│  └─ InsightSection (NEW)
├─ ExtremeCasesSection
│  ├─ ExtremeCasesTable
│  └─ InsightSection (NEW)
└─ OutliersSection
   ├─ OutliersTable
   └─ InsightSection (NEW)
```

---

## Components

### 1. InsightSection

**File**: `frontend/src/components/experiments/results/InsightSection.tsx`

**Purpose**: Reusable collapsible section displaying AI-generated insight for a chart.

**Props**:
```typescript
interface InsightSectionProps {
  experimentId: string
  chartType: ChartTypeWithInsight
  className?: string
}
```

**Behavior**:
- Collapsed by default
- Fetches insight data using `useChartInsight` hook
- Shows loading state while insight is being generated (status="pending")
- Shows error state if generation failed (status="failed")
- Shows completed insight with formatted markdown/sections (status="completed")
- Auto-refreshes every 10 seconds if status="pending"

**UI States**:

**Collapsed** (default):
```tsx
<Collapsible defaultOpen={false}>
  <CollapsibleTrigger className="flex items-center gap-2">
    <Sparkles className="h-4 w-4" />
    <span className="text-sm font-medium">Insights de IA</span>
    <Badge variant="secondary">Novo</Badge>
    <ChevronDown className="h-4 w-4 transition-transform" />
  </CollapsibleTrigger>
  <CollapsibleContent>
    {/* Insight content */}
  </CollapsibleContent>
</Collapsible>
```

**Loading** (status="pending"):
```tsx
<div className="flex items-center gap-2 text-muted-foreground">
  <Loader2 className="h-4 w-4 animate-spin" />
  <span>Gerando insights...</span>
</div>
```

**Error** (status="failed"):
```tsx
<Alert variant="destructive">
  <AlertCircle className="h-4 w-4" />
  <AlertTitle>Insights indisponíveis</AlertTitle>
  <AlertDescription>
    Não foi possível gerar insights para este gráfico. Tente novamente mais tarde.
  </AlertDescription>
</Alert>
```

**Completed** (status="completed"):
```tsx
<div className="space-y-4">
  <section>
    <h4 className="text-sm font-semibold mb-2">Compreensão do Problema</h4>
    <p className="text-sm text-muted-foreground">
      {insight.problemUnderstanding}
    </p>
  </section>

  <section>
    <h4 className="text-sm font-semibold mb-2">Tendências Observadas</h4>
    <p className="text-sm text-muted-foreground">
      {insight.trendsObserved}
    </p>
  </section>

  <section>
    <h4 className="text-sm font-semibold mb-2">Descobertas-Chave</h4>
    <ul className="list-disc list-inside space-y-1">
      {insight.keyFindings.map((finding, i) => (
        <li key={i} className="text-sm text-muted-foreground">
          {finding}
        </li>
      ))}
    </ul>
  </section>

  <section>
    <h4 className="text-sm font-semibold mb-2">Resumo</h4>
    <p className="text-sm text-muted-foreground">
      {insight.summary}
    </p>
  </section>

  <div className="flex items-center gap-2 text-xs text-muted-foreground pt-2 border-t">
    <Bot className="h-3 w-3" />
    <span>Gerado por {insight.model}</span>
    <span>•</span>
    <span>{formatDistanceToNow(new Date(insight.generationTimestamp))} atrás</span>
  </div>
</div>
```

**Example Usage**:
```tsx
// In PhaseOverview.tsx
<Card>
  <CardHeader>
    <CardTitle>Try vs Success</CardTitle>
  </CardHeader>
  <CardContent>
    <TryVsSuccessChart data={chartData} />
    <InsightSection
      experimentId={experimentId}
      chartType="try_vs_success"
    />
  </CardContent>
</Card>
```

---

### 2. ExecutiveSummaryModal

**File**: `frontend/src/components/experiments/results/ExecutiveSummaryModal.tsx`

**Purpose**: Modal/drawer displaying executive summary synthesizing all chart insights.

**Props**:
```typescript
interface ExecutiveSummaryModalProps {
  experimentId: string
  open: boolean
  onOpenChange: (open: boolean) => void
}
```

**Behavior**:
- Fetches summary data using `useExecutiveSummary` hook
- Shows loading state while summary is being generated
- Shows partial summary state if < 3 insights available
- Shows completed summary with organized sections
- Auto-refreshes every 15 seconds if status="pending" or "partial"

**UI Layout** (Sheet component from shadcn):
```tsx
<Sheet open={open} onOpenChange={onOpenChange}>
  <SheetContent side="right" className="w-full sm:max-w-2xl overflow-y-auto">
    <SheetHeader>
      <SheetTitle className="flex items-center gap-2">
        <FileText className="h-5 w-5" />
        Resumo Executivo
      </SheetTitle>
      <SheetDescription>
        Síntese de todos os insights da análise quantitativa
      </SheetDescription>
    </SheetHeader>

    <div className="mt-6 space-y-6">
      {/* Overview Section */}
      <section>
        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <Eye className="h-4 w-4" />
          Visão Geral
        </h3>
        <p className="text-sm text-muted-foreground">
          {summary.overview}
        </p>
      </section>

      {/* Explainability Section */}
      <Separator />
      <section>
        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <Lightbulb className="h-4 w-4" />
          Explicabilidade
        </h3>
        <p className="text-sm text-muted-foreground">
          {summary.explainability}
        </p>
      </section>

      {/* Segmentation Section */}
      <Separator />
      <section>
        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <Users className="h-4 w-4" />
          Segmentação
        </h3>
        <p className="text-sm text-muted-foreground">
          {summary.segmentation}
        </p>
      </section>

      {/* Edge Cases Section */}
      <Separator />
      <section>
        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4" />
          Casos Extremos
        </h3>
        <p className="text-sm text-muted-foreground">
          {summary.edgeCases}
        </p>
      </section>

      {/* Recommendations Section */}
      <Separator />
      <section>
        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <Target className="h-4 w-4" />
          Recomendações
        </h3>
        <ul className="space-y-3">
          {summary.recommendations.map((rec, i) => (
            <li key={i} className="flex gap-3">
              <div className="mt-1 flex-shrink-0 w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center">
                <span className="text-xs font-semibold text-primary">
                  {i + 1}
                </span>
              </div>
              <p className="text-sm text-muted-foreground">
                {rec}
              </p>
            </li>
          ))}
        </ul>
      </section>

      {/* Metadata Footer */}
      <Separator />
      <div className="flex flex-col gap-2 text-xs text-muted-foreground">
        <div className="flex items-center gap-2">
          <Bot className="h-3 w-3" />
          <span>Gerado por {summary.model}</span>
        </div>
        <div>
          Baseado em {summary.includedChartTypes.length} gráfico(s): {
            summary.includedChartTypes.join(", ")
          }
        </div>
        <div>
          {formatDistanceToNow(new Date(summary.generationTimestamp))} atrás
        </div>
      </div>
    </div>
  </SheetContent>
</Sheet>
```

**Loading State**:
```tsx
<div className="flex flex-col items-center justify-center h-64 gap-4">
  <Loader2 className="h-8 w-8 animate-spin text-primary" />
  <p className="text-sm text-muted-foreground">
    Gerando resumo executivo...
  </p>
  <p className="text-xs text-muted-foreground">
    Isso pode levar até 30 segundos
  </p>
</div>
```

**Partial State** (< 3 insights available):
```tsx
<Alert variant="warning">
  <AlertCircle className="h-4 w-4" />
  <AlertTitle>Resumo Parcial</AlertTitle>
  <AlertDescription>
    Baseado em {summary.includedChartTypes.length} de 7 gráficos.
    Aguardando geração de insights adicionais para análise completa.
  </AlertDescription>
</Alert>
```

---

### 3. ViewSummaryButton

**File**: `frontend/src/components/experiments/results/ViewSummaryButton.tsx`

**Purpose**: Button in results header to open executive summary modal.

**Props**:
```typescript
interface ViewSummaryButtonProps {
  experimentId: string
}
```

**Behavior**:
- Shows badge with "Novo" label to draw attention
- Opens ExecutiveSummaryModal when clicked
- Shows loading indicator if summary is pending
- Disabled if no insights are available yet

**UI**:
```tsx
<Button
  variant="outline"
  className="gap-2"
  onClick={() => setModalOpen(true)}
  disabled={!hasSummary}
>
  <FileText className="h-4 w-4" />
  Ver Resumo Executivo
  {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
  {!isLoading && <Badge variant="secondary">Novo</Badge>}
</Button>

<ExecutiveSummaryModal
  experimentId={experimentId}
  open={modalOpen}
  onOpenChange={setModalOpen}
/>
```

**Example Integration** (in ExperimentResultsPage header):
```tsx
<div className="flex items-center justify-between">
  <h1 className="text-2xl font-bold">Resultados da Análise</h1>
  <div className="flex items-center gap-2">
    <ViewSummaryButton experimentId={experimentId} />
    <Button variant="outline">Exportar Relatório</Button>
  </div>
</div>
```

---

## Hooks

### 1. useChartInsight

**File**: `frontend/src/hooks/use-chart-insight.ts`

**Purpose**: React Query hook for fetching chart insight data.

**Signature**:
```typescript
function useChartInsight(
  experimentId: string,
  chartType: ChartTypeWithInsight
): {
  insight: ChartInsight | undefined
  isLoading: boolean
  isError: boolean
  error: Error | null
  refetch: () => void
}
```

**Implementation**:
```typescript
import { useQuery } from "@tanstack/react-query"
import { getChartInsight } from "@/services/insights-api"
import { insightKeys } from "@/lib/query-keys"

export function useChartInsight(
  experimentId: string,
  chartType: ChartTypeWithInsight
) {
  return useQuery({
    queryKey: insightKeys.chart(experimentId, chartType),
    queryFn: () => getChartInsight(experimentId, chartType),
    staleTime: 5 * 60 * 1000, // 5 minutes (insights are immutable once completed)
    refetchInterval: (data) => {
      // Auto-refresh every 10s if pending
      return data?.status === "pending" ? 10000 : false
    },
    retry: 2,
  })
}
```

**Usage Example**:
```tsx
function InsightSection({ experimentId, chartType }) {
  const { insight, isLoading, isError } = useChartInsight(
    experimentId,
    chartType
  )

  if (isLoading) return <LoadingState />
  if (isError) return <ErrorState />
  if (insight?.status === "failed") return <FailedState />
  if (insight?.status === "completed") return <InsightContent insight={insight} />

  return null
}
```

---

### 2. useExecutiveSummary

**File**: `frontend/src/hooks/use-executive-summary.ts`

**Purpose**: React Query hook for fetching executive summary data.

**Signature**:
```typescript
function useExecutiveSummary(
  experimentId: string
): {
  summary: ExecutiveSummary | undefined
  isLoading: boolean
  isError: boolean
  error: Error | null
  refetch: () => void
}
```

**Implementation**:
```typescript
import { useQuery } from "@tanstack/react-query"
import { getExecutiveSummary } from "@/services/insights-api"
import { insightKeys } from "@/lib/query-keys"

export function useExecutiveSummary(experimentId: string) {
  return useQuery({
    queryKey: insightKeys.summary(experimentId),
    queryFn: () => getExecutiveSummary(experimentId),
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: (data) => {
      // Auto-refresh every 15s if pending or partial
      return data?.status === "pending" || data?.status === "partial"
        ? 15000
        : false
    },
    retry: 2,
  })
}
```

**Usage Example**:
```tsx
function ExecutiveSummaryModal({ experimentId, open, onOpenChange }) {
  const { summary, isLoading } = useExecutiveSummary(experimentId)

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent>
        {isLoading ? <LoadingState /> : <SummaryContent summary={summary} />}
      </SheetContent>
    </Sheet>
  )
}
```

---

## Services

### insights-api.ts

**File**: `frontend/src/services/insights-api.ts`

**Purpose**: API client functions for insight endpoints.

```typescript
import { fetchAPI } from "./api"
import type { ChartInsight, ExecutiveSummary, ChartTypeWithInsight } from "@/types/insights"

export async function getChartInsight(
  experimentId: string,
  chartType: ChartTypeWithInsight
): Promise<ChartInsight> {
  return fetchAPI(`/experiments/${experimentId}/insights/${chartType}`)
}

export async function getAllChartInsights(
  experimentId: string,
  status?: "pending" | "completed" | "failed"
): Promise<{
  experimentId: string
  insights: ChartInsight[]
  totalCount: number
  completedCount: number
  pendingCount: number
  failedCount: number
}> {
  const params = status ? `?status=${status}` : ""
  return fetchAPI(`/experiments/${experimentId}/insights${params}`)
}

export async function getExecutiveSummary(
  experimentId: string
): Promise<ExecutiveSummary> {
  return fetchAPI(`/experiments/${experimentId}/insights/summary`)
}

export async function triggerInsightGeneration(
  experimentId: string,
  options?: {
    chartTypes?: ChartTypeWithInsight[]
    force?: boolean
  }
): Promise<{
  experimentId: string
  message: string
  chartTypes: string[]
  estimatedCompletionTime: string
}> {
  return fetchAPI(`/experiments/${experimentId}/insights/generate`, {
    method: "POST",
    body: JSON.stringify(options),
  })
}
```

---

## Query Keys

**File**: `frontend/src/lib/query-keys.ts` (modified)

```typescript
export const insightKeys = {
  all: ["insights"] as const,
  experiments: (experimentId: string) => [...insightKeys.all, experimentId] as const,
  chart: (experimentId: string, chartType: string) =>
    [...insightKeys.experiments(experimentId), "chart", chartType] as const,
  summary: (experimentId: string) =>
    [...insightKeys.experiments(experimentId), "summary"] as const,
}
```

---

## Contract Guarantees

### Component Contracts

1. **InsightSection**:
   - ✅ Always renders without crashing (even with null data)
   - ✅ Shows appropriate state (loading/error/failed/completed)
   - ✅ Collapsed by default (never blocks chart view)
   - ✅ Auto-refreshes when status="pending"

2. **ExecutiveSummaryModal**:
   - ✅ Renders all sections even with partial data
   - ✅ Shows warning for partial summaries
   - ✅ Displays metadata (model, timestamp, included charts)
   - ✅ Auto-refreshes when status="pending" or "partial"

3. **ViewSummaryButton**:
   - ✅ Disabled when no summary available
   - ✅ Shows loading indicator during generation
   - ✅ Badge visible to draw attention

### Hook Contracts

1. **useChartInsight**:
   - ✅ Returns undefined while loading (first fetch)
   - ✅ Returns ChartInsight with status once fetched
   - ✅ Auto-refreshes every 10s if status="pending"
   - ✅ Caches completed insights for 5 minutes
   - ✅ Retries failed requests 2 times

2. **useExecutiveSummary**:
   - ✅ Returns undefined while loading
   - ✅ Returns ExecutiveSummary with status once fetched
   - ✅ Auto-refreshes every 15s if status="pending" or "partial"
   - ✅ Caches completed summaries for 5 minutes
   - ✅ Retries failed requests 2 times

### Service Contracts

1. **insights-api.ts**:
   - ✅ All functions return typed promises
   - ✅ Handles HTTP errors via fetchAPI base function
   - ✅ Converts snake_case API responses to camelCase TypeScript

---

**Version**: 1.0.0
**Last Updated**: 2025-12-29
