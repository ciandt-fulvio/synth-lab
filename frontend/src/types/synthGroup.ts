/**
 * T010 TypeScript types for SynthGroup.
 *
 * Types for synth group API request/response handling.
 *
 * References:
 *   - OpenAPI: specs/018-experiment-hub/contracts/openapi.yaml
 *   - Data model: specs/018-experiment-hub/data-model.md
 */

import type { PaginationMeta } from './common';

/**
 * Request schema for creating a new synth group.
 */
export interface SynthGroupCreate {
  /** Optional ID (grp_[a-f0-9]{8}). If not provided, will be generated. */
  id?: string;
  /** Descriptive name for the group */
  name: string;
  /** Description of the purpose/context */
  description?: string;
}

/**
 * Summary of a synth for list display.
 */
export interface SynthSummary {
  /** Synth ID */
  id: string;
  /** Synth name */
  nome: string;
  /** Synth description */
  descricao?: string | null;
  /** Path to avatar image */
  avatar_path?: string | null;
  /** Group ID */
  synth_group_id?: string | null;
  /** Creation timestamp */
  created_at: string;
}

/**
 * Summary of a synth group for list display.
 */
export interface SynthGroupSummary {
  /** Group ID (grp_[a-f0-9]{8}) */
  id: string;
  /** Group name */
  name: string;
  /** Group description */
  description?: string | null;
  /** Number of synths in group */
  synth_count: number;
  /** Creation timestamp */
  created_at: string;
}

/**
 * Full synth group details including synth list.
 */
export interface SynthGroupDetail extends SynthGroupSummary {
  /** Synths in this group */
  synths: SynthSummary[];
}

/**
 * Paginated list of synth group summaries.
 */
export interface PaginatedSynthGroup {
  data: SynthGroupSummary[];
  pagination: PaginationMeta;
}
