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
// Observable Labels (used by analysis charts for old simulation data)
// ============================================================================

/**
 * Observable attribute with formatted label for analysis chart display.
 * Used by observable-labels.ts for chart formatting.
 */
export interface ObservableWithLabel {
  key: string;
  name: string;
  value: number;
  label: 'Muito Baixo' | 'Baixo' | 'Médio' | 'Alto' | 'Muito Alto';
  description: string;
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

export interface UserSensitivities {
  risk_aversion: number;
  social_dependency: number;
  institutional_trust_level: number;
  habit_plasticity: number;
  friction_tolerance: number;
  pragmatism: number;
  digital_capability: number;
  motor_ability: number;
  subject_domain: number;
}

export interface SynthDetail extends SynthSummary {
  demografia?: Demographics;
  psicografia?: Psychographics;
  deficiencias?: Disabilities;
  sensitivities?: UserSensitivities;
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
