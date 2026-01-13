/**
 * Frontend TypeScript types for Custom Synth Groups feature
 * Generated from spec: 030-custom-synth-groups
 */

// ============================================
// Distribution Configuration Types
// ============================================

export interface IdadeDistribution {
  "15-29": number;
  "30-44": number;
  "45-59": number;
  "60+": number;
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

export interface SynthGroupSummary {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  synths_count: number;
}

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

export interface PaginationMeta {
  total: number;
  limit: number;
  offset: number;
  sort_by: string;
  sort_order: string;
}

export interface PaginatedSynthGroupList {
  data: SynthGroupSummary[];
  pagination: PaginationMeta;
}

// ============================================
// UI State Types
// ============================================

export type DomainExpertiseLevel = "baixo" | "regular" | "alto";

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
  "15-29": 0.26,
  "30-44": 0.27,
  "45-59": 0.24,
  "60+": 0.23,
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
  "15-29": "15-29",
  "30-44": "30-44",
  "45-59": "45-59",
  "60+": "60+",
};

export const ESCOLARIDADE_LABELS: Record<
  keyof EscolaridadeDistribution,
  string
> = {
  sem_instrucao: "Sem instrução",
  fundamental: "Fundamental",
  medio: "Médio",
  superior: "Superior",
};

export const COMPOSICAO_FAMILIAR_LABELS: Record<
  keyof ComposicaoFamiliarDistribution,
  string
> = {
  unipessoal: "Unipessoal",
  casal_sem_filhos: "Casal sem filhos",
  casal_com_filhos: "Casal com filhos",
  monoparental: "Monoparental",
  multigeracional: "Multigeracional",
};

export const DOMAIN_EXPERTISE_LABELS: Record<DomainExpertiseLevel, string> = {
  baixo: "Baixo (maioria leigos)",
  regular: "Regular (distribuição equilibrada)",
  alto: "Alto (maioria especialistas)",
};
