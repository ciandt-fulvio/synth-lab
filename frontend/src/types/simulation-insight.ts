/**
 * TypeScript types for simulation insights, evidence, failure modes, and clusters.
 *
 * Defines interfaces for the evidence endpoint responses.
 *
 * References:
 *   - Backend: api/schemas/simulation_insight.py
 */

/**
 * Percentile distribution for an outcome.
 */
export interface PercentileDistribution {
  p5: number;
  p25: number;
  p50: number;
  p75: number;
  p95: number;
  mean: number;
  std: number;
}

/**
 * Variance contribution (sensitivity analysis).
 */
export interface VarianceContribution {
  variable_name: string;
  variance_explained: number;
  rank: number;
}

/**
 * Condition on a variable in failure mode pattern.
 */
export interface VariableCondition {
  operator: '<' | '<=' | '>' | '>=' | '==';
  value: number;
}

/**
 * Threshold for outcome in failure mode.
 */
export interface OutcomeThreshold {
  operator: '<' | '<=' | '>' | '>=' | '==';
  value: number;
}

/**
 * Severity levels for failure modes.
 */
export type SeverityLevel = 'low' | 'medium' | 'high' | 'critical';

/**
 * Failure mode - pattern predicting poor outcomes.
 */
export interface FailureMode {
  id: string;
  evidence_id: string;
  pattern: Record<string, VariableCondition>;
  outcome_threshold: Record<string, OutcomeThreshold>;
  frequency: number;
  severity: SeverityLevel;
  description: string;
  created_at: string;
}

/**
 * Statistics for cluster outcomes.
 */
export interface ClusterOutcomeStats {
  mean: number;
  std: number;
  p50: number;
}

/**
 * Behavioral cluster - group of similar worlds.
 */
export interface BehavioralCluster {
  id: string;
  evidence_id: string;
  cluster_number: number;
  world_ids: string[];
  centroid: Record<string, number>;
  outcome_stats: Record<string, ClusterOutcomeStats>;
  size: number;
  percentage: number;
  label: string;
  created_at: string;
}

/**
 * Evidence response with all statistical analysis.
 */
export interface Evidence {
  id: string;
  simulation_id: string;
  outcome_distributions: Record<string, PercentileDistribution>;
  variance_explained: VarianceContribution[];
  correlation_matrix: Record<string, Record<string, number>>;
  failure_modes: FailureMode[];
  clusters: BehavioralCluster[];
  created_at: string;
}

/**
 * Insight response.
 */
export interface SimulationInsight {
  id: string;
  simulation_id: string;
  insight_type: 'key_driver' | 'failure_mode' | 'cluster_finding' | 'recommendation';
  title: string;
  description: string;
  evidence_references: Record<string, unknown>;
  recommended_actions: Array<{
    action: string;
    priority: string;
    impact: string;
  }>;
  confidence?: number;
  created_at: string;
}

/**
 * Insight trace response.
 */
export interface InsightTrace {
  insight_id: string;
  simulation_id: string;
  evidence_references: Record<string, unknown>;
  statistical_support: Record<string, number>;
  affected_worlds: string[];
}

/**
 * Severity badge configuration.
 */
export const SEVERITY_CONFIG: Record<SeverityLevel, { label: string; className: string }> = {
  low: { label: 'Low', className: 'badge-info' },
  medium: { label: 'Medium', className: 'badge-warning' },
  high: { label: 'High', className: 'badge-error' },
  critical: { label: 'Critical', className: 'badge-error' },
};

/**
 * Insight type badge configuration.
 */
export const INSIGHT_TYPE_CONFIG: Record<
  SimulationInsight['insight_type'],
  { label: string; className: string }
> = {
  key_driver: { label: 'Key Driver', className: 'badge-info' },
  failure_mode: { label: 'Failure Mode', className: 'badge-error' },
  cluster_finding: { label: 'Cluster', className: 'badge-neutral' },
  recommendation: { label: 'Recommendation', className: 'badge-success' },
};
