/**
 * TypeScript types for SynthGroup.
 *
 * Types for synth group API request/response handling.
 * Includes types for custom group configuration with demographic distributions.
 *
 * References:
 *   - OpenAPI: specs/018-experiment-hub/contracts/openapi.yaml
 *   - Data model: specs/018-experiment-hub/data-model.md
 *   - Custom groups: specs/030-custom-synth-groups/contracts/synth-groups-api.yaml
 */

import type { PaginationMeta } from './common';

// ============================================
// Distribution Configuration Types
// ============================================

export interface IdadeDistribution {
  '15-29': number;
  '30-44': number;
  '45-59': number;
  '60+': number;
}

export interface EscolaridadeDistribution {
  sem_instrucao: number;
  fundamental: number;
  medio: number;
  superior: number;
}

export interface SeveridadeDistribution {
  nenhuma: number;
  leve: number;
  moderada: number;
  severa: number;
  total: number;
}

export interface DeficienciasConfig {
  taxa_com_deficiencia: number;
  distribuicao_severidade: SeveridadeDistribution;
}

export interface ComposicaoFamiliarDistribution {
  unipessoal: number;
  casal_sem_filhos: number;
  casal_com_filhos: number;
  monoparental: number;
  multigeracional: number;
}

export interface DomainExpertiseConfig {
  alpha: number;
  beta: number;
}

export interface GroupDistributions {
  idade: IdadeDistribution;
  escolaridade: EscolaridadeDistribution;
  deficiencias: DeficienciasConfig;
  composicao_familiar: ComposicaoFamiliarDistribution;
  domain_expertise: DomainExpertiseConfig;
}

export interface GroupConfig {
  n_synths: number;
  distributions: GroupDistributions;
}

// ============================================
// Request Types
// ============================================

export interface CreateSynthGroupRequest {
  name: string;
  description?: string | null;
  config: GroupConfig;
}

// ============================================
// Response Types
// ============================================

export interface SynthGroupCreateResponse {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  synths_count: number;
}

export interface SynthGroupDetailResponse {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  synths_count: number;
  config: GroupConfig | null;
}

export interface PaginatedSynthGroupList {
  data: SynthGroupSummary[];
  pagination: PaginationMeta;
}

// ============================================
// UI State Types
// ============================================

export type DomainExpertiseLevel = 'baixo' | 'regular' | 'alto';

export interface SliderItem {
  key: string;
  label: string;
  value: number;
}

export interface DistributionSliderGroupState {
  items: SliderItem[];
  isDirty: boolean;
}

export interface CreateSynthGroupFormState {
  name: string;
  description: string;
  baseGroupId: string | null;
  idade: DistributionSliderGroupState;
  escolaridade: DistributionSliderGroupState;
  deficiencias: {
    taxa: number;
  };
  composicaoFamiliar: DistributionSliderGroupState;
  domainExpertise: DomainExpertiseLevel;
}

// ============================================
// Default Values (IBGE)
// ============================================

export const DEFAULT_IDADE_DISTRIBUTION: IdadeDistribution = {
  '15-29': 0.26,
  '30-44': 0.27,
  '45-59': 0.24,
  '60+': 0.23,
};

export const DEFAULT_ESCOLARIDADE_DISTRIBUTION: EscolaridadeDistribution = {
  sem_instrucao: 0.068,
  fundamental: 0.329,
  medio: 0.314,
  superior: 0.289,
};

export const DEFAULT_SEVERIDADE_DISTRIBUTION: SeveridadeDistribution = {
  nenhuma: 0.2,
  leve: 0.2,
  moderada: 0.2,
  severa: 0.2,
  total: 0.2,
};

export const DEFAULT_DEFICIENCIAS_CONFIG: DeficienciasConfig = {
  taxa_com_deficiencia: 0.084,
  distribuicao_severidade: DEFAULT_SEVERIDADE_DISTRIBUTION,
};

export const DEFAULT_COMPOSICAO_FAMILIAR: ComposicaoFamiliarDistribution = {
  unipessoal: 0.15,
  casal_sem_filhos: 0.2,
  casal_com_filhos: 0.35,
  monoparental: 0.18,
  multigeracional: 0.12,
};

export const DEFAULT_DOMAIN_EXPERTISE: DomainExpertiseConfig = {
  alpha: 3,
  beta: 3,
};

export const DEFAULT_GROUP_CONFIG: GroupConfig = {
  n_synths: 500,
  distributions: {
    idade: DEFAULT_IDADE_DISTRIBUTION,
    escolaridade: DEFAULT_ESCOLARIDADE_DISTRIBUTION,
    deficiencias: DEFAULT_DEFICIENCIAS_CONFIG,
    composicao_familiar: DEFAULT_COMPOSICAO_FAMILIAR,
    domain_expertise: DEFAULT_DOMAIN_EXPERTISE,
  },
};

// ============================================
// Domain Expertise Presets
// ============================================

export const DOMAIN_EXPERTISE_PRESETS: Record<
  DomainExpertiseLevel,
  DomainExpertiseConfig
> = {
  baixo: { alpha: 2, beta: 5 },
  regular: { alpha: 3, beta: 3 },
  alto: { alpha: 5, beta: 2 },
};

// ============================================
// Severity Distribution Presets
// ============================================

export const SEVERITY_DISTRIBUTION_IBGE: SeveridadeDistribution = {
  nenhuma: 0.2,
  leve: 0.2,
  moderada: 0.2,
  severa: 0.2,
  total: 0.2,
};

export const SEVERITY_DISTRIBUTION_WEIGHTED: SeveridadeDistribution = {
  nenhuma: 0.0,
  leve: 0.1,
  moderada: 0.25,
  severa: 0.3,
  total: 0.35,
};

// ============================================
// UI Labels (Portuguese)
// ============================================

export const IDADE_LABELS: Record<keyof IdadeDistribution, string> = {
  '15-29': '15-29 anos',
  '30-44': '30-44 anos',
  '45-59': '45-59 anos',
  '60+': '60+ anos',
};

export const ESCOLARIDADE_LABELS: Record<
  keyof EscolaridadeDistribution,
  string
> = {
  sem_instrucao: 'Sem instrução',
  fundamental: 'Fundamental',
  medio: 'Médio',
  superior: 'Superior',
};

export const COMPOSICAO_FAMILIAR_LABELS: Record<
  keyof ComposicaoFamiliarDistribution,
  string
> = {
  unipessoal: 'Unipessoal',
  casal_sem_filhos: 'Casal sem filhos',
  casal_com_filhos: 'Casal com filhos',
  monoparental: 'Monoparental',
  multigeracional: 'Multigeracional',
};

// ============================================
// Display Order (for UI consistency)
// ============================================

export const IDADE_ORDER: (keyof IdadeDistribution)[] = [
  '15-29',
  '30-44',
  '45-59',
  '60+',
];

export const ESCOLARIDADE_ORDER: (keyof EscolaridadeDistribution)[] = [
  'sem_instrucao',
  'fundamental',
  'medio',
  'superior',
];

export const COMPOSICAO_FAMILIAR_ORDER: (keyof ComposicaoFamiliarDistribution)[] = [
  'unipessoal',
  'casal_sem_filhos',
  'casal_com_filhos',
  'monoparental',
  'multigeracional',
];

export const DOMAIN_EXPERTISE_LABELS: Record<DomainExpertiseLevel, string> = {
  baixo: 'Baixo (maioria leigos)',
  regular: 'Regular (equilibrado)',
  alto: 'Alto (maioria especialistas)',
};

// ============================================
// Original Types (maintained for backward compatibility)
// ============================================

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
  /** Distribution configuration (if custom group) */
  config?: GroupConfig | null;
}

/**
 * Paginated list of synth group summaries.
 */
export interface PaginatedSynthGroup {
  data: SynthGroupSummary[];
  pagination: PaginationMeta;
}
