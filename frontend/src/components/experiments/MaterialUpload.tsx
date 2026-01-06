/**
 * MaterialUpload component for synth-lab.
 *
 * Drag-and-drop file upload with material type selection and progress tracking.
 *
 * References:
 *   - react-dropzone: https://react-dropzone.js.org/
 *   - Types: src/types/material.ts
 *   - Hooks: src/hooks/use-materials.ts
 */

import { useCallback, useState, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Upload,
  X,
  Image,
  Video,
  FileText,
  Check,
  AlertCircle,
  Loader2,
  GripVertical,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';
import { useUploadMaterials, useMaterialLimits } from '@/hooks/use-materials';
import {
  ALL_SUPPORTED_MIME_TYPES,
  FILE_TYPE_LABELS,
  MATERIAL_TYPE_LABELS,
  UPLOAD_LIMITS,
  formatFileSize,
  getFileTypeFromMime,
  validateFileSize,
  type FileType,
  type MaterialType,
} from '@/types/material';

interface StagedFile {
  id: string;
  file: File;
  fileType: FileType;
  materialType: MaterialType;
  preview?: string;
}

interface MaterialUploadProps {
  experimentId: string;
  onUploadComplete?: () => void;
  className?: string;
}

const FILE_TYPE_ICONS: Record<FileType, React.ReactNode> = {
  image: <Image className="h-4 w-4" />,
  video: <Video className="h-4 w-4" />,
  document: <FileText className="h-4 w-4" />,
};

export function MaterialUpload({
  experimentId,
  onUploadComplete,
  className,
}: MaterialUploadProps) {
  const [stagedFiles, setStagedFiles] = useState<StagedFile[]>([]);
  const [defaultMaterialType, setDefaultMaterialType] = useState<MaterialType>('design');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadErrors, setUploadErrors] = useState<string[]>([]);

  // Drag-to-reorder state
  const [draggedId, setDraggedId] = useState<string | null>(null);
  const [dragOverId, setDragOverId] = useState<string | null>(null);
  const dragImageRef = useRef<HTMLDivElement>(null);

  const { data: limits } = useMaterialLimits(experimentId);
  const { uploads, uploadFiles, clearUploads } = useUploadMaterials(experimentId);

  const canUpload = limits?.can_upload !== false;
  const remainingSlots = limits
    ? limits.max_count - limits.current_count - stagedFiles.length
    : UPLOAD_LIMITS.MAX_MATERIALS;

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const errors: string[] = [];
      const newFiles: StagedFile[] = [];

      for (const file of acceptedFiles) {
        // Check MIME type
        const fileType = getFileTypeFromMime(file.type);
        if (!fileType) {
          errors.push(`${file.name}: Tipo de arquivo não suportado`);
          continue;
        }

        // Check file size
        const sizeValidation = validateFileSize(file, fileType);
        if (!sizeValidation.valid) {
          errors.push(`${file.name}: ${sizeValidation.message}`);
          continue;
        }

        // Check remaining slots
        if (newFiles.length + stagedFiles.length >= remainingSlots) {
          errors.push(`${file.name}: Limite de ${UPLOAD_LIMITS.MAX_MATERIALS} arquivos atingido`);
          continue;
        }

        // Create preview for images
        let preview: string | undefined;
        if (fileType === 'image') {
          preview = URL.createObjectURL(file);
        }

        newFiles.push({
          id: `${file.name}-${Date.now()}`,
          file,
          fileType,
          materialType: defaultMaterialType,
          preview,
        });
      }

      if (errors.length > 0) {
        setUploadErrors(errors);
      }

      if (newFiles.length > 0) {
        setStagedFiles((prev) => [...prev, ...newFiles]);
      }
    },
    [defaultMaterialType, remainingSlots, stagedFiles.length]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ALL_SUPPORTED_MIME_TYPES.reduce(
      (acc, type) => ({ ...acc, [type]: [] }),
      {} as Record<string, string[]>
    ),
    disabled: !canUpload || isUploading,
    multiple: true,
    maxFiles: remainingSlots,
  });

  const removeStagedFile = (id: string) => {
    setStagedFiles((prev) => {
      const file = prev.find((f) => f.id === id);
      if (file?.preview) {
        URL.revokeObjectURL(file.preview);
      }
      return prev.filter((f) => f.id !== id);
    });
  };

  const updateMaterialType = (id: string, materialType: MaterialType) => {
    setStagedFiles((prev) =>
      prev.map((f) => (f.id === id ? { ...f, materialType } : f))
    );
  };

  const handleUpload = async () => {
    if (stagedFiles.length === 0) return;

    setIsUploading(true);
    setUploadErrors([]);
    clearUploads();

    const errors: string[] = [];

    // Upload files sequentially for better control
    for (const staged of stagedFiles) {
      try {
        await uploadFiles([staged.file], staged.materialType);
      } catch (error) {
        errors.push(
          `${staged.file.name}: ${error instanceof Error ? error.message : 'Erro no upload'}`
        );
      }
    }

    // Clear previews
    stagedFiles.forEach((f) => {
      if (f.preview) URL.revokeObjectURL(f.preview);
    });
    setStagedFiles([]);
    setIsUploading(false);

    if (errors.length > 0) {
      setUploadErrors(errors);
    }

    onUploadComplete?.();
  };

  const clearAll = () => {
    stagedFiles.forEach((f) => {
      if (f.preview) URL.revokeObjectURL(f.preview);
    });
    setStagedFiles([]);
    setUploadErrors([]);
    clearUploads();
  };

  // Drag-to-reorder handlers
  const handleDragStart = (e: React.DragEvent, id: string) => {
    setDraggedId(id);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', id);

    // Use custom drag image for better visual feedback
    if (dragImageRef.current) {
      e.dataTransfer.setDragImage(dragImageRef.current, 0, 0);
    }
  };

  const handleDragOver = (e: React.DragEvent, id: string) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    if (draggedId && id !== draggedId) {
      setDragOverId(id);
    }
  };

  const handleDragLeave = () => {
    setDragOverId(null);
  };

  const handleDrop = (e: React.DragEvent, targetId: string) => {
    e.preventDefault();
    if (!draggedId || draggedId === targetId) {
      setDraggedId(null);
      setDragOverId(null);
      return;
    }

    setStagedFiles((prev) => {
      const draggedIndex = prev.findIndex((f) => f.id === draggedId);
      const targetIndex = prev.findIndex((f) => f.id === targetId);

      if (draggedIndex === -1 || targetIndex === -1) return prev;

      const newFiles = [...prev];
      const [draggedItem] = newFiles.splice(draggedIndex, 1);
      newFiles.splice(targetIndex, 0, draggedItem);
      return newFiles;
    });

    setDraggedId(null);
    setDragOverId(null);
  };

  const handleDragEnd = () => {
    setDraggedId(null);
    setDragOverId(null);
  };

  return (
    <div className={cn('space-y-4', className)}>
      {/* Upload limits info */}
      {limits && (
        <div className="text-sm text-slate-500 flex items-center gap-4">
          <span>
            {limits.current_count}/{limits.max_count} arquivos
          </span>
          <span>
            {formatFileSize(limits.current_size)}/{formatFileSize(limits.max_size)}
          </span>
        </div>
      )}

      {/* Default material type selector */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-slate-600">Tipo padrão:</span>
        <Select
          value={defaultMaterialType}
          onValueChange={(v) => setDefaultMaterialType(v as MaterialType)}
          disabled={isUploading}
        >
          <SelectTrigger className="w-40">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {Object.entries(MATERIAL_TYPE_LABELS).map(([value, label]) => (
              <SelectItem key={value} value={value}>
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={cn(
          'border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer',
          isDragActive
            ? 'border-indigo-500 bg-indigo-50'
            : 'border-slate-300 hover:border-slate-400 bg-slate-50',
          (!canUpload || isUploading) && 'opacity-50 cursor-not-allowed'
        )}
      >
        <input {...getInputProps()} />
        <Upload className="h-8 w-8 mx-auto text-slate-400 mb-2" />
        {isDragActive ? (
          <p className="text-indigo-600">Solte os arquivos aqui...</p>
        ) : (
          <div>
            <p className="text-slate-600">
              Arraste arquivos ou clique para selecionar
            </p>
            <p className="text-sm text-slate-400 mt-1">
              Imagens (PNG, JPG, WebP), Vídeos (MP4, MOV), Documentos (PDF)
            </p>
          </div>
        )}
      </div>

      {/* Upload errors */}
      {uploadErrors.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
          <div className="flex items-center gap-2 text-red-700 font-medium mb-1">
            <AlertCircle className="h-4 w-4" />
            Erros no upload
          </div>
          <ul className="text-sm text-red-600 list-disc list-inside">
            {uploadErrors.map((error, i) => (
              <li key={i}>{error}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Staged files list */}
      {stagedFiles.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium text-slate-700">
              Arquivos para upload ({stagedFiles.length})
            </h4>
            <Button
              variant="ghost"
              size="sm"
              onClick={clearAll}
              disabled={isUploading}
            >
              Limpar todos
            </Button>
          </div>

          <div className="border rounded-lg divide-y">
            {stagedFiles.map((staged) => {
              const uploadState = uploads.get(staged.file.name);
              const isDragging = draggedId === staged.id;
              const isDragOver = dragOverId === staged.id;

              return (
                <div
                  key={staged.id}
                  draggable={!isUploading}
                  onDragStart={(e) => handleDragStart(e, staged.id)}
                  onDragOver={(e) => handleDragOver(e, staged.id)}
                  onDragLeave={handleDragLeave}
                  onDrop={(e) => handleDrop(e, staged.id)}
                  onDragEnd={handleDragEnd}
                  className={cn(
                    'flex items-center gap-3 p-3 transition-colors',
                    isDragging && 'opacity-50 bg-slate-100',
                    isDragOver && 'bg-indigo-50 border-t-2 border-indigo-400',
                    !isDragging && !isDragOver && 'hover:bg-slate-50'
                  )}
                >
                  {/* Drag handle */}
                  <GripVertical
                    className={cn(
                      'h-4 w-4 flex-shrink-0 transition-colors',
                      isUploading ? 'text-slate-200 cursor-not-allowed' : 'text-slate-400 cursor-grab active:cursor-grabbing'
                    )}
                  />

                  {/* Preview or icon */}
                  <div className="h-10 w-10 rounded bg-slate-100 flex items-center justify-center overflow-hidden flex-shrink-0">
                    {staged.preview ? (
                      <img
                        src={staged.preview}
                        alt={staged.file.name}
                        className="h-full w-full object-cover"
                      />
                    ) : (
                      FILE_TYPE_ICONS[staged.fileType]
                    )}
                  </div>

                  {/* File info */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-700 truncate">
                      {staged.file.name}
                    </p>
                    <p className="text-xs text-slate-400">
                      {FILE_TYPE_LABELS[staged.fileType]} •{' '}
                      {formatFileSize(staged.file.size)}
                    </p>
                  </div>

                  {/* Material type selector */}
                  <Select
                    value={staged.materialType}
                    onValueChange={(v) =>
                      updateMaterialType(staged.id, v as MaterialType)
                    }
                    disabled={isUploading}
                  >
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(MATERIAL_TYPE_LABELS).map(([value, label]) => (
                        <SelectItem key={value} value={value}>
                          {label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  {/* Upload status */}
                  {uploadState && (
                    <div className="w-24">
                      {uploadState.status === 'uploading' && (
                        <Progress value={uploadState.progress} className="h-2" />
                      )}
                      {uploadState.status === 'completed' && (
                        <Check className="h-4 w-4 text-green-500" />
                      )}
                      {uploadState.status === 'error' && (
                        <AlertCircle
                          className="h-4 w-4 text-red-500"
                          title={uploadState.error}
                        />
                      )}
                    </div>
                  )}

                  {/* Remove button */}
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => removeStagedFile(staged.id)}
                    disabled={isUploading}
                    className="h-8 w-8"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              );
            })}
          </div>

          {/* Upload button */}
          <div className="flex justify-end">
            <Button
              onClick={handleUpload}
              disabled={isUploading || stagedFiles.length === 0}
            >
              {isUploading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Enviando...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Enviar {stagedFiles.length} arquivo
                  {stagedFiles.length > 1 ? 's' : ''}
                </>
              )}
            </Button>
          </div>
        </div>
      )}

      {/* Hidden drag image for better visual feedback */}
      <div
        ref={dragImageRef}
        className="fixed -left-[9999px] bg-white border border-indigo-200 rounded-lg px-3 py-2 shadow-lg"
      >
        <span className="text-sm text-indigo-600 font-medium">Movendo...</span>
      </div>
    </div>
  );
}
