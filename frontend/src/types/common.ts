// src/types/common.ts

export interface PaginationMeta {
  total: number;
  limit: number;
  offset: number;
  has_next: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: PaginationMeta;
}

export interface PaginationParams {
  limit?: number;
  offset?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}
