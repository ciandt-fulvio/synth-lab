// src/types/synth.ts

export interface Location {
  pais?: string;
  regiao?: string;
  estado?: string;
  cidade?: string;
}

export interface FamilyComposition {
  tipo?: string;
  numero_pessoas?: number;
}

export interface Demographics {
  idade?: number;
  genero_biologico?: string;
  raca_etnia?: string;
  localizacao?: Location;
  escolaridade?: string;
  renda_mensal?: number;
  ocupacao?: string;
  estado_civil?: string;
  composicao_familiar?: FamilyComposition;
}

export interface CognitiveContract {
  tipo?: string;
  perfil_cognitivo?: string;
  regras?: string[];
  efeito_esperado?: string;
}

export interface Psychographics {
  interesses?: string[];
  contrato_cognitivo?: CognitiveContract;
}

export interface VisualDisability {
  tipo?: string;
}

export interface HearingDisability {
  tipo?: string;
}

export interface MotorDisability {
  tipo?: string;
}

export interface CognitiveDisability {
  tipo?: string;
}

export interface Disabilities {
  visual?: VisualDisability;
  auditiva?: HearingDisability;
  motora?: MotorDisability;
  cognitiva?: CognitiveDisability;
}

// ============================================================================
// Simulation Attributes (Observable vs Latent Traits)
// ============================================================================

/**
 * Observable attribute with formatted label for PM display.
 * Used in SynthDetail response.
 */
export interface ObservableWithLabel {
  key: string;
  name: string;
  value: number;
  label: 'Muito Baixo' | 'Baixo' | 'Médio' | 'Alto' | 'Muito Alto';
  description: string;
}

/**
 * Raw simulation observables (for internal use).
 */
export interface SimulationObservables {
  digital_literacy: number;
  similar_tool_experience: number;
  motor_ability: number;
  time_availability: number;
  domain_expertise: number;
}

/**
 * Latent traits derived from observables (internal use only).
 * NOT shown to PM in frontend.
 */
export interface SimulationLatentTraits {
  capability_mean: number;
  trust_mean: number;
  friction_tolerance_mean: number;
  exploration_prob: number;
}

/**
 * Raw simulation attributes (observables + latent traits).
 */
export interface SimulationAttributesRaw {
  observables: SimulationObservables;
  latent_traits: SimulationLatentTraits;
}

/**
 * Formatted simulation attributes for PM display.
 * Frontend should use `observables_formatted` and NEVER show `raw.latent_traits`.
 */
export interface SimulationAttributesFormatted {
  observables_formatted: ObservableWithLabel[];
  raw?: SimulationAttributesRaw;
}

export interface SynthSummary {
  id: string;
  synth_group_id?: string | null;
  nome: string;
  descricao?: string;
  link_photo?: string;
  avatar_path?: string;
  created_at: string;
  version: string;
}

export interface SynthDetail extends SynthSummary {
  demografia?: Demographics;
  psicografia?: Psychographics;
  deficiencias?: Disabilities;
  observables?: SimulationObservables;
  simulation_attributes?: SimulationAttributesFormatted;
}

export interface SynthsListParams {
  limit?: number;
  offset?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
  synth_group_id?: string;
}

export interface SynthSearchRequest {
  where_clause?: string;
  query?: string;
}

export interface SynthFieldInfo {
  name: string;
  type: string;
  description?: string;
  nested_fields?: string[];
}
