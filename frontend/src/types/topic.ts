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
