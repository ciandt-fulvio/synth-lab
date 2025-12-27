-- Migration: Create chart_insights table
-- Purpose: Store LLM-generated insights for simulation charts
-- Reference: specs/017-analysis-ux-research/data-model.md

CREATE TABLE IF NOT EXISTS chart_insights (
    id TEXT PRIMARY KEY,
    simulation_id TEXT NOT NULL,
    insight_type TEXT NOT NULL,
    response_json TEXT NOT NULL CHECK(json_valid(response_json)),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(simulation_id, insight_type)
);

CREATE INDEX IF NOT EXISTS idx_chart_insights_simulation ON chart_insights(simulation_id);
CREATE INDEX IF NOT EXISTS idx_chart_insights_type ON chart_insights(insight_type);

-- insight_type values (from ChartType enum):
--   'try_vs_success', 'distribution', 'sankey', 'failure_heatmap',
--   'scatter', 'tornado', 'box_plot', 'clustering', 'outliers',
--   'shap_summary', 'pdp', 'executive_summary'
--
-- response_json contains the full ChartInsight or executive summary text:
-- {
--   "caption": "42% of synths in usability issue quadrant",
--   "explanation": "Detailed analysis...",
--   "evidence": ["Point 1", "Point 2"],
--   "recommendation": "Focus on...",
--   "confidence": 0.95,
--   "generated_at": "2025-01-15T10:30:00Z"
-- }
