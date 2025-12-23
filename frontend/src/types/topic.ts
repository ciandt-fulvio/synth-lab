// src/types/topic.ts

export interface TopicContextExamples {
  positive?: string;
  negative?: string;
  neutral?: string;
}

export interface TopicQuestion {
  id: number;
  ask: string;
  context_definition?: string;
  context_examples?: TopicContextExamples;
}

export interface TopicFile {
  filename: string;
  description?: string;
}

export interface TopicSummary {
  name: string;
  display_name?: string;
  description?: string;
  question_count: number;
  file_count: number;
  created_at?: string;
  updated_at?: string;
}

export interface TopicDetail extends TopicSummary {
  summary?: { content: string } | null;
  script: TopicQuestion[];
  files: TopicFile[];
}
