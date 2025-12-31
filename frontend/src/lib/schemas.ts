// src/lib/schemas.ts

import { z } from 'zod';

export const newInterviewSchema = z.object({
  topic_name: z.string().min(1, 'Selecione um tópico'),
  additional_context: z.string().optional(),
  synth_ids: z.array(z.string()).optional(),
  synth_count: z.number().min(1).max(50).optional(),
  max_turns: z.number().min(1).max(20).default(6),
  generate_summary: z.boolean().default(true),
}).refine(
  (data) => data.synth_ids?.length || data.synth_count,
  { message: 'Selecione synths ou defina uma quantidade' }
);

export type NewInterviewFormData = z.infer<typeof newInterviewSchema>;

// Dimension schema for scorecard dimensions
const dimensionSchema = z.object({
  score: z.number().min(0).max(1),
  rules_applied: z.array(z.string()).optional(),
  min_uncertainty: z.number().min(0).max(1).optional(),
  max_uncertainty: z.number().min(0).max(1).optional(),
});

// Schema for creating a new scorecard (simulation)
export const newScorecardSchema = z.object({
  feature_name: z.string().min(1, 'Nome do recurso é obrigatório'),
  use_scenario: z.string().min(1, 'Cenário de uso é obrigatório'),
  description_text: z.string().min(1, 'Descrição é obrigatória'),
  evaluators: z.array(z.string()).optional(),
  complexity: dimensionSchema.optional(),
  initial_effort: dimensionSchema.optional(),
  perceived_risk: dimensionSchema.optional(),
  time_to_value: dimensionSchema.optional(),
});

export type NewScorecardFormData = z.infer<typeof newScorecardSchema>;

// Schema for creating a new interview from experiment
export const newInterviewFromExperimentSchema = z.object({
  topic_name: z.string().min(1, 'Selecione um tópico'),
  additional_context: z.string().optional(),
  synth_count: z.number().min(1).max(50).default(5),
  max_turns: z.number().min(1).max(20).default(6),
  generate_summary: z.boolean().default(true),
});

export type NewInterviewFromExperimentFormData = z.infer<typeof newInterviewFromExperimentSchema>;
