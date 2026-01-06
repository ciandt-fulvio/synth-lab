/**
 * Material types for synth-lab.
 *
 * Types for experiment materials (images, videos, documents).
 *
 * References:
 *   - API schemas: src/synth_lab/api/schemas/materials.py
 *   - Entity: src/synth_lab/domain/entities/experiment_material.py
 */

/**
 * Type of uploaded file.
 */
export type FileType = 'image' | 'video' | 'document';

/**
 * Purpose/category of the material.
 */
export type MaterialType = 'design' | 'prototype' | 'competitor' | 'spec' | 'other';

/**
 * Status of AI-generated description.
 */
export type DescriptionStatus = 'pending' | 'generating' | 'completed' | 'failed';

/**
 * Full material with all data.
 */
export interface ExperimentMaterial {
  id: string;
  experiment_id: string;
  file_type: FileType;
  file_url: string;
  thumbnail_url?: string | null;
  file_name: string;
  file_size: number;
  mime_type: string;
  material_type: MaterialType;
  description?: string | null;
  description_status: DescriptionStatus;
  display_order: number;
  created_at: string;
}

/**
 * Material summary for listing (without full URLs).
 */
export interface ExperimentMaterialSummary {
  id: string;
  file_type: FileType;
  file_name: string;
  file_size: number;
  thumbnail_url?: string | null;
  material_type: MaterialType;
  description?: string | null;
  description_status: DescriptionStatus;
  display_order: number;
}

/**
 * Request for presigned upload URL.
 */
export interface MaterialUploadRequest {
  file_name: string;
  file_size: number;
  mime_type: string;
  material_type: MaterialType;
}

/**
 * Response with presigned URL for upload.
 */
export interface MaterialUploadResponse {
  material_id: string;
  upload_url: string;
  object_key: string;
  expires_in: number;
}

/**
 * Confirm upload completion.
 */
export interface MaterialConfirmRequest {
  material_id: string;
  object_key: string;
}

/**
 * Response with list of materials.
 */
export interface MaterialListResponse {
  materials: ExperimentMaterialSummary[];
  total: number;
  total_size: number;
}

/**
 * Response with presigned view URL.
 */
export interface MaterialViewUrlResponse {
  material_id: string;
  view_url: string;
  thumbnail_url?: string | null;
  expires_in: number;
}

/**
 * Request to reorder materials.
 */
export interface MaterialReorderRequest {
  material_ids: string[];
}

/**
 * Response after retrying description generation.
 */
export interface RetryDescriptionResponse {
  material_id: string;
  status: DescriptionStatus;
  message: string;
}

/**
 * Material usage limits.
 */
export interface MaterialLimits {
  current_count: number;
  max_count: number;
  current_size: number;
  max_size: number;
  can_upload: boolean;
}

/**
 * Material type display labels (Portuguese).
 */
export const MATERIAL_TYPE_LABELS: Record<MaterialType, string> = {
  design: 'Design',
  prototype: 'Protótipo',
  competitor: 'Concorrente',
  spec: 'Especificação',
  other: 'Outro',
};

/**
 * File type display labels (Portuguese).
 */
export const FILE_TYPE_LABELS: Record<FileType, string> = {
  image: 'Imagem',
  video: 'Vídeo',
  document: 'Documento',
};

/**
 * Material type icons (Lucide React icon names).
 */
export const MATERIAL_TYPE_ICONS: Record<MaterialType, string> = {
  design: 'Palette',
  prototype: 'Smartphone',
  competitor: 'Users',
  spec: 'FileText',
  other: 'File',
};

/**
 * File type icons (Lucide React icon names).
 */
export const FILE_TYPE_ICONS: Record<FileType, string> = {
  image: 'Image',
  video: 'Video',
  document: 'FileText',
};

/**
 * Supported MIME types for upload.
 */
export const SUPPORTED_MIME_TYPES: Record<FileType, string[]> = {
  image: ['image/png', 'image/jpeg', 'image/jpg', 'image/webp', 'image/gif'],
  video: ['video/mp4', 'video/quicktime', 'video/webm'],
  document: ['application/pdf', 'text/plain', 'text/markdown'],
};

/**
 * All supported MIME types as flat array.
 */
export const ALL_SUPPORTED_MIME_TYPES: string[] = [
  ...SUPPORTED_MIME_TYPES.image,
  ...SUPPORTED_MIME_TYPES.video,
  ...SUPPORTED_MIME_TYPES.document,
];

/**
 * Get FileType from MIME type.
 */
export function getFileTypeFromMime(mimeType: string): FileType | null {
  if (SUPPORTED_MIME_TYPES.image.includes(mimeType)) return 'image';
  if (SUPPORTED_MIME_TYPES.video.includes(mimeType)) return 'video';
  if (SUPPORTED_MIME_TYPES.document.includes(mimeType)) return 'document';
  return null;
}

/**
 * Format file size for display.
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

/**
 * Upload limits (bytes).
 */
export const UPLOAD_LIMITS = {
  MAX_IMAGE_SIZE: 25 * 1024 * 1024, // 25MB
  MAX_VIDEO_SIZE: 100 * 1024 * 1024, // 100MB
  MAX_DOCUMENT_SIZE: 25 * 1024 * 1024, // 25MB
  MAX_TOTAL_SIZE: 250 * 1024 * 1024, // 250MB per experiment
  MAX_MATERIALS: 10, // per experiment
} as const;

/**
 * Validate file size based on type.
 */
export function validateFileSize(
  file: File,
  fileType: FileType
): { valid: boolean; message?: string } {
  const maxSize =
    fileType === 'video'
      ? UPLOAD_LIMITS.MAX_VIDEO_SIZE
      : fileType === 'image'
        ? UPLOAD_LIMITS.MAX_IMAGE_SIZE
        : UPLOAD_LIMITS.MAX_DOCUMENT_SIZE;

  if (file.size > maxSize) {
    return {
      valid: false,
      message: `Arquivo muito grande. Máximo para ${FILE_TYPE_LABELS[fileType]}: ${formatFileSize(maxSize)}`,
    };
  }

  return { valid: true };
}
