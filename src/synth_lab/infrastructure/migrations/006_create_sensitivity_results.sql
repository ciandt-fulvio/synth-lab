-- Migration: Create sensitivity_results table
-- Purpose: Store One-At-a-Time sensitivity analysis results
-- Reference: specs/017-analysis-ux-research/data-model.md

CREATE TABLE IF NOT EXISTS sensitivity_results (
    id TEXT PRIMARY KEY,
    simulation_id TEXT NOT NULL,
    analyzed_at TEXT NOT NULL,
    deltas_used TEXT NOT NULL CHECK(json_valid(deltas_used)),
    baseline_success REAL NOT NULL,
    most_sensitive_dimension TEXT NOT NULL,
    dimensions TEXT NOT NULL CHECK(json_valid(dimensions)),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (simulation_id) REFERENCES simulation_runs(id)
);

CREATE INDEX IF NOT EXISTS idx_sensitivity_simulation ON sensitivity_results(simulation_id);
CREATE INDEX IF NOT EXISTS idx_sensitivity_analyzed_at ON sensitivity_results(analyzed_at);

-- Example data structure:
-- {
--   "id": "sens_abc123",
--   "simulation_id": "sim_xyz789",
--   "analyzed_at": "2025-01-15T10:30:00Z",
--   "deltas_used": "[0.05, 0.10]",
--   "baseline_success": 0.456,
--   "most_sensitive_dimension": "complexity",
--   "dimensions": "[{
--     "dimension": "complexity",
--     "baseline_value": 0.5,
--     "deltas_tested": [-0.1, -0.05, 0.05, 0.1],
--     "outcomes_by_delta": {...},
--     "sensitivity_index": 0.789,
--     "rank": 1
--   }]"
-- }
