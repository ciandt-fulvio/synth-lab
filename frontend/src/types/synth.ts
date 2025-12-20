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
  identidade_genero?: string;
  raca_etnia?: string;
  localizacao?: Location;
  escolaridade?: string;
  renda_mensal?: number;
  ocupacao?: string;
  estado_civil?: string;
  composicao_familiar?: FamilyComposition;
}

export interface BigFivePersonality {
  abertura?: number; // 0-100
  conscienciosidade?: number;
  extroversao?: number;
  amabilidade?: number;
  neuroticismo?: number;
}

export interface CognitiveContract {
  tipo?: string;
  perfil_cognitivo?: string;
  regras?: string[];
  efeito_esperado?: string;
}

export interface Psychographics {
  personalidade_big_five?: BigFivePersonality;
  interesses?: string[];
  contrato_cognitivo?: CognitiveContract;
}

export interface ConsumptionHabits {
  frequencia_compras?: string;
  preferencia_canal?: string;
  categorias_preferidas?: string[];
}

export interface TechUsage {
  smartphone?: boolean;
  computador?: boolean;
  tablet?: boolean;
  smartwatch?: boolean;
}

export interface SocialMediaEngagement {
  plataformas?: string[];
  frequencia_posts?: string;
}

export interface Behavior {
  habitos_consumo?: ConsumptionHabits;
  uso_tecnologia?: TechUsage;
  lealdade_marca?: number;
  engajamento_redes_sociais?: SocialMediaEngagement;
}

export interface VisualDisability {
  tipo?: string;
}

export interface HearingDisability {
  tipo?: string;
}

export interface MotorDisability {
  tipo?: string;
  usa_cadeira_rodas?: boolean;
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

export interface DeviceInfo {
  principal?: string;
  qualidade?: string;
}

export interface AccessibilityPrefs {
  zoom_fonte?: number;
  alto_contraste?: boolean;
}

export interface PlatformFamiliarity {
  e_commerce?: number;
  banco_digital?: number;
  redes_sociais?: number;
}

export interface TechCapabilities {
  alfabetizacao_digital?: number;
  dispositivos?: DeviceInfo;
  preferencias_acessibilidade?: AccessibilityPrefs;
  velocidade_digitacao?: number;
  frequencia_internet?: string;
  familiaridade_plataformas?: PlatformFamiliarity;
}

export interface SynthSummary {
  id: string;
  nome: string;
  arquetipo?: string;
  descricao?: string;
  link_photo?: string;
  avatar_path?: string;
  created_at: string;
  version: string;
}

export interface SynthDetail extends SynthSummary {
  demografia?: Demographics;
  psicografia?: Psychographics;
  comportamento?: Behavior;
  deficiencias?: Disabilities;
  capacidades_tecnologicas?: TechCapabilities;
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
