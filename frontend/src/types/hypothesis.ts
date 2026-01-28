/**
 * TypeScript types for Hypothesis structures.
 *
 * References:
 *   - Backend: api/schemas/hypothesis.py
 *   - Spec: specs/035-causal-simulation/spec.md
 */

/**
 * Distribution type enum.
 */
export type DistributionType =
  | 'normal'
  | 'uniform'
  | 'beta'
  | 'lognormal'
  | 'triangular'
  | 'bernoulli';

/**
 * Distribution parameters.
 */
export interface DistributionParameters {
  distribution_type: DistributionType;
  min_value?: number | null;
  max_value?: number | null;
  mean?: number | null;
  std_dev?: number | null;
  mode?: number | null;
  alpha?: number | null;
  beta?: number | null;
}

/**
 * Correlation with another variable.
 */
export interface Correlation {
  target_variable: string;
  correlation_coefficient: number;
  relationship_type: string;
}

/**
 * Scenario option for controllable variables.
 */
export interface ScenarioOption {
  value: string;
  label: string;
  distribution_params: DistributionParameters;
}

/**
 * Single hypothesis for a variable.
 */
export interface Hypothesis {
  id: string;
  simulation_id: string;
  variable_name: string;
  parameters: DistributionParameters;
  correlations: Correlation[];
  scenario_options?: ScenarioOption[] | null;
  selected_scenario?: string | null;
  version: number;
  rationale?: string | null;
  sources: string[];
  created_at: string;
}

/**
 * Request to update a hypothesis.
 */
export interface HypothesisUpdateRequest {
  parameters?: DistributionParameters;
  correlations?: Correlation[];
  selected_scenario?: string;
  rationale?: string;
}

/**
 * Request to update multiple hypotheses.
 */
export interface HypothesesBulkUpdateRequest {
  updates: Record<string, HypothesisUpdateRequest>;
}

/**
 * Hypothesis version summary.
 */
export interface HypothesisVersion {
  version: number;
  created_at: string;
  name?: string | null;
  description?: string | null;
  changes_summary?: string | null;
}

/**
 * Request to create a hypothesis version.
 */
export interface HypothesisVersionCreateRequest {
  name: string;
  description?: string;
}

/**
 * Request to compare hypothesis versions.
 */
export interface HypothesisCompareRequest {
  version_a: number;
  version_b: number;
}

/**
 * Hypothesis comparison response.
 */
export interface HypothesisCompareResponse {
  changed_variables: string[];
  parameter_changes: Record<string, { before: any; after: any }>;
  correlation_changes: Record<string, { before: any[]; after: any[] }>;
}

/**
 * Distribution option for picker.
 */
export interface DistributionOption {
  value: DistributionType;
  label: string;
  description: string;
  params: string[];
}

/**
 * Available distribution types with descriptions.
 */
export const DISTRIBUTION_OPTIONS: DistributionOption[] = [
  {
    value: 'normal',
    label: 'Normal (Gaussian)',
    description: 'Bell curve distribution',
    params: ['mean', 'std_dev'],
  },
  {
    value: 'uniform',
    label: 'Uniform',
    description: 'Equal probability across range',
    params: ['min_value', 'max_value'],
  },
  {
    value: 'beta',
    label: 'Beta',
    description: 'Flexible bounded distribution',
    params: ['alpha', 'beta', 'min_value', 'max_value'],
  },
  {
    value: 'lognormal',
    label: 'Log-Normal',
    description: 'Skewed positive values',
    params: ['mean', 'std_dev'],
  },
  {
    value: 'triangular',
    label: 'Triangular',
    description: 'Most likely value with bounds',
    params: ['min_value', 'max_value', 'mode'],
  },
  {
    value: 'bernoulli',
    label: 'Bernoulli',
    description: 'Binary outcome (yes/no)',
    params: ['mean'], // probability
  },
];
