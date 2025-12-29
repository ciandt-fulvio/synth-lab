# Research: Analysis Charts Frontend Integration

**Feature**: 021-analysis-charts-frontend
**Date**: 2025-12-28

## Executive Summary

Esta pesquisa analisa os padrões existentes no frontend do synth-lab para implementação dos gráficos de análise quantitativa (fases 2-6). O objetivo é garantir consistência visual e arquitetural com os componentes já implementados (TryVsSuccessSection, OutcomeDistributionChart).

---

## 1. Padrões de Componentes Existentes

### 1.1 Section Component Pattern (TryVsSuccessSection)

**Decision**: Usar padrão de Section wrapper para todos os gráficos
**Rationale**: O TryVsSuccessSection estabelece um padrão claro de:
- Card com header (título + ícone + descrição)
- Explicação colapsável com gradiente indigo
- Controles em background slate-50
- Área de chart com estados loading/error/empty

**Alternatives Considered**:
- ChartContainer direto: rejeitado porque não inclui explicações educativas
- Custom wrapper por fase: rejeitado por duplicação de código

### 1.2 Color System

**Decision**: Seguir paleta de cores existente
**Rationale**: Cores já definidas com significado semântico claro

```typescript
// Status/Quadrant colors
ok: '#22c55e'           // green-500
discovery_issue: '#3b82f6' // blue-500
usability_issue: '#ef4444' // red-500
low_value: '#f59e0b'    // amber-500

// Outcome colors
success: '#22c55e'      // green-500
failed: '#ef4444'       // red-500
did_not_try: '#94a3b8'  // slate-400
```

**Alternatives Considered**:
- Cores customizadas por chart: rejeitado por inconsistência visual

### 1.3 State Management Pattern

**Decision**: React Query hooks com query keys centralizadas
**Rationale**: Padrão já estabelecido em `use-analysis-charts.ts` e `use-clustering.ts`

```typescript
// Hook pattern
export function useChartData(id: string, ...params) {
  return useQuery({
    queryKey: [...queryKeys.path(id), ...params],
    queryFn: () => getChartData(id, ...params),
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
  });
}
```

---

## 2. API Endpoints Analysis

### 2.1 Endpoint Architecture

**Decision**: Manter endpoints simulation-based existentes para fases 2-3
**Rationale**:
- PhaseLocation já usa `/simulation/simulations/{id}/charts/*`
- PhaseSegmentation usa `/simulation/simulations/{id}/clusters/*`
- Não há necessidade de refatorar para experiment-based

**Backend Status by Phase**:

| Phase | Endpoints | Backend Status |
|-------|-----------|----------------|
| 2 (Location) | heatmap, box-plot, scatter, tornado | ✅ Implemented |
| 3 (Segmentation) | clusters, elbow, dendrogram, radar | ✅ Implemented |
| 4 (Edge Cases) | extreme-cases, outliers | ✅ API exists |
| 5 (Explainability) | shap/summary, shap/{id}, pdp | ✅ API exists |
| 6 (Insights) | insights, executive-summary | ⚠️ Returns placeholders |

### 2.2 Type Definitions

**Decision**: Usar tipos existentes em `frontend/src/types/simulation.ts`
**Rationale**: Todos os tipos para todas as fases já estão definidos

Tipos disponíveis:
- Phase 4: `ExtremeCasesTable`, `ExtremeSynth`, `OutlierResult`, `OutlierSynth`
- Phase 5: `ShapSummary`, `ShapExplanation`, `PDPResult`, `PDPComparison`
- Phase 6: `ChartInsight`, `SimulationInsights`, `ExecutiveSummaryResponse`

---

## 3. Frontend Architecture Compliance

### 3.1 Architecture Rules Verification

| Rule | Status | Implementation |
|------|--------|----------------|
| Pages only compose components | ✅ | ExperimentDetail.tsx delegates to Phase components |
| Components are pure (props→JSX) | ✅ | Chart components receive data via props |
| Hooks encapsulate React Query | ✅ | use-simulation-charts.ts, use-clustering.ts |
| Services call API | ✅ | simulation-api.ts has all functions |
| Query keys centralized | ✅ | lib/query-keys.ts has all keys |

### 3.2 Component Hierarchy

```
ExperimentDetail.tsx (page)
└── AnalysisPhaseTabs.tsx (container)
    ├── PhaseOverview.tsx
    │   ├── SimulationSummary (internal)
    │   ├── ChartContainer + OutcomeDistributionChart
    │   └── TryVsSuccessSection
    │       ├── Collapsible explanation
    │       ├── Controls (sliders)
    │       └── TryVsSuccessChart
    ├── PhaseLocation.tsx
    │   ├── ChartContainer + FailureHeatmap + selects
    │   ├── ChartContainer + BoxPlotChart + select
    │   ├── ChartContainer + ScatterCorrelationChart + selects
    │   └── ChartContainer + TornadoChart
    ├── PhaseSegmentation.tsx
    │   ├── Clustering controls (tabs, inputs)
    │   ├── ChartContainer + ElbowChart
    │   ├── ChartContainer + DendrogramChart
    │   └── ChartContainer + RadarComparisonChart
    ├── PhaseEdgeCases.tsx (TODO)
    ├── PhaseExplainability.tsx (TODO)
    └── PhaseInsights.tsx (TODO)
```

---

## 4. UI/UX Patterns

### 4.1 Explanation Collapsible

**Decision**: Incluir explicação colapsável em todos os gráficos complexos
**Rationale**: TryVsSuccessSection demonstra que explicações educativas melhoram a usabilidade

Estrutura padrão:
```
- "O que este gráfico mostra?" → Descrição
- "Como interpretar?" → Guia visual
- "Para que servem os controles?" → Descrição de parâmetros
```

### 4.2 Control Patterns

| Controle | Uso | Componente |
|----------|-----|------------|
| Slider | Thresholds (0-1) | shadcn/ui Slider |
| Select | Axis/attribute selection | shadcn/ui Select |
| Tabs | Method selection | shadcn/ui Tabs |
| Input | Numeric values (clusters) | shadcn/ui Input |

### 4.3 Empty/Loading/Error States

**Decision**: Usar ChartContainer existente para estados consistentes
**Rationale**: Componente já implementa:
- Skeleton loading
- Error com retry button
- Empty state com mensagem

---

## 5. Recharts Best Practices

### 5.1 Chart Types by Phase

| Phase | Chart | Recharts Component |
|-------|-------|-------------------|
| 2 | Heatmap | Custom grid with rectangles |
| 2 | BoxPlot | Custom with ErrorBar |
| 2 | Scatter | ScatterChart |
| 2 | Tornado | BarChart (horizontal) |
| 3 | Elbow | LineChart |
| 3 | Radar | RadarChart |
| 3 | Dendrogram | Custom SVG tree |
| 5 | SHAP Summary | BarChart (horizontal) |
| 5 | SHAP Waterfall | Custom waterfall |
| 5 | PDP | LineChart with area |

### 5.2 Responsive Container Pattern

```tsx
<ResponsiveContainer width="100%" height={height}>
  <Chart margin={{ top: 20, right: 20, bottom: 40, left: 60 }}>
    {/* Chart content */}
  </Chart>
</ResponsiveContainer>
```

### 5.3 Custom Tooltip Pattern

```tsx
function CustomTooltip({ active, payload }: TooltipProps) {
  if (!active || !payload?.[0]) return null;
  const data = payload[0].payload;
  return (
    <div className="bg-white rounded-lg shadow-lg border border-slate-200 p-3 text-sm">
      {/* Tooltip content */}
    </div>
  );
}
```

---

## 6. Implementation Recommendations

### 6.1 Phase 4: Edge Cases

**Components needed**:
1. `ExtremeCasesSection.tsx` - Tabelas de casos extremos
2. `OutliersSection.tsx` - Tabela de outliers com slider de contamination

**Key features**:
- Tabelas com synth_id, taxas, categoria
- Slider para contamination (0.01-0.3)
- Perguntas sugeridas para entrevistas

### 6.2 Phase 5: Explainability

**Components needed**:
1. `ShapSummarySection.tsx` - Importância global de features
2. `ShapWaterfallSection.tsx` - Explicação individual (seletor de synth)
3. `PDPSection.tsx` - Dependência parcial por feature

**Key features**:
- Bar chart horizontal para SHAP summary
- Waterfall chart para explicação individual
- Line chart para PDP
- Feature selector dropdown

### 6.3 Phase 6: Insights

**Components needed**:
1. `InsightsListSection.tsx` - Lista de insights gerados
2. `ExecutiveSummarySection.tsx` - Resumo executivo

**Key features**:
- Cards de insight com caption, explanation, evidence
- Generate button com loading state
- Markdown rendering para summary

---

## 7. Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Backend returns empty data | Implement graceful empty states |
| SHAP/PDP endpoints slow | Add timeout handling, show loading |
| LLM insight generation fails | Show error with retry option |
| Chart performance with large data | Add limit parameters, virtualization |

---

## 8. Next Steps

1. ✅ Research complete
2. → Generate data-model.md (frontend types summary)
3. → Generate quickstart.md (developer guide)
4. → Create tasks.md with implementation tasks
5. → Begin implementation following TDD principles
