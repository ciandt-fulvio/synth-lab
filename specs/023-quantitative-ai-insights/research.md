# Phase 0: Research - AI-Generated Insights for Quantitative Analysis

**Feature**: 023-quantitative-ai-insights
**Date**: 2025-12-29
**Status**: Complete

## Objective

Research technical approach for implementing automatic AI-generated insights for quantitative analysis results, including individual chart insights and executive summaries.

## Key Research Questions

1. **How should insights be stored in analysis_cache?**
   - Use existing `analysis_cache` table with composite PK (analysis_id, cache_key)
   - Create new cache_key enum values for insights:
     - `INSIGHT_TRY_VS_SUCCESS`
     - `INSIGHT_SHAP_SUMMARY`
     - `INSIGHT_PDP`
     - `INSIGHT_PCA_SCATTER`
     - `INSIGHT_RADAR_COMPARISON`
     - `INSIGHT_EXTREME_CASES`
     - `INSIGHT_OUTLIERS`
     - `EXECUTIVE_SUMMARY`
   - Each insight stored as JSON in `data` column with structure:
     ```python
     {
       "chart_type": "try_vs_success",
       "insight_text": "...",  # ≤200 words
       "generation_timestamp": "2025-12-29T...",
       "status": "completed",  # pending|completed|failed
       "model": "04-mini",
       "reasoning_trace": "..."  # optional, for debugging
     }
     ```

2. **How should insight generation be triggered?**
   - Hook into existing analysis cache system after chart data is written
   - Pattern similar to `_pre_compute_cache()` in analysis service
   - After each chart cache write, trigger async insight generation
   - Use daemon thread pattern (existing in analysis service) or asyncio.create_task()
   - **Decision**: Use threading.Thread(daemon=True) to match existing pattern in analysis service

3. **Which LLM model should be used for reasoning?**
   - Spec requires 04-mini or equivalent reasoning-capable model
   - Current system uses gpt-4o (DEFAULT_MODEL in config.py)
   - **Decision**: Use 04-mini for insight generation (reasoning capability)
   - LLMClient already supports custom model selection via `model=` parameter
   - Add config constant: `REASONING_MODEL = "04-mini"`

4. **How should chart data be formatted for LLM input?**
   - Analysis cache stores chart data as JSON (already structured)
   - Extract relevant data from cache and convert to table/markdown format
   - Include experiment metadata (hypothesis, description) for context
   - Keep within token limits (~10K tokens per chart)
   - **Approach**:
     - Read chart data from analysis_cache
     - Convert JSON to markdown table or structured text
     - Build prompt with: experiment context + chart data + analysis request
     - For large datasets (e.g., SHAP with 1000+ points): sample or aggregate

5. **How should prompts be structured for each chart type?**
   - Each chart type needs custom prompt template
   - Common structure:
     ```
     System: You are a UX researcher analyzing simulation results.

     Context:
     - Experiment: {hypothesis}
     - Description: {description}
     - Synth Count: {n_synths}
     - Scorecard: {scorecard_name}

     Chart Data ({chart_type}):
     {formatted_data}

     Instructions:
     1. Understand the problem being tested
     2. Identify trends and patterns in the data
     3. Extract 2-4 key findings
     4. Summarize in ≤200 words

     Format your response as JSON:
     {
       "problem_understanding": "...",
       "trends_observed": "...",
       "key_findings": ["...", "...", "..."],
       "summary": "..."
     }
     ```
   - Chart-specific variations:
     - **Try vs Success**: Focus on success_rate vs failure patterns
     - **SHAP**: Emphasize feature importance and contribution direction
     - **PDP**: Highlight non-linear relationships and interaction effects
     - **PCA Scatter**: Identify clusters and segmentation patterns
     - **Radar Comparison**: Compare profile differences across segments
     - **Extreme Cases**: Analyze surprising failures/successes
     - **Outliers**: Explain anomalous behavior

6. **How should executive summary synthesis work?**
   - Wait for all individual insights to complete (or timeout after X minutes)
   - Read all 7 individual insights from analysis_cache
   - Build synthesis prompt:
     ```
     System: You are a UX research director synthesizing analysis findings.

     Context:
     - Experiment: {hypothesis}
     - Analysis: {n_synths} synthetic users

     Individual Chart Insights:

     1. Overview (Try vs Success):
     {insight_text}

     2. Explainability (SHAP Summary):
     {insight_text}

     3. Explainability (PDP):
     {insight_text}

     4. Segmentation (PCA Scatter):
     {insight_text}

     5. Segmentation (Radar Comparison):
     {insight_text}

     6. Edge Cases (Extreme Cases):
     {insight_text}

     7. Edge Cases (Outliers):
     {insight_text}

     Instructions:
     Synthesize these insights into a cohesive executive summary (≤800 words) organized by:
     - Overview: What was tested and overall results
     - Explainability: Key drivers and feature impacts
     - Segmentation: User groups and patterns
     - Edge Cases: Surprises and anomalies
     - Recommendations: 2-3 actionable insights for product team
     ```

7. **How should errors be handled during insight generation?**
   - LLMClient already has retry logic (tenacity with exponential backoff)
   - Catch exceptions at service level
   - Store failed status in analysis_cache
   - Continue processing other charts if one fails
   - For executive summary: synthesize available insights, note missing ones
   - UI shows "Insights unavailable" for failed charts
   - **Error scenarios**:
     - LLM API timeout/rate limit → Retry up to 3 times
     - Invalid response format → Log error, mark as failed
     - Missing chart data → Skip insight generation
     - Partial insight completion (< 3 of 7) → Generate summary with caveat

## Findings

### 1. Analysis Cache Integration

**Current System**:
- `analysis_cache` table: `(analysis_id, cache_key, data, params, computed_at)`
- `CacheKeys` enum: TRY_VS_SUCCESS, DISTRIBUTION, HEATMAP, SCATTER, CORRELATIONS, EXTREME_CASES, OUTLIERS, SHAP_SUMMARY
- Pre-computation via `_pre_compute_cache()` in daemon thread after analysis completes

**Integration Points**:
```python
# analysis_service.py (existing pattern)
def _pre_compute_cache(self):
    """Pre-compute standard cache entries after analysis."""
    # Existing chart pre-computation
    self._cache_try_vs_success()
    self._cache_shap_summary()
    # ... other charts

    # NEW: Trigger insight generation after all charts cached
    self._trigger_insight_generation()

def _trigger_insight_generation(self):
    """Start async insight generation for all chart types."""
    from synth_lab.services.insight_service import InsightService

    insight_service = InsightService()

    # Run in background thread (matches existing pattern)
    def generate_all_insights():
        # Generate insights for each chart type in parallel
        import asyncio
        tasks = [
            insight_service.generate_insight_async(
                analysis_id=self.analysis.id,
                chart_type="try_vs_success"
            ),
            # ... other chart types
        ]
        asyncio.run(asyncio.gather(*tasks, return_exceptions=True))

        # After all complete, generate executive summary
        insight_service.generate_executive_summary(analysis_id=self.analysis.id)

    import threading
    thread = threading.Thread(target=generate_all_insights, daemon=True)
    thread.start()
```

### 2. LLM Integration Pattern

**Existing Pattern** (from avatar_service.py, research_service.py):
```python
class MyService:
    def __init__(self, llm_client: LLMClient | None = None):
        self.llm = llm_client or get_llm_client()
        self.logger = logger.bind(component="my_service")

    def generate(self, data) -> Result:
        with _tracer.start_as_current_span("generate"):
            prompt = self._build_prompt(data)
            response = self.llm.complete_json(
                messages=[{"role": "system", "content": "..."},
                          {"role": "user", "content": prompt}],
                model="04-mini",  # Use reasoning model
            )
            return self._parse_response(response)
```

**Apply to InsightService**:
```python
class InsightService:
    def __init__(self, llm_client: LLMClient | None = None):
        self.llm = llm_client or get_llm_client()
        self.logger = logger.bind(component="insight_service")
        self.analysis_repo = AnalysisRepository()

    def generate_insight(
        self,
        analysis_id: str,
        chart_type: str
    ) -> ChartInsight:
        """Generate AI insight for a specific chart type."""
        with _tracer.start_as_current_span(f"generate_insight_{chart_type}"):
            # 1. Read chart data from analysis_cache
            chart_data = self.analysis_repo.get_cached_data(
                analysis_id,
                CacheKeys[chart_type.upper()]
            )

            # 2. Read experiment metadata
            experiment = self._get_experiment_metadata(analysis_id)

            # 3. Build prompt
            prompt = self._build_chart_prompt(chart_type, chart_data, experiment)

            # 4. Call LLM
            response = self.llm.complete_json(
                messages=[
                    {"role": "system", "content": "You are a UX researcher..."},
                    {"role": "user", "content": prompt}
                ],
                model=REASONING_MODEL,
            )

            # 5. Parse and store
            insight = self._parse_insight_response(response, chart_type)
            self.analysis_repo.store_insight(analysis_id, chart_type, insight)

            return insight
```

### 3. Data Format Examples

**Try vs Success Chart**:
```json
{
  "try_rate": 0.85,
  "success_rate": 0.62,
  "failed_rate": 0.23,
  "did_not_try_rate": 0.15
}
```

**SHAP Summary** (top features):
```json
{
  "base_value": 0.5,
  "features": [
    {"name": "Confiança", "importance": 0.234, "direction": "positive"},
    {"name": "Tolerância", "importance": 0.189, "direction": "positive"},
    {"name": "Capacidade", "importance": 0.145, "direction": "positive"}
  ]
}
```

**PCA Scatter** (clusters):
```json
{
  "n_components": 2,
  "explained_variance": [0.42, 0.28],
  "clusters": [
    {"id": 0, "size": 120, "centroid": [0.5, 0.3]},
    {"id": 1, "size": 80, "centroid": [-0.3, 0.1]}
  ]
}
```

### 4. Token Budget Analysis

**Per-Chart Limits**:
- Experiment context: ~200 tokens (hypothesis + description)
- Chart data: varies by type
  - Try vs Success: ~50 tokens (simple percentages)
  - SHAP Summary: ~500 tokens (top 10 features)
  - PDP: ~800 tokens (feature values + effects)
  - PCA Scatter: ~300 tokens (cluster summaries)
  - Radar Comparison: ~400 tokens (profile attributes)
  - Extreme Cases: ~600 tokens (10 worst + 10 best)
  - Outliers: ~500 tokens (outlier descriptions)
- Prompt instructions: ~300 tokens
- Total input: ~500-1500 tokens per chart ✅ Well within 10K limit

**For Large Datasets**:
- SHAP with 1000+ synths: Sample top 20 most important features
- PCA with 500+ points: Aggregate into cluster summaries (already done)
- Outliers: Limit to top 20 anomalies

### 5. Async Pattern Decision

**Options Evaluated**:
1. **Threading** (existing pattern in analysis_service.py)
   - ✅ Matches current codebase patterns
   - ✅ Simple integration with daemon threads
   - ❌ GIL limitations (but LLM calls are I/O-bound, not CPU-bound)

2. **asyncio** (new pattern)
   - ✅ Better for I/O-bound operations
   - ✅ Easier parallel execution
   - ❌ Requires async refactor of analysis_service
   - ❌ More complex error handling

**Decision**: Use **threading with asyncio inside thread** (hybrid)
- Outer layer: daemon thread (matches existing pattern)
- Inner layer: asyncio for parallel LLM calls
- Reason: Minimal disruption to existing code, leverage asyncio for parallel I/O

```python
def _trigger_insight_generation(self):
    def generate_all_insights():
        import asyncio
        asyncio.run(self._generate_insights_parallel())

    thread = threading.Thread(target=generate_all_insights, daemon=True)
    thread.start()

async def _generate_insights_parallel(self):
    tasks = [
        self._generate_one_insight(chart_type)
        for chart_type in CHART_TYPES_FOR_INSIGHTS
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    # After all complete, generate summary
    await self._generate_executive_summary()
```

## Recommendations

### Technical Approach

1. **Storage**: Extend `CacheKeys` enum with 8 new values (7 chart insights + 1 summary)
2. **Service Layer**: Create two services:
   - `InsightService`: Generate individual chart insights
   - `ExecutiveSummaryService`: Synthesize insights into summary
3. **Repository Layer**: Add methods to `AnalysisRepository`:
   - `store_insight(analysis_id, chart_type, insight_data)`
   - `get_insight(analysis_id, chart_type) -> ChartInsight | None`
   - `get_all_insights(analysis_id) -> list[ChartInsight]`
   - `store_executive_summary(analysis_id, summary_data)`
   - `get_executive_summary(analysis_id) -> ExecutiveSummary | None`
4. **LLM Model**: Use `04-mini` (reasoning model) for all insight generation
5. **Async Pattern**: Hybrid threading + asyncio (daemon thread with parallel async LLM calls)
6. **Error Handling**:
   - Retry LLM calls up to 3 times (existing LLMClient retry logic)
   - Store failure status in cache
   - Continue processing other charts on failure
   - Generate summary with available insights

### Data Model

**ChartInsight Entity**:
```python
from pydantic import BaseModel

class ChartInsight(BaseModel):
    analysis_id: str
    chart_type: str  # try_vs_success | shap_summary | pdp | ...
    problem_understanding: str
    trends_observed: str
    key_findings: list[str]  # 2-4 findings
    summary: str  # ≤200 words
    generation_timestamp: datetime
    status: str  # pending | completed | failed
    model: str  # 04-mini
    reasoning_trace: str | None = None  # optional debugging
```

**ExecutiveSummary Entity**:
```python
class ExecutiveSummary(BaseModel):
    analysis_id: str
    overview: str  # What was tested, overall results
    explainability: str  # Key drivers and feature impacts
    segmentation: str  # User groups and patterns
    edge_cases: str  # Surprises and anomalies
    recommendations: list[str]  # 2-3 actionable insights
    included_chart_types: list[str]  # Which charts contributed
    generation_timestamp: datetime
    status: str
    model: str
```

### Prompt Templates (Example for Try vs Success)

```python
def _build_try_vs_success_prompt(
    self,
    chart_data: dict,
    experiment: Experiment
) -> str:
    return f"""
Você é um pesquisador de UX analisando resultados de simulação.

Contexto do Experimento:
- Hipótese: {experiment.hypothesis}
- Descrição: {experiment.description or "Nenhuma descrição fornecida"}
- Total de Synths: {experiment.n_synths}
- Scorecard: {experiment.scorecard_name}

Dados do Gráfico "Try vs Success":
- Taxa de tentativa (try_rate): {chart_data['try_rate']:.1%}
- Taxa de sucesso (success_rate): {chart_data['success_rate']:.1%}
- Taxa de falha (failed_rate): {chart_data['failed_rate']:.1%}
- Taxa de não tentativa (did_not_try_rate): {chart_data['did_not_try_rate']:.1%}

Instruções:
1. Compreenda o problema sendo testado baseado na hipótese
2. Identifique tendências nos dados (alta/baixa tentativa? alta/baixa conversão?)
3. Extraia 2-4 descobertas-chave (insights acionáveis para o time de produto)
4. Resuma em até 200 palavras

Forneça sua resposta em JSON com esta estrutura:
{{
  "problem_understanding": "O que está sendo testado e por quê",
  "trends_observed": "Padrões principais nos dados",
  "key_findings": ["Descoberta 1", "Descoberta 2", "Descoberta 3"],
  "summary": "Resumo conciso em português"
}}
"""
```

### Integration Timeline

**Phase 1 (Backend - Week 1)**:
- [ ] Add CacheKeys enum values
- [ ] Create ChartInsight and ExecutiveSummary entities
- [ ] Implement InsightService with prompt builders
- [ ] Implement ExecutiveSummaryService
- [ ] Add repository methods to AnalysisRepository
- [ ] Hook into analysis_service._pre_compute_cache()
- [ ] Write unit tests (mocked LLM)

**Phase 2 (Backend - Week 1)**:
- [ ] Create API router (`/api/routers/insights.py`)
- [ ] Add endpoints:
   - `GET /experiments/{id}/insights/{chart_type}` → Get chart insight
   - `GET /experiments/{id}/insights/summary` → Get executive summary
- [ ] Write integration tests

**Phase 3 (Frontend - Week 2)**:
- [ ] Create InsightSection.tsx component (collapsible)
- [ ] Create ExecutiveSummaryModal.tsx component
- [ ] Add hooks: useChartInsight, useExecutiveSummary
- [ ] Add API client functions in insights-api.ts
- [ ] Update query keys
- [ ] Modify all 7 chart section components to include InsightSection
- [ ] Remove "Insights" tab from navigation
- [ ] Add "View Summary" button to results page header

**Phase 4 (Testing & Polish - Week 2)**:
- [ ] E2E tests for complete workflow
- [ ] Performance testing (insight generation time)
- [ ] Error handling validation
- [ ] UI polish and loading states

## References

- **Feature Spec**: [spec.md](./spec.md)
- **Constitution**: [.specify/memory/constitution.md](../../.specify/memory/constitution.md)
- **Architecture (Backend)**: [docs/arquitetura.md](../../docs/arquitetura.md)
- **Architecture (Frontend)**: [docs/arquitetura_front.md](../../docs/arquitetura_front.md)
- **Analysis Cache Exploration**: Conducted 2025-12-29 during planning session
- **OpenAI 04-mini**: https://platform.openai.com/docs/models/o1
- **LLMClient**: [src/synth_lab/infrastructure/llm_client.py](../../src/synth_lab/infrastructure/llm_client.py)
- **AnalysisRepository**: [src/synth_lab/repositories/analysis_repository.py](../../src/synth_lab/repositories/analysis_repository.py)

---

**Status**: Research complete. Ready for Phase 1 (data model and contracts).
