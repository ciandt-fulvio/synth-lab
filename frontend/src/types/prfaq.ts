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
