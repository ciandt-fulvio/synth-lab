# Data Model: AI-Generated Insights for Quantitative Analysis

**Feature**: 023-quantitative-ai-insights
**Date**: 2025-12-29
**Status**: Complete

## Overview

This feature extends the existing `analysis_cache` table to store AI-generated insights without requiring schema migrations. Insights are stored as JSON documents using new cache key enum values.

## Database Schema (No Changes Required)

### Existing Table: `analysis_cache`

```sql
CREATE TABLE analysis_cache (
    analysis_id TEXT NOT NULL,
    cache_key TEXT NOT NULL,
    data TEXT NOT NULL,           -- JSON document
    params TEXT,                   -- Optional JSON parameters
    computed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (analysis_id, cache_key),
    FOREIGN KEY (analysis_id) REFERENCES analysis_runs(id) ON DELETE CASCADE
);
```

**No schema changes needed**. Insights stored as JSON in existing `data` column.

## Enum Extensions

### CacheKeys (Extended)

```python
# src/synth_lab/repositories/analysis_repository.py

class CacheKeys(str, Enum):
    """Cache keys for analysis results."""

    # Existing chart types
    TRY_VS_SUCCESS = "try_vs_success"
    DISTRIBUTION = "distribution"
    SANKEY = "sankey"
    HEATMAP = "heatmap"
    SCATTER = "scatter"
    CORRELATIONS = "correlations"
    EXTREME_CASES = "extreme_cases"
    OUTLIERS = "outliers"
    SHAP_SUMMARY = "shap_summary"

    # NEW: Individual chart insights
    INSIGHT_TRY_VS_SUCCESS = "insight_try_vs_success"
    INSIGHT_SHAP_SUMMARY = "insight_shap_summary"
    INSIGHT_PDP = "insight_pdp"
    INSIGHT_PCA_SCATTER = "insight_pca_scatter"
    INSIGHT_RADAR_COMPARISON = "insight_radar_comparison"
    INSIGHT_EXTREME_CASES = "insight_extreme_cases"
    INSIGHT_OUTLIERS = "insight_outliers"

    # NEW: Executive summary
    EXECUTIVE_SUMMARY = "executive_summary"
```

## Domain Entities

### 1. ChartInsight

**Purpose**: Represents an AI-generated insight for a specific chart type.

**File**: `src/synth_lab/domain/entities/chart_insight.py`

```python
"""Chart insight entity."""

from datetime import datetime, timezone
from pydantic import BaseModel, Field


class ChartInsight(BaseModel):
    """AI-generated insight for a specific chart type."""

    analysis_id: str = Field(description="Parent analysis ID")
    chart_type: str = Field(
        description="Chart type identifier (e.g., 'try_vs_success', 'shap_summary')"
    )
    problem_understanding: str = Field(
        description="AI's understanding of what is being tested"
    )
    trends_observed: str = Field(
        description="Key patterns and trends identified in the data"
    )
    key_findings: list[str] = Field(
        description="2-4 actionable insights for the product team",
        min_length=2,
        max_length=4,
    )
    summary: str = Field(
        description="Concise summary in ≤200 words",
        max_length=1000,  # ~200 words * 5 chars/word
    )
    generation_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    status: str = Field(
        description="Generation status: pending|completed|failed",
        pattern="^(pending|completed|failed)$",
    )
    model: str = Field(
        description="LLM model used (e.g., '04-mini')",
        default="04-mini",
    )
    reasoning_trace: str | None = Field(
        description="Optional: LLM reasoning steps for debugging",
        default=None,
    )

    def to_cache_json(self) -> dict:
        """Convert to JSON format for storage in analysis_cache.data."""
        return self.model_dump()

    @classmethod
    def from_cache_json(cls, data: dict) -> "ChartInsight":
        """Create from JSON stored in analysis_cache.data."""
        return cls(**data)
```

**Validation Rules**:
- `chart_type`: Must match CacheKeys enum values (enforced at service layer)
- `key_findings`: Must have 2-4 items
- `summary`: Maximum 1000 characters (~200 words)
- `status`: One of `pending`, `completed`, `failed`

### 2. ExecutiveSummary

**Purpose**: Represents aggregated synthesis of all chart insights.

**File**: `src/synth_lab/domain/entities/executive_summary.py`

```python
"""Executive summary entity."""

from datetime import datetime, timezone
from pydantic import BaseModel, Field


class ExecutiveSummary(BaseModel):
    """Aggregated synthesis of all chart insights."""

    analysis_id: str = Field(description="Parent analysis ID")

    overview: str = Field(
        description="What was tested and overall results (≤200 words)",
        max_length=1000,
    )
    explainability: str = Field(
        description="Key drivers and feature impacts (≤200 words)",
        max_length=1000,
    )
    segmentation: str = Field(
        description="User groups and behavioral patterns (≤200 words)",
        max_length=1000,
    )
    edge_cases: str = Field(
        description="Surprises, anomalies, unexpected findings (≤200 words)",
        max_length=1000,
    )
    recommendations: list[str] = Field(
        description="2-3 actionable recommendations for product team",
        min_length=2,
        max_length=3,
    )

    included_chart_types: list[str] = Field(
        description="Chart types that contributed to this summary",
        min_length=1,
    )
    generation_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    status: str = Field(
        description="Generation status: pending|completed|failed",
        pattern="^(pending|completed|failed)$",
    )
    model: str = Field(
        description="LLM model used (e.g., '04-mini')",
        default="04-mini",
    )

    def to_cache_json(self) -> dict:
        """Convert to JSON format for storage in analysis_cache.data."""
        return self.model_dump()

    @classmethod
    def from_cache_json(cls, data: dict) -> "ExecutiveSummary":
        """Create from JSON stored in analysis_cache.data."""
        return cls(**data)
```

**Validation Rules**:
- All text sections: Maximum 1000 characters (~200 words)
- `recommendations`: Must have 2-3 items
- `included_chart_types`: Must have at least 1 chart type
- `status`: One of `pending`, `completed`, `failed`

## Storage Examples

### ChartInsight in analysis_cache

```sql
INSERT INTO analysis_cache (analysis_id, cache_key, data, params, computed_at)
VALUES (
    'ana_12345678',
    'insight_try_vs_success',
    '{
        "analysis_id": "ana_12345678",
        "chart_type": "try_vs_success",
        "problem_understanding": "O experimento testa a usabilidade de um novo fluxo de checkout...",
        "trends_observed": "Alta taxa de tentativa (85%) mas conversão moderada (62%)...",
        "key_findings": [
            "73% dos usuários que tentam completam o checkout",
            "Principal barreira: etapa de pagamento (23% falha)",
            "Synths com alta tolerância a fricção têm 2x mais sucesso"
        ],
        "summary": "O novo fluxo de checkout mostra boa descoberabilidade (85% tentam) mas enfrenta desafios de conversão na etapa de pagamento...",
        "generation_timestamp": "2025-12-29T10:30:00Z",
        "status": "completed",
        "model": "04-mini",
        "reasoning_trace": null
    }',
    '{"model": "04-mini", "temperature": 1.0}',
    '2025-12-29 10:30:00'
);
```

### ExecutiveSummary in analysis_cache

```sql
INSERT INTO analysis_cache (analysis_id, cache_key, data, params, computed_at)
VALUES (
    'ana_12345678',
    'executive_summary',
    '{
        "analysis_id": "ana_12345678",
        "overview": "Experimento testou novo fluxo de checkout com 500 synths. Resultados indicam boa descoberabilidade mas conversão limitada...",
        "explainability": "Análise SHAP revela que confiança (23.4%) e tolerância a fricção (18.9%) são os principais drivers de sucesso...",
        "segmentation": "PCA identificou 3 grupos: (1) usuários experientes com alta conversão, (2) novatos com taxa de tentativa média...",
        "edge_cases": "10 casos de falha surpreendente: synths com alta capacidade mas baixa confiança. Sugere problema de comunicação de segurança...",
        "recommendations": [
            "Simplificar etapa de pagamento para reduzir fricção",
            "Adicionar sinais de confiança visíveis (certificados de segurança)",
            "Oferecer onboarding para usuários novatos"
        ],
        "included_chart_types": [
            "try_vs_success",
            "shap_summary",
            "pdp",
            "pca_scatter",
            "radar_comparison",
            "extreme_cases",
            "outliers"
        ],
        "generation_timestamp": "2025-12-29T10:35:00Z",
        "status": "completed",
        "model": "04-mini"
    }',
    '{"model": "04-mini", "temperature": 1.0}',
    '2025-12-29 10:35:00'
);
```

## Repository Methods

### Extended AnalysisRepository

**File**: `src/synth_lab/repositories/analysis_repository.py` (modified)

```python
# NEW METHODS:

def store_chart_insight(
    self,
    analysis_id: str,
    chart_type: str,
    insight: ChartInsight
) -> None:
    """
    Store chart insight in analysis_cache.

    Args:
        analysis_id: Analysis ID.
        chart_type: Chart type identifier.
        insight: ChartInsight entity.
    """
    cache_key = f"insight_{chart_type}"
    data_json = json.dumps(insight.to_cache_json())
    params_json = json.dumps({"model": insight.model, "temperature": 1.0})

    self.db.execute(
        """
        INSERT OR REPLACE INTO analysis_cache
        (analysis_id, cache_key, data, params, computed_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            analysis_id,
            cache_key,
            data_json,
            params_json,
            insight.generation_timestamp.isoformat(),
        ),
    )

def get_chart_insight(
    self,
    analysis_id: str,
    chart_type: str
) -> ChartInsight | None:
    """
    Get chart insight from analysis_cache.

    Args:
        analysis_id: Analysis ID.
        chart_type: Chart type identifier.

    Returns:
        ChartInsight if found, None otherwise.
    """
    cache_key = f"insight_{chart_type}"
    row = self.db.fetchone(
        "SELECT data FROM analysis_cache WHERE analysis_id = ? AND cache_key = ?",
        (analysis_id, cache_key),
    )
    if row is None:
        return None

    data = json.loads(row["data"])
    return ChartInsight.from_cache_json(data)

def get_all_chart_insights(
    self,
    analysis_id: str
) -> list[ChartInsight]:
    """
    Get all chart insights for an analysis.

    Args:
        analysis_id: Analysis ID.

    Returns:
        List of ChartInsight entities (may be empty).
    """
    rows = self.db.fetchall(
        """
        SELECT data FROM analysis_cache
        WHERE analysis_id = ? AND cache_key LIKE 'insight_%'
        ORDER BY computed_at
        """,
        (analysis_id,),
    )

    insights = []
    for row in rows:
        data = json.loads(row["data"])
        insights.append(ChartInsight.from_cache_json(data))

    return insights

def store_executive_summary(
    self,
    analysis_id: str,
    summary: ExecutiveSummary
) -> None:
    """Store executive summary in analysis_cache."""
    data_json = json.dumps(summary.to_cache_json())
    params_json = json.dumps({"model": summary.model, "temperature": 1.0})

    self.db.execute(
        """
        INSERT OR REPLACE INTO analysis_cache
        (analysis_id, cache_key, data, params, computed_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            analysis_id,
            CacheKeys.EXECUTIVE_SUMMARY.value,
            data_json,
            params_json,
            summary.generation_timestamp.isoformat(),
        ),
    )

def get_executive_summary(
    self,
    analysis_id: str
) -> ExecutiveSummary | None:
    """Get executive summary from analysis_cache."""
    row = self.db.fetchone(
        "SELECT data FROM analysis_cache WHERE analysis_id = ? AND cache_key = ?",
        (analysis_id, CacheKeys.EXECUTIVE_SUMMARY.value),
    )
    if row is None:
        return None

    data = json.loads(row["data"])
    return ExecutiveSummary.from_cache_json(data)
```

## Data Flow

```
1. Analysis Completes
   └─> analysis_service._pre_compute_cache()
       └─> _cache_try_vs_success(), _cache_shap_summary(), etc.
           └─> Store chart data in analysis_cache

2. Insight Generation Triggered (NEW)
   └─> analysis_service._trigger_insight_generation()
       └─> Daemon thread: generate_all_insights()
           ├─> InsightService.generate_insight(chart_type="try_vs_success")
           │   ├─> Read chart data from analysis_cache
           │   ├─> Build prompt with experiment context
           │   ├─> Call LLM (04-mini)
           │   ├─> Parse JSON response → ChartInsight entity
           │   └─> AnalysisRepository.store_chart_insight()
           │       └─> INSERT INTO analysis_cache (cache_key="insight_try_vs_success")
           │
           ├─> [Parallel for all 7 chart types]
           │
           └─> ExecutiveSummaryService.generate_summary()
               ├─> AnalysisRepository.get_all_chart_insights()
               ├─> Build synthesis prompt
               ├─> Call LLM (04-mini)
               ├─> Parse JSON response → ExecutiveSummary entity
               └─> AnalysisRepository.store_executive_summary()
                   └─> INSERT INTO analysis_cache (cache_key="executive_summary")

3. Frontend Requests Insights
   └─> GET /api/experiments/{id}/insights/try_vs_success
       └─> InsightsRouter
           └─> InsightService.get_insight()
               └─> AnalysisRepository.get_chart_insight()
                   └─> SELECT from analysis_cache WHERE cache_key="insight_try_vs_success"
                       └─> Return ChartInsight JSON
```

## Relationships

```
Experiment (1) ─── (1) AnalysisRun
                        │
                        │ (1)
                        ▼
                  analysis_cache
                  ├─ chart data (9 rows: existing charts)
                  ├─ chart insights (7 rows: NEW)
                  └─ executive summary (1 row: NEW)
```

**Key Points**:
- No new tables
- No foreign key changes
- All insights linked to `analysis_id` via existing analysis_cache structure
- Insights auto-deleted when parent analysis is deleted (CASCADE)

## Type Definitions (Frontend)

**File**: `frontend/src/types/insights.ts`

```typescript
export interface ChartInsight {
  analysisId: string
  chartType: string
  problemUnderstanding: string
  trendsObserved: string
  keyFindings: string[] // 2-4 items
  summary: string // ≤200 words
  generationTimestamp: string
  status: "pending" | "completed" | "failed"
  model: string
  reasoningTrace?: string
}

export interface ExecutiveSummary {
  analysisId: string
  overview: string // ≤200 words
  explainability: string // ≤200 words
  segmentation: string // ≤200 words
  edgeCases: string // ≤200 words
  recommendations: string[] // 2-3 items
  includedChartTypes: string[]
  generationTimestamp: string
  status: "pending" | "completed" | "failed"
  model: string
}

export const CHART_TYPES_WITH_INSIGHTS = [
  "try_vs_success",
  "shap_summary",
  "pdp",
  "pca_scatter",
  "radar_comparison",
  "extreme_cases",
  "outliers",
] as const

export type ChartTypeWithInsight = typeof CHART_TYPES_WITH_INSIGHTS[number]
```

## Migration Plan

**Phase 0**: ✅ Complete (research.md)

**Phase 1**: ✅ Complete (this file)
- [x] Define data model
- [x] Create entity classes
- [x] Extend CacheKeys enum
- [x] Define repository methods
- [x] Document storage examples

**Phase 2**: Next (contracts/)
- [ ] Define API contracts
- [ ] Define frontend-backend data flow
- [ ] Create quickstart guide

---

**Status**: Data model complete. Ready for contracts (Phase 1 continued).
