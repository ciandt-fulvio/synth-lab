/**
 * MaterialGallery component for displaying experiment materials.
 *
 * Features:
 * - Thumbnail grid with metadata
 * - Click to view full-size (images/documents)
 * - Video player modal for videos
 * - Description status indicators
 * - Delete and reorder actions
 *
 * Tasks: T045-T047
 */

import { useState, useEffect } from 'react';
import { FileIcon, FileText, Film, Image as ImageIcon, X } from 'lucide-react';
import { ExperimentMaterialSummary } from '@/types/material';
import { useMaterials, useDeleteMaterial } from '@/hooks/use-materials';
import { getViewUrl } from '@/services/materials-api';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { cn } from '@/lib/utils';

interface MaterialGalleryProps {
  experimentId: string;
}

export function MaterialGallery({ experimentId }: MaterialGalleryProps) {
  const { data: response, isLoading } = useMaterials(experimentId);
  const deleteMutation = useDeleteMaterial(experimentId);
  const [selectedMaterial, setSelectedMaterial] = useState<ExperimentMaterialSummary | null>(null);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <p className="text-muted-foreground">Carregando materiais...</p>
      </div>
    );
  }

  const materials = response?.materials || [];

  if (materials.length === 0) {
    return (
      <div className="flex items-center justify-center p-8 border-2 border-dashed rounded-lg">
        <p className="text-muted-foreground">Nenhum material anexado ainda</p>
      </div>
    );
  }

  return (
    <>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {materials.map((material) => (
          <MaterialCard
            key={material.id}
            material={material}
            onView={() => setSelectedMaterial(material)}
            onDelete={() => deleteMutation.mutate(material.id)}
          />
        ))}
      </div>

      {/* Full-size viewer modal */}
      {selectedMaterial && (
        <MaterialViewerModal
          material={selectedMaterial}
          experimentId={experimentId}
          onClose={() => setSelectedMaterial(null)}
        />
      )}
    </>
  );
}

interface MaterialCardProps {
  material: ExperimentMaterialSummary;
  onView: () => void;
  onDelete: () => void;
}

function MaterialCard({ material, onView, onDelete }: MaterialCardProps) {
  const fileTypeIcon = {
    image: ImageIcon,
    video: Film,
    document: FileText,
  }[material.file_type] || FileIcon;

  const Icon = fileTypeIcon;

  return (
    <div
      className={cn(
        'group relative border rounded-lg overflow-hidden',
        'hover:shadow-md transition-shadow cursor-pointer'
      )}
      onClick={onView}
    >
      {/* Thumbnail or placeholder */}
      <div className="aspect-video bg-muted flex items-center justify-center relative">
        {material.thumbnail_url ? (
          <img
            src={material.thumbnail_url}
            alt={material.file_name}
            className="w-full h-full object-cover"
          />
        ) : (
          <Icon className="h-12 w-12 text-muted-foreground" />
        )}

        {/* Delete button (visible on hover) */}
        <Button
          variant="destructive"
          size="icon"
          className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Metadata */}
      <div className="p-3 space-y-1">
        <p className="text-sm font-medium truncate" title={material.file_name}>
          {material.file_name}
        </p>

        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Badge variant="outline" className="text-xs">
            {material.material_type}
          </Badge>
          <span>{formatFileSize(material.file_size)}</span>
        </div>

        {/* Description status */}
        {material.description && (
          <p className="text-xs text-muted-foreground line-clamp-2">
            {material.description}
          </p>
        )}
      </div>
    </div>
  );
}

interface MaterialViewerModalProps {
  material: ExperimentMaterialSummary;
  experimentId: string;
  onClose: () => void;
}

function MaterialViewerModal({
  material,
  experimentId,
  onClose,
}: MaterialViewerModalProps) {
  const [viewUrl, setViewUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function fetchViewUrl() {
      try {
        const response = await getViewUrl(experimentId, material.id);
        setViewUrl(response.view_url);
      } catch (error) {
        console.error('Failed to get view URL:', error);
      } finally {
        setIsLoading(false);
      }
    }
    fetchViewUrl();
  }, [experimentId, material.id]);

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle>{material.file_name}</DialogTitle>
        </DialogHeader>

        <div className="overflow-auto">
          {isLoading ? (
            <div className="flex items-center justify-center p-8">
              <p className="text-muted-foreground">Carregando...</p>
            </div>
          ) : !viewUrl ? (
            <div className="flex items-center justify-center p-8">
              <p className="text-muted-foreground">Erro ao carregar arquivo</p>
            </div>
          ) : (
            <>
              {material.file_type === 'image' && (
                <img
                  src={viewUrl}
                  alt={material.file_name}
                  className="w-full h-auto"
                />
              )}

              {material.file_type === 'video' && (
                <video src={viewUrl} controls className="w-full h-auto" />
              )}

              {material.file_type === 'document' && (
                <div className="flex flex-col items-center gap-4 p-8">
                  <FileText className="h-16 w-16 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">
                    Visualização de documentos em desenvolvimento
                  </p>
                  <Button asChild>
                    <a
                      href={viewUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      download
                    >
                      Baixar documento
                    </a>
                  </Button>
                </div>
              )}
            </>
          )}

          {/* Metadata */}
          <div className="mt-4 p-4 bg-muted rounded-lg space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Tipo:</span>
              <span className="font-medium">{material.file_type}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Tamanho:</span>
              <span className="font-medium">
                {formatFileSize(material.file_size)}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Categoria:</span>
              <Badge variant="outline">{material.material_type}</Badge>
            </div>
            {material.description && (
              <div className="pt-2 border-t">
                <p className="text-sm text-muted-foreground">Descrição:</p>
                <p className="text-sm mt-1">{material.description}</p>
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
}
