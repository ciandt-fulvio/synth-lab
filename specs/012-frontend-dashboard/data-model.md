# Data Model: Frontend Dashboard

**Feature**: 012-frontend-dashboard
**Date**: 2025-12-20

## Overview

Este documento define as interfaces TypeScript para o frontend, baseadas nos modelos Pydantic do backend.

## TypeScript Interfaces

### Research Execution

```typescript
// src/types/research.ts

export type ExecutionStatus =
  | 'pending'
  | 'running'
  | 'generating_summary'
  | 'completed'
  | 'failed';

export interface ResearchExecutionSummary {
  exec_id: string;
  topic_name: string;
  status: ExecutionStatus;
  synth_count: number;
  started_at: string; // ISO datetime
  completed_at: string | null;
}

export interface ResearchExecutionDetail extends ResearchExecutionSummary {
  successful_count: number;
  failed_count: number;
  model: string;
  max_turns: number;
  summary_available: boolean;
  prfaq_available: boolean;
}

export interface Message {
  speaker: string;
  text: string;
  internal_notes?: string | null;
}

export interface TranscriptSummary {
  synth_id: string;
  synth_name: string | null;
  turn_count: number;
  timestamp: string;
  status: string;
}

export interface TranscriptDetail extends TranscriptSummary {
  exec_id: string;
  messages: Message[];
}

export interface ResearchExecuteRequest {
  topic_name: string;
  synth_ids?: string[] | null;
  synth_count?: number | null;
  max_turns?: number; // default: 6
  max_concurrent?: number; // default: 10
  model?: string; // default: 'gpt-4o-mini'
  generate_summary?: boolean; // default: true
}

export interface ResearchExecuteResponse {
  exec_id: string;
  status: ExecutionStatus;
  topic_name: string;
  synth_count: number;
  started_at: string;
}
```

### Synth

```typescript
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
```

### Topic

```typescript
// src/types/topic.ts

export interface TopicSummary {
  name: string;
  description?: string;
  question_count: number;
  file_count: number;
}

export interface TopicDetail extends TopicSummary {
  questions: string[];
  files: string[];
}
```

### PR/FAQ

```typescript
// src/types/prfaq.ts

export interface PRFAQSummary {
  exec_id: string;
  generated_at: string;
  model: string;
  validation_status?: string;
}

export interface PRFAQGenerateRequest {
  exec_id: string;
  model?: string;
}

export interface PRFAQGenerateResponse {
  exec_id: string;
  status: string;
  generated_at: string;
}
```

### Pagination

```typescript
// src/types/common.ts

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface PaginationParams {
  limit?: number;
  offset?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}
```

### SSE Events

```typescript
// src/types/events.ts

export interface InterviewMessageEvent {
  event_type: 'message';
  exec_id: string;
  synth_id: string;
  turn_number: number;
  speaker: string;
  text: string;
  timestamp: string;
  is_replay: boolean;
}

export interface TranscriptionCompletedEvent {
  event_type: 'transcription_completed';
  successful_count: number;
  failed_count: number;
}

export interface ExecutionCompletedEvent {
  event_type: 'execution_completed';
}

export type SSEEvent =
  | InterviewMessageEvent
  | TranscriptionCompletedEvent
  | ExecutionCompletedEvent;
```

## State Management

### React Query Keys

```typescript
// src/lib/query-keys.ts

export const queryKeys = {
  // Research
  researchList: ['research', 'list'] as const,
  researchDetail: (execId: string) => ['research', 'detail', execId] as const,
  researchTranscripts: (execId: string) => ['research', 'transcripts', execId] as const,
  researchSummary: (execId: string) => ['research', 'summary', execId] as const,

  // Synths
  synthsList: ['synths', 'list'] as const,
  synthDetail: (synthId: string) => ['synths', 'detail', synthId] as const,
  synthAvatar: (synthId: string) => ['synths', 'avatar', synthId] as const,

  // Topics
  topicsList: ['topics', 'list'] as const,
  topicDetail: (topicName: string) => ['topics', 'detail', topicName] as const,

  // PR/FAQ
  prfaqDetail: (execId: string) => ['prfaq', 'detail', execId] as const,
  prfaqMarkdown: (execId: string) => ['prfaq', 'markdown', execId] as const,
} as const;
```

## Component Props

### Interview Components

```typescript
// Props interfaces para componentes de Interview

export interface InterviewCardProps {
  execution: ResearchExecutionSummary;
  onClick: (execId: string) => void;
}

export interface InterviewListProps {
  onInterviewClick: (execId: string) => void;
}

export interface NewInterviewDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: (execId: string) => void;
}

export interface InterviewMessagesProps {
  execId: string;
  isLive: boolean;
}
```

### Synth Components

```typescript
// Props interfaces para componentes de Synth

export interface SynthCardProps {
  synth: SynthSummary;
  onClick: (synthId: string) => void;
}

export interface SynthListProps {
  onSynthClick: (synthId: string) => void;
}

export interface SynthDetailDialogProps {
  synthId: string | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export interface BigFiveChartProps {
  personality: BigFivePersonality;
}
```

## Validation Schemas (Zod)

```typescript
// src/lib/schemas.ts

import { z } from 'zod';

export const newInterviewSchema = z.object({
  topic_name: z.string().min(1, 'Selecione um tópico'),
  synth_ids: z.array(z.string()).optional(),
  synth_count: z.number().min(1).max(50).optional(),
  max_turns: z.number().min(1).max(20).default(6),
  model: z.string().default('gpt-4o-mini'),
  generate_summary: z.boolean().default(true),
}).refine(
  (data) => data.synth_ids?.length || data.synth_count,
  { message: 'Selecione synths ou defina uma quantidade' }
);

export type NewInterviewFormData = z.infer<typeof newInterviewSchema>;
```

## File Structure

```
src/
├── types/
│   ├── index.ts          # Re-exports
│   ├── research.ts       # Research types
│   ├── synth.ts          # Synth types
│   ├── topic.ts          # Topic types
│   ├── prfaq.ts          # PR/FAQ types
│   ├── events.ts         # SSE event types
│   └── common.ts         # Pagination, shared types
├── lib/
│   ├── query-keys.ts     # React Query keys
│   ├── schemas.ts        # Zod validation schemas
│   └── utils.ts          # Utilities (já existe)
└── ...
```
