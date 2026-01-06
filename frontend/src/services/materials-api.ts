/**
 * Materials API client for synth-lab.
 *
 * API calls for experiment materials (images, videos, documents).
 *
 * References:
 *   - Backend: src/synth_lab/api/routers/materials.py
 *   - Types: src/types/material.ts
 */

import { fetchAPI } from './api';
import type {
  ExperimentMaterial,
  MaterialConfirmRequest,
  MaterialLimits,
  MaterialListResponse,
  MaterialReorderRequest,
  MaterialType,
  MaterialUploadRequest,
  MaterialUploadResponse,
  MaterialViewUrlResponse,
  RetryDescriptionResponse,
} from '@/types/material';

/**
 * List all materials for an experiment.
 */
export async function listMaterials(
  experimentId: string
): Promise<MaterialListResponse> {
  return fetchAPI(`/experiments/${experimentId}/materials`);
}

/**
 * Get material limits for an experiment.
 */
export async function getMaterialLimits(
  experimentId: string
): Promise<MaterialLimits> {
  return fetchAPI(`/experiments/${experimentId}/materials/limits`);
}

/**
 * Request a presigned upload URL.
 */
export async function requestUploadUrl(
  experimentId: string,
  request: MaterialUploadRequest
): Promise<MaterialUploadResponse> {
  return fetchAPI(`/experiments/${experimentId}/materials/upload-url`, {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Upload file directly to S3.
 *
 * @param uploadUrl - Presigned URL from requestUploadUrl
 * @param file - File to upload
 * @param onProgress - Optional progress callback (0-100)
 */
export async function uploadToS3(
  uploadUrl: string,
  file: File,
  onProgress?: (percent: number) => void
): Promise<void> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable && onProgress) {
        const percent = Math.round((event.loaded / event.total) * 100);
        onProgress(percent);
      }
    });

    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve();
      } else {
        reject(new Error(`Upload failed with status ${xhr.status}`));
      }
    });

    xhr.addEventListener('error', () => {
      reject(new Error('Upload failed'));
    });

    xhr.addEventListener('abort', () => {
      reject(new Error('Upload aborted'));
    });

    xhr.open('PUT', uploadUrl);
    xhr.setRequestHeader('Content-Type', file.type);
    xhr.send(file);
  });
}

/**
 * Confirm upload completion.
 */
export async function confirmUpload(
  experimentId: string,
  request: MaterialConfirmRequest
): Promise<ExperimentMaterial> {
  return fetchAPI(`/experiments/${experimentId}/materials/confirm`, {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Get a specific material.
 */
export async function getMaterial(
  experimentId: string,
  materialId: string
): Promise<ExperimentMaterial> {
  return fetchAPI(`/experiments/${experimentId}/materials/${materialId}`);
}

/**
 * Get presigned view URL for a material.
 */
export async function getViewUrl(
  experimentId: string,
  materialId: string
): Promise<MaterialViewUrlResponse> {
  return fetchAPI(`/experiments/${experimentId}/materials/${materialId}/view-url`);
}

/**
 * Reorder materials.
 */
export async function reorderMaterials(
  experimentId: string,
  request: MaterialReorderRequest
): Promise<MaterialListResponse> {
  return fetchAPI(`/experiments/${experimentId}/materials/reorder`, {
    method: 'PUT',
    body: JSON.stringify(request),
  });
}

/**
 * Delete a material.
 */
export async function deleteMaterial(
  experimentId: string,
  materialId: string
): Promise<void> {
  return fetchAPI(`/experiments/${experimentId}/materials/${materialId}`, {
    method: 'DELETE',
  });
}

/**
 * Retry description generation for a material.
 */
export async function retryDescription(
  experimentId: string,
  materialId: string
): Promise<RetryDescriptionResponse> {
  return fetchAPI(`/experiments/${experimentId}/materials/${materialId}/retry-description`, {
    method: 'POST',
  });
}

/**
 * Upload a material with progress tracking.
 *
 * Combines request URL, upload to S3, and confirmation in one function.
 *
 * @param experimentId - Experiment ID
 * @param file - File to upload
 * @param materialType - Purpose/category of material
 * @param onProgress - Optional progress callback (0-100)
 * @returns Confirmed material
 */
export async function uploadMaterial(
  experimentId: string,
  file: File,
  materialType: MaterialType,
  onProgress?: (percent: number) => void
): Promise<ExperimentMaterial> {
  // Step 1: Request upload URL
  const uploadResponse = await requestUploadUrl(experimentId, {
    file_name: file.name,
    file_size: file.size,
    mime_type: file.type,
    material_type: materialType,
  });

  // Step 2: Upload to S3
  await uploadToS3(uploadResponse.upload_url, file, onProgress);

  // Step 3: Confirm upload
  const material = await confirmUpload(experimentId, {
    material_id: uploadResponse.material_id,
    object_key: uploadResponse.object_key,
  });

  return material;
}
