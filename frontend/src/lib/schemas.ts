// src/lib/schemas.ts

import { z } from 'zod';

export const newInterviewSchema = z.object({
  topic_name: z.string().min(1, 'Selecione um tópico'),
  additional_context: z.string().optional(),
  synth_ids: z.array(z.string()).optional(),
  synth_count: z.number().min(1).max(50).optional(),
  max_turns: z.number().min(1).max(20).default(6),
}).refine(
  (data) => data.synth_ids?.length || data.synth_count,
  { message: 'Selecione synths ou defina uma quantidade' }
);

export type NewInterviewFormData = z.infer<typeof newInterviewSchema>;

// Schema for creating a new interview from experiment
export const newInterviewFromExperimentSchema = z.object({
  topic_name: z.string().min(1, 'Selecione um tópico'),
  additional_context: z.string().optional(),
  synth_count: z.number().min(1).max(50).default(5),
  max_turns: z.number().min(1).max(20).default(6),
});

export type NewInterviewFromExperimentFormData = z.infer<typeof newInterviewFromExperimentSchema>;
