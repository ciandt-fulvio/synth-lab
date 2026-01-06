# Quickstart: AI-Generated Insights for Quantitative Analysis

**Feature**: 023-quantitative-ai-insights
**Date**: 2025-12-29

## Overview

This guide shows how to use AI-generated insights for interpreting quantitative simulation results in synth-lab.

## For Researchers (End Users)

### Viewing Individual Chart Insights

1. **Run an Experiment**
   - Create a new experiment in the Experiment Hub
   - Configure simulation parameters (n_synths, scorecard, etc.)
   - Click "Iniciar Análise" to run the simulation

2. **Wait for Analysis to Complete**
   - Analysis typically takes 1-3 minutes depending on synth count
   - Charts are pre-computed in the background
   - Insights are generated automatically after chart data is cached

3. **View Chart-Specific Insights**
   - Navigate to the Results page for your experiment
   - Each chart card now has a collapsible "Insights de IA" section
   - Click to expand and read AI-generated analysis:
     - **Problem Understanding**: What the AI understood about your test
     - **Trends Observed**: Key patterns in the data
     - **Key Findings**: 2-4 actionable insights
     - **Summary**: Concise interpretation (≤200 words)

4. **Available Chart Types with Insights**:
   - ✅ Try vs Success (Overview phase)
   - ✅ SHAP Summary (Explainability phase)
   - ✅ PDP (Explainability phase)
   - ✅ PCA Scatter (Segmentation phase)
   - ✅ Radar Comparison (Segmentation phase)
   - ✅ Extreme Cases (Edge Cases phase)
   - ✅ Outliers (Edge Cases phase)

### Viewing Executive Summary

1. **Access the Summary**
   - On the Results page header, click the "Ver Resumo Executivo" button
   - A side panel opens with the synthesized summary

2. **Review Organized Sections**:
   - **Visão Geral**: What was tested and overall results
   - **Explicabilidade**: Key drivers and feature impacts
   - **Segmentação**: User groups and behavioral patterns
   - **Casos Extremos**: Surprises and anomalies
   - **Recomendações**: 2-3 actionable recommendations for product team

3. **Share with Stakeholders**
   - Copy text directly from the summary panel
   - Export full report (includes summary + all insights)
   - Present findings in product review meetings

### Understanding Insight Status

**Pending** (Gerando insights...):
- Insight is currently being generated
- Typically takes 30-60 seconds per chart
- Page auto-refreshes every 10 seconds to check for completion

**Completed** (✅):
- Insight successfully generated
- All sections populated with analysis
- Cached for future views (no regeneration needed)

**Failed** (❌ Insights indisponíveis):
- LLM generation failed (API error, timeout, etc.)
- You can manually trigger regeneration via API (see Developer Guide)
- Executive summary will be generated with available insights

**Partial Summary** (⚠️ Resumo Parcial):
- Less than 3 chart insights available
- Summary generated with caveat about limited data
- Will update automatically once more insights complete

---

## For Developers

### Backend Setup

1. **Install Dependencies**
   ```bash
   # Already included in pyproject.toml
   uv pip install -e ".[dev]"
   ```

2. **Configure LLM Model**
   ```python
   # src/synth_lab/infrastructure/config.py
   REASONING_MODEL = "04-mini"  # For insight generation
   ```

3. **Extend CacheKeys Enum**
   ```python
   # src/synth_lab/repositories/analysis_repository.py
   class CacheKeys(str, Enum):
       # ... existing keys
       INSIGHT_TRY_VS_SUCCESS = "insight_try_vs_success"
       INSIGHT_SHAP_SUMMARY = "insight_shap_summary"
       # ... other insight keys
       EXECUTIVE_SUMMARY = "executive_summary"
   ```

4. **Create Domain Entities**
   ```bash
   # Create entity files
   touch src/synth_lab/domain/entities/chart_insight.py
   touch src/synth_lab/domain/entities/executive_summary.py
   ```

   See [data-model.md](./data-model.md) for entity definitions.

5. **Implement Services**
   ```bash
   # Create service files
   touch src/synth_lab/services/insight_service.py
   touch src/synth_lab/services/executive_summary_service.py
   ```

   **Example: InsightService**
   ```python
   from synth_lab.infrastructure.llm_client import LLMClient, get_llm_client
   from synth_lab.infrastructure.phoenix_tracing import get_tracer
   from synth_lab.domain.entities.chart_insight import ChartInsight

   _tracer = get_tracer("insight-service")

   class InsightService:
       def __init__(self, llm_client: LLMClient | None = None):
           self.llm = llm_client or get_llm_client()
           self.analysis_repo = AnalysisRepository()

       def generate_insight(
           self,
           analysis_id: str,
           chart_type: str
       ) -> ChartInsight:
           with _tracer.start_as_current_span(f"generate_insight_{chart_type}"):
               # 1. Read chart data
               chart_data = self.analysis_repo.get_cached_data(...)

               # 2. Build prompt
               prompt = self._build_prompt(chart_type, chart_data)

               # 3. Call LLM
               response = self.llm.complete_json(
                   messages=[...],
                   model=REASONING_MODEL
               )

               # 4. Parse and store
               insight = self._parse_response(response, chart_type)
               self.analysis_repo.store_chart_insight(analysis_id, chart_type, insight)

               return insight
   ```

6. **Hook into Analysis Service**
   ```python
   # src/synth_lab/services/simulation/analysis_service.py
   def _pre_compute_cache(self):
       # ... existing chart pre-computation
       self._cache_try_vs_success()
       self._cache_shap_summary()
       # ... others

       # NEW: Trigger insight generation
       self._trigger_insight_generation()

   def _trigger_insight_generation(self):
       def generate_all_insights():
           import asyncio
           asyncio.run(self._generate_insights_parallel())

       thread = threading.Thread(target=generate_all_insights, daemon=True)
       thread.start()
   ```

7. **Create API Router**
   ```bash
   touch src/synth_lab/api/routers/insights.py
   ```

   See [api-contracts.md](./contracts/api-contracts.md) for endpoint definitions.

8. **Write Tests**
   ```bash
   # Unit tests
   touch tests/unit/services/test_insight_service.py
   touch tests/unit/domain/entities/test_chart_insight.py

   # Integration tests
   touch tests/integration/api/test_insights_router.py

   # Run tests
   pytest tests/unit/services/test_insight_service.py -v
   ```

### Frontend Setup

1. **Install Dependencies** (already installed)
   ```bash
   cd frontend
   npm install
   ```

2. **Create Type Definitions**
   ```bash
   touch frontend/src/types/insights.ts
   ```

   See [data-model.md](./data-model.md) for TypeScript types.

3. **Create API Client**
   ```bash
   touch frontend/src/services/insights-api.ts
   ```

   ```typescript
   import { fetchAPI } from "./api"
   import type { ChartInsight } from "@/types/insights"

   export async function getChartInsight(
     experimentId: string,
     chartType: string
   ): Promise<ChartInsight> {
     return fetchAPI(`/experiments/${experimentId}/insights/${chartType}`)
   }
   ```

4. **Add Query Keys**
   ```typescript
   // frontend/src/lib/query-keys.ts
   export const insightKeys = {
     all: ["insights"] as const,
     experiments: (experimentId: string) => [...insightKeys.all, experimentId] as const,
     chart: (experimentId: string, chartType: string) =>
       [...insightKeys.experiments(experimentId), "chart", chartType] as const,
     summary: (experimentId: string) =>
       [...insightKeys.experiments(experimentId), "summary"] as const,
   }
   ```

5. **Create Hooks**
   ```bash
   touch frontend/src/hooks/use-chart-insight.ts
   touch frontend/src/hooks/use-executive-summary.ts
   ```

   ```typescript
   // use-chart-insight.ts
   import { useQuery } from "@tanstack/react-query"
   import { getChartInsight } from "@/services/insights-api"
   import { insightKeys } from "@/lib/query-keys"

   export function useChartInsight(experimentId: string, chartType: string) {
     return useQuery({
       queryKey: insightKeys.chart(experimentId, chartType),
       queryFn: () => getChartInsight(experimentId, chartType),
       staleTime: 5 * 60 * 1000,
       refetchInterval: (data) => data?.status === "pending" ? 10000 : false,
     })
   }
   ```

6. **Create Components**
   ```bash
   touch frontend/src/components/experiments/results/InsightSection.tsx
   touch frontend/src/components/experiments/results/ExecutiveSummaryModal.tsx
   touch frontend/src/components/experiments/results/ViewSummaryButton.tsx
   ```

   See [frontend-contracts.md](./contracts/frontend-contracts.md) for component specifications.

7. **Modify Existing Chart Sections**
   - Add `<InsightSection />` to each chart card
   - Import and use the component:
   ```tsx
   import { InsightSection } from "./InsightSection"

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

8. **Add View Summary Button to Header**
   ```tsx
   // In ExperimentResultsPage.tsx
   import { ViewSummaryButton } from "./ViewSummaryButton"

   <div className="flex items-center justify-between">
     <h1>Resultados da Análise</h1>
     <ViewSummaryButton experimentId={experimentId} />
   </div>
   ```

---

## Testing the Feature

### Manual Testing Workflow

1. **Start Backend**
   ```bash
   uv run uvicorn synth_lab.api.main:app --reload
   ```

2. **Start Frontend**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Create Test Experiment**
   - Navigate to `http://localhost:8080`
   - Create new experiment with:
     - Hypothesis: "Novo fluxo de checkout reduz fricção"
     - n_synths: 100 (fast for testing)
     - Scorecard: Any available scorecard
   - Start analysis

4. **Monitor Insight Generation**
   - Open browser DevTools → Network tab
   - Watch for `/insights/{chart_type}` API calls
   - Check timing: should complete within 2 minutes of chart caching

5. **Verify Chart Insights**
   - Expand "Insights de IA" section in each chart card
   - Verify all sections populated:
     - Problem Understanding
     - Trends Observed
     - Key Findings (2-4 items)
     - Summary (≤200 words)

6. **Verify Executive Summary**
   - Click "Ver Resumo Executivo" button
   - Verify all sections:
     - Visão Geral
     - Explicabilidade
     - Segmentação
     - Casos Extremos
     - Recomendações (2-3 items)
   - Check metadata: model, timestamp, included charts

### Automated Testing

```bash
# Backend unit tests (fast - no LLM calls)
pytest tests/unit/services/test_insight_service.py -v

# Backend integration tests (with test DB)
pytest tests/integration/api/test_insights_router.py -v

# Frontend component tests
cd frontend
npm run test -- InsightSection.test.tsx

# Contract tests (frontend-backend compatibility)
pytest tests/contract/test_insights_contracts.py -v

# Full test suite
make test
```

---

## Troubleshooting

### Insights Not Generating

**Problem**: Insights section shows "Gerando insights..." indefinitely

**Possible Causes**:
1. LLM API key not configured
2. Chart data not cached yet
3. Background thread failed silently

**Debug Steps**:
```bash
# 1. Check logs for LLM errors
tail -f /tmp/synth-lab-backend.log | grep insight

# 2. Verify chart data exists in analysis_cache
postgresql3 output/synthlab.db "SELECT cache_key FROM analysis_cache WHERE analysis_id='ana_xxx'"

# 3. Manually trigger insight generation
curl -X POST http://localhost:8000/api/experiments/exp_xxx/insights/generate
```

### Summary Shows "Partial Summary"

**Problem**: Executive summary indicates limited data

**Cause**: Less than 3 chart insights completed successfully

**Solution**:
1. Wait for more insights to complete (auto-refreshes every 15s)
2. Check which insights failed: `GET /experiments/{id}/insights?status=failed`
3. Manually regenerate failed insights: `POST /experiments/{id}/insights/generate`

### Frontend Shows 404 Error

**Problem**: API calls return 404 for `/insights/{chart_type}`

**Cause**: Insight not generated yet or invalid chart_type

**Solution**:
```bash
# 1. Verify experiment has completed analysis
curl http://localhost:8000/api/experiments/exp_xxx

# 2. Check available insights
curl http://localhost:8000/api/experiments/exp_xxx/insights

# 3. Verify chart_type is valid
# Valid types: try_vs_success, shap_summary, pdp, pca_scatter, radar_comparison, extreme_cases, outliers
```

---

## Best Practices

### For Researchers

1. **Wait for All Insights**: Let all 7 chart insights complete before reviewing executive summary for comprehensive analysis
2. **Compare Insights**: Cross-reference findings across charts (e.g., SHAP + PDP for feature impacts)
3. **Use Summaries for Stakeholders**: Executive summary is written for non-technical audiences
4. **Save Reports Early**: Export full report once insights complete (they don't regenerate)

### For Developers

1. **Test with Mocked LLM**: Use mocked responses in unit tests (LLM calls are expensive and slow)
2. **Handle Partial Failures**: Always account for failed insight generation in UI
3. **Cache Aggressively**: Completed insights never change - cache for 5+ minutes
4. **Monitor Phoenix**: Use Phoenix tracing to debug LLM call failures
5. **Respect Token Limits**: Sample large datasets (> 1000 points) to fit within context window

---

## Example Use Cases

### Use Case 1: Quick Interpretation

**Scenario**: PM wants to quickly understand simulation results without deep analysis

**Steps**:
1. Run experiment (500 synths, checkout flow)
2. Wait 3-5 minutes for analysis + insights
3. Click "Ver Resumo Executivo"
4. Read "Recomendações" section
5. Share 2-3 bullet points with engineering team

**Time Saved**: 40% reduction (from 30 min manual analysis to 15 min with AI insights)

### Use Case 2: Deep Dive on Outliers

**Scenario**: Researcher finds surprising failure cases

**Steps**:
1. Review Try vs Success insight → Notices low conversion
2. Expand Extreme Cases insight → Identifies high-capability users failing
3. Cross-check SHAP insight → Low "Confiança" is key driver
4. Hypothesis: Security concerns, not usability issues
5. Design follow-up experiment with clearer trust signals

**Value**: AI highlights unexpected patterns that might be missed in manual review

### Use Case 3: Stakeholder Presentation

**Scenario**: Presenting simulation findings to executive team

**Steps**:
1. Export executive summary as PDF
2. Use "Visão Geral" as slide 1
3. Highlight "Recomendações" as slide 2
4. Back up with specific insights from SHAP and PCA charts
5. Q&A references detailed insights per chart

**Value**: Professional, AI-synthesized narrative for non-technical audiences

---

## Next Steps

- **Learn More**: Read [research.md](./research.md) for technical deep dive
- **API Reference**: See [api-contracts.md](./contracts/api-contracts.md)
- **Component Guide**: See [frontend-contracts.md](./contracts/frontend-contracts.md)
- **Data Model**: See [data-model.md](./data-model.md)

**Version**: 1.0.0
**Last Updated**: 2025-12-29
