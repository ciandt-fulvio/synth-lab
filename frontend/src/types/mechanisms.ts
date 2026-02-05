/**
 * TypeScript types for mechanism configuration.
 *
 * References:
 *   - Spec: specs/039-narrative-mechanism-config/spec.md
 *   - API: specs/039-narrative-mechanism-config/contracts/api.yaml
 */

// ============================================================================
// Mechanism Types
// ============================================================================

/**
 * A text option for a mechanism with a mapped numeric value.
 */
export interface MechanismOption {
  /** Unique option identifier (UUID) */
  id: string;
  /** Display text for the option (e.g., "totalmente reversível") */
  label: string;
  /** Numeric value mapped to this option [0.0, 1.0] */
  value: number;
  /** Order in dropdown (ascending) */
  display_order: number;
}

/**
 * Defines a mechanism that can be configured via narrative dropdowns.
 */
export interface MechanismDefinition {
  /** Unique mechanism identifier (UUID) */
  id: string;
  /** Programmatic key (e.g., "irreversibility") */
  key: string;
  /** Portuguese label for display */
  label_pt: string;
  /** Explanation of what this mechanism measures */
  description: string;
  /** Available text options for this mechanism */
  options: MechanismOption[];
}

/**
 * Response from GET /mechanisms
 */
export interface MechanismListResponse {
  mechanisms: MechanismDefinition[];
}

// ============================================================================
// Feature Type Types
// ============================================================================

/**
 * Categorizes features and specifies amplified mechanisms.
 */
export interface FeatureType {
  /** Unique feature type identifier (UUID) */
  id: string;
  /** Programmatic key (e.g., "financial") */
  key: string;
  /** Portuguese label for display */
  label_pt: string;
  /** Description of this feature type */
  description: string | null;
  /** List of mechanism keys this type amplifies */
  amplifies_mechanisms: string[];
}

/**
 * Response from GET /mechanisms/feature-types
 */
export interface FeatureTypeListResponse {
  feature_types: FeatureType[];
}

// ============================================================================
// Narrative Generation Types
// ============================================================================

/**
 * Request body for POST /experiments/generate-narrative
 */
export interface GenerateNarrativeRequest {
  /** Feature name */
  name: string;
  /** Hypothesis to test */
  hypothesis: string;
  /** Additional context */
  description?: string | null;
}

/**
 * A mechanism selected by the LLM with its default option.
 */
export interface SelectedMechanism {
  /** Mechanism key (e.g., "irreversibility") */
  key: string;
  /** UUID of the default option chosen by LLM */
  default_option_id: string;
}

/**
 * Response from POST /experiments/generate-narrative
 */
export interface GenerateNarrativeResponse {
  /** Feature types inferred by LLM (e.g., ["financial", "social"]) */
  inferred_types: string[];
  /** Narrative text with {mechanism_key} placeholders */
  narrative_template: string;
  /** Mechanisms selected as relevant (2-4) */
  selected_mechanisms: SelectedMechanism[];
  /** Mechanism keys deemed not relevant */
  excluded_mechanisms: string[];
}

// ============================================================================
// UI State Types
// ============================================================================

/**
 * Local state for mechanism selections in the NarrativeMechanismEditor.
 */
export type MechanismSelections = Record<string, string>; // key -> optionId

/**
 * Extracted numeric values from mechanism selections.
 */
export type MechanismValues = Record<string, number>; // key -> value
